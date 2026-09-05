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
