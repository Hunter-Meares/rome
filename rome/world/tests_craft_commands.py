"""
Tests for world/craft_commands.py - the actual player-facing crafting
commands (world/recipes.py holds the recipe classes themselves;
world/gathering.py the raw materials). Covers CmdSimpleCraft's
auto-detection (the whole reason this replaces the crafting contrib's
own CmdCraft - see that command's own docstring), CmdRecipeList, and
CmdLearnRecipe/CraftTrainer.
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaCommandTest
from evennia.utils import create
from evennia.prototypes.spawner import spawn

from world.recipes import IronShortswordRecipe, IronLoricaRecipe, _recipe_learn_cost
from world.craft_commands import (
    CmdSimpleCraft,
    CmdRecipeList,
    CmdLearnRecipe,
    CraftTrainer,
    find_craft_trainer,
)


class CraftCommandTestBase(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.craft_skill = {}
        self.char1.db.craft_recipes_known = set()
        self.char1.db.gold = 0


class TestCmdSimpleCraft(CraftCommandTestBase):
    def test_no_args_shows_usage(self):
        result = self.call(CmdSimpleCraft(), "", caller=self.char1)
        self.assertIn("Usage", result)

    def test_unknown_recipe_name(self):
        result = self.call(CmdSimpleCraft(), "a recipe that does not exist", caller=self.char1)
        self.assertIn("No recipe called", result)

    def test_missing_materials_are_named(self):
        result = self.call(CmdSimpleCraft(), "iron shortsword", caller=self.char1)
        self.assertIn("iron ore", result)
        self.assertIn("timber", result)

    def test_a_known_free_recipe_crafts_with_no_extra_typing(self):
        spawn("RAW_IRON_ORE")[0].move_to(self.char1, quiet=True)
        spawn("RAW_TIMBER")[0].move_to(self.char1, quiet=True)

        with mock.patch("world.recipes.randint", return_value=1):
            self.call(CmdSimpleCraft(), "iron shortsword", caller=self.char1)

        swords = [o for o in self.char1.contents if o.key == "a hand-forged iron shortsword"]
        self.assertEqual(len(swords), 1)
        self.assertEqual(swords[0].location, self.char1)

    def test_correctly_uses_two_identically_named_ingredients(self):
        # Real, confirmed live limitation this command exists to fix:
        # the contrib's own CmdCraft parses ingredients by NAME
        # (Evennia's text search), which can't reliably tell apart two
        # objects sharing an exact display key. CmdSimpleCraft instead
        # collects matching inventory objects directly in Python, so a
        # recipe needing 2 of an identically-keyed item (iron lorica
        # needs 2 "a chunk of iron ore") just works.
        self.char1.db.craft_recipes_known = {"iron lorica"}
        ore1 = spawn("RAW_IRON_ORE")[0]
        ore2 = spawn("RAW_IRON_ORE")[0]
        ore1.move_to(self.char1, quiet=True)
        ore2.move_to(self.char1, quiet=True)
        spawn("RAW_TIMBER")[0].move_to(self.char1, quiet=True)

        with mock.patch("world.recipes.randint", return_value=1):
            self.call(CmdSimpleCraft(), "iron lorica", caller=self.char1)

        loricas = [o for o in self.char1.contents if o.key == "a hand-riveted iron lorica"]
        self.assertEqual(len(loricas), 1)
        self.assertFalse(ore1.pk)
        self.assertFalse(ore2.pk)

    def test_an_untrained_recipe_is_refused_before_touching_materials(self):
        spawn("RAW_IRON_ORE")[0].move_to(self.char1, quiet=True)
        spawn("RAW_IRON_ORE")[0].move_to(self.char1, quiet=True)
        spawn("RAW_TIMBER")[0].move_to(self.char1, quiet=True)

        result = self.call(CmdSimpleCraft(), "iron lorica", caller=self.char1)

        self.assertIn("haven't learned", result)
        self.assertEqual(len([o for o in self.char1.contents if o.db.price]), 3)  # all 3 raw materials still there


class TestCmdRecipeList(CraftCommandTestBase):
    def test_shows_every_recipe(self):
        result = self.call(CmdRecipeList(), "", caller=self.char1)
        self.assertIn("iron shortsword", result)
        self.assertIn("iron lorica", result)
        self.assertIn("iron war-spear", result)

    def test_marks_the_free_recipe_as_free(self):
        result = self.call(CmdRecipeList(), "", caller=self.char1)
        lines = result.splitlines()
        sword_line = next(l for l in lines if "iron shortsword" in l)
        self.assertIn("free", sword_line.lower())

    def test_marks_an_unlearned_recipe_as_needing_training(self):
        result = self.call(CmdRecipeList(), "", caller=self.char1)
        lines = result.splitlines()
        lorica_line = next(l for l in lines if "iron lorica" in l)
        self.assertIn("needs training", lorica_line.lower())

    def test_marks_a_learned_recipe_as_known(self):
        self.char1.db.craft_recipes_known = {"iron lorica"}
        result = self.call(CmdRecipeList(), "", caller=self.char1)
        lines = result.splitlines()
        lorica_line = next(l for l in lines if "iron lorica" in l)
        self.assertIn("known", lorica_line.lower())


class TestFindCraftTrainer(CraftCommandTestBase):
    def test_finds_a_matching_trainer(self):
        trainer = create.create_object(CraftTrainer, key="a smith", location=self.room1)
        trainer.db.teaches_profession = "faber"
        self.assertEqual(find_craft_trainer(self.room1, "faber"), trainer)

    def test_ignores_a_trainer_for_a_different_profession(self):
        trainer = create.create_object(CraftTrainer, key="a weaver", location=self.room1)
        trainer.db.teaches_profession = "textor"
        self.assertIsNone(find_craft_trainer(self.room1, "faber"))

    def test_no_trainer_present(self):
        self.assertIsNone(find_craft_trainer(self.room1, "faber"))


class TestCmdLearnRecipe(CraftCommandTestBase):
    def setUp(self):
        super().setUp()
        self.trainer = create.create_object(CraftTrainer, key="a Faber master smith", location=self.room1)
        self.trainer.db.teaches_profession = "faber"

    def test_no_trainer_here_is_refused(self):
        self.trainer.location = self.room2
        self.char1.db.gold = 1000
        result = self.call(CmdLearnRecipe(), "iron lorica", caller=self.char1)
        self.assertIn("no one here", result.lower())

    def test_unknown_recipe_name(self):
        result = self.call(CmdLearnRecipe(), "a recipe that does not exist", caller=self.char1)
        self.assertIn("No recipe called", result)

    def test_the_free_tier_one_recipe_needs_no_training(self):
        result = self.call(CmdLearnRecipe(), "iron shortsword", caller=self.char1)
        self.assertIn("needs no training", result.lower())

    def test_not_enough_gold_is_refused(self):
        self.char1.db.gold = 0
        result = self.call(CmdLearnRecipe(), "iron lorica", caller=self.char1)
        self.assertIn("gold", result.lower())
        self.assertNotIn("iron lorica", self.char1.db.craft_recipes_known or set())

    def test_learning_costs_the_right_amount_of_gold(self):
        cost = _recipe_learn_cost(IronLoricaRecipe.TIER_LEVEL)
        self.char1.db.gold = cost

        self.call(CmdLearnRecipe(), "iron lorica", caller=self.char1)

        self.assertEqual(self.char1.db.gold, 0)
        self.assertIn("iron lorica", self.char1.db.craft_recipes_known)

    def test_already_known_recipe_is_refused(self):
        self.char1.db.craft_recipes_known = {"iron lorica"}
        self.char1.db.gold = 1000
        gold_before = self.char1.db.gold

        result = self.call(CmdLearnRecipe(), "iron lorica", caller=self.char1)

        self.assertIn("already know", result.lower())
        self.assertEqual(self.char1.db.gold, gold_before)
