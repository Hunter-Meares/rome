"""
Tests for the quest framework (world/quests.py): the generic quest
log, both step types ("kill" and "visit"), the personal-instance NPC
spawn for a kill quest, and the CmdQuest command flow (start /
reminder / turn-in / already-completed / log-only-when-no-giver).
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create

from world.combat import AutoStatNPC
from world.quests import (
    QUESTS,
    CmdQuest,
    start_quest,
    credit_quest_kill,
    check_quest_visit,
    list_all_quest_activity,
    quest_catalog,
)


class TestStartQuest(EvenniaTest):
    def test_visit_quest_just_sets_in_progress(self):
        start_quest(self.char1, "secession_memory")
        self.assertEqual(self.char1.db.quest_log["secession_memory"], "in_progress")

    def test_kill_quest_spawns_a_tagged_npc_in_the_right_room(self):
        start_quest(self.char1, "corrupt_official")

        self.assertEqual(self.char1.db.quest_log["corrupt_official"], "in_progress")

        from evennia.utils import search
        gallery = search.search_object(
            "Saepta Julia - Shopping Gallery", typeclass="typeclasses.rooms.Room"
        )
        if not gallery:
            self.skipTest("Shopping Gallery not present in this test DB")
        spawned = [
            o for o in gallery[0].contents
            if o.db.quest_key == "corrupt_official"
        ]
        self.assertEqual(len(spawned), 1)


class TestCreditQuestKill(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.quest_log = {}
        self.char2.db.quest_log = {}

    def _make_defeated(self, quest_key, damage_log):
        npc = create.create_object(AutoStatNPC, key="dummy", location=self.room1)
        npc.db.quest_key = quest_key
        npc.db.damage_log = damage_log
        return npc

    def test_matching_in_progress_quest_advances_to_ready(self):
        self.char1.db.quest_log["corrupt_official"] = "in_progress"
        npc = self._make_defeated("corrupt_official", {self.char1: 40})

        credit_quest_kill(npc)

        self.assertEqual(self.char1.db.quest_log["corrupt_official"], "ready")

    def test_no_quest_key_on_defeated_does_not_crash(self):
        npc = self._make_defeated(None, {self.char1: 40})
        credit_quest_kill(npc)
        self.assertEqual(self.char1.db.quest_log, {})

    def test_unrelated_character_in_damage_log_is_unaffected(self):
        """Only char2 has this quest active - char1's damage shouldn't touch it."""
        self.char2.db.quest_log["corrupt_official"] = "in_progress"
        npc = self._make_defeated("corrupt_official", {self.char1: 40})

        credit_quest_kill(npc)

        self.assertNotIn("corrupt_official", self.char1.db.quest_log)
        self.assertEqual(self.char2.db.quest_log["corrupt_official"], "in_progress")

    def test_already_ready_is_not_touched_again(self):
        self.char1.db.quest_log["corrupt_official"] = "ready"
        npc = self._make_defeated("corrupt_official", {self.char1: 40})
        credit_quest_kill(npc)
        self.assertEqual(self.char1.db.quest_log["corrupt_official"], "ready")

    def test_none_contributor_in_damage_log_does_not_crash(self):
        self.char1.db.quest_log["corrupt_official"] = "in_progress"
        npc = self._make_defeated("corrupt_official", {None: 40, self.char1: 60})
        credit_quest_kill(npc)
        self.assertEqual(self.char1.db.quest_log["corrupt_official"], "ready")


class TestCheckQuestVisit(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.quest_log = {"secession_memory": "in_progress"}

    def test_arriving_at_the_target_room_advances_to_ready(self):
        self.char1.location = self.room1
        self.room1.key = "The Secession Stone"
        check_quest_visit(self.char1)
        self.assertEqual(self.char1.db.quest_log["secession_memory"], "ready")

    def test_a_different_room_does_nothing(self):
        self.char1.location = self.room1
        self.room1.key = "Some Other Room"
        check_quest_visit(self.char1)
        self.assertEqual(self.char1.db.quest_log["secession_memory"], "in_progress")

    def test_not_in_progress_is_left_alone(self):
        self.char1.db.quest_log["secession_memory"] = "completed"
        self.char1.location = self.room1
        self.room1.key = "The Secession Stone"
        check_quest_visit(self.char1)
        self.assertEqual(self.char1.db.quest_log["secession_memory"], "completed")


class TestCmdQuest(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.quest_log = {}
        self.char1.db.level = 1
        self.giver = create.create_object(
            "typeclasses.characters.Character",
            key="the old man who remembers",
            location=self.room1,
        )

    def test_no_giver_and_no_quests_shows_empty_log_message(self):
        self.char1.location = self.room2
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("no quests", result)

    def test_no_giver_but_has_quests_shows_log(self):
        self.char1.location = self.room2
        self.char1.db.quest_log = {"secession_memory": "in_progress"}
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("Memory of the Secession", result)
        self.assertIn("in progress", result)

    def test_first_interaction_starts_the_quest(self):
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertEqual(self.char1.db.quest_log["secession_memory"], "in_progress")
        self.assertIn("leans forward", result)

    def test_level_gate_refuses_if_underleveled(self):
        QUESTS["secession_memory"]["level_required"] = 5
        try:
            result = self.call(CmdQuest(), "", caller=self.char1)
            self.assertIn("doesn't think you're ready", result)
            self.assertNotIn("secession_memory", self.char1.db.quest_log)
        finally:
            QUESTS["secession_memory"]["level_required"] = 1

    def test_second_interaction_while_in_progress_shows_reminder(self):
        self.char1.db.quest_log["secession_memory"] = "in_progress"
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("Well?", result)

    def test_ready_state_pays_out_and_marks_completed(self):
        # Level kept high enough that the 40 XP reward can't cross this
        # level's own xp_for_level threshold - award_xp's level-up
        # bookkeeping subtracts from db.xp as it advances, which would
        # make a direct "how much landed" assertion meaningless
        # otherwise (see TestAtDefeatXpGoldSplit's own comment on this
        # exact trap in world/tests_combat.py).
        self.char1.db.level = 10
        self.char1.db.quest_log["secession_memory"] = "ready"
        self.char1.db.gold = 0
        self.char1.db.xp = 0

        result = self.call(CmdQuest(), "", caller=self.char1)

        self.assertIn("nods slowly", result)
        self.assertEqual(self.char1.db.gold, 30)
        self.assertEqual(self.char1.db.xp, 40)
        self.assertEqual(self.char1.db.quest_log["secession_memory"], "completed")

    def test_completed_state_has_nothing_more(self):
        self.char1.db.quest_log["secession_memory"] = "completed"
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("nothing more for you", result)


class TestListAllQuestActivity(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.quest_log = {}
        self.char2.db.quest_log = {}

    def test_empty_state_message(self):
        self.assertIn("No players have any quest activity", list_all_quest_activity())

    def test_shows_multiple_players_and_states_including_completed(self):
        self.char1.db.quest_log = {"secession_memory": "completed"}
        self.char2.db.quest_log = {"corrupt_official": "in_progress"}

        result = list_all_quest_activity()

        self.assertIn(self.char1.key, result)
        self.assertIn("Memory of the Secession", result)
        self.assertIn("completed", result)
        self.assertIn(self.char2.key, result)
        self.assertIn("The Corrupt Count", result)
        self.assertIn("in progress", result)

    def test_accountless_character_is_excluded(self):
        npc = create.create_object(
            "typeclasses.characters.Character", key="a stray npc", location=self.room1
        )
        npc.db.quest_log = {"secession_memory": "in_progress"}
        self.assertIsNone(npc.account)
        result = list_all_quest_activity()
        self.assertIn("No players have any quest activity", result)


class TestQuestCatalog(EvenniaTest):
    def test_includes_every_defined_quest(self):
        result = quest_catalog()
        for quest in QUESTS.values():
            self.assertIn(quest["name"], result)
            self.assertIn(quest["giver_key"], result)

    def test_reports_not_placed_when_giver_absent_from_test_db(self):
        result = quest_catalog()
        self.assertIn("not currently placed", result)

    def test_a_newly_added_quest_appears_with_no_code_changes(self):
        """
        Proves the actual design claim: adding a quest to QUESTS at
        runtime (simulating a future edit to the real dict) makes it
        show up here with zero changes to quest_catalog() itself.
        """
        QUESTS["fake_future_quest"] = {
            "name": "A Brand New Errand",
            "giver_key": "someone new",
            "level_required": 1,
            "step_type": "visit",
            "target_room": "Nowhere",
            "reward_gold": 1,
            "reward_xp": 1,
        }
        try:
            result = quest_catalog()
            self.assertIn("A Brand New Errand", result)
        finally:
            del QUESTS["fake_future_quest"]


class TestCmdQuestOversight(EvenniaCommandTest):
    def test_non_god_refused(self):
        self.char1.db.level = 50
        result = self.call(CmdQuest(), "list", caller=self.char1)
        self.assertIn("Only gods", result)

    def test_god_gets_list_even_with_no_giver_in_room(self):
        self.char1.db.level = 101
        self.char1.db.quest_log = {}
        result = self.call(CmdQuest(), "list", caller=self.char1)
        self.assertIn("No players have any quest activity", result)

    def test_god_gets_catalog_even_with_no_giver_in_room(self):
        self.char1.db.level = 101
        result = self.call(CmdQuest(), "catalog", caller=self.char1)
        self.assertIn("Memory of the Secession", result)


class TestQuestDataIntegrity(EvenniaTest):
    """
    Structural checks over EVERY real quest in QUESTS - the nine added
    alongside class_bonus included - guarding the two real engine
    limits documented in world/quests.py's own docstring (one quest per
    giver; a kill target must not be a RespawningNPC), plus the basic
    "no typo'd field name silently breaks a quest at turn-in" shape.
    Deliberately reads the live QUESTS dict rather than a hardcoded
    list, so a quest added later is covered automatically.
    """

    REQUIRED = (
        "name", "giver_key", "level_required", "step_type",
        "reward_gold", "reward_xp", "intro", "reminder", "complete",
    )

    def test_every_quest_has_every_required_field(self):
        for key, quest in QUESTS.items():
            for field in self.REQUIRED:
                self.assertIn(field, quest, "%s is missing %r" % (key, field))
                self.assertTrue(quest[field] not in (None, ""), "%s.%s is empty" % (key, field))

    def test_step_type_is_one_the_engine_supports(self):
        for key, quest in QUESTS.items():
            self.assertIn(quest["step_type"], ("kill", "visit"), key)

    def test_visit_quests_name_a_target_room(self):
        for key, quest in QUESTS.items():
            if quest["step_type"] == "visit":
                self.assertTrue(quest.get("target_room"), key)

    def test_kill_quests_name_a_prototype_and_a_spawn_room(self):
        for key, quest in QUESTS.items():
            if quest["step_type"] == "kill":
                self.assertTrue(quest.get("npc_prototype"), key)
                self.assertTrue(quest.get("spawn_room"), key)

    def test_every_giver_is_unique_across_quests(self):
        # The real engine limit: CmdQuest matches a giver by exact key
        # and always offers the FIRST matching quest, so a second quest
        # sharing a giver_key would silently never be reachable.
        givers = [quest["giver_key"] for quest in QUESTS.values()]
        self.assertEqual(len(givers), len(set(givers)))

    def test_kill_targets_exist_and_are_not_respawning(self):
        # A RespawningNPC target would come back to life instead of
        # staying dead (at_defeat's respawn branch runs before the
        # personal-instance delete branch) - the quest could never be
        # finished twice by anyone else, and a "dead" target would
        # reappear.
        import world.prototypes as protos

        for key, quest in QUESTS.items():
            if quest["step_type"] != "kill":
                continue
            proto = getattr(protos, quest["npc_prototype"], None)
            self.assertIsNotNone(proto, "%s: no prototype %s" % (key, quest["npc_prototype"]))
            self.assertEqual(proto["typeclass"], "world.combat.HostileNPC", key)

    def test_rewards_and_levels_are_positive_ints(self):
        for key, quest in QUESTS.items():
            for field in ("level_required", "reward_gold", "reward_xp"):
                self.assertIsInstance(quest[field], int, "%s.%s" % (key, field))
                self.assertGreater(quest[field], 0, "%s.%s" % (key, field))

    def test_class_bonus_shape_and_real_classes(self):
        from world.chargen_menu import CLASSES

        for key, quest in QUESTS.items():
            bonus = quest.get("class_bonus")
            if not bonus:
                continue
            self.assertTrue(bonus["classes"], key)
            for cls in bonus["classes"]:
                self.assertIn(cls, CLASSES, "%s: %r is not a real class" % (key, cls))
            for field in ("bonus_gold", "bonus_xp"):
                self.assertIsInstance(bonus[field], int, "%s.%s" % (key, field))
                self.assertGreater(bonus[field], 0, "%s.%s" % (key, field))
            for field in ("intro", "complete"):
                self.assertTrue(bonus[field], "%s.%s" % (key, field))

    def test_quest_titles_only_reference_real_quests(self):
        from world.titles import QUEST_TITLES

        for quest_key in QUEST_TITLES:
            self.assertIn(quest_key, QUESTS)


class TestClassBonus(EvenniaCommandTest):
    """
    class_bonus: a class-FLAVORED bonus, deliberately not a lock. Uses
    a patched-in fake quest so these tests don't depend on any real
    quest's numbers or text.
    """

    def setUp(self):
        super().setUp()
        fake = {
            "name": "The Bonus Test",
            "giver_key": "a test giver",
            "level_required": 1,
            "step_type": "visit",
            "target_room": "Nowhere",
            "reward_gold": 10,
            "reward_xp": 20,
            "intro": "BASEINTRO",
            "reminder": "BASEREMINDER",
            "complete": "BASECOMPLETE",
            "class_bonus": {
                "classes": ["augur"],
                "bonus_gold": 5,
                "bonus_xp": 7,
                "intro": "BONUSINTRO",
                "complete": "BONUSCOMPLETE",
            },
        }
        patcher = patch.dict(QUESTS, {"bonus_test": fake})
        patcher.start()
        self.addCleanup(patcher.stop)

        create.create_object(
            "typeclasses.characters.Character", key="a test giver", location=self.room1
        )
        self.char1.db.quest_log = {}
        # High enough that the small XP amounts can't cross a level
        # threshold (award_xp's level-up bookkeeping would make a direct
        # "how much landed" assertion meaningless - see
        # TestCmdQuest.test_ready_state_pays_out_and_marks_completed).
        self.char1.db.level = 10
        self.char1.db.gold = 0
        self.char1.db.xp = 0

    def test_matching_class_hears_the_extra_intro_line(self):
        self.char1.db.player_class = "augur"
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("BASEINTRO", result)
        self.assertIn("BONUSINTRO", result)

    def test_other_class_does_not_hear_it(self):
        self.char1.db.player_class = "gladiator"
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("BASEINTRO", result)
        self.assertNotIn("BONUSINTRO", result)

    def test_matching_class_is_paid_the_bonus_on_top(self):
        self.char1.db.player_class = "augur"
        self.char1.db.quest_log["bonus_test"] = "ready"
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertEqual(self.char1.db.gold, 15)
        self.assertEqual(self.char1.db.xp, 27)
        self.assertIn("BONUSCOMPLETE", result)
        self.assertIn("class bonus included", result)

    def test_other_class_is_paid_only_the_base(self):
        self.char1.db.player_class = "gladiator"
        self.char1.db.quest_log["bonus_test"] = "ready"
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertEqual(self.char1.db.gold, 10)
        self.assertEqual(self.char1.db.xp, 20)
        self.assertNotIn("BONUSCOMPLETE", result)
        self.assertNotIn("class bonus included", result)

    def test_character_with_no_class_set_is_just_paid_the_base(self):
        # Must not crash, and must not accidentally match.
        self.char1.db.player_class = None
        self.char1.db.quest_log["bonus_test"] = "ready"
        self.call(CmdQuest(), "", caller=self.char1)
        self.assertEqual(self.char1.db.gold, 10)

    def test_a_quest_with_no_class_bonus_at_all_is_unaffected(self):
        del QUESTS["bonus_test"]["class_bonus"]
        self.char1.db.player_class = "augur"
        self.char1.db.quest_log["bonus_test"] = "ready"
        self.call(CmdQuest(), "", caller=self.char1)
        self.assertEqual(self.char1.db.gold, 10)

    def test_no_quest_is_ever_refused_because_of_class(self):
        # The whole point of a bonus over a lock: any class can start
        # it, including one the bonus isn't for.
        self.char1.db.player_class = "medicus"
        self.call(CmdQuest(), "", caller=self.char1)
        self.assertEqual(self.char1.db.quest_log["bonus_test"], "in_progress")

    def test_god_catalog_shows_the_class_bonus(self):
        result = quest_catalog()
        self.assertIn("class bonus: augur +5g/+7xp", result)
