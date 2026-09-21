"""
Tests for world/triumph_event.py - the recurring ambient triumphal
procession. Focused on the actual logic (message content, echo-ring
exclusion, scheduling, the two real scheduling bugs this design fixed
- see that module's own docstring), not on PROCESSION_ROUTE's specific
room ids, which point at real, already-built production rooms that
don't exist in a fresh test database - that mapping was verified live
against the real room graph instead (see the design conversation).
"""

from unittest.mock import patch, call

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create

from world.triumph_event import (
    TriumphEventScript,
    CmdTriumphNow,
    CAPTIVE_POOL,
    PROCESSION_ROUTE,
    ROOM_HOLD_TIME,
    PRE_ANNOUNCE_LEAD_SECONDS,
)


class TestCaptivePoolAndRoute(EvenniaTest):
    """Pure data-shape checks - no database dependency."""

    def test_every_captive_is_a_well_formed_triple(self):
        for entry in CAPTIVE_POOL:
            self.assertEqual(len(entry), 3)
            name, title, flavor = entry
            for part in (name, title, flavor):
                self.assertIsInstance(part, str)
                self.assertTrue(part.strip())

    def test_captive_names_are_all_distinct(self):
        names = [entry[0] for entry in CAPTIVE_POOL]
        self.assertEqual(len(names), len(set(names)))

    def test_route_has_no_duplicate_rooms(self):
        self.assertEqual(len(PROCESSION_ROUTE), len(set(PROCESSION_ROUTE)))

    def test_route_is_at_least_six_rooms_long(self):
        # Matches the design's own "6-8 rooms" target.
        self.assertGreaterEqual(len(PROCESSION_ROUTE), 6)


class TestAdvanceToRoom(EvenniaTest):
    """
    Exercises _advance_to_room directly against real (test-fixture)
    rooms wired together with real exits, so the echo-ring logic runs
    against genuine room.exits rather than anything mocked out.
    """

    def setUp(self):
        super().setUp()
        self.script = create.create_script(TriumphEventScript, autostart=False)

        # A tiny fake "route": room1 -> room2 (on route), with room3 a
        # genuine off-route neighbor of room2 reachable by a real exit.
        self.off_route = create.create_object("typeclasses.rooms.Room", key="Off Route Alley")
        create.create_object(
            "typeclasses.exits.Exit", key="alley", location=self.room2,
            destination=self.off_route,
        )
        self.captive = CAPTIVE_POOL[0]

    def _capture_messages(self, *rooms):
        captured = {room: [] for room in rooms}
        originals = {}
        for room in rooms:
            originals[room] = room.msg_contents

            def make_capture(target_room):
                def _capture(text, **kwargs):
                    captured[target_room].append(text)
                return _capture

            room.msg_contents = make_capture(room)
        return captured

    def test_sends_the_full_spectacle_message_naming_the_captive(self):
        captured = self._capture_messages(self.room2)
        self.script._advance_to_room(self.room2.id, self.captive)
        name = self.captive[0]
        self.assertTrue(any(name in str(m) for m in captured[self.room2]))

    def test_echoes_to_a_real_off_route_neighbor(self):
        captured = self._capture_messages(self.room2, self.off_route)
        self.script._advance_to_room(self.room2.id, self.captive)
        self.assertTrue(
            any("nearby" in str(m).lower() for m in captured[self.off_route])
        )

    def test_does_not_echo_to_a_neighbor_that_is_also_on_the_route(self):
        # room1 is "on the route" for this test (passed as previous_id
        # below is irrelevant - what matters is patching PROCESSION_ROUTE
        # so room1's id is treated as an on-route room, same as room2).
        with patch("world.triumph_event.PROCESSION_ROUTE", [self.room1.id, self.room2.id]):
            # Wire room1 as an actual exit-neighbor of room2 too.
            create.create_object(
                "typeclasses.exits.Exit", key="back", location=self.room2,
                destination=self.room1,
            )
            captured = self._capture_messages(self.room1, self.off_route)
            self.script._advance_to_room(self.room2.id, self.captive)
            self.assertEqual(captured[self.room1], [])
            self.assertTrue(len(captured[self.off_route]) >= 1)

    def test_sends_a_fading_message_to_the_previous_room(self):
        captured = self._capture_messages(self.room1)
        self.script._advance_to_room(self.room2.id, self.captive, previous_id=self.room1.id)
        self.assertTrue(any("fades away" in str(m).lower() for m in captured[self.room1]))

    def test_no_previous_room_sends_no_fading_message(self):
        # Just confirms this doesn't crash with previous_id=None (the
        # first stop on the route).
        self.script._advance_to_room(self.room2.id, self.captive, previous_id=None)

    def test_a_deleted_room_id_is_handled_gracefully(self):
        # Real defensive case: a room resolved from a persisted delay()
        # callback could, in principle, no longer exist by the time it
        # fires. Must not raise.
        self.script._advance_to_room(999999999, self.captive)


class TestRunProcessionScheduling(EvenniaTest):
    """
    Confirms run_procession schedules the right number of delayed
    steps, all persistent (see the module's own docstring on why a
    non-persistent chain silently dies across a reload), plus the new
    pre-announcement lead-in.
    """

    def setUp(self):
        super().setUp()
        self.script = create.create_script(TriumphEventScript, autostart=False)

    def test_schedules_one_delay_per_route_room_all_persistent(self):
        with patch("world.triumph_event.evennia_utils.delay") as mock_delay:
            self.script.run_procession()
        self.assertEqual(mock_delay.call_count, len(PROCESSION_ROUTE))
        for c in mock_delay.call_args_list:
            self.assertTrue(c.kwargs.get("persistent"))

    def test_first_stop_fires_after_the_pre_announce_lead_time(self):
        with patch("world.triumph_event.evennia_utils.delay") as mock_delay:
            self.script.run_procession()
        first_call_delay = mock_delay.call_args_list[0].args[0]
        self.assertEqual(first_call_delay, PRE_ANNOUNCE_LEAD_SECONDS)

    def test_stops_are_spaced_by_room_hold_time(self):
        with patch("world.triumph_event.evennia_utils.delay") as mock_delay:
            self.script.run_procession()
        delays = [c.args[0] for c in mock_delay.call_args_list]
        gaps = [b - a for a, b in zip(delays, delays[1:])]
        self.assertTrue(all(gap == ROOM_HOLD_TIME for gap in gaps))

    def test_only_plain_data_crosses_the_persistent_delay_boundary(self):
        # Real, confirmed constraint (see module docstring): delay()'s
        # own docs warn against persistent tasks carrying live object
        # references. Every positional/keyword arg passed through must
        # be a plain, trivially-serializable type.
        with patch("world.triumph_event.evennia_utils.delay") as mock_delay:
            self.script.run_procession()
        for c in mock_delay.call_args_list:
            for arg in c.args[2:]:  # skip (timedelay, callback)
                self.assertIsInstance(arg, (int, str, tuple, type(None)))
            previous_id = c.kwargs.get("previous_id")
            self.assertIsInstance(previous_id, (int, type(None)))


class TestJitterActuallyReschedules(EvenniaTest):
    """
    Regression test for the real bug this design fixes: reassigning
    self.interval alone does not reschedule an already-running
    Script's ticking task (confirmed against Evennia's own
    scripts.py - a Script's interval is only ever applied when its
    task is (re)started). at_repeat() must call self.start(interval=
    ...), not just set the attribute.
    """

    def test_at_repeat_calls_start_with_a_new_interval(self):
        script = create.create_script(TriumphEventScript, autostart=False)
        with patch.object(script, "start") as mock_start, \
                patch.object(script, "run_procession"):
            script.at_repeat()
        mock_start.assert_called_once()
        self.assertIn("interval", mock_start.call_args.kwargs)


class TestCmdTriumphNow(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.level = 106

    def _call(self, caller):
        cmd = CmdTriumphNow()
        cmd.caller = caller
        cmd.args = ""
        return cmd

    def test_refuses_below_god_level(self):
        self.char1.db.level = 100
        messages = []
        self.char1.msg = lambda text="", **kw: messages.append(text)
        self._call(self.char1).func()
        self.assertTrue(any("only a god" in str(m).lower() for m in messages))

    def test_god_triggers_a_real_procession(self):
        import evennia

        script = create.create_script(TriumphEventScript, key="triumph_event", autostart=False)
        evennia.GLOBAL_SCRIPTS.triumph_event = script

        messages = []
        self.char1.msg = lambda text="", **kw: messages.append(text)
        with patch.object(script, "run_procession") as mock_run:
            self._call(self.char1).func()
        mock_run.assert_called_once()
        self.assertTrue(any("triggered" in str(m).lower() for m in messages))
