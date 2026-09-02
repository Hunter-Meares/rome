"""
Tests for the bounty board (world/bounties.py) - tier selection, the
reward formula, party-aware progress crediting off a real damage_log,
and the CmdBounty command flow.

test_real_spawn_has_the_expected_key is the load-bearing one: it
verifies the actual mechanism the whole system depends on (a real
spawned NPC's own `.key` matches the prototype dict's "key" field)
against Evennia's real spawner, rather than assuming it. This
replaced an earlier, wrong assumption - a prototype-tag-based design
was tried first and seemed like the more "correct" mechanism, but an
equivalent load-bearing test against the real spawner proved
`prototype_key` is never actually injected into these dicts when
`spawn()` is given the raw dict object directly (as every sewer NPC's
setup script does) rather than a string looked up through Evennia's
own prototype registry - caught before this ever went live, exactly
what this kind of test is for. Kept as TestRealSpawnKeyMatching here,
now testing the assumption the shipped design actually relies on.
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create

from world.combat import COMBAT_RULES, AutoStatNPC
from world.bounties import (
    BOUNTY_TIERS,
    BountyBoard,
    CmdBounty,
    _tier_for_level,
    roll_bounty,
    credit_bounty_progress,
    list_active_bounties,
    bounty_catalog,
)
import world.prototypes as protos


class TestRealSpawnKeyMatching(EvenniaTest):
    def test_real_spawn_has_the_expected_key(self):
        """
        The load-bearing assumption this whole system depends on: a
        real object spawned from one of the BOUNTY_TIERS target dicts
        ends up with a `.key` equal to that same dict's own "key"
        field - verified against Evennia's real spawner, not assumed.
        """
        from evennia.prototypes.spawner import spawn

        target_dict, _ = BOUNTY_TIERS["novice"]["targets"][0]
        npc = spawn(target_dict)[0]
        self.assertEqual(npc.key, target_dict["key"])


class TestTierForLevel(EvenniaTest):
    def test_boundaries(self):
        self.assertEqual(_tier_for_level(1)[0], "novice")
        self.assertEqual(_tier_for_level(10)[0], "novice")
        self.assertEqual(_tier_for_level(11)[0], "veteran")
        self.assertEqual(_tier_for_level(18)[0], "veteran")
        self.assertEqual(_tier_for_level(19)[0], "champion")
        self.assertEqual(_tier_for_level(100)[0], "champion")

    def test_above_every_range_fails_safe_to_champion(self):
        self.assertEqual(_tier_for_level(150)[0], "champion")


class TestRollBounty(EvenniaTest):
    @patch("world.bounties.random.randint")
    @patch("world.bounties.random.choice")
    def test_roll_produces_expected_shape_and_reward_math(self, mock_choice, mock_randint):
        target_dict, display_name = BOUNTY_TIERS["novice"]["targets"][0]
        mock_choice.return_value = (target_dict, display_name)
        mock_randint.return_value = 4

        self.char1.db.level = 3
        bounty = roll_bounty(self.char1)

        self.assertEqual(bounty["tier"], "novice")
        self.assertEqual(bounty["target_key"], target_dict["key"])
        self.assertEqual(bounty["target_display"], display_name)
        self.assertEqual(bounty["count_required"], 4)
        self.assertEqual(bounty["count_progress"], 0)

        expected_xp = int(round(4 * target_dict["xp_reward"] * 0.75))
        self.assertEqual(bounty["xp_reward"], expected_xp)
        self.assertEqual(bounty["gold_reward"], max(1, expected_xp // 3))


class TestCreditBountyProgress(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.active_bounty = None
        self.char2.db.active_bounty = None

    def _make_defeated(self, key, damage_log):
        npc = create.create_object(AutoStatNPC, key=key, location=self.room1)
        npc.db.damage_log = damage_log
        return npc

    def test_matching_bounty_gets_credited(self):
        self.char1.db.active_bounty = {
            "target_key": "a Subura footpad",
            "target_display": "Subura footpads",
            "count_required": 3,
            "count_progress": 1,
        }
        npc = self._make_defeated("a Subura footpad", {self.char1: 50})

        credit_bounty_progress(npc)

        self.assertEqual(self.char1.db.active_bounty["count_progress"], 2)

    def test_non_matching_target_is_ignored(self):
        self.char1.db.active_bounty = {
            "target_key": "a Subura footpad",
            "target_display": "Subura footpads",
            "count_required": 3,
            "count_progress": 1,
        }
        npc = self._make_defeated("a Cloaca bandit", {self.char1: 50})

        credit_bounty_progress(npc)

        self.assertEqual(self.char1.db.active_bounty["count_progress"], 1)

    def test_no_active_bounty_does_not_crash(self):
        npc = self._make_defeated("a Subura footpad", {self.char1: 50})
        credit_bounty_progress(npc)  # should simply do nothing
        self.assertIsNone(self.char1.db.active_bounty)

    def test_already_complete_bounty_does_not_over_increment(self):
        self.char1.db.active_bounty = {
            "target_key": "a Subura footpad",
            "target_display": "Subura footpads",
            "count_required": 3,
            "count_progress": 3,
        }
        npc = self._make_defeated("a Subura footpad", {self.char1: 50})

        credit_bounty_progress(npc)

        self.assertEqual(self.char1.db.active_bounty["count_progress"], 3)

    def test_party_kill_credits_each_contributor_independently(self):
        """
        Two different characters, two completely different bounties,
        both advance off the same shared kill - the whole point of
        hooking the same damage_log the XP/gold split already uses.
        """
        self.char1.db.active_bounty = {
            "target_key": "a Subura footpad",
            "target_display": "Subura footpads",
            "count_required": 3,
            "count_progress": 0,
        }
        self.char2.db.active_bounty = {
            "target_key": "a Subura footpad",
            "target_display": "Subura footpads",
            "count_required": 5,
            "count_progress": 2,
        }
        npc = self._make_defeated("a Subura footpad", {self.char1: 30, self.char2: 70})

        credit_bounty_progress(npc)

        self.assertEqual(self.char1.db.active_bounty["count_progress"], 1)
        self.assertEqual(self.char2.db.active_bounty["count_progress"], 3)

    def test_none_contributor_in_damage_log_does_not_crash(self):
        """See CLAUDE.md gotcha #2 - a stale reference resolves to literal None."""
        self.char1.db.active_bounty = {
            "target_key": "a Subura footpad",
            "target_display": "Subura footpads",
            "count_required": 3,
            "count_progress": 0,
        }
        npc = self._make_defeated("a Subura footpad", {None: 50, self.char1: 50})
        credit_bounty_progress(npc)
        self.assertEqual(self.char1.db.active_bounty["count_progress"], 1)


class TestCmdBounty(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.active_bounty = None
        self.board = create.create_object(BountyBoard, key="a bounty board", location=self.room1)

    def test_no_board_here_refuses(self):
        self.char1.location = self.room2
        result = self.call(CmdBounty(), "", caller=self.char1)
        self.assertIn("no bounty board here", result)

    def test_bare_bounty_with_none_active_prompts_to_accept(self):
        result = self.call(CmdBounty(), "", caller=self.char1)
        self.assertIn("no active bounty", result)

    @patch("world.bounties.roll_bounty")
    def test_accept_assigns_a_new_bounty(self, mock_roll):
        mock_roll.return_value = {
            "tier": "novice", "target_key": "a Subura footpad",
            "target_display": "Subura footpads", "count_required": 3,
            "count_progress": 0, "xp_reward": 30, "gold_reward": 10,
        }
        result = self.call(CmdBounty(), "accept", caller=self.char1)
        self.assertIn("New bounty", result)
        self.assertIsNotNone(self.char1.db.active_bounty)

    def test_accept_refuses_if_already_have_one(self):
        self.char1.db.active_bounty = {
            "target_key": "x", "target_display": "x",
            "count_required": 1, "count_progress": 0, "xp_reward": 1, "gold_reward": 1,
        }
        result = self.call(CmdBounty(), "accept", caller=self.char1)
        self.assertIn("already have an active bounty", result)

    def test_turnin_refuses_if_incomplete(self):
        self.char1.db.active_bounty = {
            "target_key": "x", "target_display": "footpads",
            "count_required": 3, "count_progress": 1, "xp_reward": 30, "gold_reward": 10,
        }
        result = self.call(CmdBounty(), "turnin", caller=self.char1)
        self.assertIn("haven't finished", result)
        self.assertIsNotNone(self.char1.db.active_bounty)

    def test_turnin_pays_out_and_clears_when_complete(self):
        self.char1.db.gold = 0
        self.char1.db.xp = 0
        self.char1.db.level = 1
        self.char1.db.active_bounty = {
            "target_key": "x", "target_display": "footpads",
            "count_required": 3, "count_progress": 3, "xp_reward": 5, "gold_reward": 10,
        }
        result = self.call(CmdBounty(), "turnin", caller=self.char1)
        self.assertIn("Bounty complete", result)
        self.assertEqual(self.char1.db.gold, 10)
        self.assertEqual(self.char1.db.xp, 5)
        self.assertIsNone(self.char1.db.active_bounty)

    def test_abandon_clears_active_bounty(self):
        self.char1.db.active_bounty = {
            "target_key": "x", "target_display": "footpads",
            "count_required": 3, "count_progress": 1, "xp_reward": 30, "gold_reward": 10,
        }
        result = self.call(CmdBounty(), "abandon", caller=self.char1)
        self.assertIn("abandon", result)
        self.assertIsNone(self.char1.db.active_bounty)


class TestListActiveBounties(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.active_bounty = None
        self.char2.db.active_bounty = None

    def test_empty_state_message(self):
        self.assertIn("No players currently", list_active_bounties())

    def test_shows_a_real_active_bounty(self):
        self.char1.db.active_bounty = {
            "tier": "novice", "target_key": "x", "target_display": "Subura footpads",
            "count_required": 4, "count_progress": 2, "xp_reward": 30, "gold_reward": 10,
        }
        result = list_active_bounties()
        self.assertIn(self.char1.key, result)
        self.assertIn("Subura footpads", result)
        self.assertIn("2/4", result)

    def test_accountless_character_is_excluded(self):
        """
        Same typeclass real players use, but no persistent account
        link (a flavor NPC built with typeclasses.characters.Character,
        as most in this game are) accidentally carrying
        db.active_bounty should never show up here - exercises
        all_player_characters()'s own account filter specifically,
        not just the broader typeclass filter.
        """
        npc = create.create_object(
            "typeclasses.characters.Character", key="a stray npc", location=self.room1
        )
        npc.db.active_bounty = {
            "tier": "novice", "target_key": "x", "target_display": "Subura footpads",
            "count_required": 4, "count_progress": 2, "xp_reward": 30, "gold_reward": 10,
        }
        self.assertIsNone(npc.account)
        result = list_active_bounties()
        self.assertIn("No players currently", result)


class TestBountyCatalog(EvenniaTest):
    def test_includes_every_defined_tier_and_target(self):
        result = bounty_catalog()
        for tier_name in BOUNTY_TIERS:
            self.assertIn(tier_name.capitalize(), result)
        for tier_data in BOUNTY_TIERS.values():
            for _, display_name in tier_data["targets"]:
                self.assertIn(display_name, result)

    def test_a_newly_added_target_appears_with_no_code_changes(self):
        """
        Proves the actual design claim, not just asserts it: adding a
        target to BOUNTY_TIERS at runtime (simulating a future edit to
        the real dict) makes it show up here with zero changes to
        bounty_catalog() itself - it reads the live dict directly.
        """
        fake_target = ({"key": "a brand new menace", "xp_reward": 999}, "brand new menaces")
        BOUNTY_TIERS["novice"]["targets"].append(fake_target)
        try:
            result = bounty_catalog()
            self.assertIn("brand new menaces", result)
        finally:
            BOUNTY_TIERS["novice"]["targets"].remove(fake_target)

    def test_reports_board_location_when_no_board_exists_in_test_db(self):
        result = bounty_catalog()
        self.assertIn("not currently placed", result)


class TestCmdBountyOversight(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.active_bounty = None

    def test_non_god_refused(self):
        self.char1.db.level = 50
        result = self.call(CmdBounty(), "list", caller=self.char1)
        self.assertIn("Only gods", result)

    def test_god_gets_list_even_with_no_board_in_room(self):
        self.char1.db.level = 101
        result = self.call(CmdBounty(), "list", caller=self.char1)
        self.assertIn("No players currently", result)

    def test_god_gets_catalog_even_with_no_board_in_room(self):
        self.char1.db.level = 101
        result = self.call(CmdBounty(), "catalog", caller=self.char1)
        self.assertIn("Novice", result)
