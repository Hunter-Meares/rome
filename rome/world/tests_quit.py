"""
Tests for CmdQuit's combat-aware override (world/combat.py) - blocks
'quit' while the character actually puppeted by the issuing session is
mid-combat, per the explicit design in that class's docstring: a hard
block (not an auto-disengage), and scoped to THIS session's puppet
specifically, not just any character owned by the account.

Note: EvenniaTest's base setUp() already replaces
evennia.SESSION_HANDLER.data_out and .disconnect with Mocks (see
evennia/utils/test_resources.py), so letting the real, un-blocked
quit path run through to completion is safe here - it won't try to
touch a real network connection.
"""

from evennia.utils.test_resources import EvenniaCommandTest
from evennia.utils import create

from world.combat import CmdQuit


class TestCmdQuitCombatOverride(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.combat_turnhandler = None
        # quit is an account-level command (account_caller=True) - the
        # real cmdhandler sets self.caller to the account, not the
        # puppeted character. self.session already exists via
        # EvenniaTest's setup_session().
        self.session.puppet = self.char1

    def test_blocked_while_puppeted_character_is_in_combat(self):
        self.char1.db.combat_turnhandler = "truthy_stand_in"  # is_in_combat only checks bool()
        result = self.call(CmdQuit(), "", caller=self.account)
        self.assertIn("cannot quit now", result)
        self.assertIn("still fighting", result)

    def test_allowed_when_puppeted_character_is_not_in_combat(self):
        self.char1.db.combat_turnhandler = None
        result = self.call(CmdQuit(), "", caller=self.account)
        self.assertNotIn("cannot quit now", result)

    def test_allowed_when_session_has_no_puppet(self):
        """An account in OOC mode (not puppeting anyone) can always quit."""
        self.session.puppet = None
        self.char1.db.combat_turnhandler = "truthy_stand_in"  # some character IS fighting...
        result = self.call(CmdQuit(), "", caller=self.account)
        # ...but this session isn't puppeting them, so it's not blocked.
        self.assertNotIn("cannot quit now", result)

    def test_only_checks_this_sessions_own_puppet(self):
        """
        The docstring is explicit: this checks the character actually
        puppeted by THIS session, not just any character owned by the
        account. Puppet a different (non-fighting) character on this
        session while char1 (a separate character) is mid-combat -
        quit must NOT be blocked, since this session isn't the one
        controlling the fighting character.
        """
        bystander = create.create_object(
            "typeclasses.characters.Character", key="Bystander", location=self.room1
        )
        self.session.puppet = bystander
        self.char1.db.combat_turnhandler = "truthy_stand_in"

        result = self.call(CmdQuit(), "", caller=self.account)

        self.assertNotIn("cannot quit now", result)

    def test_blocked_message_does_not_disconnect_the_session(self):
        self.char1.db.combat_turnhandler = "truthy_stand_in"
        self.call(CmdQuit(), "", caller=self.account)
        # Still logged in - the block genuinely stopped the quit, it
        # didn't just print a warning and disconnect anyway.
        self.assertTrue(self.session.logged_in)
