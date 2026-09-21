"""
Tests for world/welcome_mail.py - the one-time, in-character welcome
letter sent from Jupiter's own real character to a brand-new
character the moment chargen completes.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from evennia.comms.models import Msg

from world.welcome_mail import send_welcome_mail, WELCOME_MAIL_SUBJECT


class TestSendWelcomeMail(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.jupiter = create.create_object(
            "typeclasses.characters.Character", key="Jupiter", location=self.room1,
        )

    def _mail_for(self, character):
        return Msg.objects.get_by_tag(category="mail").filter(db_receivers_objects=character)

    def test_sends_a_real_discoverable_mail_to_the_new_character(self):
        send_welcome_mail(self.char1)
        mail = self._mail_for(self.char1)
        self.assertEqual(mail.count(), 1)

    def test_mail_is_from_jupiter(self):
        send_welcome_mail(self.char1)
        mail = self._mail_for(self.char1).first()
        self.assertIn(self.jupiter, mail.senders)

    def test_mail_has_the_expected_subject(self):
        send_welcome_mail(self.char1)
        mail = self._mail_for(self.char1).first()
        self.assertEqual(mail.header, WELCOME_MAIL_SUBJECT)

    def test_mail_points_to_the_real_tutorial_commands(self):
        send_welcome_mail(self.char1)
        mail = self._mail_for(self.char1).first()
        self.assertIn("help newbie", mail.message)
        self.assertIn("whatnow", mail.message)

    def test_missing_jupiter_is_a_silent_no_op(self):
        self.jupiter.delete()
        # Must not raise.
        send_welcome_mail(self.char1)
        self.assertEqual(self._mail_for(self.char1).count(), 0)

    def test_two_different_new_characters_each_get_their_own_mail(self):
        send_welcome_mail(self.char1)
        send_welcome_mail(self.char2)
        self.assertEqual(self._mail_for(self.char1).count(), 1)
        self.assertEqual(self._mail_for(self.char2).count(), 1)
