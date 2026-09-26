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


class TestScalingStartsAtEachSpellsOwnUnlockLevel(EvenniaTest):
    """
    Every damaging spell grows with level from the level it's learned at
    (capped at the shared level-20 anchor) - a level-1 spell no longer sits
    flat until level 20. Owner requirement: "ALL damage spells should scale
    with level including level 1 spells."
    """

    def _at(self, level, authored, spell):
        self.char1.db.level = level
        return scale_spell_damage_range(self.char1, authored, spell_name=spell)

    def test_magic_missile_is_as_authored_at_level_one_and_grows_from_there(self):
        from world.combat import SPELLS

        authored = SPELLS["magic arrow"]["damage_range"]
        self.assertEqual(self._at(1, authored, "magic arrow"), authored)
        low = self._at(10, authored, "magic arrow")
        high = self._at(40, authored, "magic arrow")
        self.assertGreater(low[1], authored[1])
        self.assertGreater(high[1], low[1])

    def test_every_damaging_spell_is_as_authored_at_its_own_unlock_level(self):
        from world.combat import SPELLS

        for name, data in SPELLS.items():
            authored = data.get("damage_range")
            if not authored:
                continue
            # A spell's authored range is what it does at its own unlock
            # level, or at the shared anchor level if it unlocks above that.
            tuned_for = min(data["level_required"], SPELL_DAMAGE_ANCHOR_LEVEL)
            self.assertEqual(self._at(tuned_for, authored, name), authored, name)

    def test_every_damaging_spell_never_shrinks_as_level_rises(self):
        from world.combat import SPELLS

        for name, data in SPELLS.items():
            authored = data.get("damage_range")
            if not authored:
                continue
            previous = (0, 0)
            for level in range(min(data["level_required"], SPELL_DAMAGE_ANCHOR_LEVEL), MAX_LEVEL + 1):
                current = self._at(level, authored, name)
                self.assertGreaterEqual(current[1], previous[1], (name, level))
                previous = current

    def test_spells_unlocked_at_or_above_the_anchor_are_unchanged_by_the_new_rule(self):
        # Ritual Flame unlocks at the anchor level itself: the same numbers
        # as before the per-spell rule existed, at every level.
        for level in (20, 40, 60, 100):
            self.assertEqual(
                self._at(level, RITUAL_FLAME, "ritual flame"),
                scale_spell_damage_range(self._caster(level), RITUAL_FLAME),
            )

    def _caster(self, level):
        self.char1.db.level = level
        return self.char1

    def test_magic_missile_stays_well_below_divine_judgment_at_every_level(self):
        from world.combat import SPELLS

        for level in (15, 30, 60, 100):
            mm = sum(self._at(level, SPELLS["magic arrow"]["damage_range"], "magic arrow"))
            dj = sum(self._at(level, SPELLS["divine judgment"]["damage_range"], "divine judgment"))
            self.assertLess(mm, dj, level)

    def test_an_npc_caster_is_still_never_scaled(self):
        from world.combat import AutoStatNPC

        npc = create.create_object(AutoStatNPC, key="a hedge wizard", location=self.room1)
        npc.db.level = 60
        self.assertEqual(scale_spell_damage_range(npc, (4, 6), spell_name="magic arrow"), (4, 6))
