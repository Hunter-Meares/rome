"""
Tests for religion & piety (world/religion.py): tier math, the
Pontifex/blemish/expel management gate, the four real action triggers
(Mars/Mercury/Apollo/Pluto), and the CmdPray/CmdPontifex/CmdBlemish/
CmdExpel/CmdReligion command flows.
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create

from world.combat import AutoStatNPC, COMBAT_RULES
from world.religion import (
    PANTHEON_ALTAR_ROOM,
    RELIGION_TRIGGERS,
    RELIGION_BONUSES,
    PIETY_PER_TICK,
    BLEMISH_AMOUNT,
    CmdPray,
    CmdPontifex,
    CmdBlemish,
    CmdExpel,
    CmdReligion,
    piety_tier,
    can_manage_religion,
    join_religion,
    leave_religion,
    add_piety,
    religion_bonus,
    credit_mars_kill,
    credit_mercury_trade,
    credit_apollo_heal,
    credit_pluto_resurrection,
    ensure_religion_channels_exist,
    get_religion_channel,
)


class TestPietyTier(EvenniaTest):
    def test_boundaries(self):
        self.assertIsNone(piety_tier(0))
        self.assertIsNone(piety_tier(24))
        self.assertEqual(piety_tier(25), "Favored")
        self.assertEqual(piety_tier(74), "Favored")
        self.assertEqual(piety_tier(75), "Devoted")
        self.assertEqual(piety_tier(149), "Devoted")
        self.assertEqual(piety_tier(150), "Beloved")


class TestCanManageReligion(EvenniaTest):
    def test_god_can_manage_any_religion(self):
        self.char1.db.level = 101
        self.char1.db.religion = None
        self.assertTrue(can_manage_religion(self.char1, "mars"))

    def test_pontifex_of_own_religion(self):
        self.char1.db.level = 10
        self.char1.db.religion = "mars"
        self.char1.db.religion_rank = "pontifex"
        self.assertTrue(can_manage_religion(self.char1, "mars"))

    def test_pontifex_of_a_different_religion_cannot_manage_this_one(self):
        self.char1.db.level = 10
        self.char1.db.religion = "mercury"
        self.char1.db.religion_rank = "pontifex"
        self.assertFalse(can_manage_religion(self.char1, "mars"))

    def test_ordinary_member_cannot_manage(self):
        self.char1.db.level = 10
        self.char1.db.religion = "mars"
        self.char1.db.religion_rank = "member"
        self.assertFalse(can_manage_religion(self.char1, "mars"))


class TestJoinLeaveAndAddPiety(EvenniaTest):
    def test_join_sets_religion_and_member_rank(self):
        join_religion(self.char1, "mars")
        self.assertEqual(self.char1.db.religion, "mars")
        self.assertEqual(self.char1.db.religion_rank, "member")

    def test_leave_clears_both(self):
        join_religion(self.char1, "mars")
        leave_religion(self.char1)
        self.assertIsNone(self.char1.db.religion)
        self.assertIsNone(self.char1.db.religion_rank)

    def test_add_piety_floors_at_zero(self):
        self.char1.db.piety = {"mars": 5}
        add_piety(self.char1, "mars", -100)
        self.assertEqual(self.char1.db.piety["mars"], 0)

    def test_add_piety_announces_a_new_tier(self):
        self.char1.db.piety = {"mars": 20}
        add_piety(self.char1, "mars", 10)  # crosses into Favored (25)
        self.assertEqual(self.char1.db.piety["mars"], 30)


class TestActionTriggers(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.religion = None
        self.char1.db.piety = {}
        self.char1.db.piety_progress = {}

    def _tick_to_threshold(self, credit_fn, god_key, arg):
        required = RELIGION_TRIGGERS[god_key]["count_required"]
        for _ in range(required):
            credit_fn(arg)

    def test_mars_kill_ignored_for_non_mars_devotee(self):
        self.char1.db.religion = "mercury"
        npc = create.create_object(AutoStatNPC, key="dummy", location=self.room1)
        npc.db.damage_log = {self.char1: 10}
        credit_mars_kill(npc)
        self.assertEqual(self.char1.db.piety.get("mars", 0), 0)

    def test_mars_kill_ticks_piety_at_threshold_and_resets_counter(self):
        self.char1.db.religion = "mars"
        required = RELIGION_TRIGGERS["mars"]["count_required"]

        for i in range(required - 1):
            npc = create.create_object(AutoStatNPC, key="dummy", location=self.room1)
            npc.db.damage_log = {self.char1: 10}
            credit_mars_kill(npc)
        self.assertEqual(self.char1.db.piety.get("mars", 0), 0)

        npc = create.create_object(AutoStatNPC, key="dummy", location=self.room1)
        npc.db.damage_log = {self.char1: 10}
        credit_mars_kill(npc)
        self.assertEqual(self.char1.db.piety["mars"], PIETY_PER_TICK)
        self.assertEqual(self.char1.db.piety_progress["mars"], 0)

    def test_mercury_trade_ticks_piety(self):
        self.char1.db.religion = "mercury"
        required = RELIGION_TRIGGERS["mercury"]["count_required"]
        for _ in range(required):
            credit_mercury_trade(self.char1)
        self.assertEqual(self.char1.db.piety["mercury"], PIETY_PER_TICK)

    def test_apollo_heal_ticks_piety(self):
        self.char1.db.religion = "apollo"
        required = RELIGION_TRIGGERS["apollo"]["count_required"]
        for _ in range(required):
            credit_apollo_heal(self.char1)
        self.assertEqual(self.char1.db.piety["apollo"], PIETY_PER_TICK)

    def test_pluto_resurrection_grants_piety_immediately_no_counter(self):
        self.char1.db.religion = "pluto"
        credit_pluto_resurrection(self.char1)
        self.assertGreater(self.char1.db.piety["pluto"], 0)

    def test_pluto_ignored_for_non_pluto_devotee(self):
        self.char1.db.religion = "mars"
        credit_pluto_resurrection(self.char1)
        self.assertEqual(self.char1.db.piety.get("pluto", 0), 0)


class TestCmdPray(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.religion = None
        self.char1.db.religion_rank = None
        self.jupiter_cella = create.create_object(
            "typeclasses.rooms.Room", key="Main Cella - Jupiter"
        )
        self.altar = create.create_object(
            "typeclasses.rooms.Room", key=PANTHEON_ALTAR_ROOM
        )

    def test_implicit_join_at_dedicated_temple_requires_confirm(self):
        self.char1.location = self.jupiter_cella
        result = self.call(CmdPray(), "", caller=self.char1)
        self.assertIn("pray jupiter confirm", result)
        self.assertIsNone(self.char1.db.religion)

    def test_implicit_join_confirmed_actually_joins(self):
        self.char1.location = self.jupiter_cella
        result = self.call(CmdPray(), "confirm", caller=self.char1)
        self.assertIn("devote yourself to Jupiter", result)
        self.assertEqual(self.char1.db.religion, "jupiter")

    def test_mismatched_explicit_god_at_a_specific_temple_is_refused(self):
        self.char1.location = self.jupiter_cella
        result = self.call(CmdPray(), "mars confirm", caller=self.char1)
        self.assertIn("belongs to Jupiter", result)
        self.assertIsNone(self.char1.db.religion)

    def test_pantheon_altar_requires_explicit_god(self):
        self.char1.location = self.altar
        result = self.call(CmdPray(), "", caller=self.char1)
        self.assertIn("Pray to which god", result)

    def test_pantheon_altar_works_for_a_god_with_no_dedicated_temple(self):
        self.char1.location = self.altar
        result = self.call(CmdPray(), "neptune confirm", caller=self.char1)
        self.assertEqual(self.char1.db.religion, "neptune")

    def test_no_shrine_elsewhere(self):
        self.char1.location = self.room1
        result = self.call(CmdPray(), "", caller=self.char1)
        self.assertIn("no shrine here", result)

    def test_ordinary_member_cannot_switch_religions(self):
        self.char1.db.religion = "mars"
        self.char1.db.level = 10
        self.char1.location = self.jupiter_cella
        result = self.call(CmdPray(), "confirm", caller=self.char1)
        self.assertIn("already devoted to Mars", result)
        self.assertEqual(self.char1.db.religion, "mars")

    def test_god_can_switch_freely(self):
        self.char1.db.religion = "mars"
        self.char1.db.level = 101
        self.char1.location = self.jupiter_cella
        result = self.call(CmdPray(), "confirm", caller=self.char1)
        self.assertEqual(self.char1.db.religion, "jupiter")


class TestCmdPontifex(EvenniaCommandTest):
    def test_non_god_refused(self):
        self.char1.db.level = 50
        result = self.call(CmdPontifex(), "mars = Char2", caller=self.char1)
        self.assertIn("lack the standing", result)

    def test_god_appoints_and_auto_joins_if_needed(self):
        self.char1.db.level = 101
        self.char2.db.religion = None
        result = self.call(CmdPontifex(), "mars = Char2", caller=self.char1)
        self.assertIn("Pontifex", result)
        self.assertEqual(self.char2.db.religion, "mars")
        self.assertEqual(self.char2.db.religion_rank, "pontifex")


class TestCmdBlemish(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char2.db.religion = "mars"
        self.char2.db.religion_rank = "member"
        self.char2.db.piety = {"mars": 50}
        self.char1.db.blemish_cooldowns = {}

    def test_requires_a_reason(self):
        self.char1.db.level = 101
        result = self.call(CmdBlemish(), "Char2 = ", caller=self.char1)
        self.assertIn("reason is required", result)

    def test_non_manager_refused(self):
        self.char1.db.level = 10
        self.char1.db.religion = None
        result = self.call(CmdBlemish(), "Char2 = betraying Mars", caller=self.char1)
        self.assertIn("don't have the standing", result)
        self.assertEqual(self.char2.db.piety["mars"], 50)

    def test_god_can_blemish_and_it_is_logged(self):
        self.char1.db.level = 101
        result = self.call(CmdBlemish(), "Char2 = fled from battle", caller=self.char1)
        self.assertIn("blemished", result)
        self.assertEqual(self.char2.db.piety["mars"], 50 - BLEMISH_AMOUNT)
        self.assertEqual(len(self.char2.db.religion_log), 1)
        self.assertEqual(self.char2.db.religion_log[0]["reason"], "fled from battle")

    def test_cooldown_blocks_a_second_blemish_from_the_same_discipliner(self):
        self.char1.db.level = 101
        self.call(CmdBlemish(), "Char2 = first offense", caller=self.char1)
        result = self.call(CmdBlemish(), "Char2 = second offense", caller=self.char1)
        self.assertIn("too recently", result)
        self.assertEqual(self.char2.db.piety["mars"], 50 - BLEMISH_AMOUNT)


class TestCmdExpel(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char2.db.religion = "mars"
        self.char2.db.religion_rank = "member"
        self.char2.db.piety = {"mars": 50}

    def test_requires_a_reason(self):
        self.char1.db.level = 101
        result = self.call(CmdExpel(), "Char2 = ", caller=self.char1)
        self.assertIn("reason is required", result)

    def test_god_can_expel_preserving_piety(self):
        self.char1.db.level = 101
        result = self.call(CmdExpel(), "Char2 = renounced the faith", caller=self.char1)
        self.assertIn("expelled", result)
        self.assertIsNone(self.char2.db.religion)
        self.assertEqual(self.char2.db.piety["mars"], 50)  # preserved, not erased
        self.assertEqual(len(self.char2.db.religion_log), 1)


class TestCmdReligion(EvenniaCommandTest):
    def test_no_piety_shows_empty_state(self):
        self.char1.db.piety = {}
        result = self.call(CmdReligion(), "", caller=self.char1)
        self.assertIn("no standing with any god", result)

    def test_shows_own_standing(self):
        self.char1.db.piety = {"mars": 30}
        self.char1.db.religion = "mars"
        self.char1.db.religion_rank = "member"
        result = self.call(CmdReligion(), "", caller=self.char1)
        self.assertIn("Mars", result)
        self.assertIn("Favored", result)

    def test_log_refused_for_non_god(self):
        self.char1.db.level = 50
        result = self.call(CmdReligion(), "log mars", caller=self.char1)
        self.assertIn("Only gods", result)

    def test_log_shows_logged_entries(self):
        self.char1.db.level = 101
        self.char2.db.religion = "mars"
        self.char2.db.religion_log = [
            {"action": "blemish", "by": "Someone", "reason": "test reason", "time": 1.0}
        ]
        result = self.call(CmdReligion(), "log mars", caller=self.char1)
        self.assertIn("test reason", result)


class TestReligionBonus(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.religion = None
        self.char1.db.piety = {}

    def test_no_bonus_below_devoted(self):
        self.char1.db.religion = "mars"
        self.char1.db.piety = {"mars": 30}  # Favored, not Devoted
        self.assertEqual(religion_bonus(self.char1, "mars", "melee_damage_bonus"), 0)

    def test_devoted_grants_the_defined_bonus(self):
        self.char1.db.religion = "mars"
        self.char1.db.piety = {"mars": 80}  # Devoted
        self.assertEqual(
            religion_bonus(self.char1, "mars", "melee_damage_bonus"),
            RELIGION_BONUSES["mars"]["Devoted"]["melee_damage_bonus"],
        )

    def test_wrong_religion_gets_nothing(self):
        self.char1.db.religion = "mercury"
        self.char1.db.piety = {"mars": 200}  # high Mars piety, but not currently devoted to Mars
        self.assertEqual(religion_bonus(self.char1, "mars", "melee_damage_bonus"), 0)

    def test_god_with_no_bonus_defined_returns_zero(self):
        self.char1.db.religion = "neptune"
        self.char1.db.piety = {"neptune": 200}
        self.assertEqual(religion_bonus(self.char1, "neptune", "melee_damage_bonus"), 0)


class TestReligionChannels(EvenniaTest):
    def test_ensure_creates_one_channel_per_god(self):
        from world.god_help import PANTHEON

        created = ensure_religion_channels_exist()
        self.assertEqual(len(created), len(PANTHEON))
        for god_key in PANTHEON:
            self.assertIsNotNone(get_religion_channel(god_key))

    def test_ensure_is_idempotent(self):
        ensure_religion_channels_exist()
        second_pass = ensure_religion_channels_exist()
        self.assertEqual(len(second_pass), 0)

    def test_joining_connects_to_the_channel(self):
        ensure_religion_channels_exist()
        join_religion(self.char1, "mars")
        channel = get_religion_channel("mars")
        self.assertTrue(channel.has_connection(self.char1))

    def test_leaving_disconnects_from_the_channel(self):
        ensure_religion_channels_exist()
        join_religion(self.char1, "mars")
        leave_religion(self.char1)
        channel = get_religion_channel("mars")
        self.assertFalse(channel.has_connection(self.char1))

    def test_switching_religions_disconnects_the_old_channel(self):
        ensure_religion_channels_exist()
        join_religion(self.char1, "mars")
        join_religion(self.char1, "mercury")
        mars_channel = get_religion_channel("mars")
        mercury_channel = get_religion_channel("mercury")
        self.assertFalse(mars_channel.has_connection(self.char1))
        self.assertTrue(mercury_channel.has_connection(self.char1))
