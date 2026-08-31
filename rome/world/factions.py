"""
Faction membership system

Eight NPC-induction-only factions, one at a time per character. Joining
grants a small set of faction-exclusive skills (added to db.skills_known,
gated in world.combat.SKILLS via a "factions" key and the "classes":
["faction"] sentinel - see the comment on FACTION_ABILITY_NAMES below for
why that sentinel matters), auto-connects the character to the faction's
private channel, and sets db.faction/db.faction_rank ("member" or
"leader" - exactly one leader per faction at a time).

Joining happens by finding a FactionInductorNPC in the room and using
`faction join <name>` - the NPC is flavor/roleplay dressing, the actual
grant happens through this module. `invest`/`expel` give gods (level
over 100) and a faction's own leader a direct shortcut that doesn't
require physically visiting the NPC - useful for correcting mistakes or
handling remote requests, not a replacement for the induction scene as
the normal path new members take.
"""

import random

from evennia import create_channel
from evennia.utils import search
from evennia.objects.objects import DefaultCharacter

from commands.command import Command

MIN_JOIN_LEVEL = 10
GOD_LEVEL_THRESHOLD = 100

FACTIONS = {
    "imperial_legion": {
        "name": "Imperial Legion",
        "channel": "Legion",
        "skills": ["muster", "forced march", "requisition"],
        "desc": (
            "The Empire's own soldiers, bound by discipline, rank, and the "
            "unbroken chain of command."
        ),
    },
    "praetorian_order": {
        "name": "Praetorian Order",
        "channel": "Praetorian",
        "skills": ["coerce", "censure", "interrogate"],
        "desc": (
            "The Emperor's guard and the city's real political power, working "
            "through leverage and quiet authority as often as the sword."
        ),
    },
    "hellenic_resistance": {
        "name": "Hellenic Resistance",
        "channel": "Hellenic",
        "skills": ["raid", "safehouse"],
        "desc": (
            "Greek partisans keeping the old world alive under Roman rule, "
            "fighting from the shadows of the city that conquered them."
        ),
    },
    "cult_of_mithras": {
        "name": "Cult of Mithras",
        "channel": "Mithras",
        "skills": ["vow", "aegis", "oath sworn"],
        "desc": (
            "An incorruptible brotherhood bound by sworn oaths, trusted by "
            "soldiers of every rank for exactly that reason."
        ),
    },
    "orphic_mysteries": {
        "name": "Orphic Mysteries",
        "channel": "Orphic",
        "skills": ["dirge", "rebirth", "speak with dead"],
        "desc": (
            "Mystics who study death and rebirth directly, unafraid of the "
            "Underworld because they claim to already understand it."
        ),
    },
    "cult_of_hecate": {
        "name": "Cult of Hecate",
        "channel": "Hecate",
        "skills": ["hex", "curse", "scrying"],
        "desc": (
            "Witches of the crossroads, trading in curses, bargains, and "
            "unpleasant knowledge nobody else wants to have."
        ),
    },
    "cult_of_bacchus": {
        "name": "Cult of Bacchus",
        "channel": "Bacchus",
        "skills": ["frenzy", "wild rite", "libation"],
        "desc": (
            "Devotees of wine and ecstatic revelry, dangerous precisely "
            "because they've given up restraint entirely."
        ),
    },
    "collegium_umbrae": {
        "name": "Collegium Umbrae",
        "channel": "Umbrae",
        "skills": ["evasion", "wither", "cloak"],
        "desc": (
            "A secret guild of assassins under Pluto's patronage, paid in "
            "silence as often as coin."
        ),
    },
}

# Every skill name across all 8 factions' "skills" lists above - built
# once here so world/combat.py's SKILLS entries and any other lookup can
# check "is this a faction skill" without importing FACTIONS and
# re-flattening it themselves.
FACTION_ABILITY_NAMES = {
    skill for data in FACTIONS.values() for skill in data["skills"]
}


def faction_for_skill(skill_name):
    """Returns the faction key that grants `skill_name`, or None."""
    for key, data in FACTIONS.items():
        if skill_name in data["skills"]:
            return key
    return None


RECENT_VISITORS_CAP = 10


def record_room_visit(character):
    """
    Appends (name, timestamp) to the room's own capped recent-visitors
    list - called from CombatCharacter.at_post_move. Deliberately
    separate from world/analytics.py's heavier session-trail logging
    (which only finalizes on logout and isn't meant for live querying)
    - this is a tiny, always-current list that Praetorian Order's
    Interrogate (see CmdInterrogate) reads directly.
    """
    import time

    location = character.location
    if not location:
        return
    visitors = location.db.recent_visitors or []
    visitors.append((character.key, time.time()))
    location.db.recent_visitors = visitors[-RECENT_VISITORS_CAP:]


class FactionInductorNPC(DefaultCharacter):
    """
    A faction's recruiter - plain DefaultCharacter, not CombatCharacter,
    matching SpellSkillTrainer's precedent (no reason to fight). Set
    db.faction to one of the FACTIONS keys; `faction join <name>` checks
    for one of these in the room with a matching db.faction.
    """

    def at_object_creation(self):
        self.locks.add("puppet:false()")


# ----------------------------------------------------------------------
# Channels
# ----------------------------------------------------------------------


def get_faction_channel(faction_key):
    """Finds the live Channel object for a faction, or None if it hasn't
    been created yet (see ensure_faction_channels_exist)."""
    data = FACTIONS.get(faction_key)
    if not data:
        return None
    found = search.search_channel(data["channel"])
    return found[0] if found else None


def ensure_faction_channels_exist():
    """
    Creates all 8 faction channels if they don't already exist. Safe to
    call repeatedly (e.g. on every server start) - idempotent, skips any
    channel that's already there. Locked so non-members can see the
    channel exists (it appears in a channel listing) but can't listen or
    send without being connected as a subscriber first - membership
    itself is what "connects" someone (see join_faction below), not this
    lock.
    """
    created = []
    for key, data in FACTIONS.items():
        if get_faction_channel(key):
            continue
        # Gods are gated by db.level directly (attr(level, 100,
        # compare=gt)), not by Evennia permission tier - matches every
        # other god-check in this codebase (CmdGodLevel, CmdRestore,
        # CmdWizInvis all compare caller.db.level, not perm()). Using
        # perm(Admin) here would only work for Praeses (104+), silently
        # locking out Novus Deus/Auspex/Aedilis (101-103) despite them
        # being real gods per every other check in the game.
        god_clause = "attr(level, 100, compare=gt)"
        channel = create_channel(
            key=data["channel"],
            desc="%s - private faction channel" % data["name"],
            locks=(
                "control:%s;"
                "listen:attr(faction, %s) or %s;"
                "send:attr(faction, %s) or %s"
            )
            % (god_clause, key, god_clause, key, god_clause),
        )
        _connect_all_gods_to(channel)
        created.append(channel)
    return created


def _connect_all_gods_to(channel):
    """Every character at a god level (over 100) auto-joins a channel the
    moment it exists, in addition to joining automatically on promotion
    (see world/combat.py's CmdGodLevel)."""
    for obj in search.search_object_attribute(key="level"):
        if not obj.is_typeclass("evennia.objects.objects.DefaultCharacter", exact=False):
            continue
        if (obj.db.level or 0) > GOD_LEVEL_THRESHOLD:
            channel.connect(obj)


def connect_god_to_all_faction_channels(character):
    """Called from CmdGodLevel whenever someone is promoted above level
    100 - joins every faction channel immediately rather than waiting
    for the next server restart's ensure_faction_channels_exist pass."""
    for key in FACTIONS:
        channel = get_faction_channel(key)
        if channel:
            channel.connect(character)


# ----------------------------------------------------------------------
# Membership
# ----------------------------------------------------------------------


def get_faction(character):
    return character.db.faction


def get_faction_rank(character):
    return character.db.faction_rank


def _strip_faction_abilities(character, faction_key):
    data = FACTIONS.get(faction_key)
    if not data:
        return
    known = character.db.skills_known or []
    character.db.skills_known = [s for s in known if s not in data["skills"]]


def _grant_faction_abilities(character, faction_key):
    data = FACTIONS[faction_key]
    known = character.db.skills_known or []
    for skill in data["skills"]:
        if skill not in known:
            known.append(skill)
    character.db.skills_known = known


def leave_faction(character, *, silent=False):
    """
    Removes a character from whatever faction they're currently in -
    strips their faction-exclusive skills, disconnects them from the
    channel, clears db.faction/db.faction_rank. If they were the
    faction's leader, the faction is simply left leaderless (a god has
    to designate a new one - see CmdFactionLeader) rather than promoting
    someone automatically, since who should lead isn't something this
    system can guess at.
    """
    old_faction = character.db.faction
    if not old_faction:
        return False

    _strip_faction_abilities(character, old_faction)
    channel = get_faction_channel(old_faction)
    if channel:
        channel.disconnect(character)

    character.db.faction = None
    character.db.faction_rank = None

    if not silent:
        character.msg(
            "You are no longer a member of the %s." % FACTIONS[old_faction]["name"]
        )
    return True


def join_faction(character, faction_key):
    """
    Adds character to faction_key as a plain member - switching from an
    existing faction leaves the old one first (one faction at a time).
    Rank always starts at "member"; leadership is a separate, deliberate
    step (see CmdFactionLeader), never automatic on join.
    """
    if faction_key not in FACTIONS:
        return False

    if character.db.faction == faction_key:
        character.msg("You are already a member of the %s." % FACTIONS[faction_key]["name"])
        return False

    if character.db.faction:
        leave_faction(character, silent=True)

    _grant_faction_abilities(character, faction_key)
    character.db.faction = faction_key
    character.db.faction_rank = "member"

    channel = get_faction_channel(faction_key)
    if channel:
        channel.connect(character)

    character.msg("You are now a member of the %s." % FACTIONS[faction_key]["name"])
    return True


def set_faction_leader(faction_key, character):
    """
    Designates character as the faction's one and only leader - demotes
    whoever held it before (a faction can never have more than one
    leader at a time). character must already be a member; promotes
    them in place rather than requiring a separate join first.
    """
    if faction_key not in FACTIONS:
        return False

    for obj in search.search_object_attribute(key="faction", value=faction_key):
        if obj.db.faction_rank == "leader" and obj != character:
            obj.db.faction_rank = "member"
            obj.msg(
                "You have been replaced as leader of the %s."
                % FACTIONS[faction_key]["name"]
            )

    if character.db.faction != faction_key:
        join_faction(character, faction_key)
    character.db.faction_rank = "leader"
    character.msg("You are now the leader of the %s." % FACTIONS[faction_key]["name"])
    return True


def can_manage_faction(caller, faction_key):
    """True if caller can invest/expel members of faction_key - any god
    (level over 100, or true superuser), or that specific faction's own
    leader."""
    is_superuser = bool(caller.account and caller.account.is_superuser)
    if is_superuser or (caller.db.level or 0) > GOD_LEVEL_THRESHOLD:
        return True
    return caller.db.faction == faction_key and caller.db.faction_rank == "leader"


# ----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------


class CmdFaction(Command):
    """
    Manage faction membership.

    Usage:
      faction                    - show your faction and rank
      faction join <name>        - hear an inductor NPC's warning
                                    about what joining means
      faction join <name> confirm
                                  - actually join, having heard it
      faction leave              - leader: step down from leadership
                                    only, still bound as a member.
                                    god: leave outright.
      faction invest <char> = <faction>
                                  - god or faction-leader only: add
                                    someone as a member directly
      faction expel <char>       - god or faction-leader only: remove
                                    someone from their faction

    Joining a faction is permanent - there is no walking away from it
    on your own once you're in. An ordinary member can't self-leave at
    all. A leader's 'faction leave' only sheds the leadership role -
    they remain bound to the faction for life like anyone else, and
    getting out entirely still requires a god's 'faction expel'. See
    'help factions' for the full policy and what each faction offers.
    """

    key = "faction"
    help_category = "general"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            current = caller.db.faction
            if not current:
                caller.msg("You are not a member of any faction.")
                return
            rank = caller.db.faction_rank or "member"
            caller.msg(
                "You are a %s of the %s." % (rank, FACTIONS[current]["name"])
            )
            return

        parts = args.split(None, 1)
        sub = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        if sub == "join":
            self._join(caller, rest)
        elif sub == "leave":
            self._leave(caller)
        elif sub == "invest":
            self._invest(caller, rest)
        elif sub == "expel":
            self._expel(caller, rest)
        else:
            caller.msg("Usage: faction [join <name>|leave|invest <char> = <faction>|expel <char>]")

    def _leave(self, caller):
        current = caller.db.faction
        if not current:
            caller.msg("You are not a member of any faction.")
            return

        is_superuser = bool(caller.account and caller.account.is_superuser)
        is_god = is_superuser or (caller.db.level or 0) > GOD_LEVEL_THRESHOLD

        if caller.db.faction_rank == "leader" and not is_god:
            # Stepping down from leadership is not the same vow as
            # membership itself - a leader shouldn't be trapped running
            # a faction forever just because they were once willing to
            # lead it. This only sheds the role; the lifelong
            # membership commitment underneath it is untouched, same
            # as any other member's - a former leader who wants out
            # entirely still needs a god to expel them, same as anyone.
            caller.db.faction_rank = "member"
            caller.msg(
                "You step down as leader of the %s, though you remain "
                "bound to it for life, same as any other member."
                % FACTIONS[current]["name"]
            )
            return

        if not is_god:
            caller.msg(
                "You swore yourself to the %s for life - there is no walking "
                "away from that on your own. Petition your faction's leader, "
                "or the gods themselves, if you truly want out."
                % FACTIONS[current]["name"]
            )
            return

        leave_faction(caller)

    def _join(self, caller, name):
        if not name:
            caller.msg("Join whom, or which faction? There's no one here to be inducted by.")
            return

        level = caller.db.level or 1
        if level < MIN_JOIN_LEVEL:
            caller.msg("You aren't experienced enough yet - factions require level %d." % MIN_JOIN_LEVEL)
            return

        # "faction join <name> confirm" - the trailing word is stripped
        # off before the inductor-name matching below, so it never
        # interferes with matching a name/faction that happens to
        # contain "confirm" as a substring (none currently do, but this
        # keeps the two concerns cleanly separate regardless).
        confirmed = False
        words = name.split()
        if words and words[-1].lower() == "confirm":
            confirmed = True
            name = " ".join(words[:-1])
        if not name:
            caller.msg("Join whom, or which faction? There's no one here to be inducted by.")
            return

        # Accepts either the inductor's own name ("faction join gaius")
        # or the faction's name ("faction join legion") - a player
        # standing right in front of the recruiter is more likely to
        # know which faction they want than to know the NPC's full
        # name, so matching on both is a lot more forgiving.
        name_lower = name.lower()
        here = caller.location
        inductor = None
        for obj in here.contents:
            faction_key = obj.db.faction
            if not faction_key:
                continue
            if obj.key.lower().startswith(name_lower):
                inductor = obj
                break
            if name_lower in FACTIONS[faction_key]["name"].lower():
                inductor = obj
                break
        if not inductor:
            caller.msg("There's no one here by that name to induct you into a faction.")
            return

        faction_name = FACTIONS[inductor.db.faction]["name"]

        if not confirmed:
            caller.msg(
                "%s fixes you with a level look. \"Think carefully before you "
                "answer. Join the %s and you belong to it for the rest of your "
                "life - there is no walking away from this whenever you please. "
                "The only way out, once you're in, is a petition to the "
                "faction's leader, or to the gods themselves. If you are "
                "certain, say so plainly: |wfaction join %s confirm|n.\""
                % (inductor.key, faction_name, inductor.key)
            )
            return

        join_faction(caller, inductor.db.faction)

    def _invest(self, caller, args):
        if "=" not in args:
            caller.msg("Usage: faction invest <character> = <faction>")
            return
        lhs, rhs = args.split("=", 1)
        target = caller.search(lhs.strip(), global_search=True)
        if not target:
            return

        try:
            faction_key = _resolve_faction_name(rhs.strip())
        except ValueError as e:
            caller.msg("Which faction do you mean: %s?" % e)
            return
        if not faction_key:
            caller.msg("No faction matches '%s'." % rhs.strip())
            return

        if not can_manage_faction(caller, faction_key):
            caller.msg("You don't have the standing to invest anyone into that faction.")
            return

        join_faction(target, faction_key)
        caller.msg("%s has been invested into the %s." % (target.key, FACTIONS[faction_key]["name"]))

    def _expel(self, caller, name):
        if not name:
            caller.msg("Usage: faction expel <character>")
            return
        target = caller.search(name.strip(), global_search=True)
        if not target:
            return

        faction_key = target.db.faction
        if not faction_key:
            caller.msg("%s is not a member of any faction." % target.key)
            return

        if not can_manage_faction(caller, faction_key):
            caller.msg("You don't have the standing to expel members of that faction.")
            return

        leave_faction(target, silent=True)
        target.msg("You have been expelled from the %s." % FACTIONS[faction_key]["name"])
        caller.msg("%s has been expelled from the %s." % (target.key, FACTIONS[faction_key]["name"]))


def _resolve_faction_name(text):
    """
    Returns a faction key for text, or None if there's no match. Raises
    ValueError with the list of candidate names if text matches more
    than one faction (e.g. "cult" alone matches three) - callers should
    catch this and show the message to the user rather than silently
    picking the first match, which could invest/expel someone into the
    wrong faction entirely.
    """
    text_lower = text.strip().lower()
    if text_lower in FACTIONS:
        return text_lower
    matches = [key for key, data in FACTIONS.items() if text_lower in data["name"].lower()]
    if len(matches) > 1:
        raise ValueError(", ".join(FACTIONS[key]["name"] for key in matches))
    return matches[0] if matches else None


class CmdFactionLeader(Command):
    """
    Designate a faction's leader - god-only.

    Usage:
      factionleader <character> = <faction>

    Promotes character to leader of that faction, demoting whoever held
    it before (a faction only ever has one leader at a time). Requires
    Auspex (level over 100) or true superuser.
    """

    key = "factionleader"
    help_category = "admin"

    def func(self):
        caller = self.caller
        is_superuser = bool(caller.account and caller.account.is_superuser)
        if (caller.db.level or 0) <= GOD_LEVEL_THRESHOLD and not is_superuser:
            caller.msg("You lack the standing to designate a faction leader.")
            return

        if "=" not in self.args:
            caller.msg("Usage: factionleader <character> = <faction>")
            return
        lhs, rhs = self.args.split("=", 1)
        target = caller.search(lhs.strip(), global_search=True)
        if not target:
            return

        try:
            faction_key = _resolve_faction_name(rhs.strip())
        except ValueError as e:
            caller.msg("Which faction do you mean: %s?" % e)
            return
        if not faction_key:
            caller.msg("No faction matches '%s'." % rhs.strip())
            return

        set_faction_leader(faction_key, target)
        caller.msg(
            "%s is now the leader of the %s." % (target.key, FACTIONS[faction_key]["name"])
        )


class CmdChannelKick(Command):
    """
    Remove someone from a channel - god-only.

    Usage:
      channelkick <channel> = <character>

    Requires Auspex (level over 100) or true superuser.
    """

    key = "channelkick"
    help_category = "admin"

    def func(self):
        caller = self.caller
        is_superuser = bool(caller.account and caller.account.is_superuser)
        if (caller.db.level or 0) <= GOD_LEVEL_THRESHOLD and not is_superuser:
            caller.msg("You lack the standing to remove anyone from a channel.")
            return

        if "=" not in self.args:
            caller.msg("Usage: channelkick <channel> = <character>")
            return
        lhs, rhs = self.args.split("=", 1)
        found = search.search_channel(lhs.strip())
        if not found:
            caller.msg("No channel found matching '%s'." % lhs.strip())
            return
        channel = found[0]

        target = caller.search(rhs.strip(), global_search=True)
        if not target:
            return

        if channel.disconnect(target):
            caller.msg("%s has been removed from %s." % (target.key, channel.key))
            target.msg("You have been removed from the %s channel." % channel.key)
        else:
            caller.msg("%s wasn't connected to %s." % (target.key, channel.key))


# ----------------------------------------------------------------------
# Custom-mechanic ability commands
#
# The rest of each faction's abilities (Muster, Coerce, Censure, Raid,
# Vow, Aegis, Dirge, Rebirth, Hex, Curse, Frenzy, Wild Rite, Libation,
# Evasion, Wither) all reuse existing generic skillfuncs (skill_attack,
# skill_add_condition, spell_cure_condition) and are defined as plain
# SKILLS entries in world/combat.py - no dedicated command needed. These
# seven don't fit that generic character-targeting dispatch (movement,
# NPC dialogue, a two-player pact, item inspection, a resource grant),
# so each gets its own small command instead, gated the same way -
# checking db.skills_known - rather than going through the generic
# 'skill' command (CmdUseSkill).
# ----------------------------------------------------------------------


def _knows(character, skill_name):
    return skill_name in (character.db.skills_known or [])


class CmdMarch(Command):
    """
    Cross several connected rooms in one command - Imperial Legion's
    Forced March.

    Usage:
      march <direction> <direction> [<direction> ...]

    Usable out of combat only. Up to 3 directions.
    """

    key = "march"
    help_category = "combat"

    def func(self):
        caller = self.caller
        if not _knows(caller, "forced march"):
            caller.msg("You don't know that skill.")
            return
        if caller.db.combat_turnhandler:
            caller.msg("You can't force-march in the middle of a fight.")
            return
        if not self.args:
            caller.msg("Usage: march <direction> <direction> [<direction> ...]")
            return

        directions = self.args.split()[:3]
        if (caller.db.sp or 0) < 5:
            caller.msg("You don't have the stamina (5 SP) to force-march.")
            return

        moved = 0
        for direction in directions:
            exit_obj = caller.search(direction, location=caller.location, quiet=True)
            exit_obj = exit_obj[0] if exit_obj else None
            if not exit_obj or not exit_obj.destination:
                break
            caller.execute_cmd(direction)
            moved += 1

        if moved:
            caller.db.sp -= 5
            caller.msg("|wYou push your pace, covering %d room(s) at a march.|n" % moved)
        else:
            caller.msg("There's nowhere to march that way.")


class CmdInterrogate(Command):
    """
    Extract real information from someone - Praetorian Order's
    Interrogate.

    Usage:
      interrogate <target>

    Costs 5 SP. Pulls a real, current rumor if one exists, otherwise
    tells you who's genuinely passed through this room recently.
    """

    key = "interrogate"
    help_category = "combat"

    def func(self):
        caller = self.caller
        if not _knows(caller, "interrogate"):
            caller.msg("You don't know that skill.")
            return
        if not self.args:
            caller.msg("Usage: interrogate <target>")
            return

        target = caller.search(self.args.strip())
        if not target:
            return
        if (caller.db.sp or 0) < 5:
            caller.msg("You don't have the stamina (5 SP) to press them.")
            return

        caller.db.sp -= 5

        from world.rumors import get_random_rumor_line

        rumor = get_random_rumor_line()
        recent = getattr(caller.location.db, "recent_visitors", None) or []
        if rumor and random.random() < 0.5:
            caller.msg("%s mutters: \"%s\"" % (target.key, rumor))
        elif recent:
            names = ", ".join(name for name, _ts in recent[-3:])
            caller.msg("%s admits: \"I've seen %s pass through here recently.\"" % (target.key, names))
        else:
            caller.msg("%s has nothing useful to say." % target.key)


class CmdCommune(Command):
    """
    Ask the dead one question - Orphic Mysteries' Speak with Dead.

    Usage:
      commune <ghost or corpse>

    Costs 6 SP. Works on any ghostly NPC or the recently fallen.
    """

    key = "commune"
    help_category = "combat"

    ANSWERS = [
        "\"What was taken from you will be taken from another, in time.\"",
        "\"The path you seek forks where the living fear to look.\"",
        "\"Not all debts are paid in gold, and not all payment is owed to the living.\"",
        "\"Ask again when you are less afraid of the answer.\"",
        "\"The dead remember everything you have tried to forget.\"",
    ]

    def func(self):
        caller = self.caller
        if not _knows(caller, "speak with dead"):
            caller.msg("You don't know that skill.")
            return
        if not self.args:
            caller.msg("Usage: commune <ghost or corpse>")
            return

        target = caller.search(self.args.strip())
        if not target:
            return
        if (caller.db.sp or 0) < 6:
            caller.msg("You don't have the stamina (6 SP) to commune with the dead.")
            return

        caller.db.sp -= 6
        answer = random.choice(self.ANSWERS)
        caller.location.msg_contents(
            "%s speaks a rite over %s, and a cold voice answers: %s" % (caller, target.key, answer)
        )


class CmdOath(Command):
    """
    Swear a binding pact with another player - Cult of Mithras' Oath
    Sworn.

    Usage:
      oath <character>

    While the oath holds, you and your oath-partner both gain Accuracy
    Up whenever you're in the same fight together. Attacking your own
    oath-partner breaks the oath and inflicts Defense Down on both of
    you instead.
    """

    key = "oath"
    help_category = "combat"

    def func(self):
        caller = self.caller
        if not _knows(caller, "oath sworn"):
            caller.msg("You don't know that skill.")
            return
        if not self.args:
            caller.msg("Usage: oath <character>")
            return

        target = caller.search(self.args.strip())
        if not target:
            return
        if target == caller:
            caller.msg("You can't swear an oath to yourself.")
            return

        caller.db.oath_partner = target
        target.db.oath_partner = caller
        caller.location.msg_contents(
            "%s and %s swear a binding oath before Mithras." % (caller, target)
        )


class CmdScry(Command):
    """
    Inspect an item's real properties before buying it - Cult of
    Hecate's Scrying.

    Usage:
      scry <item>

    Costs 5 SP.
    """

    key = "scry"
    help_category = "combat"

    def func(self):
        caller = self.caller
        if not _knows(caller, "scrying"):
            caller.msg("You don't know that skill.")
            return
        if not self.args:
            caller.msg("Usage: scry <item>")
            return

        item = caller.search(self.args.strip(), location=caller.location, quiet=True)
        item = item[0] if item else caller.search(self.args.strip())
        if not item:
            return
        if (caller.db.sp or 0) < 5:
            caller.msg("You don't have the stamina (5 SP) to scry it.")
            return

        caller.db.sp -= 5

        lines = ["|wYou peer into the true nature of %s:|n" % item.key]
        if item.db.price is not None:
            lines.append("  Price: %d gold" % item.db.price)
        if item.db.damage_range is not None:
            lines.append("  Damage: %d-%d" % item.db.damage_range)
        if item.db.accuracy_bonus is not None:
            lines.append("  Accuracy bonus: %d" % item.db.accuracy_bonus)
        if item.db.damage_reduction is not None:
            lines.append("  Damage reduction: %d" % item.db.damage_reduction)
        if item.db.defense_modifier is not None:
            lines.append("  Defense modifier: %d" % item.db.defense_modifier)
        if len(lines) == 1:
            lines.append("  It holds no secrets worth seeing.")

        caller.msg("\n".join(lines))


class CmdRequisition(Command):
    """
    Demand supply from a Legion-aligned contact - Imperial Legion's
    Requisition.

    Usage:
      requisition

    Once per real day. Requires a Legion-aligned NPC in the room.
    """

    key = "requisition"
    help_category = "combat"

    AMOUNT = 15
    COOLDOWN = 86400

    def func(self):
        caller = self.caller
        if not _knows(caller, "requisition"):
            caller.msg("You don't know that skill.")
            return

        import time

        last = caller.db.requisition_last_used or 0
        if time.time() - last < self.COOLDOWN:
            caller.msg("You've already requisitioned supply recently - try again later.")
            return

        contact = None
        for obj in caller.location.contents:
            if obj.tags.get("legion_aligned", category="npc_role"):
                contact = obj
                break
        if not contact:
            caller.msg("There's no one here aligned with the Legion to requisition from.")
            return

        caller.db.gold = (caller.db.gold or 0) + self.AMOUNT
        caller.db.requisition_last_used = time.time()
        caller.msg(
            "%s hands over %d gold in supply, no questions asked." % (contact.key, self.AMOUNT)
        )


class CmdSafehouse(Command):
    """
    Call in a sympathizer's help to recover - Hellenic Resistance's
    Safehouse.

    Usage:
      safehouse

    Once per real day, out of combat only. Fully restores HP/MP/SP.
    """

    key = "safehouse"
    help_category = "combat"

    COOLDOWN = 86400

    def func(self):
        caller = self.caller
        if not _knows(caller, "safehouse"):
            caller.msg("You don't know that skill.")
            return
        if caller.db.combat_turnhandler:
            caller.msg("There's no time for that in the middle of a fight.")
            return

        import time

        last = caller.db.safehouse_last_used or 0
        if time.time() - last < self.COOLDOWN:
            caller.msg("You've already called on a sympathizer recently - try again later.")
            return

        caller.db.hp = caller.db.max_hp
        caller.db.mp = caller.db.max_mp
        caller.db.sp = caller.db.max_sp
        caller.db.safehouse_last_used = time.time()
        caller.msg("A sympathizer hides you away just long enough to patch you up fully.")
