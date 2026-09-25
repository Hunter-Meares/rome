"""
Player crafting recipes for evennia.contrib.game_systems.crafting
(world/gathering.py is the other half of this system - raw materials
feed the recipes here; world/craft_commands.py is the third half - the
player-facing commands, deliberately NOT the contrib's own CmdCraft).
CRAFT_RECIPE_MODULES = ["world.recipes"] in server/conf/settings.py
registers every top-level recipe class defined in this module - see
that contrib's own README for the exact mechanics (a recipe declares
tool_tags/consumable_tags; ingredients are matched by Tag, not name).

First profession built end-to-end: Faber (smith - Latin for
"craftsman"/"maker," the root of "fabricate") - promoted ahead of the
crafting design discussion's original "build Textor first, not Faber"
recommendation, which was specifically about Faber's ore needing
frontier-safe gathering that didn't exist yet. That blocker is
resolved (see world/gathering.py's docstring on the new Ore Vein
Shaft), and Faber has the strongest cross-demand with combat players
of any profession in the original design doc, a real reason to build
it first once nothing was actually blocking it.

Skill progression (SkilledCraftingRecipe): a per-character crafting
skill (db.craft_skill, a dict keyed by profession, 0-100) gates each
recipe's success chance. A failed attempt keeps its materials
(consume_on_fail stays at the contrib's own default, False) and
still grants a small amount of skill progress - a direct design
requirement, so a solo player grinding alone never walks away from a
failed attempt with literally nothing to show for it.

REWARD MODEL - a real design correction, made from direct user
feedback, worth recording in full since it reverses an earlier
decision in this same file's own history: the reward was originally
scaled to the CRAFTER's own level (fixing an even earlier bug where
it was a flat number forever). Both of those were wrong in the same
way - tying reward to WHO crafts something, rather than to WHAT is
being crafted. The correct analogy, pointed out directly: an NPC's
own xp_reward is a FIXED property of that NPC, set once from ITS OWN
level at spawn time - a level 100 character killing a level 5 NPC
gets the exact same small reward a level 5 character would, not more.
Reward-scales-with-attacker-level was never how combat worked at all.
Tying craft reward to the crafter's level let a high-level character
spam the easiest recipe forever for a reward meant for their level,
exactly the exploit combat's own design already avoids. Fixed by
giving every recipe a fixed TIER_LEVEL (its own inherent difficulty,
like an NPC's own level) that drives BOTH its reward and its item's
power - a low recipe always pays a low, fixed reward to anyone, and
the only way to earn more is to progress to a harder recipe, exactly
mirroring how a player has to fight higher-level content for better
XP rather than farming trivial enemies forever.

Leveling-parity math itself (see rome_mud_todo.md's crafting section)
is unchanged: a recipe's TIER_LEVEL plugs into the same xp_for_level()/
GOLD_PER_XP_DIVISOR formulas an NPC kill already uses, so a tier-N
recipe pays what fighting a level-N NPC for the same real time would.
Reaching level 100 via crafting now requires moving through the tier
ladder as combat's own zones would require moving to harder content -
not scaling one recipe forever. The reward is paid entirely on SALE
(world/economy.py's node_confirm_sell, reading db.craft_xp), not on
gathering or crafting itself.

RECIPE ACCESS: KNOWN_BY_DEFAULT = True (the tier-1 recipe only) needs
no training and no gold - a genuinely broke, non-combat character can
attempt it the moment they've gathered materials, closing what would
otherwise be a real chicken-and-egg problem (needing gold to learn
crafting, but needing crafting to get gold without fighting). Every
higher tier needs to be learned from a CraftTrainer (world/
craft_commands.py's `learnrecipe`) for gold funded by tier-1 proceeds,
mirroring how learnspell/learnskill already require an in-person
trainer plus gold - crafting was the one teachable system in the game
without that gate until now.
"""

from random import randint

from evennia.contrib.game_systems.crafting import CraftingRecipe, CraftingValidationError

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
# leading underscore - which is why every helper FUNCTION below is
# prefixed, not because it's "private" by convention. A plain list
# like ALL_RECIPES further down is safe unprefixed (callable() is
# False for a list), but any future top-level helper FUNCTION added
# to a CRAFT_RECIPE_MODULES file needs the same underscore prefix, or
# the entire in-game 'craft' command breaks the moment anyone uses it.
CRAFT_SKILL_CAP = 100

# How much of a level's own xp_for_level() a full gather-craft-sell
# cycle should be worth per real minute it takes - see rome_mud_
# todo.md's crafting section: derived from combat's own
# PVP_XP_REWARD_PERCENT (0.06 per same-level kill, ~2 assumed real
# minutes per kill), so ~0.03 per minute is the target rate for ANY
# non-combat activity to match combat's own pace, not a separately
# guessed number.
CRAFT_XP_PERCENT_PER_MINUTE = 0.03


def _craft_reward(tier_level, cycle_minutes):
    """
    (craft_xp, price) for a recipe of fixed difficulty `tier_level`
    that takes `cycle_minutes` of real play (gather + craft + travel
    to sell) to produce - a property of the RECIPE, not of whoever
    crafts it (see this module's own docstring for why). `price` is
    set so that selling at an ordinary Rome merchant (distance_bonus
    1.0) nets exactly the same gold an NPC kill of this level would
    pay for equivalent real time - see world/economy.py's
    node_confirm_sell for the actual sale math (price *
    SELL_BACK_RATE * distance_bonus), and GOLD_PER_XP_DIVISOR for the
    same xp-to-gold ratio every NPC kill already uses.
    """
    from world.combat import COMBAT_RULES, GOLD_PER_XP_DIVISOR
    from world.economy import SELL_BACK_RATE

    craft_xp = max(1, round(cycle_minutes * CRAFT_XP_PERCENT_PER_MINUTE * COMBAT_RULES.xp_for_level(tier_level)))
    target_net_gold = max(1, craft_xp // GOLD_PER_XP_DIVISOR)
    price = max(1, round(target_net_gold / SELL_BACK_RATE))
    return craft_xp, price


def _recipe_learn_cost(tier_level):
    """Gold cost to learn a recipe above tier 1 - mirrors world/
    combat.py's compute_learn_cost's own "price scales with power"
    shape exactly, for the same reason (a flat fee would undersell how
    much stronger a high-tier recipe actually is)."""
    return 20 + tier_level * 3


class SkilledCraftingRecipe(CraftingRecipe):
    """
    Shared skill-check parent for every profession's recipes.

    Class attributes a concrete recipe sets:
      - skill_key: which entry of db.craft_skill this recipe trains
        and checks (e.g. "faber").
      - difficulty: roughly 0-100, matching the skill scale - how hard
        THIS recipe is to succeed at.
      - TIER_LEVEL: this recipe's own fixed difficulty/tier, driving
        both its reward (_craft_reward) and its item's power - see
        this module's own docstring for why this is a property of the
        recipe, never of the crafter.
      - CYCLE_MINUTES: real-world minutes this recipe is assumed to
        take, feeding the same reward formula.
      - KNOWN_BY_DEFAULT: True for the one free, untrained starting
        recipe per profession; False for anything that needs
        `learnrecipe` first (world/craft_commands.py).
    """

    difficulty = 0
    skill_key = None
    TIER_LEVEL = 1
    CYCLE_MINUTES = 5
    KNOWN_BY_DEFAULT = True

    def _skill(self):
        return (self.crafter.db.craft_skill or {}).get(self.skill_key, 0)

    def _train(self, amount):
        skills = self.crafter.db.craft_skill or {}
        skills[self.skill_key] = min(CRAFT_SKILL_CAP, skills.get(self.skill_key, 0) + amount)
        self.crafter.db.craft_skill = skills

    def knows_recipe(self):
        return self.KNOWN_BY_DEFAULT or self.name in (self.crafter.db.craft_recipes_known or set())

    def pre_craft(self, **kwargs):
        # Checked here too, not just in world/craft_commands.py's
        # CmdSimpleCraft (defense in depth - anything that ever calls
        # this recipe directly, now or later, gets the same gate).
        if not self.knows_recipe():
            self.msg("You haven't learned how to make %s yet - find a trainer." % self.name)
            raise CraftingValidationError
        return super().pre_craft(**kwargs)

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


class FaberWeaponRecipe(SkilledCraftingRecipe):
    """Shared reward/stat tail for every Faber WEAPON recipe. A
    subclass sets WEAPON_TYPE to a real world.combat.WEAPON_SUBTYPES
    key - everything else (damage/accuracy/price/craft_xp) is computed
    from that plus the recipe's own fixed TIER_LEVEL, the same formula
    a merchant's own stock already uses."""

    skill_key = "faber"
    WEAPON_TYPE = None

    def do_craft(self, **kwargs):
        result = super().do_craft(**kwargs)
        if not result:
            return result

        from world.combat import compute_weapon_stats

        damage_range, accuracy_bonus, _shop_price = compute_weapon_stats(self.WEAPON_TYPE, self.TIER_LEVEL)
        craft_xp, price = _craft_reward(self.TIER_LEVEL, self.CYCLE_MINUTES)

        for obj in result:
            obj.db.damage_range = damage_range
            obj.db.accuracy_bonus = accuracy_bonus
            obj.db.item_level = self.TIER_LEVEL
            obj.db.price = price
            obj.db.craft_xp = craft_xp
            obj.db.item_category = "weapon"

        return result


class FaberArmorRecipe(SkilledCraftingRecipe):
    """Shared reward/stat tail for every Faber ARMOR recipe - same
    shape as FaberWeaponRecipe above, using compute_armor_stats
    instead. A subclass sets ARMOR_CATEGORY to "light"/"medium"/
    "heavy" (world.combat.ARMOR_CATEGORIES)."""

    skill_key = "faber"
    ARMOR_CATEGORY = None

    def do_craft(self, **kwargs):
        result = super().do_craft(**kwargs)
        if not result:
            return result

        from world.combat import compute_armor_stats

        reduction, defense_modifier, _shop_price = compute_armor_stats(self.ARMOR_CATEGORY, self.TIER_LEVEL)
        craft_xp, price = _craft_reward(self.TIER_LEVEL, self.CYCLE_MINUTES)

        for obj in result:
            obj.db.damage_reduction = reduction
            obj.db.defense_modifier = defense_modifier
            obj.db.item_level = self.TIER_LEVEL
            obj.db.price = price
            obj.db.craft_xp = craft_xp
            obj.db.item_category = "armor"

        return result


class IronShortswordRecipe(FaberWeaponRecipe):
    """
    Tier 1 - Faber's free, untrained starting recipe. Anyone can
    attempt this the moment they've gathered materials, no gold or
    trainer needed - see this module's own docstring on why the
    starting recipe of each profession has to work this way.
    """

    name = "iron shortsword"
    difficulty = 10
    TIER_LEVEL = 8
    WEAPON_TYPE = "gladius"
    KNOWN_BY_DEFAULT = True

    # Deliberately just 1 of each, not 2 ore - two real reasons found
    # live: (1) iron ore has a ~24h per-character cooldown, so
    # requiring 2 would mean a genuinely new player waits TWO DAYS
    # before their very first craft attempt is even possible; (2) the
    # ordinary crafting command used to parse ingredients by NAME
    # (Evennia's own text search), and two objects sharing an
    # identical display key aren't reliably both addressable that way
    # - moot now that world/craft_commands.py's CmdSimpleCraft
    # collects matching inventory objects directly rather than
    # searching by name, but tier 1 stays minimal regardless.
    consumable_tags = ["iron_ore", "timber"]
    consumable_names = ["iron ore", "timber"]
    output_prototypes = ["CRAFTED_IRON_SHORTSWORD"]

    success_message = "|gYou hammer the ore into shape and fit a timber grip - a real iron shortsword, plain but sound.|n"


class IronLoricaRecipe(FaberArmorRecipe):
    """
    Tier 2 - Faber's first trainable recipe (see `learnrecipe`, world/
    craft_commands.py). A genuine step up in both material cost and
    power from the tier-1 sword.
    """

    name = "iron lorica"
    difficulty = 30
    TIER_LEVEL = 18
    ARMOR_CATEGORY = "medium"
    KNOWN_BY_DEFAULT = False

    consumable_tags = ["iron_ore", "iron_ore", "timber"]
    consumable_names = ["iron ore", "iron ore", "timber"]
    output_prototypes = ["CRAFTED_IRON_LORICA"]

    success_message = "|gPlate by plate, you rivet together a real iron lorica - heavier work than the sword, and it shows.|n"


class IronWarSpearRecipe(FaberWeaponRecipe):
    """Tier 3 - Faber's hardest recipe so far, and its best reward."""

    name = "iron war-spear"
    difficulty = 45
    TIER_LEVEL = 28
    WEAPON_TYPE = "spear"
    KNOWN_BY_DEFAULT = False

    consumable_tags = ["iron_ore", "iron_ore", "timber", "timber"]
    consumable_names = ["iron ore", "iron ore", "timber", "timber"]
    output_prototypes = ["CRAFTED_IRON_WARSPEAR"]

    success_message = "|gA long, true haft and a real forged head - this war-spear could hold a line.|n"


# Every concrete, craftable recipe - the single source world/
# craft_commands.py's 'recipes'/'learnrecipe' commands read from,
# rather than reaching into the crafting contrib's own private
# _RECIPE_CLASSES registry (which would also pick up the abstract
# SkilledCraftingRecipe/FaberWeaponRecipe/FaberArmorRecipe bases
# above, none of which are real recipes on their own).
ALL_RECIPES = [IronShortswordRecipe, IronLoricaRecipe, IronWarSpearRecipe]


def _get_recipe_class(name):
    """Case-insensitive lookup by recipe name, or None."""
    name = (name or "").strip().lower()
    for cls in ALL_RECIPES:
        if cls.name == name:
            return cls
    return None
