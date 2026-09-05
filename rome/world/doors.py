"""
Doors

Extends Evennia's SimpleDoor contrib (evennia.contrib.grid.simpledoor)
with things the base contrib doesn't handle:

1. A door's open/closed state shows directly in the room's exit list
   ("west (closed)"), so a player can see a door is shut before
   walking into it, rather than getting a "you can't go that way"
   surprise with zero warning.
2. Natural messages throughout - "The door to the west is closed."
   instead of "west is closed.", "You close the door to the west."
   instead of "You close west." - when the door's key is a direction
   (matching the convention we've settled on: key = direction, "door"
   as an alias), or "the <name>" for doors given a purely descriptive
   name instead.

To use: create doors with BOTH the door typeclass and the command set
from the very start, not by creating a plain SimpleDoor and swapping
its typeclass afterward - @typeclass re-runs at_object_creation on
SimpleDoor, which resets db.return_exit to None and breaks the
open/close link between the two sides. Always create fresh with:
    @open door;west;w:world.doors.DescriptiveDoor = <destination>
"""

from evennia.contrib.grid.simpledoor.simpledoor import SimpleDoor, CmdOpenCloseDoor
from evennia.utils.utils import inherits_from

from typeclasses.exits import STANDARD_DIRECTION_ALIASES


_DIRECTIONS = {
    "north", "south", "east", "west",
    "northeast", "northwest", "southeast", "southwest",
    "up", "down", "in", "out",
}


def _door_phrase(door):
    """Returns 'door to the west' or 'iron door', without a leading article."""
    if door.key.lower() in _DIRECTIONS:
        return "door to the %s" % door.key
    return door.key


class DescriptiveDoor(SimpleDoor):
    """
    See module docstring - a SimpleDoor with visible open/closed
    state and a more natural closed-door message.

    Also restores the "look <exit>" destination-preview behavior
    every other exit in the game already has (see typeclasses/
    exits.py) - DescriptiveDoor extends the contrib's SimpleDoor,
    which extends Evennia's base DefaultExit directly, completely
    bypassing our custom Exit class and its fix. Without this
    override, "look <door>" would fall back to the generic "This is
    an exit." placeholder that motivated that fix in the first place.
    """

    def at_object_creation(self):
        """
        Same reasoning as typeclasses/exits.py's Exit.at_object_creation
        - SimpleDoor extends DefaultExit directly, completely bypassing
        that fix (and its own docstring's "623 of 1265 exits missing
        their short alias" bug) the same way it bypasses
        get_display_desc below. A door named "south" needs 's' to
        work exactly as much as a plain exit does.
        """
        super().at_object_creation()
        short = STANDARD_DIRECTION_ALIASES.get((self.key or "").strip().lower())
        if short:
            self.aliases.add(short)

    def get_display_desc(self, looker, **kwargs):
        if self.db.desc:
            return self.db.desc
        if self.destination:
            return "The way leads to |w%s|n." % self.destination.get_display_name(looker)
        return super().get_display_desc(looker, **kwargs)

    def get_display_name(self, looker, **kwargs):
        name = super().get_display_name(looker, **kwargs)
        if not self.locks.check(looker, "traverse"):
            return "%s |r(closed)|n" % name
        return name

    def at_traverse(self, traversing_object, target_location, **kwargs):
        """
        Same reasoning and same duplication-over-multi-inheritance
        precedent as get_display_desc above - SimpleDoor extends
        DefaultExit directly, bypassing typeclasses/exits.py's Exit
        (and the real move_type="traverse"-vs-"move" fix that lives
        there; see that class's own at_traverse docstring for the full
        story) entirely. Without this, walking through any door in the
        game would stay silently exempt from the movement-SP cost and
        would never get the "You walk <door>." feedback message every
        other exit now has.
        """
        source_location = traversing_object.location
        if traversing_object.move_to(
            target_location, move_type="move", exit_obj=self, **kwargs
        ):
            self.at_post_traverse(traversing_object, source_location)
        else:
            if self.db.err_traverse:
                traversing_object.msg(self.db.err_traverse)
            else:
                self.at_failed_traverse(traversing_object)

    def at_failed_traverse(self, traversing_object):
        traversing_object.msg("The %s is closed." % _door_phrase(self))


class DescriptiveOpenCloseDoor(CmdOpenCloseDoor):
    """
    Same open/close command as the base SimpleDoor contrib, but with
    natural messages - "You close the door to the west." instead of
    "You close west." Registered after SimpleDoorCmdSet in
    default_cmdsets.py so it overrides the base command for the same
    key.
    """

    def func(self):
        if not self.args:
            self.caller.msg("Usage: open||close <door>")
            return

        door = self.caller.search(self.args)
        if not door:
            return
        if not inherits_from(door, SimpleDoor):
            self.caller.msg("This is not a door.")
            return

        phrase = _door_phrase(door)

        if self.cmdstring == "open":
            if door.locks.check(self.caller, "traverse"):
                self.caller.msg("The %s is already open." % phrase)
            else:
                door.setlock("traverse:true()")
                self.caller.msg("You open the %s." % phrase)
        else:  # close
            if not door.locks.check(self.caller, "traverse"):
                self.caller.msg("The %s is already closed." % phrase)
            else:
                door.setlock("traverse:false()")
                self.caller.msg("You close the %s." % phrase)