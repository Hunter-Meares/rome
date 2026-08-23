"""
In-game room/exit building menu

Wraps Evennia's building_menu contrib (a real, ready-made menu
framework - press a letter, edit a field, no Python required) around
Rome's own rooms and exits. Deliberately scoped to rooms/exits only:
NPCs, weapons, armor, and other items are already well covered by
Evennia's own stock 'spawn' command (spawn/list modules shows every
prototype in world/prototypes.py, spawn <key> creates one) - no need
to duplicate that here, just to make it discoverable via CmdBuild's
own help text.

Gated to Aedilis (level 103) or higher - see the Cursus Divinorum tier
ladder in world/combat.py's GOD_TIERS.
"""

from evennia.contrib.base_systems.building_menu import BuildingMenu
from evennia.utils import create
from evennia import CmdSet
from commands.command import Command

_OPPOSITES = {
    "north": "south", "south": "north", "east": "west", "west": "east",
    "up": "down", "down": "up", "in": "out", "out": "in",
    "northeast": "southwest", "southwest": "northeast",
    "northwest": "southeast", "southeast": "northwest",
}

_ALIASES = {
    "north": "n", "south": "s", "east": "e", "west": "w", "up": "u", "down": "d",
    "northeast": "ne", "northwest": "nw", "southeast": "se", "southwest": "sw",
}


def _glance_exits(room):
    if not room.exits:
        return "\n  |rNo exits yet|n"
    lines = []
    for ex in room.exits:
        dest = ex.destination
        lines.append(
            "  |y%s|n -> %s" % (ex.key, "%s(#%d)" % (dest.key, dest.id) if dest else "nowhere")
        )
    return "\n" + "\n".join(lines)


def _exits_text(room):
    return (
        "-------------------------------------------------------------------------------\n"
        "Exits from %s(#%d)\n"
        "%s\n\n"
        "Type |wnew <direction> = <destination>|n to add a new exit (destination can be\n"
        "a room name or #id) - for the eight standard compass/up/down/in/out directions\n"
        "this also creates the matching return exit back here automatically.\n"
        "Type |wdel <direction>|n to remove just that one exit.\n"
        "Use |w@|n to go back to the main menu."
        % (room.key, room.id, _glance_exits(room))
    )


def _exits_on_nomatch(caller, room, string):
    string = string.strip()
    low = string.lower()

    if low.startswith("new ") and "=" in string:
        direction, _, dest_name = string[4:].partition("=")
        direction = direction.strip().lower()
        dest_name = dest_name.strip()
        if not direction or not dest_name:
            caller.msg("Usage: new <direction> = <destination>")
            return

        existing = [e.key.lower() for e in room.exits]
        if direction in existing:
            caller.msg("There's already an exit called '%s' here." % direction)
            return

        dest = caller.search(dest_name, global_search=True)
        if not dest:
            return

        exit_typeclass = "typeclasses.exits.Exit"
        new_exit = create.create_object(exit_typeclass, key=direction, location=room, destination=dest)
        if direction in _ALIASES:
            new_exit.aliases.add(_ALIASES[direction])
        caller.msg("|gCreated exit '%s' to %s.|n" % (direction, dest.key))

        back_dir = _OPPOSITES.get(direction)
        if back_dir and back_dir not in [e.key.lower() for e in dest.exits]:
            back_exit = create.create_object(exit_typeclass, key=back_dir, location=dest, destination=room)
            if back_dir in _ALIASES:
                back_exit.aliases.add(_ALIASES[back_dir])
            caller.msg("|g(Also created the return exit '%s' back here.)|n" % back_dir)
        return

    if low.startswith("del "):
        direction = string[4:].strip().lower()
        for ex in room.exits:
            if ex.key.lower() == direction:
                ex.delete()
                caller.msg("|yDeleted exit '%s'.|n" % direction)
                return
        caller.msg("No exit called '%s' here." % direction)
        return

    caller.msg("Usage: new <direction> = <destination> | del <direction>")


def _glance_tags(room):
    tags = room.tags.all()
    return ", ".join(tags) if tags else "|rNo tags|n"


def _tags_text(room):
    return (
        "-------------------------------------------------------------------------------\n"
        "Tags on %s(#%d): %s\n\n"
        "Type |wadd <tag>|n or |wdel <tag>|n.\nUse |w@|n to go back to the main menu."
        % (room.key, room.id, _glance_tags(room))
    )


def _tags_on_nomatch(caller, room, string):
    string = string.strip()
    low = string.lower()
    if low.startswith("add "):
        tag = string[4:].strip()
        room.tags.add(tag)
        caller.msg("|gAdded tag '%s'.|n" % tag)
        return
    if low.startswith("del "):
        tag = string[4:].strip()
        room.tags.remove(tag)
        caller.msg("|yRemoved tag '%s'.|n" % tag)
        return
    caller.msg("Usage: add <tag> | del <tag>")


class RoomBuildingMenu(BuildingMenu):
    """
    In-game editor for a room: title, description, exits, and tags.
    """

    def init(self, room):
        self.add_choice("title", key="t", attr="key", glance="{obj.key}")
        self.add_choice_edit("description", key="d")
        self.add_choice(
            "exits", key="e", glance=_glance_exits, text=_exits_text, on_nomatch=_exits_on_nomatch
        )
        self.add_choice(
            "tags", key="g", glance=_glance_tags, text=_tags_text, on_nomatch=_tags_on_nomatch
        )


class CmdBuild(Command):
    """
    Open an in-game menu to edit a room - no Python required.

    Usage:
      build
      build <room>

    Opens a menu on the room you're standing in (or the named/#id
    room given) letting you change its title and description, add or
    remove exits, and manage tags, all by pressing a letter and typing
    - no batch scripts or 'evennia shell' needed for straightforward
    world-building.

    For NPCs, weapons, armor, or other items, use Evennia's own
    'spawn' command instead - it already covers this well:
      spawn/list modules   - see every prototype in world/prototypes.py
      spawn <prototype>    - create one here

    Requires Aedilis (level 103) or higher.
    """

    key = "build"
    aliases = ["redit"]
    help_category = "building"

    def func(self):
        caller = self.caller
        level = caller.db.level or 0
        is_superuser = bool(caller.account and caller.account.is_superuser)
        if level < 103 and not is_superuser:
            caller.msg("You lack the authority to reshape the world.")
            return

        if self.args:
            room = caller.search(self.args.strip(), global_search=True)
            if not room:
                return
        else:
            room = caller.location
            if not room:
                caller.msg("You have no location to edit.")
                return

        menu = RoomBuildingMenu(caller, room)
        menu.open()


class RomeBuildingCmdSet(CmdSet):
    """The in-game room/exit building menu."""

    key = "Rome Building CmdSet"

    def at_cmdset_creation(self):
        self.add(CmdBuild())
