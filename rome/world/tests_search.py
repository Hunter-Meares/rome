"""
Tests for two related, real bugs found live during a human playtest:

1. Every flavor NPC using typeclasses.characters.Character (which
   pulls in rpsystem's ContribRPCharacter) showed the generic sdesc
   "A normal person" to every player, since nothing ever set a real
   one - rpsystem's own at_object_creation() writes that literal
   string as its built-in default, and this project never overrode it
   for anything but a chargen'd player character. Fixed in
   Character.at_object_creation() (typeclasses/characters.py) by
   defaulting sdesc to the object's own key instead.

2. A player disambiguating between multiple same-named NPCs (e.g.
   three Ludus recruit trainers) was shown Evennia's default trailing-
   number format ("a Ludus recruit trainer-1") but typing that back
   always failed to match anything - every player search here actually
   routes through rpsystem's own sdesc-aware search override, which
   only recognizes a LEADING number ("1-a Ludus recruit trainer").
   Fixed with a custom SEARCH_AT_RESULT (server/conf/at_search.py)
   that displays the number first, matching what will actually work.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from evennia.utils.ansi import ANSIString

from server.conf.at_search import at_search_result


class TestFlavorNPCDefaultSdesc(EvenniaTest):
    def test_new_character_gets_its_own_key_as_sdesc_not_generic_default(self):
        npc = create.create_object(
            "typeclasses.characters.Character", key="Old Milo", location=self.room1
        )
        self.assertEqual(npc.sdesc.get(), "Old Milo")
        self.assertNotIn("normal person", npc.sdesc.get())

    def test_real_player_characters_still_get_their_own_key_by_default_too(self):
        # Chargen itself later overwrites this with a proper player-chosen
        # default - this just confirms creation no longer leaves rpsystem's
        # own generic placeholder in place even before that happens.
        self.assertNotIn("normal person", self.char1.sdesc.get())


class TestMultimatchLeadingNumberDisplay(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.trainer1 = create.create_object(
            "typeclasses.characters.Character", key="a Ludus recruit trainer", location=self.room1
        )
        self.trainer2 = create.create_object(
            "typeclasses.characters.Character", key="a Ludus recruit trainer", location=self.room1
        )

    def test_multimatch_returns_none(self):
        result = at_search_result([self.trainer1, self.trainer2], self.char1, query="trainer")
        self.assertIsNone(result)

    def test_single_match_passes_straight_through(self):
        result = at_search_result([self.trainer1], self.char1, query="trainer")
        self.assertEqual(result, self.trainer1)

    def test_no_match_returns_none(self):
        result = at_search_result([], self.char1, query="nonexistent")
        self.assertIsNone(result)

    def test_multimatch_text_shows_leading_number_not_trailing(self):
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)
        at_search_result([self.trainer1, self.trainer2], self.char1, query="trainer")
        full_text = ANSIString("".join(captured)).clean()
        self.assertIn("1-a Ludus recruit trainer", full_text)
        self.assertIn("2-a Ludus recruit trainer", full_text)
        self.assertNotIn("a Ludus recruit trainer-1", full_text)
