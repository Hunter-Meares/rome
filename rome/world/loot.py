"""
Loot drops. Originally built specifically for the Cloaca Maxima sewer
zone (roll_loot_drop, gated on the "sewer_npc" tag), which the design
explicitly flagged as needing this as new infrastructure, not
something to silently retrofit onto every existing NPC in the game -
Arena Fighters, Colosseum trainers, and everything else stayed
untouched at the time. Extended since then with roll_arena_loot_drop
for the Deeper Sands' Arena Fighters specifically (gated on their own
existing "arena_fighter" tag) - still opt-in per population via a Tag,
not a blanket change to every NPC with an xp_reward.

Both reuse the existing level-scaled item generation wholesale
(spawn_leveled_weapon/spawn_leveled_armor, world/combat.py) rather
than inventing a second, parallel item-power system - an NPC's level
already determines what its drops are capable of, with zero
additional balancing work.
"""

import random
import time

from world.combat import spawn_leveled_weapon, spawn_leveled_armor

LOOT_DROP_CHANCE = 20  # percent, checked once per defeat

# Deliberately NOT the plain DAGGER/BROADSWORD/LEATHERARMOR/etc.
# prototypes - those are exactly what chargen hands multiple classes
# for free, and the Ludus weaponsmith's SMITH_* stock already sells
# the rest. A sewer drop needs to feel like a genuine find, not an
# indistinguishable copy of something a player already owns or could
# just buy - see the SEWER_LOOT_* prototypes in world/prototypes.py,
# each with its own real identity and a tie back to a specific
# tier/faction of the zone, even though they reuse the exact same
# weapon_type_name/armor_category values (and therefore the exact
# same balance) as everything else in the game.
WEAPON_PROTOTYPES = [
    "SEWER_LOOT_GLADIUS", "SEWER_LOOT_DAGGER", "SEWER_LOOT_SPEAR",
    "SEWER_LOOT_WARAXE", "SEWER_LOOT_RITUAL_STAFF", "SEWER_LOOT_SHORTBOW",
]
ARMOR_PROTOTYPES = ["SEWER_LOOT_LEATHER", "SEWER_LOOT_SCALE", "SEWER_LOOT_PLATE"]


def roll_loot_drop(defeated, attacker=None):
    """
    Called from CombatRules.at_defeat, right alongside the existing
    XP-reward block - same "any NPC with xp_reward" gate, further
    narrowed to just the sewer's own population via the sewer_npc tag.
    A 50/50 roll between a weapon and a body armor piece, spawned at
    the defeated NPC's own level and dropped into the room for
    whoever's there to pick up - not auto-granted to a specific
    contributor, matching how a dropped item works everywhere else in
    this game (on the ground, first-come).
    """
    if not defeated.tags.has("sewer_npc", category="npc_role"):
        return
    if random.randint(1, 100) > LOOT_DROP_CHANCE:
        return

    location = defeated.location
    if not location:
        return

    level = defeated.db.level or 1

    if random.random() < 0.5:
        prototype = random.choice(WEAPON_PROTOTYPES)
        item = spawn_leveled_weapon(prototype, level, location=location)
    else:
        prototype = random.choice(ARMOR_PROTOTYPES)
        item = spawn_leveled_armor(prototype, level, location=location)

    # Real bug found and fixed: spawn_leveled_weapon/armor place the
    # item via move_to(), which never calls at_drop() - the hook that
    # normally stamps db.dropped_at for the existing 24-hour clutter
    # sweep (ItemDecayManager/find_decayed_items, world/combat.py).
    # Without this, loot would sit on the ground forever, accumulating
    # without bound across the whole zone. Stamped manually here so a
    # loot drop decays exactly like any player-dropped item does.
    item.db.dropped_at = time.time()

    location.msg_contents("|YSomething drops from %s: %s!|n" % (defeated.key, item.key))


# Deeper Sands Arena Fighters - a direct follow-up request alongside
# giving them real equipped gear (see ARENA_FIGHTER_GEAR/
# equip_arena_fighter, world/combat.py): they should drop loot too.
# A deliberately different shape from the sewer's shared random pool
# above - each of the six Arena Fighters is a distinct, named
# identity (not interchangeable trash-mob population), so a drop is
# deterministic-by-fighter (still a 50/50 weapon-vs-armor roll) rather
# than pulled from one pool shared across all six. Higher drop chance
# than the sewers (40% vs 20%) - these are meaningful, one-at-a-time
# endgame fights, not high-volume trash clearing, so a single kill
# should feel more likely to pay off.
ARENA_LOOT_DROP_CHANCE = 40  # percent, checked once per defeat

# (weapon_prototype, armor_prototype) per fighter, keyed by db.base_name
# (spawn_personal_npc's clean pre-rename key - the live NPC's own .key
# has already been rewritten to "<name> (<challenger>'s opponent)" by
# the time it's defeated). Own named ARENA_LOOT_* prototypes rather
# than the plain GLADIUS/WARAXE/etc. equip-time prototypes, or the
# sewer's own SEWER_LOOT_* ones - see world/prototypes.py's own
# comment on this for why (a drop should feel like a genuine find tied
# to the specific fighter it came from).
ARENA_LOOT_TABLE = {
    "a hardened arena recruit": ("ARENA_LOOT_RECRUIT_GLADIUS", "ARENA_LOOT_RECRUIT_ARMOR"),
    "a Centaur arena hunter": ("ARENA_LOOT_HUNTER_JAVELIN", "ARENA_LOOT_HUNTER_ARMOR"),
    "a Minotaur arena brute": ("ARENA_LOOT_BRUTE_WARAXE", "ARENA_LOOT_BRUTE_ARMOR"),
    "a Harpy arena duelist": ("ARENA_LOOT_DUELIST_DAGGER", "ARENA_LOOT_DUELIST_ARMOR"),
    "a Cyclops arena champion": ("ARENA_LOOT_CHAMPION_BROADSWORD", "ARENA_LOOT_CHAMPION_ARMOR"),
    "the Arena Master": ("ARENA_LOOT_MASTER_WARAXE", "ARENA_LOOT_MASTER_ARMOR"),
}


def roll_arena_loot_drop(defeated, attacker=None):
    """
    Called from CombatRules.at_defeat right alongside roll_loot_drop
    above - same "any NPC with xp_reward" gate, narrowed to the Deeper
    Sands' Arena Fighters via the existing arena_fighter tag (already
    on every ARENA_FIGHTER_* prototype for other purposes). Dropped
    into the room, not auto-granted, matching every other loot drop
    in the game.
    """
    if not defeated.tags.has("arena_fighter", category="npc_role"):
        return
    if random.randint(1, 100) > ARENA_LOOT_DROP_CHANCE:
        return

    location = defeated.location
    if not location:
        return

    gear = ARENA_LOOT_TABLE.get(defeated.db.base_name or defeated.key)
    if not gear:
        return

    weapon_prototype, armor_prototype = gear
    level = defeated.db.level or 1

    if random.random() < 0.5:
        item = spawn_leveled_weapon(weapon_prototype, level, location=location)
    else:
        item = spawn_leveled_armor(armor_prototype, level, location=location)

    item.db.dropped_at = time.time()  # see roll_loot_drop's own note above

    location.msg_contents("|YSomething drops from %s: %s!|n" % (defeated.key, item.key))
