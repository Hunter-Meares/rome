"""
Tests for world/languages.py: CmdSpeak (pre-existing, previously
untested) and the new trainer/level/gold gating on CmdLearnLanguage -
learning a language used to be free, unlocated, and level-less; now
it matches the same trainer pattern every spell/skill already uses.
"""

from evennia.utils.test_resources import EvenniaCommandTest
from evennia.utils import create

from world.languages import (
    CmdSpeak,
    CmdLearnLanguage,
    LanguageTrainer,
    LANGUAGE_LEVEL_REQUIRED,
    DEFAULT_LANGUAGE,
    find_language_trainer,
    find_language_trainer_anywhere,
)
from world.combat import compute_learn_cost


class TestCmdSpeak(EvenniaCommandTest):
    def test_bare_shows_current_and_known(self):
        result = self.call(CmdSpeak(), "", caller=self.char1)
        self.assertIn("latin", result)

    def test_switch_to_a_known_language(self):
        self.char1.db.known_languages = ["latin", "greek"]
        result = self.call(CmdSpeak(), "greek", caller=self.char1)
        self.assertIn("greek", result)
        self.assertEqual(self.char1.db.speaking, "greek")

    def test_switch_to_an_unknown_language_is_refused(self):
        self.char1.db.known_languages = ["latin"]
        result = self.call(CmdSpeak(), "germanic", caller=self.char1)
        self.assertIn("don't know how to speak", result)
        self.assertNotEqual(self.char1.db.speaking, "germanic")


class TestLearnLanguageGating(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.known_languages = [DEFAULT_LANGUAGE]
        self.char1.db.level = 20
        self.char1.db.gold = 1000
        self.trainer = create.create_object(
            LanguageTrainer, key="a Greek tutor", location=self.room1
        )
        self.trainer.db.language = "greek"

    def test_already_known_is_refused(self):
        self.char1.db.known_languages = [DEFAULT_LANGUAGE, "greek"]
        result = self.call(CmdLearnLanguage(), "greek", caller=self.char1)
        self.assertIn("already know", result)

    def test_below_level_floor_is_refused(self):
        self.char1.db.level = LANGUAGE_LEVEL_REQUIRED["celtic"] - 1
        result = self.call(CmdLearnLanguage(), "celtic", caller=self.char1)
        self.assertIn("aren't experienced enough", result)
        self.assertNotIn("celtic", self.char1.db.known_languages)

    def test_no_trainer_in_room_is_refused(self):
        self.char1.location = self.room2
        result = self.call(CmdLearnLanguage(), "greek", caller=self.char1)
        self.assertIn("need to find someone", result)
        self.assertNotIn("greek", self.char1.db.known_languages)

    def test_wrong_trainer_in_room_is_refused(self):
        # The Greek tutor is here, but Celtic was asked for.
        result = self.call(CmdLearnLanguage(), "celtic", caller=self.char1)
        self.assertIn("need to find someone", result)

    def test_not_enough_gold_is_refused(self):
        self.char1.db.gold = 0
        result = self.call(CmdLearnLanguage(), "greek", caller=self.char1)
        self.assertIn("costs", result)
        self.assertNotIn("greek", self.char1.db.known_languages)
        self.assertEqual(self.char1.db.gold, 0)

    def test_successful_learn_charges_gold_and_adds_language(self):
        cost = compute_learn_cost(LANGUAGE_LEVEL_REQUIRED["greek"])
        result = self.call(CmdLearnLanguage(), "greek", caller=self.char1)
        self.assertIn("learned greek", result)
        self.assertIn("greek", self.char1.db.known_languages)
        self.assertEqual(self.char1.db.gold, 1000 - cost)

    def test_germanic_with_no_trainer_anywhere_gives_the_honest_message(self):
        result = self.call(CmdLearnLanguage(), "germanic", caller=self.char1)
        self.assertIn("nobody in Rome who can teach you Germanic", result)

    def test_germanic_finds_a_trainer_once_one_exists_anywhere(self):
        far_room = create.create_object("typeclasses.rooms.Room", key="The Germanic Settlement")
        germanic_trainer = create.create_object(
            LanguageTrainer, key="a Germanic elder", location=far_room
        )
        germanic_trainer.db.language = "germanic"

        # Still refused from the wrong room, but with the generic
        # "wrong room" message now, not the "nobody teaches this"
        # message - the language is genuinely teachable now.
        result = self.call(CmdLearnLanguage(), "germanic", caller=self.char1)
        self.assertIn("need to find someone", result)
        self.assertNotIn("nobody in Rome", result)

    def test_latin_is_already_known_from_the_start(self):
        # known_languages defaults to [DEFAULT_LANGUAGE] whenever unset
        # or empty - every character starts knowing Latin, so trying
        # to learn it again is always a no-op "already know" refusal,
        # never a real trainer/gold transaction.
        self.char1.db.known_languages = []
        result = self.call(CmdLearnLanguage(), "latin", caller=self.char1)
        self.assertIn("already know", result)
        self.assertEqual(self.char1.db.gold, 1000)


class TestFindLanguageTrainer(EvenniaCommandTest):
    def test_finds_the_right_trainer_in_a_room(self):
        trainer = create.create_object(LanguageTrainer, key="a tutor", location=self.room1)
        trainer.db.language = "egyptian"
        found = find_language_trainer(self.room1, "egyptian")
        self.assertEqual(found, trainer)

    def test_does_not_match_a_trainer_teaching_something_else(self):
        trainer = create.create_object(LanguageTrainer, key="a tutor", location=self.room1)
        trainer.db.language = "celtic"
        self.assertIsNone(find_language_trainer(self.room1, "egyptian"))

    def test_find_anywhere_across_the_whole_game(self):
        self.assertFalse(find_language_trainer_anywhere("egyptian"))
        trainer = create.create_object(LanguageTrainer, key="a tutor", location=self.room2)
        trainer.db.language = "egyptian"
        self.assertTrue(find_language_trainer_anywhere("egyptian"))
