"""
Tests for the level-scaled weapon/armor generation formulas
(compute_weapon_stats, compute_armor_stats) and the data integrity of
WEAPON_SUBTYPES/WEAPON_CATEGORIES/ARMOR_CATEGORIES.

Pure math, no database dependency - imports the real functions directly
from world.combat rather than duplicating their logic inline, per the
working-conventions note in CLAUDE.md.
"""

import unittest

from world.combat import (
    WEAPON_CATEGORIES,
    WEAPON_SUBTYPES,
    ARMOR_CATEGORIES,
    ARMOR_MITIGATION_TARGET,
    compute_weapon_stats,
    compute_armor_stats,
)


class TestWeaponSubtypeIntegrity(unittest.TestCase):
    """Every subtype must point at a real category - a typo here would
    otherwise only surface as a live KeyError the first time someone
    spawns that weapon type."""

    def test_every_subtype_category_exists(self):
        for subtype, info in WEAPON_SUBTYPES.items():
            self.assertIn(
                info["category"],
                WEAPON_CATEGORIES,
                "weapon subtype %r references unknown category %r" % (subtype, info["category"]),
            )


class TestComputeWeaponStats(unittest.TestCase):
    def test_dagger_level_1_matches_hand_calculation(self):
        (min_dmg, max_dmg), accuracy, price = compute_weapon_stats("dagger", 1)
        # base_min = 7 + 1*1.3 = 8.3, base_max = 14 + 1*2.1 = 16.1
        # light_blade mult 1.0 * dagger mult 0.91
        self.assertEqual((min_dmg, max_dmg), (8, 15))
        self.assertEqual(accuracy, 30)  # light_blade 25 + dagger offset 5

    def test_gladius_level_1_is_distinct_from_dagger(self):
        (dagger_min, dagger_max), dagger_acc, _ = compute_weapon_stats("dagger", 1)
        (gladius_min, gladius_max), gladius_acc, _ = compute_weapon_stats("gladius", 1)
        # Same category (light_blade), different subtype deltas - the
        # whole point of Option A was that these must NOT collapse to
        # identical numbers.
        self.assertNotEqual((dagger_min, dagger_max), (gladius_min, gladius_max))
        self.assertNotEqual(dagger_acc, gladius_acc)
        # Gladius hits harder, Dagger is more accurate - matches the
        # real, already-live data this system was calibrated against.
        self.assertGreater(gladius_max, dagger_max)
        self.assertGreater(dagger_acc, gladius_acc)

    def test_accuracy_never_scales_with_level(self):
        _, acc_low, _ = compute_weapon_stats("waraxe", 1)
        _, acc_high, _ = compute_weapon_stats("waraxe", 100)
        self.assertEqual(acc_low, acc_high)

    def test_damage_increases_with_level(self):
        for subtype in WEAPON_SUBTYPES:
            (min1, max1), _, _ = compute_weapon_stats(subtype, 1)
            (min50, max50), _, _ = compute_weapon_stats(subtype, 50)
            self.assertGreater(min50, min1, "min damage didn't grow for %r" % subtype)
            self.assertGreater(max50, max1, "max damage didn't grow for %r" % subtype)
            self.assertLessEqual(min50, max50)

    def test_unknown_subtype_raises(self):
        with self.assertRaises(KeyError):
            compute_weapon_stats("not-a-real-weapon", 1)


class TestComputeArmorStats(unittest.TestCase):
    def test_defense_modifier_always_mirrors_reduction(self):
        for category in ARMOR_CATEGORIES:
            for level in (1, 25, 50, 100):
                reduction, defense_modifier, _ = compute_armor_stats(category, level)
                self.assertEqual(defense_modifier, -reduction)

    def test_categories_stay_distinct_at_every_level(self):
        for level in (1, 25, 50, 100):
            light, _, _ = compute_armor_stats("light", level)
            medium, _, _ = compute_armor_stats("medium", level)
            heavy, _, _ = compute_armor_stats("heavy", level)
            # Regression guard for the exact bug found while designing
            # this system: a pure multiplier collapsed light/medium/
            # heavy to identical values at level 1 due to rounding.
            self.assertLess(light, medium, "light/medium collapsed at level %d" % level)
            self.assertLess(medium, heavy, "medium/heavy collapsed at level %d" % level)

    def test_reduction_grows_with_level(self):
        low, _, _ = compute_armor_stats("medium", 1)
        high, _, _ = compute_armor_stats("medium", 100)
        self.assertGreater(high, low)


class TestMitigationRatioStaysProportional(unittest.TestCase):
    """
    The actual bug this whole armor formula exists to fix: under the
    old (round(1 + level*0.15) + offset) formula, medium armor's
    mitigation against a light_blade hit dropped from ~19% at level 1
    to ~4.5% at level 100. Confirms the new formula keeps that ratio
    essentially flat across the same range instead.
    """

    def test_mitigation_ratio_is_stable_across_levels(self):
        ratios = []
        for level in (1, 25, 50, 75, 100):
            reduction, _, _ = compute_armor_stats("medium", level)
            (_, max_dmg), _, _ = compute_weapon_stats("dagger", level)
            ratios.append(reduction / max_dmg)

        # Every ratio should be close to the design target
        # (ARMOR_MITIGATION_TARGET), not just close to each other -
        # guards against both drift AND a miscalibrated target.
        for ratio in ratios:
            self.assertAlmostEqual(ratio, ARMOR_MITIGATION_TARGET, delta=0.03)

        # And the spread across the whole level range should be tiny -
        # this is the actual regression guard for the drift bug.
        self.assertLess(max(ratios) - min(ratios), 0.03)


if __name__ == "__main__":
    unittest.main()
