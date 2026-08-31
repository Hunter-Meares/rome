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

RECENT_UPDATES_DATE = "2026-08-31"

RECENT_UPDATES_TEXT = (
    "The Cloaca Maxima is open - a real leveling zone beneath the city,\n"
    "reached through sewer grates near the Ludus, the Subura, and the Forum.\n"
    "Stats now grow past chargen too: every 3rd level, use 'statup' to spend\n"
    "a point. Try 'help statup' and 'help factions' if you missed either."
)


def get_motd():
    return (
        "|Y==================================================|n\n"
        "         Welcome to |wRome: The Eternal City|n\n"
        "|Y--------------------------------------------------|n\n"
        "Website: |whttp://rome.vineyard.haus/|n\n"
        "Email:   |wzeus@rome.vineyard.haus|n |x(Admin - bugs, ideas, feedback)|n\n"
        "|Y--------------------------------------------------|n\n"
        "You're exploring a world still being built - the gods,\n"
        "the streets of Rome, and everyone in between are all a\n"
        "work in progress. Things will change, break, and grow.\n"
        "Your patience, curiosity, and feedback shape where this\n"
        "goes next.\n"
        "\n"
        "|r>> Getting Started|n\n"
        "  |whelp|n         - full command list and how things work\n"
        "  |wwho|n          - see who else is out there right now\n"
        "  |wtitle|n        - set a custom title shown next to your name\n"
        "  |wpublic <msg>|n - talk to everyone online, even if you can't see them\n"
        "  |wmotd|n         - see this message again any time\n"
        "\n"
        "|r>> Recent Updates|n |x(%s)|n\n"
        "%s\n"
        "\n"
        "Got a bug, an idea, or a player to report? Use 'bug', 'idea', or\n"
        "'report' in-character, or just email us - either way, we read it.\n"
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
