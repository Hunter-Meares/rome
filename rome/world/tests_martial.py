"""
Tests for critical hits and the martial status effects (world/martial.py), the
Headbutt and Dirt Kick skills, and the Omen of Ruin redesign.

Crits are random, so under the test runner they are off unless a test here turns
them on (martial.CRITS_IN_TESTS) - hundreds of other tests assert exact damage.
"""

import time
from unittest.mock import patch

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTestMixin

from world import martial
from world.combat import (
    COMBAT_RULES,
    SKILLS,
    SPELLS,
    CmdCast,
    CmdDisengage,
    CombatTurnHandler,
)
from world.tests_skill_damage import SkillDamageBase, _weapon


class MartialBase(EvenniaCommandTestMixin, SkillDamageBase):
    def setUp(self):
        super().setUp()
        patcher = patch("world.martial.CRITS_IN_TESTS", True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _armor(self, target, slot="worn_armor", reduction=20, defense=5):
        item = create.create_object(
            "typeclasses.objects.Object", key="a test cuirass", location=target,
            attributes=[("damage_reduction", reduction), ("defense_modifier", defense),
                        ("armor_category", "light")],
        )
        setattr(target.db, slot, item)
        return item

    def _fight(self):
        self.room1.ndb.pending_fighters = [self.char1, self.char2]
        return self.room1.scripts.add(CombatTurnHandler)

    def _rider(self, effect, **extra):
        rider = {"effect": effect, "chance": 100, "duration": 3}
        rider.update(extra)
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            return martial.apply_rider(COMBAT_RULES, self.char1, self.char2, rider, damage=100)


class TestCriticalHits(MartialBase):
    def test_the_weapon_decides_the_chance_and_multiplier(self):
        expected = {"light_blade": (10, 2.0), "heavy_blade": (8, 2.0), "polearm": (5, 3.0),
                    "heavy_weapon": (5, 3.0), "staff": (5, 2.0)}
        for category, profile in expected.items():
            self.char1.db.wielded_weapon = _weapon(self.char1, 10, 10, category=category)
            self.assertEqual(martial.crit_profile(self.char1), profile, category)

    def test_agilitas_raises_the_chance_up_to_a_cap(self):
        self.char1.db.agilitas = 18
        self.assertEqual(martial.crit_profile(self.char1)[0], 10 + 8 * martial.CRIT_PER_AGILITAS)
        self.char1.db.agilitas = 500
        self.assertEqual(martial.crit_profile(self.char1)[0], martial.CRIT_MAX_CHANCE)

    def test_a_bow_crits_and_so_do_fists(self):
        self.char1.db.wielded_weapon = _weapon(self.char1, 10, 10, category="ranged")
        self.assertEqual(martial.crit_profile(self.char1), (8, 2.0))
        self.char1.db.wielded_weapon = None
        self.assertEqual(martial.crit_profile(self.char1), martial.UNARMED_CRIT)

    def test_something_that_is_not_a_weapon_category_cannot_crit(self):
        self.char1.db.wielded_weapon = _weapon(self.char1, 10, 10, category="mystery")
        self.assertIsNone(martial.crit_profile(self.char1))

    def test_monsters_never_crit(self):
        from world.combat import HostileNPC

        npc = create.create_object(HostileNPC, key="a brute", location=self.room1)
        self.assertIsNone(martial.crit_profile(npc))

    def test_a_disarmed_fighter_crits_like_a_brawler(self):
        self.char1.db.conditions = {"Disarmed": [2, self.char2]}
        self.assertEqual(martial.crit_profile(self.char1), martial.UNARMED_CRIT)

    def test_a_crit_roll_at_or_under_the_chance_crits(self):
        with patch("world.combat.randint", return_value=10):
            self.assertEqual(martial.roll_crit(self.char1), 2.0)
        with patch("world.combat.randint", return_value=11):
            self.assertEqual(martial.roll_crit(self.char1), 1.0)

    def test_a_basic_attack_that_crits_does_the_multiplier(self):
        with patch("world.combat.randint", side_effect=lambda lo, hi: lo):
            COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=999, defense_value=0)
        self.assertEqual(100000 - self.char2.db.hp, 200)

    def test_a_basic_attack_that_does_not_crit_is_unchanged(self):
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=999, defense_value=0)
        self.assertEqual(100000 - self.char2.db.hp, 100)

    def test_a_handed_in_damage_number_never_crits_unless_allowed(self):
        with patch("world.combat.randint", side_effect=lambda lo, hi: lo):
            COMBAT_RULES.resolve_attack(
                self.char1, self.char2, attack_value=999, defense_value=0, damage_value=100
            )
        self.assertEqual(100000 - self.char2.db.hp, 100)
        self.char2.db.hp = 100000
        with patch("world.combat.randint", side_effect=lambda lo, hi: lo):
            COMBAT_RULES.resolve_attack(
                self.char1, self.char2, attack_value=999, defense_value=0,
                damage_value=100, allow_crit=True,
            )
        self.assertEqual(100000 - self.char2.db.hp, 200)

    def test_a_crit_is_announced(self):
        with patch("world.combat.randint", side_effect=lambda lo, hi: lo), \
                patch.object(self.room1, "msg_contents") as sent:
            COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=999, defense_value=0)
        self.assertTrue(any("CRITICAL HIT" in str(call) for call in sent.call_args_list))

    def test_glory_is_a_guaranteed_critical(self):
        # weapon 100 x crit 2.0 x Glory 2.5
        self.assertEqual(self._hit("glory"), 500)

    def test_a_weapon_skill_can_crit_by_chance_too(self):
        data = dict(SKILLS["finishing blow"])
        kwargs = {k: v for k, v in data.items() if k in ("weapon_multiplier", "damage_range")}
        with patch("world.combat.randint", side_effect=lambda lo, hi: lo):
            damage = COMBAT_RULES._skill_damage(self.char1, self.char2, kwargs, (0, 0), "agilitas")
        self.assertEqual(damage, int(100 * 2.0 * 1.6))

    def test_a_ranged_skill_crits_by_chance_too(self):
        self.char1.db.wielded_weapon = _weapon(self.char1, 100, 100, category="ranged")
        self.char1.db.player_class = "venator"
        self.assertEqual(self._hit("piercing shot"), int(100 * 1.3))  # no crit on a high roll
        data = dict(SKILLS["piercing shot"])
        kwargs = {k: v for k, v in data.items() if k in ("weapon_multiplier", "damage_range")}
        with patch("world.combat.randint", side_effect=lambda lo, hi: lo):
            damage = COMBAT_RULES._skill_damage(
                self.char1, self.char2, kwargs, (0, 0), "agilitas", ignore_armor=True
            )
        self.assertEqual(damage, int(100 * 2.0 * 1.3))

    def test_crits_are_off_under_the_test_runner_by_default(self):
        with patch("world.martial.CRITS_IN_TESTS", False):
            self.assertIsNone(martial.crit_profile(self.char1))


class TestBleeding(MartialBase):
    def test_a_rider_opens_a_wound_worth_a_share_of_the_blow(self):
        self.assertTrue(self._rider("Bleeding", share=0.2))
        self.assertEqual(self.char2.db.conditions["Bleeding"][2], 20)

    def test_it_costs_hp_every_turn(self):
        self._rider("Bleeding", share=0.2)
        before = self.char2.db.hp
        COMBAT_RULES.apply_turn_conditions(self.char2)
        self.assertEqual(before - self.char2.db.hp, 20)

    def test_a_healing_spell_closes_the_wound(self):
        self._rider("Bleeding")
        self.char2.db.hp = 50
        COMBAT_RULES.spell_healing(self.char1, "cure wounds", [self.char2], 5, healing_range=(20, 20))
        self.assertNotIn("Bleeding", self.char2.db.conditions)

    def test_a_healing_potion_closes_it_too(self):
        self._rider("Bleeding")
        self.char2.db.hp = 50
        item = create.create_object("typeclasses.objects.Object", key="a tonic", location=self.char2)
        COMBAT_RULES.itemfunc_heal(item, self.char1, self.char2, healing_range=(10, 10))
        self.assertNotIn("Bleeding", self.char2.db.conditions)

    def test_poison_is_not_closed_by_a_heal_but_a_wound_is(self):
        # The point of Bleeding: unlike poison, healing stops it.
        from world.martial import stop_bleeding

        self.char2.db.conditions = {"Poisoned": [3, self.char1], "Bleeding": [3, self.char1, 5]}
        stop_bleeding(self.char2)
        self.assertIn("Poisoned", self.char2.db.conditions)
        self.assertNotIn("Bleeding", self.char2.db.conditions)

    def test_bleeding_can_kill_and_credit_the_attacker(self):
        self._rider("Bleeding", share=0.2)
        self.char2.db.hp = 5
        with patch.object(COMBAT_RULES, "at_defeat") as defeated:
            COMBAT_RULES.apply_turn_conditions(self.char2)
        defeated.assert_called_once_with(self.char2, attacker=self.char1)


class TestSundered(MartialBase):
    def test_it_cleaves_a_worn_piece_for_the_rest_of_the_fight(self):
        self._armor(self.char2)
        base = COMBAT_RULES.get_damage(self.char1, self.char2)
        defense = COMBAT_RULES.get_defense(self.char1, self.char2)
        self.assertTrue(self._rider("Sundered"))
        self.assertEqual(self.char2.db.combat_sundered, "worn_armor")
        self.assertGreater(COMBAT_RULES.get_damage(self.char1, self.char2), base)
        self.assertLess(COMBAT_RULES.get_defense(self.char1, self.char2), defense)

    def test_it_picks_among_body_armor_and_shield(self):
        self._armor(self.char2, "worn_armor")
        self._armor(self.char2, "worn_shield", reduction=0, defense=8)
        seen = set()
        for _ in range(40):
            self.char2.db.combat_sundered = None
            self._rider("Sundered")
            seen.add(self.char2.db.combat_sundered)
        self.assertEqual(seen, {"worn_armor", "worn_shield"})

    def test_nothing_worn_means_nothing_to_cleave(self):
        self.assertFalse(self._rider("Sundered"))
        self.assertIsNone(self.char2.db.combat_sundered)

    def test_the_item_itself_is_untouched_and_it_ends_with_the_fight(self):
        armor = self._armor(self.char2)
        self._rider("Sundered")
        self.assertEqual(armor.db.damage_reduction, 20)  # nothing about the item changed
        COMBAT_RULES.combat_cleanup(self.char2)
        self.assertIsNone(self.char2.db.combat_sundered)

    def test_a_sundered_shield_stops_giving_defense_only(self):
        self._armor(self.char2, "worn_armor", reduction=20, defense=5)
        shield = self._armor(self.char2, "worn_shield", reduction=0, defense=10)
        self.char2.db.combat_sundered = "worn_shield"
        with_armor = COMBAT_RULES.get_damage(self.char1, self.char2)
        self.char2.db.combat_sundered = None
        self.assertEqual(COMBAT_RULES.get_damage(self.char1, self.char2), with_armor)
        self.assertTrue(shield)


class TestDisarmedGrappledBlinded(MartialBase):
    def test_a_disarmed_fighter_uses_bare_fists(self):
        self.char2.db.wielded_weapon = _weapon(self.char2, 500, 500)
        self.char2.db.unarmed_damage_range = (5, 5)
        armed = COMBAT_RULES.get_damage(self.char2, self.char1)
        self.char2.db.conditions = {"Disarmed": [2, self.char1]}
        self.assertEqual(COMBAT_RULES.get_damage(self.char2, self.char1), 5)
        self.assertGreater(armed, 5)
        self.assertIsNone(martial.wielded_weapon(self.char2))

    def test_disarm_wears_off_and_the_weapon_is_never_lost(self):
        weapon = self.char2.db.wielded_weapon = _weapon(self.char2, 500, 500)
        self._rider("Disarmed")
        self.assertIs(self.char2.db.wielded_weapon, weapon)
        del self.char2.db.conditions["Disarmed"]
        self.assertIs(martial.wielded_weapon(self.char2), weapon)

    def test_a_grappled_fighter_cannot_disengage(self):
        handler = self._fight()
        handler.db.turn = handler.db.fighters.index(self.char1)
        self.char1.db.combat_actionsleft = 1
        self.char1.db.conditions = {"Grappled": [3, self.char2]}
        with patch("world.combat.randint", return_value=1):  # would be a sure escape
            result = self.call(CmdDisengage(), "", caller=self.char1)
        self.assertIn("held fast", result)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))

    def test_an_ungrappled_fighter_still_can(self):
        handler = self._fight()
        handler.db.turn = handler.db.fighters.index(self.char1)
        self.char1.db.combat_actionsleft = 1
        with patch("world.combat.randint", return_value=1):
            self.call(CmdDisengage(), "", caller=self.char1)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_a_grapple_ends_with_the_fight(self):
        self.char2.db.conditions = {"Grappled": [3, self.char1]}
        COMBAT_RULES.combat_cleanup(self.char2)
        self.assertNotIn("Grappled", self.char2.db.conditions)

    def test_blinded_is_a_big_accuracy_penalty_twice_accuracy_down(self):
        with patch("world.combat.randint", return_value=50):
            clear = COMBAT_RULES.get_attack(self.char1, self.char2)
            self.char1.db.conditions = {"Blinded": [3, self.char2]}
            blind = COMBAT_RULES.get_attack(self.char1, self.char2)
            self.char1.db.conditions = {"Accuracy Down": [3, self.char2]}
            down = COMBAT_RULES.get_attack(self.char1, self.char2)
        self.assertEqual(clear - blind, 50)
        self.assertEqual(clear - down, 25)

    def test_blinded_also_hurts_skills_and_spells(self):
        self.char1.db.conditions = {"Blinded": [3, self.char2]}
        self.assertEqual(martial.BLINDED_ACCURACY_MOD, -50)
        # A blinded fighter's skill against a sturdy defender misses.
        self.char2.db.agilitas = 18
        data = dict(SKILLS["finishing blow"])
        before = self.char2.db.hp
        with patch("world.combat.randint", side_effect=lambda lo, hi: 40 if hi == 100 else hi):
            data["skillfunc"](self.char1, "finishing blow", [self.char2], 8,
                              weapon_multiplier=1.6, damage_range=(1, 1))
        self.assertEqual(self.char2.db.hp, before)


class TestStunned(MartialBase):
    def test_a_stun_takes_hold_and_grants_immunity_afterwards(self):
        self.assertTrue(self._rider("Stunned", duration=2))
        self.assertIn("Stunned", self.char2.db.conditions)
        self.assertEqual(self.char2.db.conditions["Stun Immunity"][0], 2 + martial.STUN_IMMUNITY_EXTRA_TURNS)

    def test_a_stunned_target_cannot_be_stunned_again_at_once(self):
        self._rider("Stunned")
        del self.char2.db.conditions["Stunned"]
        self.assertFalse(self._rider("Stunned"))
        self.assertNotIn("Stunned", self.char2.db.conditions)

    def test_a_stunned_character_cannot_cast_or_move(self):
        self._rider("Stunned")
        self.char2.db.mp = 50
        cast = self.call(CmdCast(), "magic arrow = Char", caller=self.char2)
        self.assertIn("stunned", cast)
        self.assertFalse(self.char2.move_to(self.room2, move_type="move"))

    def test_damage_does_not_wake_a_stunned_target(self):
        self._rider("Stunned")
        COMBAT_RULES.apply_damage(self.char2, 10, attacker=self.char1)
        self.assertIn("Stunned", self.char2.db.conditions)

    def test_a_stunned_fighter_loses_their_turn(self):
        handler = self._fight()
        self.char2.db.conditions = {"Stunned": [2, self.char1]}
        handler.db.turn = handler.db.fighters.index(self.char2)
        self.char2.db.combat_actionsleft = 1
        COMBAT_RULES.apply_turn_conditions(self.char2)
        self.assertEqual(self.char2.db.combat_actionsleft, 0)

    def test_a_stun_ends_with_the_fight_and_shows_in_the_room_list(self):
        self._rider("Stunned")
        self.assertIn("(stunned)", self.room1.get_display_characters(self.char1))
        COMBAT_RULES.combat_cleanup(self.char2)
        self.assertNotIn("Stunned", self.char2.db.conditions)
        self.assertNotIn("Stun Immunity", self.char2.db.conditions)

    def test_a_high_vigor_target_can_resist_a_stun(self):
        self.char2.db.vigor = 40
        rider = {"effect": "Stunned", "chance": 100, "duration": 2}
        with patch("world.combat.randint", return_value=5):
            landed = martial.apply_rider(COMBAT_RULES, self.char1, self.char2, rider, 100)
        self.assertFalse(landed)
        self.assertNotIn("Stunned", self.char2.db.conditions)

    def test_toughness_shrugs_off_a_wound_or_a_knockout_and_reflexes_slip_the_rest(self):
        from world.combat import CONDITION_RESIST_STAT

        for effect in ("Bleeding", "Stunned"):
            self.assertEqual(CONDITION_RESIST_STAT[effect], "vigor", effect)
        for effect in ("Blinded", "Disarmed", "Grappled"):
            self.assertEqual(CONDITION_RESIST_STAT[effect], "agilitas", effect)

    def test_a_nimble_target_dodges_dirt_but_not_a_knockout(self):
        self.char2.db.agilitas, self.char2.db.vigor = 18, 10
        with patch("world.combat.randint", return_value=20):  # 10 + 8*2 = 26% resist
            self.assertTrue(COMBAT_RULES.resists_condition(self.char1, self.char2, condition="Blinded"))
            self.assertFalse(COMBAT_RULES.resists_condition(self.char1, self.char2, condition="Stunned"))


class TestRidersInGeneral(MartialBase):
    def test_a_monsters_skill_never_carries_a_rider(self):
        from world.combat import HostileNPC

        npc = create.create_object(HostileNPC, key="a brute", location=self.room1)
        rider = {"effect": "Bleeding", "chance": 100, "duration": 3}
        self.assertFalse(martial.apply_rider(COMBAT_RULES, npc, self.char2, rider, 100))

    def test_a_pacifist_is_never_touched(self):
        self.char2.db.pacifist = True
        self.assertFalse(self._rider("Stunned"))

    def test_the_chance_gates_the_rider(self):
        with patch("world.combat.randint", return_value=100):
            rider = {"effect": "Disarmed", "chance": 40, "duration": 2}
            self.assertFalse(martial.apply_rider(COMBAT_RULES, self.char1, self.char2, rider, 0))

    def test_a_skill_that_lands_applies_its_rider(self):
        data = dict(SKILLS["reckless swing"])
        kwargs = {k: v for k, v in data.items()
                  if k not in ("skillfunc", "target", "cost", "classes", "desc", "level_required")}
        kwargs["rider"] = {"effect": "Bleeding", "chance": 100, "duration": 3, "share": 0.2}
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False), \
                patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            data["skillfunc"](self.char1, "reckless swing", [self.char2], 5, **kwargs)
        self.assertIn("Bleeding", self.char2.db.conditions)

    def test_the_planned_skills_carry_the_planned_riders(self):
        expected = {
            "reckless swing": "Bleeding", "thundering maul": "Sundered",
            "fury of the frontier": "Bleeding", "shield bash": "Disarmed",
            "shattering blow": "Sundered", "feint": "Bleeding", "disarming strike": "Disarmed",
            "finishing blow": "Grappled", "rapid volley": "Bleeding", "backstab": "Bleeding",
            "headbutt": "Stunned",
        }
        for name, effect in expected.items():
            self.assertEqual(SKILLS[name]["rider"]["effect"], effect, name)
        self.assertTrue(SKILLS["glory"]["guaranteed_crit"])

    def test_no_martial_effect_duplicates_a_caster_condition(self):
        casters = {"Accuracy Down", "Accuracy Up", "Cursed", "Damage Down", "Damage Up",
                   "Defense Down", "Defense Up", "Frightened", "Haste", "Paralyzed", "Poisoned",
                   "Regeneration", "Shielded", "Silenced", "Slowed", "Asleep", "Confused",
                   "Death Ward", "Invisible", "Marked for Death"}
        for name, data in SKILLS.items():
            rider = data.get("rider")
            if rider:
                self.assertNotIn(rider["effect"], casters, name)


class TestHeadbuttAndDirtKick(MartialBase):
    def test_headbutt_is_a_level_35_barbarian_skill_monsters_never_use(self):
        data = SKILLS["headbutt"]
        self.assertEqual(data["classes"], ["barbarian"])
        self.assertEqual(data["level_required"], 35)
        self.assertIs(data["npc_cast"], False)
        self.assertGreater(data["weapon_multiplier"], 1.0)
        self.assertEqual(data["rider"]["duration"], 2)

    def test_dirt_kick_is_a_gladiator_blind_and_never_a_monster_move(self):
        data = SKILLS["dirt kick"]
        self.assertEqual(data["classes"], ["gladiator"])
        self.assertEqual(data["level_required"], 25)
        self.assertEqual(data["conditions"][0][0], "Blinded")
        self.assertIs(data["npc_cast"], False)

    def test_dirt_kick_blinds_through_the_real_skill(self):
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            SKILLS["dirt kick"]["skillfunc"](
                self.char1, "dirt kick", [self.char2], 5, conditions=[("Blinded", 3)]
            )
        self.assertIn("Blinded", self.char2.db.conditions)

    def test_a_monster_barbarian_never_picks_headbutt_or_dirt_kick(self):
        from world.combat import HostileNPC

        for cls, level in (("barbarian", 60), ("gladiator", 60)):
            npc = create.create_object(
                HostileNPC, key="a %s" % cls, location=self.room1,
                attributes=[("player_class", cls), ("level", level)],
            )
            npc.db.sp = 100
            names = {a[1] for a in npc._gather_actions()}
            self.assertNotIn("headbutt", names)
            self.assertNotIn("dirt kick", names)


class TestOmenOfRuinRedesign(MartialBase):
    def test_it_is_an_area_fear_with_lingering_weakness(self):
        data = SPELLS["omen of ruin"]
        self.assertEqual(data["max_targets"], 3)
        conditions = dict(data["conditions"])
        self.assertEqual(conditions["Frightened"], 2)
        self.assertGreater(conditions["Accuracy Down"], conditions["Frightened"])
        self.assertGreater(conditions["Damage Down"], conditions["Frightened"])
        self.assertEqual(data["cost"], 10)

    def test_it_frightens_every_target_it_lands_on(self):
        third = create.create_object("typeclasses.characters.Character", key="Third", location=self.room1)
        third.db.conditions = {}
        third.db.max_hp = third.db.hp = 100
        self.char1.db.mp = 100
        data = SPELLS["omen of ruin"]
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            COMBAT_RULES.spell_add_condition(
                self.char1, "omen of ruin", [self.char2, third], data["cost"],
                conditions=data["conditions"],
            )
        for target in (self.char2, third):
            self.assertIn("Frightened", target.db.conditions)
            self.assertIn("Accuracy Down", target.db.conditions)
            self.assertIn("Damage Down", target.db.conditions)

    def test_the_debuffs_outlast_the_fear(self):
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            COMBAT_RULES.spell_add_condition(
                self.char1, "omen of ruin", [self.char2], 10,
                conditions=SPELLS["omen of ruin"]["conditions"],
            )
        held = self.char2.db.conditions
        self.assertGreater(held["Accuracy Down"][0], held["Frightened"][0])
        self.assertGreater(held["Damage Down"][0], held["Frightened"][0])


class TestMartialHelp(MartialBase):
    def setUp(self):
        super().setUp()
        from world.help_setup import create_all_help_entries

        create_all_help_entries()

    def test_the_new_skills_have_help_with_their_real_stats(self):
        from evennia.help.models import HelpEntry

        from world.help_setup import NEW_SKILL_HELP

        for name in NEW_SKILL_HELP:
            text = HelpEntry.objects.get(db_key=name).db_entrytext
            self.assertIn("level %d" % SKILLS[name]["level_required"], text, name)
            self.assertIn("Cost: %s SP" % SKILLS[name]["cost"], text, name)
            self.assertIn("skill %s" % name, text, name)

    def test_crits_and_the_effects_are_explained(self):
        from evennia.help.models import HelpEntry

        crits = HelpEntry.objects.get(db_key="critical hits").db_entrytext
        self.assertIn("triple", crits)
        self.assertIn("Glory", crits)
        effects = HelpEntry.objects.get(db_key="martial effects").db_entrytext
        for effect in ("Bleeding", "Sundered", "Disarmed", "Grappled", "Stunned", "Blinded"):
            self.assertIn(effect, effects)
        self.assertIn("Vigor", effects)

    def test_skills_describe_their_riders(self):
        for name in ("reckless swing", "shield bash", "finishing blow", "glory"):
            self.assertTrue(len(SKILLS[name]["desc"]) > 60, name)
        self.assertIn("bleeding", SKILLS["reckless swing"]["desc"])
        self.assertIn("critical", SKILLS["glory"]["desc"])


class TestSmiteAndScalingDebuffs(MartialBase):
    def test_smite_the_unclean_costs_10_mp_not_the_cheapest_of_its_tier(self):
        self.assertEqual(SPELLS["smite the unclean"]["cost"], 10)
        self.assertGreater(SPELLS["smite the unclean"]["cost"], SPELLS["doom"]["cost"])

    def test_the_extra_turns_grow_with_level_and_cap_at_five(self):
        from world.combat import debuff_level_bonus

        for level, extra in ((1, 0), (19, 0), (20, 1), (60, 3), (99, 4), (100, 5)):
            self.char1.db.level = level
            self.assertEqual(debuff_level_bonus(self.char1), extra, level)

    def test_a_monster_gets_no_level_bonus(self):
        from world.combat import HostileNPC, debuff_level_bonus, poison_floor_for

        npc = create.create_object(HostileNPC, key="a witch", location=self.room1)
        npc.db.level = 90
        self.assertEqual(debuff_level_bonus(npc), 0)
        self.assertEqual(poison_floor_for(npc), 0)

    def test_a_high_level_stat_debuff_lasts_longer(self):
        self.char1.db.level = 60
        self.char1.db.ingenium = 10
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            COMBAT_RULES.spell_add_condition(
                self.char1, "grave chill", [self.char2], 4, conditions=[("Accuracy Down", 4)]
            )
        self.assertEqual(self.char2.db.conditions["Accuracy Down"][0], 4 + 3)

    def test_a_turn_skipping_control_is_not_lengthened(self):
        self.char1.db.level = 100
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            COMBAT_RULES.spell_add_condition(
                self.char1, "omen of ruin", [self.char2], 10,
                conditions=[("Frightened", 2), ("Accuracy Down", 5)],
            )
        self.assertEqual(self.char2.db.conditions["Frightened"][0], 2)
        self.assertEqual(self.char2.db.conditions["Accuracy Down"][0], 5 + 5)

    def test_a_curse_on_an_ally_is_not_lengthened(self):
        self.char1.db.level = 100
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2]
        self.char2.db.party_leader = self.char1
        COMBAT_RULES.spell_add_condition(
            self.char1, "rite of the entrails", [self.char2], 5, conditions=[("Cursed", 4)]
        )
        self.assertEqual(self.char2.db.conditions["Cursed"][0], 4)

    def test_a_players_poison_hits_harder_at_higher_level(self):
        from world.combat import poison_floor_for

        self.char1.db.level = 60
        self.assertEqual(poison_floor_for(self.char1), round(112.5 * 0.35))
        self.char2.db.conditions = {"Poisoned": [4, self.char1]}
        before = self.char2.db.hp
        with patch("world.combat.randint", side_effect=lambda lo, hi: lo):
            COMBAT_RULES.apply_turn_conditions(self.char2)
        self.assertEqual(before - self.char2.db.hp, round(112.5 * 0.35))

    def test_a_low_level_poison_is_never_weaker_than_before(self):
        self.char1.db.level = 1
        self.char2.db.conditions = {"Poisoned": [4, self.char1]}
        before = self.char2.db.hp
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            COMBAT_RULES.apply_turn_conditions(self.char2)
        self.assertGreaterEqual(before - self.char2.db.hp, 12)

    def test_a_monsters_poison_is_unchanged(self):
        from world.combat import HostileNPC

        npc = create.create_object(HostileNPC, key="a viper", location=self.room1)
        npc.db.level = 90
        self.char2.db.conditions = {"Poisoned": [4, npc]}
        before = self.char2.db.hp
        with patch("world.combat.randint", side_effect=lambda lo, hi: lo):
            COMBAT_RULES.apply_turn_conditions(self.char2)
        self.assertLessEqual(before - self.char2.db.hp, 12)


class TestGoad(MartialBase):
    def test_goad_is_a_level_10_legionary_taunt_monsters_never_use(self):
        data = SKILLS["goad"]
        self.assertEqual(data["classes"], ["legionary"])
        self.assertEqual(data["level_required"], 10)
        self.assertEqual(data["conditions"][0][0], "Goaded")
        self.assertIs(data["npc_cast"], False)

    def test_a_goaded_player_is_less_accurate_against_anyone_but_the_goader(self):
        third = create.create_object("typeclasses.characters.Character", key="Third", location=self.room1)
        third.db.conditions = {}
        self.char2.db.conditions = {"Goaded": [3, self.char1]}
        with patch("world.combat.randint", return_value=50):
            at_goader = COMBAT_RULES.get_attack(self.char2, self.char1)
            at_other = COMBAT_RULES.get_attack(self.char2, third)
        self.assertEqual(at_goader - at_other, -martial_penalty())

    def test_goad_lands_through_the_real_skill_and_records_who(self):
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            SKILLS["goad"]["skillfunc"](
                self.char1, "goad", [self.char2], 5, conditions=[("Goaded", 3)]
            )
        self.assertEqual(self.char2.db.conditions["Goaded"][1], self.char1)

    def test_a_goaded_monster_can_only_attack_the_goader(self):
        from world.combat import HostileNPC

        self.char2.location = self.room2  # out of this fight
        other = create.create_object("typeclasses.characters.Character", key="Ally", location=self.room1)
        other.db.hp = other.db.max_hp = 100
        other.db.conditions = {}
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, other]
        other.db.party_leader = self.char1
        npc = create.create_object(HostileNPC, key="a raider", location=self.room1)
        self.room1.scripts.add(CombatTurnHandler)
        npc.db.conditions = {"Goaded": [3, self.char1]}
        npc.db.combat_actionsleft = 1
        with patch.object(COMBAT_RULES, "resolve_attack") as attack, \
                patch.object(COMBAT_RULES, "spend_action"):
            for _ in range(12):
                npc.at_turn_start()
        targets = {call.args[1] for call in attack.call_args_list}
        self.assertEqual(targets, {self.char1})


def martial_penalty():
    from world.combat import GOAD_OFFTARGET_PENALTY

    return GOAD_OFFTARGET_PENALTY


class TestSentinel(MartialBase):
    def setUp(self):
        super().setUp()
        self.ally = create.create_object("typeclasses.characters.Character", key="Ally", location=self.room1)
        self.ally.db.hp = self.ally.db.max_hp = 100000
        self.ally.db.conditions = {}
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.ally]
        self.ally.db.party_leader = self.char1
        self.room1.scripts.add(CombatTurnHandler)
        self.char1.db.conditions = {"Sentinel": [4, self.char1]}
        self.char1.db.combat_sentinel_used = False

    def _foe_hits(self, victim):
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            COMBAT_RULES.resolve_attack(self.char2, victim, attack_value=999, defense_value=0)

    def test_an_enemy_who_attacks_an_ally_takes_a_free_strike(self):
        before = self.char2.db.hp
        self._foe_hits(self.ally)
        self.assertEqual(before - self.char2.db.hp, 100)  # the sentinel's weapon hit

    def test_attacking_the_sentinel_themself_triggers_nothing(self):
        before = self.char2.db.hp
        self._foe_hits(self.char1)
        self.assertEqual(before, self.char2.db.hp)

    def test_it_reacts_only_once_per_turn(self):
        self._foe_hits(self.ally)
        after_first = self.char2.db.hp
        self._foe_hits(self.ally)
        self.assertEqual(self.char2.db.hp, after_first)
        COMBAT_RULES.apply_turn_conditions(self.char1)  # the sentinel's next turn
        self.assertFalse(self.char1.db.combat_sentinel_used)

    def test_a_reaction_never_chains(self):
        self.char2.db.conditions = {"Sentinel": [4, self.char2]}
        third = create.create_object("typeclasses.characters.Character", key="Third", location=self.room1)
        self.char1.db.hp = 100000
        before = self.char1.db.hp
        self._foe_hits(self.ally)
        self.assertLess(before - self.char1.db.hp, 100000)  # finishes, no runaway loop

    def test_it_costs_no_action(self):
        self.char1.db.combat_actionsleft = 1
        self._foe_hits(self.ally)
        self.assertEqual(self.char1.db.combat_actionsleft, 1)

    def test_a_physical_skill_against_an_ally_triggers_it_too(self):
        data = dict(SKILLS["finishing blow"])
        kwargs = {k: v for k, v in data.items() if k in ("weapon_multiplier", "damage_range")}
        before = self.char2.db.hp
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            data["skillfunc"](self.char2, "finishing blow", [self.ally], 8, **kwargs)
        self.assertGreaterEqual(before - self.char2.db.hp, 100)

    def test_no_sentinel_stance_means_no_reaction(self):
        self.char1.db.conditions = {}
        before = self.char2.db.hp
        self._foe_hits(self.ally)
        self.assertEqual(before, self.char2.db.hp)

    def test_sentinel_is_a_level_45_legionary_stance(self):
        data = SKILLS["sentinel"]
        self.assertEqual(data["classes"], ["legionary"])
        self.assertEqual(data["level_required"], 45)
        self.assertEqual(data["target"], "self")
        self.assertIs(data["npc_cast"], False)


class TestRageResistance(MartialBase):
    def test_a_raging_fighter_shrugs_off_over_a_third_of_a_blow(self):
        from world.combat import RAGE_MELEE_RESISTANCE

        self.char2.db.conditions = {"Raging": [4, self.char2]}
        before = self.char2.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        self.assertEqual(before - self.char2.db.hp, int(100 * (1 - RAGE_MELEE_RESISTANCE)))
        self.assertGreater(RAGE_MELEE_RESISTANCE, 0.33)

    def test_it_does_not_soften_a_spell(self):
        self.char2.db.conditions = {"Raging": [4, self.char2]}
        before = self.char2.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=False)
        self.assertEqual(before - self.char2.db.hp, 100)

    def test_ferocity_is_the_upgrade_and_rage_of_the_north_is_unchanged(self):
        ferocity = dict(SKILLS["ferocity"]["conditions"])
        self.assertIn("Raging", ferocity)
        self.assertIn("Damage Up", ferocity)
        self.assertNotIn("Defense Down", ferocity)
        rage = dict(SKILLS["rage of the north"]["conditions"])
        self.assertNotIn("Raging", rage)
        self.assertIn("Defense Down", rage)

    def test_ferocity_grants_it_through_the_real_skill(self):
        SKILLS["ferocity"]["skillfunc"](
            self.char1, "ferocity", [self.char1], 8, conditions=SKILLS["ferocity"]["conditions"]
        )
        self.assertIn("Raging", self.char1.db.conditions)


class TestParryAndShieldBlock(MartialBase):
    def setUp(self):
        super().setUp()
        self.char2.db.wielded_weapon = _weapon(self.char2, 50, 50)  # the defender (char2) has a weapon
        self.char2.db.player_class = "gladiator"

    def _chance_needed(self, name, stat_defender, stat_attacker, stat="agilitas"):
        """The exact percent chance, found by bisecting on a forced roll."""
        setattr(self.char2.db, stat, stat_defender)
        setattr(self.char1.db, stat, stat_attacker)
        self.char2.db.conditions = {name: [99, self.char2]}
        if name == "Shield Block":
            self._armor(self.char2, "worn_shield", reduction=0, defense=5)
        best = 0
        for roll in range(1, 101):
            with patch("world.combat.randint", return_value=roll):
                if COMBAT_RULES._defensive_block(self.char1, self.char2):
                    best = roll
        return best

    def test_the_skills_are_where_the_owner_put_them(self):
        parry, block, guard = SKILLS["parry"], SKILLS["shield block"], SKILLS["barbed guard"]
        self.assertEqual((parry["classes"], parry["level_required"]), (["gladiator"], 35))
        self.assertEqual((block["classes"], block["level_required"]), (["legionary"], 30))
        self.assertEqual((guard["classes"], guard["level_required"]), (["legionary"], 65))
        for data in (parry, block):
            self.assertEqual(data["cooldown"], 0)          # no cooldown
            self.assertEqual(data["conditions"][0][1], 99)  # lasts the whole fight
            self.assertIs(data["noncombat_spell"], False)   # a fight stance
        self.assertEqual(parry["requires"], "weapon")
        self.assertEqual(block["requires"], "shield")
        for data in (parry, block, guard):
            self.assertIs(data["npc_cast"], False)

    def test_the_parry_chance_is_base_plus_two_per_agilitas_over_the_attacker(self):
        self.assertEqual(self._chance_needed("Parrying", 10, 10), 15)
        self.assertEqual(self._chance_needed("Parrying", 18, 10), 15 + 16)
        self.assertEqual(self._chance_needed("Parrying", 18, 18), 15)

    def test_a_nimbler_attacker_beats_the_parry_more_often(self):
        even = self._chance_needed("Parrying", 14, 14)
        nimbler = self._chance_needed("Parrying", 14, 18)
        self.assertLess(nimbler, even)
        self.assertEqual(nimbler, 15 - 8)

    def test_the_chance_is_clamped(self):
        self.assertEqual(self._chance_needed("Parrying", 10, 60), 5)
        self.assertEqual(self._chance_needed("Parrying", 60, 10), 45)

    def test_shield_block_is_opposed_virtus_not_agilitas(self):
        self.assertEqual(self._chance_needed("Shield Block", 16, 10, stat="virtus"), 15 + 12)
        self.assertEqual(self._chance_needed("Shield Block", 10, 16, stat="virtus"), 5)  # 3%, floored
        self.assertEqual(self._chance_needed("Shield Block", 10, 12, stat="virtus"), 15 - 4)

    def test_a_parried_blow_does_no_damage_at_all(self):
        self.char2.db.conditions = {"Parrying": [99, self.char2]}
        before = self.char2.db.hp
        with patch("world.combat.randint", return_value=1):
            COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=999, defense_value=0)
        self.assertEqual(self.char2.db.hp, before)

    def test_a_blow_that_beats_the_parry_lands_normally(self):
        self.char2.db.conditions = {"Parrying": [99, self.char2]}
        before = self.char2.db.hp
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=999, defense_value=0)
        self.assertEqual(before - self.char2.db.hp, 100)

    def test_a_physical_skill_can_be_parried_too(self):
        self.char2.db.conditions = {"Parrying": [99, self.char2]}
        data = dict(SKILLS["finishing blow"])
        kwargs = {k: v for k, v in data.items() if k in ("weapon_multiplier", "damage_range")}
        before = self.char2.db.hp
        with patch("world.combat.randint", return_value=1):
            data["skillfunc"](self.char1, "finishing blow", [self.char2], 8, **kwargs)
        self.assertEqual(self.char2.db.hp, before)

    def test_a_disarmed_gladiator_cannot_parry(self):
        self.char2.db.conditions = {"Parrying": [99, self.char2], "Disarmed": [2, self.char1]}
        self.assertFalse(COMBAT_RULES._defensive_block(self.char1, self.char2))

    def test_a_missing_or_cleaved_shield_cannot_block(self):
        self.char2.db.conditions = {"Shield Block": [99, self.char2]}
        with patch("world.combat.randint", return_value=1):
            self.assertFalse(COMBAT_RULES._defensive_block(self.char1, self.char2))  # no shield
            self._armor(self.char2, "worn_shield", reduction=0, defense=5)
            self.assertTrue(COMBAT_RULES._defensive_block(self.char1, self.char2))
            self.char2.db.combat_sundered = "worn_shield"
            self.assertFalse(COMBAT_RULES._defensive_block(self.char1, self.char2))

    def test_an_unevadable_strike_and_an_incapacitated_defender_are_never_blocked(self):
        self.char2.db.conditions = {"Parrying": [99, self.char2], "Marked for Death": [3, self.char1]}
        with patch("world.combat.randint", return_value=1):
            self.assertFalse(COMBAT_RULES._defensive_block(self.char1, self.char2, marked=True))
            self.char2.db.conditions = {"Parrying": [99, self.char2], "Stunned": [2, self.char1]}
            self.assertFalse(COMBAT_RULES._defensive_block(self.char1, self.char2))

    def test_taking_up_a_stance_needs_its_gear_and_costs_nothing_if_refused(self):
        self.char1.db.wielded_weapon = None
        before = self.char1.db.sp
        self.assertIs(SKILLS["parry"]["skillfunc"](
            self.char1, "parry", [self.char1], 6, conditions=[("Parrying", 99)], requires="weapon"), False)
        self.assertIs(SKILLS["shield block"]["skillfunc"](
            self.char1, "shield block", [self.char1], 6, conditions=[("Shield Block", 99)], requires="shield"), False)
        self.assertEqual(self.char1.db.sp, before)
        self.assertNotIn("Parrying", self.char1.db.conditions)

    def test_the_stance_is_taken_once_and_lasts_until_the_fight_ends(self):
        self.char1.db.wielded_weapon = _weapon(self.char1, 10, 10)
        kwargs = {"conditions": [("Parrying", 99)], "requires": "weapon"}
        SKILLS["parry"]["skillfunc"](self.char1, "parry", [self.char1], 6, **kwargs)
        self.assertIn("Parrying", self.char1.db.conditions)
        self.assertIs(SKILLS["parry"]["skillfunc"](self.char1, "parry", [self.char1], 6, **kwargs), False)
        COMBAT_RULES.combat_cleanup(self.char1)
        self.assertNotIn("Parrying", self.char1.db.conditions)
        self.assertNotIn("Shield Block", self.char1.db.conditions)


class TestBarbedGuard(MartialBase):
    def _guarded(self):
        self.char2.db.conditions = {"Barbed Guard": [4, self.char2]}

    def test_a_quarter_of_a_physical_blow_is_thrown_back(self):
        self._guarded()
        before = self.char1.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        self.assertEqual(before - self.char1.db.hp, 25)
        self.assertEqual(100000 - self.char2.db.hp, 100)  # the guard doesn't lessen the blow

    def test_a_spell_is_not_reflected(self):
        self._guarded()
        before = self.char1.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=False)
        self.assertEqual(before, self.char1.db.hp)

    def test_it_reflects_what_the_target_is_actually_hit_for_after_a_rage(self):
        self.char2.db.conditions = {"Barbed Guard": [4, self.char2], "Raging": [4, self.char2]}
        before = self.char1.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        self.assertEqual(before - self.char1.db.hp, int(65 * 0.25))

    def test_a_blow_soaked_by_a_ward_is_still_thrown_back(self):
        self._guarded()
        wards_module = __import__("world.wards", fromlist=["grant_temp_hp"])
        wards_module.grant_temp_hp(self.char2, 500)
        before = self.char1.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        self.assertEqual(before - self.char1.db.hp, 25)

    def test_a_fully_absorbed_blow_reflects_nothing(self):
        self._guarded()
        self.char2.db.conditions["Shielded"] = [4, self.char2]
        before = self.char1.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        self.assertEqual(before, self.char1.db.hp)

    def test_two_guards_do_not_ping_pong_forever(self):
        self._guarded()
        self.char1.db.conditions = {"Barbed Guard": [4, self.char1]}
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        self.assertGreater(self.char1.db.hp, 99000)

    def test_a_reflected_blow_can_finish_the_attacker(self):
        self._guarded()
        self.char1.db.hp = 10
        with patch.object(COMBAT_RULES, "at_defeat") as defeated:
            COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        defeated.assert_called_once_with(self.char1, attacker=self.char2)

    def test_it_lasts_a_few_turns_not_the_whole_fight(self):
        self.assertEqual(SKILLS["barbed guard"]["conditions"][0], ("Barbed Guard", 4))
        self.assertEqual(SKILLS["barbed guard"]["level_required"], 65)


class TestCritChancePerStrike(MartialBase):
    def test_the_numbers_a_player_can_be_told(self):
        table = {}
        for category in ("light_blade", "heavy_blade", "ranged", "polearm", "heavy_weapon", "staff"):
            self.char1.db.wielded_weapon = _weapon(self.char1, 10, 10, category=category)
            self.char1.db.agilitas = 10
            base = martial.crit_profile(self.char1)[0]
            self.char1.db.agilitas = 18
            table[category] = (base, martial.crit_profile(self.char1)[0])
        self.assertEqual(table["light_blade"], (10, 14.0))
        self.assertEqual(table["heavy_blade"], (8, 12.0))
        self.assertEqual(table["ranged"], (8, 12.0))
        self.assertEqual(table["polearm"], (5, 9.0))
        self.assertEqual(table["heavy_weapon"], (5, 9.0))
        self.assertEqual(table["staff"], (5, 9.0))


class TestSpeculatorSkills(MartialBase):
    def setUp(self):
        super().setUp()
        self.char1.db.player_class = "speculator"

    def test_the_new_speculator_lineup(self):
        expected = {"slip away": 30, "fast hands": 40, "pilfer": 50, "uncanny dodge": 55,
                    "elusive footwork": 65, "assassinate": 70}
        for name, level in expected.items():
            self.assertEqual(SKILLS[name]["classes"], ["speculator"], name)
            self.assertEqual(SKILLS[name]["level_required"], level, name)
            self.assertIs(SKILLS[name]["npc_cast"], False, name)

    def test_the_two_defensive_ones_are_passives_that_cost_no_action(self):
        for name in ("uncanny dodge", "elusive footwork"):
            self.assertEqual(SKILLS[name]["cost"], 0)
            self.assertIs(SKILLS[name]["skillfunc"].__func__, COMBAT_RULES.skill_passive_info.__func__)

    # --- Slip Away ---
    def test_slip_away_is_a_guaranteed_free_escape(self):
        handler = self._fight()
        self.char1.db.xp = 500
        with patch("world.combat.randint", return_value=100):  # a roll that would fail a normal flee
            self.assertIsNot(SKILLS["slip away"]["skillfunc"](self.char1, "slip away", [self.char1], 6), False)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))
        self.assertEqual(self.char1.db.xp, 500)  # no XP penalty

    def test_slip_away_is_refused_when_grappled_or_out_of_a_fight(self):
        self.assertIs(SKILLS["slip away"]["skillfunc"](self.char1, "slip away", [self.char1], 6), False)
        self._fight()
        self.char1.db.conditions = {"Grappled": [3, self.char2]}
        self.assertIs(SKILLS["slip away"]["skillfunc"](self.char1, "slip away", [self.char1], 6), False)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))

    # --- Fast Hands ---
    def test_fast_hands_makes_an_item_free_in_a_fight(self):
        self._fight()
        self.char1.db.combat_actionsleft = 1
        self.char1.db.hp = 50
        tonic = create.create_object("typeclasses.objects.Object", key="a tonic", location=self.char1,
                                     attributes=[("item_func", "heal"), ("item_kwargs", {"healing_range": (10, 10)})])
        self.char1.db.conditions = {"Fast Hands": [4, self.char1]}
        COMBAT_RULES.use_item(self.char1, tonic, self.char1)
        self.assertEqual(self.char1.db.combat_actionsleft, 1)  # the action is still there
        self.assertEqual(self.char1.db.hp, 60)

    def test_without_fast_hands_an_item_still_costs_the_action(self):
        self._fight()
        self.char1.db.combat_actionsleft = 1
        self.char1.db.hp = 50
        tonic = create.create_object("typeclasses.objects.Object", key="a tonic", location=self.char1,
                                     attributes=[("item_func", "heal"), ("item_kwargs", {"healing_range": (10, 10)})])
        COMBAT_RULES.use_item(self.char1, tonic, self.char1)
        self.assertNotEqual(self.char1.db.combat_actionsleft, 1)

    # --- Uncanny Dodge & Evasion ---
    def test_uncanny_dodge_halves_a_physical_blow_then_rests(self):
        self.char2.db.skills_known = ["uncanny dodge"]
        before = self.char2.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        self.assertEqual(before - self.char2.db.hp, 50)
        self.assertEqual(COMBAT_RULES.get_cooldowns(self.char2)["uncanny dodge"], 4)
        mid = self.char2.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        self.assertEqual(mid - self.char2.db.hp, 100)  # on cooldown: takes it in full

    def test_uncanny_dodge_does_not_soften_a_spell_and_needs_the_skill(self):
        self.char2.db.skills_known = ["uncanny dodge"]
        before = self.char2.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=False)
        self.assertEqual(before - self.char2.db.hp, 100)
        self.char2.db.skills_known = []
        before = self.char2.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        self.assertEqual(before - self.char2.db.hp, 100)

    def test_a_stunned_speculator_cannot_dodge(self):
        self.char2.db.skills_known = ["uncanny dodge"]
        self.char2.db.conditions = {"Stunned": [2, self.char1]}
        before = self.char2.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1, melee=True)
        self.assertEqual(before - self.char2.db.hp, 100)

    def test_elusive_footwork_halves_area_damage_only(self):
        self.char2.db.skills_known = ["elusive footwork"]
        third = create.create_object("typeclasses.characters.Character", key="Third", location=self.room1)
        third.db.max_hp = third.db.hp = 100000
        third.db.conditions = {}
        data = dict(SKILLS["whirlwind"])
        kwargs = {k: v for k, v in data.items() if k in ("weapon_multiplier", "damage_range")}
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            data["skillfunc"](self.char1, "whirlwind", [self.char2, third], 11, **kwargs)
        self.assertEqual(100000 - third.db.hp, 130)
        self.assertEqual(100000 - self.char2.db.hp, 65)   # halved
        self.char2.db.hp = 100000
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            data["skillfunc"](self.char1, "finishing blow", [self.char2], 8, **{
                k: v for k, v in SKILLS["finishing blow"].items() if k in ("weapon_multiplier", "damage_range")})
        self.assertEqual(100000 - self.char2.db.hp, 160)  # a single-target blow is not halved

    # --- Assassinate ---
    def test_assassinate_needs_the_hiding_sneak_and_vanish_leave(self):
        self.assertIs(SKILLS["assassinate"]["skillfunc"](
            self.char1, "assassinate", [self.char2], 12,
            weapon_multiplier=2.5, damage_range=(60, 90)), False)
        self.assertEqual(self.char2.db.hp, 100000)

    def test_from_hiding_it_is_a_guaranteed_critical_at_two_and_a_half_times(self):
        self.char1.db.conditions = {"Invisible": [3, self.char1]}
        SKILLS["assassinate"]["skillfunc"](
            self.char1, "assassinate", [self.char2], 12, weapon_multiplier=2.5, damage_range=(60, 90))
        # weapon 100 x crit 2.0 x 2.5
        self.assertEqual(100000 - self.char2.db.hp, 500)
        self.assertNotIn("Invisible", self.char1.db.conditions)  # the hiding is spent

    def test_sneak_and_vanish_really_leave_the_state_assassinate_needs(self):
        self.assertEqual(SKILLS["sneak"]["conditions"][0][0], "Invisible")
        self.assertEqual(SKILLS["vanish"]["conditions"][0][0], "Invisible")

    # --- Pilfer ---
    def _pilfer(self, target=None, rolls=1):
        target = target or self.char2
        with patch("world.combat.randint", return_value=rolls):
            return SKILLS["pilfer"]["skillfunc"](self.char1, "pilfer", [target], 5)

    def test_a_successful_pilfer_moves_a_tenth_of_a_players_purse(self):
        self.char2.db.gold = 1000
        self.char1.db.gold = 0
        self._pilfer()
        self.assertEqual(self.char1.db.gold, 100)
        self.assertEqual(self.char2.db.gold, 900)

    def test_the_take_is_capped_by_the_thiefs_level(self):
        self.char2.db.gold = 100000
        self.char1.db.level = 30
        self.char1.db.gold = 0
        self._pilfer()
        self.assertEqual(self.char1.db.gold, 25 + 5 * 30)

    def test_the_victim_is_told_something_was_taken_but_not_who(self):
        self.char2.db.gold = 1000
        with patch.object(self.char2, "msg") as told:
            self._pilfer()
        text = " ".join(str(c) for c in told.call_args_list)
        self.assertIn("lighter", text)
        self.assertNotIn("Char,", text)

    def test_a_nimble_target_is_hard_to_rob(self):
        self.char2.db.gold = 1000
        self.char1.db.agilitas, self.char2.db.agilitas = 10, 30
        self.char1.db.gold = 0
        self._pilfer(rolls=20)  # 35 + 3*(10-30) = -25 -> 5% chance; a roll of 20 fails
        self.assertEqual(self.char1.db.gold, 0)
        self.assertEqual(self.char2.db.gold, 1000)

    def test_a_clumsy_target_is_easy(self):
        self.char2.db.gold = 1000
        self.char1.db.agilitas, self.char2.db.agilitas = 18, 10
        self.char1.db.gold = 0
        self._pilfer(rolls=55)  # 35 + 24 = 59%
        self.assertGreater(self.char1.db.gold, 0)

    def test_a_target_is_only_tried_once_per_half_hour(self):
        self.char2.db.gold = 1000
        self._pilfer()
        self.assertIs(self._pilfer(), False)

    def test_it_never_works_on_a_pacifist_a_god_an_ally_or_an_empty_purse(self):
        self.char2.db.gold = 1000
        self.char2.db.pacifist = True
        self.assertIs(self._pilfer(), False)
        self.char2.db.pacifist = False
        self.char2.db.level = 106
        self.assertIs(self._pilfer(), False)
        self.char2.db.level = 30
        self.char2.db.gold = 3
        self.assertIs(self._pilfer(), False)
        self.char2.db.gold = 1000
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2]
        self.char2.db.party_leader = self.char1
        self.assertIs(self._pilfer(), False)

    def test_a_refused_pilfer_costs_nothing(self):
        self.char2.db.pacifist = True
        before = self.char1.db.sp
        self._pilfer()
        self.assertEqual(before, self.char1.db.sp)

    def test_an_npc_yields_half_of_its_kill_gold_and_pilfer_never_starts_a_fight(self):
        from world.combat import HostileNPC

        npc = create.create_object(HostileNPC, key="a merchant guard", location=self.room1,
                                   attributes=[("xp_reward", 60)])
        self.char1.db.gold = 0
        self._pilfer(target=npc)
        self.assertEqual(self.char1.db.gold, 10)  # 60 xp -> 20 gold -> half
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_pilfer_is_flagged_so_the_command_never_starts_a_fight_or_reveals_you_early(self):
        self.assertTrue(SKILLS["pilfer"]["no_fight_start"])
        self.assertTrue(SKILLS["pilfer"]["manages_reveal"])
        self.assertIs(SKILLS["pilfer"]["combat_spell"], False)


class TestVenatorSkills(MartialBase):
    def setUp(self):
        super().setUp()
        self.char1.db.player_class = "venator"
        self.char1.db.wielded_weapon = _weapon(self.char1, 100, 100, category="ranged")

    def test_the_new_venator_lineup(self):
        expected = {"quarry": 1, "forager's eye": 25, "aimed shot": 45, "pathfinder": 55, "bestial fury": 75}
        for name, level in expected.items():
            self.assertEqual(SKILLS[name]["classes"], ["venator"], name)
            self.assertEqual(SKILLS[name]["level_required"], level, name)
            self.assertIs(SKILLS[name]["npc_cast"], False, name)
        self.assertNotIn("mark", SKILLS)

    # --- Quarry ---
    def test_quarry_boosts_only_the_hunters_own_blows_against_it(self):
        self._fight()
        SKILLS["quarry"]["skillfunc"](self.char1, "quarry", [self.char2], 4)
        self.assertIn("Quarry", self.char2.db.conditions)
        before = self.char2.db.hp
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=self.char1)
        self.assertEqual(before - self.char2.db.hp, 120)
        before = self.char2.db.hp
        third = create.create_object("typeclasses.characters.Character", key="Third", location=self.room1)
        COMBAT_RULES.apply_damage(self.char2, 100, attacker=third)
        self.assertEqual(before - self.char2.db.hp, 100)  # someone else's blow: no bonus

    def test_marking_a_new_quarry_drops_the_old_one(self):
        third = create.create_object("typeclasses.characters.Character", key="Third", location=self.room1)
        third.db.hp = third.db.max_hp = 100
        third.db.conditions = {}
        self.room1.scripts.add(CombatTurnHandler)
        SKILLS["quarry"]["skillfunc"](self.char1, "quarry", [self.char2], 4)
        SKILLS["quarry"]["skillfunc"](self.char1, "quarry", [third], 4)
        self.assertNotIn("Quarry", self.char2.db.conditions)
        self.assertIn("Quarry", third.db.conditions)

    def test_quarry_ends_with_the_fight_and_is_never_a_debuff_on_an_ally(self):
        self._fight()
        SKILLS["quarry"]["skillfunc"](self.char1, "quarry", [self.char2], 4)
        COMBAT_RULES.combat_cleanup(self.char2)
        self.assertNotIn("Quarry", self.char2.db.conditions)
        self.assertIs(SKILLS["quarry"]["skillfunc"](self.char1, "quarry", [self.char1], 4), False)

    def test_quarry_is_a_fight_only_skill_that_never_starts_one(self):
        self.assertIs(SKILLS["quarry"]["noncombat_spell"], False)
        self.assertTrue(SKILLS["quarry"]["no_fight_start"])

    def test_a_player_who_knew_mark_now_knows_quarry(self):
        from world import concentration as conc

        self.char1.db.skills_known = ["mark", "keen eye"]
        self.char1.db.cooldowns = {"mark": 2}
        conc.prune_renamed_skills(self.char1)
        self.assertEqual(sorted(self.char1.db.skills_known), ["keen eye", "quarry"])
        self.assertEqual(self.char1.db.cooldowns.get("quarry"), 2)
        conc.prune_renamed_skills(self.char1)  # idempotent
        self.assertEqual(self.char1.db.skills_known.count("quarry"), 1)

    def test_a_new_venator_starts_with_quarry(self):
        from world.chargen_menu import CLASSES

        self.assertEqual(CLASSES["venator"]["starting_skills"], ["quarry"])

    # --- Aimed Shot ---
    def test_aimed_shot_needs_a_ranged_weapon_and_costs_the_turn(self):
        self.char1.db.wielded_weapon = _weapon(self.char1, 100, 100, category="light_blade")
        self.assertIs(SKILLS["aimed shot"]["skillfunc"](self.char1, "aimed shot", [self.char1], 6), False)
        self.char1.db.wielded_weapon = _weapon(self.char1, 100, 100, category="ranged")
        SKILLS["aimed shot"]["skillfunc"](self.char1, "aimed shot", [self.char1], 6)
        self.assertIn("Aiming", self.char1.db.conditions)

    def test_the_aimed_shot_cannot_miss_and_hits_two_and_a_half_times_then_is_spent(self):
        self.char1.db.conditions = {"Aiming": [3, self.char1]}
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=0, defense_value=999)
        self.assertEqual(100000 - self.char2.db.hp, int(100 * 2.5))
        self.assertNotIn("Aiming", self.char1.db.conditions)

    def test_the_shot_after_the_aimed_one_is_ordinary(self):
        self.char1.db.conditions = {"Aiming": [3, self.char1]}
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=999, defense_value=0)
            self.char2.db.hp = 100000
            COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=999, defense_value=0)
        self.assertEqual(100000 - self.char2.db.hp, 100)

    def test_an_aimed_shot_cannot_be_parried(self):
        self.char2.db.conditions = {"Parrying": [99, self.char2]}
        self.char2.db.wielded_weapon = _weapon(self.char2, 50, 50)
        self.char1.db.conditions = {"Aiming": [3, self.char1]}
        with patch("world.combat.randint", return_value=1):  # a sure parry, if it were allowed
            COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=0, defense_value=999)
        self.assertLess(self.char2.db.hp, 100000)

    def test_an_aimed_skill_also_spends_the_aim(self):
        self.char1.db.conditions = {"Aiming": [3, self.char1]}
        data = dict(SKILLS["piercing shot"])
        kwargs = {k: v for k, v in data.items() if k in ("weapon_multiplier", "damage_range")}
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            SKILLS["rapid volley"]["skillfunc"](
                self.char1, "rapid volley", [self.char2], 8,
                **{k: v for k, v in SKILLS["rapid volley"].items() if k in ("weapon_multiplier", "damage_range")})
        self.assertNotIn("Aiming", self.char1.db.conditions)

    # --- Pathfinder ---
    def test_pathfinder_makes_every_other_step_free(self):
        self.char1.db.conditions = {"Pathfinding": [20, self.char1]}
        start = self.char1.db.sp
        for _ in range(8):
            self.assertTrue(self.char1._check_and_pay_movement_sp("move"))
        self.assertEqual(self.char1.db.sp, start - 4)

    def test_flight_is_the_better_discount_when_both_apply(self):
        from world import concentration as conc

        self.char1.db.conditions = {"Pathfinding": [20, self.char1]}
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        start = self.char1.db.sp
        for _ in range(8):
            self.char1._check_and_pay_movement_sp("move")
        self.assertEqual(self.char1.db.sp, start - 2)

    # --- Forager's Eye ---
    def test_foragers_eye_raises_the_chance_to_spot_a_resource(self):
        from world import gathering

        self.room1.db.gather_resource = "timber"
        self.room1.db.gather_uses_wilderness_chance = True  # the plain 30% chance
        with patch("world.gathering.random.random", return_value=0.5):
            gathering.announce_gather_spot(self.char1)
            plain = self.char1.ndb.gather_spot
            self.char1.db.conditions = {"Forager's Eye": [20, self.char1]}
            gathering.announce_gather_spot(self.char1)
            with_eye = self.char1.ndb.gather_spot
        self.assertIsNone(plain)          # 0.5 is not under 0.30
        self.assertEqual(with_eye, "timber")  # 0.5 is under 0.30 + 0.30

    # --- Bestial Fury ---
    def _pet(self):
        from world.combat import SummonedAlly

        pet = create.create_object(SummonedAlly, key="a hunting hound", location=self.room1)
        pet.db.hp = pet.db.max_hp = 500
        pet.db.instance_owner = self.char1
        self.char1.db.active_companion = pet
        return pet

    def test_it_needs_a_companion_and_costs_nothing_if_refused(self):
        before = self.char1.db.sp
        self.assertIs(SKILLS["bestial fury"]["skillfunc"](self.char1, "bestial fury", [], 9), False)
        self.assertEqual(before, self.char1.db.sp)

    def test_a_frenzied_companion_attacks_twice_each_turn(self):
        pet = self._pet()
        self.room1.ndb.pending_fighters = [self.char1, self.char2]
        self.room1.scripts.add(CombatTurnHandler)
        SKILLS["bestial fury"]["skillfunc"](self.char1, "bestial fury", [], 9)
        self.assertIn("Frenzied", pet.db.conditions)
        self.char1.db.combat_last_target = self.char2
        pet.db.combat_actionsleft = 1
        with patch.object(COMBAT_RULES, "resolve_attack") as strike, patch.object(COMBAT_RULES, "spend_action"):
            pet.at_turn_start()
        self.assertEqual(strike.call_count, 2)

    def test_an_ordinary_companion_attacks_once(self):
        pet = self._pet()
        self.room1.ndb.pending_fighters = [self.char1, self.char2]
        self.room1.scripts.add(CombatTurnHandler)
        self.char1.db.combat_last_target = self.char2
        pet.db.combat_actionsleft = 1
        with patch.object(COMBAT_RULES, "resolve_attack") as strike, patch.object(COMBAT_RULES, "spend_action"):
            pet.at_turn_start()
        self.assertEqual(strike.call_count, 1)

    def test_the_frenzy_is_worth_more_than_the_attack_it_costs(self):
        # Three extra companion attacks for one lost personal attack.
        self.assertEqual(SKILLS["bestial fury"]["cost"], 9)
        self.assertIn("three extra attacks", SKILLS["bestial fury"]["desc"])


class TestOverlapCleanup(MartialBase):
    def test_no_speculator_or_venator_skill_is_a_caster_debuff_any_more(self):
        casters = {"Accuracy Down", "Damage Down", "Defense Down", "Cursed", "Frightened"}
        for name, data in SKILLS.items():
            if not ({"speculator", "venator"} & set(data.get("classes", []))):
                continue
            for cond, _ in data.get("conditions", []):
                self.assertNotIn(cond, casters, name)

    def test_the_debuff_skills_became_real_strikes_with_martial_riders(self):
        for name, effect in (("precision strike", "Disarmed"), ("crippling strike", "Sundered")):
            data = SKILLS[name]
            self.assertIs(data["skillfunc"].__func__, COMBAT_RULES.skill_attack.__func__, name)
            self.assertEqual(data["rider"]["effect"], effect, name)
            self.assertGreater(data["weapon_multiplier"], 1.0, name)

    def test_entangle_is_now_a_net_that_grapples(self):
        self.assertEqual(SKILLS["entangle"]["conditions"], [("Grappled", 3)])

    def test_poison_is_the_speculators_alone_among_the_scouts(self):
        for name, data in SKILLS.items():
            if "venator" in data.get("classes", []):
                self.assertNotIn("Poisoned", [c for c, _ in data.get("conditions", [])], name)
        self.assertEqual(SKILLS["poisoned blade"]["classes"], ["speculator"])

    def test_the_class_labels_match_what_each_actually_is(self):
        from world.chargen_menu import CLASSES

        self.assertIn("Rogue/Assassin", CLASSES["speculator"]["display"])
        self.assertIn("Ranger/Scout", CLASSES["venator"]["display"])


class TestBackstabOpensAFight(MartialBase):
    def test_backstab_can_start_the_fight_and_lands_at_once(self):
        from world.combat import CmdUseSkill

        self.char1.db.player_class = "speculator"
        self.char1.db.skills_known = ["backstab"]
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))
        before = self.char2.db.hp
        with patch("world.combat.randint", side_effect=lambda lo, hi: hi):
            self.call(CmdUseSkill(), "backstab = Char2", caller=self.char1)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))
        self.assertGreater(before - self.char2.db.hp, 0)

    def test_backstab_is_no_longer_flagged_combat_only(self):
        self.assertNotIn("noncombat_spell", SKILLS["backstab"])
        self.assertIn("open a fight", SKILLS["backstab"]["desc"])

    def test_backstab_still_needs_a_target_that_has_not_acted(self):
        self._fight()
        self.char2.db.combat_lastaction = "attack"
        before = self.char2.db.hp
        SKILLS["backstab"]["skillfunc"](self.char1, "backstab", [self.char2], 6, weapon_multiplier=2.0, bonus_damage=20)
        self.assertEqual(self.char2.db.hp, before)


class TestAreaTargetsFillFromTheFight(MartialBase):
    def setUp(self):
        super().setUp()
        from world.combat import HostileNPC

        self.char2.location = self.room2  # keep the arithmetic to the goblins
        self.goblins = []
        for n in range(1, 4):
            g = create.create_object(HostileNPC, key="goblin %d" % n, location=self.room1)
            g.db.hp = g.db.max_hp = 50
            self.goblins.append(g)

    def _start(self, count):
        for extra in self.goblins[count:]:
            extra.location = self.room2
        handler = self.room1.scripts.add(CombatTurnHandler)
        handler.db.turn = handler.db.fighters.index(self.char1)
        self.char1.db.combat_actionsleft = 1
        self.char1.db.player_class = "venator"
        self.char1.db.skills_known = ["rapid volley"]
        self.char1.db.spells_known = ["soul rot"]
        self.char1.db.sp = self.char1.db.mp = 100
        return handler

    def _targets_used(self, command, arg, count, table, name):
        from unittest.mock import MagicMock

        self._start(count)
        spy = MagicMock(return_value=None)
        with patch.dict(table[name], {("skillfunc" if table is SKILLS else "spellfunc"): spy}):
            self.call(command(), arg, caller=self.char1)
        return spy.call_args[0][2]

    def test_a_three_target_skill_takes_three_enemies_from_the_fight(self):
        from world.combat import CmdUseSkill

        targets = self._targets_used(CmdUseSkill, "rapid volley = goblin 1", 3, SKILLS, "rapid volley")
        self.assertEqual(sorted(t.key for t in targets), ["goblin 1", "goblin 2", "goblin 3"])
        self.assertEqual(targets[0].key, "goblin 1")  # the one you named comes first

    def test_with_only_two_enemies_it_takes_two(self):
        from world.combat import CmdUseSkill

        targets = self._targets_used(CmdUseSkill, "rapid volley = goblin 2", 2, SKILLS, "rapid volley")
        self.assertEqual(sorted(t.key for t in targets), ["goblin 1", "goblin 2"])

    def test_with_one_enemy_it_takes_one(self):
        from world.combat import CmdUseSkill

        targets = self._targets_used(CmdUseSkill, "rapid volley = goblin 1", 1, SKILLS, "rapid volley")
        self.assertEqual([t.key for t in targets], ["goblin 1"])

    def test_naming_no_one_takes_up_to_three_as_before(self):
        from world.combat import CmdUseSkill

        targets = self._targets_used(CmdUseSkill, "rapid volley", 3, SKILLS, "rapid volley")
        self.assertEqual(len(targets), 3)

    def test_a_three_target_spell_fills_the_same_way(self):
        targets = self._targets_used(CmdCast, "soul rot = goblin 3", 3, SPELLS, "soul rot")
        self.assertEqual(sorted(t.key for t in targets), ["goblin 1", "goblin 2", "goblin 3"])
        self.assertEqual(targets[0].key, "goblin 3")

    def test_it_never_pulls_in_an_ally_or_a_bystander_who_is_not_in_the_fight(self):
        from world.combat import CmdUseSkill, HostileNPC

        ally = create.create_object("typeclasses.characters.Character", key="Ally", location=self.room1)
        ally.db.hp = ally.db.max_hp = 100
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, ally]
        ally.db.party_leader = self.char1
        self._start(1)
        bystander = create.create_object(HostileNPC, key="a passing vendor", location=self.room1)
        bystander.db.hp = bystander.db.max_hp = 50
        from unittest.mock import MagicMock

        spy = MagicMock(return_value=None)
        with patch.dict(SKILLS["rapid volley"], {"skillfunc": spy}):
            self.call(CmdUseSkill(), "rapid volley = goblin 1", caller=self.char1)
        names = {t.key for t in spy.call_args[0][2]}
        self.assertNotIn("Ally", names)
        self.assertNotIn("a passing vendor", names)

    def test_a_physical_skill_skips_an_enemy_it_could_not_reach_but_a_spell_does_not(self):
        from world.combat import CmdUseSkill

        self._start(3)
        self.goblins[2].db.combat_row = "back"
        self.assertTrue(COMBAT_RULES.is_row_protected(self.goblins[2]))
        from unittest.mock import MagicMock

        spy = MagicMock(return_value=None)
        with patch.dict(SKILLS["rapid volley"], {"skillfunc": spy}):
            self.call(CmdUseSkill(), "rapid volley = goblin 1", caller=self.char1)
        self.assertNotIn("goblin 3", {t.key for t in spy.call_args[0][2]})
        self.char1.db.combat_actionsleft = 1
        spy = MagicMock(return_value=None)
        with patch.dict(SPELLS["soul rot"], {"spellfunc": spy}):
            self.call(CmdCast(), "soul rot = goblin 1", caller=self.char1)
        self.assertIn("goblin 3", {t.key for t in spy.call_args[0][2]})

    def test_a_single_target_skill_is_untouched(self):
        from world.combat import CmdUseSkill

        targets = self._targets_used(CmdUseSkill, "rapid volley = goblin 1", 3, SKILLS, "rapid volley")
        self.assertEqual(SKILLS["finishing blow"].get("max_targets", 1), 1)
        self.assertGreater(len(targets), 1)


class TestGroupBuffsPickThePartyThemselves(MartialBase):
    """Owner request: type 'testudo' and it picks up to five allies if they exist."""

    def setUp(self):
        super().setUp()
        self.char1.db.player_class = "legionary"
        self.char1.db.skills_known = ["testudo"]
        self.char1.db.spells_known = ["mass cure wounds"]
        self.char1.db.sp = self.char1.db.mp = 100
        self.allies = []

    def _party(self, count, wounded=None):
        members = [self.char1]
        for n in range(count):
            ally = create.create_object("typeclasses.characters.Character", key="Friend%d" % n, location=self.room1)
            ally.db.hp = ally.db.max_hp = 100
            ally.db.conditions = {}
            members.append(ally)
            ally.db.party_leader = self.char1
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = members
        return members

    def _skill_targets(self, arg="testudo"):
        from unittest.mock import MagicMock

        from world.combat import CmdUseSkill

        spy = MagicMock(return_value=None)
        with patch.dict(SKILLS["testudo"], {"skillfunc": spy}):
            self.call(CmdUseSkill(), arg, caller=self.char1)
        return spy.call_args[0][2]

    def test_alone_it_is_just_you_as_before(self):
        self.assertEqual(self._skill_targets(), [self.char1])

    def test_it_picks_the_whole_party_here_including_you(self):
        self._party(3)
        self.assertEqual(len(self._skill_targets()), 4)

    def test_it_stops_at_five_and_prefers_the_most_wounded(self):
        members = self._party(6)
        members[3].db.hp = 10
        members[5].db.hp = 30
        picked = self._skill_targets()
        self.assertEqual(len(picked), 5)
        self.assertIn(members[3], picked)
        self.assertIn(members[5], picked)

    def test_a_party_member_in_another_room_is_left_out(self):
        members = self._party(2)
        members[2].location = self.room2
        picked = self._skill_targets()
        self.assertNotIn(members[2], picked)
        self.assertEqual(len(picked), 2)

    def test_a_dead_party_member_is_left_out(self):
        members = self._party(2)
        members[1].db.is_dead = True
        self.assertNotIn(members[1], self._skill_targets())

    def test_naming_a_target_still_targets_only_that_one(self):
        members = self._party(2)
        picked = self._skill_targets("testudo = Friend0")
        self.assertEqual([t.key for t in picked], ["Friend0"])

    def test_the_party_keyword_still_works(self):
        self._party(2)
        self.assertEqual(len(self._skill_targets("testudo = party")), 3)

    def test_a_group_spell_does_the_same(self):
        from unittest.mock import MagicMock

        self._party(3)
        spy = MagicMock(return_value=None)
        with patch.dict(SPELLS["mass cure wounds"], {"spellfunc": spy}):
            self.call(CmdCast(), "mass cure wounds", caller=self.char1)
        self.assertEqual(len(spy.call_args[0][2]), 4)

    def test_a_single_target_heal_still_defaults_to_you(self):
        from unittest.mock import MagicMock

        self._party(3)
        self.char1.db.spells_known = ["cure wounds"]
        spy = MagicMock(return_value=None)
        with patch.dict(SPELLS["cure wounds"], {"spellfunc": spy}):
            self.call(CmdCast(), "cure wounds", caller=self.char1)
        self.assertEqual(spy.call_args[0][2], [self.char1])

    def test_the_descriptions_no_longer_tell_you_to_type_equals_party(self):
        for name in ("testudo", "rally"):
            self.assertNotIn("= party", SKILLS[name]["desc"], name)
            self.assertIn("automatically", SKILLS[name]["desc"], name)


class TestFightingRetreat(MartialBase):
    def setUp(self):
        super().setUp()
        self.char1.db.player_class = "legionary"
        self.allies = []
        for n in range(2):
            a = create.create_object("typeclasses.characters.Character", key="Comrade%d" % n, location=self.room1)
            a.db.hp = a.db.max_hp = 100
            a.db.conditions = {}
            a.db.party_leader = self.char1
            self.allies.append(a)
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1] + self.allies
        self.handler = self.room1.scripts.add(CombatTurnHandler)  # sweeps everyone in the room in

    def _retreat(self, targets):
        return SKILLS["fighting retreat"]["skillfunc"](self.char1, "fighting retreat", targets, 10)

    def test_it_is_a_level_50_legionary_group_skill(self):
        data = SKILLS["fighting retreat"]
        self.assertEqual((data["classes"], data["level_required"], data["max_targets"]), (["legionary"], 50, 5))
        self.assertEqual(data["target"], "anychar")
        self.assertIs(data["npc_cast"], False)

    def test_the_whole_party_breaks_away_at_once(self):
        for member in [self.char1] + self.allies:
            self.assertTrue(COMBAT_RULES.is_in_combat(member))
        self._retreat([self.char1] + self.allies)
        for member in [self.char1] + self.allies:
            self.assertFalse(COMBAT_RULES.is_in_combat(member))

    def test_nobody_loses_experience(self):
        for member in [self.char1] + self.allies:
            member.db.xp = 500
        with patch("world.combat.randint", return_value=100):  # would fail an ordinary flee
            self._retreat([self.char1] + self.allies)
        for member in [self.char1] + self.allies:
            self.assertEqual(member.db.xp, 500)

    def test_naming_only_some_keeps_the_rest_in_the_fight(self):
        self._retreat(self.allies)
        for ally in self.allies:
            self.assertFalse(COMBAT_RULES.is_in_combat(ally))
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))

    def test_a_grappled_or_stunned_ally_cannot_be_pulled_out(self):
        self.allies[0].db.conditions = {"Grappled": [3, self.char2]}
        self.allies[1].db.conditions = {"Stunned": [2, self.char2]}
        self._retreat([self.char1] + self.allies)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.allies[0]))
        self.assertTrue(COMBAT_RULES.is_in_combat(self.allies[1]))
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_it_is_refused_outside_a_fight_and_costs_nothing(self):
        for member in [self.char1] + self.allies:
            COMBAT_RULES.force_disengage(member)
        before = self.char1.db.sp
        self.assertIs(self._retreat([self.char1] + self.allies), False)
        self.assertEqual(before, self.char1.db.sp)

    def test_it_is_refused_when_no_one_can_move(self):
        for member in [self.char1] + self.allies:
            member.db.conditions = {"Grappled": [3, self.char2]}
        before = self.char1.db.sp
        self.assertIs(self._retreat([self.char1] + self.allies), False)
        self.assertEqual(before, self.char1.db.sp)

    def test_typing_it_with_no_target_picks_the_party_automatically(self):
        from unittest.mock import MagicMock

        from world.combat import CmdUseSkill

        self.char1.db.skills_known = ["fighting retreat"]
        self.handler.db.turn = self.handler.db.fighters.index(self.char1)
        self.char1.db.combat_actionsleft = 1
        spy = MagicMock(return_value=None)
        with patch.dict(SKILLS["fighting retreat"], {"skillfunc": spy}):
            self.call(CmdUseSkill(), "fighting retreat", caller=self.char1)
        self.assertEqual({t.key for t in spy.call_args[0][2]}, {"Char", "Comrade0", "Comrade1"})


class TestOverlapFixPass(MartialBase):
    """Sep 27 consolidation: Provoke/Goad, Cleave/Shattering Blow, Gladiator and War Cry."""

    def test_provoke_is_gone_and_its_owners_get_goad(self):
        from world import concentration as conc

        self.assertNotIn("provoke", SKILLS)
        self.char1.db.skills_known = ["provoke", "hold the line"]
        conc.prune_renamed_skills(self.char1)
        self.assertEqual(sorted(self.char1.db.skills_known), ["goad", "hold the line"])

    def test_favor_became_crowds_surge(self):
        from world import concentration as conc

        self.assertNotIn("favor", SKILLS)
        self.char1.db.skills_known = ["favor"]
        conc.prune_renamed_skills(self.char1)
        self.assertEqual(self.char1.db.skills_known, ["crowd's surge"])

    def test_cleave_is_a_pure_area_attack_and_shattering_blow_the_armor_breaker(self):
        self.assertNotIn("rider", SKILLS["gladius cleave"])
        self.assertEqual(SKILLS["gladius cleave"]["max_targets"], 3)
        rider = SKILLS["shattering blow"]["rider"]
        self.assertEqual((rider["effect"], rider["chance"], rider["both"]), ("Sundered", 100, True))

    def test_shattering_blow_breaks_body_armor_and_shield_together(self):
        self._armor(self.char2)
        self._armor(self.char2, slot="worn_shield", reduction=0, defense=8)
        self.assertTrue(self._rider("Sundered", both=True))
        self.assertTrue(martial.is_sundered(self.char2, "worn_armor"))
        self.assertTrue(martial.is_sundered(self.char2, "worn_shield"))

    def test_an_ordinary_sunder_after_another_still_ends_with_both_broken(self):
        self._armor(self.char2)
        self._armor(self.char2, slot="worn_shield", reduction=0, defense=8)
        self._rider("Sundered")
        self._rider("Sundered")
        self.assertTrue(martial.is_sundered(self.char2, "worn_armor"))
        self.assertTrue(martial.is_sundered(self.char2, "worn_shield"))
        self.assertFalse(self._rider("Sundered"))  # nothing left to cleave

    def test_a_sundered_shield_no_longer_blocks_and_body_armor_stops_reducing(self):
        self._armor(self.char2)
        self.char2.db.combat_sundered = "both"
        with patch("world.combat.randint", return_value=50):
            reduced = COMBAT_RULES.get_damage(self.char1, self.char2)
        self.char2.db.combat_sundered = None
        with patch("world.combat.randint", return_value=50):
            full = COMBAT_RULES.get_damage(self.char1, self.char2)
        self.assertGreater(reduced, full)

    def test_feint_and_disarming_strike_are_weapon_strikes_with_martial_riders(self):
        for name, effect in (("feint", "Bleeding"), ("disarming strike", "Disarmed")):
            data = SKILLS[name]
            self.assertIs(data["skillfunc"].__func__, COMBAT_RULES.skill_attack.__func__, name)
            self.assertEqual(data["rider"]["effect"], effect, name)
            self.assertGreater(data["weapon_multiplier"], 1.0, name)

    def test_weapon_flourish_raises_crit_chance_instead_of_accuracy(self):
        self.assertEqual(SKILLS["weapon flourish"]["conditions"], [("Keen Edge", 3)])
        base, _ = martial.crit_profile(self.char1)
        self.char1.db.conditions = {"Keen Edge": [3, self.char1]}
        boosted, _ = martial.crit_profile(self.char1)
        self.assertEqual(boosted - base, martial.KEEN_EDGE_CRIT_BONUS)

    def test_no_gladiator_skill_is_a_caster_buff_or_debuff_twin(self):
        casters = {"Accuracy Down", "Accuracy Up", "Damage Down"}
        for name, data in SKILLS.items():
            if data.get("classes") != ["gladiator"]:
                continue
            for cond, _ in data.get("conditions", []):
                self.assertNotIn(cond, casters - {"Damage Up"}, name)

    def test_war_cry_goads_up_to_three_enemies(self):
        data = SKILLS["war cry"]
        self.assertEqual(data["conditions"], [("Goaded", 2)])
        self.assertEqual(data["max_targets"], 3)

    def test_crowds_surge_grants_one_extra_action_in_a_fight(self):
        handler = self._fight()
        self.char1.db.combat_actionsleft = 1
        sp = self.char1.db.sp
        self.assertIsNot(
            SKILLS["crowd's surge"]["skillfunc"](self.char1, "crowd's surge", [self.char1], 10),
            False,
        )
        self.assertEqual(self.char1.db.combat_actionsleft, 2)
        self.assertEqual(self.char1.db.sp, sp - 10)
        handler.stop()

    def test_crowds_surge_is_refused_outside_a_fight(self):
        sp = self.char1.db.sp
        self.assertIs(
            SKILLS["crowd's surge"]["skillfunc"](self.char1, "crowd's surge", [self.char1], 10),
            False,
        )
        self.assertEqual(self.char1.db.sp, sp)

    def test_damage_up_and_down_scale_with_the_blow(self):
        self.char1.db.wielded_weapon = _weapon(self.char1, 200, 200)
        with patch("world.combat.randint", return_value=50):
            plain = COMBAT_RULES.get_damage(self.char1, self.char2)
            self.char1.db.conditions = {"Damage Up": [3, self.char1]}
            up = COMBAT_RULES.get_damage(self.char1, self.char2)
            self.char1.db.conditions = {"Damage Down": [3, self.char2]}
            down = COMBAT_RULES.get_damage(self.char1, self.char2)
        self.assertGreater(up - plain, 5)
        self.assertLess(down - plain, -5)
        self.assertAlmostEqual(up - plain, plain * 0.15, delta=plain * 0.03)


class TestAgilitasAndPhysicalContests(MartialBase):
    """A physical skill's effect is the USER's fighting stat against the target's resist stat."""

    def setUp(self):
        super().setUp()
        self.char1.db.level = self.char2.db.level = 10
        self.char1.db.ingenium = 10

    def test_a_grab_uses_the_users_agilitas_not_ingenium(self):
        self.char1.db.agilitas = 20
        self.char2.db.agilitas = 10
        with patch("world.combat.randint", return_value=8):
            self.assertTrue(COMBAT_RULES.resists_condition(self.char1, self.char2, condition="Grappled"))
            self.assertFalse(
                COMBAT_RULES.resists_condition(
                    self.char1, self.char2, condition="Grappled", attacker_stat="agilitas"
                )
            )

    def test_a_nimble_target_escapes_more_often(self):
        self.char2.db.agilitas = 20
        with patch("world.combat.randint", return_value=30):
            self.assertTrue(
                COMBAT_RULES.resists_condition(
                    self.char1, self.char2, condition="Blinded", attacker_stat="agilitas"
                )
            )
            self.char2.db.agilitas = 10
            self.assertFalse(
                COMBAT_RULES.resists_condition(
                    self.char1, self.char2, condition="Blinded", attacker_stat="agilitas"
                )
            )

    def test_mind_effects_ignore_the_physical_stat(self):
        self.char1.db.virtus = 20
        self.char2.db.ingenium = 10
        with patch("world.combat.randint", return_value=8):
            self.assertTrue(
                COMBAT_RULES.resists_condition(
                    self.char1, self.char2, condition="Goaded", attacker_stat="virtus"
                )
            )

    def test_monsters_keep_their_old_odds(self):
        from world.combat import HostileNPC

        npc = create.create_object(HostileNPC, key="a brute", location=self.room1)
        npc.db.level = 10
        npc.db.agilitas = 20
        npc.db.ingenium = 10
        self.char2.db.agilitas = 10
        with patch("world.combat.randint", return_value=8):
            self.assertTrue(
                COMBAT_RULES.resists_condition(
                    npc, self.char2, condition="Grappled", attacker_stat="agilitas"
                )
            )

    def test_snare_is_sprung_free_of_with_agilitas(self):
        self.char1.db.location = self.room1
        self.char2.db.pacifist = False
        self.char2.db.agilitas = 20
        self.char2.db.vigor = 10
        with patch("world.combat.randint", return_value=25):  # would resist an Agilitas contest
            self.assertTrue(
                COMBAT_RULES.resists_condition(
                    self.char1, self.char2, condition="Snared", attacker_stat="agilitas"
                )
            )

    def test_use_skill_passes_each_classs_contest_stat(self):
        from world.combat import CLASS_CONTEST_STAT, CmdUseSkill

        self.assertEqual(CLASS_CONTEST_STAT["legionary"], "virtus")
        self.assertEqual(CLASS_CONTEST_STAT["venator"], "agilitas")
        self.char1.db.skills_known = ["entangle"]
        handler = self._fight()
        handler.db.turn = handler.db.fighters.index(self.char1)
        self.char1.db.combat_actionsleft = 1
        seen = {}

        def spy(user, name, targets, cost, **kwargs):
            seen.update(kwargs)

        with patch.dict(SKILLS["entangle"], {"skillfunc": spy}):
            self.call(CmdUseSkill(), "entangle = Char2", caller=self.char1)
        self.assertEqual(seen.get("contest_stat"), "agilitas")

    def test_piercing_shot_can_now_miss_a_nimble_target(self):
        data = SKILLS["piercing shot"]
        before = self.char2.db.hp
        with patch.object(COMBAT_RULES, "get_defense", return_value=999):
            data["skillfunc"](self.char1, "piercing shot", [self.char2], data["cost"],
                              **{k: v for k, v in data.items()
                                 if k not in ("skillfunc", "target", "cost", "classes", "desc", "level_required")})
        self.assertEqual(self.char2.db.hp, before)

    def test_reckless_abandon_still_exposes_the_user_when_it_misses(self):
        data = SKILLS["reckless abandon"]
        before = self.char2.db.hp
        with patch.object(COMBAT_RULES, "get_defense", return_value=999):
            data["skillfunc"](self.char1, "reckless abandon", [self.char2], data["cost"],
                              **{k: v for k, v in data.items()
                                 if k not in ("skillfunc", "target", "cost", "classes", "desc", "level_required")})
        self.assertEqual(self.char2.db.hp, before)
        self.assertIn("Defense Down", self.char1.db.conditions)

    def test_thundering_maul_can_miss(self):
        maul = _weapon(self.char1, 100, 100, "heavy_weapon")
        maul.db.two_handed = True
        self.char1.db.wielded_weapon = maul
        data = SKILLS["thundering maul"]
        before = self.char2.db.hp
        with patch.object(COMBAT_RULES, "get_defense", return_value=999):
            data["skillfunc"](self.char1, "thundering maul", [self.char2], data["cost"],
                              **{k: v for k, v in data.items()
                                 if k not in ("skillfunc", "target", "cost", "classes", "desc", "level_required")})
        self.assertEqual(self.char2.db.hp, before)


class TestRowProtectionOnDebuffSkills(MartialBase):
    """
    Sep 27, owner verification request: physical debuff skills (skill_
    add_condition, otherchar target) split the same way spell_attack and
    skill_attack already do - a shouted/willed effect (Goad, War Cry,
    Intimidating Roar) reaches a protected back row like a spell does; one
    that represents actually touching the target (Dirt Kick, Poisoned
    Blade, Entangle - "requires_contact") is blocked by it, same
    reach-aware check skill_attack uses (a bow or spear still gets through).
    """

    def _protect(self, target):
        self._fight()
        target.db.combat_row = "back"
        guard = create.create_object(
            "typeclasses.characters.Character", key="Guard", location=self.room1
        )
        guard.db.hp = guard.db.max_hp = 100
        guard.db.conditions = {}
        guard.db.combat_side = target.db.combat_side
        guard.db.combat_row = "front"
        target.db.combat_turnhandler.db.fighters.append(guard)

    def test_a_shout_reaches_a_protected_back_row(self):
        self._protect(self.char2)
        data = SKILLS["goad"]
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            data["skillfunc"](self.char1, "goad", [self.char2], data["cost"], **{
                k: v for k, v in data.items() if k not in ("skillfunc", "target", "cost", "classes", "desc", "level_required")
            })
        self.assertIn("Goaded", self.char2.db.conditions)

    def test_dirt_kick_cannot_reach_a_protected_back_row(self):
        self._protect(self.char2)
        data = SKILLS["dirt kick"]
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            data["skillfunc"](self.char1, "dirt kick", [self.char2], data["cost"], **{
                k: v for k, v in data.items() if k not in ("skillfunc", "target", "cost", "classes", "desc", "level_required")
            })
        self.assertNotIn("Blinded", self.char2.db.conditions)

    def test_a_ranged_weapon_still_lets_entangle_through(self):
        self._protect(self.char2)
        self.char1.db.wielded_weapon = _weapon(self.char1, 20, 20, "ranged")
        data = SKILLS["entangle"]
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            data["skillfunc"](self.char1, "entangle", [self.char2], data["cost"], **{
                k: v for k, v in data.items() if k not in ("skillfunc", "target", "cost", "classes", "desc", "level_required")
            })
        self.assertIn("Grappled", self.char2.db.conditions)


class TestBackstabFlankRule(MartialBase):
    """
    Backstab's targeting is the literal inverse of is_row_protected (Sep 27,
    owner request): a rear approach reaches a back-row target directly, but
    a front-row target with a living ally covering their back is safe from
    it - the mirror image of the normal "someone standing in front of you"
    rule. A target with no ally at all (an ordinary solo fight) is NOT
    protected either.
    """

    def _ally_of(self, target, row):
        ally = create.create_object(
            "typeclasses.characters.Character", key="Ally", location=self.room1
        )
        ally.db.hp = ally.db.max_hp = 100
        ally.db.conditions = {}
        ally.db.combat_side = target.db.combat_side
        ally.db.combat_row = row
        target.db.combat_turnhandler.db.fighters.append(ally)
        return ally

    def test_a_solo_target_is_not_protected(self):
        self._fight()
        self.assertFalse(COMBAT_RULES.is_backstab_protected(self.char2))

    def test_a_back_row_target_is_never_protected(self):
        self._fight()
        self.char2.db.combat_row = "back"
        self._ally_of(self.char2, "front")
        self.assertFalse(COMBAT_RULES.is_backstab_protected(self.char2))

    def test_a_front_row_target_with_someone_behind_is_protected(self):
        self._fight()
        self.char2.db.combat_row = "front"
        self._ally_of(self.char2, "back")
        self.assertTrue(COMBAT_RULES.is_backstab_protected(self.char2))

    def test_a_front_row_target_with_no_one_behind_is_not_protected(self):
        self._fight()
        self.char2.db.combat_row = "front"
        self._ally_of(self.char2, "front")
        self.assertFalse(COMBAT_RULES.is_backstab_protected(self.char2))

    def test_backstab_itself_is_refused_against_a_covered_target(self):
        self._fight()
        self.char2.db.combat_row = "front"
        self._ally_of(self.char2, "back")
        self.char2.db.combat_lastaction = "null"
        before = self.char2.db.hp
        data = SKILLS["backstab"]
        result = data["skillfunc"](self.char1, "backstab", [self.char2], data["cost"], **{
            k: v for k, v in data.items()
            if k not in ("skillfunc", "target", "cost", "classes", "desc", "level_required")
        })
        self.assertIs(result, False)
        self.assertEqual(self.char2.db.hp, before)


class TestSneakVanishStealth(MartialBase):
    """
    Sep 27, owner request: Sneak's evasion window extended (90s -> 15 real
    minutes) and, along with Vanish, it now also grants a genuine but
    narrower movement-stealth window (world.concentration.is_stealthed) -
    room arrivals/departures/speech go unnamed and wilderness ambushes skip
    it, but (deliberately, unlike real Invisibility) it does NOT hide the
    holder from someone already looking at the room.
    """

    def test_sneak_grants_a_15_minute_stealth_window(self):
        from world import concentration as conc

        data = SKILLS["sneak"]
        self.assertEqual(data["stealth_seconds"], 900)
        self.assertFalse(conc.is_stealthed(self.char1))
        data["skillfunc"](self.char1, "sneak", [self.char1], data["cost"],
                          conditions=data["conditions"], stealth_seconds=data["stealth_seconds"])
        self.assertTrue(conc.is_stealthed(self.char1))
        self.assertGreater(self.char1.db.stealth_until - time.time(), 890)

    def test_stealthed_does_not_hide_from_a_direct_look(self):
        from world import concentration as conc

        self.char1.db.stealth_until = time.time() + 100
        self.assertTrue(conc.is_stealthed(self.char1))
        self.assertFalse(conc.invisible_hides_from(self.char1, self.char2))
        self.assertTrue(self.char1.access(self.char2, "view"))

    def test_stealthed_hides_the_name_in_room_broadcasts(self):
        from world import concentration as conc

        self.char1.db.stealth_until = time.time() + 100
        self.assertTrue(conc.stealth_hides_from(self.char1, self.char2))
        self.assertFalse(conc.stealth_hides_from(self.char1, self.char1))

    def test_a_god_and_sees_invisible_see_through_stealth_too(self):
        from world import concentration as conc

        self.char1.db.stealth_until = time.time() + 100
        god = create.create_object("typeclasses.characters.Character", key="Jupiter", location=self.room1)
        god.db.level = 106
        self.assertFalse(conc.stealth_hides_from(self.char1, god))
        self.char2.db.conditions = {"Sees Invisible": [3, self.char2]}
        self.assertFalse(conc.stealth_hides_from(self.char1, self.char2))

    def test_wilderness_ambush_skips_a_stealthed_mover(self):
        from world.wilderness_rome import _is_unseen

        self.assertFalse(_is_unseen(self.char1))
        self.char1.db.stealth_until = time.time() + 100
        self.assertTrue(_is_unseen(self.char1))

    def test_attacking_breaks_stealth_immediately(self):
        from world.concentration import reveal_on_offense, is_stealthed

        self.char1.db.stealth_until = time.time() + 100
        self.assertTrue(is_stealthed(self.char1))
        reveal_on_offense(self.char1)
        self.assertFalse(is_stealthed(self.char1))

    def test_vanish_also_grants_a_short_stealth_window(self):
        self._fight()
        data = SKILLS["vanish"]
        self.assertEqual(data["stealth_seconds"], 120)
        data["skillfunc"](self.char1, "vanish", [self.char1], data["cost"],
                          conditions=data["conditions"], stealth_seconds=data["stealth_seconds"])
        self.assertGreater(self.char1.db.stealth_until - time.time(), 110)
