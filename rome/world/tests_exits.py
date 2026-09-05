"""
Tests for a real bug found live: a player typed 's' to go south and
got "Command 's' is not available" even though 'south' worked fine.
Evennia's own @tunnel/@open builder commands auto-add the standard
short alias (n/s/e/w/etc) when an exit is named one of the 12
recognized direction words, but that's those commands' own courtesy,
not something DefaultExit.at_object_creation() does by itself - and
almost every exit in this game was created directly in batch-build
scripts, bypassing it entirely. A live database sweep found 623 of
1265 exits missing their short alias. Fixed at the root in
typeclasses/exits.py so every future exit gets it automatically.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create

from world.combat import MOVEMENT_SP_COST


class TestExitStandardDirectionAliases(EvenniaTest):
    def test_south_exit_gets_s_alias_automatically(self):
        exit_obj = create.create_object(
            "typeclasses.exits.Exit",
            key="south",
            location=self.room1,
            destination=self.room2,
        )
        self.assertIn("s", [a.lower() for a in exit_obj.aliases.all()])

    def test_all_twelve_standard_directions_get_their_alias(self):
        expected = {
            "north": "n", "south": "s", "east": "e", "west": "w",
            "northeast": "ne", "northwest": "nw", "southeast": "se", "southwest": "sw",
            "up": "u", "down": "d", "in": "i", "out": "o",
        }
        for direction, short in expected.items():
            exit_obj = create.create_object(
                "typeclasses.exits.Exit",
                key=direction,
                location=self.room1,
                destination=self.room2,
            )
            self.assertIn(
                short,
                [a.lower() for a in exit_obj.aliases.all()],
                "exit '%s' didn't get its expected '%s' alias" % (direction, short),
            )

    def test_non_direction_exit_key_is_unaffected(self):
        exit_obj = create.create_object(
            "typeclasses.exits.Exit",
            key="a rickety ladder",
            location=self.room1,
            destination=self.room2,
        )
        self.assertEqual(list(exit_obj.aliases.all()), [])

    def test_explicit_aliases_are_preserved_alongside_the_automatic_one(self):
        exit_obj = create.create_object(
            "typeclasses.exits.Exit",
            key="south",
            aliases=["s", "back"],
            location=self.room1,
            destination=self.room2,
        )
        lowered = [a.lower() for a in exit_obj.aliases.all()]
        self.assertIn("s", lowered)
        self.assertIn("back", lowered)


class TestRealExitTraversalChargesMovementSP(EvenniaTest):
    """
    A real, previously-undiscovered bug found while adding movement
    feedback: Evennia's own DefaultExit.at_traverse calls
    move_to(..., move_type="traverse") - not "move" - so
    CombatCharacter.at_pre_move's movement-SP-cost gate (gated on
    move_type == "move" exactly) was silently exempting every single
    ordinary exit traversal in the game, despite
    tests_combat_commands.py's TestMovementSPCost passing the whole
    time (it calls at_pre_move directly with a hand-supplied
    move_type="move", never exercising a real Exit). Confirmed live
    before this fix: walking through a real Exit left SP completely
    unchanged. Fixed by reimplementing Exit.at_traverse
    (typeclasses/exits.py) with the corrected move_type. These tests
    go through the real Exit object specifically, not at_pre_move
    directly, so a regression here can't hide behind an isolated unit
    test again.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.combat_turnhandler = None
        self.char1.db.resting = False
        self.char1.db.is_dead = False
        self.char1.db.hp = 100
        self.char1.db.level = 1
        self.exit_obj = create.create_object(
            "typeclasses.exits.Exit",
            key="south",
            aliases=["s"],
            location=self.room1,
            destination=self.room2,
        )

    def test_real_traversal_deducts_movement_sp(self):
        self.char1.db.sp = 10
        self.char1.location = self.room1
        self.exit_obj.at_traverse(self.char1, self.room2)
        self.assertEqual(self.char1.db.sp, 10 - MOVEMENT_SP_COST)
        self.assertEqual(self.char1.location, self.room2)

    def test_real_traversal_blocked_when_out_of_sp(self):
        self.char1.db.sp = 0
        self.char1.location = self.room1
        self.exit_obj.at_traverse(self.char1, self.room2)
        self.assertEqual(self.char1.location, self.room1)

    def test_walk_message_sent_on_successful_traversal(self):
        self.char1.db.sp = 10
        self.char1.location = self.room1
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)
        self.exit_obj.at_traverse(self.char1, self.room2)
        self.assertIn("You walk south.", captured)

    def test_no_walk_message_when_traversal_is_blocked(self):
        self.char1.db.sp = 0
        self.char1.location = self.room1
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)
        self.exit_obj.at_traverse(self.char1, self.room2)
        self.assertNotIn("You walk south.", captured)
