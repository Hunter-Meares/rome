"""
Tests for character creation: race/class data integrity, the
_leans_caster synergy-hint logic, and _apply_race_and_class's actual
stat math.

Per the working-conventions note in CLAUDE.md, this imports the real
functions directly from world.chargen_menu rather than duplicating
their logic inline - keeping these tests honest against the real
code, not a hand-copied mirror of it that can silently drift.
"""

from itertools import product

from evennia.utils.test_resources import EvenniaTest

from world.chargen_menu import (
    RACES,
    CLASSES,
    _RACE_ORDER,
    _CLASS_ORDER,
    _leans_caster,
    _apply_race_and_class,
)
from world.combat import SPELLS, SKILLS


class TestLeansCaster(EvenniaTest):
    """
    Regression coverage for the two real bugs CLAUDE.md documents
    against this function: a fully-balanced entry (Human) incorrectly
    resolving to "physical" via tuple tiebreak order, and a *partial*
    tie (Centaur's Virtus/Agilitas) hitting the same bug in a
    narrower form. Also runs every real race x class combo in the
    live data, per the "test against all 48 combos" instruction.
    """

    def test_all_stats_equal_is_none(self):
        self.assertIsNone(_leans_caster({"virtus": 0, "agilitas": 0, "ingenium": 0, "vigor": 0}))

    def test_all_stats_equal_nonzero_is_none(self):
        self.assertIsNone(_leans_caster({"virtus": 5, "agilitas": 5, "ingenium": 5, "vigor": 5}))

    def test_partial_tie_at_top_is_none(self):
        # Centaur: virtus=2, agilitas=2 tied for highest, ingenium=0 lower.
        self.assertIsNone(_leans_caster({"virtus": 2, "agilitas": 2, "ingenium": 0, "vigor": 0}))

    def test_partial_tie_not_at_top_resolves_normally(self):
        # A tie for SECOND place shouldn't affect the real winner.
        self.assertFalse(
            _leans_caster({"virtus": 3, "agilitas": 1, "ingenium": 1, "vigor": 0})
        )

    def test_clear_physical_lean(self):
        self.assertFalse(_leans_caster({"virtus": 3, "agilitas": 0, "ingenium": 0, "vigor": 0}))
        self.assertFalse(_leans_caster({"virtus": 0, "agilitas": 3, "ingenium": 0, "vigor": 0}))
        self.assertFalse(_leans_caster({"virtus": 0, "agilitas": 0, "ingenium": 0, "vigor": 3}))

    def test_clear_caster_lean(self):
        self.assertTrue(_leans_caster({"virtus": 0, "agilitas": 0, "ingenium": 3, "vigor": 0}))

    def test_two_way_tie_at_top_including_ingenium_is_none(self):
        # A genuine tie between ingenium and something else at the top
        # must NOT resolve to True just because ingenium participates.
        self.assertIsNone(_leans_caster({"virtus": 0, "agilitas": 2, "ingenium": 2, "vigor": 0}))

    def test_missing_keys_default_to_zero(self):
        # Class stat_mods dicts don't always carry max_hp/mp/sp keys -
        # _leans_caster must not KeyError on a sparse dict.
        self.assertIsNone(_leans_caster({}))

    def test_every_real_race_and_class_combo_runs_without_error(self):
        """
        Every one of the 6 races x 8 classes = 48 real combinations
        must resolve without raising, and the race/class synergy-hint
        comparison (race_caster != class_caster, both not None) must
        itself not raise for any combo either - this is the exact
        code path exercised by _set_class when a player finishes
        picking their class.
        """
        combos = list(product(_RACE_ORDER, _CLASS_ORDER))
        self.assertEqual(len(combos), 48)
        for race_key, class_key in combos:
            race_caster = _leans_caster(RACES[race_key]["stat_mods"])
            class_caster = _leans_caster(CLASSES[class_key]["stat_mods"])
            # Just needs to not raise, and be one of the 3 valid values.
            self.assertIn(race_caster, (True, False, None))
            self.assertIn(class_caster, (True, False, None))

    def test_known_real_mismatches_are_flagged(self):
        """
        Spot-check a couple of real, current race/class pairings that
        SHOULD trigger the synergy hint (genuinely different leanings)
        and a couple that should NOT (same leaning, or either side
        undetermined) - locks in the actual current behavior for real
        game data, not just synthetic stat dicts.
        """
        # Cyclops (physical) + Augur (caster) - a real mismatch.
        cyclops_caster = _leans_caster(RACES["cyclops"]["stat_mods"])
        augur_caster = _leans_caster(CLASSES["augur"]["stat_mods"])
        self.assertFalse(cyclops_caster)
        self.assertTrue(augur_caster)
        self.assertNotEqual(cyclops_caster, augur_caster)

        # Nymph (caster-leaning) + Medicus (caster-leaning) - no mismatch.
        nymph_caster = _leans_caster(RACES["nymph"]["stat_mods"])
        medicus_caster = _leans_caster(CLASSES["medicus"]["stat_mods"])
        self.assertTrue(nymph_caster)
        self.assertTrue(medicus_caster)
        self.assertEqual(nymph_caster, medicus_caster)

        # Human (balanced/None) + any class - never flagged, since
        # _set_class only fires the hint when BOTH sides resolve.
        human_caster = _leans_caster(RACES["human"]["stat_mods"])
        self.assertIsNone(human_caster)


class TestRaceClassDataIntegrity(EvenniaTest):
    """
    Data-integrity checks on the RACES/CLASSES dicts themselves -
    catches the exact class of bug CLAUDE.md flags repeatedly
    (referencing a spell/skill/prototype key that doesn't actually
    exist anywhere, silently doing nothing at chargen time instead of
    failing loudly).
    """

    def test_race_order_matches_races_dict(self):
        self.assertEqual(set(_RACE_ORDER), set(RACES.keys()))

    def test_class_order_matches_classes_dict(self):
        self.assertEqual(set(_CLASS_ORDER), set(CLASSES.keys()))

    def test_every_race_stat_mods_has_all_four_core_stats(self):
        for race_key, race in RACES.items():
            for stat in ("virtus", "agilitas", "ingenium", "vigor"):
                self.assertIn(
                    stat, race["stat_mods"],
                    "Race '%s' is missing '%s' in stat_mods" % (race_key, stat),
                )

    def test_every_race_stat_mods_has_hp_mp_sp(self):
        for race_key, race in RACES.items():
            for stat in ("max_hp", "max_mp", "max_sp"):
                self.assertIn(
                    stat, race["stat_mods"],
                    "Race '%s' is missing '%s' in stat_mods" % (race_key, stat),
                )

    def test_no_single_stat_mod_exceeds_documented_ceiling(self):
        """
        CLAUDE.md states the real ceiling is base 10 + best race (+3)
        + best class (+3) = 16, and that no stat mod anywhere exceeds
        +3 individually. Locks that invariant in so a future data
        edit can't silently break the documented balance ceiling.
        """
        for race_key, race in RACES.items():
            for stat in ("virtus", "agilitas", "ingenium", "vigor"):
                self.assertLessEqual(
                    race["stat_mods"][stat], 3,
                    "Race '%s' stat '%s' exceeds +3" % (race_key, stat),
                )
        for class_key, pclass in CLASSES.items():
            for stat in ("virtus", "agilitas", "ingenium", "vigor"):
                self.assertLessEqual(
                    pclass["stat_mods"].get(stat, 0), 3,
                    "Class '%s' stat '%s' exceeds +3" % (class_key, stat),
                )

    def test_every_class_starting_spell_exists_in_spells_dict(self):
        for class_key, pclass in CLASSES.items():
            for spell_name in pclass.get("starting_spells", []):
                self.assertIn(
                    spell_name, SPELLS,
                    "Class '%s' starting_spells references unknown spell '%s'"
                    % (class_key, spell_name),
                )

    def test_every_class_starting_skill_exists_in_skills_dict(self):
        for class_key, pclass in CLASSES.items():
            for skill_name in pclass.get("starting_skills", []):
                self.assertIn(
                    skill_name, SKILLS,
                    "Class '%s' starting_skills references unknown skill '%s'"
                    % (class_key, skill_name),
                )

    def test_every_class_starting_gear_prototype_exists(self):
        import world.prototypes as prototypes_module

        for class_key, pclass in CLASSES.items():
            for prototype_name in pclass.get("starting_gear", []):
                self.assertTrue(
                    hasattr(prototypes_module, prototype_name),
                    "Class '%s' starting_gear references unknown prototype '%s'"
                    % (class_key, prototype_name),
                )


class TestApplyRaceAndClass(EvenniaTest):
    """
    Exercises _apply_race_and_class against a real Character object -
    this is the actual mechanical effect of chargen (stat bonuses,
    derived HP/MP, starting gear/spells), not just the data feeding
    into it.
    """

    def test_human_baseline_gets_no_stat_changes(self):
        """Human has all-zero stat_mods - baseline 10s should survive untouched."""
        char = self.char1
        char.db.race = "human"
        char.db.player_class = "augur"  # only class stat_mods (ingenium+3) apply
        _apply_race_and_class(char)

        self.assertEqual(char.db.virtus, 10)
        self.assertEqual(char.db.agilitas, 10)
        self.assertEqual(char.db.ingenium, 13)  # +3 from Augur class only
        self.assertEqual(char.db.vigor, 10)

    def test_cyclops_legionary_stacks_race_and_class_vigor(self):
        """
        Cyclops (+2 vigor) + Legionary (+3 vigor) should stack to +5
        over baseline, and max_hp should reflect both the race's flat
        max_hp bonus AND the derived (vigor-10)*2 bonus on top of it -
        exactly the "tankier than the flat number alone" case
        CLAUDE.md calls out.
        """
        char = self.char1
        char.db.race = "cyclops"
        char.db.player_class = "legionary"
        base_max_hp_before = 100  # EvenniaTest default from at_object_creation

        _apply_race_and_class(char)

        self.assertEqual(char.db.vigor, 10 + 2 + 3)  # 15
        expected_max_hp = base_max_hp_before + 30 + (15 - 10) * 2
        self.assertEqual(char.db.max_hp, expected_max_hp)
        # hp/mp/sp should be topped off to the new max after chargen.
        self.assertEqual(char.db.hp, char.db.max_hp)
        self.assertEqual(char.db.mp, char.db.max_mp)
        self.assertEqual(char.db.sp, char.db.max_sp)

    def test_stat_ceiling_respected_for_max_investment_combo(self):
        """
        Minotaur (+3 virtus) + Barbarian (+3 virtus) is the real
        maximum-single-stat combo - should land exactly at the
        documented ceiling of 16, not higher.
        """
        char = self.char1
        char.db.race = "minotaur"
        char.db.player_class = "barbarian"
        _apply_race_and_class(char)
        self.assertEqual(char.db.virtus, 16)

    def test_starting_gear_is_spawned_and_equipped(self):
        char = self.char1
        char.db.race = "human"
        char.db.player_class = "legionary"
        _apply_race_and_class(char)

        self.assertIsNotNone(char.db.wielded_weapon)
        self.assertEqual(char.db.wielded_weapon.key, "an iron broadsword")
        self.assertIsNotNone(char.db.worn_armor)
        self.assertEqual(char.db.worn_armor.key, "a suit of plate mail")

    def test_starting_spells_and_skills_are_learned(self):
        char = self.char1
        char.db.race = "human"
        char.db.player_class = "medicus"
        _apply_race_and_class(char)

        for spell in ("cure wounds", "field dressing", "antidote"):
            self.assertIn(spell, char.db.spells_known)

    def test_no_duplicate_starting_spells_on_repeated_apply(self):
        """
        _apply_race_and_class guards with 'if spell_name not in
        spells_known' - if that guard were ever removed, calling this
        twice (which shouldn't normally happen, but is easy to trigger
        via a chargen bug/retry) would silently double up entries.
        """
        char = self.char1
        char.db.race = "human"
        char.db.player_class = "medicus"
        _apply_race_and_class(char)
        _apply_race_and_class(char)
        self.assertEqual(char.db.spells_known.count("cure wounds"), 1)
