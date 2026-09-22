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
    STEP_TYPES,
    CmdQuest,
    start_quest,
    advance_quest,
    credit_quest_kill,
    check_quest_visit,
    ensure_kill_target,
    quest_target_is_live,
    quest_entry_hint,
    build_quest_log,
    get_steps,
    get_step_index,
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
    Structural checks over EVERY real quest in QUESTS, guarding the two
    real engine limits documented in world/quests.py's own docstring (one
    quest per giver; a kill target must not be a RespawningNPC), plus the
    basic "no typo'd field name silently breaks a quest at turn-in"
    shape. Step-aware: a quest is either the original flat single-step
    shape or an explicit "steps" list. Deliberately reads the live QUESTS
    dict rather than a hardcoded list, so a quest added later is covered
    automatically.
    """

    REQUIRED = (
        "name", "giver_key", "level_required",
        "reward_gold", "reward_xp", "intro", "reminder", "complete",
    )

    def _all_steps(self):
        for key, quest in QUESTS.items():
            for idx, step in enumerate(get_steps(quest)):
                yield key, idx, step

    def test_every_quest_has_every_required_field(self):
        for key, quest in QUESTS.items():
            for field in self.REQUIRED:
                self.assertIn(field, quest, "%s is missing %r" % (key, field))
                self.assertTrue(quest[field] not in (None, ""), "%s.%s is empty" % (key, field))

    def test_a_quest_is_either_flat_or_has_a_steps_list_never_both(self):
        for key, quest in QUESTS.items():
            self.assertNotEqual("steps" in quest, "step_type" in quest, key)

    def test_a_steps_list_really_is_multi_step(self):
        for key, quest in QUESTS.items():
            if "steps" in quest:
                self.assertGreaterEqual(len(quest["steps"]), 2, key)

    def test_every_step_type_is_one_the_engine_supports(self):
        for key, idx, step in self._all_steps():
            self.assertIn(step["type"], STEP_TYPES, "%s step %d" % (key, idx))

    def test_every_step_tells_the_player_what_to_do(self):
        # The log and every reminder show the step's objective text, so
        # an empty one would leave a player with no idea what's next.
        for key, idx, step in self._all_steps():
            self.assertTrue(step.get("objective"), "%s step %d has no objective" % (key, idx))

    def test_each_step_has_the_fields_its_type_needs(self):
        for key, idx, step in self._all_steps():
            where = "%s step %d" % (key, idx)
            if step["type"] == "visit":
                self.assertTrue(step.get("target_room"), where)
            elif step["type"] == "kill":
                self.assertTrue(step.get("npc_prototype"), where)
                self.assertTrue(step.get("spawn_room"), where)
            elif step["type"] == "talk":
                self.assertTrue(step.get("npc_key"), where)

    def test_every_giver_is_unique_across_quests(self):
        # The real engine limit: CmdQuest matches a giver by exact key
        # and always offers the FIRST matching quest, so a second quest
        # sharing a giver_key would silently never be reachable.
        givers = [quest["giver_key"] for quest in QUESTS.values()]
        self.assertEqual(len(givers), len(set(givers)))

    def test_kill_targets_exist_and_are_not_respawning(self):
        # A RespawningNPC target would come back to life instead of
        # staying dead (at_defeat's respawn branch runs before the
        # personal-instance delete branch).
        import world.prototypes as protos

        for key, idx, step in self._all_steps():
            if step["type"] != "kill":
                continue
            proto = getattr(protos, step["npc_prototype"], None)
            self.assertIsNotNone(proto, "%s step %d: no prototype" % (key, idx))
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


def _fake_chain():
    """A three-step quest using every step type, for the engine tests."""
    return {
        "name": "The Fake Chain",
        "giver_key": "a chain giver",
        "level_required": 1,
        "reward_gold": 10,
        "reward_xp": 20,
        "intro": "CHAININTRO",
        "reminder": "CHAINREMINDER",
        "complete": "CHAINDONE",
        "steps": [
            {
                "type": "visit", "target_room": "Chain Room",
                "objective": "GO TO CHAIN ROOM", "advance": "CHAINSTORY1",
                "reminder": "STEP1REMINDER",
            },
            {
                "type": "talk", "npc_key": "a chain contact",
                "objective": "TALK TO CONTACT", "advance": "CHAINSTORY2",
            },
            {
                "type": "kill", "npc_prototype": "QUEST_CORRUPT_SCRIBE",
                "spawn_room": "Chain Alley", "objective": "KILL THE THING",
                "advance": "CHAINSTORY3",
            },
        ],
    }


def _fake_kill():
    """A flat single-step kill quest, for the target-recovery tests."""
    return {
        "name": "The Fake Hunt",
        "giver_key": "a hunt giver",
        "level_required": 1,
        "step_type": "kill",
        "npc_prototype": "QUEST_CORRUPT_SCRIBE",
        "spawn_room": "Chain Alley",
        "objective": "HUNT THE THING",
        "reward_gold": 5,
        "reward_xp": 5,
        "intro": "HUNTINTRO",
        "reminder": "HUNTREMINDER",
        "complete": "HUNTDONE",
    }


class _ChainFixture:
    """Shared setup: patched-in fake quests plus the two rooms they use."""

    def make_fixture(self):
        patcher = patch.dict(QUESTS, {"chain_test": _fake_chain(), "hunt_test": _fake_kill()})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.chain_room = create.create_object("typeclasses.rooms.Room", key="Chain Room")
        self.chain_alley = create.create_object("typeclasses.rooms.Room", key="Chain Alley")
        self.char1.db.quest_log = {}
        self.char1.db.quest_steps = {}
        self.char1.db.quest_targets = {}
        # High enough that small XP awards can't cross a level threshold.
        self.char1.db.level = 10
        self.char1.db.gold = 0
        self.char1.db.xp = 0
        self.char1.db.player_class = None
        self.char1.location = self.room1

    def capture_messages(self):
        self.msgs = []
        self.char1.msg = lambda text="", **kw: self.msgs.append(str(text))

    def said(self, needle):
        return any(needle in m for m in self.msgs)


class TestGetSteps(EvenniaTest):
    def test_a_flat_single_step_quest_is_normalized_to_one_step(self):
        steps = get_steps(QUESTS["ceres_favor"])
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["type"], "visit")
        self.assertEqual(steps[0]["target_room"], "Market Row - Back Stalls")
        self.assertTrue(steps[0]["objective"])

    def test_an_explicit_steps_list_is_returned_as_is(self):
        steps = get_steps(QUESTS["missing_quaestor"])
        self.assertEqual([step["type"] for step in steps], ["talk", "visit", "visit", "kill"])

    def test_step_index_defaults_to_zero_for_a_quest_already_in_progress(self):
        # What every player with a quest in progress BEFORE steps
        # existed looks like - no quest_steps attribute at all.
        self.char1.db.quest_log = {"ceres_favor": "in_progress"}
        self.assertIsNone(self.char1.db.quest_steps)
        self.assertEqual(get_step_index(self.char1, "ceres_favor"), 0)

    def test_step_index_is_clamped_to_a_real_step(self):
        self.char1.db.quest_steps = {"missing_quaestor": 99}
        self.assertEqual(get_step_index(self.char1, "missing_quaestor"), 3)
        self.char1.db.quest_steps = {"missing_quaestor": -4}
        self.assertEqual(get_step_index(self.char1, "missing_quaestor"), 0)


class TestMultiStepEngine(_ChainFixture, EvenniaTest):
    def setUp(self):
        super().setUp()
        self.make_fixture()
        self.capture_messages()

    def test_starting_begins_at_the_first_step(self):
        start_quest(self.char1, "chain_test")
        self.assertEqual(self.char1.db.quest_log["chain_test"], "in_progress")
        self.assertEqual(get_step_index(self.char1, "chain_test"), 0)

    def test_a_visit_step_advances_and_tells_the_player_what_is_next(self):
        start_quest(self.char1, "chain_test")
        self.char1.location = self.chain_room
        check_quest_visit(self.char1)

        self.assertEqual(get_step_index(self.char1, "chain_test"), 1)
        self.assertEqual(self.char1.db.quest_log["chain_test"], "in_progress")
        self.assertTrue(self.said("Objective complete"))
        self.assertTrue(self.said("CHAINSTORY1"))
        self.assertTrue(self.said("Next objective"))
        self.assertTrue(self.said("TALK TO CONTACT"))

    def test_the_wrong_room_does_not_advance(self):
        start_quest(self.char1, "chain_test")
        self.char1.location = self.room2
        check_quest_visit(self.char1)
        self.assertEqual(get_step_index(self.char1, "chain_test"), 0)

    def test_visiting_the_first_steps_room_again_does_not_skip_a_talk_step(self):
        start_quest(self.char1, "chain_test")
        self.char1.location = self.chain_room
        check_quest_visit(self.char1)
        self.assertEqual(get_step_index(self.char1, "chain_test"), 1)
        check_quest_visit(self.char1)  # still standing there
        self.assertEqual(get_step_index(self.char1, "chain_test"), 1)

    def test_reaching_a_kill_step_spawns_a_target_stamped_with_that_step(self):
        start_quest(self.char1, "chain_test")
        advance_quest(self.char1, "chain_test")  # visit -> talk
        advance_quest(self.char1, "chain_test")  # talk -> kill

        self.assertEqual(get_step_index(self.char1, "chain_test"), 2)
        spawned = [o for o in self.chain_alley.contents if o.db.quest_key == "chain_test"]
        self.assertEqual(len(spawned), 1)
        self.assertEqual(spawned[0].db.quest_step, 2)

    def test_finishing_the_last_step_marks_the_quest_ready(self):
        start_quest(self.char1, "chain_test")
        advance_quest(self.char1, "chain_test")
        advance_quest(self.char1, "chain_test")
        target = [o for o in self.chain_alley.contents if o.db.quest_key == "chain_test"][0]
        target.db.damage_log = {self.char1: 50}

        credit_quest_kill(target)

        self.assertEqual(self.char1.db.quest_log["chain_test"], "ready")
        self.assertTrue(self.said("CHAINSTORY3"))
        self.assertTrue(self.said("Return to report back"))

    def test_a_kill_from_an_earlier_step_cannot_skip_the_player_ahead(self):
        # Quest is only on step 1 (talk); an NPC stamped for step 2
        # dying must not credit it.
        start_quest(self.char1, "chain_test")
        advance_quest(self.char1, "chain_test")  # now on the talk step
        stray = create.create_object(AutoStatNPC, key="a stray target", location=self.room1)
        stray.db.quest_key = "chain_test"
        stray.db.quest_step = 2
        stray.db.damage_log = {self.char1: 50}

        credit_quest_kill(stray)

        self.assertEqual(get_step_index(self.char1, "chain_test"), 1)
        self.assertEqual(self.char1.db.quest_log["chain_test"], "in_progress")

    def test_a_legacy_target_with_no_step_stamp_still_counts_as_step_zero(self):
        # An NPC spawned before step-stamping existed has no
        # db.quest_step at all.
        start_quest(self.char1, "hunt_test")
        legacy = create.create_object(AutoStatNPC, key="a legacy target", location=self.room1)
        legacy.db.quest_key = "hunt_test"
        legacy.db.damage_log = {self.char1: 50}

        credit_quest_kill(legacy)

        self.assertEqual(self.char1.db.quest_log["hunt_test"], "ready")


class TestCmdQuestMultiStep(_ChainFixture, EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.make_fixture()
        self.giver = create.create_object(
            "typeclasses.characters.Character", key="a chain giver", location=self.room1
        )

    def test_the_intro_ends_with_the_first_objective(self):
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("CHAININTRO", result)
        self.assertIn("Objective:", result)
        self.assertIn("GO TO CHAIN ROOM", result)

    def test_the_giver_reminder_is_specific_to_the_current_step(self):
        self.char1.db.quest_log["chain_test"] = "in_progress"
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("STEP1REMINDER", result)
        self.assertIn("GO TO CHAIN ROOM", result)

    def test_a_step_with_no_reminder_of_its_own_uses_the_quests(self):
        self.char1.db.quest_log["chain_test"] = "in_progress"
        self.char1.db.quest_steps = {"chain_test": 1}
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("CHAINREMINDER", result)
        self.assertIn("TALK TO CONTACT", result)

    def test_a_talk_step_completes_when_you_use_quest_with_the_contact(self):
        self.char1.db.quest_log["chain_test"] = "in_progress"
        self.char1.db.quest_steps = {"chain_test": 1}
        create.create_object(
            "typeclasses.characters.Character", key="a chain contact", location=self.room1
        )

        result = self.call(CmdQuest(), "", caller=self.char1)

        self.assertIn("CHAINSTORY2", result)
        self.assertEqual(get_step_index(self.char1, "chain_test"), 2)

    def test_a_talk_step_does_not_fire_without_the_contact_present(self):
        self.char1.db.quest_log["chain_test"] = "in_progress"
        self.char1.db.quest_steps = {"chain_test": 1}
        self.call(CmdQuest(), "", caller=self.char1)
        self.assertEqual(get_step_index(self.char1, "chain_test"), 1)

    def test_the_contact_does_nothing_for_someone_not_on_that_step(self):
        # Standing next to the same NPC for an unrelated reason.
        create.create_object(
            "typeclasses.characters.Character", key="a chain contact", location=self.room1
        )
        self.char1.db.quest_log["chain_test"] = "in_progress"  # still step 0
        self.call(CmdQuest(), "", caller=self.char1)
        self.assertEqual(get_step_index(self.char1, "chain_test"), 0)

    def test_turning_in_pays_out_and_clears_step_bookkeeping(self):
        self.char1.db.quest_log["chain_test"] = "ready"
        self.char1.db.quest_steps = {"chain_test": 2}

        result = self.call(CmdQuest(), "", caller=self.char1)

        self.assertIn("CHAINDONE", result)
        self.assertEqual(self.char1.db.gold, 10)
        self.assertEqual(self.char1.db.quest_log["chain_test"], "completed")
        self.assertNotIn("chain_test", self.char1.db.quest_steps or {})


class TestQuestLog(_ChainFixture, EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.make_fixture()

    def test_quest_log_works_standing_right_next_to_a_giver(self):
        # The gap this fixes: plain 'quest' next to a giver interacts
        # with the giver, which used to make the log unreachable there.
        create.create_object(
            "typeclasses.characters.Character", key="a chain giver", location=self.room1
        )
        self.char1.db.quest_log["chain_test"] = "in_progress"

        result = self.call(CmdQuest(), "log", caller=self.char1)

        self.assertIn("The Fake Chain", result)
        self.assertNotIn("CHAININTRO", result)
        self.assertNotIn("CHAINREMINDER", result)

    def test_the_quests_alias_shows_the_log_and_does_not_start_anything(self):
        create.create_object(
            "typeclasses.characters.Character", key="a chain giver", location=self.room1
        )
        result = self.call(CmdQuest(), "", caller=self.char1, cmdstring="quests")
        self.assertIn("no quests", result)
        self.assertNotIn("chain_test", self.char1.db.quest_log)

    def test_the_log_shows_which_step_and_what_to_do_next(self):
        self.char1.db.quest_log["chain_test"] = "in_progress"
        self.char1.db.quest_steps = {"chain_test": 1}
        text = build_quest_log(self.char1)
        self.assertIn("in progress (step 2 of 3)", text)
        self.assertIn("TALK TO CONTACT", text)

    def test_a_single_step_quest_shows_no_step_counter(self):
        self.char1.db.quest_log["hunt_test"] = "in_progress"
        text = build_quest_log(self.char1)
        self.assertIn("in progress", text)
        self.assertNotIn("step 1 of", text)
        self.assertIn("HUNT THE THING", text)

    def test_a_ready_quest_says_who_to_report_to(self):
        self.char1.db.quest_log["chain_test"] = "ready"
        text = build_quest_log(self.char1)
        self.assertIn("ready to turn in", text)
        self.assertIn("a chain giver", text)

    def test_active_quests_are_listed_before_completed_ones(self):
        self.char1.db.quest_log = {"hunt_test": "completed", "chain_test": "in_progress"}
        text = build_quest_log(self.char1)
        self.assertLess(text.index("The Fake Chain"), text.index("The Fake Hunt"))

    def test_no_quests_at_all_returns_none(self):
        self.char1.db.quest_log = {}
        self.assertIsNone(build_quest_log(self.char1))


class TestKillTargetRecovery(_ChainFixture, EvenniaTest):
    """
    Real, confirmed gap: InstanceCleanupTimer deleted ANY personal
    instance NPC not mid-fight after 10 minutes, so a kill-quest target
    could vanish before a slow player reached it and the quest could
    never be finished. Two lines of defence, both covered here: quest
    targets are exempted from that cleanup, and a missing target is
    respawned.
    """

    def setUp(self):
        super().setUp()
        self.make_fixture()

    def _target(self):
        found = [o for o in self.chain_alley.contents if o.db.quest_key == "hunt_test"]
        return found[0] if found else None

    def test_a_target_that_is_still_alive_is_left_alone(self):
        start_quest(self.char1, "hunt_test")
        self.assertFalse(ensure_kill_target(self.char1, "hunt_test"))
        self.assertEqual(
            len([o for o in self.chain_alley.contents if o.db.quest_key == "hunt_test"]), 1
        )

    def test_a_missing_target_is_respawned(self):
        start_quest(self.char1, "hunt_test")
        self._target().delete()
        self.assertIsNone(self._target())

        self.assertTrue(ensure_kill_target(self.char1, "hunt_test"))

        self.assertIsNotNone(self._target())

    def test_a_target_spawned_before_bookkeeping_existed_is_adopted_not_duplicated(self):
        from world.combat import HostileNPC

        self.char1.db.quest_log["hunt_test"] = "in_progress"
        legacy = create.create_object(
            HostileNPC, key="a legacy target", location=self.chain_alley,
            attributes=[("quest_key", "hunt_test"), ("instance_owner", self.char1)],
        )
        self.assertEqual(self.char1.db.quest_targets, {})

        self.assertFalse(ensure_kill_target(self.char1, "hunt_test"))

        self.assertEqual(self.char1.db.quest_targets["hunt_test"], legacy)
        self.assertEqual(
            len([o for o in self.chain_alley.contents if o.db.quest_key == "hunt_test"]), 1
        )

    def test_a_non_kill_step_never_spawns_anything(self):
        start_quest(self.char1, "chain_test")  # step 0 is a visit
        self.assertFalse(ensure_kill_target(self.char1, "chain_test"))

    def test_walking_into_the_targets_room_respawns_it_if_it_went_missing(self):
        start_quest(self.char1, "hunt_test")
        self._target().delete()

        self.char1.location = self.chain_alley
        check_quest_visit(self.char1)

        self.assertIsNotNone(self._target())

    def test_a_live_target_is_recognized(self):
        start_quest(self.char1, "hunt_test")
        self.assertTrue(quest_target_is_live(self._target()))

    def test_a_target_is_no_longer_live_once_the_quest_moves_on(self):
        start_quest(self.char1, "hunt_test")
        target = self._target()
        self.char1.db.quest_log["hunt_test"] = "completed"
        self.assertFalse(quest_target_is_live(target))

    def test_an_ordinary_personal_instance_is_never_treated_as_a_quest_target(self):
        plain = create.create_object(AutoStatNPC, key="an ordinary opponent", location=self.room1)
        plain.db.instance_owner = self.char1
        self.assertFalse(quest_target_is_live(plain))

    def test_a_target_from_an_earlier_step_is_not_live(self):
        start_quest(self.char1, "chain_test")
        stray = create.create_object(AutoStatNPC, key="a stray", location=self.room1)
        stray.db.quest_key = "chain_test"
        stray.db.quest_step = 2
        stray.db.instance_owner = self.char1
        self.assertFalse(quest_target_is_live(stray))  # quest is on step 0

    def test_the_cleanup_timer_leaves_a_live_quest_target_alone(self):
        from world.combat import InstanceCleanupTimer

        start_quest(self.char1, "hunt_test")
        target = self._target()
        timer = create.create_script(InstanceCleanupTimer, obj=target, autostart=False)

        timer.at_repeat()

        self.assertTrue(target.pk)

    def test_the_cleanup_timer_still_cleans_up_once_the_quest_is_done(self):
        from world.combat import InstanceCleanupTimer

        start_quest(self.char1, "hunt_test")
        target = self._target()
        timer = create.create_script(InstanceCleanupTimer, obj=target, autostart=False)
        self.char1.db.quest_log["hunt_test"] = "completed"

        timer.at_repeat()

        self.assertFalse(target.pk)


class TestCleanupNpcsSparesQuestTargets(_ChainFixture, EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.make_fixture()

    def test_a_live_quest_target_is_not_listed_as_an_orphan(self):
        from world.combat import CmdCleanupNPCs

        start_quest(self.char1, "hunt_test")
        result = self.call(CmdCleanupNPCs(), "", caller=self.char1)
        self.assertIn("No orphaned personal NPCs found", result)


class TestQuestEntryHint(_ChainFixture, EvenniaTest):
    def setUp(self):
        super().setUp()
        self.make_fixture()
        self.capture_messages()
        self.giver = create.create_object(
            "typeclasses.characters.Character", key="a chain giver", location=self.room1
        )

    def test_hints_when_a_giver_here_has_a_quest_you_can_start(self):
        quest_entry_hint(self.char1)
        self.assertTrue(self.said("A chain giver looks like they have something for you"))
        self.assertTrue(self.said("quest"))

    def test_no_hint_if_you_are_below_the_level_requirement(self):
        QUESTS["chain_test"]["level_required"] = 50
        quest_entry_hint(self.char1)
        self.assertEqual(self.msgs, [])

    def test_no_hint_once_the_quest_is_started(self):
        self.char1.db.quest_log["chain_test"] = "in_progress"
        quest_entry_hint(self.char1)
        self.assertEqual(self.msgs, [])

    def test_no_hint_once_the_quest_is_completed(self):
        self.char1.db.quest_log["chain_test"] = "completed"
        quest_entry_hint(self.char1)
        self.assertEqual(self.msgs, [])

    def test_a_ready_quest_prompts_you_to_report_back(self):
        self.char1.db.quest_log["chain_test"] = "ready"
        quest_entry_hint(self.char1)
        self.assertTrue(self.said("waiting to hear how it went"))

    def test_no_hint_in_a_room_with_no_giver(self):
        self.char1.location = self.room2
        quest_entry_hint(self.char1)
        self.assertEqual(self.msgs, [])

    def test_a_character_with_no_location_does_not_crash(self):
        self.char1.location = None
        quest_entry_hint(self.char1)  # must not raise

    def test_moving_into_a_givers_room_triggers_the_hint_for_real_players(self):
        self.char1.location = self.room2
        with patch("evennia.objects.objects.DefaultObject.has_account", new=True), \
                patch("world.quests.quest_entry_hint") as mock_hint:
            self.char1.move_to(self.room1, quiet=True)
        mock_hint.assert_called_once_with(self.char1)

    def test_a_character_with_no_session_never_triggers_it(self):
        self.char1.location = self.room2
        with patch("world.quests.quest_entry_hint") as mock_hint:
            self.char1.move_to(self.room1, quiet=True)
        mock_hint.assert_not_called()
