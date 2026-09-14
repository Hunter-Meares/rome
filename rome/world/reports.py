"""
Local override for evennia.contrib.base_systems.ingame_reports' report-
management menu ("manage bugs"/"manage ideas"/"manage players", and
bare "manage reports" - a hidden alias for "manage players", see
CmdManageReports' own docstring below).

The contrib is otherwise used completely unmodified (see CLAUDE.md's
Contribs table) - this is the one, deliberate exception. Real gap
found live: a god mid-menu typed 'help manage' (trying to see the
menu's own options again after they'd scrolled past), then bare
'help', and got nothing useful back from either. Both turned out to
be genuine, stock Evennia behavior, not something broken:

  - EvMenu only ever recognizes the exact bare word 'help' (or 'h') as
    a keyword - 'help <anything else>' always falls through to the
    generic "Choose an option or try 'help'." This is true of every
    EvMenu in this game (chargen, shops, this menu), not something
    specific to reports.
  - The contrib's own menu nodes (menu.py) never author any custom
    help text at all, so bare 'help' falls back to EvMenu's own
    generic "Commands: <menu option>, help, quit" - again the
    universal default for ANY node that doesn't provide its own,
    not a reports-specific gap.

('look'/'l' already redisplays the current node correctly, via
EvMenu's own auto_look - that's the actual fix for "I want to see the
list again." But reaching for 'help' first is exactly what happened
live, so it's worth actually answering instead of leaving the generic
fallback in place.)

Each node function below is a thin wrapper, not a reimplementation:
call the real, unmodified contrib function to get its genuine
(text, options), then attach a node-appropriate helptext by returning
(text, helptext), options - EvMenu's own documented mechanism for a
node to opt into custom help (see its module docstring: nodetext may
be a (nodetext, helptext) tuple). None of the actual report-browsing
or status-toggling logic is duplicated here.
"""

from evennia.contrib.base_systems.ingame_reports import menu as _stock_menu
from evennia.contrib.base_systems.ingame_reports.reports import (
    CmdManageReports as _StockCmdManageReports,
    _get_report_hub,
    _REPORT_TYPES,
)
from evennia.utils import evmenu


def menunode_list_reports(caller, raw_string, **kwargs):
    text, options = _stock_menu.menunode_list_reports(caller, raw_string, **kwargs)
    helptext = (
        "Type the number next to a report to open it. 'f' filters the "
        "list by status. 'look' shows this list again if it's scrolled "
        "past. 'quit' leaves the menu entirely."
    )
    return (text, helptext), options


def menunode_choose_filter(caller, raw_string, **kwargs):
    text, options = _stock_menu.menunode_choose_filter(caller, raw_string, **kwargs)
    helptext = (
        "Pick a status to filter the list down to just those reports, "
        "or 'All open reports' to clear any filter currently applied."
    )
    return (text, helptext), options


def menunode_manage_report(caller, raw_string, report, **kwargs):
    text, options = _stock_menu.menunode_manage_report(caller, raw_string, report, **kwargs)
    helptext = (
        "Pick a status to toggle it on this report, 'Manage another "
        "report' to go back to the full list, or 'quit' to leave."
    )
    return (text, helptext), options


class CmdManageReports(_StockCmdManageReports):
    """
    Same as the contrib's own manage-reports command in every way,
    except:

    1. It opens the help-text-augmented menu above instead of the
       stock one (see this module's own docstring for why).
    2. The bare "manage reports" form no longer silently defaults to
       managing Player reports specifically. That default was a real,
       confirmed source of live confusion - a god filed a bug report,
       then typed "manage reports" expecting to see it, and got "No
       open Player Reports at the moment." instead, with no
       indication anything had been silently redirected to a
       different category. The stock contrib has no documented reason
       for that particular default (see this project's own commit
       message/conversation for the full trace) - it's an undocumented
       upstream implementation quirk, not a deliberate design a player
       could reasonably guess. Now it just asks for a specific
       category instead of guessing one, mirroring how bare "manage"
       (no category at all) already correctly rejects with a
       suggestion rather than silently picking one.

    func() is a full reimplementation rather than a super() call with
    a wrapper - the stock command hardcodes which menu module it opens
    inline, with no separate overridable hook for that, so pointing it
    at a different module (and changing the bare-"reports" handling)
    means duplicating the rest of the method. Kept byte-for-byte
    identical to the original otherwise, key/aliases/locks/get_help
    included (all inherited, untouched).
    """

    def func(self):
        report_type = self.cmdstring.split()[-1]
        if report_type == "reports":
            self.msg(
                "Which reports? Use |wmanage bugs|n, |wmanage ideas|n, "
                "or |wmanage players|n."
            )
            return
        if report_type not in _REPORT_TYPES:
            self.msg(f"'{report_type}' is not a valid report category.")
            return
        # remove the trailing s, just so everything reads nicer
        report_type = report_type[:-1]
        hub = _get_report_hub(report_type)
        if not hub:
            self.msg("You cannot manage that.")

        evmenu.EvMenu(
            self.account,
            "world.reports",
            startnode="menunode_list_reports",
            hub=hub,
            persistent=True,
        )
