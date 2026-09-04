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
from evennia.utils.ansi import ANSIString
from evennia.utils.utils import wrap as evennia_wrap

from commands.command import Command

RECENT_UPDATES_DATE = "2026-09-04"

RECENT_UPDATES_TEXT = (
    "Beyond the Walls: Rome has a real northern gate now, the Porta Flaminia, "
    "opening onto real wilderness and a long road all the way to a Germanic "
    "stronghold - a full new leveling zone for levels 25-45. Also new: "
    "'recall' teleports you home from anywhere, and 'titles' shows off what "
    "you've earned. See 'help beyond the walls', 'help recall', and "
    "'help titles'."
)

# The box's own interior width, between its left/right borders and
# their one space of padding - comfortably under 80 columns once the
# borders/padding are added back (WIDTH + 4), and wide enough for the
# longest fixed line already in use here without wrapping it oddly.
MOTD_WIDTH = 70


def _box_border(char="="):
    return "|Y+%s+|n" % (char * (MOTD_WIDTH + 2))


def _box_line(text="", align="l"):
    """
    One bordered, padded line. Uses ANSIString for both wrapping-
    safety and padding, since a line can freely contain color codes
    (|w, |Y, etc.) - a plain str.ljust() or textwrap call would count
    those as real characters and under-pad the line, letting the
    right-hand border drift instead of lining up.
    """
    ansi_text = ANSIString(text)
    if len(ansi_text) > MOTD_WIDTH:
        # Safety net, not the normal path - _box_paragraph already
        # wraps real paragraphs before this is called. A single fixed
        # line (e.g. a command list entry) that's simply too long to
        # fit is cropped rather than allowed to overflow the border.
        ansi_text = ansi_text[:MOTD_WIDTH]
    padded = ansi_text.center(MOTD_WIDTH) if align == "c" else ansi_text.ljust(MOTD_WIDTH)
    return "|Y|||n %s |Y|||n" % padded


def _box_paragraph(text, align="l"):
    """Wraps a plain-text paragraph to the box's own width and
    returns one bordered, padded line per wrapped line."""
    wrapped = evennia_wrap(text, width=MOTD_WIDTH)
    return [_box_line(line, align=align) for line in wrapped.split("\n")]


def _box_blank():
    return _box_line("")


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
