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


class TestDistanceBonusAndCraftXp(EconomyTestBase):
    """
    world/gathering.py + world/recipes.py's crafting economy - no new
    vendor system needed, just db.price/db.craft_xp on the item and
    db.distance_bonus on the merchant, both read by the existing sell
    flow.
    """

    def test_an_ordinary_merchant_has_no_distance_bonus(self):
        self.assertEqual(self.merchant.db.distance_bonus, 1.0)

    def test_distance_bonus_multiplies_the_sell_price(self):
        self.merchant.db.distance_bonus = 1.5
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        self.char1.db.gold = 0

        text, options = node_confirm_sell(self.char1, item=item)
        options[0]["goto"](self.char1)  # "Yes"

        self.assertEqual(self.char1.db.gold, int(40 * SELL_BACK_RATE * 1.5))

    def test_node_sell_shows_the_bonus_when_one_applies(self):
        self.merchant.db.distance_bonus = 1.3
        self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        text, options = node_sell(self.char1)
        self.assertIn("bonus", text.lower())

    def test_node_sell_says_nothing_extra_at_the_baseline(self):
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        text, options = node_sell(self.char1)
        self.assertNotIn("bonus", text.lower())

    def test_selling_a_crafted_good_awards_its_craft_xp(self):
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        item.db.craft_xp = 50
        self.char1.db.level = 50  # high enough this can't trigger a level-up
        self.char1.db.xp = 0

        text, options = node_confirm_sell(self.char1, item=item)
        options[0]["goto"](self.char1)

        self.assertEqual(self.char1.db.xp, 50)

    def test_selling_an_ordinary_bought_item_awards_no_xp(self):
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        self.char1.db.level = 50
        self.char1.db.xp = 0

        text, options = node_confirm_sell(self.char1, item=item)
        options[0]["goto"](self.char1)

        self.assertEqual(self.char1.db.xp, 0)


class TestMerchantSpecialtyBonus(EconomyTestBase):
    """
    Real, direct request: selling to a merchant who actually deals in
    that kind of goods should pay more than an ordinary vendor -
    world/economy.py's SPECIALTY_BONUS, stacking with (not replacing)
    distance_bonus.
    """

    def test_a_weapon_specialist_pays_more_for_a_weapon(self):
        self.merchant.db.buys_specialty = ["weapon"]
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)  # CombatWeapon
        self.char1.db.gold = 0

        text, options = node_confirm_sell(self.char1, item=item)
        options[0]["goto"](self.char1)

        self.assertEqual(self.char1.db.gold, int(40 * SELL_BACK_RATE * 1.2))

    def test_no_bonus_for_a_category_the_merchant_does_not_specialize_in(self):
        self.merchant.db.buys_specialty = ["armor"]  # not weapons
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        self.char1.db.gold = 0

        text, options = node_confirm_sell(self.char1, item=item)
        options[0]["goto"](self.char1)

        self.assertEqual(self.char1.db.gold, int(40 * SELL_BACK_RATE))

    def test_an_armor_specialist_pays_more_for_armor(self):
        self.merchant.db.buys_specialty = ["armor"]
        item = self._spawn_ware(proto_key="CALIGAE_FERRATAE", price=40, location=self.char1)  # CombatArmor
        self.char1.db.gold = 0

        text, options = node_confirm_sell(self.char1, item=item)
        options[0]["goto"](self.char1)

        self.assertEqual(self.char1.db.gold, int(40 * SELL_BACK_RATE * 1.2))

    def test_stacks_multiplicatively_with_the_distance_bonus(self):
        self.merchant.db.buys_specialty = ["weapon"]
        self.merchant.db.distance_bonus = 1.3
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        self.char1.db.gold = 0

        text, options = node_confirm_sell(self.char1, item=item)
        options[0]["goto"](self.char1)

        self.assertEqual(self.char1.db.gold, int(40 * SELL_BACK_RATE * 1.3 * 1.2))

    def test_a_potion_specialist_pays_more_for_a_crafted_potion(self):
        # world/economy.py's SuburaApothecary (Aviola) now specializes
        # in potions - a crafted good's db.item_category ("potion",
        # set by world/recipes.py's HerbalistRecipe) is what this
        # checks, not a typeclass. Deliberately NOT spawned as a DAGGER
        # here - a DAGGER is a real CombatWeapon, and _item_category()
        # checks typeclass first, so it would resolve to "weapon"
        # regardless of any db.item_category set on top; a genuine
        # non-weapon/armor prototype is needed to actually exercise the
        # fallback path this test means to check.
        self.merchant.db.buys_specialty = ["potion"]
        item = self._spawn_ware(proto_key="CRAFTED_HEALING_TONIC", price=40, location=self.char1)
        item.db.item_category = "potion"
        self.char1.db.gold = 0

        text, options = node_confirm_sell(self.char1, item=item)
        options[0]["goto"](self.char1)

        self.assertEqual(self.char1.db.gold, int(40 * SELL_BACK_RATE * 1.2))

    def test_no_specialty_set_at_all_is_a_plain_no_op(self):
        item = self._spawn_ware(proto_key="DAGGER", price=40, location=self.char1)
        self.char1.db.gold = 0

        text, options = node_confirm_sell(self.char1, item=item)
        options[0]["goto"](self.char1)

        self.assertEqual(self.char1.db.gold, int(40 * SELL_BACK_RATE))


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

    def test_stocks_three_tiers_of_ritual_staff(self):
        """
        Real, confirmed live gap this fixes: RITUAL_STAFF (the fixed
        chargen starting weapon for every caster class) never had a
        leveled upgrade anywhere in the game - a real player asked
        directly whether a better weapon existed for their class, and
        the honest answer used to be no. These three tiers give every
        caster class the same real progression every other weapon
        type already has.
        """
        staves = [i for i in self.smith.contents if i.db.weapon_type_name == "ritual staff"]
        self.assertEqual(len(staves), 3)
        staves_by_level = sorted(staves, key=lambda i: i.db.item_level)
        prices = [i.db.price for i in staves_by_level]
        self.assertEqual(prices, sorted(prices))
        self.assertLess(prices[0], prices[-1])
        self.assertEqual(len({i.key for i in staves}), 3)  # distinct names per tier

    def test_stocks_weapons_armor_and_shields(self):
        from world.combat import CombatWeapon, CombatArmor

        weapons = [i for i in self.smith.contents if i.is_typeclass(CombatWeapon, exact=True)]
        armor_and_shields = [
            i for i in self.smith.contents if i.is_typeclass(CombatArmor, exact=True)
        ]
        shields = [i for i in armor_and_shields if i.db.armor_slot == "shield"]
        body_armor = [i for i in armor_and_shields if i.db.armor_slot != "shield"]

        self.assertEqual(len(weapons), 18)  # 6 weapons x 3 tiers (staff added)
        self.assertEqual(len(shields), 9)  # 3 shield categories x 3 tiers
        self.assertEqual(len(body_armor), 9)  # 3 armor categories x 3 tiers


class TestRomeShopsStockThemselves(EvenniaTest):
    """
    The six Rome-proper shops (apothecary, provisioner, baths vendor,
    scribe, wine merchant, Ludus outfitter) all use the same flat-price
    self-stocking pattern as AmberTrader - no weapon/armor stats to
    compute, so these checks are simpler than TestLudusWeaponsmith's:
    every shop stocks exactly its own stock list, and - the actual
    point of this whole build - every single item sold anywhere in
    this batch has a real item_func wired up, not just a price. A shop
    selling something with no item_func would silently violate the
    entire premise this feature was built for ("items sold in the
    shops actually do something and not just favor").
    """

    def setUp(self):
        super().setUp()
        from world.economy import (
            SuburaApothecary, APOTHECARY_STOCK,
            SuburaProvisioner, PROVISIONER_STOCK,
            BathsOilVendor, BATHS_VENDOR_STOCK,
            ForumScribe, SCRIBE_STOCK,
            ForumWineMerchant, WINE_MERCHANT_STOCK,
            LudusOutfitter, OUTFITTER_STOCK,
        )

        self.shops = [
            (SuburaApothecary, APOTHECARY_STOCK, "the herbalist's stall"),
            (SuburaProvisioner, PROVISIONER_STOCK, "the baker's stall"),
            (BathsOilVendor, BATHS_VENDOR_STOCK, "the oil-and-soap vendor's table"),
            (ForumScribe, SCRIBE_STOCK, "the scribe's writing desk"),
            (ForumWineMerchant, WINE_MERCHANT_STOCK, "the wine merchant's stall"),
            (LudusOutfitter, OUTFITTER_STOCK, "the adventuring-supplies stall"),
        ]

    def test_each_shop_stocks_exactly_its_own_stock_list(self):
        for typeclass, stock_list, _ in self.shops:
            merchant = create.create_object(typeclass, key="Vendor", location=self.room1)
            self.assertEqual(
                len(merchant.contents), len(stock_list),
                "%s stocked %d items, expected %d" % (
                    typeclass.__name__, len(merchant.contents), len(stock_list)
                ),
            )

    def test_shopnames_are_set_correctly(self):
        for typeclass, _, expected_name in self.shops:
            merchant = create.create_object(typeclass, key="Vendor", location=self.room1)
            self.assertEqual(merchant.db.shopname, expected_name)

    def test_every_stocked_item_has_a_positive_price(self):
        for typeclass, _, _ in self.shops:
            merchant = create.create_object(typeclass, key="Vendor", location=self.room1)
            for item in merchant.contents:
                self.assertTrue(
                    item.db.price and item.db.price > 0,
                    "%s (%s) has no price" % (item.key, typeclass.__name__),
                )

    def test_every_stocked_item_has_a_real_item_func(self):
        """
        The whole point of this batch, made concrete: every item any of
        these six shops sells must actually do something when used, not
        just be a sellable trinket. Also confirms the item_func string
        on each new prototype is a real key in ITEMFUNCS - a typo here
        would silently make CmdUse's own error message the only sign
        anything was wrong.
        """
        from world.combat import ITEMFUNCS

        for typeclass, _, _ in self.shops:
            merchant = create.create_object(typeclass, key="Vendor", location=self.room1)
            for item in merchant.contents:
                self.assertTrue(
                    item.db.item_func,
                    "%s (%s) has no item_func - sells for gold but does nothing" % (
                        item.key, typeclass.__name__
                    ),
                )
                self.assertIn(
                    item.db.item_func, ITEMFUNCS,
                    "%s's item_func %r isn't a real ITEMFUNCS key" % (
                        item.key, item.db.item_func
                    ),
                )

    def test_ludus_outfitter_reuses_the_generic_consumables_not_new_ones(self):
        # A deliberate design choice, not an oversight - see the
        # OUTFITTER_STOCK comment in world/economy.py.
        from world.economy import OUTFITTER_STOCK

        self.assertEqual(
            set(OUTFITTER_STOCK),
            {
                "MEDKIT", "HEALTH_POTION", "REGEN_POTION", "HASTE_POTION",
                "BOMB", "POISON_DART", "ANTIDOTE_POTION",
            },
        )
