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
    """
    Rebalanced by direct request from a level 6 newbie-adjacent
    continuation into genuine level 75+ endgame content, so it stops
    competing with the sewers as "where a fresh escapee goes next."
    """

    def test_blocked_below_level_75(self):
        room2 = create.create_object("typeclasses.rooms.Room", key="Deeper Sands")
        gate = create.create_object(
            DeeperSandsGateExit, key="south", location=self.room1, destination=room2
        )
        self.char1.db.level = 74

        gate.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, self.room1)

    def test_allowed_at_level_75(self):
        room2 = create.create_object("typeclasses.rooms.Room", key="Deeper Sands 2")
        gate = create.create_object(
            DeeperSandsGateExit, key="south2", location=self.room1, destination=room2
        )
        self.char1.db.level = 75

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


class TestEscapePurse(ColosseumTestBase):
    """A new character has 0 gold and the cheapest first lesson costs 23,
    so escaping the cells now pays a one-time purse, by either route."""

    def _trainer(self):
        trainer = create.create_object("evennia.objects.objects.DefaultObject", key="a purse test trainer")
        trainer.tags.add("colosseum_trainer", category="npc_role")
        trainer.db.hp = 0
        return trainer

    def _stairwell(self):
        stairwell = create.create_object("typeclasses.rooms.Room", key="Hidden Stairwell Purse")
        stairwell.tags.add("colosseum_hidden_stairwell", category="colosseum")
        return stairwell

    def test_a_new_character_starts_with_no_gold_to_begin_with(self):
        self.assertFalse(self.char1.db.gold)

    def test_defeating_the_trainer_pays_the_purse(self):
        from world.colosseum import ESCAPE_PURSE_GOLD
        from world.combat import COMBAT_RULES

        self.char1.db.gold = 0
        COMBAT_RULES.at_defeat(self._trainer(), attacker=self.char1)
        self.assertEqual(self.char1.db.gold, ESCAPE_PURSE_GOLD)

    def test_solving_the_riddle_pays_the_purse(self):
        from world.colosseum import ESCAPE_PURSE_GOLD

        self.room1.key = "Riddle Door Chamber"
        self._stairwell()
        self.char1.db.gold = 0
        self.call(CmdSolve(), "shadow", caller=self.char1)
        self.assertEqual(self.char1.db.gold, ESCAPE_PURSE_GOLD)

    def test_it_is_paid_only_once_however_you_escape(self):
        from world.colosseum import ESCAPE_PURSE_GOLD
        from world.combat import COMBAT_RULES

        self.char1.db.gold = 0
        COMBAT_RULES.at_defeat(self._trainer(), attacker=self.char1)
        # Solving the riddle afterwards must not pay a second time.
        self.room1.key = "Riddle Door Chamber"
        self._stairwell()
        self.call(CmdSolve(), "shadow", caller=self.char1)
        self.assertEqual(self.char1.db.gold, ESCAPE_PURSE_GOLD)

    def test_re_solving_after_already_escaping_pays_nothing(self):
        self.char1.db.colosseum_escaped = True
        self.char1.db.gold = 0
        self.room1.key = "Riddle Door Chamber"
        self._stairwell()
        self.call(CmdSolve(), "shadow", caller=self.char1)
        self.assertEqual(self.char1.db.gold, 0)

    def test_the_purse_message_names_the_amount(self):
        from unittest import mock

        from world.combat import COMBAT_RULES

        self.char1.db.gold = 0
        with mock.patch.object(self.char1, "msg") as mock_msg:
            COMBAT_RULES.at_defeat(self._trainer(), attacker=self.char1)
        said = " ".join(str(c.args[0]) for c in mock_msg.call_args_list if c.args)
        self.assertIn("+30 gold", said)

    def test_an_npc_defeating_a_trainer_is_not_paid(self):
        from world.colosseum import grant_escape_purse

        npc = create.create_object("typeclasses.characters.Character", key="a passer-by")
        npc.db.gold = 0
        grant_escape_purse(npc, "x")
        self.assertEqual(npc.db.gold, 0)


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
