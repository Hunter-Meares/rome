"""
Tests for the combat engine (world/combat.py): hit/defense/damage math,
apply_damage's special-case conditions, XP/gold splitting on defeat,
the turn handler's fighter-pruning and side-based victory check, and
the resting regen cycle.

Uses EvenniaTest for real Character objects with real stats, per the
priority list in CLAUDE.md's Testing section. Where a formula has a
deterministic component (get_defense has NO random roll at all - only
get_attack's base d100 is random), the RNG is mocked via
unittest.mock.patch so the assertion is exact rather than statistical.
The one genuinely statistical test (the documented ~90%+ hit-chance
calibration target) is deliberately left un-mocked, but constructed so
its analytically-true probability is 100% - see that test's docstring.
"""

import unittest
from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest

from world.combat import (
    COMBAT_RULES,
    CombatTurnHandler,
    ACCURACY_STAT_MULTIPLIER,
    NONPROFICIENT_ACCURACY_PENALTY,
    NONPROFICIENT_DAMAGE_MULTIPLIER,
    RIPOSTE_COUNTER_DAMAGE,
    CURSED_DAMAGE_MULTIPLIER,
    AMBUSH_DAMAGE_BONUS,
    MARKED_FOR_DEATH_DAMAGE_BONUS,
    GOLD_PER_XP_DIVISOR,
    get_weapon_attack_messages,
    WEAPON_CATEGORY_MESSAGES,
    WEAPON_TYPE_MESSAGE_OVERRIDES,
    DEFAULT_WEAPON_MESSAGES,
)


class TestGetWeaponAttackMessages(unittest.TestCase):
    """
    Pure logic, no DB needed - get_weapon_attack_messages just picks
    which template dict resolve_attack should use. Regression coverage
    for the fix that gave every weapon category (and a couple of
    one-off weapons like Jupiter's thunderbolt) its own combat-log
    flavor instead of one single generic "strikes/misses/bounces
    harmlessly off" sentence for every weapon in the game.
    """

    def test_known_category_returns_its_own_templates(self):
        messages = get_weapon_attack_messages("shortbow", "ranged")
        self.assertEqual(messages, WEAPON_CATEGORY_MESSAGES["ranged"])

    def test_weapon_type_override_wins_over_its_own_category(self):
        # Thunderbolt is mechanically a polearm, but it should never
        # read as one - the override table must win.
        messages = get_weapon_attack_messages("thunderbolt", "polearm")
        self.assertEqual(messages, WEAPON_TYPE_MESSAGE_OVERRIDES["thunderbolt"])
        self.assertNotEqual(messages, WEAPON_CATEGORY_MESSAGES["polearm"])

    def test_unarmed_falls_back_to_default_generic_messages(self):
        messages = get_weapon_attack_messages("attack", None)
        self.assertEqual(messages, DEFAULT_WEAPON_MESSAGES)

    def test_unknown_category_falls_back_to_default_generic_messages(self):
        messages = get_weapon_attack_messages("some future weapon", "some future category")
        self.assertEqual(messages, DEFAULT_WEAPON_MESSAGES)

    def test_every_message_set_has_all_three_keys_and_is_formattable(self):
        all_sets = list(WEAPON_CATEGORY_MESSAGES.values()) + list(
            WEAPON_TYPE_MESSAGE_OVERRIDES.values()
        ) + [DEFAULT_WEAPON_MESSAGES]
        for messages in all_sets:
            self.assertEqual(set(messages), {"hit", "miss", "bounce"})
            # hit takes 6 args (attacker, weapon, defender, damage, defender, hp phrase);
            # miss/bounce take 3 (attacker, weapon, defender). Would raise on a typo'd
            # placeholder count/type - real regression risk with this many hand-written strings.
            messages["hit"] % ("A", "sword", "B", 5, "B", "looks wounded")
            messages["miss"] % ("A", "sword", "B")
            messages["bounce"] % ("A", "sword", "B")


class CombatTestBase(EvenniaTest):
    """Common setup: char1/char2 as plain, unequipped combatants."""

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


class TestOrphanedCharacterTicking(CombatTestBase):
    """
    Regression coverage for a real bug found live: characters that end
    up with location=None (confirmed instances: an account link
    severed with the character left behind - see rome_mud_todo.md)
    crashed every 30 seconds forever via the out-of-combat ticker,
    since condition_tickdown/apply_turn_conditions/add_condition all
    called character.location.msg_contents() with no null check.
    """

    def test_at_update_does_not_crash_with_no_location(self):
        self.char1.location = None
        self.char1.db.conditions = {"Regeneration": [3, self.char1]}
        self.char1.at_update()  # should not raise

    def test_condition_tickdown_does_not_crash_with_no_location(self):
        self.char1.location = None
        self.char1.db.conditions = {"Haste": [0, self.char1]}
        COMBAT_RULES.condition_tickdown(self.char1, self.char1)
        self.assertNotIn("Haste", self.char1.db.conditions)

    def test_apply_turn_conditions_does_not_crash_with_no_location(self):
        self.char1.location = None
        self.char1.db.conditions = {"Regeneration": [True, self.char1]}
        self.char1.db.hp = 50
        self.char1.db.max_hp = 100
        COMBAT_RULES.apply_turn_conditions(self.char1)
        self.assertGreater(self.char1.db.hp, 50)

    def test_add_condition_does_not_crash_with_no_location(self):
        self.char1.location = None
        COMBAT_RULES.add_condition(self.char1, self.char1, "Haste", 3)
        self.assertIn("Haste", self.char1.db.conditions)


class TestPoisonDeathAttributesThePoisoner(CombatTestBase):
    """
    Real gap found live: a kill delivered by Poisoned ticking down at
    the start of a fighter's own turn called at_defeat(character) with
    no attacker at all, silently skipping anything gated on one - the
    colosseum escape-on-victory check ("if attacker and ...") included,
    and damage_log never crediting the poisoner's share either. The
    condition's own stored turnchar (see add_condition) is exactly who
    inflicted it, so there's no need to leave attacker unset.
    """

    def test_lethal_poison_tick_passes_the_poisoner_as_attacker(self):
        self.char1.db.hp = 3
        self.char1.db.max_hp = 100
        self.char1.db.conditions = {"Poisoned": [4, self.char2]}
        self.char1.db.damage_log = {}

        with patch("world.combat.randint", return_value=50):
            with patch.object(COMBAT_RULES, "at_defeat") as mock_at_defeat:
                COMBAT_RULES.apply_turn_conditions(self.char1)

        mock_at_defeat.assert_called_once_with(self.char1, attacker=self.char2)

    def test_lethal_poison_tick_credits_the_poisoner_in_damage_log(self):
        self.char1.db.hp = 50
        self.char1.db.max_hp = 100
        self.char1.db.conditions = {"Poisoned": [4, self.char2]}
        self.char1.db.damage_log = {}

        with patch("world.combat.randint", return_value=5):
            COMBAT_RULES.apply_turn_conditions(self.char1)

        self.assertIn(self.char2, self.char1.db.damage_log)
        self.assertGreater(self.char1.db.damage_log[self.char2], 0)


class TestGetDefense(CombatTestBase):
    """get_defense has zero random component - fully deterministic."""

    def test_baseline_defense_is_50(self):
        self.assertEqual(COMBAT_RULES.get_defense(self.char1, self.char2), 50)

    def test_agilitas_shifts_defense_one_for_one(self):
        self.char2.db.agilitas = 16
        self.assertEqual(COMBAT_RULES.get_defense(self.char1, self.char2), 56)

    def test_armor_defense_modifier_applies(self):
        armor = self._make_armor(defense_modifier=-6)
        self.char2.db.worn_armor = armor
        self.assertEqual(COMBAT_RULES.get_defense(self.char1, self.char2), 44)

    def test_defense_up_and_down_conditions(self):
        self.char2.db.conditions = {"Defense Up": [3, self.char1]}
        self.assertEqual(COMBAT_RULES.get_defense(self.char1, self.char2), 65)
        self.char2.db.conditions = {"Defense Down": [3, self.char1]}
        self.assertEqual(COMBAT_RULES.get_defense(self.char1, self.char2), 35)

    def _make_armor(self, defense_modifier=0, damage_reduction=0):
        from evennia.utils import create
        from world.combat import CombatArmor

        armor = create.create_object(CombatArmor, key="test armor")
        armor.db.defense_modifier = defense_modifier
        armor.db.damage_reduction = damage_reduction
        return armor


class TestGetAttack(CombatTestBase):
    """get_attack's only random component is the base d100 roll - mocked here for exact assertions."""

    @patch("world.combat.randint")
    def test_agilitas_bonus_uses_documented_multiplier(self, mock_randint):
        mock_randint.return_value = 50  # the base "roll"
        self.char1.db.agilitas = 16  # +6 over baseline
        self.char1.db.unarmed_accuracy = 0  # isolate the stat term
        expected = 50 + (16 - 10) * ACCURACY_STAT_MULTIPLIER
        self.assertEqual(COMBAT_RULES.get_attack(self.char1, self.char2), expected)

    @patch("world.combat.randint")
    def test_unarmed_accuracy_added_when_no_weapon(self, mock_randint):
        mock_randint.return_value = 1
        self.char1.db.unarmed_accuracy = 30
        self.assertEqual(COMBAT_RULES.get_attack(self.char1, self.char2), 31)

    @patch("world.combat.randint")
    def test_nonproficient_weapon_accuracy_penalty(self, mock_randint):
        mock_randint.return_value = 1
        weapon = self._make_weapon(accuracy_bonus=20, weapon_category="heavy_weapon")
        self.char1.db.wielded_weapon = weapon
        self.char1.db.player_class = "augur"  # not proficient with heavy_weapon
        expected = 1 + 20 + NONPROFICIENT_ACCURACY_PENALTY
        self.assertEqual(COMBAT_RULES.get_attack(self.char1, self.char2), expected)

    @patch("world.combat.randint")
    def test_proficient_weapon_no_penalty(self, mock_randint):
        mock_randint.return_value = 1
        weapon = self._make_weapon(accuracy_bonus=20, weapon_category="light_blade")
        self.char1.db.wielded_weapon = weapon
        self.char1.db.player_class = "speculator"  # proficient with light_blade
        self.assertEqual(COMBAT_RULES.get_attack(self.char1, self.char2), 21)

    @patch("world.combat.randint")
    def test_defender_invisible_penalty_applies_to_attacker_roll(self, mock_randint):
        mock_randint.return_value = 50
        self.char1.db.unarmed_accuracy = 0
        self.char2.db.conditions = {"Invisible": [3, self.char1]}
        self.assertEqual(COMBAT_RULES.get_attack(self.char1, self.char2), 50 - 40)

    def _make_weapon(self, accuracy_bonus=0, weapon_category="light_blade", damage_range=(5, 10)):
        from evennia.utils import create
        from world.combat import CombatWeapon

        weapon = create.create_object(CombatWeapon, key="test weapon")
        weapon.db.accuracy_bonus = accuracy_bonus
        weapon.db.weapon_category = weapon_category
        weapon.db.damage_range = damage_range
        weapon.db.weapon_type_name = "test weapon"
        return weapon


class TestGetDamage(CombatTestBase):
    @patch("world.combat.randint")
    def test_ranged_and_light_blade_scale_with_agilitas_not_virtus(self, mock_randint):
        # First randint call is the weapon's damage roll; make it a no-op
        # by returning the same value regardless of range args.
        mock_randint.return_value = 10
        self.char1.db.virtus = 20  # should NOT matter for a ranged weapon
        self.char1.db.agilitas = 16  # should matter
        weapon = self._make_weapon(weapon_category="ranged", damage_range=(10, 10))
        self.char1.db.wielded_weapon = weapon
        expected = 10 + (16 - 10) // 2
        self.assertEqual(COMBAT_RULES.get_damage(self.char1, self.char2), expected)

    @patch("world.combat.randint")
    def test_heavy_weapon_scales_with_virtus_not_agilitas(self, mock_randint):
        mock_randint.return_value = 10
        self.char1.db.virtus = 16
        self.char1.db.agilitas = 20  # should NOT matter for a heavy blade
        weapon = self._make_weapon(weapon_category="heavy_blade", damage_range=(10, 10))
        self.char1.db.wielded_weapon = weapon
        expected = 10 + (16 - 10) // 2
        self.assertEqual(COMBAT_RULES.get_damage(self.char1, self.char2), expected)

    @patch("world.combat.randint")
    def test_unarmed_uses_virtus(self, mock_randint):
        mock_randint.return_value = 10
        self.char1.db.virtus = 16
        self.char1.db.unarmed_damage_range = (10, 10)
        expected = 10 + (16 - 10) // 2
        self.assertEqual(COMBAT_RULES.get_damage(self.char1, self.char2), expected)

    @patch("world.combat.randint")
    def test_armor_damage_reduction_and_vigor_both_apply(self, mock_randint):
        mock_randint.return_value = 20
        self.char1.db.unarmed_damage_range = (20, 20)
        armor = self._make_armor(damage_reduction=5)
        self.char2.db.worn_armor = armor
        self.char2.db.vigor = 16  # (16-10)//3 = 2 extra reduction
        expected = 20 - 5 - 2
        self.assertEqual(COMBAT_RULES.get_damage(self.char1, self.char2), expected)

    @patch("world.combat.randint")
    def test_nonproficient_weapon_damage_penalty(self, mock_randint):
        mock_randint.return_value = 20
        weapon = self._make_weapon(weapon_category="heavy_weapon", damage_range=(20, 20))
        self.char1.db.wielded_weapon = weapon
        self.char1.db.player_class = "augur"
        expected = int(20 * NONPROFICIENT_DAMAGE_MULTIPLIER)
        self.assertEqual(COMBAT_RULES.get_damage(self.char1, self.char2), expected)

    @patch("world.combat.randint")
    def test_cursed_multiplies_damage_on_defender(self, mock_randint):
        mock_randint.return_value = 10
        self.char1.db.unarmed_damage_range = (10, 10)
        self.char2.db.conditions = {"Cursed": [3, self.char1]}
        self.assertEqual(
            COMBAT_RULES.get_damage(self.char1, self.char2), int(10 * CURSED_DAMAGE_MULTIPLIER)
        )

    @patch("world.combat.randint")
    def test_ambush_bonus_consumed_after_use(self, mock_randint):
        mock_randint.return_value = 10
        self.char1.db.unarmed_damage_range = (10, 10)
        self.char1.db.conditions = {"Ambush": [True, self.char1]}
        first = COMBAT_RULES.get_damage(self.char1, self.char2)
        self.assertEqual(first, 10 + AMBUSH_DAMAGE_BONUS)
        self.assertNotIn("Ambush", self.char1.db.conditions)
        # A second hit shouldn't get the bonus again - it was consumed.
        second = COMBAT_RULES.get_damage(self.char1, self.char2)
        self.assertEqual(second, 10)

    @patch("world.combat.randint")
    def test_marked_for_death_bonus_consumed_after_use(self, mock_randint):
        mock_randint.return_value = 10
        self.char1.db.unarmed_damage_range = (10, 10)
        self.char2.db.conditions = {"Marked for Death": [True, self.char1]}
        first = COMBAT_RULES.get_damage(self.char1, self.char2)
        self.assertEqual(first, 10 + MARKED_FOR_DEATH_DAMAGE_BONUS)
        self.assertNotIn("Marked for Death", self.char2.db.conditions)

    @patch("world.combat.randint")
    def test_damage_never_goes_negative(self, mock_randint):
        mock_randint.return_value = 1
        self.char1.db.unarmed_damage_range = (1, 1)
        armor = self._make_armor(damage_reduction=999)
        self.char2.db.worn_armor = armor
        self.assertEqual(COMBAT_RULES.get_damage(self.char1, self.char2), 0)

    def _make_weapon(self, accuracy_bonus=0, weapon_category="light_blade", damage_range=(5, 10)):
        from evennia.utils import create
        from world.combat import CombatWeapon

        weapon = create.create_object(CombatWeapon, key="test weapon")
        weapon.db.accuracy_bonus = accuracy_bonus
        weapon.db.weapon_category = weapon_category
        weapon.db.damage_range = damage_range
        weapon.db.weapon_type_name = "test weapon"
        return weapon

    def _make_armor(self, defense_modifier=0, damage_reduction=0):
        from evennia.utils import create
        from world.combat import CombatArmor

        armor = create.create_object(CombatArmor, key="test armor")
        armor.db.defense_modifier = defense_modifier
        armor.db.damage_reduction = damage_reduction
        return armor


class TestResolveAttackDamageValue(CombatTestBase):
    """
    Regression coverage for a real bug: resolve_attack used to check
    `if not damage_value:` rather than `if damage_value is None:` (the
    is-None check its own attack_value/defense_value params correctly
    use a few lines above it). Since 0 is falsy, an explicitly passed
    damage_value=0 - a caller like itemfunc_attack (bombs/darts, which
    roll their own item-specific damage and pass it straight through)
    deliberately reporting "this hit connected but did zero damage" -
    got silently discarded and recomputed from get_damage() instead,
    which reads the ATTACKER'S EQUIPPED WEAPON - unrelated to whatever
    item was actually used. Currently unreachable in live gameplay
    (BOMB rolls 25-40, POISON_DART rolls 5-10 - neither range can ever
    produce 0), but a real latent bug for any future weak/dud item.
    """

    def test_explicit_zero_damage_value_is_respected_not_recomputed(self):
        # A high-damage weapon so an incorrect recompute via
        # get_damage() would obviously NOT land on 0 by chance.
        weapon = self._make_weapon(damage_range=(50, 50))
        self.char1.db.wielded_weapon = weapon
        self.char2.db.hp = 100
        self.char2.db.max_hp = 100

        COMBAT_RULES.resolve_attack(
            self.char1, self.char2, attack_value=999, defense_value=1, damage_value=0
        )

        self.assertEqual(self.char2.db.hp, 100)

    def test_omitted_damage_value_still_computes_fresh(self):
        # No damage_value passed at all (None, the real default) -
        # should still compute normally, unaffected by the fix.
        weapon = self._make_weapon(damage_range=(50, 50))
        self.char1.db.wielded_weapon = weapon
        self.char2.db.hp = 100
        self.char2.db.max_hp = 100

        COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=999, defense_value=1)

        self.assertLess(self.char2.db.hp, 100)

    def _make_weapon(self, accuracy_bonus=0, weapon_category="light_blade", damage_range=(5, 10)):
        from evennia.utils import create
        from world.combat import CombatWeapon

        weapon = create.create_object(CombatWeapon, key="test weapon")
        weapon.db.accuracy_bonus = accuracy_bonus
        weapon.db.weapon_category = weapon_category
        weapon.db.damage_range = damage_range
        weapon.db.weapon_type_name = "test weapon"
        return weapon


class TestHitChanceCalibration(CombatTestBase):
    """
    The one deliberately un-mocked, statistical test - covers priority
    item #3 from CLAUDE.md's testing section: the documented
    calibration target that a maximally-invested attacker (Agilitas
    16, the real race+class ceiling) should hit a weak-defense target
    (baseline Agilitas 10, no armor - defense_value 50) roughly 90%+
    of the time.

    Constructed so the true probability is analytically 100% (attack
    roll minimum of 1, plus a fixed bonus of 72, can never fall below
    the defense value of 50) - so this is not flaky, but it still
    exercises the real, un-mocked RNG path end to end, which the
    fully-mocked tests above deliberately don't.
    """

    def test_max_agilitas_attacker_vs_weak_defense_hits_at_least_90_percent(self):
        self.char1.db.agilitas = 16
        self.char1.db.unarmed_accuracy = 30
        self.char2.db.agilitas = 10
        self.char2.db.worn_armor = None

        trials = 300
        hits = 0
        for _ in range(trials):
            attack_value = COMBAT_RULES.get_attack(self.char1, self.char2)
            defense_value = COMBAT_RULES.get_defense(self.char1, self.char2)
            if attack_value >= defense_value:
                hits += 1

        self.assertGreaterEqual(hits / trials, 0.90)

    def test_stat_investment_meaningfully_swings_hit_chance(self):
        """
        Sanity check that the formula isn't a no-op: a baseline
        attacker (Agilitas 10, unarmed) against a maximally-defensive
        target (Agilitas 16 + heavy armor + Defense Up) should connect
        distinctly less often than the calibration-target matchup
        above - if this ever comes back ~equal, the stat math has
        been broken/short-circuited somewhere.
        """
        self.char1.db.agilitas = 10
        self.char1.db.unarmed_accuracy = 30
        self.char2.db.agilitas = 16
        self.char2.db.conditions = {"Defense Up": [99, self.char1]}

        trials = 300
        hits = 0
        for _ in range(trials):
            attack_value = COMBAT_RULES.get_attack(self.char1, self.char2)
            defense_value = COMBAT_RULES.get_defense(self.char1, self.char2)
            if attack_value >= defense_value:
                hits += 1

        # defense_value here is 50 + 6 + 15 = 71; attacker fixed bonus
        # is only 30, so hit requires roll >= 41 -> analytically 60%.
        self.assertLess(hits / trials, 0.80)
        self.assertGreater(hits / trials, 0.40)


class TestApplyDamage(CombatTestBase):
    def test_basic_damage_reduces_hp(self):
        self.char2.db.hp = 100
        COMBAT_RULES.apply_damage(self.char2, 30, attacker=self.char1)
        self.assertEqual(self.char2.db.hp, 70)

    def test_hp_floors_at_zero(self):
        self.char2.db.hp = 10
        COMBAT_RULES.apply_damage(self.char2, 30, attacker=self.char1)
        self.assertEqual(self.char2.db.hp, 0)

    def test_invincible_takes_no_damage(self):
        self.char2.db.hp = 100
        self.char2.db.invincible = True
        COMBAT_RULES.apply_damage(self.char2, 999, attacker=self.char1)
        self.assertEqual(self.char2.db.hp, 100)

    def test_death_ward_saves_at_1hp_and_is_consumed(self):
        self.char2.db.hp = 10
        self.char2.db.conditions = {"Death Ward": [True, self.char1]}
        COMBAT_RULES.apply_damage(self.char2, 999, attacker=self.char1)
        self.assertEqual(self.char2.db.hp, 1)
        self.assertNotIn("Death Ward", self.char2.db.conditions)
        # A second lethal hit with no ward left should actually kill.
        COMBAT_RULES.apply_damage(self.char2, 999, attacker=self.char1)
        self.assertEqual(self.char2.db.hp, 0)

    def test_shielded_blocks_the_hit_entirely_and_is_consumed(self):
        self.char2.db.hp = 100
        self.char2.db.conditions = {"Shielded": [True, self.char1]}
        COMBAT_RULES.apply_damage(self.char2, 50, attacker=self.char1)
        self.assertEqual(self.char2.db.hp, 100)
        self.assertNotIn("Shielded", self.char2.db.conditions)

    def test_damage_log_tracks_contribution_per_attacker(self):
        self.char2.db.hp = 100
        self.char2.db.damage_log = {}
        COMBAT_RULES.apply_damage(self.char2, 10, attacker=self.char1)
        COMBAT_RULES.apply_damage(self.char2, 5, attacker=self.char1)
        self.assertEqual(self.char2.db.damage_log[self.char1], 15)

    def test_zero_damage_not_logged(self):
        self.char2.db.hp = 100
        self.char2.db.damage_log = {}
        COMBAT_RULES.apply_damage(self.char2, 0, attacker=self.char1)
        self.assertEqual(self.char2.db.damage_log, {})

    def test_riposte_counters_the_attacker_immediately(self):
        self.char1.db.hp = 100
        self.char2.db.hp = 100
        self.char2.db.conditions = {"Riposte Ready": [True, self.char1]}
        COMBAT_RULES.apply_damage(self.char2, 10, attacker=self.char1)
        self.assertEqual(self.char2.db.hp, 90)
        self.assertEqual(self.char1.db.hp, 100 - RIPOSTE_COUNTER_DAMAGE)
        self.assertNotIn("Riposte Ready", self.char2.db.conditions)

    def test_riposte_does_not_fire_if_the_hit_was_lethal(self):
        """Docstring is explicit: only fires if defender is still standing."""
        self.char1.db.hp = 100
        self.char2.db.hp = 10
        self.char2.db.conditions = {"Riposte Ready": [True, self.char1]}
        COMBAT_RULES.apply_damage(self.char2, 50, attacker=self.char1)
        self.assertEqual(self.char2.db.hp, 0)
        self.assertEqual(self.char1.db.hp, 100)  # no counter-damage taken


class TestAtDefeatXpGoldSplit(CombatTestBase):
    """
    Covers the documented "never explicitly confirmed" scenario:
    XP/gold splitting proportionally by damage_log across multiple
    contributors when an NPC goes down.
    """

    def _make_dummy_npc(self, xp_reward=100):
        from evennia.utils import create
        from world.combat import AutoStatNPC

        npc = create.create_object(AutoStatNPC, key="dummy", location=self.room1)
        npc.db.hp = 0
        npc.db.xp_reward = xp_reward
        return npc

    def test_two_attackers_split_xp_and_gold_proportionally(self):
        # xp_reward deliberately kept below xp_for_level(1) (=20) so
        # award_xp's level-up bookkeeping (which SUBTRACTS the level
        # cost from xp once crossed) can't interfere with a direct
        # "how much was awarded" assertion - that's covered separately
        # in TestAwardXp. Damage split (80/100, 20/100) against a
        # reward of 15 divides evenly with no rounding ambiguity.
        npc = self._make_dummy_npc(xp_reward=15)
        npc.db.damage_log = {self.char1: 80, self.char2: 20}

        self.char1.db.xp = 0
        self.char2.db.xp = 0
        self.char1.db.gold = 0
        self.char2.db.gold = 0
        self.char1.db.level = 1
        self.char2.db.level = 1

        COMBAT_RULES.at_defeat(npc, attacker=self.char1)

        self.assertEqual(self.char1.db.xp, 12)
        self.assertEqual(self.char2.db.xp, 3)

        gold_pool = max(1, 15 // GOLD_PER_XP_DIVISOR)  # 5
        self.assertEqual(self.char1.db.gold, 4)
        self.assertEqual(self.char2.db.gold, 1)

    def test_solo_kill_with_no_damage_log_falls_back_to_full_reward(self):
        """
        at_defeat's documented fallback: if damage_log is somehow
        empty, the passed-in attacker gets the full xp_reward rather
        than nobody getting anything.
        """
        npc = self._make_dummy_npc(xp_reward=15)  # below xp_for_level(1)=20
        npc.db.damage_log = {}
        self.char1.db.xp = 0
        self.char1.db.gold = 0
        self.char1.db.level = 1

        COMBAT_RULES.at_defeat(npc, attacker=self.char1)

        self.assertEqual(self.char1.db.xp, 15)
        self.assertEqual(self.char1.db.gold, max(1, 15 // GOLD_PER_XP_DIVISOR))

    def test_stale_damage_log_entry_for_deleted_character_is_skipped(self):
        """
        apply_damage/at_defeat both guard 'if not contributor.pk' -
        a damage_log entry for someone since deleted shouldn't crash
        the whole reward split.
        """
        from evennia.utils import create

        ghost = create.create_object("typeclasses.characters.Character", key="ghost")
        npc = self._make_dummy_npc(xp_reward=15)  # below xp_for_level(1)=20
        npc.db.damage_log = {self.char1: 50, ghost: 50}
        self.char1.db.xp = 0
        self.char1.db.level = 1
        ghost.delete()

        # Should not raise (regression test for CLAUDE.md gotcha #2 -
        # a stale damage_log entry for a deleted character reloads as
        # literal None, not an object with pk=None).
        COMBAT_RULES.at_defeat(npc, attacker=self.char1)
        self.assertEqual(self.char1.db.xp, 8)  # round(15 * 50/100) == 8


class TestPvPXpReward(CombatTestBase):
    """
    Real request: defeating another real player should earn XP too,
    the same fair proportional-damage way an NPC kill already does.
    The critical safety property is the flip side of that: an
    ORDINARY monster killing a player (a normal, constant PvE
    occurrence, not PvP at all) must never try to "award XP" to that
    monster - the persistent account link is checked on the rewarded side
    to prevent that.
    """

    def test_defeating_a_real_player_awards_the_attacker_xp(self):
        self.char2.db.level = 1  # xp_for_level(1) = 20 -> pool = round(0.06*20) = 1
        self.char2.db.hp = 0
        self.char2.db.damage_log = {}
        self.char1.db.xp = 0

        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)

        self.assertEqual(self.char1.db.xp, 1)

    def test_higher_level_victim_is_worth_more_xp(self):
        # char1 kept at a high level of its own (with a matching high
        # xp_for_level threshold) so the awarded pool can't trigger a
        # level-up mid-test - award_xp's leveling loop actively
        # subtracts from db.xp as it advances, which would make a
        # direct "how much landed" assertion meaningless otherwise
        # (see TestAtDefeatXpGoldSplit's own comment on this exact trap).
        self.char1.db.level = 50
        self.char1.db.xp = 0
        self.char2.db.level = 50
        self.char2.db.hp = 0
        self.char2.db.damage_log = {}

        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)

        expected = max(1, round(0.06 * COMBAT_RULES.xp_for_level(50)))
        self.assertEqual(self.char1.db.xp, expected)
        self.assertGreater(expected, 1)

    def test_splits_proportionally_across_multiple_real_attackers(self):
        from evennia.utils import create

        ally = create.create_object("typeclasses.characters.Character", key="ally_pvp", location=self.room1)
        # A freshly create_object()'d Character has no account link at
        # all by default (unlike char1/char2, which EvenniaTest's own
        # fixture setup links for us) - reusing account2 here is only
        # to make getattr(ally, "account", None) truthy for this
        # check, not to exercise any real session/puppet behavior.
        ally.account = self.account2
        # High level on both recipients, matching the note above - the
        # awarded pool must stay under xp_for_level(their own level)
        # or award_xp's leveling loop eats into the exact number being
        # asserted on.
        ally.db.level = 50
        ally.db.xp = 0
        self.char1.db.level = 50
        self.char1.db.xp = 0
        self.char2.db.level = 50
        self.char2.db.hp = 0
        self.char2.db.damage_log = {self.char1: 80, ally: 20}

        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)

        pool = max(1, round(0.06 * COMBAT_RULES.xp_for_level(50)))
        self.assertEqual(self.char1.db.xp, int(round(pool * 0.8)))
        self.assertEqual(ally.db.xp, int(round(pool * 0.2)))

    def test_an_ordinary_monster_killing_a_player_awards_the_monster_nothing(self):
        """
        The critical safety case: a player dying to a regular NPC in
        normal PvE (constant, ordinary) must never try to give that
        NPC "XP" - the persistent account link on the attacker/contributor side is
        what prevents this from firing on every routine PvE death.
        """
        from evennia.utils import create
        from world.combat import AutoStatNPC

        monster = create.create_object(AutoStatNPC, key="a wolf", location=self.room1)
        monster.db.xp = 0
        monster.db.level = 1
        self.char1.db.level = 1
        self.char1.db.hp = 0
        self.char1.db.damage_log = {monster: 100}

        COMBAT_RULES.at_defeat(self.char1, attacker=monster)

        self.assertEqual(monster.db.xp, 0)

    def test_mixed_damage_log_only_counts_real_player_contributions(self):
        """
        A player's summoned ally/monster helper dealing some of the
        damage in a PvP fight shouldn't dilute or steal from the real
        player's share - only real, account-linked contributors count at all,
        both for the total used to compute shares and for who gets paid.
        """
        from evennia.utils import create
        from world.combat import AutoStatNPC

        familiar = create.create_object(AutoStatNPC, key="a familiar", location=self.room1)
        self.char1.db.level = 50  # keep the awarded pool under this level's own threshold
        self.char1.db.xp = 0
        self.char2.db.level = 50
        self.char2.db.hp = 0
        self.char2.db.damage_log = {self.char1: 50, familiar: 50}

        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)

        pool = max(1, round(0.06 * COMBAT_RULES.xp_for_level(50)))
        # char1 dealt half the RAW damage, but 100% of the PLAYER
        # damage - should get the full pool, not half of it.
        self.assertEqual(self.char1.db.xp, pool)

    def test_pvp_kill_awards_no_gold(self):
        self.char2.db.level = 50
        self.char2.db.hp = 0
        self.char2.db.damage_log = {}
        self.char1.db.gold = 0

        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)

        self.assertEqual(self.char1.db.gold, 0)

    def test_never_double_pays_when_defeated_has_a_real_xp_reward(self):
        # Defensive: an NPC somehow account-linked (shouldn't
        # normally happen) but a real xp_reward set must still only
        # ever pay out via the NPC branch, never both.
        self.char1.db.level = 50  # keep the award under this level's own threshold
        self.char1.db.xp = 0
        self.char2.db.xp_reward = 100
        self.char2.db.level = 50
        self.char2.db.hp = 0
        self.char2.db.damage_log = {}

        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)

        self.assertEqual(self.char1.db.xp, 100)  # the NPC-style reward, not the PvP one


class TestAwardXp(CombatTestBase):
    def test_level_up_restores_and_raises_max_pools(self):
        self.char1.db.level = 1
        self.char1.db.xp = 0
        self.char1.db.max_hp = 100
        self.char1.db.hp = 1
        needed = COMBAT_RULES.xp_for_level(1)

        COMBAT_RULES.award_xp(self.char1, needed)

        self.assertEqual(self.char1.db.level, 2)
        self.assertEqual(self.char1.db.hp, self.char1.db.max_hp)

    def test_multi_level_up_from_one_large_reward(self):
        self.char1.db.level = 1
        self.char1.db.xp = 0
        total_needed = COMBAT_RULES.xp_for_level(1) + COMBAT_RULES.xp_for_level(2)

        COMBAT_RULES.award_xp(self.char1, total_needed)

        self.assertEqual(self.char1.db.level, 3)

    def test_no_xp_awarded_at_max_level(self):
        from world.combat import MAX_LEVEL

        self.char1.db.level = MAX_LEVEL
        self.char1.db.xp = 0
        COMBAT_RULES.award_xp(self.char1, 99999)
        self.assertEqual(self.char1.db.xp, 0)


class TestNextTurnFighterPruning(CombatTestBase):
    """
    Direct regression coverage for gotcha #2: a deleted object's
    reference, reloaded from a persisted attribute, resolves to
    literal None - not an object with pk=None. next_turn() must
    prune a literal None entry without raising, and correctly end
    the fight once only one side remains.
    """

    def _make_handler_without_creation_hook(self):
        """
        Builds a CombatTurnHandler-like object with a controlled
        fighters list, bypassing at_script_creation's own room-sweep
        logic so the test can set up an exact, contrived scenario.
        """
        from evennia.utils import create

        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        return handler

    def test_none_entry_in_fighters_is_pruned_without_raising(self):
        handler = self._make_handler_without_creation_hook()
        self.char1.db.hp = 100
        self.char1.db.combat_side = "A"
        self.char2.db.hp = 100
        self.char2.db.combat_side = "B"

        handler.db.fighters = [self.char1, None, self.char2]
        handler.db.turn = 0

        try:
            handler.next_turn()
        except Exception as exc:  # pragma: no cover - failure path
            self.fail("next_turn() raised on a None fighter entry: %r" % exc)

        self.assertNotIn(None, handler.db.fighters)
        self.assertEqual(len(handler.db.fighters), 2)

    def test_pruning_down_to_one_side_ends_combat(self):
        handler = self._make_handler_without_creation_hook()
        self.char1.db.hp = 100
        self.char1.db.combat_side = "A"
        self.char2.db.hp = 0  # already defeated

        handler.db.fighters = [self.char1, self.char2]
        handler.db.turn = 0
        self.char2.db.combat_side = "B"

        handler.next_turn()

        # Combat should have ended (script stops and deletes itself).
        self.assertFalse(handler.pk)

    def test_last_fighter_standing_after_others_destroyed_wins(self):
        """
        The len(valid_fighters) == 1 branch - simulates @destroy
        (not a normal defeat) removing every other fighter mid-combat.
        """
        from evennia.utils import create

        handler = self._make_handler_without_creation_hook()
        self.char1.db.hp = 100
        self.char1.db.combat_side = "A"
        doomed = create.create_object("typeclasses.characters.Character", key="doomed", location=self.room1)
        handler.db.fighters = [self.char1, doomed]
        handler.db.turn = 0
        doomed.delete()

        handler.next_turn()
        self.assertFalse(handler.pk)


class TestNextTurnSkipsDefeatedFighters(CombatTestBase):
    """
    Regression coverage for a real bug found via a live 2v2 party
    fight test: a defeated (0 HP) fighter whose SIDE still has a
    living member (so the fight correctly doesn't end) was never
    removed from db.fighters and never skipped either - next_turn()'s
    round-robin advance handed them a real turn like anyone else.
    handle_player_defeat() does clean a defeated REAL PLAYER out of
    db.fighters, but only for characters with an account - anything
    else that ends up defeated-but-still-listed (confirmed live: a
    plain Character with no account, matching how a persistent
    RespawningNPC also has none) got stuck cycling through dead turns
    that CmdAttack silently no-ops on, relying purely on the
    (separately unverified) TURN_TIMEOUT to eventually force a
    disengage. Fixed at the single choke point instead - next_turn()
    itself now skips any 0-HP entry it lands on.
    """

    def _make_handler(self):
        from evennia.utils import create

        return create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)

    def test_defeated_ally_is_skipped_not_given_a_turn(self):
        from evennia.utils import create

        ally1 = create.create_object("typeclasses.characters.Character", key="ally1", location=self.room1)
        ally2 = create.create_object("typeclasses.characters.Character", key="ally2", location=self.room1)

        handler = self._make_handler()
        self.char1.db.hp, self.char1.db.combat_side = 100, "team_0"
        ally1.db.hp, ally1.db.combat_side = 0, "team_0"  # defeated, but team_0 still lives via char1
        self.char2.db.hp, self.char2.db.combat_side = 100, "team_1"
        ally2.db.hp, ally2.db.combat_side = 100, "team_1"

        # Turn order: char1 -> ally1 (defeated) -> char2 -> ally2.
        # char1 just acted, so the naive next entry would be ally1.
        handler.db.fighters = [self.char1, ally1, self.char2, ally2]
        handler.db.turn = 0

        handler.next_turn()

        self.assertTrue(handler.pk)  # fight correctly still running
        newchar = handler.db.fighters[handler.db.turn]
        self.assertNotEqual(newchar, ally1)
        self.assertGreater(newchar.db.hp, 0)

    def test_two_consecutive_defeated_fighters_are_both_skipped(self):
        from evennia.utils import create

        ally1 = create.create_object("typeclasses.characters.Character", key="ally1", location=self.room1)
        ally2 = create.create_object("typeclasses.characters.Character", key="ally2", location=self.room1)

        handler = self._make_handler()
        self.char1.db.hp, self.char1.db.combat_side = 100, "team_0"
        ally1.db.hp, ally1.db.combat_side = 0, "team_0"
        ally2.db.hp, ally2.db.combat_side = 0, "team_0"
        self.char2.db.hp, self.char2.db.combat_side = 100, "team_1"

        # char1 acts, then both ally1 and ally2 (defeated) should be
        # skipped in a row, landing on char2.
        handler.db.fighters = [self.char1, ally1, ally2, self.char2]
        handler.db.turn = 0

        handler.next_turn()

        self.assertEqual(handler.db.fighters[handler.db.turn], self.char2)


class TestSideBasedVictory(CombatTestBase):
    """
    A genuine 2v2 group-fight side check - the "never tested with an
    actual group" item flagged in CLAUDE.md's known-untested list.
    """

    def _make_handler(self):
        from evennia.utils import create

        return create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)

    def test_2v2_does_not_end_while_both_sides_have_a_survivor(self):
        from evennia.utils import create

        ally1 = create.create_object("typeclasses.characters.Character", key="ally1", location=self.room1)
        ally2 = create.create_object("typeclasses.characters.Character", key="ally2", location=self.room1)

        handler = self._make_handler()
        self.char1.db.hp, self.char1.db.combat_side = 100, "team_0"
        ally1.db.hp, ally1.db.combat_side = 0, "team_0"  # one ally down
        self.char2.db.hp, self.char2.db.combat_side = 100, "team_1"
        ally2.db.hp, ally2.db.combat_side = 100, "team_1"

        handler.db.fighters = [self.char1, ally1, self.char2, ally2]
        handler.db.turn = 0

        handler.next_turn()

        # Both sides still have at least one living member (char1 and
        # char2/ally2) - combat must still be running.
        self.assertTrue(handler.pk)

    def test_2v2_ends_when_one_whole_side_is_defeated(self):
        from evennia.utils import create

        ally1 = create.create_object("typeclasses.characters.Character", key="ally1", location=self.room1)
        ally2 = create.create_object("typeclasses.characters.Character", key="ally2", location=self.room1)

        handler = self._make_handler()
        self.char1.db.hp, self.char1.db.combat_side = 0, "team_0"
        ally1.db.hp, ally1.db.combat_side = 0, "team_0"
        self.char2.db.hp, self.char2.db.combat_side = 100, "team_1"
        ally2.db.hp, ally2.db.combat_side = 100, "team_1"

        handler.db.fighters = [self.char1, ally1, self.char2, ally2]
        handler.db.turn = 0

        handler.next_turn()

        self.assertFalse(handler.pk)


class TestAtPreMove(CombatTestBase):
    """
    CombatCharacter.at_pre_move - the movement gate checked by every
    move_to() call (direct exit traversal included). Covers the real
    bug found while reviewing a live Underworld rebuild: a genuinely
    dead character (is_dead=True, hp=0 by design - see
    CombatRules.handle_player_defeat) could not move through a normal
    exit at all, making the entire Underworld unwalkable by an actual
    dead player - the hp<=0 block had no exception for is_dead, only
    for the one system-driven force_move relocation.
    """

    def _make_normal_exit(self, destination):
        from evennia.utils import create

        return create.create_object(
            "typeclasses.exits.Exit", key="north", location=self.room1, destination=destination
        )

    def test_dead_character_can_traverse_a_normal_exit(self):
        from evennia.utils import create

        room2 = create.create_object("typeclasses.rooms.Room", key="deeper in the underworld")
        exit_obj = self._make_normal_exit(room2)

        self.char1.db.hp = 0
        self.char1.db.is_dead = True
        self.char1.db.combat_turnhandler = None
        self.char1.db.resting = False

        exit_obj.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, room2)

    def test_non_dead_character_at_zero_hp_is_still_blocked(self):
        """
        Regression guard: this must stay narrowly scoped to is_dead,
        not become a general 'anyone at 0 hp can walk around' hole -
        someone just knocked to 0 hp mid-fight (not yet processed by
        handle_player_defeat, is_dead still False) should still be
        stuck, same as always.
        """
        from evennia.utils import create

        room2 = create.create_object("typeclasses.rooms.Room", key="elsewhere")
        exit_obj = self._make_normal_exit(room2)

        self.char1.db.hp = 0
        self.char1.db.is_dead = False
        self.char1.db.combat_turnhandler = None
        self.char1.db.resting = False

        exit_obj.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, self.room1)

    def test_living_character_moves_normally(self):
        from evennia.utils import create

        room2 = create.create_object("typeclasses.rooms.Room", key="next room")
        exit_obj = self._make_normal_exit(room2)

        self.char1.db.hp = 100
        self.char1.db.is_dead = False
        self.char1.db.combat_turnhandler = None
        self.char1.db.resting = False

        exit_obj.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, room2)

    def test_in_combat_still_blocks_movement_even_if_dead(self):
        """is_in_combat is checked first and unconditionally - being
        dead doesn't grant an escape from an active fight."""
        from evennia.utils import create

        room2 = create.create_object("typeclasses.rooms.Room", key="battle exit")
        exit_obj = self._make_normal_exit(room2)

        self.char1.db.hp = 0
        self.char1.db.is_dead = True
        self.char1.db.combat_turnhandler = "truthy_stand_in"
        self.char1.db.resting = False

        exit_obj.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, self.room1)

    def test_resting_still_blocks_movement(self):
        from evennia.utils import create

        room2 = create.create_object("typeclasses.rooms.Room", key="resting exit")
        exit_obj = self._make_normal_exit(room2)

        self.char1.db.hp = 100
        self.char1.db.is_dead = False
        self.char1.db.combat_turnhandler = None
        self.char1.db.resting = True

        exit_obj.at_traverse(self.char1, room2)

        self.assertEqual(self.char1.location, self.room1)

    def test_force_move_still_bypasses_the_block_for_a_non_dead_character(self):
        """The force_move escape hatch stays available independent of
        is_dead, for any future system-driven relocation at hp<=0."""
        self.char1.db.hp = 0
        self.char1.db.is_dead = False
        self.char1.db.combat_turnhandler = None
        self.char1.db.resting = False

        from evennia.utils import create

        room2 = create.create_object("typeclasses.rooms.Room", key="forced destination")
        result = self.char1.move_to(room2, quiet=True, force_move=True)

        self.assertTrue(result)
        self.assertEqual(self.char1.location, room2)


class TestResting(CombatTestBase):
    def test_at_rest_tick_restores_percentage_of_max(self):
        self.char1.db.resting = True
        self.char1.db.max_hp = 100
        self.char1.db.hp = 50
        self.char1.db.max_mp = 100
        self.char1.db.mp = 50
        self.char1.db.max_sp = 100
        self.char1.db.sp = 50

        self.char1.at_rest_tick()

        self.assertEqual(self.char1.db.hp, 52)  # 2.5% of 100 = 2.5 -> int() = 2
        self.assertTrue(self.char1.db.resting)  # not full yet

    def test_resting_ends_automatically_at_full(self):
        from evennia import TICKER_HANDLER as tickerhandler

        self.char1.db.resting = True
        self.char1.db.max_hp = 100
        self.char1.db.hp = 99
        self.char1.db.max_mp = 20
        self.char1.db.mp = 20
        self.char1.db.max_sp = 30
        self.char1.db.sp = 30
        # Real usage always registers via CmdRest before resting
        # starts - stop_resting() (called once full) unregisters this
        # same ticker, so it must actually be registered first or the
        # test isn't exercising the real flow.
        tickerhandler.add(self.char1.REST_TICK_INTERVAL, self.char1.at_rest_tick)

        self.char1.at_rest_tick()

        self.assertEqual(self.char1.db.hp, 100)
        self.assertFalse(self.char1.db.resting)

    def test_stop_resting_is_safe_when_not_resting(self):
        self.char1.db.resting = False
        # Should not raise even though there's no active ticker to remove.
        self.char1.stop_resting()
        self.assertFalse(self.char1.db.resting)


class TestIsAlly(CombatTestBase):
    def test_prefers_combat_side_over_party_when_in_combat(self):
        """
        Two party members dueling each other for sport: party
        membership says allies, but combat_side says opposed - the
        docstring is explicit that combat_side should win here.
        """
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2]
        self.char2.db.party_leader = self.char1

        self.char1.db.combat_side = "A"
        self.char2.db.combat_side = "B"

        self.assertFalse(COMBAT_RULES.is_ally(self.char1, self.char2))

    def test_falls_back_to_party_membership_out_of_combat(self):
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2]
        self.char2.db.party_leader = self.char1

        self.char1.db.combat_side = None
        self.char2.db.combat_side = None

        self.assertTrue(COMBAT_RULES.is_ally(self.char1, self.char2))

    def test_strangers_are_not_allies(self):
        self.char1.db.combat_side = None
        self.char2.db.combat_side = None
        self.char1.db.party_leader = None
        self.char1.db.party_members = None
        self.assertFalse(COMBAT_RULES.is_ally(self.char1, self.char2))


class TestRegenCombatResources(CombatTestBase):
    """
    MP/SP previously never recovered mid-fight at all - see
    COMBAT_REGEN_PERCENT's own comment in world/combat.py for why
    that made every long fight collapse into plain 'attack' the
    moment early spending ran out.
    """

    def test_restores_a_percentage_of_max_mp_and_sp(self):
        self.char1.db.max_mp = 100
        self.char1.db.mp = 40
        self.char1.db.max_sp = 100
        self.char1.db.sp = 40

        COMBAT_RULES.regen_combat_resources(self.char1)

        self.assertEqual(self.char1.db.mp, 45)  # 40 + 5% of 100
        self.assertEqual(self.char1.db.sp, 45)

    def test_never_exceeds_max(self):
        self.char1.db.max_mp = 100
        self.char1.db.mp = 99
        self.char1.db.max_sp = 100
        self.char1.db.sp = 100

        COMBAT_RULES.regen_combat_resources(self.char1)

        self.assertEqual(self.char1.db.mp, 100)
        self.assertEqual(self.char1.db.sp, 100)

    def test_zero_max_pool_is_left_alone(self):
        # A pure-melee character with no real MP pool shouldn't get a
        # meaningless minimum-1 gain toward a pool that does nothing.
        self.char1.db.max_mp = 0
        self.char1.db.mp = 0
        self.char1.db.max_sp = 100
        self.char1.db.sp = 50

        COMBAT_RULES.regen_combat_resources(self.char1)

        self.assertEqual(self.char1.db.mp, 0)
        self.assertEqual(self.char1.db.sp, 55)

    def test_small_max_pool_still_gains_at_least_one(self):
        self.char1.db.max_mp = 10
        self.char1.db.mp = 0
        self.char1.db.max_sp = 0

        COMBAT_RULES.regen_combat_resources(self.char1)

        self.assertEqual(self.char1.db.mp, 1)  # round(10*0.05)=1 already, but guards the floor


class TestTryAutoAttack(CombatTestBase):
    """
    Regression coverage for the auto-attack toggle's core safety
    property: a manual action a player takes on their own turn must
    always win the race against the delayed auto-attack callback,
    never double-act alongside it.
    """

    def _make_handler(self):
        from evennia.utils import create
        from world.combat import CombatTurnHandler

        return create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)

    def setUp(self):
        super().setUp()
        self.char1.db.auto_attack = True
        self.char1.db.hp = 100
        self.char1.db.combat_side = "A"
        self.char2.db.hp = 100
        self.char2.db.combat_side = "B"
        self.handler = self._make_handler()
        self.handler.db.fighters = [self.char1, self.char2]
        self.handler.db.turn = 0
        self.char1.db.combat_turnhandler = self.handler
        self.char1.db.combat_actionsleft = 1

    @patch("world.combat.randint")
    def test_fires_when_nothing_else_has_happened(self, mock_randint):
        # A real, unmocked accuracy/damage roll made this test genuinely
        # flaky - it could legitimately miss or land 0 damage by chance,
        # exactly the un-guaranteed-probability testing mistake CLAUDE.md's
        # own testing conventions warn against. Force a guaranteed hit -
        # but NOT exactly 100 (char2's max_hp): mocking every randint()
        # call to a flat 100 makes the damage roll one-shot char2 to
        # precisely 0 HP, triggering the real defeat/respawn flow, which
        # then restores hp back to max as part of the "level<=5, no real
        # penalty" safe-respawn path - silently undoing the very damage
        # this test means to check for. Same trap already documented and
        # avoided elsewhere in this file (test_attack_on_your_turn_deals_
        # damage) - non-lethal 30 avoids it here too.
        mock_randint.return_value = 30
        COMBAT_RULES.try_auto_attack(self.char1)
        self.assertLess(self.char2.db.hp, 100)
        self.assertEqual(self.char1.db.combat_actionsleft, 0)

    def test_does_not_fire_if_player_already_acted(self):
        # Simulates a manual attack/cast/etc already having spent the turn's action.
        self.char1.db.combat_actionsleft = 0
        COMBAT_RULES.try_auto_attack(self.char1)
        self.assertEqual(self.char2.db.hp, 100)  # untouched

    def test_does_not_fire_when_toggled_off(self):
        self.char1.db.auto_attack = False
        COMBAT_RULES.try_auto_attack(self.char1)
        self.assertEqual(self.char2.db.hp, 100)

    def test_does_not_fire_if_defeated(self):
        self.char1.db.hp = 0
        COMBAT_RULES.try_auto_attack(self.char1)
        self.assertEqual(self.char2.db.hp, 100)

    def test_does_not_crash_if_character_has_no_location(self):
        """
        Real crash found live: a character deleted (or otherwise left
        locationless) while this delayed callback was still pending
        reached resolve_attack, which unconditionally does
        attacker.location.msg_contents(...) with no guard of its own -
        an AttributeError on a live server, not a quiet no-op.
        """
        self.char1.location = None
        COMBAT_RULES.try_auto_attack(self.char1)  # must not raise
        self.assertEqual(self.char2.db.hp, 100)

    def test_does_not_fire_if_turn_already_moved_on(self):
        self.handler.db.turn = 1  # now char2's turn, not char1's
        COMBAT_RULES.try_auto_attack(self.char1)
        self.assertEqual(self.char2.db.hp, 100)

    @patch("world.combat.randint")
    def test_falls_back_to_sole_living_opponent_if_last_target_invalid(self, mock_randint):
        # Non-lethal roll - see the comment on test_fires_when_nothing_
        # else_has_happened above for why exactly 100 (char2's max_hp)
        # would silently self-defeat this test via the respawn flow.
        mock_randint.return_value = 30
        self.char1.db.combat_last_target = None
        COMBAT_RULES.try_auto_attack(self.char1)
        self.assertLess(self.char2.db.hp, 100)

    def test_refuses_to_guess_with_multiple_possible_targets(self):
        from evennia.utils import create

        ally = create.create_object("typeclasses.characters.Character", key="ally3", location=self.room1)
        ally.db.hp = 100
        ally.db.combat_side = "B"
        self.handler.db.fighters = [self.char1, self.char2, ally]
        self.char1.db.combat_last_target = None

        COMBAT_RULES.try_auto_attack(self.char1)

        self.assertEqual(self.char2.db.hp, 100)
        self.assertEqual(ally.db.hp, 100)
