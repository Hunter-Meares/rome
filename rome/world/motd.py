"""
Message of the day

One shared source for the MOTD, shown automatically at login
(typeclasses/accounts.py's at_post_login) and available any time via
the 'motd' command below - both read from the same get_motd(), so
there's only ever one place to update.

Keeping this current: RECENT_UPDATES_DATE/RECENT_UPDATES_TEXT below
are meant to be edited after any major player-facing change (a new
area, a new player-usable command, a significant bugfix players would
notice) - keep it to 2-3 lines, written for a player, not a changelog
entry. Update the date whenever the text changes. Admin-only changes
(new god-tier commands, internal fixes with no visible effect) don't
belong here - this is for players, not other developers.
"""

from evennia import CmdSet

from commands.command import Command

RECENT_UPDATES_DATE = "2026-08-23"

RECENT_UPDATES_TEXT = (
    "The Capitoline Hill is now open past the Forum - Jupiter's\n"
    "temple, the Arx, and more. City NPCs actually talk now, and\n"
    "'learnlanguage' lets you pick up tongues beyond the Latin\n"
    "everyone starts with."
)


def get_motd():
    return (
        "|Y==================================================|n\n"
        "Welcome to |wRome: The Eternal City|n\n"
        "|Y--------------------------------------------------|n\n"
        "Website: http://rome.vineyard.haus/\n"
        "Email:   zeus@rome.vineyard.haus (Admin)\n"
        "|Y--------------------------------------------------|n\n"
        "You are exploring a world still being built - the gods,\n"
        "the streets of Rome, and everyone in between are all a\n"
        "work in progress. Things will change, break, and grow.\n"
        "Your patience, curiosity, and feedback all help shape\n"
        "where this goes next.\n"
        "\n"
        "|wGetting started:|n\n"
        "  |whelp|n         - full command list and how things work\n"
        "  |wwho|n          - see who else is out there right now\n"
        "  |wtitle|n        - set a custom title shown next to your name\n"
        "  |wpublic <msg>|n - talk to everyone online, even if you can't see them\n"
        "  |wmotd|n         - see this message again any time\n"
        "\n"
        "|wRecent updates|n |x(%s)|n:\n"
        "%s\n"
        "\n"
        "Got a bug, an idea, or just want to talk shop? Reach out\n"
        "any time at |wzeus@rome.vineyard.haus|n - we read everything.\n"
        "|Y--------------------------------------------------|n\n"
        "May the gods watch over you as you ascend the Aventine.\n"
        "|Y==================================================|n"
    ) % (RECENT_UPDATES_DATE, RECENT_UPDATES_TEXT)


class CmdMOTD(Command):
    """
    Show the message of the day.

    Usage:
      motd

    The same welcome message shown when you first log in, including
    what's changed recently - handy if you missed it in the login
    scroll or just want to check back later.
    """

    key = "motd"
    aliases = ["news"]
    help_category = "general"

    def func(self):
        self.account.msg(get_motd())


class MOTDCmdSet(CmdSet):
    """The 'motd' command."""

    key = "MOTD CmdSet"

    def at_cmdset_creation(self):
        self.add(CmdMOTD())
