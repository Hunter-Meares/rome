"""
Tests for world/doors.py's DescriptiveDoor - specifically its
at_traverse override, added alongside typeclasses/exits.py's Exit fix
for the same real bug: SimpleDoor (the contrib DescriptiveDoor
extends) inherits DefaultExit.at_traverse directly, which calls
move_to(..., move_type="traverse") - not "move" - silently exempting
every door in the game from the movement-SP cost and from the new
"You walk <door>." feedback message, since DescriptiveDoor bypasses
typeclasses/exits.py's Exit entirely (SimpleDoor extends DefaultExit
directly, not this project's own Exit class).
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create

from world.combat import MOVEMENT_SP_COST


class TestDescriptiveDoorChargesMovementSP(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.combat_turnhandler = None
        self.char1.db.resting = False
        self.char1.db.is_dead = False
        self.char1.db.hp = 100
        self.char1.db.level = 1
        self.door = create.create_object(
            "world.doors.DescriptiveDoor",
            key="west",
            aliases=["door", "w"],
            location=self.room1,
            destination=self.room2,
        )

    def test_traversal_deducts_movement_sp(self):
        self.char1.db.sp = 10
        self.char1.location = self.room1
        self.door.at_traverse(self.char1, self.room2)
        self.assertEqual(self.char1.db.sp, 10 - MOVEMENT_SP_COST)
        self.assertEqual(self.char1.location, self.room2)

    def test_walk_message_sent_on_successful_traversal(self):
        self.char1.db.sp = 10
        self.char1.location = self.room1
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)
        self.door.at_traverse(self.char1, self.room2)
        # Substring search, not exact list membership - the real
        # message has a deliberate trailing blank-line separator (see
        # world/combat.py).
        self.assertTrue(any("You walk west." in str(m) for m in captured))

    def test_traversal_blocked_when_out_of_sp_gives_no_walk_message(self):
        # Note: the door's OWN lock (open/closed) is checked earlier,
        # in ExitCommand.func() before at_traverse is ever called - not
        # something at_traverse itself re-checks, so it isn't exercised
        # by calling at_traverse directly here. This only covers the
        # movement-SP gate this fix actually touches.
        self.char1.db.sp = 0
        self.char1.location = self.room1
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)
        self.door.at_traverse(self.char1, self.room2)
        self.assertEqual(self.char1.location, self.room1)
        self.assertNotIn("You walk west.", captured)


class TestDescriptiveDoorStandardDirectionAliases(EvenniaTest):
    """
    Same real bug and same fix as typeclasses/exits.py's Exit - a door
    named after a standard direction needs its short alias too, and
    SimpleDoor (DescriptiveDoor's real parent) bypasses that class
    entirely, extending DefaultExit directly instead.
    """

    def test_south_door_gets_s_alias_automatically(self):
        door = create.create_object(
            "world.doors.DescriptiveDoor",
            key="south",
            location=self.room1,
            destination=self.room2,
        )
        self.assertIn("s", [a.lower() for a in door.aliases.all()])

    def test_non_direction_door_key_is_unaffected(self):
        door = create.create_object(
            "world.doors.DescriptiveDoor",
            key="the cellar door",
            location=self.room1,
            destination=self.room2,
        )
        self.assertEqual(list(door.aliases.all()), [])
