"""
Loot drops - built specifically for the Cloaca Maxima sewer zone,
which the design explicitly flagged as needing this as new
infrastructure, not something to silently retrofit onto every
existing NPC in the game. Gated on the "sewer_npc" tag (world/
prototypes.py's sewer population) so Arena Fighters, Colosseum
trainers, and everything else already live keep behaving exactly as
before - nobody asked for their drop behavior to change.

Reuses the existing level-scaled item generation wholesale
(spawn_leveled_weapon/spawn_leveled_armor, world/combat.py) rather
than inventing a second, parallel item-power system - an NPC's level
already determines what its drops are capable of, with zero
additional balancing work.
"""

import random
import time

from world.combat import spawn_leveled_weapon, spawn_leveled_armor

LOOT_DROP_CHANCE = 20  # percent, checked once per defeat

WEAPON_PROTOTYPES = [
    "DAGGER", "BROADSWORD", "GREATSWORD", "GLADIUS", "SPEAR",
    "TRIDENT", "JAVELIN", "SHORTBOW", "WARAXE", "RITUAL_STAFF",
]
ARMOR_PROTOTYPES = ["LEATHERARMOR", "SCALEMAIL", "PLATEMAIL"]


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
