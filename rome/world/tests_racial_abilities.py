"""
Tests for world/racial_abilities.py - the first real, working mechanic
behind a race's own listed "signature abilities" (previously pure
flavor text - see that module's own docstring for the full story
behind why this exists: a real player asked in-character how to use
their race's abilities, and there was genuinely no way to).
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaCommandTest
from evennia.utils import create

from world.combat import COMBAT_RULES, CmdFight
from world.racial_abilities import (
    RACIAL_ABILITIES,
    racial_abilities_known,
    CmdRacial,
    CmdRacialInfo,
)


class TestRacialAbilitiesKnown(EvenniaCommandTest):
    def test_nymph_knows_both_of_its_own_abilities(self):
        self.char1.db.race = "nymph"
        known = racial_abilities_known(self.char1)
        self.assertEqual(known, ["boon of the wilds", "elemental ward"])

    def test_a_different_race_does_not_know_nymph_abilities(self):
        self.char1.db.race = "cyclops"
        known = racial_abilities_known(self.char1)
        self.assertNotIn("boon of the wilds", known)
        self.assertIn("crushing blow", known)

    def test_every_ability_names_a_real_race(self):
        # A typo'd race key here would silently make an ability
        # unreachable by anyone - cheap, load-bearing insurance.
        from world.chargen_menu import RACES

        for name, data in RACIAL_ABILITIES.items():
            self.assertIn(data["race"], RACES, "racial ability '%s' names an unknown race" % name)


class RacialAbilityCommandTestBase(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.db.virtus = 10
            char.db.agilitas = 10
            char.db.ingenium = 10
            char.db.vigor = 10
            char.db.max_hp = 100
            char.db.hp = 100
            char.db.max_mp = 20
            char.db.mp = 20
            char.db.max_sp = 30
            char.db.sp = 30
            char.db.is_dead = False
            char.db.resting = False
            char.db.combat_turnhandler = None
            char.db.combat_side = None
            char.db.conditions = {}
            char.db.cooldowns = {}
            char.location = self.room1


class TestCmdRacialInfo(RacialAbilityCommandTestBase):
    def test_shows_known_abilities_and_ready_status(self):
        self.char1.db.race = "nymph"
        result = self.call(CmdRacialInfo(), "", caller=self.char1)
        self.assertIn("Boon Of The Wilds", result)
        self.assertIn("Elemental Ward", result)
        self.assertIn("ready", result)

    def test_shows_cooldown_status_when_recovering(self):
        self.char1.db.race = "nymph"
        self.char1.db.cooldowns = {"boon of the wilds": 3}
        result = self.call(CmdRacialInfo(), "", caller=self.char1)
        self.assertIn("recovering - 3 more turns", result)

    def test_a_race_with_no_abilities_built_yet_gets_an_honest_message(self):
        self.char1.db.race = "human"  # Command Presence/Civic Access - not built
        result = self.call(CmdRacialInfo(), "", caller=self.char1)
        self.assertIn("grants you no innate abilities", result)


class TestCmdRacialHeal(RacialAbilityCommandTestBase):
    def test_boon_of_the_wilds_heals_self_by_default(self):
        self.char1.db.race = "nymph"
        self.char1.db.hp = 50

        with patch("world.racial_abilities.randint", return_value=20):
            self.call(CmdRacial(), "boon of the wilds", caller=self.char1)

        self.assertGreater(self.char1.db.hp, 50)

    def test_boon_of_the_wilds_can_target_an_ally_by_name(self):
        self.char1.db.race = "nymph"
        self.char2.db.hp = 50
        self.char2.db.max_hp = 100

        with patch("world.racial_abilities.randint", return_value=20):
            self.call(CmdRacial(), "boon of the wilds = Char2", caller=self.char1)

        self.assertGreater(self.char2.db.hp, 50)

    def test_goes_on_cooldown_after_use(self):
        self.char1.db.race = "nymph"
        self.call(CmdRacial(), "boon of the wilds", caller=self.char1)
        self.assertEqual(self.char1.db.cooldowns.get("boon of the wilds"), 8)

    def test_refused_while_on_cooldown(self):
        self.char1.db.race = "nymph"
        self.char1.db.cooldowns = {"boon of the wilds": 5}
        result = self.call(CmdRacial(), "boon of the wilds", caller=self.char1)
        self.assertIn("still recovering", result)


class TestCmdRacialCondition(RacialAbilityCommandTestBase):
    def test_elemental_ward_grants_defense_up_to_self(self):
        self.char1.db.race = "nymph"
        self.call(CmdRacial(), "elemental ward", caller=self.char1)
        self.assertIn("Defense Up", self.char1.db.conditions)

    def test_cannot_use_an_ability_your_race_does_not_grant(self):
        self.char1.db.race = "human"
        result = self.call(CmdRacial(), "elemental ward", caller=self.char1)
        self.assertIn("doesn't grant you an ability called that", result)

    def test_intimidating_presence_cannot_target_self(self):
        self.char1.db.race = "cyclops"
        # "me" rather than the caller's own key - a real, confirmed
        # gap in EvenniaCommandTest's fixture room otherwise: an
        # out-of-combat self-search by exact name isn't reliable here
        # the same way CmdAttack's own self-target test avoids it too
        # (that one only runs the same search after already starting
        # a duel). "me" is Evennia's own built-in self-reference and
        # sidesteps that entirely - this test is about the "can't
        # target yourself" guard, not about name resolution.
        result = self.call(CmdRacial(), "intimidating presence = me", caller=self.char1)
        self.assertIn("can't use", result)


class TestCmdRacialStartsCombat(RacialAbilityCommandTestBase):
    """
    Mirrors CmdCast/CmdUseSkill's own fix from the same session - an
    offensive racial ability used outside combat must actually start a
    real, tracked fight (see start_combat_from_offensive_action's own
    docstring, world/combat.py), not land as a free hit.
    """

    def test_crushing_blow_out_of_combat_starts_a_real_fight(self):
        self.char1.db.race = "cyclops"
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

        self.call(CmdRacial(), "crushing blow = Char2", caller=self.char1)

        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char2))

    def test_a_self_targeted_ability_never_starts_a_fight(self):
        self.char1.db.race = "nymph"
        self.call(CmdRacial(), "elemental ward", caller=self.char1)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))


class TestCmdRacialDefaultsToCurrentOpponent(RacialAbilityCommandTestBase):
    def test_defaults_to_combat_last_target_with_multiple_enemies_present(self):
        third = create.create_object(
            "typeclasses.characters.Character", key="a third fighter", location=self.room1
        )
        third.db.hp = 50
        third.db.max_hp = 50

        self.char1.db.race = "cyclops"
        with patch("world.combat.COMBAT_RULES.roll_init") as mock_roll:
            mock_roll.side_effect = lambda char: 1000 if char == self.char1 else 1
            self.call(CmdFight(), "Char2", caller=self.char1)
        self.char1.db.combat_turnhandler.db.fighters.append(third)
        third.db.combat_turnhandler = self.char1.db.combat_turnhandler
        third.db.combat_side = "solo_join_%d" % id(third)
        self.char1.db.combat_last_target = self.char2

        with patch("world.racial_abilities.randint", return_value=100):
            self.call(CmdRacial(), "crushing blow", caller=self.char1)

        # Landed on char2 (the current target), not third.
        self.assertLess(self.char2.db.hp, 100)
        self.assertEqual(third.db.hp, 50)
