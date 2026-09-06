"""
Regression tests for hiding god-only commands and help topics from
regular players - a direct security request: normal players should
never see channelkick/factionleader/godlevel/pontifex/restore/snoop/
slay, or the godbounty/godquest/godreligion help topics, in their own
help listing.

Evennia's help system (evennia/commands/default/help.py) filters the
visible command grid by each command's own "cmd" lock
(`cmd.access(caller, "cmd", session=...)`), and filters help-topic
listings by a "view" lock if one is defined (falling back to "read").
Every one of these commands/topics used to carry no lock at all (or,
for the three topics, an explicit "view:all()"), so they showed up
for every player regardless of level - not a secrecy mechanism, just
an oversight once the help category made them visually prominent.

The fix reuses the exact same in-function level gate each command
already enforces, expressed as a lock string via Evennia's built-in
attr_gt/attr_ge lockfuncs (which read the real db.level Attribute off
the accessing object, confirmed via evennia/locks/lockfuncs.py - not
a separate, possibly-drifting threshold). These tests check the lock
directly via .access(), which is what the real help listing and the
real cmdhandler both consult - unlike EvenniaCommandTest.call(),
which bypasses lock checks entirely and so could never have caught
this gap on its own.
"""

from evennia.utils.test_resources import EvenniaTest

from world.combat import CmdGodLevel, CmdWizInvis, CmdRestore, CmdSnoop, CmdSlay
from world.factions import CmdChannelKick, CmdFactionLeader
from world.religion import CmdPontifex
from world.help_setup import create_all_help_entries
from evennia.help.models import HelpEntry


# (command class, level that must just barely fail, level that must
# just barely pass) - matching each command's own real in-func gate.
GOD_ONLY_COMMANDS = [
    (CmdChannelKick, 100, 101),
    (CmdFactionLeader, 100, 101),
    (CmdPontifex, 100, 101),
    (CmdSlay, 100, 101),
    (CmdWizInvis, 101, 102),
    (CmdRestore, 101, 102),
    (CmdSnoop, 101, 102),
    (CmdGodLevel, 103, 104),
]


class TestGodOnlyCommandLocks(EvenniaTest):
    def test_ordinary_player_cannot_see_or_use_any_of_them(self):
        self.char1.db.level = 1
        for cmd_cls, _fail_level, _pass_level in GOD_ONLY_COMMANDS:
            cmd = cmd_cls()
            self.assertFalse(
                cmd.access(self.char1, "cmd"),
                "%s should be hidden from a level 1 player" % cmd_cls.__name__,
            )

    def test_level_just_below_threshold_is_still_blocked(self):
        for cmd_cls, fail_level, _pass_level in GOD_ONLY_COMMANDS:
            self.char1.db.level = fail_level
            cmd = cmd_cls()
            self.assertFalse(
                cmd.access(self.char1, "cmd"),
                "%s should still be hidden at level %d"
                % (cmd_cls.__name__, fail_level),
            )

    def test_level_at_threshold_is_visible(self):
        for cmd_cls, _fail_level, pass_level in GOD_ONLY_COMMANDS:
            self.char1.db.level = pass_level
            cmd = cmd_cls()
            self.assertTrue(
                cmd.access(self.char1, "cmd"),
                "%s should be visible at level %d"
                % (cmd_cls.__name__, pass_level),
            )

    def test_no_level_attribute_at_all_is_blocked(self):
        # A brand new object with no db.level set yet (not the normal
        # case for a real character, which always gets level 1, but
        # the safe/expected behavior either way).
        for cmd_cls, _fail_level, _pass_level in GOD_ONLY_COMMANDS:
            cmd = cmd_cls()
            self.assertFalse(cmd.access(self.char2, "cmd"))


class TestGodOnlyHelpTopicLocks(EvenniaTest):
    def setUp(self):
        super().setUp()
        create_all_help_entries()

    def test_ordinary_player_cannot_see_god_only_topics(self):
        self.char1.db.level = 1
        for key in ("godbounty", "godquest", "godreligion"):
            entry = HelpEntry.objects.get(db_key=key)
            self.assertFalse(
                entry.access(self.char1, "view"),
                "%s topic should be hidden from a level 1 player" % key,
            )

    def test_god_can_see_god_only_topics(self):
        self.char1.db.level = 101
        for key in ("godbounty", "godquest", "godreligion"):
            entry = HelpEntry.objects.get(db_key=key)
            self.assertTrue(
                entry.access(self.char1, "view"),
                "%s topic should be visible to a level 101 god" % key,
            )

    def test_player_facing_religion_topic_is_unaffected(self):
        # Only the three god-only topics changed - the ordinary
        # 'religion' topic must stay open to everyone.
        self.char1.db.level = 1
        entry = HelpEntry.objects.get(db_key="religion")
        self.assertTrue(entry.access(self.char1, "view"))


class TestMixedAudienceCommandsStayOpen(EvenniaTest):
    """
    CmdFaction and CmdReligion are used by both gods AND ordinary
    empowered mortals (a faction's own leader, a religion's own
    Pontifex) via their own internal can_manage_faction()/
    can_manage_religion() checks - these must NOT get a blanket
    god-only lock, or real non-god players would lose a legitimate
    feature. Confirmed by reading both commands directly: neither one
    has (nor should gain) a level-gated "cmd" lock.
    """

    def test_faction_command_has_no_god_only_cmd_lock(self):
        from world.factions import CmdFaction

        self.char1.db.level = 1
        cmd = CmdFaction()
        self.assertTrue(cmd.access(self.char1, "cmd"))

    def test_religion_command_has_no_god_only_cmd_lock(self):
        from world.religion import CmdReligion

        self.char1.db.level = 1
        cmd = CmdReligion()
        self.assertTrue(cmd.access(self.char1, "cmd"))
