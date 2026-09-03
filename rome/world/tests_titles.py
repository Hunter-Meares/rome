"""
Tests for earned titles (world/titles.py): the shared grant helper,
the CmdTitles command, and its three hook-ins (achievements, quests,
religion), plus the stats/look/who display changes that read
db.active_earned_title alongside the pre-existing db.custom_title.
"""

from evennia.utils.test_resources import EvenniaCommandTest

from world.titles import (
    ACHIEVEMENT_TITLES,
    QUEST_TITLES,
    RELIGION_BELOVED_TITLES,
    CmdTitles,
    grant_earned_title,
)
from world.combat import CmdCoreStats
from world.religion import add_piety


class TestGrantEarnedTitle(EvenniaCommandTest):
    def test_first_title_auto_activates(self):
        grant_earned_title(self.char1, "the Undefeated")
        self.assertIn("the Undefeated", self.char1.db.earned_titles)
        self.assertEqual(self.char1.db.active_earned_title, "the Undefeated")

    def test_second_title_does_not_override_active(self):
        grant_earned_title(self.char1, "the Undefeated")
        grant_earned_title(self.char1, "the Incorruptible")
        self.assertIn("the Incorruptible", self.char1.db.earned_titles)
        self.assertEqual(self.char1.db.active_earned_title, "the Undefeated")

    def test_granting_same_title_twice_is_a_no_op(self):
        grant_earned_title(self.char1, "the Undefeated")
        self.char1.db.active_earned_title = None
        grant_earned_title(self.char1, "the Undefeated")
        self.assertEqual(self.char1.db.earned_titles, ["the Undefeated"])
        self.assertIsNone(self.char1.db.active_earned_title)

    def test_announces_the_earn_moment(self):
        self.char1.msg = lambda text, **kwargs: messages.append(text)
        messages = []
        grant_earned_title(self.char1, "the Undefeated")
        joined = "\n".join(messages)
        self.assertIn('New title earned: "the Undefeated"', joined)
        self.assertIn("now your active title", joined)


class TestCmdTitles(EvenniaCommandTest):
    def test_bare_with_no_titles(self):
        result = self.call(CmdTitles(), "", caller=self.char1)
        self.assertIn("haven't earned any titles", result)

    def test_bare_lists_earned_and_marks_active(self):
        self.char1.db.earned_titles = ["the Undefeated", "the Incorruptible"]
        self.char1.db.active_earned_title = "the Undefeated"
        result = self.call(CmdTitles(), "", caller=self.char1)
        self.assertIn("the Undefeated", result)
        self.assertIn("(active)", result)
        self.assertIn("the Incorruptible", result)

    def test_set_switches_active_title(self):
        self.char1.db.earned_titles = ["the Undefeated", "the Incorruptible"]
        self.char1.db.active_earned_title = "the Undefeated"
        result = self.call(CmdTitles(), "set the Incorruptible", caller=self.char1)
        self.assertIn("now", result)
        self.assertEqual(self.char1.db.active_earned_title, "the Incorruptible")

    def test_set_unearned_title_is_refused(self):
        self.char1.db.earned_titles = ["the Undefeated"]
        result = self.call(CmdTitles(), "set the Radiant", caller=self.char1)
        self.assertIn("haven't earned", result)

    def test_clear_removes_active_title(self):
        self.char1.db.earned_titles = ["the Undefeated"]
        self.char1.db.active_earned_title = "the Undefeated"
        self.call(CmdTitles(), "clear", caller=self.char1)
        self.assertIsNone(self.char1.db.active_earned_title)

    def test_clear_with_nothing_active(self):
        result = self.call(CmdTitles(), "clear", caller=self.char1)
        self.assertIn("no active earned title", result)


class TestAchievementHook(EvenniaCommandTest):
    def test_legend_achievement_grants_the_undefeated(self):
        from world.achievements import announce_achievements

        self.assertEqual(ACHIEVEMENT_TITLES["legend"], "the Undefeated")
        announce_achievements(self.char1, ["legend"])
        self.assertIn("the Undefeated", self.char1.db.earned_titles or [])

    def test_untitled_achievement_grants_nothing(self):
        from world.achievements import announce_achievements

        announce_achievements(self.char1, ["first_blood"])
        self.assertNotIn("first_blood", ACHIEVEMENT_TITLES)
        self.assertFalse(self.char1.db.earned_titles)


class TestQuestHook(EvenniaCommandTest):
    def test_corrupt_official_turn_in_grants_the_incorruptible(self):
        from world.quests import CmdQuest, QUESTS
        from evennia.utils import create

        self.assertEqual(QUEST_TITLES["corrupt_official"], "the Incorruptible")
        giver = create.create_object(
            "typeclasses.objects.Object",
            key=QUESTS["corrupt_official"]["giver_key"],
            location=self.room1,
        )
        self.char1.location = self.room1
        self.char1.db.quest_log = {"corrupt_official": "ready"}
        self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("the Incorruptible", self.char1.db.earned_titles or [])


class TestReligionHook(EvenniaCommandTest):
    def test_reaching_beloved_with_mars_grants_the_war_blessed(self):
        self.assertEqual(RELIGION_BELOVED_TITLES["mars"], "the War-Blessed")
        self.char1.db.religion = "mars"
        self.char1.db.piety = {"mars": 0}
        add_piety(self.char1, "mars", 150)
        self.assertIn("the War-Blessed", self.char1.db.earned_titles or [])
        self.assertEqual(self.char1.db.active_earned_title, "the War-Blessed")

    def test_devoted_tier_alone_grants_no_title(self):
        self.char1.db.religion = "mars"
        self.char1.db.piety = {"mars": 0}
        add_piety(self.char1, "mars", 75)
        self.assertFalse(self.char1.db.earned_titles)


class TestStatsAndLookDisplayBothTitles(EvenniaCommandTest):
    def test_stats_shows_earned_and_custom_title_both(self):
        self.char1.db.active_earned_title = "the Undefeated"
        self.char1.db.custom_title = "Senator of Rome"
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("the Undefeated", result)
        self.assertIn('"Senator of Rome"', result)

    def test_look_shows_earned_and_custom_title_both(self):
        self.char1.db.active_earned_title = "the War-Blessed"
        self.char1.db.custom_title = "the Unbroken"
        appearance = self.char1.return_appearance(self.char2)
        self.assertIn("the War-Blessed", appearance)
        self.assertIn('"the Unbroken"', appearance)

    def test_look_with_no_titles_is_unchanged(self):
        self.char1.db.active_earned_title = None
        self.char1.db.custom_title = None
        appearance = self.char1.return_appearance(self.char2)
        self.assertNotIn('"', appearance.splitlines()[0] if appearance else "")


class TestWhoShowsOnlyOneTitleSlot(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.location = self.room1
        # get_puppet()'s result comes from the session, not just the
        # account/character link - EvenniaTest's fixture session isn't
        # puppeting anyone by default (see tests_social.py's own
        # TestCmdWho for the same setup requirement).
        self.session.puppet = self.char1

    def test_earned_title_takes_priority_over_custom_in_who(self):
        from commands.social import CmdWho

        self.char1.db.active_earned_title = "the Undefeated"
        self.char1.db.custom_title = "Senator of Rome"
        result = self.call(CmdWho(), "", caller=self.account)
        self.assertIn("the Undefeated", result)
        self.assertNotIn("Senator of Rome", result)

    def test_custom_title_shown_when_no_earned_title_active(self):
        from commands.social import CmdWho

        self.char1.db.active_earned_title = None
        self.char1.db.custom_title = "Senator of Rome"
        result = self.call(CmdWho(), "", caller=self.account)
        self.assertIn("Senator of Rome", result)
