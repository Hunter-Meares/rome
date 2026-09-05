"""
Tests for the Colosseum questline mechanics (world/colosseum.py) -
previously entirely untested: the sneak/solve stealth escape path,
the combat escape gate, and the level-gated Deeper Sands entrance.

This module used to also test its own CmdRecall here - removed along
with the class itself (a real bug: it silently shadowed the real,
more complete CmdRecall in world/combat.py by cmdset key-collision;
see world/colosseum.py's module docstring for the full story). See
world/tests_recall.py for coverage of the real CmdRecall that remains.
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaCommandTest
from evennia.utils import create

from world.colosseum import (
    GateOfLifeExit,
    DeeperSandsGateExit,
    CmdSneak,
    CmdSolve,
)


class ColosseumTestBase(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.colosseum_escaped = False
        self.char1.db.level = 1
        self.char1.db.combat_turnhandler = None
        self.char1.location = self.room1


class TestDefeatingTheTrainerSetsColosseumEscaped(ColosseumTestBase):
    """
    Real gap found live: escaping via the combat route (defeat
    Rutilus) was never actually covered by any automated test - only
    the stealth sneak/solve route was (see TestCmdSolve below). This
    tests CombatRules.at_defeat's own "colosseum escape-on-victory"
    branch directly, the same code path CmdChallenge's opponent
    ultimately triggers when its HP reaches 0 via resolve_attack.
    """

    def test_defeating_a_tagged_trainer_sets_the_flag(self):
        from world.combat import COMBAT_RULES

        trainer = create.create_object(
            "evennia.objects.objects.DefaultObject", key="a test trainer"
        )
        trainer.tags.add("colosseum_trainer", category="npc_role")
        trainer.db.hp = 0

        COMBAT_RULES.at_defeat(trainer, attacker=self.char1)

        self.assertTrue(self.char1.db.colosseum_escaped)

    def test_does_not_set_the_flag_without_an_attacker(self):
        from world.combat import COMBAT_RULES

        trainer = create.create_object(
            "evennia.objects.objects.DefaultObject", key="a test trainer 2"
        )
        trainer.tags.add("colosseum_trainer", category="npc_role")
        trainer.db.hp = 0

        COMBAT_RULES.at_defeat(trainer, attacker=None)

        self.assertFalse(self.char1.db.colosseum_escaped)

    def test_untagged_defeat_does_not_set_the_flag(self):
        from world.combat import COMBAT_RULES

        not_a_trainer = create.create_object(
            "evennia.objects.objects.DefaultObject", key="an ordinary target"
        )
        not_a_trainer.db.hp = 0

        COMBAT_RULES.at_defeat(not_a_trainer, attacker=self.char1)

        self.assertFalse(self.char1.db.colosseum_escaped)


class TestGateOfLifeExit(ColosseumTestBase):
    def test_blocked_without_earning_freedom(self):
        room2 = create.create_object("typeclasses.rooms.Room", key="Atrium")
        gate = create.create_object(
            GateOfLifeExit, key="east", location=self.room1, destination=room2
        )
        self.char1.db.colosseum_escaped = False

        gate.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, self.room1)

    def test_allowed_after_earning_freedom(self):
        room2 = create.create_object("typeclasses.rooms.Room", key="Atrium 2")
        gate = create.create_object(
            GateOfLifeExit, key="east2", location=self.room1, destination=room2
        )
        self.char1.db.colosseum_escaped = True

        gate.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, room2)


class TestDeeperSandsGateExit(ColosseumTestBase):
    def test_blocked_below_level_6(self):
        room2 = create.create_object("typeclasses.rooms.Room", key="Deeper Sands")
        gate = create.create_object(
            DeeperSandsGateExit, key="south", location=self.room1, destination=room2
        )
        self.char1.db.level = 5

        gate.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, self.room1)

    def test_allowed_at_level_6(self):
        room2 = create.create_object("typeclasses.rooms.Room", key="Deeper Sands 2")
        gate = create.create_object(
            DeeperSandsGateExit, key="south2", location=self.room1, destination=room2
        )
        self.char1.db.level = 6

        gate.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, room2)


class TestCmdSneak(ColosseumTestBase):
    def test_only_works_in_guard_checkpoint(self):
        self.room1.key = "Somewhere Else"
        result = self.call(CmdSneak(), "", caller=self.char1)
        self.assertIn("nothing to sneak past", result)

    @patch("world.colosseum.randint")
    def test_success_moves_to_tunnel(self, mock_randint):
        mock_randint.return_value = 100  # > 40 -> success (60% band)
        self.room1.key = "Guard Checkpoint"
        tunnel = create.create_object("typeclasses.rooms.Room", key="Maintenance Tunnel")
        tunnel.tags.add("colosseum_maintenance_tunnel", category="colosseum")

        self.call(CmdSneak(), "", caller=self.char1)

        self.assertEqual(self.char1.location, tunnel)

    @patch("world.colosseum.randint")
    def test_failure_leaves_character_in_place(self, mock_randint):
        mock_randint.return_value = 1  # <= 40 -> failure
        self.room1.key = "Guard Checkpoint"
        tunnel = create.create_object("typeclasses.rooms.Room", key="Maintenance Tunnel 2")
        tunnel.tags.add("colosseum_maintenance_tunnel", category="colosseum")

        result = self.call(CmdSneak(), "", caller=self.char1)

        self.assertIn("stirs", result)
        self.assertEqual(self.char1.location, self.room1)

    @patch("world.colosseum.randint")
    def test_can_retry_after_failure(self, mock_randint):
        """Docstring promises 'if you're spotted, you can simply try again.'"""
        self.room1.key = "Guard Checkpoint"
        tunnel = create.create_object("typeclasses.rooms.Room", key="Maintenance Tunnel 3")
        tunnel.tags.add("colosseum_maintenance_tunnel", category="colosseum")

        mock_randint.return_value = 1
        self.call(CmdSneak(), "", caller=self.char1)
        self.assertEqual(self.char1.location, self.room1)

        mock_randint.return_value = 100
        self.call(CmdSneak(), "", caller=self.char1)
        self.assertEqual(self.char1.location, tunnel)


class TestCmdSolve(ColosseumTestBase):
    def test_only_works_in_riddle_door_chamber(self):
        self.room1.key = "Somewhere Else"
        result = self.call(CmdSolve(), "shadow", caller=self.char1)
        self.assertIn("nothing to solve", result)

    def test_wrong_answer_does_not_escape(self):
        self.room1.key = "Riddle Door Chamber"
        result = self.call(CmdSolve(), "a fish", caller=self.char1)
        self.assertIn("remains dark", result)
        self.assertFalse(self.char1.db.colosseum_escaped)

    def test_correct_answer_escapes_and_moves(self):
        self.room1.key = "Riddle Door Chamber"
        stairwell = create.create_object(
            "typeclasses.rooms.Room", key="Hidden Stairwell"
        )
        stairwell.tags.add("colosseum_hidden_stairwell", category="colosseum")

        self.call(CmdSolve(), "shadow", caller=self.char1)

        self.assertTrue(self.char1.db.colosseum_escaped)
        self.assertEqual(self.char1.location, stairwell)

    def test_accepts_answer_variants(self):
        self.room1.key = "Riddle Door Chamber"
        stairwell = create.create_object(
            "typeclasses.rooms.Room", key="Hidden Stairwell 2"
        )
        stairwell.tags.add("colosseum_hidden_stairwell", category="colosseum")

        self.call(CmdSolve(), "your shadow", caller=self.char1)
        self.assertTrue(self.char1.db.colosseum_escaped)

    def test_no_answer_given_prompts_usage(self):
        self.room1.key = "Riddle Door Chamber"
        result = self.call(CmdSolve(), "", caller=self.char1)
        self.assertIn("Usage", result)
