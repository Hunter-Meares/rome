"""
Room

Rooms are simple containers that has no location of their own.

"""
from evennia.objects.objects import DefaultRoom
from evennia.utils.utils import delay

from .objects import ObjectParent


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects.

    """

    pass


class ZeusThroneRoom(ObjectParent, DefaultRoom):
    def at_object_receive(self, obj, source_location, move_type="move", **kwargs):
        """
        Called when something arrives in this room. Only greets actual
        player characters (skips items, NPCs being moved around, etc.),
        and only messages the specific character who arrived - not the
        whole room.
        """
        if not obj.has_account:
            return
        delay(3, callback=lambda: obj.msg("|cArgus|n turns his many eyes towards you as you enter."))


# Orientation sequence shown to brand-new characters arriving in the
# starting cell - deliberately OOC/tutorial in tone (commands, not
# lore), since Old Milo (see world/prototypes.py OLD_MILO) is meant to
# cover the in-character "what do I actually do" guidance separately.
# Kept as plain messages with a short pause between each rather than
# one big dump, so it doesn't scroll past before a brand-new player
# has a chance to read it.
CELL_INTRO_MESSAGES = [
    "|YWelcome to Rome: The Eternal City.|n",
    "|c>> Type |Whelp|c at any time to see the full list of commands available to you.|n",
    "|c>> Type |Wpublic <message>|c to talk to other players online right now, even if you can't see them from here.|n",
    "|c>> Type |Wstats|c to see your character sheet, or |Wspellinfo|c / |Wskillinfo|c to see what your class can learn as you grow.|n",
    "|c>> Type |Whelp newbie|c for the full walkthrough of what to do first, or |Wjourney|c any time for a quick, personal suggestion.|n",
    "|YWhen you're ready to see what's beyond these cells, look for the way out.|n",
]


def _send_message_sequence(character, messages, index=0):
    """
    Shared engine behind _send_cell_intro/_send_milo_greeting/
    _send_atrium_intro below (previously three near-identical copies
    of this same logic - unified here after a real live bug and a
    real live complaint both turned out to need the identical fix
    applied to all three). Sends a list of plain messages one at a
    time, with a pause between each. Uses a plain delay() rather than
    a persistent Script - unlike something like the Underworld's
    Charon timer, nothing gets permanently stuck if a reload
    interrupts this mid-sequence, worst case is just a player missing
    a line or two of tutorial text.

    Always delays even the very first line (a real bug found live):
    Evennia's own move_to() calls the destination room's
    at_object_receive (what triggers this) BEFORE it calls the
    mover's own at_post_move (what actually sends the room's
    description) - so a same-tick character.msg() here would always
    print above the room description the player hasn't even seen yet.
    Any delay, even a short one, defers to the next reactor tick,
    landing after that synchronous look instead.

    Every line - including the first - gets a leading blank line too
    (a separate, real complaint: several lines sent back to back with
    no visual gap read as one unbroken wall of text, no different from
    the room description itself, or from the tail end of whatever
    happened just before this sequence started).
    """
    if index >= len(messages):
        return

    def _send_this_line():
        if character.pk and character.location:
            character.msg("\n" + messages[index])
        delay(2, callback=lambda: _send_message_sequence(character, messages, index + 1))

    # Only the very first line needs the extra beat - every later line
    # already runs from inside a delay() callback (the one right
    # above), so it's already on a fresh reactor tick.
    delay(1 if index == 0 else 0, callback=_send_this_line)


def _send_cell_intro(character, index=0):
    _send_message_sequence(character, CELL_INTRO_MESSAGES, index)


class WelcomeCellRoom(ObjectParent, DefaultRoom):
    """
    Your Cell - the starting location. Fires the orientation sequence
    above exactly once per character (tracked via db.seen_cell_intro),
    so a veteran character passing back through later (after a death
    respawn, say) never sees it again.
    """

    def at_object_receive(self, obj, source_location, move_type="move", **kwargs):
        if not obj.has_account:
            return
        if obj.db.seen_cell_intro:
            return
        obj.db.seen_cell_intro = True
        _send_cell_intro(obj)


# Old Milo's guidance (see world/prototypes.py OLD_MILO) - the first
# room after the cells, room #226. Deliberately purely in-character,
# no command names or OOC language at all - that's what
# CELL_INTRO_MESSAGES above is for. This is just an old captive giving
# a new one some direction, same as his own description already
# promises he does for everyone who passes through.
MILO_GREETING_MESSAGES = [
    "|cOld Milo|n's sharp eyes find you as you pass. \"New, are you,\" he says - not really a question.",
    "|cOld Milo|n says, \"Don't much matter how you ended up in these chains. Never does. What matters is what you do next.\"",
    "|cOld Milo|n says, \"Go north if you want to fight your way out. There's a trainer waiting past the iron gate - beat him, and you've earned your freedom outright.\"",
    "|cOld Milo|n says, \"Or go west if you'd rather not risk it. There's a way to slip out quiet, through the old passages below - if you're clever enough to find it.\"",
    "|cOld Milo|n says, \"Either way...\" He looks back down at his chains. \"Good luck. You'll need it.\"",
]


def _send_milo_greeting(character, index=0):
    _send_message_sequence(character, MILO_GREETING_MESSAGES, index)


class MiloGreetingRoom(ObjectParent, DefaultRoom):
    """
    Room #226 - where Old Milo is stationed, the first room past the
    cells. Fires his greeting exactly once per character, same
    tracking pattern as WelcomeCellRoom.
    """

    def at_object_receive(self, obj, source_location, move_type="move", **kwargs):
        if not obj.has_account:
            return
        if obj.db.seen_milo_greeting:
            return
        obj.db.seen_milo_greeting = True
        _send_milo_greeting(obj)


# Fires the moment a character first reaches Atrium of the Games -
# which, since both escape routes (fighting the trainer, sneaking
# through the riddle door) lead here, means this fires right at the
# moment of actual escape, whichever path they took. Gives immediate,
# concrete direction rather than leaving a newly-free character
# standing in a big room with no idea what to do next.
ATRIUM_INTRO_MESSAGES = [
    "A weight lifts off your shoulders the moment you step past the gate - whatever's next, at least you're not in chains anymore.",
    "Go east to reach the Ludus, where you can train and level up safely before testing yourself further.",
    "The rest of the Colosseum - the stands above, the tunnels below - isn't going anywhere. It'll still be here once you've found your feet.",
]


def _send_atrium_intro(character, index=0):
    _send_message_sequence(character, ATRIUM_INTRO_MESSAGES, index)


class AtriumGreetingRoom(ObjectParent, DefaultRoom):
    """
    Atrium of the Games (#283) - where both escape routes lead. Fires
    the orientation sequence above exactly once per character, same
    tracking pattern as every other one-time greeting tonight.
    """

    def at_object_receive(self, obj, source_location, move_type="move", **kwargs):
        if not obj.has_account:
            return
        if obj.db.seen_atrium_intro:
            return
        obj.db.seen_atrium_intro = True
        _send_atrium_intro(obj)