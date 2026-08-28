"""
Light integration coverage for the ingame_reports contrib (CmdBug,
CmdIdea, CmdReport, all bundled in ReportsCmdSet and installed on
AccountCmdSet) - not re-testing the contrib's own internals, just
confirming it's actually wired up correctly and that filing a real
bug/idea/player report produces a real, readable report.
"""
from evennia.contrib.base_systems.ingame_reports import ReportsCmdSet
from evennia.contrib.base_systems.ingame_reports.reports import CmdBug, CmdIdea, CmdReport
from evennia.utils.test_resources import EvenniaCommandTest

from commands.default_cmdsets import AccountCmdSet


class TestReportsCmdSetRegistration(EvenniaCommandTest):
    """
    Confirms ReportsCmdSet is actually part of AccountCmdSet, so the
    commands are reachable in-game and not just importable in isolation.
    """

    def test_account_cmdset_includes_reports(self):
        cmdset = AccountCmdSet()
        cmdset.at_cmdset_creation()
        keys = {cmd.key for cmd in cmdset.commands}
        self.assertIn("bug", keys)
        self.assertIn("idea", keys)
        self.assertIn("report", keys)
        self.assertIn("manage reports", keys)


class TestFilingReports(EvenniaCommandTest):
    """
    Real end-to-end filing of each report type, confirming the expected
    success message comes back to the reporter.
    """

    def test_file_an_idea(self):
        result = self.call(CmdIdea(), "More gladiator taunts, please.", caller=self.char1)
        self.assertIn("Thank you for your suggestion", result)

    def test_file_a_bug(self):
        self.account.permissions.add("Developer")
        result = self.call(CmdBug(), "The Colosseum gate never opens.", caller=self.char1)
        self.assertIn("Your report has been filed", result)

    def test_file_a_player_report(self):
        # CmdReport is account_caller, so target_search() resolves against
        # AccountDB.search() - that matches by Account key, not Character
        # key, so the target string here is self.account2's own name.
        result = self.call(
            CmdReport(),
            f"{self.account2.key}=Kept spamming the same line in Forum chat.",
            caller=self.account,
        )
        self.assertIn("Your report has been filed", result)
