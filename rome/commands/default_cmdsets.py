"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.
"""
from evennia import default_cmds
from evennia.contrib.grid import simpledoor
from world import combat
from world import analytics
from evennia.contrib.rpg.rpsystem import RPSystemCmdSet
from world import colosseum
from world import party
from world import underworld
from world import factions
from world import leveling
from world import doors
from world import economy
from world import languages
from world import building_menu
from world import motd
from world import worldcheck
from world import bounties
from world import quests
from world import religion
from evennia.contrib.utils.debugpy import CmdDebugPy
from evennia.contrib.grid.ingame_map_display import MapDisplayCmdSet
from evennia.contrib.grid.ingame_map_display.ingame_map_display import CmdMap
from evennia.contrib.game_systems import barter
from evennia.contrib.game_systems.achievements.achievements import CmdAchieve
from evennia.contrib.game_systems.mail import CmdMailCharacter
from evennia.contrib.base_systems.ingame_reports import ReportsCmdSet
from commands import social


class LockedCmdDebugPy(CmdDebugPy):
    """
    Same as the contrib's own CmdDebugPy, just explicitly locked to
    Developer permission - starting a debugger listening on an open
    port is a genuine developer-only tool, and this makes sure of
    that regardless of whatever the contrib's own default lock
    happens to be, rather than assuming it's already safe.
    """

    locks = "cmd:perm(Developer)"


class FriendlyCmdMap(CmdMap):
    """
    Shows a simple map of the area around you.

    Usage:
      map
      map <size>

    Draws an ASCII map centered on your current room, built from the
    real exits connecting nearby rooms - not a hand-drawn image, so
    it's always accurate to what's actually there. The number after
    'map' controls how far out it looks in each direction (try 'map
    4' for a wider view); leave it off for the default size.
    """

    # No func() override - this only replaces the help text above.
    # The actual map-drawing logic is entirely inherited, unchanged,
    # from the real CmdMap this subclasses.


class FriendlyCmdMailCharacter(CmdMailCharacter):
    """
    Send and receive in-character letters with other characters.

    Usage:
      mail                                 - see everything in your mailbox
      mail <#>                             - read a specific message
      mail <name>=<subject>/<message>      - send a letter (comma-separate
                                              names to reach more than one
                                              character at once)
      mail/reply <#>=<message>             - reply, with the original
                                              message attached beneath
      mail/forward <name>=<#>[/<message>]  - forward a message on, with
                                              an optional note of your own
      mail/delete <#>                      - delete a message

    This is the in-character half of the mail system only - letters go
    between characters, not out-of-character accounts, and only work
    while you're actually logged in and playing. See 'help mailsystem'
    for the bigger picture.
    """

    # No func() override - this only replaces the help text above (the
    # contrib's own docstring is written for @mail's Account-level
    # sibling, which isn't installed here). The actual send/read/
    # reply/forward/delete logic is entirely inherited, unchanged.


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(combat.BattleCmdSet())
        self.add(analytics.CmdSessionLogs())
        self.add(economy.CmdShop())
        self.add(LockedCmdDebugPy())
        self.add(MapDisplayCmdSet)
        self.add(FriendlyCmdMap())
        self.add(barter.CmdsetTrade)
        self.add(CmdAchieve)
        self.add(RPSystemCmdSet())
        self.add(combat.CmdGreet())
        self.add(combat.CmdSlay())
        self.add(combat.CmdCleanupNPCs())
        self.add(combat.CmdCleanupItems())
        self.add(combat.CmdGodLevel())
        self.add(combat.CmdWizInvis())
        self.add(combat.CmdRestore())
        self.add(combat.CmdSnoop())
        self.add(combat.FriendlyCmdMask())
        self.add(colosseum.ColosseumCmdSet())
        self.add(social.CmdTitle())
        self.add(party.CmdParty())
        self.add(underworld.UnderworldCmdSet())
        self.add(simpledoor.SimpleDoorCmdSet)
        self.add(doors.DescriptiveOpenCloseDoor())
        self.add(languages.LanguageCmdSet())
        self.add(building_menu.RomeBuildingCmdSet())
        self.add(worldcheck.CmdWorldCheck())
        self.add(FriendlyCmdMailCharacter())
        self.add(factions.CmdFaction())
        self.add(factions.CmdFactionLeader())
        self.add(factions.CmdChannelKick())
        self.add(factions.CmdMarch())
        self.add(factions.CmdInterrogate())
        self.add(factions.CmdCommune())
        self.add(factions.CmdOath())
        self.add(factions.CmdScry())
        self.add(factions.CmdRequisition())
        self.add(factions.CmdSafehouse())
        self.add(leveling.CmdStatUp())
        self.add(bounties.CmdBounty())
        self.add(quests.CmdQuest())
        self.add(religion.CmdPray())
        self.add(religion.CmdPontifex())
        self.add(religion.CmdBlemish())
        self.add(religion.CmdExpel())
        self.add(religion.CmdReligion())


from world.character_creator import ContribChargenCmdSet


class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        # Combat-aware quit override - refuses to work while the
        # character this session is puppeting is mid-combat. See
        # world/combat.py's CmdQuit for the full reasoning.
        self.add(combat.CmdQuit())
        self.add(ContribChargenCmdSet)
        self.add(social.CmdWho())
        self.add(social.FriendlyCmdPage())
        self.add(motd.MOTDCmdSet())
        self.add(ReportsCmdSet)


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.
        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #