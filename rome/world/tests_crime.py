"""
Tests for world/crime.py - phase 1 of the crime-and-punishment project
(the data model and detection only; guards/jail/execution/confiscation
aren't built yet - see rome_mud_todo.md).
"""

import time
from unittest.mock import patch

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTestMixin

from world import crime
from world.combat import COMBAT_RULES, CombatTurnHandler, CmdDuel, HostileNPC


class CrimeTestBase(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.room1.tags.add("rome_proper_zone", category="zone")
        for char in (self.char1, self.char2):
            char.db.conditions = {}
            char.db.combat_turnhandler = None
            char.db.damage_log = {}
            char.db.homo_sacer = False
            char.db.wanted = False
            char.db.crime_events = []
            char.db.crime_record = []


class TestIsRomeProper(CrimeTestBase):
    def test_tagged_room_is_rome_proper(self):
        self.assertTrue(crime.is_rome_proper(self.room1))

    def test_untagged_room_is_not(self):
        self.assertFalse(crime.is_rome_proper(self.room2))

    def test_no_room_at_all_is_not(self):
        self.assertFalse(crime.is_rome_proper(None))


class TestIsSanctioned(CrimeTestBase):
    def test_true_when_combat_duel_partner_matches(self):
        self.char1.db.combat_duel_partner = self.char2
        self.assertTrue(crime.is_sanctioned(self.char1, self.char2))

    def test_false_by_default(self):
        self.assertFalse(crime.is_sanctioned(self.char1, self.char2))

    def test_false_if_the_partner_points_elsewhere(self):
        third = create.create_object("typeclasses.characters.Character", key="Third", location=self.room1)
        self.char1.db.combat_duel_partner = third
        self.assertFalse(crime.is_sanctioned(self.char1, self.char2))


class TestLogCrime(CrimeTestBase):
    def test_noop_outside_rome_proper(self):
        result = crime.log_crime(self.char1, self.char2, "assault", self.room2)
        self.assertIsNone(result)
        self.assertEqual(self.char1.db.crime_record, [])

    def test_noop_if_either_side_is_not_a_real_player(self):
        npc = create.create_object(HostileNPC, key="a brute", location=self.room1)
        self.assertIsNone(crime.log_crime(self.char1, npc, "assault", self.room1))
        self.assertIsNone(crime.log_crime(npc, self.char1, "assault", self.room1))

    def test_noop_for_a_sanctioned_duel(self):
        self.char1.db.combat_duel_partner = self.char2
        self.char2.db.combat_duel_partner = self.char1
        self.assertIsNone(crime.log_crime(self.char1, self.char2, "assault", self.room1))
        self.assertEqual(self.char1.db.crime_record, [])

    def test_noop_if_the_victim_is_already_homo_sacer(self):
        self.char2.db.homo_sacer = True
        self.assertIsNone(crime.log_crime(self.char1, self.char2, "murder", self.room1))
        self.assertEqual(self.char1.db.crime_record, [])

    def test_an_npc_present_auto_flags_the_crime_immediately(self):
        create.create_object(HostileNPC, key="a passing guard", location=self.room1)
        event = crime.log_crime(self.char1, self.char2, "assault", self.room1)
        self.assertTrue(event["resolved"])
        self.assertEqual(len(self.char1.db.crime_record), 1)
        self.assertEqual(self.char1.db.crime_record[0]["type"], "assault")
        self.assertTrue(self.char1.db.wanted)

    def test_no_npc_present_logs_but_does_not_flag(self):
        event = crime.log_crime(self.char1, self.char2, "theft", self.room1)
        self.assertFalse(event["resolved"])
        self.assertEqual(self.char1.db.crime_record, [])
        self.assertFalse(self.char1.db.wanted)
        self.assertIn(event, self.char1.db.crime_events)

    def test_a_bystander_player_is_recorded_as_present_but_not_flagged(self):
        bystander = create.create_object("typeclasses.characters.Character", key="Bystander", location=self.room1)
        bystander.account = self.account2  # a freshly create_object()'d Character has no account link by default
        event = crime.log_crime(self.char1, self.char2, "assault", self.room1)
        self.assertFalse(event["resolved"])
        self.assertIn(bystander, event["players_present"])

    def test_perpetrator_and_victim_are_never_counted_as_their_own_witness(self):
        event = crime.log_crime(self.char1, self.char2, "assault", self.room1)
        self.assertNotIn(self.char1, event["players_present"])
        self.assertNotIn(self.char2, event["players_present"])


class TestFlagCrime(CrimeTestBase):
    def test_murder_sets_homo_sacer_not_wanted(self):
        crime.flag_crime(self.char1, "murder", self.room1)
        self.assertTrue(self.char1.db.homo_sacer)
        self.assertFalse(self.char1.db.wanted)

    def test_lesser_crime_sets_wanted_not_homo_sacer(self):
        crime.flag_crime(self.char1, "theft", self.room1)
        self.assertTrue(self.char1.db.wanted)
        self.assertFalse(self.char1.db.homo_sacer)

    def test_weight_recorded_matches_crime_weights(self):
        crime.flag_crime(self.char1, "assault", self.room1)
        self.assertEqual(self.char1.db.crime_record[0]["weight"], crime.CRIME_WEIGHTS["assault"])

    def test_murder_announces_only_in_rome_proper_rooms(self):
        self.room2.tags.add("some_other_zone", category="zone")  # not rome_proper
        captured = {}

        def fake_msg_contents(self_room, text=None, **kwargs):
            captured[self_room] = text

        with patch("typeclasses.rooms.Room.msg_contents", fake_msg_contents):
            crime.flag_crime(self.char1, "murder", self.room1)
        self.assertIn(self.room1, captured)
        self.assertNotIn(self.room2, captured)
        self.assertIn("murderer", captured[self.room1])

    def test_theft_does_not_announce_anything(self):
        with patch("typeclasses.rooms.Room.msg_contents") as mocked:
            crime.flag_crime(self.char1, "theft", self.room1)
        mocked.assert_not_called()


class TestAccuse(CrimeTestBase):
    def test_cannot_accuse_with_no_logged_event(self):
        success, message = crime.accuse(self.char2, self.char1)
        self.assertFalse(success)
        self.assertIn("nothing to accuse", message)

    def test_cannot_accuse_yourself(self):
        success, message = crime.accuse(self.char1, self.char1)
        self.assertFalse(success)

    def test_the_victim_can_always_accuse_even_with_no_bystanders(self):
        crime.log_crime(self.char1, self.char2, "theft", self.room1)
        success, message = crime.accuse(self.char2, self.char1)
        self.assertTrue(success)
        self.assertTrue(self.char1.db.wanted)

    def test_a_genuine_bystander_can_accuse(self):
        bystander = create.create_object("typeclasses.characters.Character", key="Bystander", location=self.room1)
        bystander.account = self.account2
        crime.log_crime(self.char1, self.char2, "assault", self.room1)
        success, message = crime.accuse(bystander, self.char1)
        self.assertTrue(success)

    def test_someone_who_was_never_there_cannot_accuse(self):
        crime.log_crime(self.char1, self.char2, "assault", self.room1)
        stranger = create.create_object("typeclasses.characters.Character", key="Stranger", location=self.room2)
        stranger.account = self.account2
        success, message = crime.accuse(stranger, self.char1)
        self.assertFalse(success)

    def test_an_already_resolved_event_cannot_be_double_accused(self):
        create.create_object(HostileNPC, key="a guard", location=self.room1)
        crime.log_crime(self.char1, self.char2, "murder", self.room1)  # auto-resolved by the NPC
        success, message = crime.accuse(self.char2, self.char1)
        self.assertFalse(success)

    def test_an_expired_event_cannot_be_accused(self):
        crime.log_crime(self.char1, self.char2, "theft", self.room1)
        self.char1.db.crime_events[0]["timestamp"] = time.time() - crime.CRIME_EVENT_EXPIRY - 1
        success, message = crime.accuse(self.char2, self.char1)
        self.assertFalse(success)


class TestPilferHooksIntoCrime(CrimeTestBase):
    def setUp(self):
        super().setUp()
        self.char1.db.agilitas = 10
        self.char2.db.agilitas = 10
        self.char2.db.gold = 1000
        self.char1.db.gold = 0
        self.char1.db.level = 50
        self.char1.db.pilfer_log = {}

    def test_a_caught_pilfer_against_a_player_logs_theft(self):
        from world.combat import SKILLS

        with patch("world.combat.randint", return_value=100):  # guaranteed catch
            SKILLS["pilfer"]["skillfunc"](self.char1, "pilfer", [self.char2], 5)
        self.assertEqual(len(self.char1.db.crime_events), 1)
        self.assertEqual(self.char1.db.crime_events[0]["type"], "theft")

    def test_a_successful_pilfer_never_logs_anything_at_all(self):
        from world.combat import SKILLS

        with patch("world.combat.randint", return_value=1):  # guaranteed success
            SKILLS["pilfer"]["skillfunc"](self.char1, "pilfer", [self.char2], 5)
        self.assertEqual(self.char1.db.crime_events, [])


class TestDuelAndAssaultDetection(EvenniaCommandTestMixin, CrimeTestBase):
    def test_an_ordinary_fight_logs_assault(self):
        self.room1.ndb.pending_fighters = [self.char1, self.char2]
        self.room1.scripts.add(CombatTurnHandler)

        self.assertEqual(len(self.char1.db.crime_events), 1)
        self.assertEqual(self.char1.db.crime_events[0]["type"], "assault")
        # The victim never gets a crime logged for simply defending themselves.
        self.assertEqual(self.char2.db.crime_events, [])

    def test_a_sanctioned_duel_never_logs_anything(self):
        self.call(CmdDuel(), "Char2", caller=self.char1)
        self.call(CmdDuel(), "accept", caller=self.char2)

        self.assertEqual(self.char1.db.crime_events, [])
        self.assertEqual(self.char2.db.crime_events, [])

    def test_an_npc_present_auto_flags_the_assault(self):
        create.create_object(HostileNPC, key="a passing guard", location=self.room1)
        self.room1.ndb.pending_fighters = [self.char1, self.char2]
        self.room1.scripts.add(CombatTurnHandler)

        self.assertTrue(self.char1.db.wanted)


class TestMurderDetection(CrimeTestBase):
    def setUp(self):
        super().setUp()
        self.char1.db.level = 30
        self.char2.db.level = 30
        self.char1.db.max_hp = self.char1.db.hp = 100
        self.char2.db.max_hp = self.char2.db.hp = 0
        self.char2.db.damage_log = {self.char1: 50}
        self.char2.db.is_dead = False

    def test_an_unwitnessed_kill_in_an_empty_room_logs_but_never_flags(self):
        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)
        self.assertFalse(self.char1.db.homo_sacer)
        events = self.char1.db.crime_events or []
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "murder")

    def test_an_npc_witnessed_kill_is_flagged_immediately(self):
        create.create_object(HostileNPC, key="a market crowd", location=self.room1)
        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)
        self.assertTrue(self.char1.db.homo_sacer)

    def test_killing_an_already_homo_sacer_victim_is_not_a_new_crime(self):
        create.create_object(HostileNPC, key="a market crowd", location=self.room1)
        self.char2.db.homo_sacer = True
        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)
        self.assertEqual(self.char1.db.crime_record, [])

    def test_a_sanctioned_duel_kill_is_never_a_crime(self):
        create.create_object(HostileNPC, key="a market crowd", location=self.room1)
        self.char1.db.combat_duel_partner = self.char2
        self.char2.db.combat_duel_partner = self.char1
        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)
        self.assertFalse(self.char1.db.homo_sacer)

    def test_the_victim_can_accuse_their_own_killer_once_revived(self):
        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)
        success, message = crime.accuse(self.char2, self.char1)
        self.assertTrue(success)
        self.assertTrue(self.char1.db.homo_sacer)
