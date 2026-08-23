"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.
"""
from evennia.objects.objects import DefaultCharacter
from .objects import ObjectParent
from world.combat import CombatCharacter

"""
----------------------------------------------------------------------------
DIVINE PRESENCE - per-god teleport arrival/departure flavor
----------------------------------------------------------------------------
Set db.divine_presence on a character to one of the keys below (a plain
string, lowercase) to give them a signature entrance/exit whenever they
@tel somewhere - matched to their domain from the lore on gods.html. Any
value not found here still gets a dramatic generic message, so a future
god-player doesn't need a lore entry written before they can use this.

Only fires on actual teleports (move_type == "teleport"), never on
regular walking through exits.
"""

DIVINE_ANNOUNCE_MESSAGES = {
    "jupiter": {
        "arrive": (
            "|c*** The air splits with a deafening crack of thunder as {name} "
            "descends in a blinding flash of lightning - all who witness it feel "
            "a shiver of awe and dread. ***|n"
        ),
        "leave": (
            "|c*** A deep rumble of thunder rolls through the air as {name} "
            "vanishes in a blinding flash of lightning! ***|n"
        ),
    },
    "juno": {
        "arrive": (
            "|m*** A regal golden light fills the room, and somewhere unseen a "
            "peacock's cry rings out, as {name} arrives. ***|n"
        ),
        "leave": (
            "|m*** The golden light withdraws like a queen's favor quietly "
            "revoked, and {name} is gone. ***|n"
        ),
    },
    "neptune": {
        "arrive": (
            "|C*** The ground trembles and the sharp scent of brine fills the "
            "air as {name} rises, as though from some unseen tide. ***|n"
        ),
        "leave": (
            "|C*** An unseen wave recedes, leaving only damp, salt-heavy air "
            "behind as {name} departs. ***|n"
        ),
    },
    "ceres": {
        "arrive": (
            "|g*** The air turns warm and sweet with the scent of ripening "
            "wheat as {name} arrives, and for a moment the room feels like "
            "harvest season. ***|n"
        ),
        "leave": (
            "|g*** Nearby flowers wilt and still as {name} departs, the "
            "borrowed warmth of the season fading with them. ***|n"
        ),
    },
    "minerva": {
        "arrive": (
            "|W*** A silver owl's cry pierces the air as {name} descends in a "
            "shimmer of cool, grey light. ***|n"
        ),
        "leave": (
            "|W*** The owl's cry fades into silence as {name} withdraws, their "
            "presence lingering like an unfinished thought. ***|n"
        ),
    },
    "apollo": {
        "arrive": (
            "|Y*** Golden light floods the room, and for a moment the faint hum "
            "of an unseen lyre seems to hang in the air, as {name} arrives. ***|n"
        ),
        "leave": (
            "|Y*** The golden light dims slowly, like a sunset, as {name} "
            "departs. ***|n"
        ),
    },
    "diana": {
        "arrive": (
            "|C*** The shadows sharpen and a sliver of moonlight cuts through "
            "as {name} arrives, silent as a hunting cat. ***|n"
        ),
        "leave": (
            "|C*** The moonlight withdraws as swiftly as a loosed arrow, and "
            "{name} is already gone. ***|n"
        ),
    },
    "mars": {
        "arrive": (
            "|r*** The air turns thick with the scent of iron and smoke as a "
            "blood-red light heralds {name}'s arrival, distant war-drums "
            "pounding somewhere unseen. ***|n"
        ),
        "leave": (
            "|r*** The war-drums fall silent as {name} departs, leaving only "
            "the lingering scent of ash behind. ***|n"
        ),
    },
    "venus": {
        "arrive": (
            "|M*** A wave of intoxicating perfume rolls through the room as "
            "rose petals drift down from nowhere - {name} has arrived. ***|n"
        ),
        "leave": (
            "|M*** The rose petals wilt and vanish as {name}'s perfume fades "
            "from the air. ***|n"
        ),
    },
    "vulcan": {
        "arrive": (
            "|y*** The ring of hammer on anvil echoes for just a moment, "
            "sparks scattering through the air, as {name} arrives, trailing "
            "the smell of hot iron. ***|n"
        ),
        "leave": (
            "|y*** The sparks fade and the smell of the forge dissipates as "
            "{name} withdraws. ***|n"
        ),
    },
    "mercury": {
        "arrive": (
            "|c*** A sudden gust of wind swirls through the room, gone as "
            "quickly as it came - and {name} is simply standing there, where "
            "nothing was a moment ago. ***|n"
        ),
        "leave": (
            "|c*** A rush of wind is the only sign that {name} has already "
            "gone. ***|n"
        ),
    },
    "bacchus": {
        "arrive": (
            "|M*** The sweet smell of wine and ripe grapes fills the air as "
            "unseen vines curl briefly along the walls - {name} has "
            "arrived. ***|n"
        ),
        "leave": (
            "|M*** The scent of wine fades like the last note of a song as "
            "{name} departs. ***|n"
        ),
    },
    "pluto": {
        "arrive": (
            "|K*** The light dims and a bone-deep cold settles over the room "
            "as shadows pool in the corners, and {name} steps forth from "
            "between them. ***|n"
        ),
        "leave": (
            "|K*** The shadows lengthen and swallow {name} whole, leaving only "
            "the cold behind. ***|n"
        ),
    },
    "trivia": {
        "arrive": (
            "|m*** Twin torch-flames flare to life at the room's edges as "
            "{name} steps from the space between one heartbeat and the "
            "next. ***|n"
        ),
        "leave": (
            "|m*** The torch-flames gutter out as {name} withdraws into the "
            "crossroads between worlds. ***|n"
        ),
    },
}

# Fallback for any divine_presence value not found above - so a new
# god-player still gets something dramatic before you've written their
# lore-specific flavor.
_DEFAULT_DIVINE_ARRIVE = (
    "|y*** A radiant light fills the room as {name} steps forth from beyond "
    "mortal sight. ***|n"
)
_DEFAULT_DIVINE_LEAVE = (
    "|y*** The light fades, and {name} is gone as suddenly as they came. ***|n"
)


class Character(ObjectParent, CombatCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.
    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.
    """

    def at_object_creation(self):
        """
        Called once, when this character is first created.
        """
        super().at_object_creation()

    def announce_move_from(self, destination, msg=None, mapping=None, move_type="move", **kwargs):
        """
        Called in the OLD room, just before a move happens. Characters
        with db.divine_presence set to a god's name get that god's
        signature departure message instead of the plain default, but
        only when actually teleporting - regular walking is untouched.

        Wizinvis (see CmdWizInvis in world/combat.py) overrides all of
        this: while active, no plain-movement departure message is
        sent to anyone at all, and even the divine-teleport flavor
        only reaches whoever can already see through the wizinvis
        (CombatCharacter.access's 'view' check - anyone at or above
        this character's own level, or a true superuser). Anyone who
        can see through it still sees the character directly via
        look/room contents regardless of this message.
        """
        if self.db.wizinvis and self.location:
            god_key = self.db.divine_presence
            if god_key and move_type == "teleport":
                flavor = DIVINE_ANNOUNCE_MESSAGES.get(str(god_key).lower())
                text = (flavor["leave"] if flavor else _DEFAULT_DIVINE_LEAVE).format(name=self.key)
                for observer in self.location.contents:
                    if observer != self and self.access(observer, "view"):
                        observer.msg(text)
            return

        god_key = self.db.divine_presence
        if god_key and move_type == "teleport" and self.location:
            flavor = DIVINE_ANNOUNCE_MESSAGES.get(str(god_key).lower())
            text = (flavor["leave"] if flavor else _DEFAULT_DIVINE_LEAVE).format(name=self.key)
            self.location.msg_contents(text, exclude=self)
            return
        super().announce_move_from(
            destination, msg=msg, mapping=mapping, move_type=move_type, **kwargs
        )

    def announce_move_to(self, source_location, msg=None, mapping=None, move_type="move", **kwargs):
        """
        Called in the NEW room, just after a move happens. Same
        divine_presence + teleport check as announce_move_from above,
        for that god's signature arrival instead - and the same
        wizinvis override.
        """
        if self.db.wizinvis and self.location:
            god_key = self.db.divine_presence
            if god_key and move_type == "teleport":
                flavor = DIVINE_ANNOUNCE_MESSAGES.get(str(god_key).lower())
                text = (flavor["arrive"] if flavor else _DEFAULT_DIVINE_ARRIVE).format(name=self.key)
                for observer in self.location.contents:
                    if observer != self and self.access(observer, "view"):
                        observer.msg(text)
            return

        god_key = self.db.divine_presence
        if god_key and move_type == "teleport" and self.location:
            flavor = DIVINE_ANNOUNCE_MESSAGES.get(str(god_key).lower())
            text = (flavor["arrive"] if flavor else _DEFAULT_DIVINE_ARRIVE).format(name=self.key)
            self.location.msg_contents(text, exclude=self)
            return
        super().announce_move_to(
            source_location, msg=msg, mapping=mapping, move_type=move_type, **kwargs
        )