"""
Tests for world/tutorial.py's CmdJourney - the state-aware "what do I
do next" nudge. Checks the priority ordering (dead > in-combat > not
escaped > level bands) as much as the individual messages, since
that's the part most likely to silently break if a threshold ever
shifts.
"""

from evennia.utils.test_resources import EvenniaCommandTest

from world.tutorial import (
    CmdJourney,
    LUDUS_LEVEL_CEILING,
    SEWERS_LEVEL_CEILING,
    GERMANIA_LEVEL_CEILING,
)


class TestCmdJourney(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.is_dead = False
        self.char1.db.combat_turnhandler = None
        self.char1.db.colosseum_escaped = True
        self.char1.db.level = 1

    def test_whatnow_and_next_still_work_as_aliases(self):
        # Renamed to 'journey' (more in-character than 'whatnow') per
        # direct request, but this command exists specifically for
        # players who don't yet know what to do - it needs to stay
        # guessable by instinct, not just discoverable once you
        # already know its name.
        self.assertIn("whatnow", CmdJourney.aliases)
        self.assertIn("next", CmdJourney.aliases)

    def test_dead_takes_priority_over_everything(self):
        self.char1.db.is_dead = True
        self.char1.db.level = 100
        result = self.call(CmdJourney(), "", caller=self.char1)
        self.assertIn("You're dead", result)

    def test_in_combat_takes_priority_over_level(self):
        self.char1.db.combat_turnhandler = True
        self.char1.db.level = 100
        result = self.call(CmdJourney(), "", caller=self.char1)
        self.assertIn("in a fight right now", result)

    def test_not_escaped_takes_priority_over_level(self):
        self.char1.db.colosseum_escaped = False
        self.char1.db.level = 100
        result = self.call(CmdJourney(), "", caller=self.char1)
        self.assertIn("out of these", result)

    def test_low_level_suggests_the_ludus(self):
        self.char1.db.level = LUDUS_LEVEL_CEILING - 1
        result = self.call(CmdJourney(), "", caller=self.char1)
        self.assertIn("Ludus", result)

    def test_mid_level_suggests_the_sewers(self):
        self.char1.db.level = LUDUS_LEVEL_CEILING
        result = self.call(CmdJourney(), "", caller=self.char1)
        self.assertIn("Cloaca Maxima", result)

        self.char1.db.level = SEWERS_LEVEL_CEILING - 1
        result = self.call(CmdJourney(), "", caller=self.char1)
        self.assertIn("Cloaca Maxima", result)

    def test_higher_level_suggests_germania_and_side_content(self):
        self.char1.db.level = SEWERS_LEVEL_CEILING
        result = self.call(CmdJourney(), "", caller=self.char1)
        self.assertIn("Porta Flaminia", result)
        self.assertIn("achievements", result)

        self.char1.db.level = GERMANIA_LEVEL_CEILING - 1
        result = self.call(CmdJourney(), "", caller=self.char1)
        self.assertIn("Porta Flaminia", result)

    def test_max_level_gets_the_congratulatory_message(self):
        self.char1.db.level = GERMANIA_LEVEL_CEILING
        result = self.call(CmdJourney(), "", caller=self.char1)
        self.assertIn("cleared every zone", result)
