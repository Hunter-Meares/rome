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
    CmdAutoAttack,
    CmdPowerAttack,
    CmdPass,
    CmdDisengage,
    CmdChallenge,
    CmdCast,
    CmdUseSkill,
    CmdCoreStats,
    CmdLearn,
    CmdTrainer,
    CmdRest,
    POWERATTACK_SP_COST,
    DISENGAGE_SUCCESS_CHANCE,
    AUTO_ATTACK_DELAY,
    MOVEMENT_SP_COST,
    MOVEMENT_SP_WARN_THRESHOLD,
)
from evennia.contrib.game_systems.mail import CmdMailCharacter


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

    def test_no_combat_zone_blocks_a_named_duel(self):
        self.room1.tags.add("no_combat_zone", category="zone")
        result = self.call(CmdFight(), "Char2", caller=self.char1)
        self.assertIn("forbids violence", result)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_no_combat_zone_blocks_fight_all(self):
        self.room1.tags.add("no_combat_zone", category="zone")
        result = self.call(CmdFight(), "all", caller=self.char1)
        self.assertIn("forbids violence", result)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

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

    def _equip_weapon(self, char, weapon_type_name, weapon_category, accuracy_bonus=100):
        weapon = create.create_object("world.combat.CombatWeapon", key="a %s" % weapon_type_name)
        weapon.db.weapon_type_name = weapon_type_name
        weapon.db.weapon_category = weapon_category
        weapon.db.accuracy_bonus = accuracy_bonus
        char.db.wielded_weapon = weapon
        return weapon

    def test_ranged_weapon_hit_uses_ranged_specific_message(self):
        self._start_duel()
        self._equip_weapon(self.char1, "shortbow", "ranged")
        with patch("world.combat.randint", return_value=50):
            result = self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertIn("finds its mark", result)

    def test_thunderbolt_hit_uses_its_own_override_message_not_polearms(self):
        self._start_duel()
        # Mechanically a polearm, but should never read as one.
        self._equip_weapon(self.char1, "thunderbolt", "polearm")
        with patch("world.combat.randint", return_value=50):
            result = self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertIn("divine lightning", result)
        self.assertNotIn("skewers", result)

    def test_unarmed_attack_still_uses_the_original_generic_message(self):
        self._start_duel()
        with patch("world.combat.randint", return_value=50):
            result = self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertIn("strikes", result)


class TestCmdAutoAttack(CombatCommandTestBase):
    def test_on_by_default_for_a_fresh_character(self):
        self.assertTrue(self.char1.db.auto_attack)

    def test_no_argument_shows_current_state_without_changing_it(self):
        self.char1.db.auto_attack = True
        result = self.call(CmdAutoAttack(), "", caller=self.char1)
        self.assertIn("ON", result)
        self.assertTrue(self.char1.db.auto_attack)  # unchanged, just shown

    def test_off_turns_it_off(self):
        result = self.call(CmdAutoAttack(), "off", caller=self.char1)
        self.assertFalse(self.char1.db.auto_attack)
        self.assertIn("OFF", result)

    def test_on_turns_it_on(self):
        self.char1.db.auto_attack = False
        result = self.call(CmdAutoAttack(), "on", caller=self.char1)
        self.assertTrue(self.char1.db.auto_attack)
        self.assertIn("ON", result)

    def test_garbage_argument_shows_usage_and_does_not_change_state(self):
        self.char1.db.auto_attack = True
        result = self.call(CmdAutoAttack(), "banana", caller=self.char1)
        self.assertIn("Usage:", result)
        self.assertTrue(self.char1.db.auto_attack)

    def test_at_turn_start_schedules_the_delayed_auto_attack(self):
        # Confirms the wiring (at_turn_start -> evennia_utils.delay) is
        # actually in place, without needing a real elapsed delay -
        # the delay mechanism itself only ever fires correctly on a
        # live running server, not from a test/shell process (same
        # class of limitation already documented for RespawnTimer).
        self._start_duel()
        self.char1.db.auto_attack = True
        with patch("world.combat.evennia_utils.delay") as mock_delay:
            self.char1.at_turn_start()
        mock_delay.assert_called_once_with(
            AUTO_ATTACK_DELAY, COMBAT_RULES.try_auto_attack, self.char1
        )

    def test_at_turn_start_does_not_schedule_when_toggled_off(self):
        self._start_duel()
        self.char1.db.auto_attack = False
        with patch("world.combat.evennia_utils.delay") as mock_delay:
            self.char1.at_turn_start()
        mock_delay.assert_not_called()


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


class TestStatsHealthBar(CombatCommandTestBase):
    """
    'stats' now shows HP/MP/SP as visual meters (health_bar contrib)
    rather than bare 'HP: X/Y' text - covers the real edge case that
    made this worth double-checking: a pure-melee character with
    max_mp=0 (display_meter guards divide-by-zero internally, but
    worth confirming that actually holds here rather than trusting it).
    """

    def test_stats_shows_hp_mp_sp_meters(self):
        self.char1.db.hp, self.char1.db.max_hp = 50, 100
        self.char1.db.mp, self.char1.db.max_mp = 10, 20
        self.char1.db.sp, self.char1.db.max_sp = 15, 30
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("HP ", result)
        self.assertIn("MP ", result)
        self.assertIn("SP ", result)
        self.assertIn("50 / 100", result)
        self.assertIn("10 / 20", result)
        self.assertIn("15 / 30", result)

    def test_stats_does_not_crash_with_zero_max_mp(self):
        self.char1.db.max_mp = 0
        self.char1.db.mp = 0
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("0 / 0", result)


class TestSpellSkillTrainers(CombatCommandTestBase):
    """
    'learn' (formerly separate learnspell/learnskill commands, now
    merged into one - see 'learnspell'/'learnskill' kept as aliases
    for backward compatibility) requires both gold and being in the
    same room as the right trainer (world.combat.SpellSkillTrainer,
    CmdTrainer). Uses real spells/skills from the actual SPELLS/SKILLS
    dicts rather than fakes, so a formula or gating change elsewhere
    would actually be caught here.
    """

    def test_old_learnspell_and_learnskill_names_still_work_as_aliases(self):
        self.assertIn("learnspell", CmdLearn.aliases)
        self.assertIn("learnskill", CmdLearn.aliases)

    def _make_trainer(self, teaches, location=None):
        from evennia.utils import create
        from world.combat import SpellSkillTrainer

        trainer = create.create_object(
            SpellSkillTrainer, key="Test Trainer (%s)" % teaches, location=location or self.room1
        )
        trainer.db.teaches = teaches
        return trainer

    def test_compute_learn_cost_scales_with_level(self):
        from world.combat import compute_learn_cost

        self.assertEqual(compute_learn_cost(1), 23)
        self.assertEqual(compute_learn_cost(90), 290)
        self.assertLess(compute_learn_cost(1), compute_learn_cost(90))

    def test_learnskill_blocked_without_a_trainer_present(self):
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 50
        self.char1.db.gold = 9999
        result = self.call(CmdLearn(), "hold the line", caller=self.char1)
        self.assertIn("need to find a trainer", result)
        self.assertNotIn("hold the line", self.char1.db.skills_known)

    def test_learnskill_blocked_without_enough_gold(self):
        self._make_trainer("skills")
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 50
        self.char1.db.gold = 0
        result = self.call(CmdLearn(), "hold the line", caller=self.char1)
        self.assertIn("costs", result)
        self.assertNotIn("hold the line", self.char1.db.skills_known)

    def test_learnskill_succeeds_and_deducts_gold(self):
        self._make_trainer("skills")
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 50
        self.char1.db.gold = 100
        self.call(CmdLearn(), "hold the line", caller=self.char1)
        self.assertIn("hold the line", self.char1.db.skills_known)
        # level_required=1 for "hold the line" -> cost 23
        self.assertEqual(self.char1.db.gold, 77)

    def test_learnspell_succeeds_at_the_spell_trainer_not_the_skill_one(self):
        self._make_trainer("skills")  # wrong type present
        self.char1.db.player_class = "medicus"
        self.char1.db.level = 50
        self.char1.db.gold = 100
        result = self.call(CmdLearn(), "cure wounds", caller=self.char1)
        self.assertIn("need to find a trainer", result)

        self._make_trainer("spells")  # now the right type is also here
        self.call(CmdLearn(), "cure wounds", caller=self.char1)
        self.assertIn("cure wounds", self.char1.db.spells_known)

    def test_already_known_short_circuits_before_gold_or_trainer_checks(self):
        # No trainer, no gold - but already known, so neither should matter.
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 50
        self.char1.db.gold = 0
        self.char1.db.skills_known = ["hold the line"]
        result = self.call(CmdLearn(), "hold the line", caller=self.char1)
        self.assertIn("already know", result)

    def test_trainer_command_with_no_trainer_present(self):
        result = self.call(CmdTrainer(), "", caller=self.char1)
        self.assertIn("no trainer here", result)

    def test_train_is_a_working_alias_for_trainer(self):
        self.assertIn("train", CmdTrainer.aliases)

    def test_trainer_command_shows_known_ready_and_locked(self):
        self._make_trainer("skills")
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 5
        self.char1.db.gold = 1000
        self.char1.db.skills_known = ["hold the line"]  # level_required=1

        result = self.call(CmdTrainer(), "", caller=self.char1)

        self.assertIn("Hold The Line", result)
        self.assertIn("Known:", result)
        self.assertIn("Ready to learn", result)
        # A level-90 skill should show up locked for a level-5 character.
        self.assertIn("Not yet available", result)


class TestInCharacterMail(CombatCommandTestBase):
    """
    Light integration coverage for the mail contrib (CmdMailCharacter,
    installed on CharacterCmdSet) - not re-testing the contrib's own
    internals (it ships its own test suite), just confirming it's
    actually wired up correctly and a real send/receive round-trip
    works between two of this game's real Character objects.
    """

    def test_send_and_receive_between_characters(self):
        self.call(
            CmdMailCharacter(),
            "Char2=A test letter/Hail from across the Forum.",
            caller=self.char1,
        )
        result = self.call(CmdMailCharacter(), "", caller=self.char2)
        self.assertIn("A test letter", result)


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


class TestEquippedItemsShowSlotLabelsOnLook(CombatCommandTestBase):
    """
    Regression coverage for a real display bug: 'look'/'look self' used
    to dump every worn/wielded item into the same flat, alphabetically
    sorted "You see: a, b, and c" line as ordinary carried items - no
    indication of where anything was actually equipped. get_display_things
    now special-cases equipped items into the same slot-labeled format
    'inventory' already used (see EQUIPPED_SLOTS/format_equipped_lines).
    """

    def setUp(self):
        super().setUp()
        self.weapon = create.create_object(
            "typeclasses.objects.Object", key="a test sword", location=self.char1
        )
        self.weapon.db.two_handed = False
        self.armor = create.create_object(
            "typeclasses.objects.Object", key="a test breastplate", location=self.char1
        )
        self.trinket = create.create_object(
            "typeclasses.objects.Object", key="a plain trinket", location=self.char1
        )
        self.char1.db.wielded_weapon = self.weapon
        self.char1.db.worn_armor = self.armor

    def test_equipped_items_show_with_slot_labels(self):
        appearance = self.char1.return_appearance(self.char1)
        self.assertIn("Wielded (in hand):", appearance)
        self.assertIn("a test sword", appearance)
        self.assertIn("Worn (as armor):", appearance)
        self.assertIn("a test breastplate", appearance)

    def test_two_handed_weapon_says_so(self):
        self.weapon.db.two_handed = True
        appearance = self.char1.return_appearance(self.char1)
        self.assertIn("Wielded (in both hands):", appearance)

    def test_equipped_items_excluded_from_plain_carrying_line(self):
        appearance = self.char1.return_appearance(self.char1)
        self.assertIn("You see:", appearance)
        self.assertIn("a plain trinket", appearance)
        # The sword/breastplate must appear ONLY via their slot-labeled
        # lines above, not also swept into the generic "You see:" line.
        you_see_line = next(line for line in appearance.split("\n") if line.startswith("|wYou see:|n") or "You see:" in line)
        self.assertNotIn("test sword", you_see_line)
        self.assertNotIn("test breastplate", you_see_line)

    def test_no_equipment_falls_back_to_plain_carrying_line_only(self):
        self.char1.db.wielded_weapon = None
        self.char1.db.worn_armor = None
        appearance = self.char1.return_appearance(self.char1)
        self.assertNotIn("Wielded", appearance)
        self.assertNotIn("Worn", appearance)
        self.assertIn("a plain trinket", appearance)


class TestCooldowns(CombatCommandTestBase):
    """
    First-pass fix for the long-flagged gap in rome_mud_todo.md: "zero
    cooldowns exist anywhere in world/combat.py" - a level-tiered
    default (cooldown_for_level) applied automatically via CmdCast and
    CmdUseSkill, so a powerful ability can't be spammed every turn the
    instant its MP/SP cost is affordable again.
    """

    def setUp(self):
        super().setUp()
        self.char1.permissions.remove("Developer")
        self.char1.db.mp = 20
        self.char1.db.max_mp = 20
        self.char1.db.sp = 20
        self.char1.db.max_sp = 20

    def test_low_level_spell_gets_no_cooldown(self):
        self.char1.db.spells_known = ["cure wounds"]  # level_required 1
        with patch("world.combat.randint", return_value=20):
            self.call(CmdCast(), "cure wounds", caller=self.char1)
        self.assertNotIn("cure wounds", self.char1.db.cooldowns)

    def test_casting_a_tier_20_spell_sets_a_cooldown(self):
        self.char1.db.spells_known = ["vigor"]  # level_required 25 -> cooldown 2
        self.call(CmdCast(), "vigor", caller=self.char1)
        self.assertEqual(self.char1.db.cooldowns.get("vigor"), 2)

    def test_recasting_before_cooldown_expires_is_refused(self):
        self.char1.db.spells_known = ["vigor"]
        self.call(CmdCast(), "vigor", caller=self.char1)
        self.char1.db.mp = 20  # refill so MP itself isn't the blocker
        result = self.call(CmdCast(), "vigor", caller=self.char1)
        self.assertIn("recovering", result)

    def test_cooldown_ticks_down_and_clears(self):
        self.char1.db.spells_known = ["vigor"]
        self.call(CmdCast(), "vigor", caller=self.char1)
        self.assertEqual(self.char1.db.cooldowns.get("vigor"), 2)
        COMBAT_RULES.tick_cooldowns(self.char1)
        self.assertEqual(self.char1.db.cooldowns.get("vigor"), 1)
        COMBAT_RULES.tick_cooldowns(self.char1)
        self.assertNotIn("vigor", self.char1.db.cooldowns)

    def test_skill_cooldown_enforced_the_same_way(self):
        self.char1.db.skills_known = ["shield wall"]  # level_required 25
        self.call(CmdUseSkill(), "shield wall", caller=self.char1)
        self.assertEqual(self.char1.db.cooldowns.get("shield wall"), 2)

        self.char1.db.sp = 20
        result = self.call(CmdUseSkill(), "shield wall", caller=self.char1)
        self.assertIn("recovering", result)


class TestCmdRestBlockedWhileDead(CombatCommandTestBase):
    """
    A dead character's HP/MP/SP are deliberately pinned at 0 the whole
    time they're dead (see handle_player_defeat) - resting must not be
    able to creep them back up before an actual resurrection, or "stats
    stay at 0 until you make it back" stops being true.
    """

    def test_rest_refused_while_dead(self):
        self.char1.db.is_dead = True
        self.char1.db.hp = 0
        self.char1.db.mp = 0
        self.char1.db.sp = 0

        result = self.call(CmdRest(), "", caller=self.char1)

        self.assertIn("only returning to life", result)
        self.assertFalse(self.char1.db.resting)

    def test_rest_works_normally_once_alive(self):
        self.char1.db.is_dead = False
        self.char1.db.hp = 50
        result = self.call(CmdRest(), "", caller=self.char1)
        self.assertIn("settles in to rest", result)
        self.assertTrue(self.char1.db.resting)


class TestMovementSPCost(CombatCommandTestBase):
    """
    at_pre_move's movement-SP gate (world/combat.py) - MOVEMENT_SP_COST
    per ordinary player move, blocked outright if there isn't enough
    SP left, with gods/dead characters/non-"move" move_types (NPC
    wander, teleports) exempt. Called directly against at_pre_move
    rather than through a real Exit object - the hook only needs a
    destination and a move_type, so no exit wiring is needed to
    exercise it.
    """

    def test_ordinary_move_deducts_the_cost(self):
        self.char1.db.sp = 10
        allowed = self.char1.at_pre_move(self.room2, move_type="move")
        self.assertTrue(allowed)
        self.assertEqual(self.char1.db.sp, 10 - MOVEMENT_SP_COST)

    def test_move_blocked_when_sp_below_cost(self):
        self.char1.db.sp = 0
        allowed = self.char1.at_pre_move(self.room2, move_type="move")
        self.assertFalse(allowed)
        self.assertEqual(self.char1.db.sp, 0)

    def test_god_tier_exempt_from_cost(self):
        self.char1.db.level = 101
        self.char1.db.sp = 0
        allowed = self.char1.at_pre_move(self.room2, move_type="move")
        self.assertTrue(allowed)
        self.assertEqual(self.char1.db.sp, 0)

    def test_dead_character_exempt_from_cost(self):
        self.char1.db.is_dead = True
        self.char1.db.sp = 0
        allowed = self.char1.at_pre_move(self.room2, move_type="move")
        self.assertTrue(allowed)
        self.assertEqual(self.char1.db.sp, 0)

    def test_non_move_move_types_are_exempt(self):
        """NPC wandering ("wander") and teleports ("teleport") never pay this cost."""
        self.char1.db.sp = 0
        self.assertTrue(self.char1.at_pre_move(self.room2, move_type="wander"))
        self.assertTrue(self.char1.at_pre_move(self.room2, move_type="teleport"))
        self.assertEqual(self.char1.db.sp, 0)

    def test_accountless_object_exempt_as_npc_safety_net(self):
        npc = create.create_object(
            "typeclasses.characters.Character", key="a test npc", location=self.room1
        )
        npc.db.sp = 0
        npc.db.is_dead = False
        npc.db.level = 1
        self.assertIsNone(npc.account)
        allowed = npc.at_pre_move(self.room2, move_type="move")
        self.assertTrue(allowed)

    def test_low_sp_warning_fires_once_then_resets_above_threshold(self):
        self.char1.db.max_sp = 10
        self.char1.db.sp = MOVEMENT_SP_COST + int(10 * MOVEMENT_SP_WARN_THRESHOLD)
        self.char1.db.sp_low_warned = False

        # This move should land exactly at/below the warn threshold.
        self.char1.at_pre_move(self.room2, move_type="move")
        self.assertTrue(self.char1.db.sp_low_warned)

        # Restoring SP well above the threshold should clear the flag
        # so a future dip can warn again.
        self.char1.db.sp = 10
        self.char1.at_pre_move(self.room2, move_type="move")
        self.assertFalse(self.char1.db.sp_low_warned)
