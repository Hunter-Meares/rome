"""
Tests for world/motd.py - specifically locking in the real bug that
prompted rebuilding this as an actual bordered box: RECENT_UPDATES_TEXT
used to have hand-inserted line breaks with no real width discipline,
so a longer update overflowed straight through the box's own side
borders. Every line the box produces must now come out the exact same
visible width, regardless of what RECENT_UPDATES_TEXT says or how
long it is - that's the property worth testing, not the exact text.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils.ansi import ANSIString

from world.motd import get_motd, MOTD_WIDTH, RECENT_UPDATES_DATE


class TestMOTDBox(EvenniaTest):
    def test_every_line_is_the_same_visible_width(self):
        lines = get_motd().split("\n")
        widths = {len(ANSIString(line).clean()) for line in lines}
        self.assertEqual(
            widths, {MOTD_WIDTH + 4},
            "MOTD lines aren't a consistent width - %s" % widths,
        )

    def test_a_long_recent_update_does_not_break_the_box(self):
        import world.motd as motd_module

        original = motd_module.RECENT_UPDATES_TEXT
        try:
            motd_module.RECENT_UPDATES_TEXT = (
                "This is a deliberately very long single-paragraph update "
                "with absolutely no manual line breaks in it at all, written "
                "specifically to confirm that a real update of any length "
                "gets wrapped and boxed correctly instead of overflowing "
                "straight through the border the way the original bug did."
            )
            lines = get_motd().split("\n")
            widths = {len(ANSIString(line).clean()) for line in lines}
            self.assertEqual(widths, {MOTD_WIDTH + 4})
        finally:
            motd_module.RECENT_UPDATES_TEXT = original

    def test_recent_updates_date_appears(self):
        self.assertIn(RECENT_UPDATES_DATE, get_motd())

    def test_no_stray_reset_only_border_artifact(self):
        # The real bug this file exists to catch: writing "|Y|n" (pure
        # color markup, no visible glyph) instead of the escaped
        # literal pipe "|Y|||n" - which silently drops the border
        # entirely rather than erroring, so only a real width/content
        # check catches it, not a syntax check.
        clean = str(ANSIString(get_motd().split("\n")[1]).clean())
        self.assertIn("|", clean)
