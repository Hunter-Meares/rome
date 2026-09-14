"""
Tests for world/character_creator.py's ContribCmdCharCreate override.

Covers a real, confirmed live gap: "charcreate vaca Barbaric yawp" (no
'=') silently became a single character named "vaca Barbaric yawp" -
the whole string, with no warning anything unusual happened - because
with no '=' to split on, self.rhs stays None and self.lhs is the
entire typed string. Fixed to reject that specific shape (multi-word
name, no '=' at all) with guidance toward the real name/description
syntax, while leaving single-word names and genuine "name = desc"
usage completely untouched.
"""

from evennia.utils.test_resources import EvenniaCommandTest

from world.character_creator import ContribCmdCharCreate


class TestCharCreateAmbiguousMultiWordName(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        # EvenniaTest's fixture account already owns char1 - not a
        # chargen work-in-progress (no chargen_step set), so it won't
        # trigger the "resume in-progress" branch.
        self.char1.db.chargen_step = None

    def test_multiword_name_with_no_equals_is_rejected_with_guidance(self):
        result = self.call(
            ContribCmdCharCreate(), "vaca Barbaric yawp", caller=self.account
        )
        self.assertIn("charcreate vaca = Barbaric yawp", result)
        self.assertNotIn("already taken", result)

    def test_rejected_attempt_does_not_create_a_character(self):
        before = set(self.account.characters)
        self.call(ContribCmdCharCreate(), "vaca Barbaric yawp", caller=self.account)
        after = set(self.account.characters)
        self.assertEqual(before, after)

    def test_single_word_name_with_no_equals_still_works(self):
        self.call(ContribCmdCharCreate(), "Odaenathus", caller=self.account)
        keys = [c.key for c in self.account.characters]
        self.assertIn("Odaenathus", keys)

    def test_explicit_equals_with_a_multiword_name_is_not_blocked(self):
        """
        The block is specifically for a MISSING '=' - a player who
        deliberately used '=' (even with a multi-word name on the
        left) clearly meant it, and must not be blocked.
        """
        self.call(
            ContribCmdCharCreate(), "Old Trivia = a wandering fortune-teller",
            caller=self.account,
        )
        keys = [c.key for c in self.account.characters]
        self.assertIn("Old Trivia", keys)

    def test_name_and_description_via_equals_still_works_normally(self):
        self.call(ContribCmdCharCreate(), "Locusta = a poison-taster", caller=self.account)
        new_char = next(c for c in self.account.characters if c.key == "Locusta")
        self.assertEqual(new_char.db.desc, "a poison-taster")
