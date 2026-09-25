"""
Tests for eating and drinking (world/food.py) and the eat/drink/use split.

Food and drink carry `db.consume_verb` and go through `eat`/`drink`;
`use` is only for potions, pills, and other usable items. A real gap this
closes: shops sold bread and wine but nothing could be consumed - `use`
refused the unflavored ones ("not a usable item").
"""

from evennia.prototypes.spawner import spawn
from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

import world.prototypes as prototypes
from world.combat import CmdUse
from world.economy import (
    APOTHECARY_STOCK,
    BATHS_VENDOR_STOCK,
    OUTFITTER_STOCK,
    PROVISIONER_STOCK,
    SCRIBE_STOCK,
    WINE_MERCHANT_STOCK,
)
from world.food import CmdDrink, CmdEat


class FoodTestBase(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        # An ordinary player, not the Developer fixture (see the same note
        # in tests_combat_commands - Developer masks name-search bugs).
        self.char1.permissions.remove("Developer")
        self.char1.db.hp = 10
        self.char1.db.max_hp = 100
        self.char1.db.is_dead = False
        self.char1.db.combat_turnhandler = None

    def _give(self, proto_key):
        item = spawn(proto_key)[0]
        item.move_to(self.char1, quiet=True)
        return item


class TestEatAndDrink(FoodTestBase):
    def test_eating_food_heals_and_consumes_it(self):
        pie = self._give("BAKERY_MEAT_PIE")
        result = self.call(CmdEat(), "meat pie", caller=self.char1)
        self.assertGreater(self.char1.db.hp, 10)
        self.assertFalse(pie.pk)
        self.assertIn("eats", result)  # not "uses"

    def test_drinking_wine_heals(self):
        self._give("WINE_SPICED_CUP")
        result = self.call(CmdDrink(), "spiced wine", caller=self.char1)
        self.assertGreater(self.char1.db.hp, 10)
        self.assertIn("drinks", result)

    def test_a_buff_food_applies_its_condition(self):
        self._give("BAKERY_HARD_CHEESE")
        self.call(CmdEat(), "cheese", caller=self.char1)
        self.assertIn("Defense Up", self.char1.db.conditions or {})

    def test_the_four_formerly_flavor_only_items_now_do_something(self):
        for proto, verb_cmd, needle in (
            ("VENDOR_NUTS", CmdEat, "roasted nuts"),
            ("VENDOR_WATERED_WINE", CmdDrink, "watered wine"),
            ("ROASTED_MEAT_SKEWER", CmdEat, "skewer"),
            ("HONEYED_BREAD", CmdEat, "honeyed bread"),
        ):
            self.char1.db.hp, self.char1.db.sp = 10, 5
            item = self._give(proto)
            self.call(verb_cmd(), needle, caller=self.char1)
            self.assertTrue(self.char1.db.hp > 10 or self.char1.db.sp > 5, proto)
            self.assertFalse(item.pk, proto)

    def test_nuts_restore_stamina_not_health(self):
        self.char1.db.sp, self.char1.db.max_sp = 5, 100
        self._give("VENDOR_NUTS")
        result = self.call(CmdEat(), "roasted nuts", caller=self.char1)
        self.assertGreater(self.char1.db.sp, 5)
        self.assertEqual(self.char1.db.hp, 10)
        self.assertIn("SP", result)

    def test_a_food_can_restore_mana(self):
        item = create.create_object("typeclasses.objects.Object", key="a honey cake", location=self.char1)
        item.db.consume_verb = "eat"
        item.db.consume_restore = {"mp": (5, 5)}
        item.db.item_uses = 1
        item.db.item_consumable = True
        self.char1.db.mp, self.char1.db.max_mp = 1, 50
        self.call(CmdEat(), "honey cake", caller=self.char1)
        self.assertEqual(self.char1.db.mp, 6)

    def test_a_multi_serving_drink_lasts_several_sips(self):
        amphora = self._give("WINE_WATERED_AMPHORA")
        self.call(CmdDrink(), "amphora", caller=self.char1)
        self.assertTrue(amphora.pk)
        self.assertEqual(amphora.db.item_uses, 2)

    def test_a_pure_restore_food_is_not_wasted_when_you_are_already_full(self):
        self.char1.db.hp = self.char1.db.max_hp
        pie = self._give("BAKERY_MEAT_PIE")
        result = self.call(CmdEat(), "meat pie", caller=self.char1)
        self.assertIn("no need", result)
        self.assertTrue(pie.pk)

    def test_a_buff_food_is_still_eaten_at_full_strength(self):
        self.char1.db.hp = self.char1.db.max_hp
        cheese = self._give("BAKERY_HARD_CHEESE")
        self.call(CmdEat(), "cheese", caller=self.char1)
        self.assertFalse(cheese.pk)
        self.assertIn("Defense Up", self.char1.db.conditions or {})

    def test_you_cannot_eat_a_drink_or_drink_a_food(self):
        self._give("WINE_SPICED_CUP")
        self._give("BAKERY_BREAD_LOAF")
        self.assertIn("try 'drink", self.call(CmdEat(), "spiced wine", caller=self.char1))
        self.assertIn("try 'eat", self.call(CmdDrink(), "bread", caller=self.char1))

    def test_a_potion_is_not_food(self):
        self._give("HEALTH_POTION")
        result = self.call(CmdEat(), "health potion", caller=self.char1)
        self.assertIn("try 'use", result)

    def test_no_argument_lists_what_you_can_eat(self):
        self._give("BAKERY_BREAD_LOAF")
        self.assertIn("warm loaf of bread", self.call(CmdEat(), "", caller=self.char1))
        self.assertNotIn("warm loaf", self.call(CmdDrink(), "", caller=self.char1))

    def test_nothing_named_is_found(self):
        result = self.call(CmdEat(), "a unicorn steak", caller=self.char1)
        self.assertIn("aren't carrying", result)

    def test_the_dead_do_not_eat(self):
        self._give("BAKERY_BREAD_LOAF")
        self.char1.db.is_dead = True
        self.assertIn("dead", self.call(CmdEat(), "bread", caller=self.char1))


class TestNothingEdibleDoesNothing(FoodTestBase):
    """Owner rule: food must DO SOMETHING. A flagged item with neither a
    restore nor a buff/cure is bad data - it is refused and kept, never
    eaten for no effect."""

    def test_an_item_with_no_effect_is_refused_and_kept(self):
        fig = create.create_object("typeclasses.objects.Object", key="a fig", location=self.char1)
        fig.db.consume_verb = "eat"
        result = self.call(CmdEat(), "fig", caller=self.char1)
        self.assertIn("can't eat that", result)
        self.assertTrue(fig.pk)

    def test_eating_off_your_turn_in_a_fight_is_refused(self):
        from unittest import mock

        pie = self._give("BAKERY_MEAT_PIE")
        with mock.patch("world.combat.COMBAT_RULES.is_in_combat", return_value=True), mock.patch(
            "world.combat.COMBAT_RULES.is_turn", return_value=False
        ):
            result = self.call(CmdEat(), "meat pie", caller=self.char1)
        self.assertIn("your turn", result)
        self.assertTrue(pie.pk)


class TestUseIsOnlyForUsableItems(FoodTestBase):
    def test_use_refuses_food_and_points_to_eat(self):
        bread = self._give("BAKERY_BREAD_LOAF")
        result = self.call(CmdUse(), "bread", caller=self.char1)
        self.assertIn("try 'eat", result)
        self.assertTrue(bread.pk)
        self.assertEqual(self.char1.db.hp, 10)  # nothing was healed

    def test_use_refuses_wine_and_points_to_drink(self):
        self._give("WINE_FALERNIAN")
        self.assertIn("try 'drink", self.call(CmdUse(), "falernian", caller=self.char1))

    def test_use_still_works_for_a_potion(self):
        self._give("HEALTH_POTION")
        self.call(CmdUse(), "health potion", caller=self.char1)
        self.assertGreater(self.char1.db.hp, 10)


class TestEveryFoodShopWareIsFlagged(FoodTestBase):
    """The data check that stops this drifting: anything a food shop
    sells must be eat/drink-able, and nothing a potion shop sells may be."""

    FOOD_PROTOS = {
        "eat": ["VENDOR_NUTS", "ROASTED_MEAT_SKEWER", "HONEYED_BREAD"] + list(PROVISIONER_STOCK),
        "drink": ["VENDOR_WATERED_WINE"] + list(WINE_MERCHANT_STOCK),
    }
    NOT_FOOD_STOCK = (
        list(APOTHECARY_STOCK) + list(BATHS_VENDOR_STOCK)
        + list(OUTFITTER_STOCK) + list(SCRIBE_STOCK)
        + ["CRAFTED_HEALING_TONIC", "CRAFTED_ANTIDOTE"]
    )

    def test_every_food_and_drink_ware_carries_the_right_flag(self):
        for verb, protos in self.FOOD_PROTOS.items():
            for proto in protos:
                self.assertEqual(spawn(proto)[0].db.consume_verb, verb, proto)

    def test_no_potion_or_medicine_is_flagged_as_food(self):
        for proto in self.NOT_FOOD_STOCK:
            self.assertIsNone(spawn(proto)[0].db.consume_verb, proto)

    def test_every_flagged_prototype_is_in_the_lists_above(self):
        # A NEW food prototype added without joining this data check
        # (and so without being verified against its shop) fails here.
        flagged = {
            name for name, p in vars(prototypes).items()
            if isinstance(p, dict) and p.get("consume_verb")
        }
        listed = {p for protos in self.FOOD_PROTOS.values() for p in protos}
        self.assertEqual(flagged, listed)

    def test_every_flagged_prototype_does_something(self):
        # The owner rule as data: a restore of HP/MP/SP, or a buff/cure
        # item_func, or both - never neither.
        from world.combat import ITEMFUNCS

        for name, p in vars(prototypes).items():
            if not (isinstance(p, dict) and p.get("consume_verb")):
                continue
            restore = p.get("consume_restore") or {}
            for stat, (low, high) in restore.items():
                self.assertIn(stat, ("hp", "mp", "sp"), name)
                self.assertTrue(0 < low <= high, name)
            self.assertTrue(restore or p.get("item_func"), "%s does nothing" % name)
            if p.get("item_func"):
                self.assertIn(p["item_func"], ITEMFUNCS, name)

    def test_a_converted_food_does_not_also_keep_the_old_heal(self):
        # Foods that restore via consume_restore must not double-heal
        # through a leftover item_func "heal".
        for name, p in vars(prototypes).items():
            if isinstance(p, dict) and p.get("consume_restore"):
                self.assertNotEqual(p.get("item_func"), "heal", name)

    def test_every_flagged_prototype_names_a_real_verb(self):
        for name, p in vars(prototypes).items():
            if isinstance(p, dict) and p.get("consume_verb"):
                self.assertIn(p["consume_verb"], ("eat", "drink"), name)
