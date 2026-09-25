"""
Tests for world/recipes.py - the crafting half of the crafting
economy (world/gathering.py, world/tests_gathering.py cover the
other half). Covers _craft_reward()'s parity math directly,
SkilledCraftingRecipe's skill-check/training behavior, and a full
IronShortswordRecipe craft using real gathered materials.
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create
from evennia.prototypes.spawner import spawn

from world.combat import COMBAT_RULES, GOLD_PER_XP_DIVISOR
from world.economy import SELL_BACK_RATE
from world.recipes import (
    CRAFT_XP_PERCENT_PER_MINUTE,
    _craft_reward,
    SkilledCraftingRecipe,
    IronShortswordRecipe,
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

    def test_a_higher_level_pays_more_for_the_same_cycle_time(self):
        low_xp, _ = _craft_reward(5, 5)
        high_xp, _ = _craft_reward(50, 5)
        self.assertGreater(high_xp, low_xp)

    def test_selling_at_the_baseline_nets_the_full_target_gold(self):
        # This is the whole point of _craft_reward's price formula -
        # see world/economy.py's node_confirm_sell for the actual
        # sale math this has to match (price * SELL_BACK_RATE *
        # distance_bonus, with distance_bonus 1.0 at an ordinary
        # Rome merchant).
        craft_xp, price = _craft_reward(8, 5)
        target_gold = craft_xp // GOLD_PER_XP_DIVISOR
        net_at_baseline = int(price * SELL_BACK_RATE * 1.0)
        self.assertEqual(net_at_baseline, target_gold)

    def test_never_zero_even_at_a_trivial_cycle_time(self):
        craft_xp, price = _craft_reward(1, 0.01)
        self.assertGreaterEqual(craft_xp, 1)
        self.assertGreaterEqual(price, 1)


def _fake_recipe(difficulty=10):
    class _FakeRecipe(SkilledCraftingRecipe):
        name = "fake test recipe"
        skill_key = "faber"
        consumable_tags = []
        output_prototypes = ["DAGGER"]

    _FakeRecipe.difficulty = difficulty
    return _FakeRecipe


class TestSkilledCraftingRecipe(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.craft_skill = {}

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


class TestIronShortswordRecipe(EvenniaCommandTest):
    """
    Deliberately just 1 ore + 1 timber, not 2 ore - see
    IronShortswordRecipe's own comment for the two real reasons found
    live (a ~24h-cooldown material can't reasonably require 2 of
    itself, and two objects sharing an identical display key aren't
    reliably both addressable in one 'craft ... from x, x' command).
    """

    def setUp(self):
        super().setUp()
        self.char1.db.craft_skill = {}
        self.char1.db.level = 8  # matches the recipe's own ITEM_LEVEL_FLOOR
        self.ore = spawn("RAW_IRON_ORE")[0]
        self.timber = spawn("RAW_TIMBER")[0]
        for obj in (self.ore, self.timber):
            obj.move_to(self.char1, quiet=True)

    def test_a_successful_craft_produces_a_priced_weapon(self):
        recipe = IronShortswordRecipe(self.char1, self.ore, self.timber)
        with mock.patch("world.recipes.randint", return_value=1):
            result = recipe.craft()

        self.assertTrue(result)
        sword = result[0]
        self.assertTrue(sword.db.damage_range)
        self.assertTrue(sword.db.accuracy_bonus)
        self.assertEqual(sword.db.item_level, 8)

        expected_xp, expected_price = _craft_reward(8, IronShortswordRecipe.CYCLE_MINUTES)
        self.assertEqual(sword.db.craft_xp, expected_xp)
        self.assertEqual(sword.db.price, expected_price)

    def test_the_reward_scales_with_the_crafters_real_level(self):
        # Real, confirmed parity bug fixed here - see the recipe's own
        # docstring: the reward used to be a flat number forever
        # regardless of who crafted it, making crafting fall ~42x
        # behind combat's own pace past the low levels. It must now
        # track the crafter's actual level, not a hardcoded one.
        self.char1.db.level = 50
        recipe = IronShortswordRecipe(self.char1, self.ore, self.timber)
        with mock.patch("world.recipes.randint", return_value=1):
            result = recipe.craft()

        expected_xp, expected_price = _craft_reward(50, IronShortswordRecipe.CYCLE_MINUTES)
        self.assertEqual(result[0].db.craft_xp, expected_xp)
        self.assertEqual(result[0].db.price, expected_price)
        self.assertGreater(expected_xp, 156)  # meaningfully more than the old flat rate

    def test_the_items_own_power_is_capped_even_at_a_high_level(self):
        # Unlike the reward above, the sword's OWN stats deliberately
        # do NOT keep scaling forever - a plain "iron shortsword"
        # should never become best-in-slot gear just because its
        # crafter leveled up; see the recipe's own docstring.
        self.char1.db.level = 90
        recipe = IronShortswordRecipe(self.char1, self.ore, self.timber)
        with mock.patch("world.recipes.randint", return_value=1):
            result = recipe.craft()

        self.assertEqual(result[0].db.item_level, IronShortswordRecipe.ITEM_LEVEL_CEILING)

    def test_a_very_low_level_crafter_still_gets_the_floor_level_item(self):
        self.char1.db.level = 1
        recipe = IronShortswordRecipe(self.char1, self.ore, self.timber)
        with mock.patch("world.recipes.randint", return_value=1):
            result = recipe.craft()

        self.assertEqual(result[0].db.item_level, IronShortswordRecipe.ITEM_LEVEL_FLOOR)

    def test_a_successful_craft_consumes_the_materials(self):
        recipe = IronShortswordRecipe(self.char1, self.ore, self.timber)
        with mock.patch("world.recipes.randint", return_value=1):
            recipe.craft()

        self.assertFalse(self.ore.pk)
        self.assertFalse(self.timber.pk)

    def test_a_failed_craft_keeps_the_materials(self):
        recipe = IronShortswordRecipe(self.char1, self.ore, self.timber)
        with mock.patch("world.recipes.randint", return_value=100):
            result = recipe.craft()

        self.assertFalse(result)
        self.assertTrue(self.ore.pk)
        self.assertTrue(self.timber.pk)

    def test_missing_a_material_is_refused(self):
        recipe = IronShortswordRecipe(self.char1, self.timber)  # no ore
        with mock.patch("world.recipes.randint", return_value=1):
            result = recipe.craft()
        self.assertFalse(result)
        self.assertTrue(self.timber.pk)

    def test_the_real_craft_command_delivers_a_sellable_item_to_inventory(self):
        # Real, confirmed gap found during live post-deploy
        # verification: the contrib's own craft() access function does
        # NOT move its result into the crafter's inventory - only
        # CmdCraft.func() does that ("result = craft(...); if result:
        # for obj in result: obj.location = caller"). Every other test
        # here calls craft()/the recipe class directly and would never
        # catch a real player ending up with a sword sitting nowhere.
        from evennia.contrib.game_systems.crafting.crafting import CmdCraft

        with mock.patch("world.recipes.randint", return_value=1):
            result_text = self.call(
                CmdCraft(),
                "iron shortsword from iron ore, timber",
                caller=self.char1,
            )

        swords = [o for o in self.char1.contents if o.key == "a hand-forged iron shortsword"]
        self.assertEqual(len(swords), 1, "command output was: %r" % result_text)
        self.assertEqual(swords[0].location, self.char1)

    def test_the_contribs_own_craft_access_function_finds_our_recipe(self):
        # Confirms the contrib's top-level craft() access function -
        # what the real in-game 'craft' command actually calls -
        # resolves "iron shortsword" to our real registered recipe via
        # settings.CRAFT_RECIPE_MODULES, not just that the recipe
        # class works when constructed directly (covered above).
        from evennia.contrib.game_systems.crafting import craft as contrib_craft

        with mock.patch("world.recipes.randint", return_value=1):
            result = contrib_craft(self.char1, "iron shortsword", self.ore, self.timber)

        self.assertTrue(result)
        self.assertEqual(result[0].key, "a hand-forged iron shortsword")
