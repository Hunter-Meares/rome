"""
NPC home-reset sweep - a direct follow-up to a real, confirmed gap:
CombatRules.schedule_respawn only ever restores a defeated NPC to its
own db.respawn_home, and only as part of the death/respawn cycle.
Nothing brings a NON-lethal displacement back - a god using
`godteleport` directly on an NPC, or any future effect that moves an
NPC without killing it (a "charm person"-style spell was named
directly as the motivating case), currently leaves that NPC exactly
wherever it was left, permanently, with no automatic recovery.

Scoped to genuinely cover every NPC in the game, current and future,
by direct request - not just the combat/RespawningNPC population.
This turned out to mean three separate typeclass hierarchies actually
exist in this codebase for NPC-like objects:

  1. typeclasses.characters.Character - flavor NPCs (Old Milo, Titus,
     the Colosseum Herald, ...) AND real players. Distinguished from a
     player by db_account being null - verified live: 179 flavor NPCs
     have no account, exactly the 3 real player characters do.
  2. world.combat.AutoStatNPC -> HostileNPC -> RespawningNPC - the
     persistent combat population (Ludus trainers, Arena Fighters,
     every Germania/Amber Coast warband NPC).
  3. evennia.DefaultCharacter directly - NPCMerchant, LanguageTrainer,
     SpellSkillTrainer.

Rather than sweeping each hierarchy separately (fragile - a fourth
one could exist that's just never been enumerated here), this queries
every live object with no account at all, then filters to whatever is
actually a DefaultCharacter subclass (is_typeclass(..., exact=False),
NOT the typeclass-bound .objects manager, which only matches exactly -
see the historical PROTOTYPE_MODULES/spawn() gotchas in CLAUDE.md for
why that distinction matters here too). evennia.DefaultCharacter is
the one real common ancestor of all three hierarchies above, verified
live: this single query already finds NPCMerchant, RespawningNPC, and
plain flavor NPCs together. Any future NPC typeclass is covered for
free as long as it's a Character subclass, which every puppetable/
room-occupying object in Evennia has to be by construction.

Three distinct reset behaviors, not one:

  - A WanderingNPC (world/colosseum.py's own script, checked by its
    "wandering_npc" key) is allowed to be anywhere in its own
    db.wander_rooms beat - that's normal operation, not displacement.
    Only reset if found OUTSIDE that whole list, back to
    wander_rooms[0] as a consistent anchor. By direct request - a
    wandering NPC pushed clean out of its beat should still come back.
  - Anything else (combat or flavor, non-wandering) resets to
    db.respawn_home if its current location differs from it.
  - Anything eligible with NO db.respawn_home set yet gets it stamped
    lazily from its CURRENT location on first sight, exactly like
    schedule_respawn's own bootstrap pattern for the death path -
    covers every NPC that predates this system (Old Milo included, by
    direct request as "a safety measure" even though nothing has ever
    displaced him) with zero manual backfill needed. The one accepted
    tradeoff: if an NPC happens to already be somewhere wrong the very
    first time this sweep ever runs, that wrong spot gets blessed as
    home - a rare, one-time bootstrapping edge case, self-correctable
    by hand (just edit db.respawn_home) rather than something worth
    building extra machinery to prevent.

Always skips anything currently mid-fight (never yank a live NPC out
of a fight a player is actually in) and anything with location=None
(mid-respawn-wait, not this sweep's problem).

Reset timer: every 12 hours (RESET_INTERVAL_HOURS below) - a middle
ground, not the tightest or loosest option considered. The actual
triggering scenario (a non-lethal displacement) is currently rare
(only a deliberate `godteleport` used directly on an NPC can cause it
today; no live spell does yet), so this doesn't need minute-level or
even hour-level correction the way an active gameplay ticker would.
But a named leader/boss/quest-relevant NPC sitting in the wrong room
for a full 24 hours risks visibly confusing multiple players across a
whole day's sessions before it self-corrects, which felt too loose. 6
hours would also be entirely reasonable if faster self-correction is
preferred - RESET_INTERVAL_HOURS is the one constant to change either
way, nothing else in this file assumes a specific value.

Registered as a real, persistent, real-interval global script
(GLOBAL_SCRIPTS in server/conf/settings.py) - the standard,
well-supported Evennia pattern (a script WITH a genuine ticking
interval is exactly the case Evennia's own generic script-restart
machinery already handles correctly across a reload, unlike the
wilderness scripts' own zero-interval special case documented at
length in world/wilderness_rome.py). No at_server_start() workaround
needed here.
"""

from evennia import DefaultScript, DefaultCharacter

RESET_INTERVAL_HOURS = 12


def _all_npc_characters():
    """
    Every live object with no linked account, filtered down to actual
    Character-like objects (DefaultCharacter subclasses) - see this
    module's own docstring for why this single query covers every NPC
    hierarchy in the game rather than enumerating each one by hand.
    """
    from evennia.objects.models import ObjectDB

    candidates = ObjectDB.objects.filter(db_account__isnull=True)
    return [obj for obj in candidates if obj.is_typeclass(DefaultCharacter, exact=False)]


def sweep_and_reset_displaced_npcs():
    """
    Does the actual work, factored out of the script's at_repeat() so
    it can also be run by hand (e.g. `py from world.npc_reset import
    sweep_and_reset_displaced_npcs as s; s()`) without waiting for the
    next scheduled tick. Returns a dict summary for easy confirmation
    either way.
    """
    from world.combat import COMBAT_RULES

    reset_count = 0
    wandering_reset_count = 0
    bootstrapped_count = 0
    skipped_in_combat = 0

    for npc in _all_npc_characters():
        if not npc.pk or npc.location is None:
            continue
        if COMBAT_RULES.is_in_combat(npc):
            skipped_in_combat += 1
            continue

        wander_script = npc.scripts.get("wandering_npc")
        wander_rooms = npc.db.wander_rooms
        if wander_script and wander_rooms:
            if npc.location in wander_rooms:
                continue
            old_location = npc.location
            npc.move_to(wander_rooms[0], quiet=True, move_type="teleport")
            if old_location:
                old_location.msg_contents("%s is no longer here." % npc.key)
            wander_rooms[0].msg_contents("%s returns to its usual beat." % npc.key)
            wandering_reset_count += 1
            continue

        home = npc.db.respawn_home
        if not home or not home.pk:
            npc.db.respawn_home = npc.location
            bootstrapped_count += 1
            continue
        if npc.location == home:
            continue

        old_location = npc.location
        npc.move_to(home, quiet=True, move_type="teleport")
        if old_location:
            old_location.msg_contents("%s is no longer here." % npc.key)
        home.msg_contents("%s returns to where it belongs." % npc.key)
        reset_count += 1

    return {
        "reset": reset_count,
        "wandering_reset": wandering_reset_count,
        "bootstrapped": bootstrapped_count,
        "skipped_in_combat": skipped_in_combat,
    }


class NPCHomeResetScript(DefaultScript):
    """
    The persistent global ticker itself - see this module's own
    docstring for the full reasoning (interval, scope, the three
    distinct reset behaviors).
    """

    def at_script_creation(self):
        self.key = "npc_home_reset"
        self.desc = "Periodically returns any displaced NPC to its own home room or wandering beat"
        self.interval = RESET_INTERVAL_HOURS * 3600
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        sweep_and_reset_displaced_npcs()
