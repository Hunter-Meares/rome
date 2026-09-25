"""
Tests for the early-game achievements and titles (world/achievements.py's
"EARLY-GAME MILESTONES", world/titles.py's ACHIEVEMENT_TITLES) - a quick
run of wins across a new player's first hours, for fighters and pacifist
crafters alike.

tests_achievements.py already proves every one of these has a call site
somewhere (a source scan); these prove the real triggers actually complete
them and grant the right titles. The two road exits, the learn command and
quest turn-in are covered by that scan alone - each needs a great deal of
world setup for one line of hook.
"""

from unittest import mock

from evennia.contrib.game_systems.achievements import achievements as contrib
from evennia.prototypes.spawner import spawn
from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from world.achievements import announce_achievements, track_and_announce
from world.combat import AutoStatNPC, COMBAT_RULES
from world.titles import ACHIEVEMENT_TITLES


def completed(character, key):
    return bool(contrib._read_player_data(character).get(key, {}).get("completed"))


class TestTrackAndAnnounce(EvenniaTest):
    def test_completes_an_achievement_for_a_real_player(self):
        track_and_announce(self.char1, category="sell", tracking="any")
        self.assertTrue(completed(self.char1, "first_sale"))

    def test_skips_an_npc_with_no_account(self):
        npc = create.create_object("typeclasses.characters.Character", key="a bystander")
        self.assertIsNone(npc.account)
        track_and_announce(npc, category="sell", tracking="any")
        self.assertFalse(completed(npc, "first_sale"))

    def test_a_counted_achievement_needs_exactly_its_count(self):
        for _ in range(24):
            track_and_announce(self.char1, category="craft", tracking="any")
        self.assertTrue(completed(self.char1, "first_craft"))
        self.assertFalse(completed(self.char1, "craft_25"))
        track_and_announce(self.char1, category="craft", tracking="any")
        self.assertTrue(completed(self.char1, "craft_25"))

    def test_five_quests_completes_the_reliable_and_the_first_completes_first_quest(self):
        track_and_announce(self.char1, category="quest", tracking="any")
        self.assertTrue(completed(self.char1, "first_quest"))
        self.assertFalse(completed(self.char1, "quests_5"))
        for _ in range(4):
            track_and_announce(self.char1, category="quest", tracking="any")
        self.assertTrue(completed(self.char1, "quests_5"))


class TestTitlesFromMilestones(EvenniaTest):
    def test_every_titled_achievement_really_exists(self):
        from evennia.contrib.game_systems.achievements import get_achievement

        for key in ACHIEVEMENT_TITLES:
            self.assertIsNotNone(get_achievement(key), key)

    def test_the_expected_titles_are_granted(self):
        expected = {
            "first_craft": "the Apprentice",
            "craft_25": "the Craftsman",
            "quests_5": "the Reliable",
            "level_25": "the Veteran",
            "the_long_road": "the Wayfarer",
            "twice_born": "the Twice-Born",
            "the_peaceable": "the Peaceable",
            "iron_will": "the Iron-Willed",
        }
        for key, title in expected.items():
            self.assertEqual(ACHIEVEMENT_TITLES[key], title)
            self.char1.db.earned_titles = []
            announce_achievements(self.char1, [key])
            self.assertIn(title, self.char1.db.earned_titles, key)

    def test_a_milestone_with_no_title_grants_none(self):
        for key in ("first_gather", "first_sale", "first_quest", "level_5", "beyond_the_walls"):
            self.assertNotIn(key, ACHIEVEMENT_TITLES)


class TestRealTriggers(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.level = 1
        self.char1.db.xp = 0

    def test_gathering_completes_fruits_of_the_land(self):
        from world.gathering import CmdGather

        self.room1.db.gather_resource = "timber"
        self.char1.ndb.gather_spot = "timber"
        self.call(CmdGather(), "", caller=self.char1)
        self.assertTrue(completed(self.char1, "first_gather"))

    def test_crafting_completes_apprentices_hands_after_the_success_message(self):
        from world.recipes import IronShortswordRecipe

        self.char1.db.craft_skill = {}
        materials = [spawn(p)[0] for p in ("RAW_IRON_ORE", "RAW_TIMBER")]
        for obj in materials:
            obj.move_to(self.char1, quiet=True)
        forge = spawn("FABER_FORGE")[0]
        forge.location = self.room1
        with mock.patch("world.recipes.randint", return_value=1):
            result = IronShortswordRecipe(self.char1, forge, *materials).craft()
        self.assertTrue(result)
        self.assertTrue(completed(self.char1, "first_craft"))

    def test_a_failed_craft_does_not_count(self):
        from world.recipes import IronShortswordRecipe

        self.char1.db.craft_skill = {}
        materials = [spawn(p)[0] for p in ("RAW_IRON_ORE", "RAW_TIMBER")]
        for obj in materials:
            obj.move_to(self.char1, quiet=True)
        forge = spawn("FABER_FORGE")[0]
        forge.location = self.room1
        with mock.patch("world.recipes.randint", return_value=100):
            IronShortswordRecipe(self.char1, forge, *materials).craft()
        self.assertFalse(completed(self.char1, "first_craft"))

    def test_selling_completes_open_for_business(self):
        from world.economy import NPCMerchant, node_confirm_sell

        merchant = create.create_object(NPCMerchant, key="Vendor", location=self.room1)
        self.char1.ndb.shop_merchant = merchant
        item = spawn("DAGGER")[0]
        item.db.price = 20
        item.move_to(self.char1, quiet=True)
        text, options = node_confirm_sell(self.char1, item=item)
        options[0]["goto"](self.char1)
        self.assertTrue(completed(self.char1, "first_sale"))

    def test_level_milestones_fire_at_5_10_and_25(self):
        for reached, key in ((5, "level_5"), (10, "level_10"), (25, "level_25")):
            self.char1.db.level = reached - 1
            self.char1.db.xp = 0
            COMBAT_RULES.award_xp(self.char1, COMBAT_RULES.xp_for_level(reached - 1))
            self.assertEqual(self.char1.db.level, reached)
            self.assertTrue(completed(self.char1, key), key)

    def test_a_level_between_milestones_completes_nothing_extra(self):
        self.char1.db.level = 6
        self.char1.db.xp = 0
        COMBAT_RULES.award_xp(self.char1, COMBAT_RULES.xp_for_level(6))
        self.assertEqual(self.char1.db.level, 7)
        self.assertFalse(completed(self.char1, "level_10"))

    def test_returning_from_the_dead_completes_twice_born(self):
        self.char1.db.is_dead = True
        self.assertTrue(COMBAT_RULES.resurrect(self.char1))
        self.assertTrue(completed(self.char1, "twice_born"))

    def test_a_party_kill_completes_stronger_together_for_every_contributor(self):
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2]
        self.char2.db.party_leader = self.char1
        self.char1.db.level = self.char2.db.level = 1
        npc = create.create_object(AutoStatNPC, key="dummy", location=self.room1)
        npc.db.hp = 0
        npc.db.xp_reward = 15
        npc.db.damage_log = {self.char1: 80, self.char2: 20}
        COMBAT_RULES.at_defeat(npc, attacker=self.char1)
        self.assertTrue(completed(self.char1, "first_party_kill"))
        self.assertTrue(completed(self.char2, "first_party_kill"))

    def test_two_unpartied_attackers_do_not_earn_it(self):
        self.char1.db.level = self.char2.db.level = 1
        npc = create.create_object(AutoStatNPC, key="dummy", location=self.room1)
        npc.db.hp = 0
        npc.db.xp_reward = 15
        npc.db.damage_log = {self.char1: 80, self.char2: 20}
        COMBAT_RULES.at_defeat(npc, attacker=self.char1)
        self.assertFalse(completed(self.char1, "first_party_kill"))
