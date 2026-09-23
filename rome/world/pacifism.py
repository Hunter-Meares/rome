"""
Pacifism - a real, first-class opt-out of combat entirely, not just of
PvP. A pacifist character can never attack, and can never be attacked
by, another player OR any NPC. This is what makes a genuine non-combat
playstyle (exploring, trading, roleplay, and eventually crafting)
actually safe to commit to, rather than "technically optional but the
wilderness will still eat you."

No new onboarding path was needed for this: the Colosseum's holding
cells already offer a genuine non-combat escape (`sneak` past the
guard, then `solve` the riddle - see world/colosseum.py's CmdSneak/
CmdSolve, both retry-able and already zero-combat), and nothing else
in the game auto-attacks a player except the wilderness roads'
`_aggro_on_sight` (world/wilderness_rome.py, world/
wilderness_amber_coast.py) - both exempt a pacifist outright rather
than spawning an encounter and then refusing to let it engage. A
pacifist can walk the whole existing game today: escape the cells,
explore, do any "visit"/"talk" quest step, and never touch combat.

Two real abuse cases this is designed against, both named directly
during design:

  1. Kill a player in PvP, then immediately flip to pacifist to dodge
     retaliation. Closed by db.has_ever_killed_player
     (world/combat.py's CombatRules.at_defeat PvP branch sets this on
     every real contributor to a real player's death) - a permanent,
     unconditional disqualifier, not a timer. A cooldown alone can't
     close this on its own (wait it out, keep the loot), so this is a
     bright line instead.
  2. Flee a fight you're about to lose by flipping mid-crisis. Closed
     two ways: you can never switch while
     COMBAT_RULES.is_in_combat() is true, and
     PACIFISM_COMBAT_COOLDOWN keeps you ineligible for a real-time
     while after your last actual combat action (db.last_combat_
     activity, stamped for both sides of a hit in world/combat.py's
     apply_damage - refreshed continuously through a fight, so a long
     fight keeps the cooldown running the whole time it's active).

A third real concern, also named directly: a pacifist quietly
hoarding a one-of-a-kind item by sitting on it forever, immune to
ever losing it in a fight. Closed by gear surrender on switching TO
pacifist - every equipped item is removed, and anything tagged
db.unique_item = True is destroyed outright rather than merely
dropped (dropping alone doesn't actually stop hoarding - it could
just be stashed or minded by someone else). Ordinary gear is only
unequipped, since it isn't scarce. db.unique_item is a new convention
- nothing in the game sets it yet (the only "unique" gear that exists
today, world/prototypes.py's divine THUNDERBOLT_OF_JUPITER and
friends, is distinguished only by a get:false() lock and being
hand-placed, not a data flag) - but any future one-of-a-kind player
drop should set it, so this check has something real to find.

Deliberately modeled on world/factions.py's join/leave asymmetry
rather than inventing new UX: switching TO pacifist is self-service,
with an explicit 'confirm' step and an in-character warning first -
exactly like `faction join <name> confirm` - but switching BACK to a
combatant is never self-service, only a god can do it (godpacifism),
mirroring how only a faction leader or a god can release an ordinary
member. This is meant to be a real, weighty choice, not something
flipped on a whim to dodge one specific dangerous stretch of content.

Grants the "The Peaceable" achievement (world/achievements.py) the
moment someone becomes a pacifist. A second, "Iron Will" (reach level
10 as a pacifist), is granted from world/combat.py's own level-up
hook once world/gathering.py + world/recipes.py shipped a real
repeatable non-combat XP loop later the same session - see world/
achievements.py's own comment for why that one specifically waited
until it was honestly achievable rather than a rounding-margin fluke.

Stats and statup are deliberately NOT special-cased for a pacifist -
same leveling curve, same stat point every 3 levels, same `statup`
menu, same choices. Virtus/Agilitas/Ingenium/Vigor genuinely do
nothing for someone who can never enter combat, but the points
aren't wasted or hidden - a future godpacifism restoration to
combatant would make them matter again, and nothing here should
quietly punish the choice by taking options away. The one resource
that visibly matters day-to-day for a pacifist is SP, since ordinary
movement still costs it (world/combat.py's MOVEMENT_SP_COST) - the
existing flat HP/MP/SP statup conversion is the practically useful
pick for one, not any single core combat stat.
"""

import time

from evennia import Command

from world.combat import COMBAT_RULES, _equipped_items, _unequip_item

# How long, in real seconds, a character must go without a real combat
# action (dealing or taking damage - see apply_damage's stamp) before
# they're eligible to switch to pacifist. Independent of, and in
# addition to, the flat "not while actually in combat" check.
PACIFISM_COMBAT_COOLDOWN = 3600


def is_pacifist(character):
    return bool(character.db.pacifist)


def pacifism_blockers(character):
    """
    Every reason `character` can't switch to pacifist right now, most
    important first. Empty list means eligible.
    """
    if character.db.pacifist:
        return ["You've already laid down your arms for good."]

    if character.db.has_ever_killed_player:
        return [
            "You've killed another player. There's no path back from "
            "that - a pacifist's life isn't available to you."
        ]

    if COMBAT_RULES.is_in_combat(character):
        return ["You can't do that in the middle of a fight."]

    last = character.db.last_combat_activity or 0
    remaining = PACIFISM_COMBAT_COOLDOWN - (time.time() - last)
    if remaining > 0:
        minutes = max(1, int(remaining // 60) + 1)
        return [
            "You're still too keyed up from your last fight - wait "
            "about %d more minute%s." % (minutes, "" if minutes == 1 else "s")
        ]

    return []


def gear_to_surrender(character):
    """{item: attr_name} for everything currently equipped - reuses
    world/combat.py's own _equipped_items rather than duplicating the
    wielded-weapon-plus-every-armor-slot logic."""
    return _equipped_items(character)


def become_pacifist(character):
    """
    Performs the actual switch: strips every equipped item
    (destroying anything tagged db.unique_item, since dropping alone
    wouldn't stop hoarding one), sets the flag, and reports exactly
    what happened. Callers must already have confirmed
    pacifism_blockers() is empty.
    """
    kept, destroyed = [], []
    for item, attr_name in gear_to_surrender(character).items():
        # Reuses world/combat.py's own unequip step exactly (which
        # armor bonus removal applies to, whether a weapon's own
        # is_in_combat/is_turn gate fires - all moot here, since
        # pacifism_blockers() already guarantees the character isn't
        # in combat at all before this is ever called), rather than a
        # hand-rolled duplicate that could silently drift out of sync
        # with it.
        _unequip_item(character, item, attr_name, COMBAT_RULES)
        if item.db.unique_item:
            destroyed.append(item.key)
            item.delete()
        else:
            kept.append(item.key)

    character.db.pacifist = True

    character.msg(
        "|yYou lay down your arms for good. Whatever happens from here, "
        "it will not be by your hand - and no one else's hand can touch "
        "you either.|n"
    )
    if kept:
        character.msg("You set aside: %s." % ", ".join(kept))
    if destroyed:
        character.msg("|xGone for good, not merely set down: %s.|n" % ", ".join(destroyed))

    # No has_account gate here (unlike combat.py's level-100 hook) -
    # become_pacifist only ever runs from CmdPacifism, a real command
    # that can't execute without an actual connected caller in the
    # first place, so the gate would never do anything in production
    # and would only make this harder to test directly.
    from evennia.contrib.game_systems.achievements import track_achievements
    from world.achievements import announce_achievements
    completed = track_achievements(character, category="pacifism", tracking="became")
    announce_achievements(character, completed)


def restore_combatant(character):
    """The only way back - see CmdGodPacifism below. Never returns any
    gear destroyed on the way in; that loss was explicit and final."""
    character.db.pacifist = False


class CmdPacifism(Command):
    """
    Permanently lay down arms - opt out of combat entirely.

    Usage:
      pacifism
      pacifism confirm

    A pacifist can never attack, and can never be attacked by, another
    player or any creature, anywhere - the wilderness roads, a duel, a
    kill quest, all of it. This is a real, permanent choice: bare
    'pacifism' shows what it costs you and what it means before
    anything happens; only 'pacifism confirm' actually does it.

    You give up every weapon and piece of armor you're wearing to do
    this - anything one of a kind among it is lost for good, not just
    set down. Once you're a pacifist, only a god can restore your
    right to fight again; you can't undo this yourself.

    You can't switch if you've ever killed another player, if you're
    currently in a fight, or for a while after your last real combat
    action.
    """

    key = "pacifism"
    help_category = "general"

    def func(self):
        caller = self.caller
        arg = self.args.strip().lower()

        blockers = pacifism_blockers(caller)
        if blockers:
            caller.msg(blockers[0])
            return

        if arg != "confirm":
            equipped = gear_to_surrender(caller)
            unique = [item.key for item in equipped if item.db.unique_item]
            warning = (
                "|wBecoming a pacifist is permanent.|n Only a god can undo it. "
                "You will never be able to attack, or be attacked by, another "
                "player or any creature again."
            )
            if equipped:
                warning += " Every weapon and piece of armor you're wearing comes off."
            if unique:
                warning += (
                    " %s, being one of a kind, will be lost for good, not "
                    "just set down." % ", ".join(unique)
                )
            warning += "\nType |wpacifism confirm|n if you're certain."
            caller.msg(warning)
            return

        become_pacifist(caller)


class CmdGodPacifism(Command):
    """
    Restore a pacifist's right to fight - the only way back.

    Usage:
      godpacifism <character>

    Becoming a pacifist (see 'help pacifism') is deliberately not
    something a player can undo themselves - only a god can. This
    does not return any gear that was destroyed on the way in.
    """

    key = "godpacifism"
    help_category = "admin"

    def func(self):
        caller = self.caller
        if (caller.db.level or 0) <= 100:
            caller.msg("Only gods can do that.")
            return
        if not self.args:
            caller.msg("Usage: godpacifism <character>")
            return
        target = caller.search(self.args.strip(), global_search=True)
        if not target:
            return
        if not is_pacifist(target):
            caller.msg("%s isn't a pacifist." % target.key)
            return
        restore_combatant(target)
        caller.msg("%s can fight again." % target.key)
        target.msg("|yA god's hand restores your right to fight, if you ever want it.|n")
