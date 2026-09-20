"""
Tests for world/socials.py - the data-driven social command (emote)
system. Rather than one test per social (80 of them, all sharing the
exact same dispatcher logic), this tests CmdSocial's actual behavior
generically against a few representative entries, plus a structural
validation pass confirming every single SOCIALS entry is well-formed
(correct tuple shapes, format strings that actually resolve) - the
kind of check that would catch a typo'd entry no individual test
would ever exercise.
"""

from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest
from evennia.utils import create

from world.socials import SOCIALS, CmdSocial, make_social_commands


def _make_social(key):
    """Builds a single, real CmdSocial subclass instance for `key`,
    the same way make_social_commands() does for the live cmdset."""
    return type("CmdSocial_%s" % key, (CmdSocial,), {"key": key})()


class TestSocialsStructure(EvenniaTest):
    """Validates the data itself, independent of any live dispatch -
    catches a malformed entry no single functional test would reach."""

    def test_every_entry_has_a_real_no_target_pair(self):
        for name, entry in SOCIALS.items():
            no_target = entry.get("no_target")
            self.assertIsNotNone(no_target, "%s has no 'no_target' entry" % name)
            self.assertEqual(len(no_target), 2, "%s's no_target isn't a 2-tuple" % name)
            actor_msg, room_msg = no_target
            self.assertIsInstance(actor_msg, str)
            self.assertIsInstance(room_msg, str)
            # room_msg must use {name}, never a bare literal name.
            self.assertIn("{name}", room_msg, "%s's room message doesn't use {{name}}" % name)

    def test_every_targeted_entry_is_a_real_3_tuple_or_none(self):
        for name, entry in SOCIALS.items():
            targeted = entry.get("targeted")
            if targeted is None:
                continue
            self.assertEqual(len(targeted), 3, "%s's targeted isn't a 3-tuple" % name)
            actor_msg, target_msg, room_msg = targeted
            for msg, label in ((actor_msg, "actor"), (target_msg, "target"), (room_msg, "room")):
                self.assertIsInstance(msg, str, "%s's %s message isn't a string" % (name, label))
            self.assertIn("{target}", actor_msg, "%s's actor message doesn't use {{target}}" % name)
            self.assertIn("{name}", target_msg, "%s's target message doesn't use {{name}}" % name)
            self.assertIn("{name}", room_msg, "%s's room message doesn't use {{name}}" % name)
            self.assertIn("{target}", room_msg, "%s's room message doesn't use {{target}}" % name)

    def test_every_entry_actually_formats_without_raising(self):
        for name, entry in SOCIALS.items():
            actor_msg, room_msg = entry["no_target"]
            room_msg.format(name="Someone")  # must not raise
            targeted = entry.get("targeted")
            if targeted:
                actor_msg, target_msg, room_msg = targeted
                actor_msg.format(target="Someone")
                target_msg.format(name="Someone")
                room_msg.format(name="Someone", target="Someone Else")

    def test_no_social_name_contains_whitespace(self):
        # Direct requirement: "no multiple word socials."
        for name in SOCIALS:
            self.assertNotIn(" ", name, "%s is a multi-word social name" % name)

    def test_make_social_commands_returns_one_per_entry_with_matching_keys(self):
        commands = make_social_commands()
        self.assertEqual(len(commands), len(SOCIALS))
        keys = {cmd.key for cmd in commands}
        self.assertEqual(keys, set(SOCIALS.keys()))

    def test_does_not_collide_with_a_real_existing_command(self):
        # The two real collisions found and fixed while building this
        # list - regression coverage so a future addition can't
        # silently reintroduce either.
        self.assertNotIn("greet", SOCIALS)  # CmdGreet - mask-proof identity reveal
        self.assertNotIn("hold", SOCIALS)  # CmdPass's own alias


class TestCmdSocialDispatch(EvenniaCommandTest):
    """Functional tests against a handful of representative entries -
    one with a full targeted form (smile), one with no targeted form
    at all (yawn), and the generic self-target/not-found paths, which
    behave identically across every entry regardless of which one."""

    def test_no_target_messages_actor_and_room(self):
        result = self.call(_make_social("smile"), "", caller=self.char1)
        self.assertIn("You smile.", result)

    def test_targeted_message_to_the_caller_is_correct(self):
        result = self.call(_make_social("smile"), "Char2", caller=self.char1)
        self.assertIn("You smile at Char2.", result)

    def test_targeted_message_to_the_target_is_correct(self):
        self.char1.location = self.room1
        self.char2.location = self.room1
        received = []
        real_msg = self.char2.msg

        def _capture(text=None, **kwargs):
            if text:
                received.append(str(text[0]) if isinstance(text, tuple) else str(text))
            return real_msg(text=text, **kwargs)

        self.char2.msg = _capture
        try:
            self.call(_make_social("smile"), "Char2", caller=self.char1)
        finally:
            self.char2.msg = real_msg

        self.assertTrue(any("smiles at you" in m for m in received))

    def test_unfound_target_sends_a_message_and_does_not_crash(self):
        result = self.call(_make_social("smile"), "NobodyHere", caller=self.char1)
        # caller.search()'s own default not-found message - just
        # confirming this doesn't raise and produces SOME feedback,
        # not asserting the exact wording of Evennia's own built-in.
        self.assertTrue(result)

    def test_self_target_falls_back_to_the_plain_no_target_message(self):
        result = self.call(_make_social("smile"), "Char", caller=self.char1)
        self.assertIn("You smile.", result)

    def test_self_target_via_me_keyword_falls_back_too(self):
        result = self.call(_make_social("smile"), "me", caller=self.char1)
        self.assertIn("You smile.", result)

    def test_a_social_with_no_targeted_form_refuses_a_target(self):
        result = self.call(_make_social("yawn"), "Char2", caller=self.char1)
        self.assertIn("not something you can do to someone else", result)

    def test_a_social_with_no_targeted_form_still_works_untargeted(self):
        result = self.call(_make_social("yawn"), "", caller=self.char1)
        self.assertIn("You yawn.", result)

    def test_room_message_reaches_a_bystander_correctly(self):
        bystander = create.create_object(
            "typeclasses.characters.Character", key="a bystander", location=self.room1
        )
        self.char1.location = self.room1
        self.char2.location = self.room1

        received = []
        real_msg = bystander.msg

        def _capture(text=None, **kwargs):
            if text:
                received.append(str(text[0]) if isinstance(text, tuple) else str(text))
            return real_msg(text=text, **kwargs)

        bystander.msg = _capture
        try:
            self.call(_make_social("wave"), "Char2", caller=self.char1)
        finally:
            bystander.msg = real_msg

        self.assertTrue(any("waves at" in m for m in received))
