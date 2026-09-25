"""
Eating and drinking.

Food and drink are ordinary items flagged with `db.consume_verb` ("eat" or
"drink" - set on the prototype, see world/prototypes.py) and routed through
these two commands instead of `use`, which is reserved for potions, pills,
and other usable items (world/combat.py's CmdUse refuses anything flagged
this way and points the player here).

Deliberately reuses the existing item-effect system rather than a parallel
one: a food item's healing or buff is just its `item_func`/`item_kwargs`
like any potion's, run through CombatRules.use_item (so uses, residue, and
the combat action cost all behave the same), and only the wording differs
("eats"/"drinks", see world/combat.py's item_use_verb). An item flagged
edible with NO effect at all is still consumable - purely for roleplay -
but only out of combat.

A real gap this closes: shops sold bread, cheese and wine, but there was no
way to consume anything - `use` refused the unflavored ones outright ("not
a usable item") - so buying a 2-gold snack did nothing at all.
"""

from evennia import Command

FOOD_HELP_TOPIC = "food"


def _carried_with(caller, verb):
    return [obj for obj in caller.contents if obj.db.consume_verb == verb]


def consume(caller, args, verb):
    """Shared body of eat/drink - `verb` is "eat" or "drink"."""
    from world.combat import COMBAT_RULES, _search_carried_or_equipped

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

    in_combat = COMBAT_RULES.is_in_combat(caller)
    if in_combat and not COMBAT_RULES.is_turn(caller):
        caller.msg("You can only %s on your turn." % verb)
        return

    if item.db.item_func:
        # Heals / buffs / cures through the normal item path. If the
        # effect refuses (already at full health, say) it prints why and
        # leaves the item unconsumed.
        COMBAT_RULES.use_item(caller, item, caller)
        return

    if in_combat:
        caller.msg("There's no time to linger over that in the middle of a fight.")
        return

    caller.msg("You %s %s." % (verb, item))
    if caller.location:
        caller.location.msg_contents("%s %ss %s." % (caller, verb, item), exclude=caller)
    item.delete()


class CmdEat(Command):
    """
    Eat something you're carrying.

    Usage:
      eat <item>
      eat

    Bread, cheese, nuts, roasted meat, pies and the like are eaten, not
    'use'd. Many give a small healing or a short-lived bonus; a few are
    only for the taste. With no item named, lists what you're carrying
    that you can eat. Your pack is the only place to eat from - buy food
    from a baker, a food vendor, or a market stall (see 'help food' for
    where), then eat it.

    In a fight you can eat only on your own turn, it takes your action,
    and only food that actually does something - there's no lingering
    over a snack mid-battle. If the food would do nothing (you're
    already at full health, say) it stays uneaten.

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

    Wine and other drinks are drunk, not 'use'd. Many give a small
    healing or a short-lived bonus - Falernian puts fight into you, a
    fortified flask steadies your nerve - and a few are only for the
    taste. With no item named, lists what you're carrying that you can
    drink. Buy drinks from a wine merchant or a food vendor (see 'help
    food' for where).

    A drink with several servings, like an amphora, lasts for a few
    'drink's before it's finished. In a fight you can drink only on
    your own turn and it takes your action; if the drink would do
    nothing (you're already at full health, say) it stays undrunk.

    Food uses 'eat' - see 'help eat'. Potions, pills and the like use
    'use'.
    """

    key = "drink"
    help_category = "general"

    def func(self):
        consume(self.caller, self.args.strip(), "drink")
