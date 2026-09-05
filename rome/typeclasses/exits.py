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

    def at_traverse(self, traversing_object, target_location, **kwargs):
        """
        A real, previously-undiscovered bug found while investigating
        a live "movement gives no feedback" complaint: Evennia's own
        DefaultExit.at_traverse (which this would otherwise inherit
        unchanged) calls move_to(..., move_type="traverse") - not
        "move". CombatCharacter.at_pre_move's whole movement-SP-cost
        gate (world/combat.py's _check_and_pay_movement_sp) only
        charges anything when move_type == "move" *exactly* - so every
        ordinary exit traversal in the entire game has been silently
        exempt from the SP cost the whole time, despite that system
        being fully built, documented, and tested (against a hand-
        supplied move_type="move" in isolation - see
        tests_combat_commands.py's TestMovementSPCost docstring, which
        explicitly never exercised a real Exit). Confirmed live: an
        actual traversal through a real Exit left SP completely
        unchanged. Fixed here by reimplementing at_traverse with the
        corrected move_type instead of calling super() - everything
        else (at_post_traverse/at_failed_traverse/err_traverse) is
        preserved exactly as DefaultExit.at_traverse already does it.

        Also where "You walk <exit>." (a separate, real player
        complaint - movement gave literally no feedback before the
        new room's description just appeared) actually needs to live:
        NOT here, before calling move_to() - that would risk printing
        a false "You walk south." immediately followed by "You're too
        exhausted to go on" if at_pre_move's own SP check then blocks
        the move a moment later. It's sent instead from inside
        CombatCharacter.at_pre_move itself (world/combat.py), the
        exact moment a move is confirmed to actually proceed, via the
        exit_obj kwarg move_to() already threads through to
        at_pre_move for free.
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
