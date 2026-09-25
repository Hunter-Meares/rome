"""
Tests for world/gathering.py - the gathering half of the crafting
economy (world/recipes.py, world/tests_recipes.py cover the other
half). Covers resource detection (ndb for a recycled wilderness tile,
db for a real authored room like the Ore Vein Shaft), the per-
character cooldown, and CmdGather itself.
"""

import time
from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create

from world.gathering import (
    GATHERABLE_MATERIALS,
    WILDERNESS_SPOT_CHANCE,
    FIXED_NODE_SPOT_CHANCE,
    gather_resource_here,
    cooldown_remaining,
    announce_gather_spot,
    CmdGather,
)


class TestGatherResourceHere(EvenniaTest):
    def test_no_resource_by_default(self):
        self.assertIsNone(gather_resource_here(self.char1))

    def test_ndb_resource_is_found(self):
        self.room1.ndb.gather_resource = "timber"
        self.assertEqual(gather_resource_here(self.char1), "timber")

    def test_db_resource_is_found(self):
        # A real authored room (the Ore Vein Shaft) uses a plain db
        # Attribute rather than ndb, since it isn't a recycled tile.
        self.room1.db.gather_resource = "iron_ore"
        self.assertEqual(gather_resource_here(self.char1), "iron_ore")

    def test_ndb_takes_priority_over_db(self):
        self.room1.db.gather_resource = "iron_ore"
        self.room1.ndb.gather_resource = "timber"
        self.assertEqual(gather_resource_here(self.char1), "timber")

    def test_an_unknown_resource_string_is_ignored(self):
        self.room1.db.gather_resource = "unobtanium"
        self.assertIsNone(gather_resource_here(self.char1))

    def test_no_location_does_not_crash(self):
        self.char1.location = None
        self.assertIsNone(gather_resource_here(self.char1))


class TestCooldown(EvenniaTest):
    def test_ready_by_default(self):
        self.assertEqual(cooldown_remaining(self.char1, "timber"), 0)

    def test_full_cooldown_right_after_gathering(self):
        self.char1.db.gather_cooldowns = {"timber": time.time()}
        remaining = cooldown_remaining(self.char1, "timber")
        self.assertGreater(remaining, GATHERABLE_MATERIALS["timber"]["cooldown"] - 5)

    def test_ready_again_once_the_cooldown_has_passed(self):
        cooldown = GATHERABLE_MATERIALS["timber"]["cooldown"]
        self.char1.db.gather_cooldowns = {"timber": time.time() - cooldown - 10}
        self.assertEqual(cooldown_remaining(self.char1, "timber"), 0)

    def test_cooldowns_are_tracked_independently_per_resource(self):
        self.char1.db.gather_cooldowns = {"timber": time.time()}
        self.assertEqual(cooldown_remaining(self.char1, "iron_ore"), 0)


class TestAnnounceGatherSpot(EvenniaCommandTest):
    """
    Real, direct design request: gathering should reward actually
    exploring, not standing in one spot on demand. announce_gather_spot
    (called from CombatCharacter.at_post_move) is the roll that decides
    whether a resource is even THERE to gather this visit.
    """

    def test_no_room_resource_means_no_spot_and_no_message(self):
        received = []
        self.char1.msg = lambda text="", **kw: received.append(text)
        announce_gather_spot(self.char1)
        self.assertIsNone(self.char1.ndb.gather_spot)
        self.assertEqual(received, [])

    def test_a_hit_sets_the_spot_and_messages(self):
        self.room1.ndb.gather_resource = "timber"
        received = []
        self.char1.msg = lambda text="", **kw: received.append(text)
        with patch("world.gathering.random.random", return_value=0.0):
            announce_gather_spot(self.char1)
        self.assertEqual(self.char1.ndb.gather_spot, "timber")
        self.assertTrue(received)

    def test_a_miss_is_silent(self):
        self.room1.ndb.gather_resource = "timber"
        received = []
        self.char1.msg = lambda text="", **kw: received.append(text)
        with patch("world.gathering.random.random", return_value=0.999):
            announce_gather_spot(self.char1)
        self.assertIsNone(self.char1.ndb.gather_spot)
        self.assertEqual(received, [])

    def test_a_wilderness_tile_uses_the_wilderness_chance(self):
        # ndb.gather_resource (unset here) is exactly what marks a
        # recycled wilderness tile - a roll between the two chance
        # values should miss on the (lower) wilderness rate.
        self.room1.ndb.gather_resource = "timber"
        roll_between = (WILDERNESS_SPOT_CHANCE + FIXED_NODE_SPOT_CHANCE) / 2
        with patch("world.gathering.random.random", return_value=roll_between):
            announce_gather_spot(self.char1)
        self.assertIsNone(self.char1.ndb.gather_spot)

    def test_a_fixed_node_room_uses_the_higher_chance(self):
        # A plain db.gather_resource (not ndb) is exactly what marks a
        # real, permanently-authored room like the Ore Vein Shaft -
        # the same roll that misses in the wilderness should hit here.
        self.room1.db.gather_resource = "iron_ore"
        roll_between = (WILDERNESS_SPOT_CHANCE + FIXED_NODE_SPOT_CHANCE) / 2
        with patch("world.gathering.random.random", return_value=roll_between):
            announce_gather_spot(self.char1)
        self.assertEqual(self.char1.ndb.gather_spot, "iron_ore")

    def test_a_persistent_room_can_opt_into_the_wilderness_chance(self):
        # Real design fix: a persistent room isn't automatically "no
        # ground left to explore" just because it's db-based rather
        # than a recycled wilderness tile - a real multi-room mine
        # complex needs the same lower, meaningful-exploration chance
        # the wilderness uses, even though every room in it is a real,
        # permanently-authored room.
        self.room1.db.gather_resource = "iron_ore"
        self.room1.db.gather_uses_wilderness_chance = True
        roll_between = (WILDERNESS_SPOT_CHANCE + FIXED_NODE_SPOT_CHANCE) / 2
        with patch("world.gathering.random.random", return_value=roll_between):
            announce_gather_spot(self.char1)
        self.assertIsNone(self.char1.ndb.gather_spot)

    def test_still_on_cooldown_never_spots_anything(self):
        self.room1.ndb.gather_resource = "timber"
        self.char1.db.gather_cooldowns = {"timber": time.time()}
        with patch("world.gathering.random.random", return_value=0.0):
            announce_gather_spot(self.char1)
        self.assertIsNone(self.char1.ndb.gather_spot)

    def test_a_previous_spot_is_cleared_on_a_fresh_roll(self):
        self.char1.ndb.gather_spot = "timber"
        self.room1.ndb.gather_resource = None
        announce_gather_spot(self.char1)
        self.assertIsNone(self.char1.ndb.gather_spot)


class TestCmdGather(EvenniaCommandTest):
    def test_nothing_to_gather_by_default(self):
        result = self.call(CmdGather(), "", caller=self.char1)
        self.assertIn("nothing to gather", result)

    def test_no_spot_found_yet_is_refused_even_with_a_real_resource_here(self):
        self.room1.ndb.gather_resource = "timber"
        result = self.call(CmdGather(), "", caller=self.char1)
        self.assertIn("nothing to actually gather", result)

    def test_gathering_spawns_the_right_material_into_inventory(self):
        self.room1.ndb.gather_resource = "timber"
        self.char1.ndb.gather_spot = "timber"
        before = set(self.char1.contents)

        self.call(CmdGather(), "", caller=self.char1)

        gained = [o for o in self.char1.contents if o not in before]
        self.assertEqual(len(gained), 1)
        self.assertIn("timber", gained[0].tags.get(category="crafting_material") or "")

    def test_gathering_clears_the_spot_flag(self):
        self.room1.ndb.gather_resource = "timber"
        self.char1.ndb.gather_spot = "timber"
        self.call(CmdGather(), "", caller=self.char1)
        self.assertIsNone(self.char1.ndb.gather_spot)

    def test_gathering_sets_a_cooldown(self):
        self.room1.ndb.gather_resource = "timber"
        self.char1.ndb.gather_spot = "timber"
        self.assertEqual((self.char1.db.gather_cooldowns or {}).get("timber"), None)

        self.call(CmdGather(), "", caller=self.char1)

        self.assertIsNotNone(self.char1.db.gather_cooldowns["timber"])

    def test_gathering_again_immediately_is_refused(self):
        self.room1.ndb.gather_resource = "timber"
        self.char1.ndb.gather_spot = "timber"
        self.call(CmdGather(), "", caller=self.char1)
        before = set(self.char1.contents)

        self.char1.ndb.gather_spot = "timber"  # a second lucky spot roll
        result = self.call(CmdGather(), "", caller=self.char1)

        self.assertIn("try again in about", result)
        self.assertEqual(set(self.char1.contents), before)

    def test_a_different_resource_has_its_own_independent_cooldown(self):
        self.room1.ndb.gather_resource = "timber"
        self.char1.ndb.gather_spot = "timber"
        self.call(CmdGather(), "", caller=self.char1)

        self.room1.ndb.gather_resource = "iron_ore"
        self.char1.ndb.gather_spot = "iron_ore"
        result = self.call(CmdGather(), "", caller=self.char1)

        self.assertNotIn("try again in about", result)


class TestGatheringWorksForAPacifist(EvenniaCommandTest):
    """
    The whole point of this system existing at all - see world/
    pacifism.py's own docstring on why non-combat play needed a real
    repeatable activity to be more than a promise.
    """

    def test_a_pacifist_can_gather_freely(self):
        self.char1.db.pacifist = True
        self.room1.ndb.gather_resource = "iron_ore"
        self.char1.ndb.gather_spot = "iron_ore"

        result = self.call(CmdGather(), "", caller=self.char1)

        self.assertIn("You gather", result)
