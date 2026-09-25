"""
Tests for spell damage scaling with caster level
(world/combat.py's scale_spell_damage_range / weapon_base_average).

A real player report (Sep 18, "ritual flame does 40 damage, my melee
does 50... no magic really scaled") was confirmed: damaging spells were
a flat authored range plus a small Ingenium bonus, never growing with
level, while a same-level weapon roughly triples in damage between
level 20 and level 60. Kept in its own small file (the big combat
files take ~10 minutes to run) since it only needs a couple of
characters.
"""

from unittest import mock

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from world.combat import (
    COMBAT_RULES,
    MAX_LEVEL,
    SPELL_DAMAGE_ANCHOR_LEVEL,
    compute_weapon_stats,
    scale_spell_damage_range,
    weapon_base_average,
)

RITUAL_FLAME = (25, 35)


class TestWeaponCurveIsUnchangedByTheRefactor(EvenniaTest):
    def test_known_weapon_values_still_hold(self):
        # Pinned to values computed before the growth constants were
        # pulled out into shared names - a drift here would silently
        # rebalance every weapon in the game.
        self.assertEqual(compute_weapon_stats("gladius", 10)[0], (22, 38))
        self.assertEqual(compute_weapon_stats("gladius", 20)[0], (36, 61))
        self.assertEqual(compute_weapon_stats("gladius", 60)[0], (93, 153))


class TestScaleSpellDamageRange(EvenniaTest):
    def _caster(self, level):
        self.char1.db.level = level
        return self.char1

    def test_unchanged_at_and_below_the_anchor_level(self):
        for level in (1, 10, SPELL_DAMAGE_ANCHOR_LEVEL):
            self.assertEqual(
                scale_spell_damage_range(self._caster(level), RITUAL_FLAME), RITUAL_FLAME
            )

    def test_grows_with_level_above_the_anchor(self):
        low = scale_spell_damage_range(self._caster(40), RITUAL_FLAME)
        high = scale_spell_damage_range(self._caster(60), RITUAL_FLAME)
        self.assertGreater(low[0], RITUAL_FLAME[0])
        self.assertGreater(high[0], low[0])
        self.assertGreater(high[1], low[1])

    def test_never_decreases_as_level_rises(self):
        previous = (0, 0)
        for level in range(1, MAX_LEVEL + 1):
            current = scale_spell_damage_range(self._caster(level), RITUAL_FLAME)
            self.assertGreaterEqual(current[0], previous[0])
            self.assertGreaterEqual(current[1], previous[1])
            previous = current

    def test_keeps_pace_with_melee_instead_of_falling_further_behind(self):
        # The report's actual complaint: melee tripled while spells
        # stayed flat. The spell-to-weapon ratio at level 60 should now
        # match the ratio at the anchor level (within rounding).
        def ratio(level):
            spell = sum(scale_spell_damage_range(self._caster(level), RITUAL_FLAME)) / 2
            return spell / weapon_base_average(level)

        self.assertAlmostEqual(ratio(60), ratio(SPELL_DAMAGE_ANCHOR_LEVEL), delta=0.02)

    def test_level_is_capped_at_max_level(self):
        self.assertEqual(
            scale_spell_damage_range(self._caster(MAX_LEVEL + 50), RITUAL_FLAME),
            scale_spell_damage_range(self._caster(MAX_LEVEL), RITUAL_FLAME),
        )

    def test_npc_casters_are_deliberately_not_scaled(self):
        # Scaling NPC casters by their own level would make every
        # existing NPC caster far deadlier - out of scope on purpose.
        npc = create.create_object("typeclasses.characters.Character", key="a test caster")
        npc.db.level = 90
        self.assertIsNone(getattr(npc, "account", None))
        self.assertEqual(scale_spell_damage_range(npc, RITUAL_FLAME), RITUAL_FLAME)


class TestSpellAttackUsesTheScaledRange(EvenniaTest):
    def test_a_high_level_casters_hit_is_bigger_than_a_low_level_ones(self):
        def max_hit_at(level):
            self.char1.db.level = level
            self.char1.db.ingenium = 10  # no stat bonus - isolate the level scaling
            self.char1.db.mp = 1000
            self.char2.db.hp = self.char2.db.max_hp = 10**6
            # randint(a, b) -> b: attack roll 100 always connects, and
            # the damage roll lands on the top of the (scaled) range.
            with mock.patch("world.combat.randint", side_effect=lambda a, b: b):
                COMBAT_RULES.spell_attack(
                    self.char1, "ritual flame", [self.char2], 3, damage_range=RITUAL_FLAME
                )
            dealt = 10**6 - self.char2.db.hp
            self.char2.db.hp = 10**6
            return dealt

        low, high = max_hit_at(20), max_hit_at(60)
        self.assertEqual(low, RITUAL_FLAME[1])
        self.assertGreater(high, low * 2)
