"""
Tests for the physical-skill rework (world/combat.py's _skill_damage) and the
level term in condition resistance (resists_condition).

Owner-approved first pass (Sep 26): every damaging skill hits for the user's
own normal weapon strike times a per-skill multiplier, so it scales with level
and gear and can never fall below a basic attack; NPC users keep their
authored flat ranges so no monster silently changes difficulty. No new
effects yet. Also: a target's level advantage now adds to its chance to
resist a hex (a level-30 Augur could otherwise sleep a level-90 monster at
Ingenium-only odds).
"""

from unittest.mock import patch

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from world.combat import (
    COMBAT_RULES,
    CONDITION_RESIST_LEVEL_MULTIPLIER,
    CONDITION_RESIST_MAX,
    CONDITION_RESIST_MIN,
    SKILLS,
    AutoStatNPC,
    CmdSkillInfo,
    HostileNPC,
)


def _weapon(location, low, high, category="light_blade"):
    return create.create_object(
        "typeclasses.objects.Object",
        key="a test blade",
        location=location,
        attributes=[
            ("damage_range", (low, high)),
            ("accuracy_bonus", 0),
            ("weapon_category", category),
            ("stat_bonuses", {}),
            ("resource_bonuses", {}),
        ],
    )


class SkillDamageBase(EvenniaTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.permissions.remove("Developer")
            char.db.level = 60
            char.db.max_hp = char.db.hp = 100000
            char.db.sp = char.db.max_sp = 100
            char.db.conditions = {}
            char.db.combat_turnhandler = None
            char.db.virtus = char.db.agilitas = 10
            char.db.player_class = "gladiator"
            char.db.worn_armor = None
            char.db.wielded_weapon = None
        self.char1.db.wielded_weapon = _weapon(self.char1, 100, 100)

    def _hit(self, skill, target=None, **fixed):
        """Damage `skill` deals to char2, with every roll forced to a hit."""
        target = target or self.char2
        data = dict(SKILLS[skill])
        kwargs = {
            k: v for k, v in data.items()
            if k not in ("skillfunc", "target", "cost", "classes", "desc", "level_required")
        }
        kwargs.update(fixed)
        before = target.db.hp
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi if hi != 100 else 100):
            data["skillfunc"](self.char1, skill, [target], data["cost"], **kwargs)
        return before - target.db.hp


class TestEveryDamagingSkillIsWeaponBased(EvenniaTest):
    def test_every_flat_damage_skill_has_a_weapon_multiplier(self):
        for name, data in SKILLS.items():
            if "damage_range" in data or "bonus_damage" in data:
                self.assertIn("weapon_multiplier", data, name)

    def test_every_skill_hits_for_more_than_a_basic_attack_per_target(self):
        # Strictly more: with only one enemy in reach an area skill that merely
        # matched a basic attack would be strictly worse (it costs SP for nothing).
        for name, data in SKILLS.items():
            if "weapon_multiplier" in data:
                self.assertGreater(data["weapon_multiplier"], 1.0, name)

    def test_area_skills_rank_by_tier(self):
        m = lambda n: SKILLS[n]["weapon_multiplier"]
        self.assertLess(m("gladius cleave"), m("earth-shaking slam"))
        self.assertLess(m("rapid volley"), m("bane of the wild hunt"))
        self.assertLess(m("earth-shaking slam"), m("fury of the frontier"))

    def test_the_legacy_flat_ranges_are_kept_for_npcs(self):
        for name, data in SKILLS.items():
            if "weapon_multiplier" in data and name != "backstab":
                self.assertIn("damage_range", data, name)

    def test_the_mythic_is_the_biggest_hit_of_its_class(self):
        self.assertGreater(SKILLS["glory"]["weapon_multiplier"], SKILLS["finishing blow"]["weapon_multiplier"])
        self.assertGreater(SKILLS["glory"]["weapon_multiplier"], SKILLS["gory finish"]["weapon_multiplier"])


class TestSkillsHitForTheWeaponTimesTheMultiplier(SkillDamageBase):
    def test_a_skill_is_the_weapon_hit_times_its_multiplier(self):
        # weapon 100-100, stats 10 (no bonus), target unarmoured: a basic hit is 100.
        self.assertEqual(self._hit("glory"), 250)
        self.assertEqual(self._hit("finishing blow"), 160)
        self.assertEqual(self._hit("shield bash"), 130)

    def test_a_better_weapon_hits_harder_with_the_same_skill(self):
        weak = self._hit("glory")
        self.char1.db.wielded_weapon = _weapon(self.char1, 300, 300)
        self.assertGreater(self._hit("glory"), weak)

    def test_a_skill_never_does_less_than_a_plain_attack_at_any_level_or_weapon(self):
        for weapon_dmg in (20, 100, 400):
            self.char1.db.wielded_weapon = _weapon(self.char1, weapon_dmg, weapon_dmg)
            basic = COMBAT_RULES.get_damage(self.char1, self.char2)
            for name, data in SKILLS.items():
                if "weapon_multiplier" not in data or data.get("max_targets", 1) > 1:
                    continue
                if name in ("gory finish", "thundering maul", "backstab"):
                    continue  # execute / two-hander / opener: covered separately
                self.assertGreaterEqual(self._hit(name), basic, name)

    def test_it_now_beats_a_basic_attack_at_high_level_where_the_flat_range_did_not(self):
        flat_glory = sum(SKILLS["glory"]["damage_range"]) / 2  # ~55
        self.assertGreater(self._hit("glory"), flat_glory * 3)

    def test_the_target_armor_reduces_it_like_any_hit(self):
        bare = self._hit("finishing blow")
        self.char2.db.worn_armor = create.create_object(
            "typeclasses.objects.Object", key="mail", location=self.char2,
            attributes=[("damage_reduction", 20), ("defense_modifier", 0), ("armor_category", "light")],
        )
        self.assertLess(self._hit("finishing blow"), bare)

    def test_piercing_shot_ignores_armor_entirely(self):
        self.char1.db.player_class = "venator"
        bare = self._hit("piercing shot")
        self.char2.db.worn_armor = create.create_object(
            "typeclasses.objects.Object", key="mail", location=self.char2,
            attributes=[("damage_reduction", 20), ("defense_modifier", 0), ("armor_category", "light")],
        )
        self.assertEqual(self._hit("piercing shot"), bare)

    def test_damage_up_and_down_now_apply_to_a_skill(self):
        base = self._hit("finishing blow")
        self.char1.db.conditions = {"Damage Down": [3, self.char2]}
        self.assertLess(self._hit("finishing blow"), base)

    def test_an_area_skill_hits_each_target_for_its_own_multiplier(self):
        target2 = create.create_object("typeclasses.characters.Character", key="Third", location=self.room1)
        target2.db.max_hp = target2.db.hp = 100000
        target2.db.conditions = {}
        data = SKILLS["earth-shaking slam"]
        kwargs = {k: v for k, v in data.items() if k in ("weapon_multiplier", "damage_range")}
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            data["skillfunc"](self.char1, "earth-shaking slam", [self.char2, target2], 11, **kwargs)
        self.assertEqual(100000 - self.char2.db.hp, 130)
        self.assertEqual(100000 - target2.db.hp, 130)

    def test_the_two_handed_check_still_applies(self):
        self.char1.db.player_class = "barbarian"
        self.char1.db.wielded_weapon.db.two_handed = False
        self.assertEqual(self._hit("thundering maul"), 0)

    def test_a_two_handed_weapon_powers_thundering_maul(self):
        self.char1.db.player_class = "barbarian"
        self.char1.db.wielded_weapon.db.two_handed = True
        self.char1.db.wielded_weapon.db.weapon_category = "heavy_weapon"  # a barbarian's own kind
        self.assertEqual(self._hit("thundering maul"), 150)

    def test_gory_finish_is_still_an_execute(self):
        self.char2.db.hp = self.char2.db.max_hp
        self.assertEqual(self._hit("gory finish"), 0)  # target too healthy: refused
        self.char2.db.hp = 1000  # below 20% of 100000
        self.assertEqual(self._hit("gory finish"), 200)

    def test_backstab_is_now_the_weapon_hit_times_its_multiplier(self):
        self.char1.db.player_class = "speculator"
        self.char2.db.combat_lastaction = "null"
        handler = None
        self.room1.ndb.pending_fighters = [self.char1, self.char2]
        from world.combat import CombatTurnHandler

        handler = self.room1.scripts.add(CombatTurnHandler)
        self.char2.db.combat_lastaction = "null"
        self.assertEqual(self._hit("backstab"), 200)


class TestNpcsKeepTheirFlatRanges(SkillDamageBase):
    def test_an_npc_using_a_skill_still_rolls_the_authored_range(self):
        npc = create.create_object(
            HostileNPC, key="an arena champion", location=self.room1,
            attributes=[("player_class", "gladiator"), ("level", 90)],
        )
        npc.db.wielded_weapon = None
        with patch("world.combat.randint", side_effect=lambda lo, hi: lo):
            damage = COMBAT_RULES._skill_damage(
                npc, self.char2, dict(SKILLS["glory"]), (0, 0), "agilitas"
            )
        self.assertEqual(damage, SKILLS["glory"]["damage_range"][0] + ((npc.db.agilitas or 10) - 10) // 2)


class TestSkillInfoShowsTheDamage(SkillDamageBase):
    def test_the_multiplier_is_shown(self):
        from evennia.utils.test_resources import EvenniaCommandTest  # noqa: F401

        cmd = CmdSkillInfo()
        cmd.caller = self.char1
        cmd.args = "glory"
        with patch.object(self.char1, "msg") as sent:
            cmd.func()
        text = sent.call_args[0][0]
        self.assertIn("2.5 times", text)
        self.assertIn("normal hit from your weapon", text)


class TestLevelTermInResistance(SkillDamageBase):
    def _chance(self, caster_level, target_level):
        # Probe the exact chance by bisecting on a forced roll.
        self.char1.db.level, self.char2.db.level = caster_level, target_level
        self.char1.db.ingenium = self.char2.db.ingenium = 10
        for roll in range(0, 101):
            with patch("world.combat.randint", return_value=roll):
                if not COMBAT_RULES.resists_condition(self.char1, self.char2):
                    return roll - 1
        return 100

    def test_equal_levels_leave_the_stat_only_odds_unchanged(self):
        self.assertEqual(self._chance(50, 50), 10)

    def test_a_higher_level_target_resists_more(self):
        self.assertEqual(self._chance(30, 50), 10 + int(20 * CONDITION_RESIST_LEVEL_MULTIPLIER))

    def test_a_much_higher_level_target_is_capped_not_immune(self):
        self.assertEqual(self._chance(30, 90), CONDITION_RESIST_MAX)
        self.assertEqual(self._chance(10, 100), CONDITION_RESIST_MAX)

    def test_a_higher_level_caster_lands_it_more_often_down_to_the_floor(self):
        self.assertEqual(self._chance(90, 30), CONDITION_RESIST_MIN)
        self.assertLess(self._chance(60, 50), self._chance(50, 50))

    def test_the_level_gap_and_ingenium_add_together(self):
        self.char1.db.level, self.char2.db.level = 30, 40
        self.char1.db.ingenium, self.char2.db.ingenium = 10, 12
        with patch("world.combat.randint", return_value=10 + 4 + 15):
            self.assertTrue(COMBAT_RULES.resists_condition(self.char1, self.char2))
        with patch("world.combat.randint", return_value=10 + 4 + 15 + 1):
            self.assertFalse(COMBAT_RULES.resists_condition(self.char1, self.char2))

    def test_a_low_level_augur_rarely_puts_a_high_level_monster_to_sleep(self):
        from world import concentration as conc

        self.char1.db.mp = self.char1.db.max_mp = 100
        self.char1.db.level, self.char2.db.level = 30, 90
        self.char1.db.ingenium = self.char2.db.ingenium = 10
        landed = 0
        for roll in range(1, 101):
            self.char2.db.conditions = {}
            self.char1.db.concentrations = {}
            self.char1.db.mp = 100
            with patch("world.combat.randint", return_value=roll):
                conc.spell_sleep(self.char1, "sleep", [self.char2], 5, drain_percent=0.02)
            landed += "Asleep" in self.char2.db.conditions
            self.char1.scripts.remove("concentration")
        self.assertEqual(landed, 100 - CONDITION_RESIST_MAX)
