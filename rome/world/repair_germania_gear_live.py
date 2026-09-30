"""
One-off live repair: equips every already-spawned Germania rank-and-file
NPC with its new GERMANIA_GEAR kit (world/combat.py's equip_germania_npc,
Sep 30's Germania gear pass). RespawningNPC.at_object_post_creation only
ever runs once, at creation - the exact same gap gotcha #20 (CLAUDE.md)
already documents for the boss-signature-move pass: a new db default (or,
here, a whole new equip step) never reaches an object already created
before the code that sets it existed. These 14 NPCs (plus the zone boss,
Vidrik Storm-Marked) were all spawned live long before equip_germania_npc
was written, so they're sitting there unarmed/unarmored until this runs.

Idempotent - skips any NPC that already has a wielded_weapon (so a second
run, or a naturally-respawned NPC that already got equipped by this same
script, is never double-equipped).

Run via `evennia shell < world/repair_germania_gear_live.py`.
"""

from evennia.objects.models import ObjectDB

from world.combat import GERMANIA_GEAR, equip_germania_npc

npcs = ObjectDB.objects.filter(db_typeclass_path="world.combat.RespawningNPC")
germania_npcs = [n for n in npcs if n.key in GERMANIA_GEAR]

repaired = 0
already_equipped = 0

for npc in germania_npcs:
    if npc.db.wielded_weapon:
        already_equipped += 1
        continue
    equip_germania_npc(npc)
    repaired += 1
    print("Equipped %s (level %s)." % (npc.key, npc.db.level))

print("Done: %d equipped, %d already had gear, %d Germania NPCs found live total." % (
    repaired, already_equipped, len(germania_npcs)
))
