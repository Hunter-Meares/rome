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

    text = "|Y%s|n - %d gold\n\n%s" % (ware.key, price, desc)

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
        {"desc": "Buy for %d gold" % price, "goto": _buy},
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

    text = "|wWhat would you like to sell?|n\n(Merchants pay %d%% of an item's value - used goods, not new.)" % int(
        SELL_BACK_RATE * 100
    )
    options = []
    for item in items:
        sell_price = int(item.db.price * SELL_BACK_RATE)
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
    sell_price = int(item.db.price * SELL_BACK_RATE)

    def _sell(caller, raw_string="", **kwargs):
        if not item.pk or item.location != caller:
            caller.msg("You don't have that anymore.")
            return "node_shopfront"
        # Deleted rather than moved into the merchant's own inventory -
        # since stock is now effectively infinite (see _buy above),
        # there's no need to physically store sold-back items, and
        # doing so would create confusing duplicate-looking entries
        # in the shop listing over time as sold goods piled up.
        item.delete()
        caller.db.gold = (caller.db.gold or 0) + sell_price
        caller.msg("|gYou sell %s for %d gold.|n" % (item.key, sell_price))
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