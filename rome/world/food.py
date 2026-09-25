"""
Eating and drinking.

Food and drink are ordinary items flagged with `db.consume_verb` ("eat" or
"drink" - set on the prototype, see world/prototypes.py) and routed through
these two commands instead of `use`, which is reserved for potions, pills,
and other usable items (world/combat.py's CmdUse refuses anything flagged
this way and points the player here).

OWNER RULE: nothing edible may do nothing - food must do SOMETHING, even if
it's only a buff. Every food and drink either restores HP, MP or SP
(`db.consume_restore`: {"hp": (min, max)} and/or "mp"/"sp"), or has an
`item_func` effect (a buff like Defense Up, or curing a condition), or both.
An item flagged edible with neither is a data error and is refused rather
than eaten for nothing; tests_food.py checks every food prototype.

Reuses the item-effect system for that extra effect (so uses, residue, and
the combat action cost behave exactly like any potion) and only the wording
differs ("eats"/"drinks", see world/combat.py's item_use_verb).

A real gap this closes: shops sold bread, cheese and wine, but there was no
way to consume anything - `use` refused the unflavored ones outright ("not
a usable item") - so buying a 2-gold snack did nothing at all.
"""

from random import randint

from evennia import Command

STATS = ("hp", "mp", "sp")


def _carried_with(caller, verb):
    return [obj for obj in caller.contents if obj.db.consume_verb == verb]


def _restorable(caller, restore):
    """{"hp": room_left, ...} for each stat this food restores that the
    caller isn't already full on."""
    room = {}
    for stat in STATS:
        if stat in restore:
            left = (caller.attributes.get("max_" + stat) or 0) - (caller.attributes.get(stat) or 0)
            if left > 0:
                room[stat] = left
    return room


def consume(caller, args, verb):
    """Shared body of eat/drink - `verb` is "eat" or "drink"."""
    from world.combat import COMBAT_RULES, _search_carried_or_equipped, item_use_verb

    if not args:
        carried = _carried_with(caller, verb)
        msg = "Usage: %s <item>." % verb
        if carried:
            msg += " You're carrying: %s." % ", ".join(obj.key for obj in carried)
        else:
            msg += " You aren't carrying anything to %s. See 'help food'." % verb
        caller.msg(msg)
        return

    if caller.db.is_dead:
        caller.msg("The dead have no need of food or drink.")
        return

    nofound = "You aren't carrying anything called '%s'." % args
    item = _search_carried_or_equipped(caller, args, caller.contents, nofound)
    if not item:
        return

    item_verb = item.db.consume_verb
    if not item_verb:
        if item.db.item_func:
            caller.msg("That's not something you %s - try 'use %s'." % (verb, item.key))
        else:
            caller.msg("You can't %s that." % verb)
        return
    if item_verb != verb:
        caller.msg("You can't %s that - try '%s %s'." % (verb, item_verb, item.key))
        return

    restore = item.db.consume_restore or {}
    if not any(stat in restore for stat in STATS) and not item.db.item_func:
        # Owner rule: nothing edible does nothing. An item flagged as food
        # with no restore AND no buff/cure is bad data - refuse it, never
        # waste it.
        caller.msg("You can't %s that." % verb)
        return

    in_combat = COMBAT_RULES.is_in_combat(caller)
    if in_combat and not COMBAT_RULES.is_turn(caller):
        caller.msg("You can only %s on your turn." % verb)
        return

    room = _restorable(caller, restore)
    if not room and not item.db.item_func:
        # A pure restore food, and nothing it restores is missing - keep it
        # rather than waste it. (A buff food is always worth eating.)
        caller.msg("You're in no need of that right now - your strength is already full.")
        return

    old_hp = caller.db.hp or 0
    gained = {}
    for stat in STATS:
        if stat in room:
            low, high = restore[stat]
            amount = min(randint(low, high), room[stat])
            caller.attributes.add(stat, (caller.attributes.get(stat) or 0) + amount)
            gained[stat] = amount
    gain_text = " and ".join("%d %s" % (amt, stat.upper()) for stat, amt in gained.items())

    if item.db.item_func:
        # An extra effect on top (a buff or a cure). use_item prints the
        # "eats/drinks" line, spends a use/consumes the item, and takes the
        # combat action - so the restore result follows it.
        COMBAT_RULES.use_item(caller, item, caller)
        if gained:
            caller.location.msg_contents("%s regains %s." % (caller, gain_text))
    else:
        line = "%s %s %s!" % (caller, item_use_verb(item), item)
        if gained:
            line += " %s regains %s." % (caller, gain_text)
        caller.location.msg_contents(line)
        if item.attributes.has("item_uses"):
            COMBAT_RULES.spend_item_use(item, caller)
        else:
            caller.msg("You finish %s." % item)
            item.delete()
        if in_combat:
            COMBAT_RULES.spend_action(caller, 1, action_name="item")

    if "hp" in gained:
        COMBAT_RULES.announce_hp_threshold_change(caller, old_hp)


class CmdEat(Command):
    """
    Eat something you're carrying.

    Usage:
      eat <item>
      eat

    Bread, cheese, nuts, roasted meat, pies and the like are eaten, not
    'use'd. Every one does something - most restore some HP or SP (a
    hearty pie a lot, a handful of nuts a little), and some give a
    short-lived bonus instead or on top.
    With no item named, lists what you're carrying that you can eat.
    Your pack is the only place to eat from - buy food from a baker, a
    food vendor, or a market stall (see 'help food' for where), then
    eat it.

    In a fight you can eat only on your own turn, and it takes your
    action. If it would only restore something you're already full on, it
    stays uneaten rather than going to waste.

    Drinks are the same but use 'drink' - see 'help drink'. Potions,
    pills and the like use 'use'.
    """

    key = "eat"
    help_category = "general"

    def func(self):
        consume(self.caller, self.args.strip(), "eat")


class CmdDrink(Command):
    """
    Drink something you're carrying.

    Usage:
      drink <item>
      drink

    Wine and other drinks are drunk, not 'use'd. Every one does
    something - some restore HP or SP, and many give a short-lived bonus
    (Falernian puts fight into you, a fortified flask steadies your
    nerve). With no item
    named, lists what you're carrying that you can drink. Buy drinks from
    a wine merchant or a food vendor (see 'help food' for where).

    A drink with several servings, like an amphora, lasts for a few
    'drink's before it's finished. In a fight you can drink only on your
    own turn, and it takes your action. If it would only restore something
    you're already full on, it stays undrunk.

    Food uses 'eat' - see 'help eat'. Potions, pills and the like use
    'use'.
    """

    key = "drink"
    help_category = "general"

    def func(self):
        consume(self.caller, self.args.strip(), "drink")
