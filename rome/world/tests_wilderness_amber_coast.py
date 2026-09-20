"""
Tests for world/wilderness_amber_coast.py - the second bounded
wilderness stretch, connecting the Germanic Stronghold's "The
Contested Ridge" to the Amber Coast's own authored "The River Delta -
Upper Reach" room. Mirrors world/tests_wilderness.py's own structure
exactly, since the underlying architecture is deliberately identical.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from evennia.contrib.grid import wilderness

from world.wilderness_amber_coast import (
    AmberCoastWildernessMapProvider,
    ROAD_LENGTH,
    WIDTH,
    _band,
    _cleanup_encounter_npc,
    _ENCOUNTER_TAG,
    EnterAmberCoastWildernessExit,
)


class TestBounds(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.provider = AmberCoastWildernessMapProvider()

    def test_road_length_is_a_hard_edge(self):
        self.assertTrue(self.provider.is_valid_coordinates(None, (0, ROAD_LENGTH)))
        self.assertFalse(self.provider.is_valid_coordinates(None, (0, ROAD_LENGTH + 1)))

    def test_negative_y_is_invalid(self):
        self.assertFalse(self.provider.is_valid_coordinates(None, (0, -1)))

    def test_width_is_a_hard_edge_both_sides(self):
        self.assertTrue(self.provider.is_valid_coordinates(None, (WIDTH, 5)))
        self.assertTrue(self.provider.is_valid_coordinates(None, (-WIDTH, 5)))
        self.assertFalse(self.provider.is_valid_coordinates(None, (WIDTH + 1, 5)))
        self.assertFalse(self.provider.is_valid_coordinates(None, (-WIDTH - 1, 5)))

    def test_map_is_not_infinite(self):
        self.assertFalse(self.provider.is_valid_coordinates(None, (10000, 10000)))

    def test_road_length_is_at_least_the_requested_50(self):
        # Direct requirement: "at least 50 rooms (roads)".
        self.assertGreaterEqual(ROAD_LENGTH, 50)


class TestTerrainBands(EvenniaTest):
    def test_band_progression(self):
        self.assertEqual(_band(0), "borderland_fringe")
        self.assertEqual(_band(10), "borderland_fringe")
        self.assertEqual(_band(11), "highland_moor")
        self.assertEqual(_band(25), "fen_country")
        self.assertEqual(_band(35), "salt_marsh")
        self.assertEqual(_band(41), "dune_approach")
        self.assertEqual(_band(ROAD_LENGTH), "dune_approach")


class TestRoadVsOffRoad(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.provider = AmberCoastWildernessMapProvider()

    def test_road_and_offroad_have_different_names_same_band(self):
        road_name = self.provider.get_location_name((0, 3))
        offroad_name = self.provider.get_location_name((2, 3))
        self.assertNotEqual(road_name, offroad_name)

    def test_road_name_changes_by_band(self):
        fringe_name = self.provider.get_location_name((0, 0))
        dune_name = self.provider.get_location_name((0, 45))
        self.assertNotEqual(fringe_name, dune_name)


class TestLiveWilderness(EvenniaTest):
    def setUp(self):
        super().setUp()
        wilderness.create_wilderness(
            name="test_amber_coast_road", mapprovider=AmberCoastWildernessMapProvider()
        )
        self.char1.db.level = 46

    def _enter(self, coordinates=(0, 0)):
        wilderness.enter_wilderness(
            self.char1, coordinates=coordinates, name="test_amber_coast_road"
        )

    def test_entering_sets_a_real_description(self):
        self._enter((0, 0))
        desc = self.char1.location.get_display_desc(self.char1)
        self.assertTrue(desc)

    def test_milestone_appears_every_five_and_counts_down(self):
        self._enter((0, 45))
        desc = self.char1.location.get_display_desc(self.char1)
        self.assertIn("miles to the coast", desc)
        self.assertIn("75 miles to the coast", desc)

    def test_no_milestone_off_the_road(self):
        self._enter((3, 45))
        desc = self.char1.location.get_display_desc(self.char1)
        self.assertNotIn("miles to the coast", desc)

    def test_spawned_encounters_are_real_hostile_npcs(self):
        from world.combat import HostileNPC

        self._enter((0, 0))
        found_one = False
        for _ in range(60):
            exits = {e.key: e for e in self.char1.location.exits}
            ex = exits.get("north")
            ex.at_traverse(self.char1, ex.destination)
            npcs = [o for o in self.char1.location.contents if o.db.race]
            if npcs:
                found_one = True
                self.assertTrue(npcs[0].is_typeclass(HostileNPC, exact=False))
                break
            south_exits = {e.key: e for e in self.char1.location.exits}
            south_exits["south"].at_traverse(self.char1, south_exits["south"].destination)
        self.assertTrue(found_one, "no encounter spawned in 60 attempts - ENCOUNTER_CHANCE regression?")

    def test_encounter_forces_combat_with_a_real_player(self):
        from unittest.mock import PropertyMock, patch
        from world.wilderness_amber_coast import _aggro_on_sight

        npc = create.create_object(
            "world.combat.HostileNPC",
            key="a test attacker",
            location=self.room1,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 1)],
        )
        with patch.object(type(self.char1), "has_account", new_callable=PropertyMock) as mock_has_account:
            mock_has_account.return_value = True
            _aggro_on_sight(npc, self.char1, self.room1)

        self.assertIsNotNone(self.room1.db.combat_turnhandler)
        fighters = self.room1.db.combat_turnhandler.db.fighters
        self.assertIn(self.char1, fighters)
        self.assertIn(npc, fighters)

    def test_sanctuary_blocks_the_forced_fight(self):
        from world.wilderness_amber_coast import _aggro_on_sight

        self.char1.db.sanctuary_active = True
        self.char1.db.sanctuary_level = 999
        npc = create.create_object(
            "world.combat.HostileNPC",
            key="a test attacker",
            location=self.room1,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 1)],
        )
        _aggro_on_sight(npc, self.char1, self.room1)
        self.assertIsNone(self.room1.db.combat_turnhandler)

    def test_non_player_mover_does_not_trigger_aggro(self):
        from world.wilderness_amber_coast import _aggro_on_sight

        mover = create.create_object("typeclasses.characters.Character", key="a stray NPC mover")
        npc = create.create_object(
            "world.combat.HostileNPC",
            key="a test attacker",
            location=self.room1,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 1)],
        )
        _aggro_on_sight(npc, mover, self.room1)
        self.assertIsNone(self.room1.db.combat_turnhandler)

    def test_stale_encounter_is_cleared_on_revisit(self):
        self._enter((0, 10))
        room = self.char1.location
        stray = create.create_object(
            "world.combat.AutoStatNPC",
            key="a leftover bandit",
            location=room,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 46)],
        )
        stray.tags.add(_ENCOUNTER_TAG[0], category=_ENCOUNTER_TAG[1])

        from world.wilderness_amber_coast import AmberCoastWildernessMapProvider as Provider

        Provider().at_prepare_room((0, 10), self.char1, room)

        self.assertFalse(stray.pk)


class TestEncounterCleanup(EvenniaTest):
    def test_cleanup_deletes_a_npc_not_in_combat(self):
        npc = create.create_object(
            "world.combat.AutoStatNPC",
            key="a test encounter",
            location=self.room1,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 46)],
        )
        npc.db.combat_turnhandler = None
        _cleanup_encounter_npc(npc)
        self.assertFalse(npc.pk)

    def test_cleanup_reschedules_instead_of_deleting_mid_fight(self):
        npc = create.create_object(
            "world.combat.AutoStatNPC",
            key="a test encounter",
            location=self.room1,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 46)],
        )
        npc.db.combat_turnhandler = True
        _cleanup_encounter_npc(npc)
        self.assertTrue(npc.pk)
        npc.delete()

    def test_cleanup_on_an_already_deleted_npc_does_not_crash(self):
        npc = create.create_object(
            "world.combat.AutoStatNPC",
            key="a test encounter",
            location=self.room1,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 46)],
        )
        npc.delete()
        _cleanup_encounter_npc(npc)  # must not raise


class TestEnterAmberCoastWildernessExit(EvenniaTest):
    def setUp(self):
        super().setUp()
        wilderness.create_wilderness(
            name="amber_coast_road", mapprovider=AmberCoastWildernessMapProvider()
        )
        self.entrance = create.create_object(
            EnterAmberCoastWildernessExit, key="north", location=self.room1, destination=None
        )
        self.char1.location = self.room1

    def test_traversing_moves_into_the_wilderness_at_the_origin(self):
        self.entrance.at_traverse(self.char1, None)
        self.assertEqual(getattr(self.char1.location, "coordinates", None), (0, 0))
