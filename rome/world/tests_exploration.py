"""
Tests for the tiered explorer achievements (world/exploration.py,
world/achievements.py's Wanderer / Well-Traveled / Explorer / Cartographer).

Stub rooms stand in for the hundreds of distinct rooms a real tier needs -
creating 600 real rooms per test would be slow for no extra coverage; the
one thing that needs a real room typeclass (the wilderness exclusion) and
the one real-movement integration test use real rooms.
"""

from evennia.contrib.game_systems.achievements import achievements as contrib
from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

import world.achievements as achievements_module
from world.exploration import counts_for_exploration, record_room_visit
from world.titles import ACHIEVEMENT_TITLES

TIERS = (("wanderer", 100), ("well_traveled", 250), ("explorer", 350), ("cartographer", 600))


class StubRoom:
    """Just enough of a room for the tracker: an id, and 'not wilderness'."""

    def __init__(self, room_id):
        self.id = room_id

    def is_typeclass(self, *args, **kwargs):
        return False


def completed(character, key):
    return bool(contrib._read_player_data(character).get(key, {}).get("completed"))


def visit_many(character, start, count):
    for i in range(start, start + count):
        record_room_visit(character, StubRoom(i))


class TestRecordingRooms(EvenniaTest):
    def test_a_new_room_is_remembered(self):
        self.assertTrue(record_room_visit(self.char1, StubRoom(1)))
        self.assertIn(1, self.char1.db.visited_rooms)

    def test_a_revisit_is_not_a_new_room(self):
        record_room_visit(self.char1, StubRoom(1))
        self.assertFalse(record_room_visit(self.char1, StubRoom(1)))
        self.assertEqual(len(self.char1.db.visited_rooms), 1)

    def test_walking_the_same_ground_forever_never_progresses(self):
        for _ in range(300):
            for room_id in (1, 2, 3):
                record_room_visit(self.char1, StubRoom(room_id))
        self.assertEqual(len(self.char1.db.visited_rooms), 3)
        self.assertFalse(completed(self.char1, "wanderer"))

    def test_real_movement_records_the_room(self):
        self.char1.location = self.room1
        self.char1.move_to(self.room2)
        self.assertIn(self.room2.id, self.char1.db.visited_rooms or set())


class TestWhatDoesNotCount(EvenniaTest):
    def test_a_wilderness_tile_does_not_count(self):
        tile = create.create_object("world.wilderness_rome.FixedWildernessRoom", key="a road tile")
        self.assertFalse(counts_for_exploration(self.char1, tile))
        self.assertFalse(record_room_visit(self.char1, tile))
        self.assertFalse(self.char1.db.visited_rooms)

    def test_a_god_does_not_count(self):
        self.char1.db.level = 101
        self.assertFalse(record_room_visit(self.char1, StubRoom(1)))

    def test_an_npc_does_not_count(self):
        npc = create.create_object("typeclasses.characters.Character", key="a passer-by")
        self.assertIsNone(npc.account)
        self.assertFalse(record_room_visit(npc, StubRoom(1)))

    def test_no_room_does_not_count(self):
        self.assertFalse(counts_for_exploration(self.char1, None))


class TestTheTiers(EvenniaTest):
    def test_each_tier_completes_at_its_own_count_and_not_before(self):
        seen = 0
        for key, target in TIERS:
            visit_many(self.char1, seen, target - 1 - seen)
            seen = target - 1
            self.assertFalse(completed(self.char1, key), "%s completed early" % key)
            visit_many(self.char1, seen, 1)
            seen = target
            self.assertTrue(completed(self.char1, key), "%s did not complete" % key)

    def test_lower_tiers_do_not_complete_higher_ones(self):
        visit_many(self.char1, 0, 100)
        self.assertTrue(completed(self.char1, "wanderer"))
        for key in ("well_traveled", "explorer", "cartographer"):
            self.assertFalse(completed(self.char1, key), key)

    def test_the_explorer_and_cartographer_earn_titles(self):
        visit_many(self.char1, 0, 350)
        self.assertIn("the Explorer", self.char1.db.earned_titles or [])
        self.assertNotIn("the Cartographer", self.char1.db.earned_titles or [])
        visit_many(self.char1, 350, 250)
        self.assertIn("the Cartographer", self.char1.db.earned_titles or [])

    def test_the_lower_tiers_grant_no_title(self):
        self.assertNotIn("wanderer", ACHIEVEMENT_TITLES)
        self.assertNotIn("well_traveled", ACHIEVEMENT_TITLES)


class TestTheAchievementsThemselves(EvenniaTest):
    def _defs(self):
        return [
            getattr(achievements_module, name)
            for name in ("WANDERER", "WELL_TRAVELED", "EXPLORER", "CARTOGRAPHER")
        ]

    def test_the_tiers_ascend(self):
        counts = [d["count"] for d in self._defs()]
        self.assertEqual(counts, sorted(counts))
        self.assertEqual(len(set(counts)), 4)

    def test_no_number_appears_in_a_name_or_description(self):
        # A direct request: get away from hard numbers in the game.
        for d in self._defs():
            for text in (d["name"], d["desc"]):
                self.assertFalse(any(ch.isdigit() for ch in text), text)

    def test_the_top_tier_is_below_the_number_of_ordinary_rooms(self):
        # ~775 mortal-reachable rooms; the top tier must stay reachable.
        self.assertLess(max(d["count"] for d in self._defs()), 775)
