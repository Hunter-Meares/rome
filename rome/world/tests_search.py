"""
Tests for three related, real bugs found live during human playtests:

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

3. A real player spent ~10 minutes of a 75-minute first session stuck
   on exactly that disambiguation prompt, guessing at "recruit"/
   "trainer"/"ludus recruit trainer" against three genuinely identical
   NPCs before finding the "1-name" format on their own. Ambiguous
   multi-matches now auto-resolve to the first candidate instead of
   blocking on a prompt - see at_search.py's own module docstring for
   the full reasoning. The leading-number format from bug #2 still
   works unchanged for anyone who wants a specific one; it just isn't
   forced on everyone by default anymore.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create

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


class TestMultimatchAutoResolvesToFirstMatch(EvenniaTest):
    """
    Regression coverage for the auto-resolve fix - see this module's
    own docstring, item 3, for the real player friction that motivated
    it.
    """

    def setUp(self):
        super().setUp()
        self.trainer1 = create.create_object(
            "typeclasses.characters.Character", key="a Ludus recruit trainer", location=self.room1
        )
        self.trainer2 = create.create_object(
            "typeclasses.characters.Character", key="a Ludus recruit trainer", location=self.room1
        )
        self.trainer3 = create.create_object(
            "typeclasses.characters.Character", key="a Ludus recruit trainer", location=self.room1
        )

    def test_multimatch_auto_resolves_to_the_first_candidate(self):
        result = at_search_result(
            [self.trainer1, self.trainer2, self.trainer3], self.char1, query="trainer"
        )
        self.assertIs(result, self.trainer1)

    def test_auto_resolve_sends_no_disambiguation_message(self):
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)
        at_search_result([self.trainer1, self.trainer2], self.char1, query="trainer")
        self.assertEqual(captured, [])

    def test_quiet_multimatch_still_returns_the_full_list(self):
        # A caller that explicitly wants every match (e.g. a "target
        # all enemies" style command) must be unaffected by the
        # auto-resolve change - only the non-quiet, single-target path
        # changed.
        result = at_search_result(
            [self.trainer1, self.trainer2], self.char1, query="trainer", quiet=True
        )
        self.assertEqual(result, [self.trainer1, self.trainer2])

    def test_single_match_passes_straight_through(self):
        result = at_search_result([self.trainer1], self.char1, query="trainer")
        self.assertEqual(result, self.trainer1)

    def test_no_match_returns_none(self):
        result = at_search_result([], self.char1, query="nonexistent")
        self.assertIsNone(result)

    def test_no_match_still_shows_the_not_found_message(self):
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)
        at_search_result([], self.char1, query="nonexistent")
        self.assertIn("Could not find 'nonexistent'.", captured)

    def test_leading_number_disambiguation_still_works_unchanged(self):
        # This is a SEPARATE mechanism (rpsystem's own search-string
        # preprocessing, before matching even happens) from the
        # auto-resolve change above - confirms it's genuinely
        # untouched, not just coincidentally still passing.
        result = self.char1.search("2-recruit trainer")
        self.assertIs(result, self.trainer2)
