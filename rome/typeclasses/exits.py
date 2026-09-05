"""
Exits

Exits are connectors between rooms. An exit is normal Object that
sits inside the room the exit is *from*, and has a destination
attribute set to the room the exit *leads to*. Exits use the property
'destination' to point back to this room and use a special Lockable
called 'traverse' to permit access.

This is the default Exit class used everywhere @dig, @tunnel, and
@open create a new exit - editing this one file changes the behavior
of every exit already in the game, not just future ones.
"""

from evennia.objects.objects import DefaultExit

from .objects import ObjectParent


# The standard compass/vertical short-form aliases, matching Evennia's
# own CmdTunnel convention exactly (evennia/commands/default/building.py) -
# not invented here, just made automatic instead of opt-in.
STANDARD_DIRECTION_ALIASES = {
    "north": "n", "south": "s", "east": "e", "west": "w",
    "northeast": "ne", "northwest": "nw", "southeast": "se", "southwest": "sw",
    "up": "u", "down": "d", "in": "i", "out": "o",
}


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects
    except they defines the `destination` property and overrides some
    hooks and methods to represent the exits.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like
    this.
    """

    def at_object_creation(self):
        """
        A real bug found live: a player typed 's' to go south and got
        "Command 's' is not available" - full "south" worked fine.
        Evennia's own @tunnel/@open builder commands auto-add the
        standard short alias (n/s/e/w/etc, see
        STANDARD_DIRECTION_ALIASES above) when you name an exit one of
        the 12 recognized direction words, but that's a courtesy those
        two commands add themselves - it's not something
        DefaultExit.at_object_creation() does on its own. Almost every
        exit in this game was created directly in batch-build scripts
        (create.create_object(..., key="south", ...)), bypassing that
        courtesy entirely. A live database sweep after this was found
        turned up 623 of the game's 1265 exits missing their short
        alias - repaired once directly, but any future exit created
        the same way would have the identical problem, so it's fixed
        here at the root instead: any exit whose key is exactly one of
        the 12 standard words gets its short alias for free, from
        every creation path, without needing to remember to pass it.
        An exit with a real custom key (not a bare direction word)
        is completely unaffected.
        """
        super().at_object_creation()
        short = STANDARD_DIRECTION_ALIASES.get((self.key or "").strip().lower())
        if short:
            self.aliases.add(short)

    def get_display_desc(self, looker, **kwargs):
        """
        By default, looking directly at an exit ('look north', 'look
        <exit name>') just shows a generic "This is an exit."
        placeholder unless someone manually sets a custom desc on it -
        which nobody's going to reliably do across hundreds of exits.
        This override shows where the exit actually leads instead,
        which is genuinely useful for navigation and costs nothing to
        maintain, since it's computed automatically from the exit's
        destination rather than needing to be hand-written per exit.

        A manually-set db.desc (if a builder deliberately wants
        unique flavor text on a specific exit - a fancy carved
        archway, say) still takes priority over this default.
        """
        if self.db.desc:
            return self.db.desc
        if self.destination:
            return "The way leads to |w%s|n." % self.destination.get_display_name(looker)
        return super().get_display_desc(looker, **kwargs)
