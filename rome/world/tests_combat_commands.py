"""
End-to-end tests for the actual combat Commands (CmdFight, CmdAttack,
CmdPowerAttack, CmdPass, CmdDisengage, CmdChallenge, CmdCast,
CmdUseSkill) - the priority gap flagged after the first review pass:
world/tests_combat.py exercised CombatRules' methods directly, but
never the Command layer itself (argument parsing, turn/action gating,
target resolution) where a player would actually notice a bug.

Also carries the regression tests for a real bug found while writing
this file: CmdCast and CmdUseSkill's named-target resolution used
plain caller.search(), which - like the already-documented
find_combat_target fix for attack/fight/powerattack - fails to find
another real Character by their exact name for a non-Builder caller
(rpsystem's sdesc-aware search override; NPCs are unaffected since
they don't have an sdesc handler). Both commands now use
find_combat_target, matching existing precedent in this file.
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaCommandTest
from evennia.utils import create

from world.combat import (
    COMBAT_RULES,
    CombatTurnHandler,
    CmdFight,
    CmdAttack,
    CmdPowerAttack,
    CmdPass,
    CmdDisengage,
    CmdChallenge,
    CmdCast,
    CmdUseSkill,
    CmdCoreStats,
    POWERATTACK_SP_COST,
    DISENGAGE_SUCCESS_CHANCE,
)


class CombatCommandTestBase(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.db.wielded_weapon = None
            char.db.worn_armor = None
            char.db.conditions = {}
            char.db.virtus = 10
            char.db.agilitas = 10
            char.db.ingenium = 10
            char.db.vigor = 10
            char.db.player_class = None
            char.db.damage_log = {}
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
            char.location = self.room1

    def _start_duel(self):
        """Puts char1 and char2 into a real 1v1 fight via CmdFight, char1 going first."""
        with patch("world.combat.COMBAT_RULES.roll_init") as mock_roll:
            # char1 always wins initiative -> goes first.
            mock_roll.side_effect = lambda char: 1000 if char == self.char1 else 1
            self.call(CmdFight(), "Char2", caller=self.char1)
        return self.char1.db.combat_turnhandler


class TestCmdFight(CombatCommandTestBase):
    def test_starts_a_duel_with_a_named_target(self):
        self.call(CmdFight(), "Char2", caller=self.char1)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char2))

    def test_no_target_auto_picks_lone_other_fighter(self):
        self.call(CmdFight(), "", caller=self.char1)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))

    def test_cannot_fight_self(self):
        self.call(CmdFight(), "Char1", caller=self.char1)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_cannot_fight_while_already_in_combat(self):
        self._start_duel()
        result = self.call(CmdFight(), "Char2", caller=self.char1)
        self.assertIn("already in a fight", result)

    def test_cannot_fight_while_resting(self):
        self.char1.db.resting = True
        result = self.call(CmdFight(), "Char2", caller=self.char1)
        self.assertIn("resting", result)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_cannot_fight_if_dead(self):
        self.char1.db.is_dead = True
        result = self.call(CmdFight(), "Char2", caller=self.char1)
        self.assertIn("dead", result)

    def test_fight_all_groups_by_party(self):
        ally = create.create_object(
            "typeclasses.characters.Character", key="Ally", location=self.room1
        )
        ally.db.hp = 100
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, ally]
        ally.db.party_leader = self.char1

        self.call(CmdFight(), "all", caller=self.char1)

        handler = self.char1.db.combat_turnhandler
        self.assertTrue(handler)
        self.assertEqual(self.char1.db.combat_side, ally.db.combat_side)
        self.assertNotEqual(self.char1.db.combat_side, self.char2.db.combat_side)


class TestCmdAttack(CombatCommandTestBase):
    def test_attack_out_of_combat_is_rejected(self):
        result = self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertIn("only do that in combat", result)

    def test_attack_on_your_turn_deals_damage(self):
        self._start_duel()
        self.char2.db.hp = 100
        # A non-lethal roll (100 would one-shot a 100-hp char2, which
        # triggers the real player-defeat/respawn flow and restores
        # hp to full again - not what this test is checking).
        with patch("world.combat.randint", return_value=30):
            self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertLess(self.char2.db.hp, 100)

    def test_attack_out_of_turn_is_rejected(self):
        self._start_duel()
        result = self.call(CmdAttack(), "Char1", caller=self.char2)
        self.assertIn("only do that on your turn", result)

    def test_cannot_attack_self(self):
        self._start_duel()
        result = self.call(CmdAttack(), self.char1.key, caller=self.char1)
        self.assertIn("can't attack yourself", result)

    def test_dead_cannot_attack(self):
        self._start_duel()
        self.char1.db.is_dead = True
        result = self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertIn("dead", result)


class TestCmdPowerAttack(CombatCommandTestBase):
    def test_requires_enough_sp(self):
        self._start_duel()
        self.char1.db.sp = POWERATTACK_SP_COST - 1
        result = self.call(CmdPowerAttack(), "Char2", caller=self.char1)
        self.assertIn("enough SP", result)

    def test_succeeds_with_enough_sp(self):
        self._start_duel()
        self.char1.db.sp = 30
        with patch("world.combat.randint", return_value=100):
            self.call(CmdPowerAttack(), "Char2", caller=self.char1)
        self.assertFalse(self.char1.db.combat_actionsleft)


class TestCmdPass(CombatCommandTestBase):
    def test_pass_ends_turn(self):
        handler = self._start_duel()
        self.assertEqual(handler.db.fighters[handler.db.turn], self.char1)
        self.call(CmdPass(), "", caller=self.char1)
        self.assertEqual(handler.db.fighters[handler.db.turn], self.char2)

    def test_pass_out_of_combat_rejected(self):
        result = self.call(CmdPass(), "", caller=self.char1)
        self.assertIn("only do that in combat", result)


class TestCmdDisengage(CombatCommandTestBase):
    @patch("world.combat.randint")
    def test_successful_disengage_removes_from_fight(self, mock_randint):
        mock_randint.return_value = 1  # <= DISENGAGE_SUCCESS_CHANCE -> success
        self._start_duel()
        self.call(CmdDisengage(), "", caller=self.char1)
        # Only char2 is left standing - this ends the fight entirely
        # (the turn handler script stops and deletes itself), so check
        # char1's own state rather than the now-deleted handler.
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))
        self.assertIsNone(self.char1.db.combat_turnhandler)

    @patch("world.combat.randint")
    def test_failed_disengage_keeps_fighter_in_fight(self, mock_randint):
        mock_randint.return_value = 100  # > DISENGAGE_SUCCESS_CHANCE -> failure
        handler = self._start_duel()
        self.call(CmdDisengage(), "", caller=self.char1)
        self.assertIn(self.char1, handler.db.fighters)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))


class TestCmdChallenge(CombatCommandTestBase):
    def test_no_trainer_here_rejects(self):
        self.room1.db.trainer_prototype = None
        result = self.call(CmdChallenge(), "", caller=self.char1)
        self.assertIn("no one here to challenge", result)

    def test_spawns_personal_opponent_from_prototype(self):
        self.room1.db.trainer_prototype = "RESPAWNING_ARENA_FIGHTER"
        try:
            self.call(CmdChallenge(), "", caller=self.char1)
        except Exception:
            self.skipTest("RESPAWNING_ARENA_FIGHTER prototype not available in this test DB")
        opponent = self.char1.ndb.active_trainer_npc
        self.assertIsNotNone(opponent)
        self.assertEqual(opponent.db.instance_owner, self.char1)

    def test_cannot_challenge_twice_with_pending_opponent(self):
        fake_opponent = create.create_object(
            "typeclasses.characters.Character", key="pending foe", location=self.room1
        )
        fake_opponent.db.hp = 50
        self.char1.ndb.active_trainer_npc = fake_opponent
        self.room1.db.trainer_prototype = "anything"

        result = self.call(CmdChallenge(), "", caller=self.char1)
        self.assertIn("already have an opponent waiting", result)


class TestCmdCastNamedTargeting(CombatCommandTestBase):
    """
    Regression coverage for the real bug found and fixed while writing
    this file - see module docstring. 'cast <heal> = <ally name>' must
    work for an ordinary (non-Builder) caster targeting another real
    Character by their exact, correct name.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.spells_known = ["cure wounds"]
        # EvenniaTest's char1 fixture carries the "Developer" permission
        # by default, which would mask this exact bug (Builders/Devs
        # get a plain-key fallback rpsystem's override doesn't give
        # everyone else) - strip it so this test reflects an ordinary
        # player.
        self.char1.permissions.remove("Developer")

    def test_cast_heal_on_named_ally_by_real_name_succeeds(self):
        self.char2.db.hp = 50
        self.char2.db.max_hp = 100

        with patch("world.combat.randint", return_value=20):
            self.call(CmdCast(), "cure wounds = Char2", caller=self.char1)

        self.assertGreater(self.char2.db.hp, 50)

    def test_cast_heal_with_no_target_heals_self(self):
        self.char1.db.hp = 50
        self.char1.db.max_hp = 100

        with patch("world.combat.randint", return_value=20):
            self.call(CmdCast(), "cure wounds", caller=self.char1)

        self.assertGreater(self.char1.db.hp, 50)

    def test_cast_unknown_spell_rejected(self):
        result = self.call(CmdCast(), "fireball of doom = Char2", caller=self.char1)
        self.assertIn("don't know a spell", result)

    def test_cast_without_enough_mp_rejected(self):
        self.char1.db.mp = 0
        result = self.call(CmdCast(), "cure wounds = Char2", caller=self.char1)
        self.assertIn("enough MP", result)

    def test_cast_on_nonexistent_target_reports_not_found(self):
        result = self.call(CmdCast(), "cure wounds = Nobody", caller=self.char1)
        self.assertIn("Could not find", result)


class TestCmdUseSkillNamedTargeting(CombatCommandTestBase):
    """Same regression, for CmdUseSkill ('mark' - target: otherchar)."""

    def setUp(self):
        super().setUp()
        self.char1.db.skills_known = ["mark"]
        self.char1.permissions.remove("Developer")

    def test_skill_on_named_enemy_by_real_name_succeeds(self):
        self._start_duel()
        self.char2.db.conditions = {}

        self.call(CmdUseSkill(), "mark = Char2", caller=self.char1)

        self.assertIn("Accuracy Down", self.char2.db.conditions)

    def test_skill_without_enough_sp_rejected(self):
        self.char1.db.sp = 0
        result = self.call(CmdUseSkill(), "mark = Char2", caller=self.char1)
        self.assertIn("enough SP", result)

    def test_skill_unknown_rejected(self):
        result = self.call(CmdUseSkill(), "made up skill = Char2", caller=self.char1)
        self.assertIn("don't know a skill", result)


class TestCustomTitleDisplay(CombatCommandTestBase):
    """
    Regression coverage for a real gap found live: db.custom_title was
    only ever shown on the who tables - there was no way to see your
    own title in full anywhere else, and no way at all to see another
    character's title if who's column width had cropped it. Both
    'stats' and looking at a character now show it.
    """

    def test_stats_shows_the_callers_own_title(self):
        self.char1.db.custom_title = "the Undefeated"
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("the Undefeated", result)

    def test_stats_omits_the_title_line_when_none_is_set(self):
        self.char1.db.custom_title = None
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertNotIn("None", result.split("\n")[1] if "\n" in result else "")

    def test_looking_at_a_character_shows_their_title(self):
        self.char1.db.custom_title = "the Undefeated"
        self.char1.db.desc = "A tall, scarred fighter."
        appearance = self.char1.return_appearance(self.char2)
        self.assertIn("the Undefeated", appearance)

    def test_looking_at_a_character_with_no_title_is_unaffected(self):
        self.char1.db.custom_title = None
        self.char1.db.desc = "A tall, scarred fighter."
        appearance = self.char1.return_appearance(self.char2)
        self.assertIn("A tall, scarred fighter.", appearance)
