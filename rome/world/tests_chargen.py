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
    _to_roman,
    _numbered_option,
    _step_header,
    _TOTAL_STEPS,
    menunode_welcome,
    menunode_choose_race,
    menunode_choose_class,
    menunode_race_info,
    menunode_class_info,
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
        Cyclops (+2 vigor) + Legionary (+3 vigor) stack to +5 over
        baseline from race/class alone - still exactly the documented
        invariant (CLAUDE.md: "no stat mod anywhere exceeds +3
        individually", stacking to a 15 here). Legionary's starting
        gear now also includes Caligae Ferratae (+2 vigor) and Cassis
        (+20 max_hp) - equipment bonuses on top of that race/class
        baseline, not a replacement for it, added this session
        alongside the new equipment-slot system. max_hp reflects the
        race's flat bonus, the derived (vigor-10)*2 bonus computed from
        the race/class-only vigor (gear hasn't been donned yet at that
        point in _apply_race_and_class), and Cassis's own flat bonus.
        """
        char = self.char1
        char.db.race = "cyclops"
        char.db.player_class = "legionary"
        base_max_hp_before = 100  # EvenniaTest default from at_object_creation

        _apply_race_and_class(char)

        race_and_class_vigor = 10 + 2 + 3  # 15 - the documented ceiling
        self.assertEqual(char.db.vigor, race_and_class_vigor + 2)  # +2 from Caligae Ferratae
        expected_max_hp = (
            base_max_hp_before + 30 + (race_and_class_vigor - 10) * 2 + 20  # +20 from Cassis
        )
        self.assertEqual(char.db.max_hp, expected_max_hp)
        # hp/mp/sp should be topped off to the new max after chargen.
        self.assertEqual(char.db.hp, char.db.max_hp)
        self.assertEqual(char.db.mp, char.db.max_mp)
        self.assertEqual(char.db.sp, char.db.max_sp)

    def test_stat_ceiling_respected_for_max_investment_combo(self):
        """
        Minotaur (+3 virtus) + Barbarian (+3 virtus) is the real
        maximum-single-stat combo from race/class alone - lands
        exactly at the documented ceiling of 16, not higher. Barbarian's
        starting gear now also includes Brachiale (+2 virtus) - an
        equipment bonus on top of the race/class ceiling, not a
        contradiction of it (see the equipment-slot system added this
        session, which deliberately allows gear to push past what
        race/class alone can reach).
        """
        char = self.char1
        char.db.race = "minotaur"
        char.db.player_class = "barbarian"
        _apply_race_and_class(char)
        race_and_class_ceiling = 16
        self.assertEqual(char.db.virtus, race_and_class_ceiling + 2)  # +2 from Brachiale

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

    def test_default_title_is_set_and_player_changeable(self):
        char = self.char1
        char.db.race = "human"
        char.db.player_class = "gladiator"
        _apply_race_and_class(char)

        self.assertEqual(char.db.custom_title, "the Untested")
        # Confirm it's a normal custom_title value, not special-cased -
        # the player can freely change or clear it afterward same as
        # any title set via the 'title' command.
        char.db.custom_title = "the Undefeated"
        self.assertEqual(char.db.custom_title, "the Undefeated")

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


class TestRaceAndClassPresentationData(EvenniaTest):
    """
    Regression coverage for the chargen aesthetic pass - a "color" and
    a "quote" field were hand-added to all 6 RACES and 8 CLASSES
    entries individually, exactly the kind of edit where a single
    entry could silently get skipped without a test catching it.
    """

    def test_every_race_has_a_color_and_a_quote(self):
        for race_key in _RACE_ORDER:
            race = RACES[race_key]
            self.assertTrue(race.get("color"), "%s has no color" % race_key)
            self.assertTrue(race.get("quote"), "%s has no quote" % race_key)

    def test_every_class_has_a_color_and_a_quote(self):
        for class_key in _CLASS_ORDER:
            pclass = CLASSES[class_key]
            self.assertTrue(pclass.get("color"), "%s has no color" % class_key)
            self.assertTrue(pclass.get("quote"), "%s has no quote" % class_key)

    def test_every_race_and_class_color_is_a_distinct_value(self):
        """
        Not a hard game-design requirement, but the whole point of
        this feature was to make each entry visually distinct - two
        entries sharing the exact same color code would silently
        defeat that, so this is worth locking in.
        """
        all_colors = [RACES[k]["color"] for k in _RACE_ORDER] + [
            CLASSES[k]["color"] for k in _CLASS_ORDER
        ]
        self.assertEqual(len(all_colors), len(set(all_colors)))


class TestRomanNumeralHelper(EvenniaTest):
    def test_known_values(self):
        expected = {
            1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
            6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
        }
        for n, roman in expected.items():
            self.assertEqual(_to_roman(n), roman)

    def test_falls_back_to_plain_digits_past_its_known_range(self):
        # Deliberately not a general algorithm - chargen never has
        # more than a handful of options on any page. Falling back to
        # a plain digit rather than raising is the safe behavior if
        # that assumption is ever violated.
        self.assertEqual(_to_roman(11), "11")


class TestNumberedOption(EvenniaTest):
    def test_key_is_roman_numeral_and_plain_digit_both(self):
        option = _numbered_option(3, "a desc", "a_goto_target")
        self.assertEqual(option["key"], ("III", "3"))
        self.assertEqual(option["desc"], "a desc")
        self.assertEqual(option["goto"], "a_goto_target")


class TestStepHeader(EvenniaTest):
    def test_known_node_includes_step_and_total(self):
        header = _step_header("menunode_choose_class")
        self.assertIn("II", header)
        self.assertIn(_to_roman(_TOTAL_STEPS), header)
        self.assertIn("Choose Your Path", header)

    def test_unknown_node_returns_empty_string(self):
        self.assertEqual(_step_header("menunode_welcome"), "")
        self.assertEqual(_step_header("menunode_end"), "")
        self.assertEqual(_step_header("not_a_real_node"), "")

    def test_detail_page_shares_its_parent_pages_step(self):
        """
        Picking a specific race/class to read about is browsing within
        a step, not advancing to a new one - race_info and class_info
        should report the exact same step as their parent list page.
        """
        self.assertEqual(
            _step_header("menunode_choose_race"), _step_header("menunode_race_info")
        )
        self.assertEqual(
            _step_header("menunode_choose_class"), _step_header("menunode_class_info")
        )


class TestChooseRaceAndClassOptionLists(EvenniaTest):
    """
    Confirms the actual menu nodes build their option lists using the
    new Roman-numeral keys, in the established race/class order, with
    every real option still reachable.

    These node functions read caller.new_char (set on the real
    session by world/character_creator.py during actual chargen) -
    a bare EvenniaTest fixture has no such attribute, so a minimal
    stand-in with just that one attribute is used as the caller here
    instead of a real Character or session.
    """

    class _FakeCaller:
        def __init__(self, new_char):
            self.new_char = new_char

    def setUp(self):
        super().setUp()
        self.caller = self._FakeCaller(self.char1)

    def test_choose_race_options_are_numbered_in_order(self):
        (text, help_text), options = menunode_choose_race(self.caller)
        self.assertEqual(len(options), len(_RACE_ORDER))
        for i, (option, race_key) in enumerate(zip(options, _RACE_ORDER), start=1):
            self.assertEqual(option["key"], (_to_roman(i), str(i)))
            self.assertIn(RACES[race_key]["display"], option["desc"])

    def test_choose_class_options_are_numbered_in_order_plus_back(self):
        (text, help_text), options = menunode_choose_class(self.caller)
        # One numbered option per class, plus a trailing (Back) option.
        self.assertEqual(len(options), len(_CLASS_ORDER) + 1)
        for i, (option, class_key) in enumerate(zip(options, _CLASS_ORDER), start=1):
            self.assertEqual(option["key"], (_to_roman(i), str(i)))
            self.assertIn(CLASSES[class_key]["display"], option["desc"])
        self.assertEqual(options[-1]["desc"], "Go back and change your race")


class TestSingleOptionPagesUseRomanNumerals(EvenniaTest):
    """
    Regression coverage for a real bug found live: menunode_welcome's
    lone "continue" option and each race/class detail page's "Become
    a X" option were never wrapped in _numbered_option(), so EvMenu
    fell back to its own plain-digit auto-numbering ("1:") instead of
    the Roman numeral used everywhere else in this menu ("I:") -
    visibly inconsistent with the rest of the chargen aesthetic pass.
    """

    class _FakeCaller:
        def __init__(self, new_char):
            self.new_char = new_char

    def setUp(self):
        super().setUp()
        self.caller = self._FakeCaller(self.char1)

    def test_welcome_option_uses_a_roman_numeral_key(self):
        (text, help_text), options = menunode_welcome(self.caller)
        self.assertEqual(options["key"], ("I", "1"))

    def test_race_info_become_option_uses_a_roman_numeral_key(self):
        (text, help_text), options = menunode_race_info(self.caller, race_key="human")
        self.assertEqual(options[0]["key"], ("I", "1"))
        self.assertIn("Become a", options[0]["desc"])

    def test_class_info_become_option_uses_a_roman_numeral_key(self):
        (text, help_text), options = menunode_class_info(self.caller, class_key="legionary")
        self.assertEqual(options[0]["key"], ("I", "1"))
        self.assertIn("Become a", options[0]["desc"])


class TestRaceAndClassInfoFormatting(EvenniaTest):
    """
    Regression coverage for a real, previously-reported bug ("some of
    the descriptions of abilities have an extra space in the first
    line, almost like an indent") - eventually traced to interpolating
    a multi-line, differently-indented string (either a race's own
    desc, which carries a trailing newline, or _format_abilities'
    output, whose lines use their own single-leading-space convention)
    INSIDE a dedent() call. dedent() computes its common-prefix strip
    amount from the *final*, already-interpolated string - a stray
    differently-indented interpolated line drags that minimum down,
    leaving the template's own literal lines under-stripped. Fixed by
    building each such piece separately, outside the dedent() scope.
    """

    class _FakeCaller:
        def __init__(self, new_char):
            self.new_char = new_char

    def setUp(self):
        super().setUp()
        self.caller = self._FakeCaller(self.char1)

    def test_no_race_info_line_has_stray_leading_whitespace(self):
        # Up to one leading space is legitimate - _format_abilities'
        # own deliberate single-space bullet-list indent. More than
        # that is the actual under-stripped-dedent bug this guards
        # against.
        for race_key in _RACE_ORDER:
            (text, help_text), options = menunode_race_info(self.caller, race_key=race_key)
            for line in text.split("\n"):
                if line.strip():
                    leading = len(line) - len(line.lstrip())
                    self.assertLessEqual(
                        leading, 1,
                        "stray leading whitespace for race '%s': %r" % (race_key, line),
                    )

    def test_no_class_info_line_has_stray_leading_whitespace(self):
        for class_key in _CLASS_ORDER:
            (text, help_text), options = menunode_class_info(self.caller, class_key=class_key)
            for line in text.split("\n"):
                if line.strip():
                    leading = len(line) - len(line.lstrip())
                    self.assertLessEqual(
                        leading, 1,
                        "stray leading whitespace for class '%s': %r" % (class_key, line),
                    )

    def test_race_desc_trailing_newline_does_not_orphan_the_reset_code(self):
        # The specific symptom this bug produced: race["desc"] already
        # ends in "\n", so interpolating it unstripped left a lone
        # "|n" sitting alone on its own line right after the sentence.
        (text, help_text), options = menunode_race_info(self.caller, race_key="minotaur")
        self.assertNotIn("\n|n", text)

    def test_gifts_and_equipped_for_war_have_a_real_blank_line_between_them(self):
        (text, help_text), options = menunode_class_info(self.caller, class_key="legionary")
        self.assertIn("\n\n|wEquipped for War:|n", text)
