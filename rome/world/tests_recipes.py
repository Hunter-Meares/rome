"""
Tests for world/recipes.py - the crafting half of the crafting
economy (world/gathering.py/tests_gathering.py cover gathering;
world/craft_commands.py/tests_craft_commands.py cover the actual
player-facing commands). Covers _craft_reward()'s parity math,
SkilledCraftingRecipe's skill-check/training/known-recipe gating, and
each of the 3 concrete Faber recipes.
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.prototypes.spawner import spawn

from world.combat import COMBAT_RULES, GOLD_PER_XP_DIVISOR
from world.economy import SELL_BACK_RATE
from world.recipes import (
    CRAFT_XP_PERCENT_PER_MINUTE,
    ALL_RECIPES,
    _craft_reward,
    _recipe_learn_cost,
    _get_recipe_class,
    SkilledCraftingRecipe,
    IronShortswordRecipe,
    IronLoricaRecipe,
    IronWarSpearRecipe,
    HealingTonicRecipe,
    AntidoteRecipe,
)


class TestCraftReward(EvenniaTest):
    def test_matches_the_stated_formula_exactly(self):
        craft_xp, price = _craft_reward(8, 5)
        expected_xp = round(5 * CRAFT_XP_PERCENT_PER_MINUTE * COMBAT_RULES.xp_for_level(8))
        self.assertEqual(craft_xp, expected_xp)
        expected_gold = expected_xp // GOLD_PER_XP_DIVISOR
        self.assertEqual(price, round(expected_gold / SELL_BACK_RATE))

    def test_a_longer_cycle_pays_more(self):
        short_xp, _ = _craft_reward(8, 2)
        long_xp, _ = _craft_reward(8, 10)
        self.assertGreater(long_xp, short_xp)

    def test_a_higher_tier_pays_more_for_the_same_cycle_time(self):
        low_xp, _ = _craft_reward(5, 5)
        high_xp, _ = _craft_reward(50, 5)
        self.assertGreater(high_xp, low_xp)

    def test_selling_at_the_baseline_nets_the_full_target_gold(self):
        craft_xp, price = _craft_reward(8, 5)
        target_gold = craft_xp // GOLD_PER_XP_DIVISOR
        net_at_baseline = int(price * SELL_BACK_RATE * 1.0)
        self.assertEqual(net_at_baseline, target_gold)

    def test_never_zero_even_at_a_trivial_cycle_time(self):
        craft_xp, price = _craft_reward(1, 0.01)
        self.assertGreaterEqual(craft_xp, 1)
        self.assertGreaterEqual(price, 1)


class TestRecipeLearnCost(EvenniaTest):
    def test_scales_with_tier_level(self):
        self.assertGreater(_recipe_learn_cost(28), _recipe_learn_cost(18))

    def test_matches_the_stated_formula(self):
        self.assertEqual(_recipe_learn_cost(18), 20 + 18 * 3)


class TestGetRecipeClass(EvenniaTest):
    def test_finds_a_real_recipe_case_insensitively(self):
        self.assertIs(_get_recipe_class("Iron Shortsword"), IronShortswordRecipe)
        self.assertIs(_get_recipe_class("iron shortsword"), IronShortswordRecipe)

    def test_unknown_name_returns_none(self):
        self.assertIsNone(_get_recipe_class("a nonexistent recipe"))

    def test_every_concrete_recipe_is_in_all_recipes(self):
        self.assertIn(IronShortswordRecipe, ALL_RECIPES)
        self.assertIn(IronLoricaRecipe, ALL_RECIPES)
        self.assertIn(IronWarSpearRecipe, ALL_RECIPES)


def _fake_recipe(difficulty=10, known_by_default=True):
    class _FakeRecipe(SkilledCraftingRecipe):
        name = "fake test recipe"
        skill_key = "faber"
        consumable_tags = []
        output_prototypes = ["DAGGER"]

    _FakeRecipe.difficulty = difficulty
    _FakeRecipe.KNOWN_BY_DEFAULT = known_by_default
    return _FakeRecipe


class TestSkilledCraftingRecipe(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.craft_skill = {}
        self.char1.db.craft_recipes_known = set()

    def test_starts_at_zero_skill(self):
        recipe_cls = _fake_recipe()
        recipe = recipe_cls(self.char1)
        self.assertEqual(recipe._skill(), 0)

    def test_a_success_trains_skill_by_three(self):
        recipe_cls = _fake_recipe(difficulty=0)
        recipe = recipe_cls(self.char1)
        with mock.patch("world.recipes.randint", return_value=1):
            result = recipe.do_craft()
        self.assertTrue(result)
        self.assertEqual(recipe._skill(), 3)

    def test_a_failure_still_trains_skill_by_one(self):
        recipe_cls = _fake_recipe(difficulty=0)
        recipe = recipe_cls(self.char1)
        with mock.patch("world.recipes.randint", return_value=100):
            result = recipe.do_craft()
        self.assertFalse(result)
        self.assertEqual(recipe._skill(), 1)

    def test_higher_skill_than_difficulty_raises_the_chance(self):
        recipe_cls = _fake_recipe(difficulty=10)
        self.char1.db.craft_skill = {"faber": 40}
        recipe = recipe_cls(self.char1)
        # skill(40) - difficulty(10) = +30 -> chance 80: a roll of 79
        # should succeed, where it would have failed at skill 0.
        with mock.patch("world.recipes.randint", return_value=79):
            result = recipe.do_craft()
        self.assertTrue(result)

    def test_chance_is_clamped_so_it_is_never_a_sure_thing_or_hopeless(self):
        recipe_cls = _fake_recipe(difficulty=0)
        self.char1.db.craft_skill = {"faber": 1000}
        recipe = recipe_cls(self.char1)
        with mock.patch("world.recipes.randint", return_value=96):
            result = recipe.do_craft()
        self.assertFalse(result)  # even absurd skill can't exceed 95% chance

    def test_skill_is_capped_at_one_hundred(self):
        recipe_cls = _fake_recipe(difficulty=0)
        self.char1.db.craft_skill = {"faber": 99}
        recipe = recipe_cls(self.char1)
        with mock.patch("world.recipes.randint", return_value=1):
            recipe.do_craft()
        self.assertEqual(recipe._skill(), 100)

    def test_different_professions_train_independently(self):
        recipe_cls = _fake_recipe(difficulty=0)
        recipe = recipe_cls(self.char1)
        with mock.patch("world.recipes.randint", return_value=1):
            recipe.do_craft()
        self.assertEqual(self.char1.db.craft_skill.get("faber"), 3)
        self.assertNotIn("textor", self.char1.db.craft_skill)

    def test_a_known_by_default_recipe_needs_no_unlock(self):
        recipe_cls = _fake_recipe(known_by_default=True)
        recipe = recipe_cls(self.char1)
        self.assertTrue(recipe.knows_recipe())

    def test_an_untrained_recipe_is_not_known_until_learned(self):
        recipe_cls = _fake_recipe(known_by_default=False)
        recipe = recipe_cls(self.char1)
        self.assertFalse(recipe.knows_recipe())
        self.char1.db.craft_recipes_known = {"fake test recipe"}
        self.assertTrue(recipe.knows_recipe())

    def test_pre_craft_refuses_an_unlearned_recipe(self):
        from evennia.contrib.game_systems.crafting import CraftingValidationError

        recipe_cls = _fake_recipe(known_by_default=False)
        recipe = recipe_cls(self.char1)
        with self.assertRaises(CraftingValidationError):
            recipe.pre_craft()


class _FaberRecipeTestBase(EvenniaCommandTest):
    RECIPE_CLASS = None
    MATERIALS = ()  # list of prototype keys to spawn and hand to the recipe

    def setUp(self):
        super().setUp()
        self.char1.db.craft_skill = {}
        self.char1.db.craft_recipes_known = {self.RECIPE_CLASS.name}
        self.materials = [spawn(proto)[0] for proto in self.MATERIALS]
        for obj in self.materials:
            obj.move_to(self.char1, quiet=True)
        # Faber recipes now require a real forge present (world/
        # recipes.py's FaberRecipe, a fixed-location design request) -
        # a tool, so it stays in the room rather than the crafter's
        # own inventory, same as CmdSimpleCraft would find it.
        self.forge = spawn("FABER_FORGE")[0]
        self.forge.location = self.room1

    def _craft(self, roll=1, with_forge=True):
        tools = [self.forge] if with_forge else []
        recipe = self.RECIPE_CLASS(self.char1, *tools, *self.materials)
        with mock.patch("world.recipes.randint", return_value=roll):
            return recipe.craft()


class TestIronShortswordRecipe(_FaberRecipeTestBase):
    """
    Tier 1 - free, no training needed, and the one recipe that's
    deliberately just 1 ore + 1 timber (not 2 ore) - see the recipe's
    own docstring for the two real reasons (ore's ~24h cooldown, and a
    real Evennia search-ambiguity limit with duplicate-keyed items).
    """

    RECIPE_CLASS = IronShortswordRecipe
    MATERIALS = ("RAW_IRON_ORE", "RAW_TIMBER")

    def test_known_by_default_with_no_training_at_all(self):
        self.char1.db.craft_recipes_known = set()  # deliberately empty
        result = self._craft()
        self.assertTrue(result)

    def test_a_successful_craft_produces_a_priced_weapon_at_its_own_fixed_tier(self):
        result = self._craft()

        self.assertTrue(result)
        sword = result[0]
        self.assertTrue(sword.db.damage_range)
        self.assertTrue(sword.db.accuracy_bonus)
        self.assertEqual(sword.db.item_level, IronShortswordRecipe.TIER_LEVEL)
        self.assertEqual(sword.db.item_category, "weapon")

        expected_xp, expected_price = _craft_reward(
            IronShortswordRecipe.TIER_LEVEL, IronShortswordRecipe.CYCLE_MINUTES
        )
        self.assertEqual(sword.db.craft_xp, expected_xp)
        self.assertEqual(sword.db.price, expected_price)

    def test_the_reward_does_not_depend_on_the_crafters_own_level(self):
        # Real, direct design correction: reward must be a fixed
        # property of the RECIPE, exactly like an NPC's own xp_reward
        # is fixed from ITS level regardless of the attacking player's
        # level - not something that scales with who's crafting, which
        # would let a high-level character farm the easiest recipe
        # forever for a high-level reward. See this module's own
        # docstring for the full reasoning.
        self.char1.db.level = 1
        result_low = self._craft()
        self.char1.db.level = 99
        # Fresh materials for a second attempt.
        self.materials = [spawn(p)[0] for p in self.MATERIALS]
        for obj in self.materials:
            obj.move_to(self.char1, quiet=True)
        result_high = self._craft()

        self.assertEqual(result_low[0].db.craft_xp, result_high[0].db.craft_xp)
        self.assertEqual(result_low[0].db.item_level, result_high[0].db.item_level)

    def test_a_successful_craft_consumes_the_materials(self):
        self._craft()
        for obj in self.materials:
            self.assertFalse(obj.pk)

    def test_a_failed_craft_keeps_the_materials(self):
        result = self._craft(roll=100)
        self.assertFalse(result)
        for obj in self.materials:
            self.assertTrue(obj.pk)

    def test_missing_a_material_is_refused(self):
        recipe = IronShortswordRecipe(self.char1, self.forge, self.materials[1])  # timber only
        with mock.patch("world.recipes.randint", return_value=1):
            result = recipe.craft()
        self.assertFalse(result)

    def test_missing_the_forge_is_refused_even_with_all_materials(self):
        result = self._craft(with_forge=False)
        self.assertFalse(result)
        for obj in self.materials:
            self.assertTrue(obj.pk)


class TestIronLoricaRecipe(_FaberRecipeTestBase):
    """Tier 2 - armor, and the first recipe that actually needs training."""

    RECIPE_CLASS = IronLoricaRecipe
    MATERIALS = ("RAW_IRON_ORE", "RAW_IRON_ORE", "RAW_TIMBER")

    def test_refused_without_training(self):
        self.char1.db.craft_recipes_known = set()
        result = self._craft()
        self.assertFalse(result)
        for obj in self.materials:
            self.assertTrue(obj.pk)  # never even consumed - refused before crafting

    def test_a_successful_craft_produces_armor_at_its_own_fixed_tier(self):
        result = self._craft()

        self.assertTrue(result)
        armor = result[0]
        self.assertIsNotNone(armor.db.damage_reduction)
        self.assertIsNotNone(armor.db.defense_modifier)
        self.assertEqual(armor.db.item_level, IronLoricaRecipe.TIER_LEVEL)
        self.assertEqual(armor.db.item_category, "armor")

        expected_xp, expected_price = _craft_reward(IronLoricaRecipe.TIER_LEVEL, IronLoricaRecipe.CYCLE_MINUTES)
        self.assertEqual(armor.db.craft_xp, expected_xp)
        self.assertEqual(armor.db.price, expected_price)

    def test_pays_more_than_the_tier_one_sword(self):
        # A genuine step up, not just a different item - see the
        # recipe's own docstring.
        lorica_xp, _ = _craft_reward(IronLoricaRecipe.TIER_LEVEL, IronLoricaRecipe.CYCLE_MINUTES)
        sword_xp, _ = _craft_reward(IronShortswordRecipe.TIER_LEVEL, IronShortswordRecipe.CYCLE_MINUTES)
        self.assertGreater(lorica_xp, sword_xp)


class TestIronWarSpearRecipe(_FaberRecipeTestBase):
    """Tier 3 - Faber's hardest and best-paying recipe so far."""

    RECIPE_CLASS = IronWarSpearRecipe
    MATERIALS = ("RAW_IRON_ORE", "RAW_IRON_ORE", "RAW_TIMBER", "RAW_TIMBER")

    def test_refused_without_training(self):
        self.char1.db.craft_recipes_known = set()
        result = self._craft()
        self.assertFalse(result)

    def test_a_successful_craft_produces_a_weapon_at_its_own_fixed_tier(self):
        result = self._craft()

        self.assertTrue(result)
        spear = result[0]
        self.assertEqual(spear.db.item_level, IronWarSpearRecipe.TIER_LEVEL)
        self.assertEqual(spear.db.item_category, "weapon")

    def test_pays_more_than_the_tier_two_armor(self):
        spear_xp, _ = _craft_reward(IronWarSpearRecipe.TIER_LEVEL, IronWarSpearRecipe.CYCLE_MINUTES)
        lorica_xp, _ = _craft_reward(IronLoricaRecipe.TIER_LEVEL, IronLoricaRecipe.CYCLE_MINUTES)
        self.assertGreater(spear_xp, lorica_xp)


class _HerbalistRecipeTestBase(EvenniaCommandTest):
    """
    A real second profession, proving crafting isn't just weapons/
    armor - see HerbalistRecipe's own docstring. Same fixed-location
    tool pattern as Faber's own forge, just an apothecary's mortar.
    """

    RECIPE_CLASS = None
    MATERIALS = ()

    def setUp(self):
        super().setUp()
        self.char1.db.craft_skill = {}
        self.char1.db.craft_recipes_known = {self.RECIPE_CLASS.name}
        self.materials = [spawn(proto)[0] for proto in self.MATERIALS]
        for obj in self.materials:
            obj.move_to(self.char1, quiet=True)
        self.mortar = spawn("APOTHECARY_MORTAR")[0]
        self.mortar.location = self.room1

    def _craft(self, roll=1, with_mortar=True):
        tools = [self.mortar] if with_mortar else []
        recipe = self.RECIPE_CLASS(self.char1, *tools, *self.materials)
        with mock.patch("world.recipes.randint", return_value=roll):
            return recipe.craft()


class TestHealingTonicRecipe(_HerbalistRecipeTestBase):
    """Tier 1 - Herbalist's free, untrained starting recipe."""

    RECIPE_CLASS = HealingTonicRecipe
    MATERIALS = ("RAW_HEALING_HERBS",)

    def test_known_by_default_with_no_training_at_all(self):
        self.char1.db.craft_recipes_known = set()
        result = self._craft()
        self.assertTrue(result)

    def test_a_successful_craft_produces_a_usable_potion(self):
        result = self._craft()

        self.assertTrue(result)
        tonic = result[0]
        self.assertEqual(tonic.db.item_func, "heal")
        self.assertEqual(tonic.db.item_category, "potion")

        expected_xp, expected_price = _craft_reward(HealingTonicRecipe.TIER_LEVEL, HealingTonicRecipe.CYCLE_MINUTES)
        self.assertEqual(tonic.db.craft_xp, expected_xp)
        self.assertEqual(tonic.db.price, expected_price)

    def test_missing_the_mortar_is_refused(self):
        result = self._craft(with_mortar=False)
        self.assertFalse(result)
        for obj in self.materials:
            self.assertTrue(obj.pk)

    def test_a_failed_craft_keeps_the_herbs(self):
        result = self._craft(roll=100)
        self.assertFalse(result)
        for obj in self.materials:
            self.assertTrue(obj.pk)


class TestAntidoteRecipe(_HerbalistRecipeTestBase):
    """Tier 2 - a genuinely different item, not just a bigger heal."""

    RECIPE_CLASS = AntidoteRecipe
    MATERIALS = ("RAW_HEALING_HERBS", "RAW_HEALING_HERBS")

    def test_refused_without_training(self):
        self.char1.db.craft_recipes_known = set()
        result = self._craft()
        self.assertFalse(result)

    def test_a_successful_craft_cures_poison_not_heals(self):
        result = self._craft()

        self.assertTrue(result)
        antidote = result[0]
        self.assertEqual(antidote.db.item_func, "cure_condition")
        self.assertIn("Poisoned", antidote.db.item_kwargs["to_cure"])

    def test_pays_more_than_the_tier_one_tonic(self):
        antidote_xp, _ = _craft_reward(AntidoteRecipe.TIER_LEVEL, AntidoteRecipe.CYCLE_MINUTES)
        tonic_xp, _ = _craft_reward(HealingTonicRecipe.TIER_LEVEL, HealingTonicRecipe.CYCLE_MINUTES)
        self.assertGreater(antidote_xp, tonic_xp)
