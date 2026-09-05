"""
Tests for world/worldcheck.py - the connectivity/duplicate-check tool.

Each test builds a small, deliberate room/exit graph reproducing the
real incident that check exists to catch (see each check function's
own docstring for which one), confirming it's actually caught, plus a
matching "clean" case confirming no false positive.
"""

from evennia.utils.create import create_object
from evennia.utils.test_resources import EvenniaTest

from world.worldcheck import (
    check_duplicate_room_names,
    check_exit_collisions,
    check_broken_exits,
    check_reachability,
    check_one_way_exits,
    check_missing_direction_aliases,
    check_thin_descriptions,
)


def _room(key, desc="A perfectly ordinary room."):
    room = create_object("typeclasses.rooms.Room", key=key)
    room.db.desc = desc
    return room


def _exit(key, location, destination, aliases=None):
    return create_object(
        "typeclasses.exits.Exit",
        key=key,
        location=location,
        destination=destination,
        aliases=aliases or [],
    )


class TestDuplicateRoomNames(EvenniaTest):
    def test_catches_a_real_duplicate(self):
        a = _room("The Quiet Switchback")
        b = _room("The Quiet Switchback")
        findings = check_duplicate_room_names()
        names = [name for name, rooms in findings]
        self.assertIn("the quiet switchback", names)
        matched = next(rooms for name, rooms in findings if name == "the quiet switchback")
        self.assertIn(a, matched)
        self.assertIn(b, matched)

    def test_unique_names_not_flagged(self):
        _room("A Wholly Unique Room Name Xyzzy")
        findings = check_duplicate_room_names()
        names = [name for name, rooms in findings]
        self.assertNotIn("a wholly unique room name xyzzy", names)


class TestExitCollisions(EvenniaTest):
    def test_catches_two_exits_same_direction(self):
        hub = _room("Grove of Champions")
        a = _room("Blessed Fields")
        b = _room("Gardens of the Fortunate")
        _exit("west", hub, a)
        _exit("west", hub, b)
        findings = check_exit_collisions()
        rooms_with_collisions = [room for room, key, exits in findings]
        self.assertIn(hub, rooms_with_collisions)

    def test_distinct_directions_not_flagged(self):
        hub = _room("Clean Hub")
        a = _room("Clean North")
        b = _room("Clean South")
        _exit("north", hub, a)
        _exit("south", hub, b)
        findings = check_exit_collisions()
        rooms_with_collisions = [room for room, key, exits in findings]
        self.assertNotIn(hub, rooms_with_collisions)


class TestBrokenExits(EvenniaTest):
    def test_catches_null_destination(self):
        # Can't reproduce this via target.delete() - Evennia's own
        # delete() proactively calls clear_exits() and removes the
        # exit itself first, and create_object(destination=None) gets
        # silently defaulted to the exit's own location (DefaultExit's
        # basetype_setup safety net). A real broken exit's destination
        # only ends up as bare None via a lower-level path than either
        # of those - reproduced directly here instead.
        room = _room("Room With A Broken Exit")
        target = _room("Soon To Be Deleted")
        ex = _exit("nowhere", room, target)
        ex.db_destination = None
        ex.save()
        findings = check_broken_exits()
        self.assertIn(ex, findings)

    def test_valid_exit_not_flagged(self):
        a = _room("Valid A")
        b = _room("Valid B")
        ex = _exit("east", a, b)
        findings = check_broken_exits()
        self.assertNotIn(ex, findings)


class TestReachability(EvenniaTest):
    def test_finds_a_genuinely_unreachable_room(self):
        start = _room("Entry Point")
        connected = _room("Connected Room")
        orphan = _room("Orphaned Room")
        _exit("in", start, connected)

        reachable, unreachable = check_reachability(start=start)
        self.assertIn(connected, reachable)
        self.assertIn(orphan, unreachable)

    def test_duplicate_network_shows_up_as_a_reachable_count_jump(self):
        """
        Simulates the actual Underworld v1/v2 incident: a second,
        parallel network connected to the same entry point should
        just show up as more reachable rooms, not go unnoticed.
        """
        start = _room("Threshold of Return")
        v1_room = _room("V1 Network Room")
        v2_room = _room("V2 Network Room")
        _exit("path1", start, v1_room)
        _exit("path2", start, v2_room)

        reachable, unreachable = check_reachability(start=start)
        self.assertIn(v1_room, reachable)
        self.assertIn(v2_room, reachable)
        # Not asserting unreachable == [] - EvenniaTest's own fixture
        # rooms (self.room1 etc.) live in the same test DB and are
        # legitimately unreachable from this test's own start room.
        self.assertNotIn(v1_room, unreachable)
        self.assertNotIn(v2_room, unreachable)


class TestOneWayExits(EvenniaTest):
    def test_catches_a_real_one_way_gap(self):
        tunnel = _room("Maintenance Tunnel")
        checkpoint = _room("Guard Checkpoint")
        cistern = _room("Flooded Cistern")
        _exit("east", tunnel, checkpoint)
        # Checkpoint's only exit goes sideways, not back to the tunnel.
        _exit("east", checkpoint, cistern)

        findings = check_one_way_exits()
        flagged_exits = [ex.key for ex in findings if ex.location == tunnel]
        self.assertIn("east", flagged_exits)

    def test_symmetric_exits_not_flagged(self):
        a = _room("Symmetric A")
        b = _room("Symmetric B")
        _exit("north", a, b)
        _exit("south", b, a)

        findings = check_one_way_exits()
        self.assertFalse(any(ex.location == a and ex.key == "north" for ex in findings))


class TestMissingDirectionAliases(EvenniaTest):
    def test_catches_a_direction_exit_with_no_alias(self):
        """
        typeclasses/exits.py's Exit.at_object_creation() now adds the
        standard short alias automatically for any of the 12 direction
        words (the actual root fix for the bug this checker exists to
        catch) - so _exit("west", a, b) alone no longer reproduces a
        genuinely alias-less exit the way it used to. This checker
        stays valuable as a safety net regardless (an exit renamed to
        a direction word after creation, or created some other way
        that skips at_object_creation, would still slip through
        un-fixed) - the alias is stripped back off by hand here so the
        test still exercises that safety net specifically, rather than
        the now-automatic creation-time fix.
        """
        a = _room("Alias Test A")
        b = _room("Alias Test B")
        ex = _exit("west", a, b)
        ex.aliases.clear()
        findings = check_missing_direction_aliases()
        flagged = [e for e, expected in findings]
        self.assertIn(ex, flagged)

    def test_exit_with_correct_alias_not_flagged(self):
        a = _room("Alias OK A")
        b = _room("Alias OK B")
        ex = _exit("west", a, b, aliases=["w"])
        findings = check_missing_direction_aliases()
        flagged = [e for e, expected in findings]
        self.assertNotIn(ex, flagged)

    def test_non_direction_exit_names_ignored(self):
        a = _room("Custom Exit A")
        b = _room("Custom Exit B")
        ex = _exit("climb the ladder", a, b)
        findings = check_missing_direction_aliases()
        flagged = [e for e, expected in findings]
        self.assertNotIn(ex, flagged)


class TestThinDescriptions(EvenniaTest):
    def test_catches_an_empty_description(self):
        room = _room("Gardens of the Fortunate", desc="")
        findings = check_thin_descriptions()
        flagged = [r for r, word_count in findings]
        self.assertIn(room, flagged)

    def test_real_description_not_flagged(self):
        room = _room(
            "A Well-Described Room",
            desc="A genuinely long and descriptive passage full of real atmosphere and detail.",
        )
        findings = check_thin_descriptions()
        flagged = [r for r, word_count in findings]
        self.assertNotIn(room, flagged)
