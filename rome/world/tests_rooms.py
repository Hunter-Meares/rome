"""
Tests for typeclasses/rooms.py's onboarding message sequences
(_send_cell_intro/_send_milo_greeting/_send_atrium_intro, all now
thin wrappers around one shared _send_message_sequence). delay()
schedules real, deferred callbacks on Twisted's reactor - these tests
replace it with a synchronous stand-in so the whole sequence runs
immediately within the test itself, rather than needing to actually
wait on real time.
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest

from typeclasses.rooms import (
    _send_message_sequence,
    CELL_INTRO_MESSAGES,
    MILO_GREETING_MESSAGES,
    ATRIUM_INTRO_MESSAGES,
)


def _immediate_delay(seconds, callback):
    """Runs the callback right away instead of scheduling it - lets a
    delay()-driven recursive sequence unwind fully within one call."""
    callback()


class TestMessageSequenceSpacing(EvenniaTest):
    """
    A direct complaint from live playtesting: several lines sent back
    to back with no visual gap between them read as one unbroken wall
    of text. Every line - including the first - now gets a leading
    blank line.
    """

    @patch("typeclasses.rooms.delay", side_effect=_immediate_delay)
    def test_every_line_gets_a_leading_blank_line(self, mock_delay):
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)
        messages = ["First line.", "Second line.", "Third line."]

        _send_message_sequence(self.char1, messages)

        self.assertEqual(len(captured), len(messages))
        for i, text in enumerate(captured):
            self.assertTrue(text.startswith("\n"))
            self.assertIn(messages[i], text)

    @patch("typeclasses.rooms.delay", side_effect=_immediate_delay)
    def test_stops_cleanly_past_the_end_of_the_list(self, mock_delay):
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)
        _send_message_sequence(self.char1, ["only one line"], index=5)
        self.assertEqual(captured, [])

    def test_all_three_message_lists_are_nonempty(self):
        self.assertTrue(CELL_INTRO_MESSAGES)
        self.assertTrue(MILO_GREETING_MESSAGES)
        self.assertTrue(ATRIUM_INTRO_MESSAGES)
