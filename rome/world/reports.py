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

from evennia.comms.models import Msg
from evennia.contrib.base_systems.ingame_reports import menu as _stock_menu
from evennia.contrib.base_systems.ingame_reports.reports import (
    CmdManageReports as _StockCmdManageReports,
    _get_report_hub,
    _REPORT_TYPES,
)
from evennia.utils import evmenu
from evennia.utils.utils import crop

# Real, direct player-facing (well, god-facing) request: a status is
# only ever visible by opening a report individually, making it slow
# to triage a long list. Colors give each status a real visual
# identity on the list itself, not just its own report page.
_STATUS_COLOR = {
    "in progress": "|y",
    "rejected": "|r",
    "closed": "|x",
}


def _status_badge(report):
    """A short, colored status prefix for one report's list row."""
    tags = [t for t in report.tags.all() if t in _STATUS_COLOR]
    if not tags:
        return ""
    parts = ["%s%s|n" % (_STATUS_COLOR[t], t.upper()) for t in tags]
    return "[%s] " % "/".join(parts)


def menunode_list_reports(caller, raw_string, **kwargs):
    # Real, confirmed live gap: the stock list only ever excludes the
    # "closed" tag from the default (unfiltered) view - a "rejected"
    # report is just as much a final disposition, but stayed in the
    # main list forever unless ALSO separately marked closed,
    # cluttering the default view with reports that already have a
    # real resolution. Pre-seeding the cached queryset the stock
    # function reads (and only ever builds once per menu session, via
    # its own `if not (report_list := getattr(...))` check) with
    # rejected reports already excluded means the stock function's own
    # downstream pagination math stays consistent, rather than
    # filtering the rendered page after the fact and getting the
    # "Next 10" boundary slightly wrong. Mirrors the stock function's
    # own queryset construction exactly, plus the one extra exclude -
    # not a reimplementation of the real listing/pagination logic,
    # which still happens entirely inside the real call below. Only
    # applies to the true default view - an explicit status filter
    # (including filtering by "rejected" itself) should still show
    # exactly what it says.
    if not kwargs.get("status") and not getattr(caller.ndb._evmenu, "report_list", None):
        hub = caller.ndb._evmenu.hub
        report_list = Msg.objects.search_message(receiver=hub).order_by("db_date_created")
        report_list = report_list.exclude(db_tags__db_key="rejected")
        caller.ndb._evmenu.report_list = report_list

    text, options = _stock_menu.menunode_list_reports(caller, raw_string, **kwargs)

    # Real, direct request: show each report's current status right on
    # the main list, instead of requiring a god to open every single
    # one just to see whether it's already been triaged. Only options
    # carrying a real "report" kwarg are actual report rows -
    # navigation options (Filter/Next/Previous) don't, and pass
    # through untouched.
    if isinstance(options, list):
        for option in options:
            goto = option.get("goto")
            if isinstance(goto, tuple) and isinstance(goto[1], dict):
                report = goto[1].get("report")
                if report is not None:
                    badge = _status_badge(report)
                    if badge:
                        option["desc"] = badge + option["desc"]

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


def _notify_reporter_of_status_change(caller, raw_string, report, tag, **kwargs):
    """
    Wraps the contrib's own _report_toggle_tag with a player-facing
    notification - a direct player-facing feature request: whoever
    filed a bug/idea/player report had no way to know it was ever
    actually looked at, short of a god separately telling them
    in-character. Reuses the exact tags this menu already tracks (no
    new state of its own) - only fires on the "marked" direction
    (tag being added), matching the request as asked ("gets a status
    update once its marked as...") rather than also announcing every
    unmark, which is a much less interesting event to be told about.

    report.senders is the reporting ACCOUNT (see ReportCmdBase.func in
    the contrib itself - create_message(self.account, ...), not the
    character) - .msg() works on it directly. Silently does nothing
    for a sender who's since deleted their account or isn't reachable
    for some other reason, same as any other .msg() call would.
    """
    was_active = tag in report.tags.all()
    result = _stock_menu._report_toggle_tag(caller, raw_string, report=report, tag=tag, **kwargs)
    now_active = tag in report.tags.all()

    if now_active and not was_active:
        summary = crop(report.message, 60)
        for sender in report.senders:
            if hasattr(sender, "msg"):
                sender.msg(
                    '|y[Report Update]|n Your report - "%s" - has been marked '
                    "|w%s|n." % (summary, tag)
                )

    return result


def menunode_manage_report(caller, raw_string, report, **kwargs):
    text, options = _stock_menu.menunode_manage_report(caller, raw_string, report, **kwargs)
    # Real gap this closes: the stock options point straight at the
    # contrib's own _report_toggle_tag with no notification hook at
    # all - swap in the wrapper above so every status change flowing
    # through THIS menu (the only one this project actually uses)
    # reaches the reporter, without touching the contrib's own toggle
    # logic or duplicating the tag list it's built from.
    for option in options:
        goto = option.get("goto")
        if isinstance(goto, tuple) and goto[0] is _stock_menu._report_toggle_tag:
            option["goto"] = (_notify_reporter_of_status_change, goto[1])
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

        # Real, confirmed live bug: running EvMenu on self.account (the
        # stock contrib's own choice) only ever replaces cmdsets on the
        # ACCOUNT's own stack - the puppeted Character's cmdset (which
        # is where a room's dynamically-added exit commands actually
        # live) is a completely separate stack Evennia merges in
        # afterward, so it stays fully active the whole time the menu
        # is open. A god typing 'n' or 'next' for this menu's own
        # "Next 10" option got matched against the room's "north" exit
        # alias instead and just walked north. Targeting the puppeted
        # Character here instead means EvMenu's default "Replace"
        # mergetype actually replaces the stack exits live on, closing
        # this off - falling back to the account itself only for the
        # rare case of managing reports while genuinely OOC (no
        # character currently puppeted). Also a better fit for this
        # game's own permission model than the stock behavior: this
        # project's god-tier system (CmdGodLevel) grants its Evennia
        # permission strings on the CHARACTER, not the account, so a
        # non-superuser god checked via the account alone could
        # actually have FAILED this menu's own read-lock checks -
        # true superuser status (Jupiter) was never affected either
        # way, since that bypass already checks the account directly.
        menu_caller = self.account
        if self.session and self.session.puppet:
            menu_caller = self.session.puppet

        evmenu.EvMenu(
            menu_caller,
            "world.reports",
            startnode="menunode_list_reports",
            hub=hub,
            persistent=True,
        )
