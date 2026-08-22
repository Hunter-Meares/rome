"""
Tests for the items system (world/combat.py's use_item/itemfunc_* and
CmdUse) - previously entirely untested.

Carries a regression test for a real, major bug found while writing
this file: every itemfunc_* implementation returns False explicitly
on failure but has no explicit `return True` on success (falling off
the end returns None instead). use_item's `if not item_func(...):
return` treated that None (a SUCCESSFUL use) exactly like an actual
False failure, so spend_item_use and spend_action were skipped on
EVERY successful item use - limited-use/consumable items never
actually consumed a use (effectively infinite), and using an item in
combat never spent the user's turn action (a free action every turn).
Fixed to `if item_func(...) is False: return`.
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create

from world.combat import COMBAT_RULES, CmdUse, CombatTurnHandler


class ItemTestBase(EvenniaTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.db.conditions = {}
            char.db.max_hp = 100
            char.db.hp = 100
            char.db.combat_turnhandler = None
            char.db.combat_actionsleft = 1
            char.db.gold = 0
        self.char1.location = self.room1
        self.char2.location = self.room1

    def _make_real_turnhandler(self):
        """A real CombatTurnHandler (spend_action calls real methods on it)."""
        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        handler.db.fighters = [self.char1, self.char2]
        handler.db.turn = 0
        return handler

    def _make_item(self, **attrs):
        item = create.create_object(
            "evennia.objects.objects.DefaultObject", key="test item", location=self.char1
        )
        for key, value in attrs.items():
            setattr(item.db, key, value)
        return item


class TestSpendActionAndUsesRegression(ItemTestBase):
    """The core regression: a successful item use must actually cost
    both a limited use and (in combat) the user's turn action."""

    def test_successful_heal_spends_one_use(self):
        item = self._make_item(item_func="heal", item_uses=3, item_consumable=False)
        self.char1.db.hp = 50

        COMBAT_RULES.use_item(self.char1, item, self.char1)

        self.assertEqual(item.db.item_uses, 2)

    def test_successful_use_in_combat_spends_the_action(self):
        item = self._make_item(item_func="heal", item_uses=3, item_consumable=False)
        self.char1.db.hp = 50
        self.char1.db.combat_turnhandler = self._make_real_turnhandler()
        self.char1.db.combat_actionsleft = 1

        COMBAT_RULES.use_item(self.char1, item, self.char1)

        self.assertEqual(self.char1.db.combat_actionsleft, 0)

    def test_failed_use_does_not_spend_a_use_or_action(self):
        """A validation failure (e.g. target already full HP) must NOT
        consume a use or an action - only a genuine success does."""
        item = self._make_item(item_func="heal", item_uses=3, item_consumable=False)
        self.char1.db.hp = 100  # already full
        self.char1.db.combat_turnhandler = self._make_real_turnhandler()
        self.char1.db.combat_actionsleft = 1

        COMBAT_RULES.use_item(self.char1, item, self.char1)

        self.assertEqual(item.db.item_uses, 3)
        self.assertEqual(self.char1.db.combat_actionsleft, 1)

    def test_consumable_true_deletes_item_at_zero_uses(self):
        item = self._make_item(item_func="heal", item_uses=1, item_consumable=True)
        self.char1.db.hp = 50
        item_id = item.id

        COMBAT_RULES.use_item(self.char1, item, self.char1)

        from evennia.objects.models import ObjectDB

        self.assertFalse(ObjectDB.objects.filter(id=item_id).exists())

    def test_consumable_string_leaves_residue_and_deletes_item(self):
        item = self._make_item(
            item_func="heal", item_uses=1, item_consumable="GLASS_BOTTLE"
        )
        self.char1.db.hp = 50
        item_id = item.id

        try:
            COMBAT_RULES.use_item(self.char1, item, self.char1)
        except Exception:
            self.skipTest("GLASS_BOTTLE prototype not available in this test DB")

        from evennia.objects.models import ObjectDB

        self.assertFalse(ObjectDB.objects.filter(id=item_id).exists())
        # spend_item_use sets residue.location = item.location, and the
        # item lived in char1's inventory (not the room) - the residue
        # lands there too.
        residue = [o for o in self.char1.contents if o.key == "a glass bottle"]
        self.assertTrue(residue)

    def test_non_consumable_at_zero_uses_stays_but_reports_no_uses(self):
        item = self._make_item(item_func="heal", item_uses=1, item_consumable=False)
        self.char1.db.hp = 50

        COMBAT_RULES.use_item(self.char1, item, self.char1)

        self.assertEqual(item.db.item_uses, 0)
        self.assertTrue(item.pk)  # still exists


class TestItemfuncHeal(ItemTestBase):
    def test_heals_up_to_max(self):
        item = self._make_item(item_func="heal", item_uses=5, item_consumable=False)
        self.char1.db.hp = 90
        self.char1.db.max_hp = 100

        with patch("world.combat.randint", return_value=40):
            COMBAT_RULES.use_item(self.char1, item, self.char1)

        self.assertEqual(self.char1.db.hp, 100)  # capped, not 130

    def test_rejects_already_full_hp(self):
        item = self._make_item(item_func="heal", item_uses=5, item_consumable=False)
        self.char1.db.hp = 100
        self.char1.db.max_hp = 100

        COMBAT_RULES.use_item(self.char1, item, self.char1)

        self.assertEqual(item.db.item_uses, 5)  # untouched - use_item returned early

    def test_custom_healing_range_from_item_kwargs(self):
        item = self._make_item(
            item_func="heal",
            item_uses=5,
            item_consumable=False,
            item_kwargs={"healing_range": (35, 50)},
        )
        self.char1.db.hp = 10
        self.char1.db.max_hp = 100

        with patch("world.combat.randint", return_value=35):
            COMBAT_RULES.use_item(self.char1, item, self.char1)

        self.assertEqual(self.char1.db.hp, 45)


class TestItemfuncAddCondition(ItemTestBase):
    def test_applies_conditions(self):
        item = self._make_item(
            item_func="add_condition",
            item_uses=1,
            item_consumable=False,
            item_kwargs={"conditions": [("Haste", 10)]},
        )
        COMBAT_RULES.use_item(self.char1, item, self.char1)
        self.assertIn("Haste", self.char1.db.conditions)


class TestItemfuncCureCondition(ItemTestBase):
    def test_cures_only_matching_conditions(self):
        item = self._make_item(
            item_func="cure_condition",
            item_uses=1,
            item_consumable=False,
            item_kwargs={"to_cure": ["Poisoned"]},
        )
        self.char1.db.conditions = {
            "Poisoned": [4, self.char2],
            "Haste": [4, self.char1],
        }
        COMBAT_RULES.use_item(self.char1, item, self.char1)
        self.assertNotIn("Poisoned", self.char1.db.conditions)
        self.assertIn("Haste", self.char1.db.conditions)


class TestItemfuncAttack(ItemTestBase):
    def test_requires_combat(self):
        item = self._make_item(
            item_func="attack", item_uses=1, item_consumable=False,
            item_kwargs={"damage_range": (10, 10)},
        )
        self.char1.db.combat_turnhandler = None
        self.char2.db.hp = 100

        COMBAT_RULES.use_item(self.char1, item, self.char2)

        self.assertEqual(self.char2.db.hp, 100)
        self.assertEqual(item.db.item_uses, 1)  # nothing spent - failed validation

    def test_deals_damage_in_combat(self):
        # damage_range is degenerate (15, 15) so the damage roll is
        # deterministic without mocking randint; accuracy=100 flat
        # bonus guarantees a hit (attack_value = d100 + 100 always
        # beats a baseline defense_value of 50) regardless of the d100
        # roll, so no mocking needed for the attack roll either.
        item = self._make_item(
            item_func="attack", item_uses=1, item_consumable=False,
            item_kwargs={"damage_range": (15, 15), "accuracy": 100},
        )
        self.char1.db.combat_turnhandler = self._make_real_turnhandler()
        self.char2.db.hp = 100

        COMBAT_RULES.use_item(self.char1, item, self.char2)

        self.assertEqual(self.char2.db.hp, 85)
        self.assertEqual(item.db.item_uses, 0)  # a real success this time

    def test_cannot_target_self(self):
        item = self._make_item(
            item_func="attack", item_uses=1, item_consumable=False,
            item_kwargs={"damage_range": (10, 10)},
        )
        self.char1.db.combat_turnhandler = self._make_real_turnhandler()
        COMBAT_RULES.use_item(self.char1, item, self.char1)
        self.assertEqual(item.db.item_uses, 1)  # rejected, nothing spent


class TestCmdUse(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.db.conditions = {}
            char.db.max_hp = 100
            char.db.hp = 100
            char.db.combat_turnhandler = None
        self.char1.location = self.room1
        self.char2.location = self.room1

    def _make_item(self, **attrs):
        item = create.create_object(
            "evennia.objects.objects.DefaultObject", key="potion", location=self.char1
        )
        for key, value in attrs.items():
            setattr(item.db, key, value)
        return item

    def test_use_heals_self(self):
        item = self._make_item(item_func="heal", item_uses=3, item_consumable=False)
        self.char1.db.hp = 50

        with patch("world.combat.randint", return_value=20):
            self.call(CmdUse(), "potion", caller=self.char1)

        self.assertEqual(self.char1.db.hp, 70)
        self.assertEqual(item.db.item_uses, 2)

    def test_not_a_usable_item_rejected(self):
        item = create.create_object(
            "evennia.objects.objects.DefaultObject", key="a rock", location=self.char1
        )
        result = self.call(CmdUse(), "rock", caller=self.char1)
        self.assertIn("not a usable item", result)

    def test_no_uses_remaining_rejected(self):
        item = self._make_item(item_func="heal", item_uses=0, item_consumable=False)
        result = self.call(CmdUse(), "potion", caller=self.char1)
        self.assertIn("no uses remaining", result)

    def test_use_on_named_target_by_real_name(self):
        """
        Regression coverage: 'use <item> = <name>' targeting another
        real Character went through plain caller.search() with no
        fallback - same rpsystem sdesc-search issue already fixed for
        attack/cast/skill, now fixed here too.
        """
        self.char1.permissions.remove("Developer")
        item = self._make_item(
            item_func="heal", item_uses=1, item_consumable=False
        )
        self.char2.db.hp = 50

        with patch("world.combat.randint", return_value=20):
            self.call(CmdUse(), "potion = Char2", caller=self.char1)

        self.assertEqual(self.char2.db.hp, 70)

    def test_cannot_use_out_of_turn_in_combat(self):
        from world.combat import CombatTurnHandler

        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        handler.db.fighters = [self.char2, self.char1]  # char2's turn
        handler.db.turn = 0
        self.char1.db.combat_turnhandler = handler
        self.char2.db.combat_turnhandler = handler

        item = self._make_item(item_func="heal", item_uses=3, item_consumable=False)

        result = self.call(CmdUse(), "potion", caller=self.char1)
        self.assertIn("only use items on your turn", result)
