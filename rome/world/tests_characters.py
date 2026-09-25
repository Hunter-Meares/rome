"""
Tests for typeclasses/characters.py's divine teleport flavor
(_wants_divine_flavor, announce_move_from/to's divine_presence
handling) - previously entirely untested. Real, confirmed live bug
fixed here: a god-tier character (db.level > 100) with no
divine_presence explicitly set got Evennia's plain default move
message on every godteleport, contradicting the module's own stated
intent ("a future god-player doesn't need a lore entry written before
they can use this").
"""

from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import _wants_divine_flavor


class TestWantsDivineFlavor(EvenniaTest):
    def test_a_mortal_walking_gets_no_flavor(self):
        self.char1.db.level = 50
        self.char1.db.divine_presence = None
        self.assertFalse(_wants_divine_flavor(self.char1, "move"))

    def test_a_mortal_teleporting_gets_no_flavor(self):
        self.char1.db.level = 50
        self.char1.db.divine_presence = None
        self.assertFalse(_wants_divine_flavor(self.char1, "teleport"))

    def test_a_god_walking_gets_no_flavor(self):
        # Divine flavor is teleport-only - regular walking is untouched.
        self.char1.db.level = 106
        self.char1.db.divine_presence = None
        self.assertFalse(_wants_divine_flavor(self.char1, "move"))

    def test_a_god_teleporting_with_no_divine_presence_set_still_gets_the_fallback(self):
        # This is the real bug: a god-tier character with
        # divine_presence never explicitly set used to get nothing
        # special at all.
        self.char1.db.level = 101
        self.char1.db.divine_presence = None
        self.assertTrue(_wants_divine_flavor(self.char1, "teleport"))

    def test_a_mortal_with_divine_presence_explicitly_set_still_gets_flavor(self):
        # Not gated on level alone - explicitly setting divine_presence
        # always works too, e.g. for a lore NPC that isn't a real
        # "god" by level at all.
        self.char1.db.level = 5
        self.char1.db.divine_presence = "jupiter"
        self.assertTrue(_wants_divine_flavor(self.char1, "teleport"))


class TestDivineTeleportMessages(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.wizinvis = False

    def test_a_god_with_no_divine_presence_gets_the_generic_fallback_on_arrival(self):
        self.char1.db.level = 103
        self.char1.db.divine_presence = None
        self.char1.location = self.room1

        received = []
        self.room1.msg_contents = lambda text, **kw: received.append(text)

        self.char1.announce_move_to(self.room2, move_type="teleport")

        self.assertTrue(received)
        self.assertIn("radiant light", received[0].lower())

    def test_a_god_with_no_divine_presence_gets_the_generic_fallback_on_departure(self):
        self.char1.db.level = 103
        self.char1.db.divine_presence = None
        self.char1.location = self.room1

        received = []
        self.room1.msg_contents = lambda text, **kw: received.append(text)

        self.char1.announce_move_from(self.room2, move_type="teleport")

        self.assertTrue(received)
        self.assertIn("light fades", received[0].lower())

    def test_a_named_god_still_gets_their_own_signature_message(self):
        self.char1.db.level = 106
        self.char1.db.divine_presence = "jupiter"
        self.char1.location = self.room1

        received = []
        self.room1.msg_contents = lambda text, **kw: received.append(text)

        self.char1.announce_move_to(self.room2, move_type="teleport")

        self.assertTrue(received)
        self.assertIn("thunder", received[0].lower())

    def test_a_mortal_teleporting_gets_the_plain_default_message_not_a_divine_one(self):
        self.char1.db.level = 10
        self.char1.db.divine_presence = None
        self.char1.location = self.room1

        received = []
        self.room1.msg_contents = lambda text, **kw: received.append(text)

        self.char1.announce_move_to(self.room2, move_type="teleport")

        self.assertTrue(received)
        # Evennia's own default announce_move_to (the fallthrough path
        # here) may pass a plain string OR a (text, options) tuple to
        # msg_contents - only the divine-flavor branch always sends a
        # plain string directly.
        text = received[0][0] if isinstance(received[0], tuple) else received[0]
        self.assertNotIn("radiant light", str(text).lower())
