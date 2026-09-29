"""
Tests for world/jail.py - crime-and-punishment phase 2's imprisonment,
sentencing, confiscation, execution, and the wanted board. See
world/tests_guards.py for the capture side that hands off into this.
"""

import time
from unittest.mock import patch

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTestMixin

from world import jail
from world.crime import WANTED_CRIMINAL_TAG, ROME_PROPER_ZONE_TAG


class JailTestBase(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.room1.tags.add("rome_proper_zone", category="zone")
        self.room1.tags.add("carcer_cell", category="jail")
        for char in (self.char1, self.char2):
            char.db.conditions = {}
            char.db.combat_turnhandler = None
            char.db.damage_log = {}
            char.db.homo_sacer = False
            char.db.wanted = False
            char.db.imprisoned = False
            char.db.crime_record = []
            char.db.gold = 0


class TestComputeSentenceMinutes(JailTestBase):
    def test_no_record_returns_the_base_sentence(self):
        self.assertEqual(jail.compute_sentence_minutes(self.char1), jail.BASE_SENTENCE_MINUTES)

    def test_a_single_theft_scales_by_its_weight(self):
        self.char1.db.crime_record = [{"type": "theft", "weight": 2, "timestamp": time.time()}]
        self.assertEqual(jail.compute_sentence_minutes(self.char1), jail.BASE_SENTENCE_MINUTES * 2)

    def test_a_single_assault_scales_by_its_own_higher_weight(self):
        self.char1.db.crime_record = [{"type": "assault", "weight": 3, "timestamp": time.time()}]
        self.assertEqual(jail.compute_sentence_minutes(self.char1), jail.BASE_SENTENCE_MINUTES * 3)

    def test_repeat_offenses_double_on_top_of_severity(self):
        self.char1.db.crime_record = [
            {"type": "assault", "weight": 3, "timestamp": time.time()},
            {"type": "assault", "weight": 3, "timestamp": time.time()},
        ]
        # weight_sum=6, doubled once (2 offenses) -> 6*10*2 = 120
        self.assertEqual(jail.compute_sentence_minutes(self.char1), 120)

    def test_capital_crimes_never_count_toward_a_sentence(self):
        self.char1.db.crime_record = [{"type": "murder", "weight": 10, "timestamp": time.time()}]
        self.assertEqual(jail.compute_sentence_minutes(self.char1), jail.BASE_SENTENCE_MINUTES)

    def test_sentence_is_capped_at_twelve_hours(self):
        self.char1.db.crime_record = [
            {"type": "assault", "weight": 3, "timestamp": time.time()} for _ in range(6)
        ]
        self.assertEqual(jail.compute_sentence_minutes(self.char1), jail.SENTENCE_CAP_MINUTES)


class TestConfiscate(JailTestBase):
    def test_takes_a_share_of_gold(self):
        self.char1.db.gold = 100
        jail.confiscate(self.char1)
        self.assertEqual(self.char1.db.gold, 100 - int(100 * jail.CONFISCATION_GOLD_PERCENT))

    def test_zero_gold_is_a_noop(self):
        self.char1.db.gold = 0
        jail.confiscate(self.char1)
        self.assertEqual(self.char1.db.gold, 0)

    def test_non_capital_prisoner_keeps_their_gear(self):
        weapon = create.create_object(key="a sword", location=self.char1)
        self.char1.db.wielded_weapon = weapon
        self.char1.db.homo_sacer = False
        jail.confiscate(self.char1)
        self.assertEqual(self.char1.db.wielded_weapon, weapon)
        self.assertTrue(weapon.pk)

    def test_homo_sacer_prisoner_is_stripped_of_all_gear(self):
        weapon = create.create_object(key="a sword", location=self.char1)
        self.char1.db.wielded_weapon = weapon
        self.char1.db.homo_sacer = True
        jail.confiscate(self.char1)
        self.assertIsNone(self.char1.db.wielded_weapon)
        self.assertFalse(weapon.pk)


class TestImprison(JailTestBase):
    def test_sets_imprisoned_and_moves_to_the_cell(self):
        cell = self.room1
        self.char1.db.wanted = True
        self.char1.location = self.room2
        jail.imprison(self.char1)
        self.assertTrue(self.char1.db.imprisoned)
        self.assertEqual(self.char1.location, cell)

    def test_non_capital_gets_a_jail_script_and_a_deadline(self):
        self.char1.db.wanted = True
        jail.imprison(self.char1)
        self.assertIsNotNone(self.char1.db.imprisoned_until)
        self.assertTrue(self.char1.scripts.get("jail_sentence"))

    def test_homo_sacer_gets_an_execution_script_and_a_countdown(self):
        self.char1.db.homo_sacer = True
        jail.imprison(self.char1)
        self.assertIsNotNone(self.char1.db.execution_at)
        self.assertTrue(self.char1.scripts.get("execution_countdown"))


class TestRelease(JailTestBase):
    def test_clears_imprisonment_and_wanted_status(self):
        key, category = WANTED_CRIMINAL_TAG
        self.char1.tags.add(key, category=category)
        self.char1.db.imprisoned = True
        self.char1.db.imprisoned_until = time.time()
        self.char1.db.wanted = True
        self.char1.location = self.room1

        jail.release(self.char1)

        self.assertFalse(self.char1.db.imprisoned)
        self.assertFalse(self.char1.db.wanted)
        self.assertFalse(self.char1.tags.get(key, category=category))

    def test_moves_the_released_prisoner_back_to_rome_proper(self):
        self.char1.db.imprisoned = True
        self.char1.location = self.room1
        jail.release(self.char1)
        self.assertEqual(self.char1.location, self.room1)


class TestJailScript(JailTestBase):
    def test_releases_once_the_deadline_passes(self):
        self.char1.db.wanted = True
        self.char1.db.imprisoned = True
        self.char1.db.imprisoned_until = time.time() - 1
        self.char1.location = self.room1

        script = self.char1.scripts.add(jail.JailScript)
        with patch("world.jail.release") as mock_release:
            script.at_repeat()
            mock_release.assert_called_once_with(self.char1)

    def test_does_nothing_before_the_deadline(self):
        self.char1.db.imprisoned = True
        self.char1.db.imprisoned_until = time.time() + 600
        script = self.char1.scripts.add(jail.JailScript)
        with patch("world.jail.release") as mock_release:
            script.at_repeat()
            mock_release.assert_not_called()

    def test_stops_itself_if_no_longer_imprisoned(self):
        self.char1.db.imprisoned = False
        script = self.char1.scripts.add(jail.JailScript)
        script.at_repeat()
        self.assertFalse(self.char1.scripts.get("jail_sentence"))


class TestExecutionScript(JailTestBase):
    def test_fires_a_staged_message_as_its_threshold_is_crossed(self):
        self.char1.db.homo_sacer = True
        self.char1.db.imprisoned = True
        self.char1.db.execution_at = time.time() + 170
        self.char1.db.execution_stages_done = []
        script = self.char1.scripts.add(jail.ExecutionScript)

        script.at_repeat()

        self.assertIn(180, self.char1.db.execution_stages_done)
        self.assertNotIn(60, self.char1.db.execution_stages_done)

    def test_does_not_refire_an_already_fired_stage(self):
        self.char1.db.homo_sacer = True
        self.char1.db.imprisoned = True
        self.char1.db.execution_at = time.time() + 170
        self.char1.db.execution_stages_done = [180]
        script = self.char1.scripts.add(jail.ExecutionScript)

        with patch.object(self.char1, "msg") as mock_msg:
            script.at_repeat()
            mock_msg.assert_not_called()

    def test_executes_at_zero_and_clears_homo_sacer(self):
        self.char1.db.homo_sacer = True
        self.char1.db.imprisoned = True
        self.char1.db.execution_at = time.time() - 1
        self.char1.db.execution_stages_done = [180, 60]
        script = self.char1.scripts.add(jail.ExecutionScript)

        with patch("world.combat.COMBAT_RULES.handle_player_defeat") as mock_defeat:
            script.at_repeat()
            mock_defeat.assert_called_once_with(self.char1, attacker=None)

        self.assertFalse(self.char1.db.homo_sacer)
        self.assertFalse(self.char1.db.imprisoned)
        key, category = WANTED_CRIMINAL_TAG
        self.assertFalse(self.char1.tags.get(key, category=category))


class TestCmdWanted(EvenniaCommandTestMixin, JailTestBase):
    def test_empty_board(self):
        output = self.call(jail.CmdWanted(), "", caller=self.char1)
        self.assertIn("The wanted board is empty - Rome is, for now, at peace.", output)

    def test_lists_a_wanted_player(self):
        key, category = WANTED_CRIMINAL_TAG
        self.char2.tags.add(key, category=category)
        self.char2.db.wanted = True
        output = self.call(jail.CmdWanted(), "", caller=self.char1)
        self.assertIn("THE WANTED BOARD", output)
        self.assertIn(self.char2.key, output)
