"""
Tests for the shop/economy system (world/economy.py) - previously
entirely untested. Exercises the EvMenu node functions directly (they
are plain functions of (caller, ...) -> (text, options), so they can
be called and asserted on without spinning up a real EvMenu session),
plus CmdShop's merchant-presence gate.
"""

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create
from evennia.prototypes.spawner import spawn

from world.economy import (
    NPCMerchant,
    node_shopfront,
    node_inspect_and_buy,
    node_sell,
    node_confirm_sell,
    SELL_BACK_RATE,
    CmdShop,
)


class EconomyTestBase(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.merchant = create.create_object(NPCMerchant, key="Vendor", location=self.room1)
        self.char1.location = self.room1
        self.char1.db.gold = 0
        self.char1.ndb.shop_merchant = self.merchant

    def _spawn_ware(self, proto_key="DAGGER", price=None, location=None):
        try:
            ware = spawn(proto_key)[0]
        except Exception:
            self.skipTest("%s prototype not available in this test DB" % proto_key)
        ware.move_to(location or self.merchant, quiet=True)
        if price is not None:
            ware.db.price = price
        return ware


class TestNodeShopfront(EconomyTestBase):
    def test_shows_gold_and_wares(self):
        ware = self._spawn_ware(price=25)
        self.char1.db.gold = 100

        text, options = node_shopfront(self.char1)

        self.assertIn("100", text)
        self.assertIn(ware.key, text)
        self.assertIn("25", text)

    def test_empty_shop_shows_nothing_for_sale(self):
        text, options = node_shopfront(self.char1)
        self.assertIn("Nothing for sale", text)


class TestBuying(EconomyTestBase):
    def test_successful_purchase_deducts_gold_and_spawns_a_copy(self):
        ware = self._spawn_ware(proto_key="DAGGER", price=25)
        self.char1.db.gold = 100

        text, options = node_inspect_and_buy(self.char1, ware=ware)
        buy = options[0]["goto"]
        buy(self.char1)

        self.assertEqual(self.char1.db.gold, 75)
        # The original display item is untouched (still in the merchant's
        # inventory) - a fresh copy was spawned for the buyer instead.
        self.assertEqual(ware.location, self.merchant)
        bought = [o for o in self.char1.contents if o.key == ware.key]
        self.assertTrue(bought)

    def test_insufficient_gold_rejected(self):
        ware = self._spawn_ware(proto_key="DAGGER", price=25)
        self.char1.db.gold = 10

        text, options = node_inspect_and_buy(self.char1, ware=ware)
        buy = options[0]["goto"]
        buy(self.char1)

        self.assertEqual(self.char1.db.gold, 10)  # untouched
        self.assertFalse(self.char1.contents)  # nothing bought

    def test_ware_no_longer_available_is_handled_gracefully(self):
        ware = self._spawn_ware(proto_key="DAGGER", price=25)
        text, options = node_inspect_and_buy(self.char1, ware=ware)
        buy = options[0]["goto"]

        ware.delete()  # someone/something removed it before confirming

        result = buy(self.char1)  # should not raise
        self.assertEqual(result, "node_shopfront")

    def test_shop_never_depletes_after_multiple_purchases(self):
        ware = self._spawn_ware(proto_key="DAGGER", price=10)
        self.char1.db.gold = 1000

        text, options = node_inspect_and_buy(self.char1, ware=ware)
        buy = options[0]["goto"]
        for _ in range(5):
            buy(self.char1)

        self.assertTrue(ware.pk)  # the display item is still there
        self.assertEqual(ware.location, self.merchant)
        self.assertEqual(len([o for o in self.char1.contents if o.key == ware.key]), 5)


class TestSelling(EconomyTestBase):
    def test_successful_sell_pays_half_price_and_deletes_item(self):
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        self.char1.db.gold = 0
        item_id = item.id

        text, options = node_confirm_sell(self.char1, item=item)
        confirm = options[0]["goto"]  # "Yes"
        confirm(self.char1)

        self.assertEqual(self.char1.db.gold, int(40 * SELL_BACK_RATE))
        from evennia.objects.models import ObjectDB

        self.assertFalse(ObjectDB.objects.filter(id=item_id).exists())

    def test_declining_sell_keeps_the_item(self):
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        self.char1.db.gold = 0

        text, options = node_confirm_sell(self.char1, item=item)
        decline = options[1]["goto"]  # "No"
        result = decline(self.char1) if callable(decline) else decline

        self.assertEqual(self.char1.db.gold, 0)
        self.assertTrue(item.pk)
        self.assertEqual(item.location, self.char1)

    def test_item_no_longer_owned_is_handled_gracefully(self):
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        text, options = node_confirm_sell(self.char1, item=item)
        confirm = options[0]["goto"]

        item.move_to(self.room1, quiet=True)  # no longer in caller's inventory

        result = confirm(self.char1)
        self.assertEqual(result, "node_shopfront")
        self.assertEqual(self.char1.db.gold, 0)

    def test_node_sell_lists_only_priced_items(self):
        priced = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        unpriced = create.create_object(
            "evennia.objects.objects.DefaultObject", key="a plain rock", location=self.char1
        )

        text, options = node_sell(self.char1)

        # Item names appear in each option's desc (what EvMenu renders
        # as the selectable choice text), not in the node's own text -
        # same pattern node_shopfront's ware-inspect options use.
        descs = " ".join(opt.get("desc", "") for opt in options)
        self.assertIn(priced.key, descs)
        self.assertNotIn("plain rock", descs)


class TestCmdShop(EvenniaCommandTest):
    def test_no_merchant_here_rejects(self):
        result = self.call(CmdShop(), "", caller=self.char1)
        self.assertIn("no merchant here", result)


class TestLudusWeaponsmith(EvenniaTest):
    """
    The weaponsmith stocks herself entirely from at_object_creation
    (see LUDUS_WEAPONSMITH_STOCK) - these tests spawn a real one and
    check what she actually ends up carrying, rather than just
    checking the stock list's own shape.
    """

    def setUp(self):
        super().setUp()
        from world.economy import LudusWeaponsmith, LUDUS_WEAPONSMITH_STOCK

        self.LudusWeaponsmith = LudusWeaponsmith
        self.stock_list = LUDUS_WEAPONSMITH_STOCK
        self.smith = create.create_object(LudusWeaponsmith, key="Smith", location=self.room1)

    def test_stocks_exactly_one_item_per_stock_entry(self):
        self.assertEqual(len(self.smith.contents), len(self.stock_list))

    def test_every_stocked_item_has_a_positive_price(self):
        for item in self.smith.contents:
            self.assertTrue(item.db.price and item.db.price > 0, "%s has no price" % item.key)

    def test_higher_tier_costs_more_than_lower_tier(self):
        # Same weapon (gladius), three tiers - price should strictly
        # increase novice -> veteran -> champion, since price scales
        # with the baked-in level via compute_weapon_stats.
        gladii = [i for i in self.smith.contents if i.db.weapon_type_name == "gladius"]
        gladii_by_level = sorted(gladii, key=lambda i: i.db.item_level)
        prices = [i.db.price for i in gladii_by_level]
        self.assertEqual(prices, sorted(prices))
        self.assertLess(prices[0], prices[-1])

    def test_tiers_of_the_same_item_have_distinct_names(self):
        # The whole point of this shop over a plain level-scaled reskin -
        # each tier must read as a different item, not "Gladius v2".
        gladius_names = {i.key for i in self.smith.contents if i.db.weapon_type_name == "gladius"}
        self.assertEqual(len(gladius_names), 3)

    def test_shopname_set(self):
        self.assertEqual(self.smith.db.shopname, "the weaponsmith's stall")

    def test_stocks_weapons_armor_and_shields(self):
        from world.combat import CombatWeapon, CombatArmor

        weapons = [i for i in self.smith.contents if i.is_typeclass(CombatWeapon, exact=True)]
        armor_and_shields = [
            i for i in self.smith.contents if i.is_typeclass(CombatArmor, exact=True)
        ]
        shields = [i for i in armor_and_shields if i.db.armor_slot == "shield"]
        body_armor = [i for i in armor_and_shields if i.db.armor_slot != "shield"]

        self.assertEqual(len(weapons), 15)  # 5 weapons x 3 tiers
        self.assertEqual(len(shields), 9)  # 3 shield categories x 3 tiers
        self.assertEqual(len(body_armor), 9)  # 3 armor categories x 3 tiers
