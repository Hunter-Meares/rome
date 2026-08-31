"""
Tests for post-chargen stat growth (world/leveling.py): per-race stat
caps, the every-3rd-level point grant, and CmdStatUp's spend logic.
"""

from evennia.utils.test_resources import EvenniaCommandTest

from world.leveling import (
    stat_cap,
    grant_level_up_point,
    CmdStatUp,
    AGILITAS_CAP,
    STAT_CAP_BASE,
    STAT_CAP_BONUS,
)
from world.combat import COMBAT_RULES, MAX_LEVEL


class LevelingTestBase(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.virtus = 10
        self.char1.db.agilitas = 10
        self.char1.db.ingenium = 10
        self.char1.db.vigor = 10
        self.char1.db.unspent_stat_points = 0
        self.char1.db.race = "human"
        self.char1.db.level = 1
        self.char1.db.xp = 0
        self.char1.db.max_hp = 100
        self.char1.db.max_mp = 50
        self.char1.db.max_sp = 50


class TestStatCap(LevelingTestBase):
    def test_agilitas_caps_at_18_regardless_of_race(self):
        self.char1.db.race = "centaur"  # a +2 agilitas lean race
        self.assertEqual(stat_cap(self.char1, "agilitas"), AGILITAS_CAP)

    def test_baseline_cap_for_a_non_specialty_stat(self):
        self.char1.db.race = "human"
        self.assertEqual(stat_cap(self.char1, "virtus"), STAT_CAP_BASE)

    def test_bonus_cap_for_a_races_established_specialty_stat(self):
        self.char1.db.race = "minotaur"  # virtus +3 at chargen
        self.assertEqual(stat_cap(self.char1, "virtus"), STAT_CAP_BONUS)

    def test_no_bonus_for_a_races_weaker_lean(self):
        self.char1.db.race = "minotaur"  # vigor is only +1, below threshold
        self.assertEqual(stat_cap(self.char1, "vigor"), STAT_CAP_BASE)

    def test_unknown_race_falls_back_to_baseline(self):
        self.char1.db.race = "nonexistent"
        self.assertEqual(stat_cap(self.char1, "virtus"), STAT_CAP_BASE)


class TestGrantLevelUpPoint(LevelingTestBase):
    def test_grants_one_point(self):
        grant_level_up_point(self.char1)
        self.assertEqual(self.char1.db.unspent_stat_points, 1)

    def test_stacks_across_multiple_grants(self):
        grant_level_up_point(self.char1)
        grant_level_up_point(self.char1)
        self.assertEqual(self.char1.db.unspent_stat_points, 2)


class TestAwardXpGrantsPointsEveryThirdLevel(LevelingTestBase):
    def test_only_every_third_level_grants_a_point(self):
        self.char1.db.level = 1
        self.char1.db.xp = 0
        for _ in range(3):
            needed = COMBAT_RULES.xp_for_level(self.char1.db.level)
            COMBAT_RULES.award_xp(self.char1, needed)

        self.assertEqual(self.char1.db.level, 4)
        self.assertEqual(self.char1.db.unspent_stat_points, 1)

    def test_two_grants_from_six_levels(self):
        self.char1.db.level = 1
        self.char1.db.xp = 0
        for _ in range(6):
            needed = COMBAT_RULES.xp_for_level(self.char1.db.level)
            COMBAT_RULES.award_xp(self.char1, needed)

        self.assertEqual(self.char1.db.level, 7)
        self.assertEqual(self.char1.db.unspent_stat_points, 2)


class TestCmdStatUp(LevelingTestBase):
    def test_no_points_refuses_to_spend(self):
        result = self.call(CmdStatUp(), "virtus", caller=self.char1)
        self.assertIn("don't have any unspent", result)
        self.assertEqual(self.char1.db.virtus, 10)

    def test_spending_on_a_stat_increases_it_and_consumes_the_point(self):
        self.char1.db.unspent_stat_points = 1
        self.call(CmdStatUp(), "virtus", caller=self.char1)

        self.assertEqual(self.char1.db.virtus, 11)
        self.assertEqual(self.char1.db.unspent_stat_points, 0)

    def test_cannot_spend_past_the_cap(self):
        self.char1.db.unspent_stat_points = 1
        self.char1.db.agilitas = AGILITAS_CAP

        result = self.call(CmdStatUp(), "agilitas", caller=self.char1)

        self.assertIn("already at its cap", result)
        self.assertEqual(self.char1.db.agilitas, AGILITAS_CAP)
        self.assertEqual(self.char1.db.unspent_stat_points, 1)

    def test_resource_option_available_immediately_not_only_when_capped(self):
        """Direct request: hp/mp/sp must be a real choice from the very
        first point, not a fallback only once a stat is maxed."""
        self.char1.db.unspent_stat_points = 1
        self.char1.db.virtus = 10  # nowhere near its cap

        self.call(CmdStatUp(), "hp", caller=self.char1)

        self.assertEqual(self.char1.db.max_hp, 110)
        self.assertEqual(self.char1.db.unspent_stat_points, 0)
        self.assertEqual(self.char1.db.virtus, 10)

    def test_no_args_shows_status_without_spending(self):
        self.char1.db.unspent_stat_points = 2
        result = self.call(CmdStatUp(), "", caller=self.char1)

        self.assertIn("Unspent stat points", result)
        self.assertEqual(self.char1.db.unspent_stat_points, 2)
