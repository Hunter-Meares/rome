"""
Tests for world/sessions.py's RomeServerSession - the snoop-input
relay, added alongside CmdSnoop's existing output relay
(CombatCharacter.msg, world/combat.py) after a direct request that
snoop show both sides, not just what a target sees.
"""

from unittest.mock import Mock, patch

from evennia.utils.test_resources import EvenniaTest

from world.sessions import RomeServerSession


class TestSnoopInputRelay(EvenniaTest):
    def _make_session(self, puppet):
        session = RomeServerSession.__new__(RomeServerSession)
        session.get_puppet = Mock(return_value=puppet)
        return session

    def test_relays_input_to_a_snooper(self):
        session = self._make_session(self.char1)
        self.char1.db.snoopers = [self.char2]

        with patch.object(session, "audit", return_value={"text": "attack bandit"}), patch.object(
            RomeServerSession.__bases__[0], "data_in", return_value=None
        ):
            msgs = []
            self.char2.msg = lambda text, **kw: msgs.append(text)
            RomeServerSession.data_in(session, text=["attack bandit"])

        self.assertTrue(msgs)
        self.assertIn("attack bandit", msgs[0])
        self.assertIn(self.char1.key, msgs[0])

    def test_does_nothing_when_nobody_is_snooping(self):
        session = self._make_session(self.char1)
        self.char1.db.snoopers = None

        with patch.object(session, "audit") as mock_audit, patch.object(
            RomeServerSession.__bases__[0], "data_in", return_value=None
        ):
            RomeServerSession.data_in(session, text=["look"])

        mock_audit.assert_not_called()

    def test_never_relays_to_the_snooped_character_itself(self):
        """A defensive guard against a self-snoop somehow ending up in
        the list - must never echo someone's own input back to them."""
        session = self._make_session(self.char1)
        self.char1.db.snoopers = [self.char1]

        with patch.object(
            session, "audit", return_value={"text": "look"}
        ), patch.object(RomeServerSession.__bases__[0], "data_in", return_value=None):
            msgs = []
            self.char1.msg = lambda text, **kw: msgs.append(text)
            RomeServerSession.data_in(session, text=["look"])

        self.assertFalse(msgs)

    def test_masked_text_from_audit_is_what_gets_relayed(self):
        """The whole safety point of reusing audit() - a masked
        password must arrive at the snooper masked too, never raw."""
        session = self._make_session(self.char1)
        self.char1.db.snoopers = [self.char2]

        with patch.object(
            session, "audit", return_value={"text": "connect bob ********"}
        ), patch.object(RomeServerSession.__bases__[0], "data_in", return_value=None):
            msgs = []
            self.char2.msg = lambda text, **kw: msgs.append(text)
            RomeServerSession.data_in(session, text=["connect bob hunter2"])

        self.assertTrue(msgs)
        self.assertIn("********", msgs[0])
        self.assertNotIn("hunter2", msgs[0])

    def test_no_puppet_does_not_crash(self):
        session = self._make_session(None)
        with patch.object(RomeServerSession.__bases__[0], "data_in", return_value=None) as mock_super:
            RomeServerSession.data_in(session, text=["look"])
        mock_super.assert_called_once()
