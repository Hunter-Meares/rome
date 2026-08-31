"""
Post-chargen stat growth

Every 3rd level (levels 3, 6, 9, ... up to MAX_LEVEL) grants one unspent
stat point (world/combat.py's award_xp, in the level-up loop). Spend it
with 'statup' on any of the four core stats (up to a per-stat cap - see
stat_cap() below) or convert it into a flat HP/MP/SP boost instead -
available as a genuine parallel choice from the very first point, not
only after a stat maxes out, per direct request.

Why agilitas is capped far tighter than the other three: get_attack()
multiplies (agilitas - 10) by ACCURACY_STAT_MULTIPLIER (7) directly
onto the d100 attack roll. At today's chargen-only ceiling of 16
(base 10 + up to +3 race + up to +3 class), that's already a +42
bonus - calibrated on purpose to hit a weak defender ~90%+ of the
time, not 100%. A weak defender's defense_value sits around 50, so an
attacker's flat accuracy bonus alone reaching that threshold makes
every hit guaranteed regardless of the roll - and that threshold is
only about 1-2 agilitas points above today's ceiling. Virtus, ingenium,
and vigor use much gentler formulas ((stat-10)//2 for damage,
(stat-10)//3 for damage reduction, a flat +1 for max_mp/max_hp) and
have real headroom; agilitas does not. Verified with the real numbers
before picking a cap, not guessed.

Per-race caps for the other three stats are derived directly from
world.chargen_menu.RACES' existing stat_mods, rather than a separately
hand-maintained table - a race that already leans +2/+3 into a stat at
chargen (Minotaur/Cyclops -> virtus, Nymph/Harpy -> ingenium, Cyclops
-> vigor) gets a higher lifetime ceiling on that same stat, extending
an identity that's already established rather than inventing a new,
independent balancing axis.
"""

from world.chargen_menu import RACES
from commands.command import Command

AGILITAS_CAP = 18
STAT_CAP_BASE = 20
STAT_CAP_BONUS = 22
RACIAL_LEAN_THRESHOLD = 2

RESOURCE_HP_GAIN = 10
RESOURCE_MP_GAIN = 5
RESOURCE_SP_GAIN = 5

CORE_STATS = ("virtus", "agilitas", "ingenium", "vigor")
RESOURCE_OPTIONS = {
    "hp": ("max_hp", RESOURCE_HP_GAIN),
    "mp": ("max_mp", RESOURCE_MP_GAIN),
    "sp": ("max_sp", RESOURCE_SP_GAIN),
}


def stat_cap(character, stat_name):
    """Returns the lifetime cap for one of character's core stats,
    accounting for their race's existing chargen lean."""
    if stat_name == "agilitas":
        return AGILITAS_CAP

    race_key = character.db.race
    race_data = RACES.get(race_key, {})
    lean = race_data.get("stat_mods", {}).get(stat_name, 0)
    return STAT_CAP_BONUS if lean >= RACIAL_LEAN_THRESHOLD else STAT_CAP_BASE


def grant_level_up_point(character):
    """Called from world/combat.py's award_xp on every 3rd level."""
    character.db.unspent_stat_points = (character.db.unspent_stat_points or 0) + 1
    character.msg(
        "|yYou feel a new capacity within you - use 'statup' to spend a "
        "stat point.|n"
    )


class CmdStatUp(Command):
    """
    Spend an unspent stat point, earned every 3rd level.

    Usage:
      statup              - show your unspent points, current stats,
                             and your race's caps
      statup <stat>       - virtus, agilitas, ingenium, or vigor
      statup hp|mp|sp     - a flat resource boost instead of a core
                             stat - a real, always-available choice,
                             not just a fallback once a stat is capped

    Every core stat has a lifetime cap - agilitas caps at 18 for every
    race (accuracy math breaks down past that point); virtus, ingenium,
    and vigor cap at 20, or 22 if that's already your race's
    established specialty stat.
    """

    key = "statup"
    help_category = "combat"

    def func(self):
        caller = self.caller
        points = caller.db.unspent_stat_points or 0

        if not self.args:
            lines = ["|wUnspent stat points:|n %d" % points, "", "|wCurrent stats and caps:|n"]
            for stat in CORE_STATS:
                current = getattr(caller.db, stat) or 10
                lines.append("  %s: %d / %d" % (stat.title(), current, stat_cap(caller, stat)))
            lines.append("")
            lines.append(
                "Or convert a point into +%d max HP, +%d max MP, or +%d max SP "
                "instead - 'statup hp', 'statup mp', 'statup sp'."
                % (RESOURCE_HP_GAIN, RESOURCE_MP_GAIN, RESOURCE_SP_GAIN)
            )
            caller.msg("\n".join(lines))
            return

        if points < 1:
            caller.msg("You don't have any unspent stat points.")
            return

        choice = self.args.strip().lower()

        if choice in RESOURCE_OPTIONS:
            attr, gain = RESOURCE_OPTIONS[choice]
            current = getattr(caller.db, attr) or 0
            setattr(caller.db, attr, current + gain)
            caller.db.unspent_stat_points = points - 1
            caller.msg("|gYou gain %d %s!|n" % (gain, attr.replace("max_", "max ").upper()))
            return

        if choice in CORE_STATS:
            cap = stat_cap(caller, choice)
            current = getattr(caller.db, choice) or 10
            if current >= cap:
                caller.msg(
                    "Your %s is already at its cap (%d) for your race - "
                    "spend this point elsewhere." % (choice.title(), cap)
                )
                return
            setattr(caller.db, choice, current + 1)
            caller.db.unspent_stat_points = points - 1
            caller.msg("|gYour %s increases to %d!|n" % (choice.title(), current + 1))
            return

        caller.msg("Usage: statup <virtus|agilitas|ingenium|vigor|hp|mp|sp>")
