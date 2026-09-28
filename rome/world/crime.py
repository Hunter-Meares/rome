"""
Rome's crime system, phase 1: the data model and detection - theft (a
caught Pilfer), assault (an unsanctioned PvP fight), and murder (an
unsanctioned PvP kill). See rome_mud_todo.md's design log for the full,
still-unbuilt roster this is a foundation for: guards, jail, execution,
confiscation, the wanted board. Nothing in this file does any of that yet -
it only decides WHETHER a crime happened and records it.

Scoped to "Rome proper" only (ROME_PROPER_ZONE_TAG, applied by
world/tag_rome_proper_live.py's own reachability walk) - a fight, a theft,
or a killing anywhere else (the Colosseum, the sewers, the wilderness,
Germania, the Amber Coast, the Underworld) is never a crime under this
system, by design: the law's writ doesn't reach there.

WITNESSING is the whole detection model - there's no "trial," no fact-
finding, because the game already has ground truth about who did what:

  - Any NPC present when a crime happens is an automatic witness - the
    crime is flagged the instant it happens, no player action needed.
  - A PLAYER present is NOT an automatic witness. They can `accuse <name>`
    afterward to confirm something they actually saw - validated against
    the logged crime_event itself (see accuse() below), never a free-form
    accusation. There is no way to falsely accuse someone of something
    that didn't happen.
  - The VICTIM of a theft or assault always knows who did it - they don't
    need a bystander to also have been present, and can always accuse()
    the perpetrator directly. A murder victim can too, once conscious
    again in the Underworld - the one path to justice for a killing
    nobody else ever witnessed.
  - A crime with no witness at all (no NPC present, no player chooses to
    accuse before the event expires) simply never gets flagged. This
    matches the historical furtum manifestum/nec manifestum distinction
    Pilfer's own success/failure split already gives us for free: a
    SUCCESSFUL, uncaught pilfer is never even logged as an event, since by
    definition nobody saw it happen - there's nothing to later accuse
    anyone of. Only a failed, caught attempt reaches log_crime() at all.

A DUEL (world/combat.py's CmdDuel) exempts both sides from crime detection
against each other for that one fight, however it ends - see is_sanctioned().

HOMO SACER (a convicted murderer, outside the law's own protection): once
`victim.db.homo_sacer` is set, NOTHING done to that specific person by
anyone is ever logged as a new crime - not assault, not another killing.
Real player-vs-player consequences (death, resurrection, the existing PvP
XP reward) are completely unaffected either way; this only ever changes
whether a NEW crime gets recorded against whoever did it.
"""

import time

from evennia.utils import search as evennia_search

ROME_PROPER_ZONE_TAG = ("rome_proper_zone", "zone")

# How long an unresolved crime_event stays accusable before it's pruned as
# stale - a witnessed-by-a-player-only crime doesn't stay "reportable"
# forever, matching the real, practical window an actual accusation would
# have (see accuse()).
CRIME_EVENT_EXPIRY = 60 * 60 * 24  # 24 real hours

# Crime severity - not consumed by anything yet in this first pass, but
# recorded on every proven crime (db.crime_record) so a later phase (jail
# sentencing, the wanted board) can read real history instead of needing
# this module touched again.
CRIME_WEIGHTS = {
    "theft": 2,
    "assault": 3,
    "murder": 10,
}
CAPITAL_CRIMES = {"murder"}


def is_rome_proper(room):
    """True if `room` is part of Rome proper - the only place this crime
    system ever applies. Same shape as world.combat.is_no_combat_zone."""
    if not room:
        return False
    key, category = ROME_PROPER_ZONE_TAG
    return bool(room.tags.get(key, category=category))


def is_sanctioned(character, other):
    """
    True if `character` and `other` are currently dueling EACH OTHER
    (world.combat.CmdDuel, db.combat_duel_partner) - exempts every crime
    check between them for this one fight. Kept as its own function (not
    just inlined in log_crime) since CombatTurnHandler's own assault-
    detection hook can't actually use this - see that call site's own
    comment for why it uses a plain ndb flag instead, and only for the
    initial fight-creation moment this covers.
    """
    return (
        character is not None and other is not None
        and character.db.combat_duel_partner is other
    )


def _room_witnesses(room, exclude):
    """
    Everyone actually present in `room` right now, other than whoever's in
    `exclude` - split into (npcs, players), both real Character-type
    objects (a scenery object, a weapon on the ground, a summoned pet -
    typeclass world.combat.SummonedAlly, not a Character - never counts).
    An NPC's mere presence is what makes a crime automatically witnessed;
    a player's presence only ever creates the chance to accuse() later.
    """
    npcs, players = [], []
    for obj in room.contents:
        if obj in exclude:
            continue
        # evennia.objects.objects.DefaultCharacter, not this project's own
        # typeclasses.characters.Character - a combat NPC (HostileNPC/
        # AutoStatNPC) is legitimately built on the bare DefaultCharacter
        # directly, and a hostile creature witnessing a crime should count
        # exactly the same as any other NPC.
        if not obj.is_typeclass("evennia.objects.objects.DefaultCharacter", exact=False):
            continue
        if getattr(obj, "account", None):
            players.append(obj)
        else:
            npcs.append(obj)
    return npcs, players


def _prune_events(perpetrator):
    """Drops anything already resolved or past CRIME_EVENT_EXPIRY, so a
    perpetrator's own event list doesn't grow without bound."""
    now = time.time()
    events = perpetrator.db.crime_events or []
    kept = [
        e for e in events
        if not e["resolved"] and now - e["timestamp"] <= CRIME_EVENT_EXPIRY
    ]
    perpetrator.db.crime_events = kept
    return kept


def _announce_rome_proper(text):
    """Broadcasts `text` to every room tagged Rome proper - the public
    "declared a murderer by the state" echo, deliberately scoped to the
    city rather than a global, game-wide announcement."""
    key, category = ROME_PROPER_ZONE_TAG
    for room in evennia_search.search_tag(key, category=category):
        room.msg_contents(text)


def flag_crime(perpetrator, crime_type, room):
    """
    The crime is now PROVEN - either an NPC witnessed it the instant it
    happened, or a player's accuse() just confirmed it. Appends to the
    permanent db.crime_record and updates standing status. Deliberately
    separate from log_crime(): logging an event and PROVING it are two
    different moments - an event with only player witnesses waits for an
    accusation; one an NPC saw is proven immediately.
    """
    weight = CRIME_WEIGHTS.get(crime_type, 1)
    record = perpetrator.db.crime_record or []
    record.append({"type": crime_type, "timestamp": time.time(), "weight": weight})
    perpetrator.db.crime_record = record

    if crime_type in CAPITAL_CRIMES:
        perpetrator.db.homo_sacer = True
        _announce_rome_proper(
            "|r%s has been declared a murderer by the state!|n" % perpetrator.key
        )
    else:
        perpetrator.db.wanted = True


def log_crime(perpetrator, victim, crime_type, room):
    """
    Records a crime_event if - and only if - it's genuinely eligible:
    inside Rome proper, involving two real players, not a sanctioned duel,
    and the victim isn't already homo sacer (nothing done to a convicted
    murderer is itself a new crime - see this module's own docstring).

    If any NPC is present, the crime is proven immediately (flag_crime).
    Otherwise it's logged on the perpetrator's own record, waiting for a
    possible accuse() from one of the players who were actually there.

    Returns the logged event dict, or None if the crime was never eligible
    to log at all.
    """
    if not is_rome_proper(room):
        return None
    if not getattr(perpetrator, "account", None) or not getattr(victim, "account", None):
        return None
    if is_sanctioned(perpetrator, victim):
        return None
    if victim.db.homo_sacer:
        return None

    npcs, players = _room_witnesses(room, exclude=(perpetrator, victim))
    event = {
        "type": crime_type,
        "victim": victim,
        "timestamp": time.time(),
        "room": room,
        "players_present": players,
        "resolved": False,
    }

    if npcs:
        event["resolved"] = True
        flag_crime(perpetrator, crime_type, room)
        victim.msg("|y%s's crime was seen - the law will know of it.|n" % perpetrator.key)
    else:
        events = _prune_events(perpetrator)
        events.append(event)
        perpetrator.db.crime_events = events

    return event


def accuse(accuser, perpetrator):
    """
    `accuser` confirms a crime committed by `perpetrator` that they're
    eligible to speak to - either they were the actual VICTIM of it (a
    theft or assault victim always knows who did it; even a murder victim,
    once conscious again in the Underworld, can still name their own
    killer - the dead crying out for justice, not a new mechanic, just
    letting an ordinary command reach them), or they were merely a
    bystander genuinely present in the room at the time (per the logged
    event's own players_present list). The event must not already be
    resolved or expired. Returns (True, message) on a successful
    accusation, (False, message) otherwise; never silently succeeds, and
    there is no way to accuse someone of something that never actually
    happened, since this only ever confirms a real, already-logged event,
    never a free-form claim.
    """
    if accuser is perpetrator:
        return False, "You can't accuse yourself of anything."

    events = _prune_events(perpetrator)
    for event in events:
        if accuser is event["victim"] or accuser in event["players_present"]:
            event["resolved"] = True
            perpetrator.db.crime_events = events
            flag_crime(perpetrator, event["type"], event["room"])
            return True, (
                "Your accusation is confirmed - %s is marked for it." % perpetrator.key
            )

    return False, "You have nothing to accuse %s of." % perpetrator.key


# ----------------------------------------------------------------------------
# COMMAND
# ----------------------------------------------------------------------------

from commands.command import Command  # noqa: E402  (after the module docstring/logic, matching this project's other command modules)


class CmdAccuse(Command):
    """
    Formally accuse someone of a crime you witnessed.

    Usage:
      accuse <name>

    Only works if you were genuinely present when they committed a crime
    the law hasn't already caught them for - the game checks this itself
    against what actually happened, so there's no way to falsely accuse
    someone. An NPC witness already reports a crime automatically, the
    instant it happens; this is for when only another player saw it.
    """

    key = "accuse"
    help_category = "general"

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg("Usage: accuse <name>")
            return

        target = caller.search(self.args.strip(), global_search=True)
        if not target:
            return

        success, message = accuse(caller, target)
        caller.msg(message)
