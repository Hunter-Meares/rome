"""
Tests for typeclasses/accounts.py's Account.get_display_name override.

Real, confirmed live gap: a player saw "[Public] Zeus: ..." and
"[Public] Denvos: ..." on the same channel their actual characters
(Jupiter, Aeges) talk on - it read as two more, unfamiliar characters
talking, not as the people everyone already knew. Channels (and the
'channels' subscriber list) both call Account.get_display_name() to
decide what to show, which defaulted to the account's own real login
name regardless of who's puppeted.
"""

from evennia.utils.test_resources import EvenniaCommandTest


class TestAccountDisplayNameShowsThePuppetedCharacter(EvenniaCommandTest):
    def test_shows_character_name_while_puppeting(self):
        self.session.puppet = self.char1
        name = self.account.get_display_name(self.account2)
        self.assertIn(self.char1.key, name)

    def test_does_not_show_the_account_key_while_puppeting(self):
        self.session.puppet = self.char1
        name = self.account.get_display_name(self.account2)
        self.assertNotIn(self.account.key, name)

    def test_falls_back_to_account_key_when_not_puppeting(self):
        """Genuinely OOC (e.g. right after login, before 'ic') keeps
        Evennia's own default behavior - nothing to show instead."""
        self.session.puppet = None
        name = self.account.get_display_name(self.account2)
        self.assertIn(self.account.key, name)

    def test_channel_message_shows_the_character_name_not_the_account(self):
        self.session.puppet = self.char1
        formatted = self.account.at_pre_channel_msg(
            "hello there", None, senders=[self.account], no_prefix=True
        )
        self.assertIn(self.char1.key, formatted)
        self.assertNotIn(self.account.key, formatted)
