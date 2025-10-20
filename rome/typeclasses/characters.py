"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

from evennia.objects.objects import DefaultCharacter

from .objects import ObjectParent

from world.tb_basic import TBBasicCharacter
from world.tb_equip import TBEquipCharacter
from world.tb_items import TBItemsCharacter
from world.tb_magic import TBMagicCharacter



class Character(TBEquipCharacter, TBItemsCharacter, TBMagicCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

    """
    def at_object_creation(self):
        TBBasicCharacter.at_object_creation(self)
        TBMagicCharacter.at_object_creation(self)
        TBItemsCharacter.at_object_creation(self)
        TBEquipCharacter.at_object_creation(self)
        self.db.hp = 100
        self.db.mp = 100
        self.db.sp = 100



