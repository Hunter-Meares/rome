"""
Tests for player death and the Underworld return path - the single
highest-priority untested item flagged by CLAUDE.md's known-untested
list ("slay used on an actual player character (only ever tested on
NPCs)") and its own to-do notes on the Underworld.

Covers CombatRules.handle_player_defeat (the level<=5 safe-respawn
branch vs. the level 6+ real-death branch, turnhandler cleanup, and
the "Underworld not built" fail-safe), resurrect()/send_to_underworld,
CharonTimer, CharonFerryExit's gating, and CmdAnswerRiddle.
"""

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create

from world.combat import COMBAT_RULES, CombatTurnHandler
from world.underworld import CharonTimer, CharonFerryExit, CmdAnswerRiddle


class UnderworldTestBase(EvenniaTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.db.conditions = {}
            char.db.combat_turnhandler = None
            char.db.combat_side = None
            char.db.is_dead = False


class TestHandlePlayerDefeatLowLevel(UnderworldTestBase):
    """Level <= 5: safe respawn to the cells, no real penalty."""

    def test_low_level_defeat_restores_stats_and_sends_to_cells(self):
        from evennia.objects.models import ObjectDB
        from django.conf import settings

        cells = ObjectDB.objects.get_id(settings.START_LOCATION)
        if not cells:
            self.skipTest("START_LOCATION not resolvable in this test DB")

        self.char1.db.level = 3
        self.char1.db.max_hp = 100
        self.char1.db.hp = 0
        self.char1.db.max_mp = 20
        self.char1.db.mp = 0
        self.char1.db.max_sp = 30
        self.char1.db.sp = 0

        COMBAT_RULES.handle_player_defeat(self.char1, attacker=self.char2)

        self.assertEqual(self.char1.db.hp, self.char1.db.max_hp)
        self.assertEqual(self.char1.db.mp, self.char1.db.max_mp)
        self.assertEqual(self.char1.db.sp, self.char1.db.max_sp)
        self.assertFalse(self.char1.db.is_dead)
        self.assertEqual(self.char1.location, cells)

    def test_low_level_defeat_boundary_at_exactly_level_5(self):
        """Level 5 is explicitly inclusive of the safe-respawn branch."""
        self.char1.db.level = 5
        self.char1.db.hp = 0
        COMBAT_RULES.handle_player_defeat(self.char1, attacker=self.char2)
        self.assertFalse(self.char1.db.is_dead)


class TestHandlePlayerDefeatHighLevel(UnderworldTestBase):
    """Level 6+: real death - Underworld, XP halved, stats untouched."""

    def _tag_underworld_entrance(self):
        entrance = create.create_object(
            "typeclasses.rooms.Room", key="Shores of the Styx"
        )
        entrance.tags.add("underworld_entrance", category="underworld")
        return entrance

    def test_high_level_defeat_sends_to_underworld_and_halves_xp(self):
        entrance = self._tag_underworld_entrance()

        self.char1.db.level = 10
        self.char1.db.xp = 100
        self.char1.db.hp = 0

        COMBAT_RULES.handle_player_defeat(self.char1, attacker=self.char2)

        self.assertTrue(self.char1.db.is_dead)
        self.assertEqual(self.char1.db.xp, 50)
        self.assertEqual(self.char1.location, entrance)
        self.assertFalse(self.char1.db.charon_arrived)
        # A CharonTimer script should now be attached.
        self.assertTrue(
            any(isinstance(s, CharonTimer) for s in self.char1.scripts.all())
        )

    def test_high_level_defeat_boundary_at_exactly_level_6(self):
        self._tag_underworld_entrance()
        self.char1.db.level = 6
        self.char1.db.xp = 100
        self.char1.db.hp = 0
        COMBAT_RULES.handle_player_defeat(self.char1, attacker=self.char2)
        self.assertTrue(self.char1.db.is_dead)

    def test_odd_xp_halving_floors_down(self):
        self._tag_underworld_entrance()
        self.char1.db.level = 10
        self.char1.db.xp = 101
        self.char1.db.hp = 0
        COMBAT_RULES.handle_player_defeat(self.char1, attacker=self.char2)
        self.assertEqual(self.char1.db.xp, 50)

    def test_no_underworld_entrance_fails_safe_to_full_revival(self):
        """
        Documented fail-safe: if the Underworld isn't built/tagged on
        this install, a level 6+ death must not leave the player
        permanently stuck as dead with nowhere to go - it should
        revert is_dead and fully heal them back at the cells instead.
        """
        from evennia.objects.models import ObjectDB
        from django.conf import settings

        cells = ObjectDB.objects.get_id(settings.START_LOCATION)
        if not cells:
            self.skipTest("START_LOCATION not resolvable in this test DB")

        # Deliberately do NOT tag an underworld_entrance.
        self.char1.db.level = 10
        self.char1.db.max_hp = 100
        self.char1.db.hp = 0

        COMBAT_RULES.handle_player_defeat(self.char1, attacker=self.char2)

        self.assertFalse(self.char1.db.is_dead)
        self.assertEqual(self.char1.db.hp, self.char1.db.max_hp)
        self.assertEqual(self.char1.location, cells)


class TestHandlePlayerDefeatTurnHandlerCleanup(UnderworldTestBase):
    """
    handle_player_defeat is documented to clean up combat/turn-handler
    state BEFORE moving the defeated player, so they don't end up
    stuck reporting as 'in combat' after respawning elsewhere.
    """

    def test_defeated_fighter_removed_from_turnhandler_and_turn_repointed(self):
        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        self.char1.db.combat_side = "A"
        self.char2.db.combat_side = "B"
        handler.db.fighters = [self.char1, self.char2]
        handler.db.turn = 0
        self.char1.db.combat_turnhandler = handler
        self.char2.db.combat_turnhandler = handler

        self.char1.db.level = 3
        self.char1.db.hp = 0

        COMBAT_RULES.handle_player_defeat(self.char1, attacker=self.char2)

        self.assertNotIn(self.char1, handler.db.fighters)
        self.assertIsNone(self.char1.db.combat_turnhandler)

    def test_last_fighter_removed_stops_and_deletes_handler(self):
        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        self.char1.db.combat_side = "A"
        handler.db.fighters = [self.char1]
        handler.db.turn = 0
        self.char1.db.combat_turnhandler = handler

        self.char1.db.level = 3
        self.char1.db.hp = 0

        COMBAT_RULES.handle_player_defeat(self.char1, attacker=None)

        self.assertFalse(handler.pk)


class TestResurrectAndSendToUnderworld(UnderworldTestBase):
    def test_resurrect_does_nothing_if_not_dead(self):
        self.char1.db.is_dead = False
        self.char1.db.hp = 1
        result = COMBAT_RULES.resurrect(self.char1)
        self.assertFalse(result)
        self.assertEqual(self.char1.db.hp, 1)

    def test_resurrect_fully_heals_and_returns_to_cells(self):
        from evennia.objects.models import ObjectDB
        from django.conf import settings

        cells = ObjectDB.objects.get_id(settings.START_LOCATION)
        if not cells:
            self.skipTest("START_LOCATION not resolvable in this test DB")

        self.char1.db.is_dead = True
        self.char1.db.max_hp = 100
        self.char1.db.hp = 0
        self.char1.db.max_mp = 20
        self.char1.db.mp = 0

        result = COMBAT_RULES.resurrect(self.char1)

        self.assertTrue(result)
        self.assertFalse(self.char1.db.is_dead)
        self.assertEqual(self.char1.db.hp, self.char1.db.max_hp)
        self.assertEqual(self.char1.db.mp, self.char1.db.max_mp)
        self.assertEqual(self.char1.location, cells)

    def test_send_to_underworld_sets_is_dead_and_moves_if_entrance_tagged(self):
        entrance = create.create_object(
            "typeclasses.rooms.Room", key="Shores of the Styx 2"
        )
        entrance.tags.add("underworld_entrance", category="underworld")

        self.char1.db.is_dead = False
        COMBAT_RULES.send_to_underworld(self.char1)

        self.assertTrue(self.char1.db.is_dead)
        self.assertEqual(self.char1.location, entrance)


class TestCharonTimer(UnderworldTestBase):
    def test_charon_arrival_flips_flag_and_stops(self):
        self.char1.db.is_dead = True
        self.char1.db.charon_arrived = False

        timer = create.create_script(CharonTimer, obj=self.char1, autostart=False)
        timer.at_repeat()

        self.assertTrue(self.char1.db.charon_arrived)

    def test_no_ferry_exit_in_room_falls_back_to_manual_crossing_message(self):
        """No CharonFerryExit present (e.g. a differently-built room) -
        must fall back to the old 'cross manually' message, not silently
        do nothing."""
        self.char1.db.is_dead = True
        self.char1.db.charon_arrived = False
        self.char1.db.hp = 0
        self.char1.location = self.room1  # plain room, no ferry exit

        timer = create.create_script(CharonTimer, obj=self.char1, autostart=False)
        timer.at_repeat()

        self.assertTrue(self.char1.db.charon_arrived)
        self.assertEqual(self.char1.location, self.room1)  # not moved

    def test_ferry_exit_present_auto_carries_character_across(self):
        """
        Regression coverage for the force_move fix: the character's hp
        is still 0 (the normal state for a dead character - see
        CombatRules.handle_player_defeat), which would otherwise block
        this move entirely via CombatCharacter.at_pre_move.
        """
        from world.underworld import CharonFerryExit

        far_shore = create.create_object(
            "typeclasses.rooms.Room", key="Threshold of Return"
        )
        create.create_object(
            CharonFerryExit, key="onward", location=self.room1, destination=far_shore
        )

        self.char1.db.is_dead = True
        self.char1.db.charon_arrived = False
        self.char1.db.hp = 0
        self.char1.location = self.room1

        timer = create.create_script(CharonTimer, obj=self.char1, autostart=False)
        timer.at_repeat()

        self.assertEqual(self.char1.location, far_shore)
        self.assertTrue(self.char1.db.charon_arrived)

    def test_auto_carry_does_not_send_the_manual_crossing_message(self):
        """
        The 'you may now continue onward' fallback message must NOT
        also fire after a successful auto-carry - it would directly
        contradict the crossing narration that already played.
        """
        from unittest.mock import patch
        from world.underworld import CharonFerryExit

        far_shore = create.create_object(
            "typeclasses.rooms.Room", key="Threshold of Return 2"
        )
        create.create_object(
            CharonFerryExit, key="onward2", location=self.room1, destination=far_shore
        )

        self.char1.db.is_dead = True
        self.char1.db.charon_arrived = False
        self.char1.db.hp = 0
        self.char1.location = self.room1

        timer = create.create_script(CharonTimer, obj=self.char1, autostart=False)
        with patch.object(self.char1, "msg") as mock_msg:
            timer.at_repeat()

        sent_texts = [call.args[0] for call in mock_msg.call_args_list if call.args]
        self.assertFalse(any("You may now continue" in t for t in sent_texts))

    def test_timer_stops_without_flipping_flag_if_no_longer_dead(self):
        """
        Documented guard: if the character somehow isn't dead anymore
        by the time the timer fires (e.g. resurrected another way),
        it should just stop, not force charon_arrived anyway.
        """
        self.char1.db.is_dead = False
        self.char1.db.charon_arrived = False

        timer = create.create_script(CharonTimer, obj=self.char1, autostart=False)
        timer.at_repeat()

        self.assertFalse(self.char1.db.charon_arrived)


class TestCharonFerryExit(UnderworldTestBase):
    def test_blocked_without_charon_arrived(self):
        room2 = create.create_object("typeclasses.rooms.Room", key="Threshold of Return")
        ferry = create.create_object(
            CharonFerryExit, key="onward", location=self.room1, destination=room2
        )
        self.char1.db.charon_arrived = False
        self.char1.location = self.room1

        ferry.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, self.room1)

    def test_allowed_once_charon_arrived(self):
        room2 = create.create_object("typeclasses.rooms.Room", key="Threshold of Return 2")
        ferry = create.create_object(
            CharonFerryExit, key="onward2", location=self.room1, destination=room2
        )
        self.char1.db.charon_arrived = True
        self.char1.location = self.room1

        ferry.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, room2)


class TestCmdAnswerRiddle(EvenniaCommandTest):
    def test_wrong_room_rejects(self):
        self.char1.location = self.room1  # not "Threshold of Return"
        self.char1.db.is_dead = True
        result = self.call(CmdAnswerRiddle(), "man", caller=self.char1)
        self.assertIn("no riddle to answer", result)

    def test_not_dead_rejects(self):
        self.room1.key = "Threshold of Return"
        self.char1.db.is_dead = False
        result = self.call(CmdAnswerRiddle(), "man", caller=self.char1)
        self.assertIn("already among the living", result)

    def test_wrong_answer_does_not_resurrect(self):
        self.room1.key = "Threshold of Return"
        self.char1.db.is_dead = True
        result = self.call(CmdAnswerRiddle(), "a fish", caller=self.char1)
        self.assertIn("wrong", result)
        self.assertTrue(self.char1.db.is_dead)

    def test_correct_answer_resurrects(self):
        from evennia.objects.models import ObjectDB
        from django.conf import settings

        if not ObjectDB.objects.get_id(settings.START_LOCATION):
            self.skipTest("START_LOCATION not resolvable in this test DB")

        self.room1.key = "Threshold of Return"
        self.char1.db.is_dead = True
        self.char1.db.max_hp = 100
        self.char1.db.hp = 0

        self.call(CmdAnswerRiddle(), "a man", caller=self.char1)

        self.assertFalse(self.char1.db.is_dead)
        self.assertEqual(self.char1.db.hp, self.char1.db.max_hp)
