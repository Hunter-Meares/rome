"""
Tests for CmdOOC's combat-aware override (world/combat.py) - blocks
'ooc' while the character actually puppeted by the issuing session is
mid-combat, extending the exact same hard block CmdQuit already has
(world/tests_quit.py) after a real question confirmed going ooc
doesn't actually let a player escape a fight for free - it just
leaves their character defenseless in it, which is worse, not better,
so it's blocked outright instead.
"""

from evennia.utils.test_resources import EvenniaCommandTest
from evennia.utils import create

from world.combat import CmdOOC


class TestCmdOOCCombatOverride(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.combat_turnhandler = None
        # ooc is an account-level command (account_caller=True) - the
        # real cmdhandler sets self.caller to the account, not the
        # puppeted character.
        self.session.puppet = self.char1

    def test_blocked_while_puppeted_character_is_in_combat(self):
        self.char1.db.combat_turnhandler = "truthy_stand_in"
        result = self.call(CmdOOC(), "", caller=self.account)
        self.assertIn("cannot go OOC now", result)
        self.assertIn("still fighting", result)

    def test_allowed_when_puppeted_character_is_not_in_combat(self):
        self.char1.db.combat_turnhandler = None
        result = self.call(CmdOOC(), "", caller=self.account)
        self.assertNotIn("cannot go OOC now", result)

    def test_allowed_when_session_has_no_puppet(self):
        """Already-OOC account can always run ooc again (Evennia's own
        real func() just tells them "You are already OOC.")."""
        self.session.puppet = None
        self.char1.db.combat_turnhandler = "truthy_stand_in"
        result = self.call(CmdOOC(), "", caller=self.account)
        self.assertNotIn("cannot go OOC now", result)

    def test_only_checks_this_sessions_own_puppet(self):
        bystander = create.create_object(
            "typeclasses.characters.Character", key="Bystander", location=self.room1
        )
        self.session.puppet = bystander
        self.char1.db.combat_turnhandler = "truthy_stand_in"

        result = self.call(CmdOOC(), "", caller=self.account)

        self.assertNotIn("cannot go OOC now", result)

    def test_blocked_character_stays_puppeted(self):
        self.char1.db.combat_turnhandler = "truthy_stand_in"
        self.call(CmdOOC(), "", caller=self.account)
        # Still puppeting the same character - the block genuinely
        # stopped the unpuppet, it didn't happen anyway.
        self.assertEqual(self.session.puppet, self.char1)
