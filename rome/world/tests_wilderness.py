"""
Tests for world/wilderness_rome.py - the bounded, terrain-banded
wilderness map surrounding the road to Germania: the hard map edges,
road-vs-off-road naming/description, milestones, random encounter
spawning (and its self-cleanup, the real gap a live test walk found -
see _schedule_encounter_cleanup's own docstring), and the entrance
exit from "The Road's True Start."
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from evennia.contrib.grid import wilderness

from world.wilderness_rome import (
    RomeWildernessMapProvider,
    ROAD_LENGTH,
    WIDTH,
    _band,
    _cleanup_encounter_npc,
    _ENCOUNTER_TAG,
    EnterWildernessExit,
)


class TestBounds(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.provider = RomeWildernessMapProvider()

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
        # A point far outside any plausible bound must be refused.
        self.assertFalse(self.provider.is_valid_coordinates(None, (10000, 10000)))


class TestTerrainBands(EvenniaTest):
    def test_band_progression_matches_the_tonal_arc(self):
        self.assertEqual(_band(0), "farmland")
        self.assertEqual(_band(5), "farmland")
        self.assertEqual(_band(6), "scrubland")
        self.assertEqual(_band(11), "forest_edge")
        self.assertEqual(_band(17), "deep_woods")
        self.assertEqual(_band(23), "final_approach")
        self.assertEqual(_band(ROAD_LENGTH), "final_approach")


class TestRoadVsOffRoad(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.provider = RomeWildernessMapProvider()

    def test_road_and_offroad_have_different_names_same_band(self):
        road_name = self.provider.get_location_name((0, 3))
        offroad_name = self.provider.get_location_name((2, 3))
        self.assertNotEqual(road_name, offroad_name)

    def test_road_name_changes_by_band(self):
        farmland_name = self.provider.get_location_name((0, 0))
        deep_woods_name = self.provider.get_location_name((0, 20))
        self.assertNotEqual(farmland_name, deep_woods_name)


class TestLiveWilderness(EvenniaTest):
    """Exercises at_prepare_room through the real contrib machinery."""

    def setUp(self):
        super().setUp()
        wilderness.create_wilderness(
            name="test_germania_road", mapprovider=RomeWildernessMapProvider()
        )
        self.char1.db.level = 25

    def _enter(self, coordinates=(0, 0)):
        wilderness.enter_wilderness(self.char1, coordinates=coordinates, name="test_germania_road")

    def test_entering_sets_a_real_description(self):
        self._enter((0, 0))
        desc = self.char1.location.get_display_desc(self.char1)
        self.assertTrue(desc)

    def test_milestone_appears_every_five_and_counts_down(self):
        self._enter((0, 20))
        desc = self.char1.location.get_display_desc(self.char1)
        self.assertIn("miles to Rome", desc)
        self.assertIn("125 miles to Rome", desc)

    def test_no_milestone_off_the_road(self):
        self._enter((3, 20))
        desc = self.char1.location.get_display_desc(self.char1)
        self.assertNotIn("miles to Rome", desc)

    def test_stale_encounter_is_cleared_on_revisit(self):
        self._enter((0, 10))
        room = self.char1.location
        stray = create.create_object(
            "world.combat.AutoStatNPC",
            key="a leftover bandit",
            location=room,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 25)],
        )
        stray.tags.add(_ENCOUNTER_TAG[0], category=_ENCOUNTER_TAG[1])

        # Force the room to be re-prepared for the same coordinates.
        from world.wilderness_rome import RomeWildernessMapProvider as Provider

        Provider().at_prepare_room((0, 10), self.char1, room)

        self.assertFalse(stray.pk)


class TestEncounterCleanup(EvenniaTest):
    def test_cleanup_deletes_a_npc_not_in_combat(self):
        npc = create.create_object(
            "world.combat.AutoStatNPC",
            key="a test encounter",
            location=self.room1,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 25)],
        )
        npc.db.combat_turnhandler = None
        _cleanup_encounter_npc(npc)
        self.assertFalse(npc.pk)

    def test_cleanup_reschedules_instead_of_deleting_mid_fight(self):
        npc = create.create_object(
            "world.combat.AutoStatNPC",
            key="a test encounter",
            location=self.room1,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 25)],
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
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 25)],
        )
        npc.delete()
        _cleanup_encounter_npc(npc)  # must not raise


class TestEnterWildernessExit(EvenniaTest):
    def setUp(self):
        super().setUp()
        wilderness.create_wilderness(
            name="germania_road", mapprovider=RomeWildernessMapProvider()
        )
        self.entrance = create.create_object(
            EnterWildernessExit, key="north", location=self.room1, destination=None
        )
        self.char1.location = self.room1

    def test_traversing_moves_into_the_wilderness_at_the_origin(self):
        self.entrance.at_traverse(self.char1, None)
        self.assertEqual(getattr(self.char1.location, "coordinates", None), (0, 0))
