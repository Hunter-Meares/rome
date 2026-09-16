"""
Tests for world/reports.py - the local override of ingame_reports'
report-management menu/command. Two real gaps found live, both fixed
there: 'help' inside the menu gave nothing useful (a genuine stock
EvMenu limitation, not something broken, but worth actually answering
- see world/reports.py's own docstring), and bare "manage reports"
used to silently default to managing Player reports specifically, an
undocumented upstream quirk that looked like a bug to a live user.

Exercises the EvMenu node functions directly (plain functions of
(caller, raw_string, **kwargs) -> (text, options), callable without a
real EvMenu session - same established pattern as tests_economy.py),
plus CmdManageReports' own pre-menu gating logic. Doesn't test the
actual "opens a real menu" success path, matching the same scope
boundary tests_economy.py's own CmdShop tests already draw.
"""

from types import SimpleNamespace
from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create

from world import reports


class ReportsMenuTestBase(EvenniaTest):
    def _make_hub(self, key="bugs_reports"):
        return create.create_script(key=key)

    def _attach_fake_evmenu(self, caller, hub):
        # The stock node functions read caller.ndb._evmenu.hub/
        # .report_list directly - only ever set for real once a live
        # EvMenu session exists. A plain stand-in with the same
        # attributes is all either function actually touches.
        caller.ndb._evmenu = SimpleNamespace(hub=hub, report_list=None)


class TestMenuNodesAttachRealHelpText(ReportsMenuTestBase):
    def test_list_reports_node_returns_nodetext_helptext_tuple(self):
        hub = self._make_hub()
        self._attach_fake_evmenu(self.char1, hub)

        node_return, options = reports.menunode_list_reports(self.char1, "")

        self.assertIsInstance(node_return, tuple)
        text, helptext = node_return
        self.assertTrue(helptext)
        self.assertIn("quit", helptext.lower())
        # the real report-listing content still comes through unchanged
        self.assertIn("Reports", text)

    def test_choose_filter_node_returns_nodetext_helptext_tuple(self):
        hub = self._make_hub()
        self._attach_fake_evmenu(self.char1, hub)

        node_return, options = reports.menunode_choose_filter(self.char1, "")

        text, helptext = node_return
        self.assertTrue(helptext)
        self.assertIn("filter", helptext.lower())

    def test_manage_report_node_returns_nodetext_helptext_tuple(self):
        hub = self._make_hub()
        self._attach_fake_evmenu(self.char1, hub)
        msg = create.create_message(self.char1, "Something's broken.", receivers=hub)

        node_return, options = reports.menunode_manage_report(self.char1, "", report=msg)

        text, helptext = node_return
        self.assertTrue(helptext)
        self.assertIn("quit", helptext.lower())
        self.assertIn("Something's broken.", text)


class TestReportStatusChangeNotifiesTheReporter(ReportsMenuTestBase):
    """
    Direct player-facing feature request: whoever filed a bug/idea/
    player report had no way to know it was ever looked at, short of
    a god separately telling them in-character. Every status tag
    being MARKED (not unmarked - a much less interesting event) now
    messages report.senders directly - the reporting ACCOUNT, per how
    the contrib's own ReportCmdBase.func creates the report
    (create_message(self.account, ...), not the character).
    """

    def _get_toggle_option(self, options, tag):
        for option in options:
            if option["desc"].lower() in ("mark as %s" % tag, "unmark as %s" % tag):
                return option
        raise AssertionError("no option for tag %r in %r" % (tag, options))

    def test_marking_in_progress_notifies_the_reporting_account(self):
        hub = self._make_hub()
        self._attach_fake_evmenu(self.char1, hub)
        msg = create.create_message(self.account, "Wield is broken.", receivers=hub)

        (text, helptext), options = reports.menunode_manage_report(self.char1, "", report=msg)
        option = self._get_toggle_option(options, "in progress")
        goto, goto_kwargs = option["goto"]

        with patch.object(self.account, "msg") as mock_msg:
            goto(self.char1, "", **goto_kwargs)

        mock_msg.assert_called_once()
        sent_text = mock_msg.call_args[0][0]
        self.assertIn("Wield is broken.", sent_text)
        self.assertIn("in progress", sent_text)

    def test_the_underlying_tag_is_still_actually_toggled(self):
        """The notification wrapper must not skip the real effect -
        this isn't just decoration on top of a no-op."""
        hub = self._make_hub()
        self._attach_fake_evmenu(self.char1, hub)
        msg = create.create_message(self.account, "Wield is broken.", receivers=hub)

        (text, helptext), options = reports.menunode_manage_report(self.char1, "", report=msg)
        option = self._get_toggle_option(options, "in progress")
        goto, goto_kwargs = option["goto"]

        with patch.object(self.account, "msg"):
            goto(self.char1, "", **goto_kwargs)

        self.assertIn("in progress", [str(t) for t in msg.tags.all()])

    def test_unmarking_does_not_notify(self):
        """Only the 'marked' direction is interesting enough to
        announce - toggling a status back off stays silent."""
        hub = self._make_hub()
        self._attach_fake_evmenu(self.char1, hub)
        msg = create.create_message(self.account, "Wield is broken.", receivers=hub)
        msg.tags.add("in progress")

        (text, helptext), options = reports.menunode_manage_report(self.char1, "", report=msg)
        option = self._get_toggle_option(options, "in progress")
        goto, goto_kwargs = option["goto"]

        with patch.object(self.account, "msg") as mock_msg:
            goto(self.char1, "", **goto_kwargs)

        mock_msg.assert_not_called()
        self.assertNotIn("in progress", [str(t) for t in msg.tags.all()])

    def test_marking_closed_notifies_too(self):
        hub = self._make_hub()
        self._attach_fake_evmenu(self.char1, hub)
        msg = create.create_message(self.account, "Wield is broken.", receivers=hub)

        (text, helptext), options = reports.menunode_manage_report(self.char1, "", report=msg)
        option = self._get_toggle_option(options, "closed")
        goto, goto_kwargs = option["goto"]

        with patch.object(self.account, "msg") as mock_msg:
            goto(self.char1, "", **goto_kwargs)

        mock_msg.assert_called_once()
        self.assertIn("closed", mock_msg.call_args[0][0])


class TestCmdManageReportsBareFormNoLongerGuesses(EvenniaCommandTest):
    """
    Regression coverage for the real, confirmed live gap: bare
    "manage reports" used to silently open the Player-reports menu
    with no indication anything had been redirected. It should now
    ask for a specific category instead of guessing one.
    """

    def test_bare_manage_reports_asks_for_a_category(self):
        result = self.call(
            reports.CmdManageReports(), "", cmdstring="manage reports", caller=self.account
        )
        self.assertIn("Which reports", result)
        self.assertIn("manage bugs", result)
        self.assertIn("manage ideas", result)
        self.assertIn("manage players", result)

    def test_bare_manage_reports_does_not_mention_player_reports_at_all(self):
        """
        The old, confusing behavior specifically surfaced "No open
        Player Reports at the moment." with zero explanation - that
        exact phrase must not appear on this path anymore.
        """
        result = self.call(
            reports.CmdManageReports(), "", cmdstring="manage reports", caller=self.account
        )
        self.assertNotIn("Player Reports", result)

    def test_invalid_category_still_rejected_like_the_original(self):
        """
        Regression guard: only the ambiguous bare "reports" form
        changed - a genuinely invalid category (not one of bugs/ideas/
        players, and not the bare "reports" form) must still be
        rejected the same way the stock command always did.
        """
        result = self.call(
            reports.CmdManageReports(), "", cmdstring="manage nonsense", caller=self.account
        )
        self.assertIn("not a valid report category", result)
