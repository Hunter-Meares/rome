"""
Tests for the 'recall' command (world/combat.py's CmdRecall): the
combat gate, the cooldown, and the tagged-temple destination lookup
it shares with CombatRules.resurrect().
"""

import time

from evennia.utils.test_resources import EvenniaCommandTest
from evennia.utils import create

from world.combat import CmdRecall, RECALL_COOLDOWN_SECONDS


class TestCmdRecall(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.temple = create.create_object(
            "typeclasses.rooms.Room", key="Temple of Jupiter Optimus Maximus"
        )
        self.temple.tags.add("capitoline_resurrection_point", category="capitoline")
        self.char1.db.combat_turnhandler = None
        self.char1.db.recall_cooldown_until = None
        self.char1.db.is_dead = False

    def test_blocked_while_in_combat(self):
        self.char1.db.combat_turnhandler = True
        result = self.call(CmdRecall(), "", caller=self.char1)
        self.assertIn("can't recall while in combat", result)
        self.assertNotEqual(self.char1.location, self.temple)

    def test_blocked_while_dead(self):
        self.char1.db.is_dead = True
        result = self.call(CmdRecall(), "", caller=self.char1)
        self.assertIn("can't recall out of the Underworld", result)
        self.assertNotEqual(self.char1.location, self.temple)

    def test_blocked_while_in_an_underworld_room_even_if_not_flagged_dead(self):
        underworld_room = create.create_object(
            "typeclasses.rooms.Room", key="The Fields of Asphodel"
        )
        underworld_room.tags.add("underworld_zone", category="zone")
        self.char1.db.is_dead = False
        self.char1.location = underworld_room
        result = self.call(CmdRecall(), "", caller=self.char1)
        self.assertIn("can't recall out of the Underworld", result)
        self.assertEqual(self.char1.location, underworld_room)

    def test_recalls_to_the_tagged_temple(self):
        self.char1.location = self.room1
        result = self.call(CmdRecall(), "", caller=self.char1)
        self.assertIn("Temple of Jupiter Optimus Maximus", result)
        self.assertEqual(self.char1.location, self.temple)

    def test_sets_a_cooldown(self):
        self.call(CmdRecall(), "", caller=self.char1)
        self.assertGreater(self.char1.db.recall_cooldown_until, time.time())
        self.assertLessEqual(
            self.char1.db.recall_cooldown_until, time.time() + RECALL_COOLDOWN_SECONDS + 1
        )

    def test_second_recall_during_cooldown_is_refused(self):
        self.char1.db.recall_cooldown_until = time.time() + 300
        location_before = self.char1.location
        result = self.call(CmdRecall(), "", caller=self.char1)
        self.assertIn("wait", result)
        self.assertEqual(self.char1.location, location_before)

    def test_recall_works_again_once_cooldown_expires(self):
        self.char1.db.recall_cooldown_until = time.time() - 1
        self.char1.location = self.room1
        self.call(CmdRecall(), "", caller=self.char1)
        self.assertEqual(self.char1.location, self.temple)

    def test_no_tagged_temple_fails_gracefully(self):
        self.temple.tags.remove("capitoline_resurrection_point", category="capitoline")
        self.char1.location = self.room1
        result = self.call(CmdRecall(), "", caller=self.char1)
        self.assertIn("nowhere to recall", result)
        self.assertEqual(self.char1.location, self.room1)


class TestRecallIsNotShadowedInTheRealMergedCmdset(EvenniaCommandTest):
    """
    A real bug found live: world/colosseum.py used to define its own,
    older CmdRecall (same-city, no cooldown, wrong destination) and
    register it into ColosseumCmdSet, which CharacterCmdSet adds AFTER
    BattleCmdSet (the real CmdRecall's home) in
    commands/default_cmdsets.py's at_cmdset_creation(). Per Evennia's
    own CmdSet.add() docs, a later .add() call for the same command
    key replaces the earlier one outright within one
    at_cmdset_creation() - so the old, wrong recall silently won every
    time, and both classes' own isolated unit tests kept passing
    throughout, since neither test file ever exercised the real merged
    cmdset. This test does exactly that, so a future accidental
    reintroduction of a second "recall" key would be caught here
    instead of only by a live player.
    """

    def test_the_real_combat_cmdrecall_wins_in_the_actual_merged_cmdset(self):
        from commands.default_cmdsets import CharacterCmdSet

        cmdset = CharacterCmdSet()
        cmdset.at_cmdset_creation()
        matches = [cmd for cmd in cmdset.commands if cmd.key == "recall"]
        self.assertEqual(len(matches), 1)
        self.assertIs(type(matches[0]), CmdRecall)
