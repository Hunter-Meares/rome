"""
Player crafting recipes for evennia.contrib.game_systems.crafting
(world/gathering.py is the other half of this system - raw materials
feed the recipes here). CRAFT_RECIPE_MODULES = ["world.recipes"] in
server/conf/settings.py registers every top-level recipe class
defined in this module - see that contrib's own README for the
exact mechanics (a recipe declares tool_tags/consumable_tags, the
`craft` command matches inventory items against those tags).

First profession built end-to-end: Faber (smith) - promoted ahead of
the crafting design discussion's original "build Textor first, not
Faber" recommendation, which was specifically about Faber's ore
needing frontier-safe gathering that didn't exist yet. That blocker
is resolved in this same pass (see world/gathering.py's docstring on
the new Ore Vein Shaft), and Faber has the strongest cross-demand
with combat players of any profession in the original design doc, a
real reason to build it first once nothing was actually blocking it.

Skill progression (SkilledCraftingRecipe): a per-character crafting
skill (db.craft_skill, a dict keyed by profession, 0-100) gates each
recipe's success chance. A failed attempt keeps its materials
(consume_on_fail stays at the contrib's own default, False) and
still grants a small amount of skill progress - a direct design
requirement, so a solo player grinding alone never walks away from a
failed attempt with literally nothing to show for it.

Leveling parity (explicit design requirement, see rome_mud_todo.md's
crafting section for the full math): a crafted item's reward is
priced and XP-rewarded from the SAME real numbers combat already
uses - xp_for_level() and GOLD_PER_XP_DIVISOR - rather than a
separately hand-tuned number, so combat and crafting stay
comparably fast per real minute invested rather than drifting apart
as new recipes get added. The reward is paid entirely on SALE (see
world/economy.py's node_confirm_sell reading db.craft_xp), not on
gathering or crafting - gathering and crafting are the labor, selling
is the payoff, matching the real economic shape of the loop.
"""

from random import randint

from evennia.contrib.game_systems.crafting import CraftingRecipe

# Real, confirmed bug found live: the crafting contrib's own recipe
# auto-discovery (_load_recipes(), triggered by settings.CRAFT_RECIPE_
# MODULES) scans EVERY public top-level CALLABLE genuinely defined in
# this module, not just classes, despite its README describing "all
# top-level classes" - a plain function crashes it outright
# (AttributeError: 'function' object has no attribute 'mro', since it
# unconditionally calls inherits_from() on each one before checking
# it's even a class). Confirmed via evennia.utils.utils.
# callables_from_module's own docstring/source: it filters by
# get_module(obj) == this module (so an IMPORT like `from random
# import randint` is safe, its __module__ points elsewhere) and by a
# leading underscore - which is why _craft_reward below is prefixed,
# not because it's "private" by convention. Any future top-level
# helper function added to a CRAFT_RECIPE_MODULES file needs the same
# underscore prefix, or the entire in-game 'craft' command breaks the
# moment anyone uses it.
CRAFT_SKILL_CAP = 100

# How much of a level's own xp_for_level() a full gather-craft-sell
# cycle should be worth per real minute it takes - see rome_mud_
# todo.md's crafting section: derived from combat's own
# PVP_XP_REWARD_PERCENT (0.06 per same-level kill, ~2 assumed real
# minutes per kill), so ~0.03 per minute is the target rate for ANY
# non-combat activity to match combat's own pace, not a separately
# guessed number.
CRAFT_XP_PERCENT_PER_MINUTE = 0.03


def _craft_reward(level, cycle_minutes):
    """
    (craft_xp, price) for an item that takes `cycle_minutes` of real
    play (gather + craft + travel to sell) to produce, at `level`.
    `price` is set so that selling at an ordinary Rome merchant
    (distance_bonus 1.0) nets exactly the same gold an NPC kill of
    this level would pay for equivalent real time - see world/
    economy.py's node_confirm_sell for the actual sale math
    (price * SELL_BACK_RATE * distance_bonus), and GOLD_PER_XP_
    DIVISOR for the same xp-to-gold ratio every NPC kill already uses.
    """
    from world.combat import COMBAT_RULES, GOLD_PER_XP_DIVISOR
    from world.economy import SELL_BACK_RATE

    craft_xp = max(1, round(cycle_minutes * CRAFT_XP_PERCENT_PER_MINUTE * COMBAT_RULES.xp_for_level(level)))
    target_net_gold = max(1, craft_xp // GOLD_PER_XP_DIVISOR)
    price = max(1, round(target_net_gold / SELL_BACK_RATE))
    return craft_xp, price


class SkilledCraftingRecipe(CraftingRecipe):
    """
    Shared skill-check parent for every profession's recipes. A
    subclass sets `difficulty` (roughly 0-100, matching the skill
    scale) and `skill_key` (which entry of db.craft_skill this recipe
    trains and checks).
    """

    difficulty = 0
    skill_key = None

    def _skill(self):
        return (self.crafter.db.craft_skill or {}).get(self.skill_key, 0)

    def _train(self, amount):
        skills = self.crafter.db.craft_skill or {}
        skills[self.skill_key] = min(CRAFT_SKILL_CAP, skills.get(self.skill_key, 0) + amount)
        self.crafter.db.craft_skill = skills

    def do_craft(self, **kwargs):
        skill = self._skill()
        # A middling crafter (skill == difficulty) succeeds half the
        # time; skill above/below the recipe's difficulty shifts that
        # up or down, clamped so it's never a sure thing or hopeless.
        chance = max(5, min(95, 50 + (skill - self.difficulty)))
        if randint(1, 100) <= chance:
            self._train(3)
            return super().do_craft(**kwargs)

        # Failure keeps the materials (consume_on_fail is False by
        # default) but still counts for something - a real design
        # requirement, so a solo player grinding alone never walks
        # away from a failed attempt with nothing to show for it.
        self._train(1)
        self.msg(
            "|rThe attempt doesn't come together this time - you'll need "
            "more practice with this (skill: %d/%d).|n" % (self._skill(), CRAFT_SKILL_CAP)
        )
        return None


class IronShortswordRecipe(SkilledCraftingRecipe):
    """
    A basic, honest weapon - Faber's first real recipe. Level and
    cycle-time assumptions (8, 5 minutes: gather ore and timber, walk
    to the Smithy, craft, sell) are stated explicitly here since
    _craft_reward() has no other way to know them - see that function
    and rome_mud_todo.md for why 5 minutes/0.03 per minute is the
    working target rather than a guess with no basis.
    """

    name = "iron shortsword"
    skill_key = "faber"
    difficulty = 10

    # Deliberately just 1 of each, not 2 ore - two real reasons found
    # live, not just a simplification: (1) iron ore has a ~24h
    # per-character cooldown, so requiring 2 would mean a genuinely
    # new player waits TWO DAYS before their very first craft attempt
    # is even possible, badly breaking the 5-minute cycle-time
    # assumption _craft_reward's whole parity math is built on; (2) a
    # real, confirmed Evennia limitation - two objects sharing the
    # exact same display key ("a chunk of iron ore") can't reliably
    # both be referenced in one 'craft ... from iron ore, iron ore,
    # ...' command (CmdCraft's own ingredient search isn't disambig-
    # uation-aware the way a player-facing 'get' command might be),
    # so a duplicate-material recipe would have silently failed for a
    # real player with 2 identical ore chunks, not just been slow.
    consumable_tags = ["iron_ore", "timber"]
    consumable_names = ["iron ore", "timber"]
    output_prototypes = ["CRAFTED_IRON_SHORTSWORD"]

    success_message = "|gYou hammer the ore into shape and fit a timber grip - a real iron shortsword, plain but sound.|n"

    ITEM_LEVEL = 8
    CYCLE_MINUTES = 5

    def do_craft(self, **kwargs):
        result = super().do_craft(**kwargs)
        if not result:
            return result

        from world.combat import compute_weapon_stats

        damage_range, accuracy_bonus, _shop_price = compute_weapon_stats("gladius", self.ITEM_LEVEL)
        craft_xp, price = _craft_reward(self.ITEM_LEVEL, self.CYCLE_MINUTES)

        for obj in result:
            obj.db.damage_range = damage_range
            obj.db.accuracy_bonus = accuracy_bonus
            obj.db.item_level = self.ITEM_LEVEL
            obj.db.price = price
            obj.db.craft_xp = craft_xp

        return result
