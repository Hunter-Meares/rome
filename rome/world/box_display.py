"""
Shared bordered-box text rendering.

Originally built as private helpers inside world/motd.py to fix a real
bug there (manually-inserted line breaks in a plain-text MOTD kept
overflowing the box with no actual width discipline behind them -
ANSIString handles wrapping/padding correctly where a plain
str.ljust()/textwrap call would miscount color codes like |Y as real
characters). Pulled out here, parameterized by width instead of
hardcoded to MOTD_WIDTH, once a second feature (world/combat.py's
'stats' command) wanted the exact same vivid, bordered look rather
than a second, independently-written copy of the same logic at a
different width - one shared implementation, one place to fix a bug
in it.

world/motd.py's own `_box_border`/`_box_line`/`_box_paragraph`/
`_box_blank` are now thin wrappers around these, fixed to MOTD_WIDTH,
kept for that module's own readability and so nothing calling them
needed to change.
"""

from evennia.utils.ansi import ANSIString
from evennia.utils.utils import wrap as evennia_wrap


def box_border(width, char="="):
    return "|Y+%s+|n" % (char * (width + 2))


def box_line(text, width, align="l"):
    """
    One bordered, padded line at the given width. Uses ANSIString for
    both wrapping-safety and padding, since a line can freely contain
    color codes (|w, |Y, etc.) - a plain str.ljust()/textwrap call
    would count those as real characters and under-pad the line,
    letting the right-hand border drift instead of lining up.
    """
    ansi_text = ANSIString(text)
    if len(ansi_text) > width:
        # Safety net, not the normal path - box_paragraph already
        # wraps real paragraphs before this is called. A single fixed
        # line that's simply too long to fit is cropped rather than
        # allowed to overflow the border.
        ansi_text = ansi_text[:width]
    padded = ansi_text.center(width) if align == "c" else ansi_text.ljust(width)
    return "|Y|||n %s |Y|||n" % padded


def box_paragraph(text, width, align="l"):
    """Wraps a plain-text paragraph to the given width and returns one
    bordered, padded line per wrapped line."""
    wrapped = evennia_wrap(text, width=width)
    return [box_line(line, width, align=align) for line in wrapped.split("\n")]


def box_blank(width):
    return box_line("", width)
