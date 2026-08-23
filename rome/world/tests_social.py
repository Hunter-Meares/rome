"""
Tests for commands/social.py - CmdWho and CmdTitle, previously
untested. Covers the who-table wrapping fix: Title and Room were the
only two uncropped columns (everything else already had utils.crop()
applied), and since both can run long (a 40-char custom title, an
arbitrarily long room name), they were the actual cause of the table
overflowing a normal client width and wrapping into an unreadable mess.
"""

from evennia.utils.test_resources import EvenniaCommandTest

from commands.social import (
    CmdWho,
    CmdTitle,
    _colored_rank,
    _colored_level,
    _rank_color_code,
    _short_flavor_name,
)


class TestShortFlavorName(EvenniaCommandTest):
    """
    Regression coverage for a real live bug: cropping the full
    'Race (Subtitle)' display string could truncate right at the
    open-paren, and utils.crop()'s default suffix is the literal
    string "[...]" (not a single ellipsis char) - so "Human (Roman
    Citizen)" cropped to width 12 rendered as "Human ([...]", which
    reads like garbled/broken data rather than an intentional crop.
    """

    def test_splits_off_the_parenthetical_subtitle(self):
        self.assertEqual(_short_flavor_name("Human (Roman Citizen)"), "Human")
        self.assertEqual(
            _short_flavor_name("Augur (Light - Mage/Support)"), "Augur"
        )
        self.assertEqual(
            _short_flavor_name("Minotaur (Labyrinth Born)"), "Minotaur"
        )

    def test_value_with_no_parenthesis_passes_through_unchanged(self):
        # e.g. a manually-set flavor value like Zeus's "Olympian"/"Divine"
        self.assertEqual(_short_flavor_name("Olympian"), "Olympian")
        self.assertEqual(_short_flavor_name("Divine"), "Divine")

    def test_empty_or_none_becomes_a_dash(self):
        self.assertEqual(_short_flavor_name(None), "-")
        self.assertEqual(_short_flavor_name(""), "-")


class TestRankColoring(EvenniaCommandTest):
    def test_god_tier_gets_the_reserved_color(self):
        self.assertEqual(_rank_color_code(101), "|R")

    def test_legend_and_grand_master_are_distinct(self):
        self.assertNotEqual(_rank_color_code(100), _rank_color_code(90))

    def test_novice_gets_the_dim_color(self):
        self.assertEqual(_rank_color_code(1), "|x")

    def test_colored_rank_wraps_the_real_rank_title_text(self):
        # Level 101 ("Novus Deus") is the entry rung of the Cursus
        # Divinorum god ladder - see GOD_TIERS in world/combat.py.
        # Level/rank shows the specific tier name; class_display is
        # the one that's flattened to "Divine" for every god (see
        # CmdGodLevel), not this.
        result = _colored_rank(101)
        self.assertIn("Novus Deus", result)
        self.assertTrue(result.startswith("|R"))
        self.assertTrue(result.endswith("|n"))

    def test_colored_level_shows_the_raw_number_not_the_title(self):
        result = _colored_level(101)
        self.assertIn("101", result)
        self.assertNotIn("Novus Deus", result)


class TestCmdWho(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.level = 101
        self.char1.db.custom_title = (
            "An extremely long custom title that would previously have blown up the table width"
        )
        self.char1.location = self.room1
        long_room = "A Room With An Extraordinarily Long And Descriptive Name Meant To Overflow"
        self.room1.key = long_room
        self.char1.db.race_display = "Human (Roman Citizen)"
        self.char1.db.class_display = "Augur (Light - Mage/Support)"
        # get_puppet()'s result comes from the session, not just the
        # account/character link - EvenniaTest's fixture session isn't
        # puppeting anyone by default.
        self.session.puppet = self.char1

    def test_plain_who_does_not_crash_and_crops_the_long_title(self):
        # show_admin_data checks the ACCOUNT's permissions, not the
        # character's - EvenniaTest's fixture account has "Developer"
        # by default, which would otherwise route this into the admin
        # branch instead of the plain player one being tested here.
        self.account.permissions.remove("Developer")
        result = self.call(CmdWho(), "", caller=self.account)
        # The full uncropped title must not appear verbatim - it should
        # have been cropped down to _WHO_TITLE_WIDTH_WIDE (30) first.
        self.assertNotIn(self.char1.db.custom_title, result)
        self.assertIn("Human", result)
        self.assertIn("Augur", result)
        self.assertNotIn("Human ([...]", result)
        self.assertNotIn("Augur ([...]", result)

    def test_admin_lean_who_crops_title_and_room(self):
        result = self.call(CmdWho(), "", caller=self.account)
        self.assertNotIn(self.char1.db.custom_title, result)
        self.assertNotIn(self.room1.key, result)
        # Regression check: race/class must show the clean short name,
        # not the "Human ([...]" artifact from cropping the full
        # "Human (Roman Citizen)" display string mid-parenthetical.
        self.assertIn("Human", result)
        self.assertIn("Augur", result)
        self.assertNotIn("Human ([...]", result)
        self.assertNotIn("Augur ([...]", result)

    def test_admin_full_who_crops_title_and_room_but_keeps_raw_level(self):
        result = self.call(CmdWho(), "/full", cmdstring="who", caller=self.account)
        self.assertNotIn(self.char1.db.custom_title, result)
        self.assertNotIn(self.room1.key, result)
        self.assertNotIn("Human ([...]", result)
        self.assertNotIn("Augur ([...]", result)
        # /full is documented to show the exact numeric level, not the
        # rank title - must not have been swapped to the tier's "Novus
        # Deus" text instead.
        self.assertIn("101", result)

    def test_who_with_no_puppet_does_not_crash(self):
        """An account online but not puppeting anyone (OOC) must not
        break table construction in any of the three branches."""
        self.session.puppet = None
        result = self.call(CmdWho(), "", caller=self.account)
        self.assertIsNotNone(result)


class TestCmdTitle(EvenniaCommandTest):
    def test_sets_a_title(self):
        self.call(CmdTitle(), "the Undefeated", caller=self.char1)
        self.assertEqual(self.char1.db.custom_title, "the Undefeated")

    def test_clear_removes_it(self):
        self.char1.db.custom_title = "something"
        self.call(CmdTitle(), "clear", caller=self.char1)
        self.assertIsNone(self.char1.db.custom_title)

    def test_no_args_shows_current_title_without_clearing_it(self):
        """
        Regression coverage for a real reported bug: bare 'title' used
        to clear the title outright - the single most natural thing to
        type when you just want to check your current title wiped it
        instead. Must now show it and leave it untouched.
        """
        self.char1.db.custom_title = "the Undefeated"
        result = self.call(CmdTitle(), "", caller=self.char1)
        self.assertIn("the Undefeated", result)
        self.assertEqual(self.char1.db.custom_title, "the Undefeated")

    def test_no_args_with_no_title_set_reports_that_clearly(self):
        self.char1.db.custom_title = None
        result = self.call(CmdTitle(), "", caller=self.char1)
        self.assertIn("don't have a title", result)

    def test_rejects_over_40_characters(self):
        self.char1.db.custom_title = None
        self.call(CmdTitle(), "x" * 41, caller=self.char1)
        self.assertIsNone(self.char1.db.custom_title)

    def test_accepts_exactly_40_characters(self):
        title = "x" * 40
        self.call(CmdTitle(), title, caller=self.char1)
        self.assertEqual(self.char1.db.custom_title, title)
