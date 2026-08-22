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


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects
    except they defines the `destination` property and overrides some
    hooks and methods to represent the exits.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like
    this.
    """

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
