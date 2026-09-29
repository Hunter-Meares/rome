"""
Tests for world/guards.py - crime-and-punishment phase 2's City Guards:
gear, the patrol/capture detection, and capture() itself. See
world/tests_jail.py for the imprisonment/execution/confiscation side,
and world/tests_crime.py for the underlying detection this all sits on.
"""

from unittest.mock import patch

from evennia.prototypes.spawner import spawn
from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from world import guards, prototypes as protos
from world.combat import COMBAT_RULES, CombatTurnHandler


class GuardTestBase(EvenniaTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.db.conditions = {}
            char.db.combat_turnhandler = None
            char.db.damage_log = {}
            char.db.homo_sacer = False
            char.db.wanted = False
            char.db.imprisoned = False


class TestEquipCityGuard(GuardTestBase):
    def test_spawning_a_guard_prototype_gives_real_gear(self):
        guard = spawn(protos.CITY_GUARD_RECRUIT)[0]
        guard.location = self.room1
        self.assertTrue(guard.db.is_city_guard)
        self.assertIsNotNone(guard.db.wielded_weapon)
        self.assertIsNotNone(guard.db.worn_armor)
        self.assertIsNotNone(guard.db.worn_shield)
        self.assertEqual(guard.db.level, 25)

    def test_unknown_level_tier_is_a_noop(self):
        npc = create.create_object("world.guards.CityGuard", key="a stray guard", location=self.room1)
        npc.db.level = 999
        guards.equip_city_guard(npc)
        self.assertIsNone(npc.db.wielded_weapon)


class TestCheckGuardCapture(GuardTestBase):
    def _make_guard(self, level=25):
        npc = create.create_object("world.guards.CityGuard", key="a City Guard recruit", location=self.room1)
        npc.db.is_city_guard = True
        npc.db.level = level
        npc.db.hp = 500
        npc.db.max_hp = 500
        return npc

    def test_noop_with_no_guard_present(self):
        self.char1.db.wanted = True
        guards.check_guard_capture(self.room1)
        self.assertIsNone(self.room1.db.combat_turnhandler)

    def test_noop_with_no_eligible_target(self):
        self._make_guard()
        guards.check_guard_capture(self.room1)
        self.assertIsNone(self.room1.db.combat_turnhandler)

    def test_noop_if_a_fight_is_already_running(self):
        self._make_guard()
        self.char1.db.wanted = True
        self.room1.db.combat_turnhandler = object()  # any truthy stand-in
        guards.check_guard_capture(self.room1)
        # Nothing new was created - the stand-in is still exactly what we set.
        self.assertIsInstance(self.room1.db.combat_turnhandler, object)

    def test_imprisoned_target_is_never_swept_up(self):
        self._make_guard()
        self.char1.db.wanted = True
        self.char1.db.imprisoned = True
        guards.check_guard_capture(self.room1)
        self.assertIsNone(self.room1.db.combat_turnhandler)

    def test_a_wanted_player_and_a_guard_starts_a_fight(self):
        guard = self._make_guard()
        self.char1.db.wanted = True
        self.char1.db.hp = 50
        self.char1.db.max_hp = 50
        guards.check_guard_capture(self.room1)
        self.assertIsNotNone(self.room1.db.combat_turnhandler)
        self.assertIn(guard, self.room1.db.combat_turnhandler.db.fighters)
        self.assertIn(self.char1, self.room1.db.combat_turnhandler.db.fighters)

    def test_every_guard_present_joins_the_same_side_against_the_target(self):
        guard1 = self._make_guard()
        guard2 = self._make_guard()
        guard2.key = "a night watch vigile"
        self.char1.db.wanted = True
        self.char1.db.hp = 50
        self.char1.db.max_hp = 50
        guards.check_guard_capture(self.room1)
        turnhandler = self.room1.db.combat_turnhandler
        self.assertEqual(guard1.db.combat_side, guard2.db.combat_side)
        self.assertNotEqual(guard1.db.combat_side, self.char1.db.combat_side)
        self.assertIn(guard2, turnhandler.db.fighters)


class TestCapture(GuardTestBase):
    def test_capture_pulls_the_target_out_of_combat_and_imprisons_them(self):
        guard = create.create_object("world.guards.CityGuard", key="a City Guard recruit", location=self.room1)
        guard.db.is_city_guard = True
        guard.db.hp = 500
        self.char1.db.wanted = True
        self.char1.db.hp = 1

        self.room1.ndb.pending_fighters = [guard, self.char1]
        self.room1.scripts.add(CombatTurnHandler)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))

        with patch("world.jail.imprison") as mock_imprison:
            guards.capture(self.char1)
            mock_imprison.assert_called_once_with(self.char1)

        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))
