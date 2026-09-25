"""
Economy system - NPC merchants, gold, buying and selling.

Follows Evennia's own official "NPC merchants" tutorial pattern
fairly closely: gold is a simple integer balance (see
CombatCharacter.db.gold in world/combat.py), not individual coin
objects - simpler, and explicitly the pattern the tutorial itself
recommends. A merchant's wares are just whatever's sitting in its own
inventory, browsed through an EvMenu.

Stock is effectively infinite - buying a ware spawns a fresh copy
from its prototype rather than moving/depleting the display item
itself, so a shop can never be emptied out by a handful of players
buying everything available. Selling back to a merchant deletes the
item outright rather than accumulating it in the merchant's own
inventory, for the same reason - there's no need to physically store
sold-back goods once stock isn't tracked by depletion anymore.

Selling back to a merchant pays SELL_BACK_RATE of an item's price -
a standard "depreciated/used" resale rate, not full price, so buying
and immediately reselling isn't a way to generate free gold.
"""

from evennia import Command, CmdSet, DefaultCharacter
from evennia.utils.evmenu import EvMenu
from evennia.prototypes.spawner import spawn
from evennia.prototypes.prototypes import PROTOTYPE_TAG_CATEGORY

SELL_BACK_RATE = 0.5

# Real, direct request: selling to a merchant who actually deals in
# that kind of goods should pay more than an ordinary generic vendor -
# a real reason to seek out the right merchant, stacking with (not
# replacing) the distance bonus below.
SPECIALTY_BONUS = 0.2


def _item_category(item):
    """
    "weapon"/"armor"/None - checked by real typeclass first (so this
    applies to every weapon/armor already in the game, not just
    crafted goods), falling back to a plain db.item_category Attribute
    for anything that isn't a CombatWeapon/CombatArmor but still wants
    to participate (a future non-weapon craft, say).
    """
    from world.combat import CombatWeapon, CombatArmor

    if item.is_typeclass(CombatWeapon, exact=False):
        return "weapon"
    if item.is_typeclass(CombatArmor, exact=False):
        return "armor"
    return item.db.item_category


def _specialty_multiplier(merchant, item):
    """1 + SPECIALTY_BONUS if this merchant specializes in this item's
    category, else 1.0 (a no-op multiplier)."""
    specialties = merchant.db.buys_specialty or []
    if _item_category(item) in specialties:
        return 1.0 + SPECIALTY_BONUS
    return 1.0


class NPCMerchant(DefaultCharacter):
    """
    An NPC that runs a shop. Its wares are simply its own inventory -
    whatever objects are sitting in this NPC's contents when a player
    opens the shop are what's listed for sale. Set db.shopname for a
    custom display name; defaults to "the shop" if unset.

    Stock is effectively infinite - each ware here is a display item
    only, never actually handed over. Buying spawns a fresh copy from
    the ware's own prototype instead (see _buy in node_inspect_and_buy
    below), so the shop's listing never depletes no matter how many
    players buy from it.

    Deliberately plain DefaultCharacter, not HostileNPC/CombatCharacter
    - a merchant has no reason to have combat stats or fight back,
    matching the same "flavor NPCs don't need combat typeclasses"
    principle already used for Milo, Titus, the Herald, and the
    wandering spectators.
    """

    def at_object_creation(self):
        self.db.shopname = self.db.shopname or "the shop"
        self.locks.add("puppet:false()")
        # A generic-goods sell-back bonus for how far this merchant is
        # from Rome (world/gathering.py's crafting/gathering economy -
        # a player can carry a gathered/crafted good home and sell for
        # the baseline, or sell it further out for more, a real
        # tradeoff rather than a flat rate everywhere). Defaults to
        # 1.0 (no bonus) for every ordinary Rome merchant; only
        # overridden by subclasses genuinely far from the city.
        self.db.distance_bonus = self.db.distance_bonus or 1.0

    def buy_pitch(self, ware):
        """
        An optional in-character line shown on a ware's inspect screen
        (node_inspect_and_buy) before the player commits to buying it,
        or None for no line at all (the default, every ordinary
        merchant). A method rather than a db attribute on purpose: a
        db default set in at_object_creation never reaches a merchant
        that already exists live (CLAUDE.md gotcha #20), but a class
        method takes effect on every instance the moment it's reloaded.
        """
        return None


# Three tiers (prototype_key, level) per weapon/armor/shield the Ludus
# weaponsmith stocks - see the matching SMITH_* prototypes and their
# design-comment block in world/prototypes.py for why each tier has its
# own name/flavor rather than being the same item with bigger numbers.
# Levels (2/6/10) roughly match the Ludus's own tier bands (recruit/
# weapons-master/beast-handler/champion training rooms).
LUDUS_WEAPONSMITH_STOCK = [
    ("SMITH_DAGGER_NOVICE", 2),
    ("SMITH_DAGGER_VETERAN", 6),
    ("SMITH_DAGGER_CHAMPION", 10),
    ("SMITH_GLADIUS_NOVICE", 2),
    ("SMITH_GLADIUS_VETERAN", 6),
    ("SMITH_GLADIUS_CHAMPION", 10),
    ("SMITH_SPEAR_NOVICE", 2),
    ("SMITH_SPEAR_VETERAN", 6),
    ("SMITH_SPEAR_CHAMPION", 10),
    ("SMITH_SHORTBOW_NOVICE", 2),
    ("SMITH_SHORTBOW_VETERAN", 6),
    ("SMITH_SHORTBOW_CHAMPION", 10),
    ("SMITH_WARAXE_NOVICE", 2),
    ("SMITH_WARAXE_VETERAN", 6),
    ("SMITH_WARAXE_CHAMPION", 10),
    ("SMITH_STAFF_NOVICE", 2),
    ("SMITH_STAFF_VETERAN", 6),
    ("SMITH_STAFF_CHAMPION", 10),
    ("SMITH_LEATHER_NOVICE", 2),
    ("SMITH_LEATHER_VETERAN", 6),
    ("SMITH_LEATHER_CHAMPION", 10),
    ("SMITH_SCALE_NOVICE", 2),
    ("SMITH_SCALE_VETERAN", 6),
    ("SMITH_SCALE_CHAMPION", 10),
    ("SMITH_PLATE_NOVICE", 2),
    ("SMITH_PLATE_VETERAN", 6),
    ("SMITH_PLATE_CHAMPION", 10),
    ("SMITH_PARMA_NOVICE", 2),
    ("SMITH_PARMA_VETERAN", 6),
    ("SMITH_PARMA_CHAMPION", 10),
    ("SMITH_CLIPEUS_NOVICE", 2),
    ("SMITH_CLIPEUS_VETERAN", 6),
    ("SMITH_CLIPEUS_CHAMPION", 10),
    ("SMITH_SCUTUM_NOVICE", 2),
    ("SMITH_SCUTUM_VETERAN", 6),
    ("SMITH_SCUTUM_CHAMPION", 10),
]


class LudusWeaponsmith(NPCMerchant):
    """
    The Ludus weaponsmith - stocks herself automatically on creation
    from LUDUS_WEAPONSMITH_STOCK, so spawning her once (or respawning
    her after any wipe) always produces a complete, correctly-priced
    shop with no separate build-script step to remember or keep in
    sync. Uses world.combat's level-scaled weapon/armor formula (the
    same one chargen's starting gear uses) rather than hand-authored
    prices/stats, so her prices/power automatically stay consistent
    with the rest of the game if that formula is ever retuned.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the weaponsmith's stall"
        self.db.buys_specialty = ["weapon", "armor"]

        from world.combat import compute_weapon_stats, compute_armor_stats

        for prototype_key, level in LUDUS_WEAPONSMITH_STOCK:
            obj = spawn(prototype_key)[0]
            if obj.is_typeclass("world.combat.CombatWeapon", exact=True):
                damage_range, accuracy_bonus, price = compute_weapon_stats(
                    obj.db.weapon_type_name, level
                )
                obj.db.damage_range = damage_range
                obj.db.accuracy_bonus = accuracy_bonus
                obj.db.price = price
                obj.db.item_level = level
            elif obj.is_typeclass("world.combat.CombatArmor", exact=True):
                reduction, defense_modifier, price = compute_armor_stats(
                    obj.db.armor_category, level
                )
                obj.db.damage_reduction = reduction
                obj.db.defense_modifier = defense_modifier
                obj.db.price = price
                obj.db.item_level = level
            obj.move_to(self, quiet=True)


# Three tiers (prototype_key, level) per weapon/armor - mirrors
# LUDUS_WEAPONSMITH_STOCK's own 3-tier shape, scaled to this zone's
# own 25-45 level range instead of the Ludus's 2/6/10. Genuinely
# Germanic-named gear (seax, angon, francisca, waraxe, lamellar,
# mail), not reskinned Roman items - see world/prototypes.py's
# GERMANIA_* entries for the design note on why the balance lookup
# (weapon_type_name/armor_category) is reused wholesale while the
# display name is entirely separate.
GERMANIA_WEAPONSMITH_STOCK = [
    ("GERMANIA_SEAX_NOVICE", 25),
    ("GERMANIA_SEAX_VETERAN", 35),
    ("GERMANIA_SEAX_CHAMPION", 45),
    ("GERMANIA_ANGON_NOVICE", 25),
    ("GERMANIA_ANGON_VETERAN", 35),
    ("GERMANIA_ANGON_CHAMPION", 45),
    ("GERMANIA_FRANCISCA_NOVICE", 25),
    ("GERMANIA_FRANCISCA_VETERAN", 35),
    ("GERMANIA_FRANCISCA_CHAMPION", 45),
    ("GERMANIA_WARAXE_NOVICE", 25),
    ("GERMANIA_WARAXE_VETERAN", 35),
    ("GERMANIA_WARAXE_CHAMPION", 45),
    ("GERMANIA_LAMELLAR_NOVICE", 25),
    ("GERMANIA_LAMELLAR_VETERAN", 35),
    ("GERMANIA_LAMELLAR_CHAMPION", 45),
    ("GERMANIA_MAIL_NOVICE", 25),
    ("GERMANIA_MAIL_VETERAN", 35),
    ("GERMANIA_MAIL_CHAMPION", 45),
]


class GermanicWeaponsmith(NPCMerchant):
    """
    The Germanic Stronghold's own weaponsmith - same self-stocking
    pattern as LudusWeaponsmith above (same level-scaled formula, same
    automatic price/power consistency), just genuinely Germanic gear
    instead of Roman, per direct request.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the Germanic weaponsmith's stall"
        # Genuinely far from Rome - a real reason to sell a gathered/
        # crafted good here rather than lugging it all the way home.
        self.db.distance_bonus = 1.3
        self.db.buys_specialty = ["weapon", "armor"]

        from world.combat import compute_weapon_stats, compute_armor_stats

        for prototype_key, level in GERMANIA_WEAPONSMITH_STOCK:
            obj = spawn(prototype_key)[0]
            if obj.is_typeclass("world.combat.CombatWeapon", exact=True):
                damage_range, accuracy_bonus, price = compute_weapon_stats(
                    obj.db.weapon_type_name, level
                )
                obj.db.damage_range = damage_range
                obj.db.accuracy_bonus = accuracy_bonus
                obj.db.price = price
                obj.db.item_level = level
            elif obj.is_typeclass("world.combat.CombatArmor", exact=True):
                reduction, defense_modifier, price = compute_armor_stats(
                    obj.db.armor_category, level
                )
                obj.db.damage_reduction = reduction
                obj.db.defense_modifier = defense_modifier
                obj.db.price = price
                obj.db.item_level = level
            obj.move_to(self, quiet=True)


# The Amber Coast's own Smith's Quarter Armory stock - three tiers
# (46/58/70) across three weapon types and three armor categories,
# genuinely distinct flavor from the Germanic Stronghold's own
# weaponsmith (see world/prototypes.py's AC_SMITH_* comment for why a
# second "Germanic" vendor selling identical-flavored gear would read
# as repetitive).
AMBER_COAST_ARMORY_STOCK = [
    ("AC_SMITH_DIRK_NOVICE", 46),
    ("AC_SMITH_DIRK_VETERAN", 58),
    ("AC_SMITH_DIRK_CHAMPION", 70),
    ("AC_SMITH_GAFFSPEAR_NOVICE", 46),
    ("AC_SMITH_GAFFSPEAR_VETERAN", 58),
    ("AC_SMITH_GAFFSPEAR_CHAMPION", 70),
    ("AC_SMITH_TIDEAXE_NOVICE", 46),
    ("AC_SMITH_TIDEAXE_VETERAN", 58),
    ("AC_SMITH_TIDEAXE_CHAMPION", 70),
    ("AC_SMITH_SEALSKIN_NOVICE", 46),
    ("AC_SMITH_SEALSKIN_VETERAN", 58),
    ("AC_SMITH_SEALSKIN_CHAMPION", 70),
    ("AC_SMITH_FISHMAIL_NOVICE", 46),
    ("AC_SMITH_FISHMAIL_VETERAN", 58),
    ("AC_SMITH_FISHMAIL_CHAMPION", 70),
    ("AC_SMITH_WHALEBONE_NOVICE", 46),
    ("AC_SMITH_WHALEBONE_VETERAN", 58),
    ("AC_SMITH_WHALEBONE_CHAMPION", 70),
]


class AmberCoastArmorer(NPCMerchant):
    """
    The Amber Coast's Smith's Quarter Armory - same self-stocking
    pattern as GermanicWeaponsmith/LudusWeaponsmith above (same
    level-scaled formula, same automatic price/power consistency),
    with the Trading Quarter's own coastal/amber flavor instead of
    the interior Stronghold's plain forged-iron gear.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the Smith's Quarter Armory"
        # Further still than the Germanic Stronghold.
        self.db.distance_bonus = 1.6
        self.db.buys_specialty = ["weapon", "armor"]

        from world.combat import compute_weapon_stats, compute_armor_stats

        for prototype_key, level in AMBER_COAST_ARMORY_STOCK:
            obj = spawn(prototype_key)[0]
            if obj.is_typeclass("world.combat.CombatWeapon", exact=True):
                damage_range, accuracy_bonus, price = compute_weapon_stats(
                    obj.db.weapon_type_name, level
                )
                obj.db.damage_range = damage_range
                obj.db.accuracy_bonus = accuracy_bonus
                obj.db.price = price
                obj.db.item_level = level
            elif obj.is_typeclass("world.combat.CombatArmor", exact=True):
                reduction, defense_modifier, price = compute_armor_stats(
                    obj.db.armor_category, level
                )
                obj.db.damage_reduction = reduction
                obj.db.defense_modifier = defense_modifier
                obj.db.price = price
                obj.db.item_level = level
            obj.move_to(self, quiet=True)


# The Amber Trader's stock - a pure flavor-goods vendor (no weapon/
# armor mechanics), same shape as the Forum's goldsmith/perfumer.
AMBER_TRADER_STOCK = [
    "AC_AMBER_PENDANT", "AC_AMBER_BEAD_BRACELET",
    "AC_AMBER_CARVED_FIGURE", "AC_AMBER_RAW_CHUNK",
]


class AmberTrader(NPCMerchant):
    """
    The Amber Coast's Amber Trader - a pure flavor-goods vendor
    (amber jewelry and curios), same shape as the Forum's goldsmith/
    perfumer rather than GermanicWeaponsmith's level-scaled pattern -
    these wares have a flat price, no weapon/armor stats to compute.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the Amber Trader's stall"
        self.db.distance_bonus = 1.6

        for prototype_key in AMBER_TRADER_STOCK:
            obj = spawn(prototype_key)[0]
            obj.move_to(self, quiet=True)


# ----------------------------------------------------------------------------
# ROME-PROPER SHOPS - six real merchants, each stocked with items that
# have a genuine mechanical effect via item_func (world/combat.py's
# ITEMFUNCS) rather than being flavor-only, closing a real gap: the
# item-use system (CmdUse, ITEMFUNCS, the MEDKIT/HEALTH_POTION/etc.
# prototypes) was already fully built with nothing anywhere selling or
# dropping any of it. All six use the same flat-price stocking pattern
# as AmberTrader above (no weapon/armor stats to compute) - just spawn
# each prototype and move it into the merchant's own inventory.
# ----------------------------------------------------------------------------

APOTHECARY_STOCK = [
    "HERB_FEVERFEW_BUNDLE", "HERB_COMFREY_POULTICE",
    "HERB_WILLOWBARK_TINCTURE", "HERB_YARROW_SPRIG",
]


class SuburaApothecary(NPCMerchant):
    """
    A working-class herbalist's stall at Market Row - Back Stalls (the
    Subura) - cheap cures and small heals, deliberately more modest
    than the Ludus outfitter's stronger alchemical potions.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the herbalist's stall"
        self.db.buys_specialty = ["potion"]

        for prototype_key in APOTHECARY_STOCK:
            obj = spawn(prototype_key)[0]
            obj.move_to(self, quiet=True)


PROVISIONER_STOCK = [
    "BAKERY_BREAD_LOAF", "BAKERY_HARD_CHEESE",
    "BAKERY_SPICED_NUTS", "BAKERY_MEAT_PIE",
]


class SuburaProvisioner(NPCMerchant):
    """
    A baker/general provisioner's stall at Market Row - The Stalls (the
    Subura) - real food with a real, modest buff or heal, not flavor
    bread.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the baker's stall"

        for prototype_key in PROVISIONER_STOCK:
            obj = spawn(prototype_key)[0]
            obj.move_to(self, quiet=True)


BATHS_VENDOR_STOCK = [
    "BATHS_SCENTED_OIL", "BATHS_BAIAE_SOAP",
    "BATHS_BRONZE_STRIGIL", "BATHS_ROSE_BALM",
]


class BathsOilVendor(NPCMerchant):
    """
    An oil-and-soap vendor at the Baths' Apodyterium - bathing goods
    with a real cleansing/refreshing theme (soap cures a curse, oil and
    balm leave you quicker or steadily mending).
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the oil-and-soap vendor's table"

        for prototype_key in BATHS_VENDOR_STOCK:
            obj = spawn(prototype_key)[0]
            obj.move_to(self, quiet=True)


SCRIBE_STOCK = [
    "SCRIBE_INK_VIAL", "SCRIBE_PROTECTION_SCROLL",
    "SCRIBE_SWIFT_SCROLL", "SCRIBE_MEMORY_TONIC",
]


class ForumScribe(NPCMerchant):
    """
    A hired scribe at "Scribes and Notaries for Hire" (the Forum) -
    that room's own description already implied scribes working there
    with no NPC actually present; this fills that gap. Ink, scrolls,
    and tonics, each with a real buff or cure.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the scribe's writing desk"

        for prototype_key in SCRIBE_STOCK:
            obj = spawn(prototype_key)[0]
            obj.move_to(self, quiet=True)


TAILOR_STOCK = ["PLAIN_ROBE", "SIMPLE_TUNIC"]


class ForumTailor(NPCMerchant):
    """
    A tailor at "Cloth Merchants and Tailors" (the Forum) - same gap
    as ForumScribe above (that room's own description already implied
    a tailor working there, with none ever actually placed). Direct,
    practical purpose: world/combat.py's _try_don_armor now refuses
    real body armor/shields (nonzero damage_reduction/defense_modifier)
    for a pacifist, so this is where one buys something to actually
    wear instead - purely cosmetic body-slot clothing (world/
    prototypes.py's PLAIN_ROBE/SIMPLE_TUNIC), zero protection, zero
    proficiency gating.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the tailor's counter"

        for prototype_key in TAILOR_STOCK:
            obj = spawn(prototype_key)[0]
            obj.move_to(self, quiet=True)

    def buy_pitch(self, ware):
        # Everything she stocks is purely cosmetic (see TAILOR_STOCK),
        # so a player should hear that in her own voice before paying,
        # rather than discover it in a fight - or, for a pacifist who
        # bought it as their only wearable body item, never notice at all.
        return (
            '|w%s|n says, "My clothing won\'t turn a blade - it offers no '
            'protection in a fight at all - but it sure is beautiful! Are '
            'you certain you want it?"' % self.key
        )


WINE_MERCHANT_STOCK = [
    "WINE_SPICED_CUP", "WINE_FALERNIAN",
    "WINE_WATERED_AMPHORA", "WINE_FORTIFIED_FLASK",
]


class ForumWineMerchant(NPCMerchant):
    """
    A wine merchant at the Merchants' Fountain Plaza (the Forum) - wine
    as warmth, courage, and a bit of aggression, each with a real heal,
    buff, or cure rather than being purely a drink.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the wine merchant's stall"

        for prototype_key in WINE_MERCHANT_STOCK:
            obj = spawn(prototype_key)[0]
            obj.move_to(self, quiet=True)


# Reuses the pre-existing MEDKIT/HEALTH_POTION/REGEN_POTION/HASTE_
# POTION/BOMB/POISON_DART/ANTIDOTE_POTION prototypes as-is (see their
# own comment in world/prototypes.py) rather than inventing new items -
# these already had a complete item_func wired up, just no price and
# nowhere selling them.
OUTFITTER_STOCK = [
    "MEDKIT", "HEALTH_POTION", "REGEN_POTION", "HASTE_POTION",
    "BOMB", "POISON_DART", "ANTIDOTE_POTION",
]


class LudusOutfitter(NPCMerchant):
    """
    A general adventuring-supplies stall at the Ludus Entrance -
    everything a fresh Colosseum escapee needs before heading out:
    healing, a couple of buffs, a cure, and two combat-use throwables.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.shopname = "the adventuring-supplies stall"

        for prototype_key in OUTFITTER_STOCK:
            obj = spawn(prototype_key)[0]
            obj.move_to(self, quiet=True)


def _sellable_wares(merchant):
    """Every item in the merchant's inventory with a price set."""
    return [obj for obj in merchant.contents if obj.db.price]


def _sellable_inventory(shopper):
    """Every item the player is carrying with a price set - what the merchant would actually buy back."""
    return [obj for obj in shopper.contents if obj.db.price]


def node_shopfront(caller, raw_string="", **kwargs):
    """The shop's main menu - browse wares, or sell something of your own."""
    merchant = caller.ndb.shop_merchant
    shopname = merchant.db.shopname or "the shop"
    gold = caller.db.gold or 0

    wares = _sellable_wares(merchant)

    text = "|Y%s|n\n\n|wYour gold:|n %d\n" % (shopname, gold)
    if wares:
        text += "\n|wFor sale:|n\n"
        for ware in wares:
            text += "  %s - |Y%d gold|n\n" % (ware.key, ware.db.price)
    else:
        text += "\n(Nothing for sale right now.)\n"

    options = []
    for ware in wares:
        options.append(
            {
                "desc": "Inspect %s (%d gold)" % (ware.key, ware.db.price),
                "goto": ("node_inspect_and_buy", {"ware": ware}),
            }
        )
    options.append({"desc": "Sell an item", "goto": "node_sell"})
    options.append({"key": ("Leave", "quit", "q"), "desc": "Leave the shop", "goto": "node_end"})

    return text, options


def node_inspect_and_buy(caller, raw_string="", **kwargs):
    """Shows a single ware's details and offers to buy it."""
    ware = kwargs.get("ware")
    if not ware or not ware.pk:
        caller.msg("That's no longer available.")
        return "node_shopfront"

    merchant = caller.ndb.shop_merchant
    price = ware.db.price or 0
    desc = ware.db.desc or "No description available."

    from world.religion import religion_bonus
    discount = religion_bonus(caller, "mercury", "shop_discount")
    if discount:
        price = int(price * (1 - discount))

    text = "|Y%s|n - %d gold\n\n%s" % (ware.key, price, desc)

    # An in-character heads-up before committing (see NPCMerchant.
    # buy_pitch) - this screen is already the "are you sure" step, so
    # the Buy option below just gets relabeled rather than adding a
    # separate typed confirm on top of it.
    pitch = merchant.buy_pitch(ware) if merchant else None
    if pitch:
        text += "\n\n" + pitch

    def _buy(caller, raw_string="", **kwargs):
        gold = caller.db.gold or 0
        if gold < price:
            caller.msg("|rYou can't afford that - you have %d gold, it costs %d.|n" % (gold, price))
            return "node_shopfront"
        if not ware.pk or ware.location != merchant:
            caller.msg("That's no longer available.")
            return "node_shopfront"

        # Spawns a fresh copy for the buyer rather than moving the
        # display item itself - the merchant's stock never depletes,
        # which matters given a small handful of players could
        # otherwise empty a shop entirely. Falls back to moving the
        # original directly only if this ware somehow wasn't
        # prototype-spawned in the first place (no prototype_key to
        # spawn a fresh copy from) - an edge case, not the normal path.
        #
        # NOTE: a spawned object's prototype key is NOT stored as a
        # plain `.db.prototype_key` Attribute - Evennia's spawner only
        # records it as a Tag (category=PROTOTYPE_TAG_CATEGORY, i.e.
        # "from_prototype"). Reading `ware.db.prototype_key` was
        # always None for every real, prototype-spawned ware, so this
        # branch was silently unreachable in practice - EVERY purchase
        # was falling through to the "else" branch below and handing
        # over the actual display item, the exact "shop can run dry"
        # bug this whole design was meant to prevent.
        proto_key = ware.tags.get(category=PROTOTYPE_TAG_CATEGORY)
        if proto_key:
            new_item = spawn(proto_key)[0]
            new_item.move_to(caller, quiet=True)
        else:
            ware.move_to(caller, quiet=True)

        caller.db.gold = gold - price
        from world.religion import credit_mercury_trade
        credit_mercury_trade(caller)
        caller.msg("|gYou buy %s for %d gold.|n" % (ware.key, price))
        from evennia.contrib.game_systems.achievements import track_achievements
        from world.achievements import announce_achievements
        completed = track_achievements(caller, category="buy", tracking="any")
        announce_achievements(caller, completed)
        merchant.location.msg_contents(
            "%s buys %s from %s." % (caller, ware.key, merchant),
            exclude=caller,
        )
        return "node_shopfront"

    options = [
        {"desc": ("Buy anyway for %d gold" if pitch else "Buy for %d gold") % price, "goto": _buy},
        {"desc": "Back", "goto": "node_shopfront"},
    ]
    return text, options


def node_sell(caller, raw_string="", **kwargs):
    """Lists the player's own sellable items."""
    merchant = caller.ndb.shop_merchant
    items = _sellable_inventory(caller)

    if not items:
        text = "You don't have anything worth selling."
        options = [{"key": ("Back", "_default"), "goto": "node_shopfront"}]
        return text, options

    distance_bonus = merchant.db.distance_bonus or 1.0
    text = "|wWhat would you like to sell?|n\n(Merchants pay %d%% of an item's value - used goods, not new.)" % int(
        SELL_BACK_RATE * 100
    )
    if distance_bonus > 1.0:
        text += " |y(A %d%% bonus here, this far from Rome.)|n" % round((distance_bonus - 1.0) * 100)
    options = []
    for item in items:
        sell_price = int(item.db.price * SELL_BACK_RATE * distance_bonus * _specialty_multiplier(merchant, item))
        options.append(
            {
                "desc": "%s (%d gold)" % (item.key, sell_price),
                "goto": ("node_confirm_sell", {"item": item}),
            }
        )
    options.append({"key": ("Back", "_default"), "goto": "node_shopfront"})
    return text, options


def node_confirm_sell(caller, raw_string="", **kwargs):
    """Confirms selling a single item back to the merchant."""
    item = kwargs.get("item")
    if not item or not item.pk or item.location != caller:
        caller.msg("You don't have that anymore.")
        return "node_shopfront"

    merchant = caller.ndb.shop_merchant
    distance_bonus = merchant.db.distance_bonus or 1.0
    specialty_multiplier = _specialty_multiplier(merchant, item)
    sell_price = int(item.db.price * SELL_BACK_RATE * distance_bonus * specialty_multiplier)

    def _sell(caller, raw_string="", **kwargs):
        if not item.pk or item.location != caller:
            caller.msg("You don't have that anymore.")
            return "node_shopfront"
        # A gathered/crafted good (world/gathering.py, world/recipes.py)
        # carries its own db.craft_xp, baked in at spawn time - an
        # ordinary shop-bought item never has this set, so reselling
        # something you just bought can never farm XP this way. Paid
        # here rather than on gathering/crafting itself, matching the
        # design's own "the reward is at the sell step" shape.
        if item.db.craft_xp:
            from world.combat import COMBAT_RULES
            COMBAT_RULES.award_xp(caller, item.db.craft_xp)
        # Deleted rather than moved into the merchant's own inventory -
        # since stock is now effectively infinite (see _buy above),
        # there's no need to physically store sold-back items, and
        # doing so would create confusing duplicate-looking entries
        # in the shop listing over time as sold goods piled up.
        item.delete()
        caller.db.gold = (caller.db.gold or 0) + sell_price
        from world.religion import credit_mercury_trade
        credit_mercury_trade(caller)
        caller.msg("|gYou sell %s for %d gold.|n" % (item.key, sell_price))
        from world.achievements import track_and_announce

        track_and_announce(caller, category="sell", tracking="any")
        return "node_shopfront"

    text = "Sell %s for %d gold?" % (item.key, sell_price)
    options = [
        {"key": ("Yes", "y"), "goto": _sell},
        {"key": ("No", "n"), "goto": "node_sell"},
    ]
    return text, options


def node_end(caller, raw_string="", **kwargs):
    """Closing node - just ends the menu."""
    caller.msg("You step away from the shop.")
    del caller.ndb.shop_merchant
    return "", None


class CmdShop(Command):
    """
    Open a merchant's shop to buy or sell goods.

    Usage:
      shop

    Use this while standing in the same room as a merchant. You'll
    see everything they have for sale and can buy anything you can
    afford - merchants never run out of stock, no matter how many
    people buy from them. You can also sell items of your own back
    to them, for half of what they'd normally cost new - a real
    "used goods" price, not full value.

    See 'help gold' for how to actually earn money to spend here.
    """

    key = "shop"
    aliases = ["buy"]
    help_category = "general"

    def func(self):
        caller = self.caller
        merchants = [obj for obj in caller.location.contents if obj.is_typeclass(NPCMerchant, exact=False)]
        if not merchants:
            caller.msg("There's no merchant here to trade with.")
            return

        merchant = merchants[0]
        caller.ndb.shop_merchant = merchant
        EvMenu(
            caller,
            "world.economy",
            startnode="node_shopfront",
        )


class EconomyCmdSet(CmdSet):
    key = "Economy CmdSet"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdShop())