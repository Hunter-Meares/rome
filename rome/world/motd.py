"""
Message of the day

One shared source for the MOTD, shown automatically at login
(typeclasses/accounts.py's at_post_login) and available any time via
the 'motd' command below - both read from the same get_motd(), so
there's only ever one place to update.

Rendered as a real, fully enclosed box (top/bottom/side borders, every
line padded to the same interior width) rather than hand-typed lines
with a border only on top/bottom/divider - a real bug found live:
RECENT_UPDATES_TEXT had manually-inserted line breaks with no actual
width discipline behind them, so longer updates overflowed straight
through the box's own side borders. _box_lines() below wraps and pads
every paragraph itself now, using ANSIString (not a plain .ljust()/
textwrap, both of which count color codes like |Y as real characters
and would under-pad any colored line) so this can't silently recur.

Keeping this current: RECENT_UPDATES_DATE/RECENT_UPDATES_TEXT below
are meant to be edited after any major player-facing change (a new
area, a new player-usable command, a significant bugfix players would
notice) - keep it to 2-3 sentences, written for a player, not a
changelog entry (it gets wrapped and boxed automatically - no need to
hand-insert line breaks). Update the date whenever the text changes.
Admin-only changes (new god-tier commands, internal fixes with no
visible effect) don't belong here - this is for players, not other
developers.
"""

from evennia import CmdSet

from commands.command import Command
from world.box_display import box_border, box_line, box_paragraph, box_blank

RECENT_UPDATES_DATE = "2026-09-05"

RECENT_UPDATES_TEXT = (
    "Several buildings across the city now have real doors to open and "
    "close, and every temple dedicated to a specific god has an actual "
    "statue you can examine. 'stats' is now a proper bordered sheet, "
    "combat text has real color and breathing room between turns, and "
    "auto-attack waits a bit longer before taking over your turn."
)

# The box's own interior width, between its left/right borders and
# their one space of padding - comfortably under 80 columns once the
# borders/padding are added back (WIDTH + 4), and wide enough for the
# longest fixed line already in use here without wrapping it oddly.
MOTD_WIDTH = 70


def _box_border(char="="):
    return box_border(MOTD_WIDTH, char)


def _box_line(text="", align="l"):
    return box_line(text, MOTD_WIDTH, align=align)


def _box_paragraph(text, align="l"):
    return box_paragraph(text, MOTD_WIDTH, align=align)


def _box_blank():
    return box_blank(MOTD_WIDTH)


def get_motd():
    lines = [
        _box_border("="),
        _box_line("|wWelcome to Rome: The Eternal City|n", align="c"),
        _box_border("-"),
        _box_line("Website: |whttp://rome.vineyard.haus/|n"),
        _box_line("Email:   |wzeus@rome.vineyard.haus|n |x(Admin - bugs, ideas, feedback)|n"),
        _box_border("-"),
    ]
    lines += _box_paragraph(
        "You're exploring a world still being built - the gods, the streets "
        "of Rome, and everyone in between are all a work in progress. Things "
        "will change, break, and grow. Your patience, curiosity, and "
        "feedback shape where this goes next."
    )
    lines += [
        _box_blank(),
        _box_line("|r>> Getting Started|n"),
        _box_line("  |whelp|n         - full command list and how things work"),
        _box_line("  |wwho|n          - see who else is out there right now"),
        _box_line("  |wtitle|n        - set a custom title shown next to your name"),
        _box_line("  |wpublic <msg>|n - talk to everyone online, even if you can't see them"),
        _box_line("  |wmotd|n         - see this message again any time"),
        _box_blank(),
        _box_line("|r>> Recent Updates|n |x(%s)|n" % RECENT_UPDATES_DATE),
    ]
    lines += _box_paragraph(RECENT_UPDATES_TEXT)
    lines += [_box_blank()]
    lines += _box_paragraph(
        "Got a bug, an idea, or a player to report? Use 'bug', 'idea', or "
        "'report' in-character, or just email us - either way, we read it."
    )
    lines += [
        _box_border("-"),
        _box_line("May the gods watch over you as you ascend the Aventine.", align="c"),
        _box_border("="),
    ]
    return "\n".join(lines)


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
