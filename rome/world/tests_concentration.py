"""
Tests for concentration spells and the states built on them
(world/concentration.py, world/wards.py, world/visibility.py): flight,
invisibility, sleep, confusion, the Flame of Vesta, temporary HP, the
release/effects commands, and the migration of the spells this rework removed.

The engine limits these were written against, all from direct owner
requirements: several concentrations at once; combat never breaks one; logout
does; invisibility breaks the instant its holder attacks (and ends the fight
if cast mid-fight); only gods and See Invisibility see through it; damage
wakes a sleeper; a confused creature wanders; a pacifist can't be touched.
"""

import time
from unittest import mock
from unittest.mock import patch

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from world import concentration as conc
from world import wards
from world.combat import (
    COMBAT_RULES,
    SPELLS,
    CmdCast,
    CmdRest,
    CombatTurnHandler,
    HostileNPC,
)
from world.visibility import anonymize


class ConcTestBase(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.permissions.remove("Developer")
            char.db.level = 30
            char.db.max_hp = char.db.hp = 100
            char.db.max_mp = char.db.mp = 100
            char.db.max_sp = char.db.sp = 30
            char.db.is_dead = False
            char.db.conditions = {}
            char.db.combat_turnhandler = None
            char.db.pacifist = False
            char.db.race = "human"

    def _fight(self):
        self.room1.ndb.pending_fighters = [self.char1, self.char2]
        return self.room1.scripts.add(CombatTurnHandler)

    def _tick(self, caster):
        script = caster.scripts.get("concentration")[0]
        with patch("evennia.objects.objects.ObjectSessionHandler.count", return_value=1):
            script.at_repeat()

    def _sleep(self, caster=None, target=None):
        caster = caster or self.char1
        target = target or self.char2
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            return conc.spell_sleep(caster, "sleep", [target], 5, drain_percent=0.02)


class TestConcentrationCore(ConcTestBase):
    def test_drain_is_a_share_of_max_mp_with_a_floor_of_one(self):
        self.assertEqual(conc.drain_for(self.char1, 0.02), 2)
        self.char1.db.max_mp = 10
        self.assertEqual(conc.drain_for(self.char1, 0.01), 1)
        self.assertEqual(conc.drain_for(self.char1, 0), 0)

    def test_several_can_be_held_at_once(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        conc.begin_concentration(self.char1, "invisibility", "invisibility", 0.02)
        self.assertTrue(conc.is_flying(self.char1))
        self.assertTrue(conc.is_invisible(self.char1))
        self.assertEqual(conc.total_drain(self.char1), 3)

    def test_ending_the_last_one_removes_the_script(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        self.assertTrue(self.char1.scripts.has("concentration"))
        conc.end_concentration(self.char1, "fly")
        self.assertFalse(self.char1.scripts.has("concentration"))

    def test_a_tick_drains_mp_for_everything_held(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        conc.begin_concentration(self.char1, "invisibility", "invisibility", 0.02)
        self._tick(self.char1)
        self.assertEqual(self.char1.db.mp, 97)

    def test_running_out_of_mp_drops_everything(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        conc.begin_concentration(self.char1, "invisibility", "invisibility", 0.02)
        self.char1.db.mp = 1
        self._tick(self.char1)
        self.assertFalse(self.char1.db.concentrations)

    def test_combat_does_not_end_a_concentration(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        self._fight()
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))
        self._tick(self.char1)
        self.assertTrue(conc.is_flying(self.char1))
        self.assertEqual(self.char1.db.mp, 99)

    def test_logout_ends_every_concentration(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        conc.begin_concentration(self.char1, "invisibility", "invisibility", 0.02)
        with patch("world.analytics.end_session"):
            self.char1.at_post_unpuppet(account=self.account)
        self.assertFalse(self.char1.db.concentrations)

    def test_death_ends_every_concentration(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        self.char1.db.hp = 0
        COMBAT_RULES.at_defeat(self.char1)
        self.assertFalse(self.char1.db.concentrations)

    def test_rest_is_refused_while_holding_a_spell(self):
        self.char1.db.hp = 50
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        result = self.call(CmdRest(), "", caller=self.char1)
        self.assertIn("holding a spell", result)
        self.assertFalse(self.char1.db.resting)


class TestFlight(ConcTestBase):
    def test_flying_pays_stamina_only_on_every_fourth_step(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        for _ in range(8):
            self.assertTrue(self.char1._check_and_pay_movement_sp("move"))
        self.assertEqual(self.char1.db.sp, 28)

    def test_walking_pays_every_step(self):
        for _ in range(8):
            self.char1._check_and_pay_movement_sp("move")
        self.assertEqual(self.char1.db.sp, 22)

    def test_the_spell_costs_mp_and_holds_the_flight(self):
        conc.spell_fly(self.char1, "fly", [], 8, drain_percent=0.01)
        self.assertEqual(self.char1.db.mp, 92)
        self.assertTrue(conc.is_flying(self.char1))

    def test_casting_it_twice_is_refused_without_a_second_charge(self):
        conc.spell_fly(self.char1, "fly", [], 8, drain_percent=0.01)
        self.assertIs(conc.spell_fly(self.char1, "fly", [], 8, drain_percent=0.01), False)
        self.assertEqual(self.char1.db.mp, 92)

    def test_a_harpy_flies_free_with_the_command(self):
        self.char1.db.race = "harpy"
        self.call(conc.CmdFly(), "", caller=self.char1)
        self.assertTrue(conc.is_flying(self.char1))
        self.assertEqual(self.char1.db.mp, 100)
        self.assertEqual(conc.total_drain(self.char1), 0)

    def test_a_harpy_needs_no_spell(self):
        self.char1.db.race = "harpy"
        self.assertIs(conc.spell_fly(self.char1, "fly", [], 8, drain_percent=0.01), False)
        self.assertEqual(self.char1.db.mp, 100)

    def test_anyone_else_cannot_fly_by_command(self):
        result = self.call(conc.CmdFly(), "", caller=self.char1)
        self.assertIn("no wings", result)
        self.assertFalse(conc.is_flying(self.char1))

    def test_land_puts_you_down(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        self.call(conc.CmdLand(), "", caller=self.char1)
        self.assertFalse(conc.is_flying(self.char1))


class TestInvisibility(ConcTestBase):
    def _vanish(self, who=None):
        conc.begin_concentration(who or self.char1, "invisibility", "invisibility", 0.02)

    def test_hidden_from_an_ordinary_looker_but_not_from_themself(self):
        self._vanish()
        self.assertFalse(self.char1.access(self.char2, "view"))
        self.assertTrue(self.char1.access(self.char1, "view"))

    def test_gods_always_see_through_it(self):
        self._vanish()
        self.char2.db.level = 106
        self.assertTrue(self.char1.access(self.char2, "view"))

    def test_only_see_invisibility_lets_a_player_see_them(self):
        self._vanish()
        self.assertFalse(self.char1.access(self.char2, "view"))
        self.char2.db.conditions = {"Sees Invisible": [5, self.char2]}
        self.assertTrue(self.char1.access(self.char2, "view"))

    def test_not_even_a_party_member_sees_them_without_the_spell(self):
        self._vanish()
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2]
        self.char2.db.party_leader = self.char1
        self.assertFalse(self.char1.access(self.char2, "view"))

    def test_their_name_becomes_someone(self):
        self._vanish()
        self.assertEqual(self.char1.get_display_name(self.char2), "Someone")

    def test_room_announcements_say_someone_to_those_who_cannot_see(self):
        self._vanish()
        with patch.object(self.char2, "msg") as seen_by_2:
            self.room1.msg_contents("Char casts a spell.", exclude=[self.char1])
        text = seen_by_2.call_args[0][0] if seen_by_2.call_args[0] else seen_by_2.call_args[1]["text"]
        text = text[0] if isinstance(text, tuple) else text
        self.assertIn("Someone casts a spell.", text)

    def test_room_announcements_keep_the_name_for_those_who_see_through(self):
        self._vanish()
        self.char2.db.level = 106
        with patch.object(self.char2, "msg") as seen_by_2:
            self.room1.msg_contents("Char casts a spell.", exclude=[self.char1])
        text = seen_by_2.call_args[0][0] if seen_by_2.call_args[0] else seen_by_2.call_args[1]["text"]
        text = text[0] if isinstance(text, tuple) else text
        self.assertIn("Char casts a spell.", text)

    def test_anonymize_handles_case_and_lookalike_names(self):
        self.assertEqual(anonymize("Char waves at Char2.", ["Char"]), "Someone waves at Char2.")
        self.assertEqual(anonymize("You see Char.", ["Char"]), "You see someone.")
        self.assertEqual(anonymize("|YChar jolts awake!|n", ["Char"]), "|YSomeone jolts awake!|n")

    def test_the_room_list_omits_them_for_ordinary_lookers(self):
        self._vanish()
        listing = self.room1.get_display_characters(self.char2)
        self.assertNotIn("Char,", listing + ",")
        self.assertNotIn("(invis)", listing)

    def test_the_room_list_tags_them_invis_for_those_who_see_through(self):
        self._vanish()
        self.char2.db.level = 106
        listing = self.room1.get_display_characters(self.char2)
        self.assertIn("(invis)", listing)

    def test_they_cannot_be_targeted_by_name(self):
        from world.combat import find_combat_target

        self._vanish()
        # (char2 is "Char2" - a prefix match on "Char" finds them, never the hidden char1.)
        self.assertIsNot(find_combat_target(self.char2, "Char"), self.char1)

    def test_striking_ends_it_at_once(self):
        self._vanish()
        COMBAT_RULES.resolve_attack(self.char1, self.char2, attack_value=999, damage_value=1)
        self.assertFalse(conc.is_invisible(self.char1))

    def test_casting_something_hostile_ends_it(self):
        self._vanish()
        conc.reveal_on_offense(self.char1)
        self.assertFalse(conc.is_invisible(self.char1))

    def test_casting_it_in_a_fight_ends_the_fight_for_the_caster(self):
        self._fight()
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))
        conc.spell_invisibility(self.char1, "invisibility", [], 10, drain_percent=0.02)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))
        self.assertTrue(conc.is_invisible(self.char1))

    def test_it_skips_the_wildernesss_ambush(self):
        from world.wilderness_rome import _aggro_on_sight

        self._vanish()
        npc = create.create_object(HostileNPC, key="a bandit", location=self.room1)
        with patch("evennia.objects.objects.DefaultObject.has_account", new=True):
            _aggro_on_sight(npc, self.char1, self.room1)
        self.assertFalse(self.room1.ndb.pending_fighters)

    def test_see_invisibility_is_a_real_condition_spell(self):
        data = SPELLS["see invisibility"]
        self.assertEqual(data["conditions"][0][0], "Sees Invisible")
        self.assertNotIn("drain_percent", data)


class TestRoomListingTags(ConcTestBase):
    def test_a_sleeper_is_tagged_asleep(self):
        self.char2.db.conditions = {"Asleep": [True, self.char1]}
        self.assertIn("(asleep)", self.room1.get_display_characters(self.char1))

    def test_a_flier_is_tagged_flying(self):
        conc.begin_concentration(self.char2, "fly", "fly", 0.01)
        self.assertIn("(flying)", self.room1.get_display_characters(self.char1))

    def test_an_ordinary_character_has_no_tag(self):
        listing = self.room1.get_display_characters(self.char1)
        for tag in ("(asleep)", "(flying)", "(invis)"):
            self.assertNotIn(tag, listing)


class TestSleep(ConcTestBase):
    def test_sleep_puts_the_target_under_and_costs_mp(self):
        self._sleep()
        self.assertIn("Asleep", self.char2.db.conditions)
        self.assertEqual(self.char1.db.mp, 95)
        self.assertTrue(conc.is_concentrating(self.char1, conc.sleep_key(self.char2)))

    def test_a_resisted_sleep_still_costs_mp_but_holds_nothing(self):
        with patch.object(COMBAT_RULES, "resists_condition", return_value=True):
            conc.spell_sleep(self.char1, "sleep", [self.char2], 5, drain_percent=0.02)
        self.assertNotIn("Asleep", self.char2.db.conditions)
        self.assertEqual(self.char1.db.mp, 95)
        self.assertFalse(self.char1.db.concentrations)

    def test_any_damage_wakes_the_sleeper_and_frees_the_caster(self):
        self._sleep()
        COMBAT_RULES.apply_damage(self.char2, 3, attacker=self.char1)
        self.assertNotIn("Asleep", self.char2.db.conditions)
        self.assertFalse(self.char1.db.concentrations)

    def test_it_ends_the_targets_fight(self):
        self._fight()
        self._sleep()
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char2))

    def test_a_sleeper_cannot_cast_speak_or_move(self):
        self._sleep()
        cast = self.call(CmdCast(), "magic arrow = Char", caller=self.char2)
        self.assertIn("fast asleep", cast)
        self.assertFalse(self.char2.move_to(self.room2, move_type="move"))

    def test_a_sleeper_can_still_look(self):
        from world.combat import CmdLook

        self._sleep()
        result = self.call(CmdLook(), "", caller=self.char2)
        self.assertNotIn("fast asleep", result)

    def test_releasing_wakes_them(self):
        self._sleep()
        self.call(conc.CmdRelease(), "sleep", caller=self.char1)
        self.assertNotIn("Asleep", self.char2.db.conditions)
        self.assertFalse(self.char1.db.concentrations)

    def test_the_caster_running_dry_wakes_them(self):
        self._sleep()
        self.char1.db.mp = 0
        self._tick(self.char1)
        self.assertNotIn("Asleep", self.char2.db.conditions)

    def test_a_held_sleep_has_a_hard_time_limit(self):
        self._sleep()
        token = self.char2.db.sleep_token
        conc._expire_sleep(self.char2, token + 1)  # a stale timer does nothing
        self.assertIn("Asleep", self.char2.db.conditions)
        conc._expire_sleep(self.char2, token)
        self.assertNotIn("Asleep", self.char2.db.conditions)

    def test_a_pacifist_cannot_be_put_to_sleep(self):
        self.char2.db.pacifist = True
        self.assertIs(conc.spell_sleep(self.char1, "sleep", [self.char2], 5), False)
        self.assertNotIn("Asleep", self.char2.db.conditions)
        self.assertEqual(self.char1.db.mp, 100)

    def test_an_ally_cannot_be_put_to_sleep(self):
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2]
        self.char2.db.party_leader = self.char1
        self.assertIs(conc.spell_sleep(self.char1, "sleep", [self.char2], 5), False)

    def test_a_sleeper_cannot_send_on_a_channel(self):
        from types import SimpleNamespace

        channel = create.create_channel("Sleepy", typeclass="typeclasses.channels.Channel")
        self._sleep()
        speaker = SimpleNamespace(sessions=SimpleNamespace(all=lambda: [SimpleNamespace(puppet=self.char2)]))
        self.assertFalse(channel.access(speaker, "send"))

    def test_a_sleeping_npc_does_not_chatter(self):
        from world.colosseum import NPCChatter

        npc = create.create_object("typeclasses.characters.Character", key="a guard", location=self.room1)
        npc.db.chatter_lines = ["Move along."]
        npc.db.conditions = {"Asleep": [True, self.char1]}
        script = create.create_script(NPCChatter, obj=npc)
        with patch.object(self.char1, "msg") as heard:
            script.at_repeat()
        heard.assert_not_called()


class TestConfusion(ConcTestBase):
    def _confuse(self):
        with patch.object(COMBAT_RULES, "resists_condition", return_value=False):
            return conc.spell_confusion(self.char1, "confusion", [self.char2], 14)

    def test_it_lasts_three_to_five_real_minutes(self):
        before = time.time()
        self._confuse()
        left = self.char2.db.confused_until - before
        self.assertGreaterEqual(left, conc.CONFUSION_MIN_SECONDS - 1)
        self.assertLessEqual(left, conc.CONFUSION_MAX_SECONDS + 1)
        self.assertTrue(conc.is_confused(self.char2))
        self.assertTrue(self.char2.scripts.has("confusion"))

    def test_it_is_not_a_concentration(self):
        self._confuse()
        self.assertFalse(self.char1.db.concentrations)

    def test_it_ends_the_targets_fight(self):
        self._fight()
        self._confuse()
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char2))

    def test_a_confused_creature_wanders_into_another_room(self):
        self._confuse()
        script = self.char2.scripts.get("confusion")[0]
        with patch("world.concentration.randint", return_value=1):
            script.at_repeat()
        self.assertEqual(self.char2.location, self.room2)

    def test_a_confused_creature_may_lash_out_at_someone_nearby(self):
        self._confuse()
        script = self.char2.scripts.get("confusion")[0]
        with patch("world.concentration.randint", return_value=70):
            script.at_repeat()
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char2))

    def test_it_fades_on_its_own(self):
        self._confuse()
        self.char2.db.confused_until = time.time() - 1
        script = self.char2.scripts.get("confusion")[0]
        script.at_repeat()
        self.assertFalse(conc.is_confused(self.char2))
        self.assertFalse(self.char2.scripts.has("confusion"))

    def test_a_pacifist_cannot_be_confused(self):
        self.char2.db.pacifist = True
        self.assertIs(conc.spell_confusion(self.char1, "confusion", [self.char2], 14), False)

    def test_a_confused_players_kill_never_counts_against_pacifism(self):
        self.char1.db.conditions = {"Confused": [True, self.char2]}
        self.char2.db.hp = 0
        self.char2.db.damage_log = {self.char1: 10}
        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)
        self.assertFalse(self.char1.db.has_ever_killed_player)

    def test_an_ordinary_players_kill_still_does(self):
        self.char2.db.hp = 0
        self.char2.db.damage_log = {self.char1: 10}
        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)
        self.assertTrue(self.char1.db.has_ever_killed_player)


class TestSlow(ConcTestBase):
    def test_slow_costs_a_turn_every_other_turn(self):
        handler = self._fight()
        self.char2.db.conditions = {"Slowed": [4, self.char1]}
        lost = []
        for _ in range(4):
            self.char2.db.combat_actionsleft = 1
            COMBAT_RULES.apply_turn_conditions(self.char2)
            lost.append(self.char2.db.combat_actionsleft == 0)
            if handler.pk is None or not self.char2.db.combat_turnhandler:
                break
        self.assertIn(True, lost)
        self.assertIn(False, lost)


class TestTemporaryHP(ConcTestBase):
    def _false_life(self, target=None):
        target = target or self.char1
        return wards.spell_temp_hp(self.char1, "false life", [target], 5, hp_percent=0.20)

    def test_it_is_a_share_of_the_targets_own_max_hp(self):
        self.char1.db.max_hp = 200
        self._false_life()
        self.assertEqual(wards.get_temp_hp(self.char1), 40)
        self.assertEqual(self.char1.db.mp, 95)

    def test_it_soaks_damage_before_real_hp(self):
        self._false_life()
        COMBAT_RULES.apply_damage(self.char1, 30, attacker=self.char2)
        self.assertEqual(self.char1.db.hp, 90)
        self.assertEqual(wards.get_temp_hp(self.char1), 0)

    def test_a_hit_smaller_than_the_ward_costs_no_real_hp(self):
        self._false_life()
        COMBAT_RULES.apply_damage(self.char1, 8, attacker=self.char2)
        self.assertEqual(self.char1.db.hp, 100)
        self.assertEqual(wards.get_temp_hp(self.char1), 12)

    def test_a_weaker_ward_never_replaces_a_stronger_one(self):
        wards.grant_temp_hp(self.char1, 50)
        self.assertIs(self._false_life(), False)
        self.assertEqual(wards.get_temp_hp(self.char1), 50)
        self.assertEqual(self.char1.db.mp, 100)

    def test_it_fades_after_ten_minutes(self):
        self._false_life()
        self.char1.db.temp_hp_until = time.time() - 1
        self.assertEqual(wards.get_temp_hp(self.char1), 0)

    def test_aid_reaches_up_to_three_allies_by_their_own_max_hp(self):
        self.char2.db.max_hp = 300
        wards.spell_temp_hp(self.char1, "aid", [self.char1, self.char2], 6, hp_percent=0.15)
        self.assertEqual(wards.get_temp_hp(self.char1), 15)
        self.assertEqual(wards.get_temp_hp(self.char2), 45)

    def test_armor_of_agathys_lashes_a_melee_attacker(self):
        wards.spell_temp_hp(
            self.char1, "armor of agathys", [self.char1], 8, hp_percent=0.25, thorns_range=(5, 9)
        )
        COMBAT_RULES.apply_damage(self.char1, 10, attacker=self.char2, melee=True)
        self.assertLess(self.char2.db.hp, 100)

    def test_armor_of_agathys_ignores_a_spell(self):
        wards.spell_temp_hp(
            self.char1, "armor of agathys", [self.char1], 8, hp_percent=0.25, thorns_range=(5, 9)
        )
        COMBAT_RULES.apply_damage(self.char1, 10, attacker=self.char2, melee=False)
        self.assertEqual(self.char2.db.hp, 100)

    def test_the_retaliation_scales_with_level(self):
        def thorns_at(level):
            self.char1.db.level = level
            self.char1.db.mp = 100
            wards.clear_temp_hp(self.char1)
            wards.spell_temp_hp(
                self.char1, "armor of agathys", [self.char1], 8,
                hp_percent=0.25, thorns_range=(5, 9),
            )
            return self.char1.db.thorns_range

        self.assertGreater(thorns_at(60)[1], thorns_at(28)[1])

    def test_the_temp_hp_share_grows_with_level_through_max_hp(self):
        self.char1.db.max_hp = 100
        self._false_life()
        low = wards.get_temp_hp(self.char1)
        wards.clear_temp_hp(self.char1)
        self.char1.db.max_hp = 600
        self._false_life()
        self.assertGreater(wards.get_temp_hp(self.char1), low)


class TestFlameOfVesta(ConcTestBase):
    def test_it_scorches_every_enemy_in_the_casters_fight_each_tick(self):
        conc.spell_flame_of_vesta(self.char1, "flame of vesta", [], 10, drain_percent=0.03)
        self._fight()
        self._tick(self.char1)
        self.assertLess(self.char2.db.hp, 100)

    def test_it_does_nothing_outside_a_fight(self):
        conc.spell_flame_of_vesta(self.char1, "flame of vesta", [], 10, drain_percent=0.03)
        self._tick(self.char1)
        self.assertEqual(self.char2.db.hp, 100)

    def test_it_is_a_heavy_drain(self):
        self.assertEqual(conc.drain_word(SPELLS["flame of vesta"]["drain_percent"]), "heavy")


class TestReleaseAndEffects(ConcTestBase):
    def test_release_with_one_held_lets_it_go(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        self.call(conc.CmdRelease(), "", caller=self.char1)
        self.assertFalse(self.char1.db.concentrations)

    def test_release_with_several_asks_which(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        conc.begin_concentration(self.char1, "invisibility", "invisibility", 0.02)
        result = self.call(conc.CmdRelease(), "", caller=self.char1)
        self.assertIn("release all", result)
        self.assertEqual(len(self.char1.db.concentrations), 2)

    def test_release_all_and_release_by_name(self):
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        conc.begin_concentration(self.char1, "invisibility", "invisibility", 0.02)
        self.call(conc.CmdRelease(), "fly", caller=self.char1)
        self.assertEqual(list(self.char1.db.concentrations), ["invisibility"])
        self.call(conc.CmdRelease(), "all", caller=self.char1)
        self.assertFalse(self.char1.db.concentrations)

    def test_visible_drops_invisibility(self):
        conc.begin_concentration(self.char1, "invisibility", "invisibility", 0.02)
        self.call(conc.CmdVisible(), "", caller=self.char1)
        self.assertFalse(conc.is_invisible(self.char1))

    def test_releasing_when_nothing_is_held(self):
        self.assertIn("aren't holding", self.call(conc.CmdRelease(), "", caller=self.char1))

    def test_effects_when_nothing_is_active(self):
        self.assertIn("Nothing is affecting you", self.call(conc.CmdEffects(), "", caller=self.char1))

    def test_effects_lists_conditions_concentrations_and_drain(self):
        self.char1.db.conditions = {"Haste": [3, self.char1]}
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        conc.begin_concentration(self.char1, "invisibility", "invisibility", 0.02)
        wards.grant_temp_hp(self.char1, 20)
        result = self.call(conc.CmdEffects(), "", caller=self.char1)
        for expected in ("Haste", "fly", "invisibility", "light drain", "moderate drain",
                         "land", "visible", "temporary hit points", "will last"):
            self.assertIn(expected, result)


class TestSpellTable(ConcTestBase):
    def test_the_lineup_changes(self):
        for gone in ("bane", "omen of weakness", "omen of doom", "bless", "divine favor"):
            self.assertNotIn(gone, SPELLS)
        for name in ("magic arrow", "sleep", "see invisibility", "fly", "invisibility", "slow",
                     "confusion", "veil of night", "inflict wounds", "false life",
                     "armor of agathys", "aid", "healing word", "flame of vesta"):
            self.assertIn(name, SPELLS)
        self.assertNotIn("longstrider", SPELLS)

    def test_new_spells_are_in_the_right_lanes(self):
        for name in ("magic arrow", "sleep", "see invisibility", "fly", "invisibility",
                     "slow", "confusion"):
            self.assertEqual(SPELLS[name]["classes"], ["augur"], name)
        for name in ("inflict wounds", "false life", "armor of agathys"):
            self.assertEqual(SPELLS[name]["classes"], ["haruspex"], name)
        for name in ("aid", "healing word", "flame of vesta"):
            self.assertEqual(SPELLS[name]["classes"], ["medicus"], name)

    def test_the_new_spell_names_do_not_collide_with_existing_ones(self):
        self.assertNotIn("spirit guardians", SPELLS)
        self.assertIn("guardian spirit", SPELLS)

    def test_npcs_never_cast_the_new_special_spells(self):
        for name in ("sleep", "fly", "invisibility", "confusion", "false life",
                     "armor of agathys", "aid", "healing word", "flame of vesta"):
            self.assertIs(SPELLS[name].get("npc_cast"), False, name)

    def test_concentration_spells_all_declare_a_drain(self):
        for name in ("sleep", "fly", "invisibility", "flame of vesta"):
            self.assertGreater(SPELLS[name]["drain_percent"], 0, name)
        self.assertNotIn("drain_percent", SPELLS["confusion"])

    def test_every_new_spell_can_be_learned_at_its_level(self):
        for name, level in (("magic arrow", 1), ("sleep", 10), ("see invisibility", 20),
                            ("fly", 30), ("invisibility", 42), ("slow", 45),
                            ("confusion", 65), ("inflict wounds", 10), ("false life", 12),
                            ("armor of agathys", 28), ("aid", 15), ("healing word", 12),
                            ("flame of vesta", 35)):
            self.assertEqual(SPELLS[name]["level_required"], level, name)

    def test_a_refused_cast_costs_nothing_and_grants_no_xp(self):
        self.char1.db.player_class = "augur"
        self.char1.db.spells_known = ["fly"]
        conc.begin_concentration(self.char1, "fly", "fly", 0.01)
        xp_before = self.char1.db.xp
        self.call(CmdCast(), "fly", caller=self.char1)
        self.assertEqual(self.char1.db.mp, 100)
        self.assertEqual(self.char1.db.xp, xp_before)


class TestRemovedSpellMigration(ConcTestBase):
    def test_bane_is_swapped_for_magic_missile_for_an_augur(self):
        self.char1.db.player_class = "augur"
        self.char1.db.spells_known = ["bane", "auspice"]
        self.char1.db.gold = 0
        conc.prune_removed_spells(self.char1)
        self.assertEqual(sorted(self.char1.db.spells_known), ["auspice", "magic arrow"])
        self.assertEqual(self.char1.db.gold, 0)

    def test_purchased_spells_are_refunded_at_their_cost(self):
        from world.combat import compute_learn_cost

        self.char1.db.player_class = "augur"
        self.char1.db.spells_known = ["omen of weakness", "omen of doom"]
        self.char1.db.gold = 10
        refund = conc.prune_removed_spells(self.char1)
        expected = compute_learn_cost(20) + compute_learn_cost(45)
        self.assertEqual(refund, expected)
        self.assertEqual(self.char1.db.gold, 10 + expected)
        self.assertEqual(self.char1.db.spells_known, [])

    def test_the_medicus_swaps_are_refunded(self):
        from world.combat import compute_learn_cost

        self.char1.db.player_class = "medicus"
        self.char1.db.spells_known = ["bless", "divine favor", "cure wounds"]
        self.char1.db.gold = 0
        conc.prune_removed_spells(self.char1)
        self.assertEqual(self.char1.db.spells_known, ["cure wounds"])
        self.assertEqual(self.char1.db.gold, compute_learn_cost(15) + compute_learn_cost(35))

    def test_it_is_idempotent(self):
        self.char1.db.player_class = "medicus"
        self.char1.db.spells_known = ["bless"]
        self.char1.db.gold = 0
        conc.prune_removed_spells(self.char1)
        gold = self.char1.db.gold
        self.assertEqual(conc.prune_removed_spells(self.char1), 0)
        self.assertEqual(self.char1.db.gold, gold)

    def test_casting_triggers_the_cleanup_for_an_online_player(self):
        self.char1.db.player_class = "medicus"
        self.char1.db.spells_known = ["bless"]
        self.char1.db.gold = 0
        self.call(CmdCast(), "cure wounds", caller=self.char1)
        self.assertNotIn("bless", self.char1.db.spells_known)
        self.assertGreater(self.char1.db.gold, 0)


class TestBlessingOfAsclepiusWaivesTheDeathXpPenalty(ConcTestBase):
    """
    Owner requirement: being brought back by Blessing of Asclepius bypasses
    the half-XP death penalty. Solving the riddle yourself does not.
    """

    def _die(self):
        self.char1.db.xp = 100
        COMBAT_RULES.handle_player_defeat(self.char1)
        # (no Underworld built in the test DB - the fail-safe branch revives
        # them at once, so put them back in the dead state a real death leaves.)
        self.char1.db.is_dead = True
        self.char1.db.charon_arrived = True

    def test_dying_records_what_it_took(self):
        self._die()
        self.assertEqual(self.char1.db.xp, 50)
        self.assertEqual(self.char1.db.death_xp_lost, 50)

    def test_the_blessing_gives_it_back(self):
        self._die()
        self.char2.db.mp = 100
        COMBAT_RULES.spell_resurrect(self.char2, "blessing of asclepius", [self.char1], 18)
        self.assertFalse(self.char1.db.is_dead)
        self.assertEqual(self.char1.db.xp, 100)
        self.assertIsNone(self.char1.db.death_xp_lost)

    def test_solving_the_riddle_keeps_the_penalty(self):
        self._die()
        COMBAT_RULES.resurrect(self.char1)
        self.assertEqual(self.char1.db.xp, 50)
        self.assertIsNone(self.char1.db.death_xp_lost)

    def test_it_only_refunds_once(self):
        self._die()
        self.char2.db.mp = 100
        COMBAT_RULES.spell_resurrect(self.char2, "blessing of asclepius", [self.char1], 18)
        COMBAT_RULES.resurrect(self.char1, restore_lost_xp=True)  # not dead: a no-op
        self.assertEqual(self.char1.db.xp, 100)

    def test_the_help_says_so(self):
        from evennia.help.models import HelpEntry
        from world.help_setup import create_all_help_entries

        create_all_help_entries()
        text = HelpEntry.objects.get(db_key="death").db_entrytext
        self.assertIn("waives", text)
        self.assertIn("waives", SPELLS["blessing of asclepius"]["desc"])


class TestResistingTheNewCrowdControl(ConcTestBase):
    """Slow, Sleep and Confusion are all resisted on Ingenium - never guaranteed."""

    def test_a_high_ingenium_target_shrugs_off_all_three(self):
        self.char1.db.ingenium = 10
        self.char2.db.ingenium = 40
        with patch("world.combat.randint", return_value=1):
            COMBAT_RULES.spell_add_condition(
                self.char1, "slow", [self.char2], 9, conditions=[("Slowed", 4)]
            )
            conc.spell_sleep(self.char1, "sleep", [self.char2], 5, drain_percent=0.02)
            conc.spell_confusion(self.char1, "confusion", [self.char2], 14)
        for name in ("Slowed", "Asleep", "Confused"):
            self.assertNotIn(name, self.char2.db.conditions)

    def test_a_much_stronger_caster_still_leaves_a_small_chance(self):
        from world.combat import CONDITION_RESIST_MIN

        self.char1.db.ingenium = 40
        self.char2.db.ingenium = 10
        with patch("world.combat.randint", return_value=CONDITION_RESIST_MIN):
            self.assertTrue(COMBAT_RULES.resists_condition(self.char1, self.char2))
        with patch("world.combat.randint", return_value=CONDITION_RESIST_MIN + 1):
            self.assertFalse(COMBAT_RULES.resists_condition(self.char1, self.char2))


class TestLookingAtACharacter(ConcTestBase):
    def test_a_sleeper_shows_asleep_when_looked_at(self):
        self.char2.db.conditions = {"Asleep": [True, self.char1]}
        self.assertIn("(asleep)", self.char2.return_appearance(self.char1))

    def test_a_flier_shows_flying_when_looked_at(self):
        conc.begin_concentration(self.char2, "fly", "fly", 0.01)
        self.assertIn("(flying)", self.char2.return_appearance(self.char1))

    def test_an_ordinary_character_has_no_tag(self):
        text = self.char2.return_appearance(self.char1)
        self.assertNotIn("(asleep)", text)
        self.assertNotIn("(flying)", text)


class TestHelpForTheNewMagic(ConcTestBase):
    def setUp(self):
        super().setUp()
        from world.help_setup import create_all_help_entries

        create_all_help_entries()

    def test_every_new_spell_has_a_help_topic_with_its_real_stats(self):
        from evennia.help.models import HelpEntry
        from world.help_setup import NEW_SPELL_HELP

        for name in NEW_SPELL_HELP:
            text = HelpEntry.objects.get(db_key=name).db_entrytext
            self.assertIn("level %d" % SPELLS[name]["level_required"], text, name)
            self.assertIn("Cost: %s MP" % SPELLS[name]["cost"], text, name)
            self.assertIn("cast", text, name)

    def test_the_new_spells_are_all_covered_by_a_topic_or_a_command(self):
        from world.help_setup import NEW_SPELL_HELP

        new_spells = {"magic arrow", "sleep", "see invisibility", "fly", "invisibility", "slow",
                      "confusion", "inflict wounds", "false life", "armor of agathys", "aid",
                      "healing word", "flame of vesta"}
        self.assertEqual(new_spells - set(NEW_SPELL_HELP), {"fly"})  # fly: the CmdFly help

    def test_concentration_spell_topics_show_their_drain(self):
        from evennia.help.models import HelpEntry

        for name in ("sleep", "invisibility", "flame of vesta"):
            self.assertIn("drain", HelpEntry.objects.get(db_key=name).db_entrytext, name)

    def test_release_land_visible_and_fly_each_have_their_own_help(self):
        docs = {
            "release": conc.CmdRelease.__doc__,
            "land": conc.CmdLand.__doc__,
            "visible": conc.CmdVisible.__doc__,
            "fly": conc.CmdFly.__doc__,
            "effects": conc.CmdEffects.__doc__,
        }
        for key, doc in docs.items():
            self.assertTrue(doc and key in doc.lower(), key)
        self.assertEqual(conc.CmdLand.key, "land")
        self.assertEqual(conc.CmdVisible.key, "visible")
        self.assertNotIn("land", conc.CmdRelease.aliases)

    def test_the_fly_help_covers_both_the_harpy_command_and_the_spell(self):
        self.assertIn("Harpies", conc.CmdFly.__doc__)
        self.assertIn("cast fly", conc.CmdFly.__doc__)

    def test_chargen_tells_a_harpy_it_can_fly(self):
        from world.chargen_menu import RACES

        text = " ".join(RACES["harpy"]["abilities"])
        self.assertIn("Innate Flight", text)
        self.assertIn("fly", text)
