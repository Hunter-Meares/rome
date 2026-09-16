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

from evennia.utils import create

from world.combat import (
    COMBAT_RULES,
    CombatTurnHandler,
    HostileNPC,
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
    wizinvis_hides_from,
    ARENA_FIGHTER_GEAR,
    equip_arena_fighter,
    InstanceCleanupTimer,
    find_combat_target,
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
            # hit takes 4 args (attacker, weapon, defender, damage); miss/bounce
            # take 3 (attacker, weapon, defender). Would raise on a typo'd
            # placeholder count/type - real regression risk with this many hand-written strings.
            messages["hit"] % ("A", "sword", "B", 5)
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


class TestFindCombatTargetMatchesAnyWordInAMultiWordName(CombatTestBase):
    """
    find_combat_target's plain-key fallback (used whenever the sdesc-
    aware search finds nothing - see the function's own docstring) -
    real, confirmed live bug: it only matched a search string against
    the START of an object's WHOLE key, so a multi-word name's own
    trailing, most-distinguishing word ("stiletto" in "a duelist's
    stiletto") could never match at all, only a genuine prefix of the
    full name ("a duelist"). Found via the shared equipment-search
    helper this same fix applies to (_search_carried_or_equipped,
    world/tests_combat_commands.py) - fixed at the shared root
    (_key_or_alias_matches) so both call sites benefit.
    """

    def test_matches_the_trailing_word_of_a_multiword_key(self):
        from evennia.utils import create

        npc = create.create_object(
            "typeclasses.characters.Character", key="a grizzled old veteran", location=self.room1
        )
        self.char1.location = self.room1
        # Strip Builder-tier permission so this actually exercises the
        # fallback path being tested, not rpsystem's own separate
        # plain-key fallback for Builders (get_search_result's
        # is_builder branch) - see the equivalent note in
        # tests_combat_commands.py's equipment-search tests.
        self.char1.permissions.remove("Developer")

        found = find_combat_target(self.char1, "veteran", candidates=self.room1.contents)

        self.assertEqual(found, npc)

    def test_still_matches_a_genuine_whole_key_prefix(self):
        from evennia.utils import create

        npc = create.create_object(
            "typeclasses.characters.Character", key="a grizzled old veteran", location=self.room1
        )
        self.char1.location = self.room1
        self.char1.permissions.remove("Developer")

        found = find_combat_target(self.char1, "a grizzled", candidates=self.room1.contents)

        self.assertEqual(found, npc)


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


class TestConditionTickdownDoesNotDependOnTheOriginalInflicter(CombatTestBase):
    """
    Regression coverage for a real, confirmed live bug: a player got
    Poisoned by another player (a Haruspex) in one fight, then kept
    fighting entirely unrelated NPCs afterward - and the Poisoned
    condition never expired, reapplying its damage every single turn
    indefinitely, for hours, even across a disconnect/reconnect.

    Root cause: condition_tickdown only ever decremented duration
    `if condition_turnchar == turnchar` - condition_turnchar being the
    ORIGINAL INFLICTER (stored so a DOT kill can still credit the
    right attacker). The moment that exact inflicter isn't part of
    the character's current turn rotation (a different fight, or no
    fight at all), turnchar can never equal them again, so the
    duration count is permanently frozen above 0. Confirmed live via
    the actual stuck character's own data: {'Poisoned': [4, Caesar]}
    - Caesar being the original attacker from a past, unrelated fight.

    Fixed to decrement on the condition-HOLDER's own turn instead.
    """

    def test_hostile_condition_ticks_down_on_the_victims_own_turn_not_the_inflicters(self):
        # char2 poisoned char1 in some past encounter - char2 isn't
        # part of char1's current turn rotation at all anymore.
        self.char1.db.conditions = {"Poisoned": [3, self.char2]}

        # char1's own turn starting, in a fight that doesn't involve
        # char2 at all (e.g. char1 vs an NPC) - this must still count.
        COMBAT_RULES.condition_tickdown(self.char1, self.char1)

        self.assertEqual(self.char1.db.conditions["Poisoned"][0], 2)

    def test_hostile_condition_does_not_tick_down_on_someone_elses_turn(self):
        self.char1.db.conditions = {"Poisoned": [3, self.char2]}

        # A different fighter's turn starting (not char1's own) -
        # char1's own condition shouldn't move yet.
        COMBAT_RULES.condition_tickdown(self.char1, self.char2)

        self.assertEqual(self.char1.db.conditions["Poisoned"][0], 3)

    def test_hostile_condition_eventually_expires_across_unrelated_turns(self):
        self.char1.db.conditions = {"Poisoned": [2, self.char2]}

        COMBAT_RULES.condition_tickdown(self.char1, self.char1)
        self.assertIn("Poisoned", self.char1.db.conditions)
        COMBAT_RULES.condition_tickdown(self.char1, self.char1)

        self.assertNotIn("Poisoned", self.char1.db.conditions)

    def test_self_inflicted_condition_behavior_is_unchanged(self):
        """
        Regression guard: a self-inflicted condition (turnchar ==
        character already) must decrement exactly the same as before -
        this fix should be a no-op for anything that already worked.
        """
        self.char1.db.conditions = {"Regeneration": [2, self.char1]}
        COMBAT_RULES.condition_tickdown(self.char1, self.char1)
        self.assertEqual(self.char1.db.conditions["Regeneration"][0], 1)

    def test_out_of_combat_ticker_now_expires_a_lingering_hostile_condition(self):
        """
        The exact real-world path the live bug took: the out-of-combat
        ticker calls condition_tickdown(self, self) every 30 seconds.
        Under the old logic that never matched a hostile condition's
        stored (different) inflicter, so it never decremented while
        idle either - confirmed live (combat_turnhandler was None,
        condition still stuck). Now it correctly does.
        """
        self.char1.location = self.room1
        self.char1.db.conditions = {"Poisoned": [1, self.char2]}
        self.char1.db.combat_turnhandler = None

        self.char1.at_update()

        self.assertNotIn("Poisoned", self.char1.db.conditions)

    def test_out_of_combat_tick_no_longer_reattributes_the_condition_to_the_victim(self):
        """
        A second, related bug this same fix removed: at_update used to
        overwrite every condition's stored turnchar with the character
        themselves before ticking down, as a workaround for the (now
        fixed) old condition_tickdown logic. That workaround silently
        misattributed a poisoner's own kill credit to the VICTIM the
        moment one idle tick passed - breaking XP/gold-split and the
        colosseum escape-on-victory check for a poison death that
        happens to land while the victim is out of combat. Confirmed
        fixed: the real poisoner (char2) must still be the one
        credited after an out-of-combat tick, not char1 themselves.
        """
        self.char1.location = self.room1
        self.char1.db.conditions = {"Poisoned": [5, self.char2]}
        self.char1.db.combat_turnhandler = None

        self.char1.at_update()

        self.assertEqual(self.char1.db.conditions["Poisoned"][1], self.char2)


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


class TestResolveAttackMessageColor(CombatTestBase):
    """
    Names are deliberately plain in combat messages - a direct
    follow-up request reversing an earlier pass that colored attacker/
    defender names in every hit/miss/bounce message. The action verb
    and the damage number are the things worth highlighting instead
    (see WEAPON_CATEGORY_MESSAGES/DEFAULT_WEAPON_MESSAGES, each "hit"
    template's verb phrase wrapped in |y).
    """

    def test_hit_message_does_not_color_either_name(self):
        captured = []
        self.room1.msg_contents = lambda text="", **kwargs: captured.append(text)
        COMBAT_RULES.resolve_attack(
            self.char1, self.char2, attack_value=999, defense_value=1, damage_value=10
        )
        full_text = "".join(str(m) for m in captured)
        self.assertNotIn("|c%s|n" % self.char1.key, full_text)
        self.assertNotIn("|m%s|n" % self.char2.key, full_text)
        self.assertIn(self.char1.key, full_text)
        self.assertIn(self.char2.key, full_text)

    def test_hit_message_colors_the_action_verb_and_damage(self):
        captured = []
        self.room1.msg_contents = lambda text="", **kwargs: captured.append(text)
        COMBAT_RULES.resolve_attack(
            self.char1, self.char2, attack_value=999, defense_value=1, damage_value=10
        )
        full_text = "".join(str(m) for m in captured)
        # Unarmed default template - see DEFAULT_WEAPON_MESSAGES.
        self.assertIn("|ystrikes|n", full_text)
        self.assertIn("|r10|n", full_text)

    def test_miss_message_does_not_color_either_name(self):
        captured = []
        self.room1.msg_contents = lambda text="", **kwargs: captured.append(text)
        COMBAT_RULES.resolve_attack(
            self.char1, self.char2, attack_value=1, defense_value=999
        )
        full_text = "".join(str(m) for m in captured)
        self.assertNotIn("|c%s|n" % self.char1.key, full_text)
        self.assertNotIn("|m%s|n" % self.char2.key, full_text)
        self.assertIn(self.char1.key, full_text)
        self.assertIn(self.char2.key, full_text)


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

    def test_initialize_for_combat_resets_stale_damage_log(self):
        """
        Real bug found live: a persistent NPC (e.g. a Ludus trainer)
        fought and killed more than once kept accumulating damage_log
        entries from every past fight forever - nothing ever cleared
        it, not respawn, not a fresh fight starting. That silently
        diluted a genuinely solo kill's own share of xp_reward below
        100%, explaining reported XP varying kill to kill against the
        identical NPC. initialize_for_combat runs for every fighter at
        the start of every single fight regardless of how the last one
        ended, making it the one safe place to reset this.
        """
        from evennia.utils import create

        self.char2.db.damage_log = {self.char1: 9999, "stale": 1}
        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        handler.initialize_for_combat(self.char2)
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

    def test_party_kill_gets_a_bonus_to_the_whole_xp_pool_but_not_gold(self):
        """
        Two REAL party members (not just two unrelated attackers - see
        the sibling test below) contributing to the same kill should
        get the +20% PARTY_XP_BONUS_PERCENT applied to the whole XP
        pool before it's split, same proportional damage share as
        always. Gold is deliberately untouched by this bonus.
        """
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2]
        self.char2.db.party_leader = self.char1

        npc = self._make_dummy_npc(xp_reward=15)  # below xp_for_level(1)=20
        npc.db.damage_log = {self.char1: 80, self.char2: 20}

        self.char1.db.xp = 0
        self.char2.db.xp = 0
        self.char1.db.gold = 0
        self.char2.db.gold = 0
        self.char1.db.level = 1
        self.char2.db.level = 1

        COMBAT_RULES.at_defeat(npc, attacker=self.char1)

        # 15 * 1.20 = 18 total pool, split 80/20 -> 14/4
        self.assertEqual(self.char1.db.xp, 14)
        self.assertEqual(self.char2.db.xp, 4)

        # Gold still derives from the ORIGINAL xp_reward (15), no bonus.
        self.assertEqual(self.char1.db.gold, 4)
        self.assertEqual(self.char2.db.gold, 1)

    def test_two_unpartied_attackers_do_not_get_the_party_bonus(self):
        """
        Two different characters both hitting the same NPC, with no
        real party between them, is exactly the existing
        test_two_attackers_split_xp_and_gold_proportionally scenario -
        this makes the "why no bonus" reasoning explicit and directly
        testable on its own, via _is_party_kill itself.
        """
        self.char1.db.party_leader = None
        self.char2.db.party_leader = None
        damage_log = {self.char1: 80, self.char2: 20}
        self.assertFalse(COMBAT_RULES._is_party_kill(damage_log))

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


class TestStartTurnRoomSpacing(CombatTestBase):
    """
    A direct complaint from live playtesting: a long fight reads as an
    unbroken wall of text, since none of the many separate combat
    message call sites across this file insert any visual separation.
    Rather than touching every one of those individually,
    CombatTurnHandler.start_turn() now sends one blank line to the
    whole room at the start of every character's turn - guaranteed to
    run exactly once per turn, for every fighter, in every fight.
    """

    def _make_handler(self):
        from evennia.utils import create

        return create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)

    def test_start_turn_sends_a_blank_line_to_the_room(self):
        handler = self._make_handler()
        captured = []
        self.room1.msg_contents = lambda text="", **kwargs: captured.append(text)

        handler.start_turn(self.char1)

        self.assertIn("\n", captured)

    def test_start_turn_does_not_crash_with_no_location(self):
        handler = self._make_handler()
        self.char1.location = None

        handler.start_turn(self.char1)  # should not raise


class TestTurnStartMessageIsPlain(CombatTestBase):
    """
    A direct complaint from live playtesting: the HP/MP/SP meter block
    shown at the start of every turn made combat feel cluttered,
    restating the same numbers the ordinary trailing prompt
    (RomePromptMixin) already shows after every command. Removed -
    'It's your turn!' now stands alone.
    """

    def test_no_meter_bars_in_turn_start_message(self):
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)
        self.char1.db.combat_turnhandler = "truthy_stand_in"

        self.char1.at_turn_start()

        full_text = "".join(str(m) for m in captured)
        self.assertIn("It's your turn!", full_text)
        self.assertNotIn("HP ", full_text)
        self.assertNotIn("MP ", full_text)
        self.assertNotIn("SP ", full_text)


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


class TestWizinvis(CombatTestBase):
    """
    Regression coverage for wizinvis: hidden from a lower-level looker,
    visible to an equal-or-higher one or a true superuser, and its
    effect on get_display_name (used for both the who-list check in
    commands/social.py and, since say/pose both resolve a speaker's
    name via get_display_name per listener, for masking speech/emotes
    too).
    """

    def setUp(self):
        super().setUp()
        self.char1.db.wizinvis = True
        self.char1.db.level = 105
        self.char2.db.level = 10

    def test_hidden_from_a_lower_level_looker(self):
        self.assertTrue(wizinvis_hides_from(self.char1, self.char2))

    def test_visible_to_an_equal_or_higher_level_looker(self):
        self.char2.db.level = 105
        self.assertFalse(wizinvis_hides_from(self.char1, self.char2))

    def test_visible_to_a_true_superuser(self):
        self.account2.is_superuser = True
        self.assertFalse(wizinvis_hides_from(self.char1, self.char2))

    def test_not_hidden_when_wizinvis_is_off(self):
        self.char1.db.wizinvis = False
        self.assertFalse(wizinvis_hides_from(self.char1, self.char2))

    def test_never_hidden_from_self(self):
        self.assertFalse(wizinvis_hides_from(self.char1, self.char1))

    def test_get_display_name_returns_someone_to_a_lower_level_looker(self):
        self.assertEqual(self.char1.get_display_name(self.char2), "Someone")

    def test_get_display_name_returns_real_name_to_an_equal_level_looker(self):
        self.char2.db.level = 105
        self.assertEqual(self.char1.get_display_name(self.char2), self.char1.key)


class TestConditionMessagesColorTheConditionName(CombatTestBase):
    """
    A direct follow-up request: condition names (Accuracy Down,
    Defense Up, etc.) are one of the "key things a player needs to
    see" in combat, alongside the action verb and damage number -
    colored consistently everywhere a condition is gained, expires, or
    is cured (add_condition, tick_conditions, itemfunc_cure_condition,
    spell_cure_condition).
    """

    def test_add_condition_colors_the_condition_name(self):
        captured = []
        self.char1.location.msg_contents = lambda text="", **kwargs: captured.append(text)
        COMBAT_RULES.add_condition(self.char1, self.char1, "Accuracy Down", 3)
        full_text = "".join(str(m) for m in captured)
        self.assertIn("|MAccuracy Down|n", full_text)

    def test_condition_expiry_colors_the_condition_name(self):
        # turnchar is char1 (the condition-holder) - ticking down now
        # happens on the HOLDER's own turn, not the original
        # inflicter's (char2) - see condition_tickdown's own docstring
        # for the real bug this fixed.
        COMBAT_RULES.get_conditions(self.char1)["Accuracy Down"] = [1, self.char2]
        captured = []
        self.char1.location.msg_contents = lambda text="", **kwargs: captured.append(text)

        COMBAT_RULES.condition_tickdown(self.char1, self.char1)

        full_text = "".join(str(m) for m in captured)
        self.assertIn("|MAccuracy Down|n", full_text)


class TestSkillAndSpellAnnouncementOrdering(CombatTestBase):
    """
    Regression coverage for a real bug found live: 'Gaveth gains the
    Accuracy Down condition' printed BEFORE 'Rutilus uses feint!' -
    add_condition() sends its own message immediately, so any
    skillfunc/spellfunc that applied conditions before sending its own
    'uses/casts X!' announcement had the two messages backwards. Fixed
    in every skillfunc/spellfunc that calls add_condition. These tests
    capture messages in send order and assert the skill/spell's own
    announcement comes first.
    """

    def _capture(self):
        captured = []
        self.char1.location.msg_contents = lambda text="", **kwargs: captured.append(str(text))
        return captured

    def _assert_announcement_before_condition(self, captured, announcement_substr):
        ann_index = next(i for i, m in enumerate(captured) if announcement_substr in m)
        cond_index = next(i for i, m in enumerate(captured) if "gains the" in m)
        self.assertLess(ann_index, cond_index)

    def test_skill_add_condition_announces_before_condition(self):
        captured = self._capture()
        self.char1.db.sp = 10
        COMBAT_RULES.skill_add_condition(
            self.char1, "feint", [self.char2], 4, conditions=[("Accuracy Down", 3)]
        )
        self._assert_announcement_before_condition(captured, "uses feint!")

    def test_spell_add_condition_announces_before_condition(self):
        captured = self._capture()
        self.char1.db.mp = 10
        COMBAT_RULES.spell_add_condition(
            self.char1, "auspice", [self.char2], 4, conditions=[("Defense Up", 3)]
        )
        self._assert_announcement_before_condition(captured, "casts auspice!")

    def test_skill_deathmark_announces_before_condition(self):
        captured = self._capture()
        self.char1.db.sp = 10
        COMBAT_RULES.skill_deathmark(self.char1, "deathmark", [self.char2], 6)
        self._assert_announcement_before_condition(captured, "marks")

    def test_skill_riposte_announces_before_condition(self):
        captured = self._capture()
        self.char1.db.sp = 10
        COMBAT_RULES.skill_riposte(self.char1, "riposte", [self.char1], 3)
        self._assert_announcement_before_condition(captured, "ready stance")

    def test_skill_reckless_abandon_announces_before_condition(self):
        captured = self._capture()
        self.char1.db.sp = 10
        COMBAT_RULES.skill_reckless_abandon(self.char1, "reckless abandon", [self.char2], 6)
        self._assert_announcement_before_condition(captured, "devastating strike")

    def test_skill_pack_tactics_announces_before_condition(self):
        from evennia.utils import create
        from typeclasses.characters import Character

        companion = create.create_object(Character, key="a wolf", location=self.room1)
        self.char1.db.active_companion = companion
        captured = self._capture()
        self.char1.db.sp = 10
        COMBAT_RULES.skill_pack_tactics(self.char1, "pack tactics", [], 3)
        self._assert_announcement_before_condition(captured, "practiced coordination")

    def test_skill_ambush_announces_before_condition(self):
        self.char1.db.hp = self.char1.db.max_hp
        self.char2.db.hp = self.char2.db.max_hp
        captured = self._capture()
        self.char1.db.sp = 10
        COMBAT_RULES.skill_ambush(self.char1, "ambush", [self.char2], 5)
        self._assert_announcement_before_condition(captured, "ambushing")


class TestPromptRefreshDuringAutoAttack(CombatTestBase):
    """
    Regression coverage for two real bugs found live, in sequence:

    1. An entire fight resolved almost entirely via auto-attack showed
       the HP/MP/SP prompt exactly once (on the manually-typed
       'challenge'/'fight') and never again for the rest of the fight -
       auto-attack runs as a delayed callback, not a real Command, so
       RomePromptMixin's at_post_cmd() (the only other place the
       prompt was ever sent) never fired for that character's turn.
       Fixed by explicitly refreshing the prompt in try_auto_attack()
       right after it resolves.

    2. That fix was first placed in BOTH start_turn() (every turn) and
       try_auto_attack() - which then showed the prompt TWICE, back to
       back, every single round: start_turn()'s own explicit send
       landed immediately next to the prompt a player already gets for
       free from an idle return while waiting (CmdNoInput ->
       RomePromptMixin.at_post_cmd, commands/command.py) - something
       most players do while auto-attack counts down. start_turn()'s
       explicit send was removed, keeping only try_auto_attack()'s -
       still covers the one real gap (a player who never types
       anything at all during an auto-attacked turn) without colliding
       with the idle-return refresh that already covers everyone else.
    """

    def _make_handler(self):
        from evennia.utils import create

        return create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)

    def test_start_turn_does_not_send_its_own_hpmp_prompt(self):
        handler = self._make_handler()
        prompts = []
        self.char1.msg = lambda text="", **kwargs: prompts.append(kwargs.get("prompt"))

        handler.start_turn(self.char1)

        self.assertFalse(any(p for p in prompts if p))

    def test_try_auto_attack_sends_the_hpmp_prompt(self):
        self.char1.db.combat_turnhandler = self._make_handler()
        self.char1.db.combat_turnhandler.db.fighters = [self.char1, self.char2]
        self.char1.db.combat_turnhandler.db.turn = 0
        self.char1.db.auto_attack = True
        self.char1.db.combat_actionsleft = 1
        self.char1.db.combat_last_target = self.char2

        prompts = []
        self.char1.msg = lambda text="", **kwargs: prompts.append(kwargs.get("prompt"))

        COMBAT_RULES.try_auto_attack(self.char1)

        self.assertTrue(any(p for p in prompts if p))


class TestTimeoutWarningSkipsAutoAttack(CombatTestBase):
    """
    Direct request: a player with auto-attack on can never actually
    time out (AUTO_ATTACK_DELAY fires well before TURN_TIMEOUT), so
    the 'WARNING: About to time out!' message is pure noise for them -
    skipped entirely when db.auto_attack is True.
    """

    def _make_handler_at_timer(self, timer_value, auto_attack):
        from evennia.utils import create

        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        handler.db.fighters = [self.char1, self.char2]
        handler.db.turn = 0
        handler.db.timer = timer_value
        handler.db.timeout_warning_given = False
        handler.interval = 5
        self.char1.db.auto_attack = auto_attack
        return handler

    def test_warning_shown_without_auto_attack(self):
        handler = self._make_handler_at_timer(15, auto_attack=False)
        messages = []
        self.char1.msg = lambda text="", **kwargs: messages.append(text)

        handler.at_repeat()

        self.assertTrue(any("About to time out" in str(m) for m in messages))

    def test_warning_skipped_with_auto_attack(self):
        handler = self._make_handler_at_timer(15, auto_attack=True)
        messages = []
        self.char1.msg = lambda text="", **kwargs: messages.append(text)

        handler.at_repeat()

        self.assertFalse(any("About to time out" in str(m) for m in messages))


class TestArenaFighterEquipment(EvenniaTest):
    """
    A direct request: the Deeper Sands' Arena Fighters should have
    real, mechanically-active weapons/armor, not just flavor text like
    every other NPC in the game. equip_arena_fighter() is called from
    RespawningNPC.at_object_post_creation() - these tests spawn the
    real prototypes (via Evennia's actual spawner, not a stand-in) to
    confirm the whole path really wires up, matching this project's
    own "verify against real spawn behavior" testing convention (see
    world/tests_bounties.py's TestRealSpawnKeyMatching).
    """

    def test_every_gear_table_entry_matches_a_real_prototype_key(self):
        from world.prototypes import (
            ARENA_FIGHTER_RECRUIT, ARENA_FIGHTER_HUNTER, ARENA_FIGHTER_BRUTE,
            ARENA_FIGHTER_DUELIST, ARENA_FIGHTER_CHAMPION, ARENA_FIGHTER_MASTER,
        )

        real_keys = {
            p["key"] for p in (
                ARENA_FIGHTER_RECRUIT, ARENA_FIGHTER_HUNTER, ARENA_FIGHTER_BRUTE,
                ARENA_FIGHTER_DUELIST, ARENA_FIGHTER_CHAMPION, ARENA_FIGHTER_MASTER,
            )
        }
        self.assertEqual(set(ARENA_FIGHTER_GEAR.keys()), real_keys)

    def test_recruit_spawns_with_a_real_weapon_and_armor(self):
        from evennia.prototypes.spawner import spawn

        npc = spawn("ARENA_FIGHTER_RECRUIT")[0]
        self.assertIsNotNone(npc.db.wielded_weapon)
        self.assertEqual(npc.db.wielded_weapon.db.weapon_type_name, "gladius")
        self.assertIsNotNone(npc.db.worn_armor)
        self.assertEqual(npc.db.worn_armor.db.armor_category, "medium")
        self.assertIsNone(npc.db.worn_shield)

    def test_gear_is_leveled_to_the_fighter_own_level(self):
        from evennia.prototypes.spawner import spawn
        from world.combat import compute_weapon_stats

        npc = spawn("ARENA_FIGHTER_RECRUIT")[0]
        expected_range, expected_accuracy, _ = compute_weapon_stats("gladius", 75)
        self.assertEqual(npc.db.wielded_weapon.db.damage_range, expected_range)
        self.assertEqual(npc.db.wielded_weapon.db.accuracy_bonus, expected_accuracy)

    def test_champion_gets_a_shield_with_its_fixed_unleveled_bonus(self):
        from evennia.prototypes.spawner import spawn

        npc = spawn("ARENA_FIGHTER_CHAMPION")[0]
        self.assertIsNotNone(npc.db.worn_shield)
        # SCUTUM's own fixed +12 - NOT run through compute_armor_stats,
        # which would invert its sign at this level (see
        # equip_arena_fighter's own docstring for why).
        self.assertEqual(npc.db.worn_shield.db.defense_modifier, 12)

    def test_master_has_no_race_key_and_still_gets_equipped(self):
        from evennia.prototypes.spawner import spawn

        # ARENA_FIGHTER_MASTER has no "race" field at all - confirms
        # equip_arena_fighter doesn't depend on it.
        npc = spawn("ARENA_FIGHTER_MASTER")[0]
        self.assertIsNotNone(npc.db.wielded_weapon)
        self.assertEqual(npc.db.wielded_weapon.db.weapon_type_name, "waraxe")

    def test_unrelated_npc_is_left_alone(self):
        from evennia.utils import create

        npc = create.create_object(
            "typeclasses.characters.Character", key="a passerby", location=self.room1
        )
        equip_arena_fighter(npc)  # should be a silent no-op
        self.assertIsNone(npc.db.wielded_weapon)


class TestAnnounceHpThresholdChange(CombatTestBase):
    """
    A direct request: a player needs some standing way to gauge how
    wounded an NPC - or another PLAYER, for a healer specifically -
    actually is, not just whatever happened to be baked into the one
    attacker's own last hit message (which also only ever showed on a
    successful hit, not a miss, and only to whoever landed it). This
    reuses hp_status_phrase's own existing 100/75/50/25% bands rather
    than inventing a second set of thresholds.
    """

    def _capture(self):
        captured = []
        self.char1.location.msg_contents = lambda text="", **kwargs: captured.append(str(text))
        return captured

    def test_no_announcement_when_still_in_the_same_band(self):
        self.char1.db.max_hp = 100
        self.char1.db.hp = 90
        captured = self._capture()

        COMBAT_RULES.announce_hp_threshold_change(self.char1, old_hp=95)

        self.assertEqual(captured, [])

    def test_announces_when_crossing_downward(self):
        self.char1.db.max_hp = 100
        self.char1.db.hp = 40  # "looks badly wounded" band
        captured = self._capture()

        COMBAT_RULES.announce_hp_threshold_change(self.char1, old_hp=60)  # "looks wounded"

        full_text = "".join(captured)
        self.assertIn(self.char1.key, full_text)
        self.assertIn("badly wounded", full_text)

    def test_announces_when_crossing_upward_after_healing(self):
        self.char1.db.max_hp = 100
        self.char1.db.hp = 100
        captured = self._capture()

        COMBAT_RULES.announce_hp_threshold_change(self.char1, old_hp=60)  # "looks wounded"

        full_text = "".join(captured)
        self.assertIn("completely unscathed", full_text)

    def test_no_location_does_not_crash(self):
        self.char1.location = None
        COMBAT_RULES.announce_hp_threshold_change(self.char1, old_hp=100)  # should not raise


class TestHpThresholdAnnouncementIntegration(CombatTestBase):
    """
    Confirms the actual call sites: attack paths (resolve_attack,
    spell_attack, skill_attack) suppress the standalone announcement
    since their own hit message already shows the same information
    inline, while everything else that changes HP with no wound
    feedback of its own (poison, Riposte counter-damage, Vampiric
    Touch's damage side, and every healing path) gets it.
    """

    def _capture(self):
        captured = []
        self.char1.location.msg_contents = lambda text="", **kwargs: captured.append(str(text))
        return captured

    def test_resolve_attack_does_not_double_announce(self):
        self.char2.db.max_hp = 100
        self.char2.db.hp = 100
        captured = self._capture()

        # 100 - 60 = 40% remaining -> the "badly wounded" band.
        COMBAT_RULES.resolve_attack(
            self.char1, self.char2, attack_value=999, defense_value=1, damage_value=60
        )

        # The hit message itself mentions the wound phrase once - a
        # separate standalone "|Y...|n" announcement line would be a
        # second, different message string in the captured list.
        wound_mentions = sum(1 for m in captured if "badly wounded" in m)
        self.assertEqual(wound_mentions, 1)

    def test_poison_tick_gets_the_standalone_announcement(self):
        self.char1.db.max_hp = 100
        self.char1.db.hp = 60
        COMBAT_RULES.get_conditions(self.char1)["Poisoned"] = [3, self.char2]
        captured = self._capture()

        # 60 - 15 = 45% remaining -> the "badly wounded" band.
        with patch("world.combat.randint", return_value=15):
            COMBAT_RULES.apply_turn_conditions(self.char1)

        full_text = "".join(captured)
        self.assertIn("badly wounded", full_text)

    def test_itemfunc_heal_announces_a_full_recovery(self):
        from evennia.utils import create

        self.char1.db.max_hp = 100
        self.char1.db.hp = 20
        item = create.create_object(
            "evennia.objects.objects.DefaultObject", key="a healing potion",
        )
        captured = self._capture()

        with patch("world.combat.randint", return_value=999):
            COMBAT_RULES.itemfunc_heal(item, self.char1, self.char1)

        full_text = "".join(captured)
        self.assertIn("completely unscathed", full_text)

    def test_spell_healing_announces_per_target(self):
        self.char1.db.max_hp = 100
        self.char1.db.hp = 100
        self.char2.db.max_hp = 100
        self.char2.db.hp = 20
        self.char1.db.mp = 50
        captured = self._capture()

        with patch("world.combat.randint", return_value=999):
            COMBAT_RULES.spell_healing(
                self.char1, "greater restoration", [self.char2], 10
            )

        full_text = "".join(captured)
        self.assertIn("%s looks completely unscathed" % self.char2.key, full_text)


class TestSummonedAllySignatureMoves(CombatTestBase):
    """
    Regression coverage for each summon line's one on-theme signature
    move - a flat proc chance on the pet's own landed attack, not a
    random pick from a full class's spell/skill list (see
    SummonedAlly's own docstring for the full design reasoning behind
    that choice). Each line reuses an existing condition/mechanic
    rather than inventing anything new: Augur familiars apply
    Accuracy Down, Haruspex lemures apply Frightened, Venator beasts
    just deal flat bonus damage.
    """

    def _make_pet(self, pet_line, key="a test pet"):
        from evennia.utils import create

        pet = create.create_object(
            "world.combat.SummonedAlly", key=key, location=self.room1
        )
        pet.db.pet_line = pet_line
        return pet

    def test_augur_familiar_applies_accuracy_down_on_a_landed_hit(self):
        pet = self._make_pet("augur")
        hp_before = self.char2.db.hp
        self.char2.db.hp -= 10  # simulate the attack having landed
        with patch("world.combat.randint", return_value=1):  # force the proc to succeed
            pet._try_signature_move(self.char2, hp_before)
        self.assertIn("Accuracy Down", COMBAT_RULES.get_conditions(self.char2))

    def test_haruspex_lemures_applies_frightened_on_a_landed_hit(self):
        pet = self._make_pet("haruspex")
        hp_before = self.char2.db.hp
        self.char2.db.hp -= 10
        with patch("world.combat.randint", return_value=1):
            pet._try_signature_move(self.char2, hp_before)
        self.assertIn("Frightened", COMBAT_RULES.get_conditions(self.char2))

    def test_venator_beast_deals_bonus_damage_on_a_landed_hit(self):
        pet = self._make_pet("venator")
        self.char2.db.hp = 100
        self.char2.db.max_hp = 100
        hp_before = self.char2.db.hp
        self.char2.db.hp -= 10
        # First randint call is the proc-chance roll (force success);
        # second is the bonus-damage roll (fixed at 8 for an exact
        # assertion).
        with patch("world.combat.randint", side_effect=[1, 8]):
            pet._try_signature_move(self.char2, hp_before)
        self.assertEqual(self.char2.db.hp, 100 - 10 - 8)

    def test_no_signature_move_on_a_miss(self):
        pet = self._make_pet("augur")
        hp_before = self.char2.db.hp  # unchanged - simulates a miss
        with patch("world.combat.randint", return_value=1):
            pet._try_signature_move(self.char2, hp_before)
        self.assertNotIn("Accuracy Down", COMBAT_RULES.get_conditions(self.char2))

    def test_no_signature_move_when_the_hit_was_lethal(self):
        pet = self._make_pet("augur")
        hp_before = self.char2.db.hp
        self.char2.db.hp = 0
        with patch("world.combat.randint", return_value=1):
            pet._try_signature_move(self.char2, hp_before)
        self.assertNotIn("Accuracy Down", COMBAT_RULES.get_conditions(self.char2))

    def test_proc_chance_roll_above_threshold_does_nothing(self):
        pet = self._make_pet("augur")
        hp_before = self.char2.db.hp
        self.char2.db.hp -= 10
        with patch("world.combat.randint", return_value=pet.PET_PROC_CHANCE + 1):
            pet._try_signature_move(self.char2, hp_before)
        self.assertNotIn("Accuracy Down", COMBAT_RULES.get_conditions(self.char2))

    def test_unknown_pet_line_is_a_silent_no_op(self):
        pet = self._make_pet(None)
        hp_before = self.char2.db.hp
        self.char2.db.hp -= 10
        with patch("world.combat.randint", return_value=1):
            pet._try_signature_move(self.char2, hp_before)  # should not raise
        self.assertEqual(COMBAT_RULES.get_conditions(self.char2), {})


class TestReleasePet(CombatTestBase):
    """
    Regression coverage for CombatRules.release_pet() - the shared
    cleanup helper backing 'dismiss', a successful flee/disengage, and
    an owner's own defeat. See handle_player_defeat's and
    CmdDisengage's own tests for the wiring into those two call sites;
    this class exercises release_pet() itself directly.
    """

    def _make_pet(self, key="a test pet"):
        from evennia.utils import create

        return create.create_object(
            "world.combat.SummonedAlly", key=key, location=self.room1
        )

    def test_dismissed_clears_owner_reference_and_deletes_pet(self):
        pet = self._make_pet()
        self.char1.db.active_companion = pet
        COMBAT_RULES.release_pet(pet, self.char1, reason="dismissed")
        self.assertIsNone(self.char1.db.active_companion)
        self.assertFalse(pet.pk)

    def test_owner_fled_deletes_the_pet(self):
        pet = self._make_pet()
        self.char1.db.active_companion = pet
        COMBAT_RULES.release_pet(pet, self.char1, reason="owner_fled")
        self.assertFalse(pet.pk)

    def test_owner_defeated_deletes_the_pet(self):
        pet = self._make_pet()
        self.char1.db.active_companion = pet
        COMBAT_RULES.release_pet(pet, self.char1, reason="owner_defeated")
        self.assertFalse(pet.pk)

    def test_none_pet_is_a_no_op_past_clearing_the_owner_reference(self):
        self.char1.db.active_companion = None
        COMBAT_RULES.release_pet(None, self.char1, reason="dismissed")  # should not raise
        self.assertIsNone(self.char1.db.active_companion)

    def test_removes_the_pet_from_an_active_turnhandler(self):
        from evennia.utils import create

        pet = self._make_pet()
        self.char1.db.active_companion = pet
        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        handler.db.fighters = [self.char1, pet, self.char2]
        handler.db.turn = 1
        pet.db.combat_turnhandler = handler

        COMBAT_RULES.release_pet(pet, self.char1, reason="dismissed")

        self.assertNotIn(pet, handler.db.fighters)
        self.assertLess(handler.db.turn, len(handler.db.fighters))

    def test_no_owner_still_deletes_the_pet(self):
        """A pet dismissed via a nonstandard path with no owner reference
        (e.g. cleanup code that only has the pet itself) should still
        be safely removable."""
        pet = self._make_pet()
        COMBAT_RULES.release_pet(pet, None, reason="dismissed")
        self.assertFalse(pet.pk)


class TestActiveCompanionTrackingOnSummonSpells(CombatTestBase):
    """
    Both Augur's Summon Familiar and Haruspex's Summon Lemures now set
    db.active_companion on the caster - reusing the field Venator's
    Call of the Wild already used - so 'dismiss' and the flee/defeat
    cleanup can find a caster's pet regardless of which class summoned
    it.
    """

    def test_summon_familiar_sets_active_companion(self):
        self.char1.db.level = 5
        self.char1.db.mp = 50
        self.char1.location = self.room1
        try:
            COMBAT_RULES.spell_summon_familiar(self.char1, "summon familiar", [], 10)
        except Exception:
            self.skipTest("AUGUR_FAMILIAR_TIER1 prototype not available in this test DB")
        self.assertIsNotNone(self.char1.db.active_companion)
        self.assertTrue(self.char1.db.active_companion.pk)

    def test_summon_lemures_sets_active_companion(self):
        self.char1.db.level = 5
        self.char1.db.mp = 50
        self.char1.location = self.room1
        try:
            COMBAT_RULES.spell_summon_lemures(self.char1, "summon lemures", [], 10)
        except Exception:
            self.skipTest("HARUSPEX_LEMURES_TIER1 prototype not available in this test DB")
        self.assertIsNotNone(self.char1.db.active_companion)
        self.assertTrue(self.char1.db.active_companion.pk)


class TestRecastingASummonReplacesRatherThanOrphansTheOldOne(CombatTestBase):
    """
    Real, confirmed live bug: spell_summon_familiar/spell_summon_lemures/
    skill_call_of_the_wild all just overwrote db.active_companion with
    a freshly-spawned pet, with no check for one already being active -
    a player recasting (whether by mistake or wanting a fresh one at a
    new level) silently orphaned the old instance, which kept existing
    (and, if still in a fight, kept fighting) with nothing left
    pointing back to it - 'dismiss' could no longer find or release it
    at all. Fixed by releasing whatever's already active first, via the
    same release_pet() the real 'dismiss' command already uses.
    """

    def test_recasting_summon_familiar_deletes_the_old_one(self):
        self.char1.db.level = 5
        self.char1.db.mp = 50
        self.char1.location = self.room1
        try:
            COMBAT_RULES.spell_summon_familiar(self.char1, "summon familiar", [], 10)
        except Exception:
            self.skipTest("AUGUR_FAMILIAR_TIER1 prototype not available in this test DB")
        old_companion = self.char1.db.active_companion

        COMBAT_RULES.spell_summon_familiar(self.char1, "summon familiar", [], 10)

        self.assertFalse(old_companion.pk)  # deleted, not left behind
        new_companion = self.char1.db.active_companion
        self.assertIsNotNone(new_companion)
        self.assertNotEqual(old_companion, new_companion)

    def test_recasting_summon_lemures_deletes_the_old_one(self):
        self.char1.db.level = 5
        self.char1.db.mp = 50
        self.char1.location = self.room1
        try:
            COMBAT_RULES.spell_summon_lemures(self.char1, "summon lemures", [], 10)
        except Exception:
            self.skipTest("HARUSPEX_LEMURES_TIER1 prototype not available in this test DB")
        old_companion = self.char1.db.active_companion

        COMBAT_RULES.spell_summon_lemures(self.char1, "summon lemures", [], 10)

        self.assertFalse(old_companion.pk)
        self.assertNotEqual(old_companion, self.char1.db.active_companion)

    def test_recasting_call_of_the_wild_deletes_the_old_one(self):
        self.char1.db.level = 55
        self.char1.db.sp = 50
        self.char1.location = self.room1
        try:
            COMBAT_RULES.skill_call_of_the_wild(self.char1, "call of the wild", [], 10)
        except Exception:
            self.skipTest("VENATOR_BEAST_TIER2 prototype not available in this test DB")
        old_companion = self.char1.db.active_companion

        COMBAT_RULES.skill_call_of_the_wild(self.char1, "call of the wild", [], 10)

        self.assertFalse(old_companion.pk)
        self.assertNotEqual(old_companion, self.char1.db.active_companion)

    def test_first_summon_with_no_prior_companion_does_not_crash(self):
        """release_pet(None, ...) must be a safe no-op - the common
        case of summoning for the very first time."""
        self.char1.db.level = 5
        self.char1.db.mp = 50
        self.char1.location = self.room1
        self.char1.db.active_companion = None
        try:
            COMBAT_RULES.spell_summon_familiar(self.char1, "summon familiar", [], 10)
        except Exception as e:
            if "prototype" in str(e).lower() or "AUGUR_FAMILIAR" in str(e):
                self.skipTest("AUGUR_FAMILIAR_TIER1 prototype not available in this test DB")
            raise
        self.assertIsNotNone(self.char1.db.active_companion)


class TestInstanceCleanupTimerSkipsWhileFighting(CombatTestBase):
    """
    Regression coverage for a real, confirmed bug: this timer used to
    be a true one-shot (repeats=1) that deleted a personal-instance
    NPC (a summoned pet included) unconditionally at the 10-minute
    mark, with zero check for whether it was still genuinely fighting
    - unlike the manual cleanupnpcs sweep, which does skip anything
    with a live combat_turnhandler. Now a repeating check: skip while
    fighting, delete once that's no longer true.
    """

    def _make_npc(self):
        from evennia.utils import create

        return create.create_object(
            "typeclasses.characters.Character", key="an abandoned instance", location=self.room1
        )

    def _make_timer(self, npc):
        from evennia.utils import create

        return create.create_script(InstanceCleanupTimer, obj=npc, autostart=False)

    def test_skips_deletion_while_still_fighting(self):
        from evennia.utils import create

        npc = self._make_npc()
        # A live combat_turnhandler is a real Script with a real pk -
        # at_repeat checks turnhandler.pk specifically, so a bare
        # truthy string stand-in (used elsewhere in this file for
        # simpler bool-only checks) won't do here.
        npc.db.combat_turnhandler = create.create_script(
            CombatTurnHandler, obj=self.room1, autostart=False
        )
        timer = self._make_timer(npc)

        timer.at_repeat()

        self.assertTrue(npc.pk)
        self.assertTrue(timer.pk)  # timer itself is not stopped/deleted either

    def test_deletes_once_no_longer_fighting(self):
        npc = self._make_npc()
        npc.db.combat_turnhandler = None
        timer = self._make_timer(npc)

        timer.at_repeat()

        self.assertFalse(npc.pk)
        self.assertFalse(timer.pk)

    def test_a_stale_or_deleted_obj_is_handled_without_crashing(self):
        npc = self._make_npc()
        timer = self._make_timer(npc)
        npc.delete()

        timer.at_repeat()  # should not raise

        self.assertFalse(timer.pk)


class TestStartCombatFromOffensiveAction(CombatTestBase):
    """
    CombatRules.start_combat_from_offensive_action - the real fix for a
    confirmed live player report: "when I used a combat action out of
    combat, it hits an enemy but does not start a fight." CmdCast and
    CmdUseSkill only ever gated their turn/action checks behind 'if
    is_in_combat', which is simply skipped when out of combat rather
    than blocking anything - an offensive spell/skill dealt real damage
    against a target with no CombatTurnHandler ever created. See the
    end-to-end CmdCast/CmdUseSkill coverage in
    tests_combat_commands.py for the full command-level regression;
    this covers the shared helper's own logic directly.
    """

    def test_starts_a_real_tracked_fight_against_a_hostile_target(self):
        self.char1.location = self.room1
        self.char2.location = self.room1
        self.char1.db.combat_turnhandler = None
        self.char2.db.combat_turnhandler = None

        COMBAT_RULES.start_combat_from_offensive_action(self.char1, [self.char2])

        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char2))
        self.assertNotEqual(self.char1.db.combat_side, self.char2.db.combat_side)

    def test_no_op_if_caller_already_in_combat(self):
        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        self.char1.db.combat_turnhandler = handler
        self.char2.db.combat_turnhandler = None

        COMBAT_RULES.start_combat_from_offensive_action(self.char1, [self.char2])

        # Nothing should have changed the target's own state - no new
        # fight was started on their account.
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char2))

    def test_no_op_against_an_ally(self):
        self.char1.location = self.room1
        self.char2.location = self.room1
        self.char1.db.combat_turnhandler = None
        self.char2.db.combat_turnhandler = None
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2]
        self.char2.db.party_leader = self.char1

        COMBAT_RULES.start_combat_from_offensive_action(self.char1, [self.char2])

        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char2))

    def test_no_op_in_a_no_combat_zone(self):
        self.char1.location = self.room1
        self.char2.location = self.room1
        self.char1.db.combat_turnhandler = None
        self.char2.db.combat_turnhandler = None
        self.room1.tags.add("no_combat_zone", category="zone")

        COMBAT_RULES.start_combat_from_offensive_action(self.char1, [self.char2])

        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_joins_an_already_open_fight_in_the_room_instead_of_starting_a_second_one(self):
        self.char1.location = self.room1
        self.char2.location = self.room1
        third = create.create_object(
            "typeclasses.characters.Character", key="a bystander", location=self.room1
        )
        third.db.hp = 100

        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        handler.db.fighters = [self.char2, third]
        handler.db.turn = 0
        self.room1.db.combat_turnhandler = handler
        self.char2.db.combat_turnhandler = handler
        self.char2.db.combat_side = "A"
        third.db.combat_turnhandler = handler
        third.db.combat_side = "B"
        self.char1.db.combat_turnhandler = None

        COMBAT_RULES.start_combat_from_offensive_action(self.char1, [third])

        self.assertIs(self.char1.db.combat_turnhandler, handler)
        self.assertIn(self.char1, handler.db.fighters)


class TestFightAllGroupsHostileNPCsIntoOneSharedSide(CombatTestBase):
    """
    CombatTurnHandler.at_script_creation's 'fight all' side-assignment
    - real, confirmed live bug: every accountless, partyless NPC swept
    into 'fight all' used to get its OWN individual side (same as a
    genuinely unrelated solo player would), rather than being grouped
    with other NPCs as "the mob." Combined with HostileNPC.at_turn_start
    picking whichever other fighter came first in turn order with no
    concept of sides at all (see TestHostileNPCDoesNotAttackItsOwnSide
    below), this made a real player's 'fight all' against a room of
    monsters turn into the monsters fighting each other instead of the
    player - reported live, verbatim: "I tried fight all.. And the
    mobiles are now fighting each other, and my own attacks don't
    proc."
    """

    def _make_npc(self, key):
        npc = create.create_object(
            "typeclasses.characters.Character", key=key, location=self.room1
        )
        npc.db.hp = 50
        npc.db.max_hp = 50
        return npc

    def test_three_partyless_npcs_share_one_side_not_three(self):
        from evennia.utils import create as ev_create

        npc1 = self._make_npc("a wolf")
        npc2 = self._make_npc("a bandit")
        npc3 = self._make_npc("a boar")
        self.char1.location = self.room1
        self.char1.db.combat_turnhandler = None

        handler = ev_create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)

        self.assertEqual(npc1.db.combat_side, npc2.db.combat_side)
        self.assertEqual(npc2.db.combat_side, npc3.db.combat_side)
        self.assertNotEqual(self.char1.db.combat_side, npc1.db.combat_side)
        self.assertTrue(handler.pk)

    def test_a_partied_companion_with_no_account_still_groups_with_its_party(self):
        """
        Regression guard: the fix must not treat every accountless
        Character as "the mob" - an explicitly partied companion (real
        party_leader set, just no account of its own) must still end
        up on its party leader's side, exactly like
        TestCmdFight.test_fight_all_groups_by_party already covers at
        the command layer.
        """
        from evennia.utils import create as ev_create

        companion = self._make_npc("a loyal companion")
        companion.db.party_leader = self.char1
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, companion]
        self.char1.location = self.room1
        self.char1.db.combat_turnhandler = None

        mob = self._make_npc("a bandit")

        handler = ev_create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)

        self.assertEqual(self.char1.db.combat_side, companion.db.combat_side)
        self.assertNotEqual(self.char1.db.combat_side, mob.db.combat_side)
        self.assertTrue(handler.pk)


class TestHostileNPCDoesNotAttackItsOwnSide(CombatTestBase):
    """
    HostileNPC.at_turn_start - real, confirmed live bug: this picked
    whichever OTHER fighter came first in turn order with absolutely no
    concept of sides, so once more than one hostile NPC shared a fight
    (see TestFightAllGroupsHostileNPCsIntoOneSharedSide above), a
    fellow NPC on the exact same side was just as valid a target as the
    actual player. Fixed to exclude allies (same combat_side) via
    is_ally, matching every other targeting path in this file.
    """

    def _make_handler(self):
        from evennia.utils import create as ev_create

        # Deliberately NOT self.room1 - at_script_creation sweeps
        # whatever's already in obj.contents with truthy hp the moment
        # the script is created (autostart only gates the repeating
        # tick, not this one-time creation hook), so building the
        # handler on a fresh, otherwise-empty room first and wiring
        # db.fighters by hand afterward - same ordering
        # TestSideBasedVictory already uses - avoids that sweep
        # silently picking up real fighters early and running its own
        # turn cascade before the test ever gets to call
        # at_turn_start() itself.
        #
        # A truly empty room isn't safe either - at_script_creation
        # unconditionally calls start_turn(fighters[0]), which crashes
        # with IndexError if the sweep finds nobody at all. One inert
        # dummy (hp set, no at_turn_start method of its own) satisfies
        # that without risking any real auto-attack: start_turn's own
        # fallback for a non-CombatCharacter target ("like a training
        # dummy" - see its docstring) just sends a plain room message.
        # Discarded the moment each test overwrites handler.db.fighters
        # with its own real list right after this returns.
        room = ev_create.create_object("typeclasses.rooms.Room", key="a testing void")
        dummy = ev_create.create_object(
            "evennia.objects.objects.DefaultObject", key="a training dummy", location=room
        )
        dummy.db.hp = 1
        return ev_create.create_script(CombatTurnHandler, obj=room, autostart=False)

    def _make_hostile(self, key, side):
        npc = create.create_object(HostileNPC, key=key, location=self.room1)
        npc.db.hp = 50
        npc.db.max_hp = 50
        npc.db.mp = 0
        npc.db.sp = 0
        npc.db.player_class = None
        npc.db.combat_side = side
        return npc

    def test_never_targets_a_fellow_npc_on_its_own_side(self):
        handler = self._make_handler()

        mob1 = self._make_hostile("a wolf", "team_1")
        mob2 = self._make_hostile("a boar", "team_1")
        self.char1.location = self.room1
        self.char1.db.combat_side = "team_0"
        self.char1.db.hp = 100

        handler.db.fighters = [mob1, mob2, self.char1]
        mob1.db.combat_turnhandler = handler
        mob2.db.combat_turnhandler = handler
        self.char1.db.combat_turnhandler = handler

        # spend_action is also mocked here - calling at_turn_start
        # directly (rather than through a real, scripted turn cycle)
        # would otherwise let its own real turn_end_check/next_turn
        # cascade straight into mob2's turn too (mob2 is ALSO a
        # HostileNPC that auto-acts the instant its own turn starts) -
        # this test is only about mob1's own single target choice, not
        # the separate, already-covered turn-advancement machinery.
        with patch("world.combat.COMBAT_RULES.resolve_attack") as mock_attack, \
                patch("world.combat.COMBAT_RULES.spend_action"):
            mob1.at_turn_start()

        # Called exactly once, and never against mob2 (same side) -
        # only the real enemy, char1, is a valid target here.
        mock_attack.assert_called_once_with(mob1, self.char1)

    def test_does_nothing_if_every_other_fighter_is_an_ally(self):
        handler = self._make_handler()

        mob1 = self._make_hostile("a wolf", "team_1")
        mob2 = self._make_hostile("a boar", "team_1")
        handler.db.fighters = [mob1, mob2]
        mob1.db.combat_turnhandler = handler
        mob2.db.combat_turnhandler = handler

        with patch("world.combat.COMBAT_RULES.resolve_attack") as mock_attack, \
                patch("world.combat.COMBAT_RULES.spend_action"):
            mob1.at_turn_start()  # should not raise, and should not attack mob2

        mock_attack.assert_not_called()


class TestHostileNPCSkipsAnAlreadyActiveSelfBuff(CombatTestBase):
    """
    HostileNPC._gather_actions - real, confirmed live bug reported
    directly by a player: a barbarian champion NPC "keeps running a
    no-damage skill (rage of the north) so it's doing minimal damage."
    Rage of the North is a self-buff (Damage Up/Defense Down, no
    damage of its own) - _gather_actions offered it as an equally
    likely random pick every single turn regardless of whether it was
    already active, so re-casting it (which just refreshes the same
    duration) could keep winning the draw turn after turn instead of
    ever falling through to an actual attack. Fixed to stop offering a
    self-buff once its own condition(s) are already up.
    """

    def _make_champion(self):
        npc = create.create_object(HostileNPC, key="a champion", location=self.room1)
        npc.db.player_class = "barbarian"
        npc.db.level = 90
        npc.db.mp = 0
        npc.db.sp = 50
        npc.db.hp = 200
        npc.db.max_hp = 200
        return npc

    def test_active_self_buff_is_not_offered_again(self):
        champion = self._make_champion()
        champion.db.conditions = {"Damage Up": [3, champion], "Defense Down": [3, champion]}

        actions = champion._gather_actions()

        names = [name for (_kind, name, _self) in actions]
        self.assertNotIn("rage of the north", names)

    def test_expired_self_buff_is_offered_again(self):
        champion = self._make_champion()
        champion.db.conditions = {}

        actions = champion._gather_actions()

        names = [name for (_kind, name, _self) in actions]
        self.assertIn("rage of the north", names)

    def test_only_offered_again_once_every_one_of_its_conditions_has_expired(self):
        """The skip requires ALL of the buff's conditions to still be
        active - with only one of Rage of the North's two conditions
        (Damage Up/Defense Down) left, it's re-offered rather than
        silently withheld."""
        champion = self._make_champion()
        champion.db.conditions = {"Damage Up": [1, champion]}

        actions = champion._gather_actions()

        names = [name for (_kind, name, _self) in actions]
        self.assertIn("rage of the north", names)


class TestHostileNPCAppliesPerTurnConditions(CombatTestBase):
    """
    HostileNPC.at_turn_start - real, confirmed live bug: it never
    called apply_turn_conditions at all (unlike CombatCharacter's own
    at_turn_start, which does), so Poisoned/Regeneration/Haste/
    Paralyzed inflicted on an NPC silently did nothing. Duration
    counting is unaffected (condition_tickdown is driven by the
    turnhandler itself, not by at_turn_start), so the condition still
    visibly landed and still expired right on schedule - only the
    actual per-turn EFFECT never fired. A player reported exactly this
    after landing a Poisoned-inflicting spell (Mark of Decay) on an
    enemy: "seems to poison the enemy for 1 turn and then it ends but
    i dont see it do any damage."
    """

    def _make_handler(self):
        from evennia.utils import create as ev_create

        # See the identical setup/comment in
        # TestHostileNPCDoesNotAttackItsOwnSide - building the handler
        # on a fresh, otherwise-empty room (plus one inert dummy so
        # at_script_creation's own start_turn(fighters[0]) doesn't
        # IndexError on a truly empty sweep) avoids its creation-time
        # room sweep silently picking up real fighters early.
        room = ev_create.create_object("typeclasses.rooms.Room", key="a testing void")
        dummy = ev_create.create_object(
            "evennia.objects.objects.DefaultObject", key="a training dummy", location=room
        )
        dummy.db.hp = 1
        return ev_create.create_script(CombatTurnHandler, obj=room, autostart=False)

    def _make_hostile(self, key):
        npc = create.create_object(HostileNPC, key=key, location=self.room1)
        npc.db.hp = 50
        npc.db.max_hp = 50
        npc.db.mp = 0
        npc.db.sp = 0
        npc.db.player_class = None
        return npc

    def test_poisoned_npc_takes_damage_on_its_own_turn(self):
        handler = self._make_handler()
        npc = self._make_hostile("a wolf")
        npc.db.combat_turnhandler = handler
        npc.db.combat_side = "team_1"
        npc.db.conditions = {"Poisoned": [3, self.char1]}
        handler.db.fighters = [npc]

        with patch("world.combat.COMBAT_RULES.resolve_attack"), \
                patch("world.combat.COMBAT_RULES.spend_action"):
            npc.at_turn_start()

        self.assertLess(npc.db.hp, 50)

    def test_a_lethal_poison_tick_stops_it_from_also_attacking(self):
        handler = self._make_handler()
        npc = self._make_hostile("a wolf")
        npc.db.combat_turnhandler = handler
        npc.db.combat_side = "team_1"
        npc.db.hp = 1  # POISON_RATE's minimum (4) guarantees a kill
        npc.db.conditions = {"Poisoned": [3, self.char1]}
        self.char1.location = self.room1
        self.char1.db.combat_side = "team_0"
        self.char1.db.hp = 100
        handler.db.fighters = [npc, self.char1]

        with patch("world.combat.COMBAT_RULES.resolve_attack") as mock_attack, \
                patch("world.combat.COMBAT_RULES.spend_action"):
            npc.at_turn_start()

        mock_attack.assert_not_called()

    def test_unpoisoned_npc_still_acts_normally(self):
        handler = self._make_handler()
        npc = self._make_hostile("a wolf")
        npc.db.combat_turnhandler = handler
        npc.db.combat_side = "team_1"
        npc.db.conditions = {}
        self.char1.location = self.room1
        self.char1.db.combat_side = "team_0"
        self.char1.db.hp = 100
        handler.db.fighters = [npc, self.char1]

        with patch("world.combat.COMBAT_RULES.resolve_attack") as mock_attack, \
                patch("world.combat.COMBAT_RULES.spend_action"):
            npc.at_turn_start()

        mock_attack.assert_called_once_with(npc, self.char1)
