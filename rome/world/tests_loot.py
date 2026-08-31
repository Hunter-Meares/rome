"""
Tests for the sewer zone's loot-drop system (world/loot.py) - gated
strictly on the "sewer_npc" tag so existing NPCs (Arena Fighters,
Colosseum trainers) keep their current, untouched drop behavior.
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create

from world.loot import roll_loot_drop, LOOT_DROP_CHANCE


class TestRollLootDrop(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.npc = create.create_object(
            "evennia.objects.objects.DefaultObject", key="a test sewer bandit",
            location=self.room1,
        )
        self.npc.db.level = 10
        self.npc.db.xp_reward = 145
        # EvenniaTest's own fixtures (char1, char2, obj1, obj2) already
        # live in room1 - snapshot what's there before each test acts,
        # rather than asserting an absolute content count.
        self.baseline = set(self.room1.contents)

    def _new_drops(self):
        return [o for o in self.room1.contents if o not in self.baseline]

    def test_untagged_npc_never_drops_loot(self):
        with patch("world.loot.random.randint", return_value=1):
            roll_loot_drop(self.npc)
        self.assertEqual(self._new_drops(), [])

    @patch("world.loot.random.randint")
    def test_tagged_npc_drops_nothing_above_the_chance_threshold(self, mock_randint):
        self.npc.tags.add("sewer_npc", category="npc_role")
        mock_randint.return_value = LOOT_DROP_CHANCE + 1

        roll_loot_drop(self.npc)

        self.assertEqual(self._new_drops(), [])

    @patch("world.loot.random.random")
    @patch("world.loot.random.randint")
    def test_tagged_npc_drops_a_weapon_on_a_successful_roll(self, mock_randint, mock_random):
        self.npc.tags.add("sewer_npc", category="npc_role")
        mock_randint.return_value = 1  # within the drop chance
        mock_random.return_value = 0.1  # < 0.5 -> weapon branch

        roll_loot_drop(self.npc)

        dropped = self._new_drops()
        self.assertEqual(len(dropped), 1)
        self.assertTrue(dropped[0].is_typeclass("world.combat.CombatWeapon", exact=False))
        self.assertEqual(dropped[0].db.item_level, 10)

    @patch("world.loot.random.random")
    @patch("world.loot.random.randint")
    def test_tagged_npc_drops_armor_on_the_other_half_of_the_roll(self, mock_randint, mock_random):
        self.npc.tags.add("sewer_npc", category="npc_role")
        mock_randint.return_value = 1
        mock_random.return_value = 0.9  # >= 0.5 -> armor branch

        roll_loot_drop(self.npc)

        dropped = self._new_drops()
        self.assertEqual(len(dropped), 1)
        self.assertTrue(dropped[0].is_typeclass("world.combat.CombatArmor", exact=False))

    def test_no_location_does_not_crash(self):
        self.npc.tags.add("sewer_npc", category="npc_role")
        self.npc.location = None
        with patch("world.loot.random.randint", return_value=1):
            roll_loot_drop(self.npc)  # should not raise
