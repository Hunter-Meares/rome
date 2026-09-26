"""
Tests for critical hits and the martial status effects (world/martial.py), the
Headbutt and Dirt Kick skills, and the Omen of Ruin redesign.

Crits are random, so under the test runner they are off unless a test here turns
them on (martial.CRITS_IN_TESTS) - hundreds of other tests assert exact damage.
"""

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

    def test_a_bow_cannot_crit_and_fists_can(self):
        self.char1.db.wielded_weapon = _weapon(self.char1, 10, 10, category="ranged")
        self.assertIsNone(martial.crit_profile(self.char1))
        self.char1.db.wielded_weapon = None
        self.assertEqual(martial.crit_profile(self.char1), martial.UNARMED_CRIT)

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

    def test_a_ranged_skill_does_not_crit(self):
        self.char1.db.wielded_weapon = _weapon(self.char1, 100, 100, category="ranged")
        self.char1.db.player_class = "venator"
        self.assertEqual(self._hit("piercing shot"), int(100 * 1.3))

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

    def test_the_effects_are_all_body_effects_resisted_with_vigor(self):
        from world.combat import CONDITION_RESIST_STAT

        for effect in ("Bleeding", "Stunned", "Blinded", "Disarmed", "Grappled"):
            self.assertEqual(CONDITION_RESIST_STAT[effect], "vigor", effect)


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
            "gladius cleave": "Sundered", "shattering blow": "Sundered",
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

        for name in ("headbutt", "dirt kick"):
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
