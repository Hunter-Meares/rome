"""
The bounty board - a repeatable "kill X" objective system, the first
of the two systems requested (bounties, then quests) to give players a
clearer default answer than open-ended grinding.

Design, per direct discussion before any of this was built:
  - Kill-only for v1 (no fetch/item objectives yet - those need a
    clean pool of "fetchable" items to draw from, which doesn't exist
    yet).
  - Personal board: every character has their own independent bounty
    state (db.active_bounty), not a shared/contested board. No claim
    or expiry logic needed - "regeneration" is just accepting a new
    one whenever you're ready.
  - A real, physical board object (BountyBoard, placed near the
    Forum's Rostra - the actual historical spot Romans posted public
    notices) rather than a command usable from anywhere.
  - Completing the required kill count does NOT auto-pay out - you
    return to the board and 'bounty turnin' to collect, giving the
    board (and the trip there) recurring relevance rather than a
    silent background counter.
  - Party-aware: progress is credited to every character in the
    defeated NPC's damage_log (the same population that already
    splits XP/gold fairly on a group kill - see CombatRules.at_defeat)
    who individually has a matching active bounty, not just whoever
    landed the killing blow. A party hunting bounties together also
    separately gets the new PARTY_XP_BONUS_PERCENT bonus on the kill's
    own ordinary combat XP (world/combat.py) - the two systems compose
    for free, no special-casing needed between them.

Targets are drawn exclusively from the Cloaca Maxima's sewer_npc
roster (world/prototypes.py) - deliberately NOT the Colosseum/Ludus
trainers or Deeper Sands Arena Fighters, which are consensual training/
sport content, not "wanted criminal" fare. The sewers were already
built with exactly this theme (deserters, footpads, bandits, cultists,
smugglers), so it's a natural fit requiring zero new content. The
Drowned Sentinel (boss) is deliberately excluded - too rare/special
for a repeatable board target.

A target is identified by its stable display `key` (e.g. "a runaway
slave" - already a literal field on every prototype dict, needed for
the game anyway) rather than Evennia's spawn-prototype tag machinery.
A `prototype_key`-based approach was tried first and seemed like the
more "correct" mechanism (matching world/economy.py's own documented
convention for identifying a spawned object's origin) - but a direct
test against Evennia's real spawner (see world/tests_bounties.py's
TestRealPrototypeTagMatching, still kept as a regression guard even
though the underlying assumption turned out wrong) proved that
`prototype_key` is never actually injected into these dicts when
`spawn()` is given the raw dict object directly (as every sewer NPC's
setup script does), rather than a string looked up through Evennia's
own prototype registry. Matching on `key` instead sidesteps that
internal machinery entirely, using an identifier this file already
controls directly and that nothing in the game ever renames on a
hostile NPC.
"""

import random

from evennia import Command, DefaultObject

import world.prototypes as protos
from world.combat import GOLD_PER_XP_DIVISOR

# Bonus applied on top of what the kills themselves already grant via
# ordinary combat XP - the bounty is a real, additional incentive to
# hunt a specific target down, not just a renamed copy of XP you'd
# earn anyway. Paid out as a single lump sum at turn-in, not split by
# damage share (unlike ordinary combat XP/gold) - a bounty is "your"
# personal job once accepted, tracked per-contributor to the actual
# kills that complete it.
BOUNTY_XP_MULTIPLIER = 0.75

BOUNTY_TIERS = {
    "novice": {
        "level_range": (1, 10),
        "count_range": (3, 5),
        "targets": [
            (protos.SEWER_LUDUS_RUNAWAY, "runaway slaves"),
            (protos.SEWER_SUBURA_FOOTPAD, "Subura footpads"),
            (protos.SEWER_FORUM_DESERTER, "deserting legionaries"),
            (protos.SEWER_GANG_THUG, "territorial gang thugs"),
            (protos.SEWER_GANG_SCOUT, "rival gang scouts"),
            (protos.SEWER_CLOACA_BANDIT, "Cloaca bandits"),
        ],
    },
    "veteran": {
        "level_range": (11, 18),
        "count_range": (3, 4),
        "targets": [
            (protos.SEWER_HECATE_CULTIST, "cultists of Hecate"),
            (protos.SEWER_VIGILES_FUGITIVE, "fugitives of the Vigiles"),
            (protos.SEWER_SMUGGLER, "sewer smugglers"),
            (protos.SEWER_FERAL_MUTANT, "feral sewer mutants"),
            (protos.SEWER_MINOTAUR_GLADIATOR, "Minotaur gladiators"),
            (protos.SEWER_SETTLEMENT_GUARD, "settlement guards"),
        ],
    },
    "champion": {
        "level_range": (19, 100),
        "count_range": (2, 3),
        "targets": [
            (protos.SEWER_SETTLEMENT_ENFORCER, "settlement enforcers"),
            (protos.SEWER_CYCLOPS_BARBARIAN, "feral Cyclopes"),
            (protos.SEWER_NYMPH_AUGUR, "Nymph augurs"),
            (protos.SEWER_CISTERN_LURKER, "cistern lurkers"),
        ],
    },
}


def _tier_for_level(level):
    for tier_name, tier_data in BOUNTY_TIERS.items():
        low, high = tier_data["level_range"]
        if low <= level <= high:
            return tier_name, tier_data
    # Above every defined range (shouldn't happen given "champion" caps
    # at 100) - fail safe to champion rather than crash.
    return "champion", BOUNTY_TIERS["champion"]


def roll_bounty(character):
    """
    Rolls a fresh bounty for this character, tiered to their own
    level - no menu, matches the "simple" ask. Returns the new bounty
    dict; does not assign it to the character (CmdBounty does that).
    """
    level = character.db.level or 1
    tier_name, tier_data = _tier_for_level(level)
    target_dict, display_name = random.choice(tier_data["targets"])
    count_required = random.randint(*tier_data["count_range"])

    base_xp = target_dict.get("xp_reward", 0)
    xp_reward = max(1, int(round(count_required * base_xp * BOUNTY_XP_MULTIPLIER)))
    gold_reward = max(1, xp_reward // GOLD_PER_XP_DIVISOR)

    return {
        "tier": tier_name,
        "target_key": target_dict["key"],
        "target_display": display_name,
        "count_required": count_required,
        "count_progress": 0,
        "xp_reward": xp_reward,
        "gold_reward": gold_reward,
    }


def credit_bounty_progress(defeated):
    """
    Called from CombatRules.at_defeat alongside the existing XP/gold/
    loot hooks (a local import there, matching how world/loot.py's
    roll_loot_drop is already wired in - avoids a circular import,
    since this module imports from world.combat itself).

    Checks the defeated NPC's stable display key against every
    contributor in its damage_log - the same population that already
    splits ordinary combat XP/gold fairly on a group kill - crediting
    1 point of progress to anyone with a matching active bounty.
    """
    damage_log = defeated.db.damage_log or {}
    for contributor in damage_log:
        # See gotcha #2 in CLAUDE.md: a deleted object's reference,
        # reloaded from a persisted attribute, resolves to literal
        # None - not an object with pk=None.
        if contributor is None or not contributor.pk:
            continue

        bounty = contributor.db.active_bounty
        if not bounty or bounty.get("target_key") != defeated.key:
            continue
        if bounty["count_progress"] >= bounty["count_required"]:
            continue  # already complete, just waiting on turn-in

        bounty["count_progress"] += 1
        contributor.db.active_bounty = bounty

        if bounty["count_progress"] >= bounty["count_required"]:
            contributor.msg(
                "|YBounty complete: %s (%d/%d). Return to the bounty board to "
                "collect your reward.|n"
                % (bounty["target_display"], bounty["count_progress"], bounty["count_required"])
            )
        else:
            contributor.msg(
                "|yBounty progress: %s (%d/%d).|n"
                % (bounty["target_display"], bounty["count_progress"], bounty["count_required"])
            )


class BountyBoard(DefaultObject):
    """
    A real, physical bounty board - see CmdBounty for the actual
    interaction. Deliberately not typeclasses.objects.Object (its
    fix is only for the "the X" article-insertion bug on objects with
    a key literally starting with "the" - this board's own key
    doesn't, so the plain base is fine, matching how NPCMerchant
    itself is just a bare DefaultCharacter subclass with no extra
    scenery-fix mixin needed).
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.locks.add("get:false()")


class CmdBounty(Command):
    """
    Check, accept, turn in, or abandon a bounty at a real bounty board.

    Usage:
      bounty
      bounty accept
      bounty turnin
      bounty abandon

    Use this while standing at a real bounty board. With no active
    bounty, 'bounty accept' (or just 'bounty') rolls you a fresh one,
    matched to your own level - hunt down the stated number of a
    specific kind of hostile in the Cloaca Maxima, then come back here
    and 'bounty turnin' to collect your reward. Completing the kill
    count doesn't pay out by itself - you have to actually report back.

    'bounty abandon' gives up your current bounty with no penalty, if
    you'd rather roll a different one.

    A real party sharing credit toward the same kill also splits the
    fight's own ordinary combat XP with a party bonus on top (see
    'help groupcombat') - the two rewards stack, they're not the same
    thing.
    """

    key = "bounty"
    aliases = ["bounties"]
    help_category = "general"

    def func(self):
        caller = self.caller
        boards = [
            obj for obj in caller.location.contents
            if obj.is_typeclass(BountyBoard, exact=False)
        ]
        if not boards:
            caller.msg("There's no bounty board here.")
            return

        arg = self.args.strip().lower()
        bounty = caller.db.active_bounty

        if arg in ("", "check"):
            if not bounty:
                caller.msg("You have no active bounty. Use 'bounty accept' to take one.")
                return
            status = (
                "|Gcomplete - use 'bounty turnin'!|n"
                if bounty["count_progress"] >= bounty["count_required"]
                else "in progress"
            )
            caller.msg(
                "|wCurrent bounty:|n defeat %d %s (%d/%d) - %s\n"
                "Reward: %d gold, %d XP."
                % (
                    bounty["count_required"], bounty["target_display"],
                    bounty["count_progress"], bounty["count_required"], status,
                    bounty["gold_reward"], bounty["xp_reward"],
                )
            )
        elif arg == "accept":
            if bounty:
                caller.msg(
                    "You already have an active bounty. Use 'bounty abandon' "
                    "first if you want a different one."
                )
                return
            new_bounty = roll_bounty(caller)
            caller.db.active_bounty = new_bounty
            caller.msg(
                "|YNew bounty:|n defeat %d %s. Reward: %d gold, %d XP."
                % (
                    new_bounty["count_required"], new_bounty["target_display"],
                    new_bounty["gold_reward"], new_bounty["xp_reward"],
                )
            )
        elif arg == "turnin":
            if not bounty:
                caller.msg("You have no active bounty.")
                return
            if bounty["count_progress"] < bounty["count_required"]:
                caller.msg(
                    "You haven't finished this bounty yet (%d/%d)."
                    % (bounty["count_progress"], bounty["count_required"])
                )
                return
            from world.combat import COMBAT_RULES

            caller.db.gold = (caller.db.gold or 0) + bounty["gold_reward"]
            caller.msg("|Y+%d gold.|n" % bounty["gold_reward"])
            COMBAT_RULES.award_xp(caller, bounty["xp_reward"])
            caller.db.active_bounty = None
            caller.msg("|GBounty complete! You've collected your reward.|n")
        elif arg == "abandon":
            if not bounty:
                caller.msg("You have no active bounty to abandon.")
                return
            caller.db.active_bounty = None
            caller.msg("You abandon your current bounty.")
        else:
            caller.msg("Usage: bounty | bounty accept | bounty turnin | bounty abandon")
