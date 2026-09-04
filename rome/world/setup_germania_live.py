"""
One-time live setup for the Germanic Stronghold (world/batch_germania_data.py):
creates all 115 rooms and their exits, attaches to the wilderness's own
(0, ROAD_LENGTH) tile via a real crossover exit
(world.wilderness_rome.LeaveGermaniaWildernessExit, already wired into
that tile's own "north" exit by the wilderness map provider itself -
this script only needs to make sure "The Palisade Gate" exists for it
to move players into), populates flavor NPCs and lookable objects,
spawns the real combat population (world/prototypes.py's GERMANIA_*
RespawningNPC prototypes, ~55 placements across the four warband camps
and the Contested Borderlands, plus the Storm-callers' unique
champion), and places the Germanic weaponsmith.

Run once via `evennia shell < world/setup_germania_live.py`. Not
idempotent - re-running duplicates everything. If ever reused, guard
by checking room count first.
"""

from evennia.utils import search, create
from evennia.prototypes.spawner import spawn

from world.batch_germania_data import ROOMS, LINKS, NPCS, OBJECTS, ECHOES

CHARACTER_TYPECLASS = "typeclasses.characters.Character"
OBJECT_TYPECLASS = "typeclasses.objects.Object"

# ----------------------------------------------------------------------
# 1. Create all 115 rooms
# ----------------------------------------------------------------------

room_objs = {}
for key, data in ROOMS.items():
    room = create.create_object("typeclasses.rooms.Room", key=data["name"])
    room.db.desc = data["desc"]
    room.tags.add(data["zone"], category="zone")
    room_objs[key] = room

print("Created %d rooms." % len(room_objs))

# ----------------------------------------------------------------------
# 2. Wire every internal exit, bidirectionally.
# ----------------------------------------------------------------------

exit_count = 0
for from_key, from_dir, to_key, to_dir in LINKS:
    from_room = room_objs[from_key]
    to_room = room_objs[to_key]
    create.create_object(
        "typeclasses.exits.Exit", key=from_dir, location=from_room, destination=to_room
    )
    create.create_object(
        "typeclasses.exits.Exit", key=to_dir, location=to_room, destination=from_room
    )
    exit_count += 2

print("Created %d internal exits." % exit_count)

# ----------------------------------------------------------------------
# 3. Confirm the wilderness crossover can actually find this zone -
#    LeaveGermaniaWildernessExit (world/wilderness_rome.py) looks up
#    "The Palisade Gate" by name at traversal time, so nothing needs
#    to be created here for that side; just verify it now exists.
# ----------------------------------------------------------------------

if not search.search_object("The Palisade Gate", typeclass="typeclasses.rooms.Room"):
    raise SystemExit("ABORTED: 'The Palisade Gate' was not created - crossover exit will fail.")
print("Confirmed 'The Palisade Gate' exists for the wilderness crossover exit.")

# ----------------------------------------------------------------------
# 4. Flavor NPCs
# ----------------------------------------------------------------------

npc_count = 0
for room_key, name, kind, desc, extra in NPCS:
    room = room_objs[room_key]
    npc = create.create_object(CHARACTER_TYPECLASS, key=name, location=room)
    npc.db.desc = desc
    npc.locks.add("get:false()")
    npc_count += 1

print("Spawned %d flavor NPCs." % npc_count)

# ----------------------------------------------------------------------
# 5. Lookable scenery objects
# ----------------------------------------------------------------------

obj_count = 0
for room_key, name, desc in OBJECTS:
    room = room_objs[room_key]
    obj = create.create_object(OBJECT_TYPECLASS, key=name, location=room)
    obj.db.desc = desc
    obj.locks.add("get:false()")
    obj_count += 1

print("Created %d scenery objects." % obj_count)

# ----------------------------------------------------------------------
# 6. Room echoes
# ----------------------------------------------------------------------

echo_count = 0
for room_key, lines in ECHOES.items():
    room = room_objs[room_key]
    room.db.echo_messages = lines
    room.scripts.add("world.colosseum.ColosseumEcho")
    echo_count += 1

print("Set echoes on %d rooms." % echo_count)

# ----------------------------------------------------------------------
# 7. The real, persistent combat population - RespawningNPC prototypes
#    spread across multiple rooms per camp, never a single spawn
#    point, matching the density plan settled on before this zone was
#    built: 3-per-camp variety for the two brawler camps, 2 for the
#    leaner scout/elite camps, 3 for the Contested Borderlands, plus
#    the Storm-callers' own unique named champion.
# ----------------------------------------------------------------------

COMBAT_PLACEMENTS = [
    # Wolf-kin (levels 27-31)
    ("wk_entrance", "GERMANIA_WOLFKIN_RAIDER"),
    ("wk_path_a", "GERMANIA_WOLFKIN_RAIDER"),
    ("wk_path_b", "GERMANIA_WOLFKIN_RAIDER"),
    ("wk_training_yard", "GERMANIA_WOLFKIN_RAIDER"),
    ("wk_sparring_ring", "GERMANIA_WOLFKIN_RAIDER"),
    ("wk_perimeter", "GERMANIA_WOLFKIN_BRAWLER"),
    ("wk_practice_ground", "GERMANIA_WOLFKIN_BRAWLER"),
    ("wk_cookfire", "GERMANIA_WOLFKIN_BRAWLER"),
    ("wk_lookout", "GERMANIA_WOLFKIN_BRAWLER"),
    ("wk_edge", "GERMANIA_WOLFKIN_BRAWLER"),
    ("wk_sleeping_a", "GERMANIA_WOLFKIN_YOUNG_MINOTAUR"),
    ("wk_sleeping_b", "GERMANIA_WOLFKIN_YOUNG_MINOTAUR"),
    ("wk_path_a", "GERMANIA_WOLFKIN_YOUNG_MINOTAUR"),
    ("wk_training_yard", "GERMANIA_WOLFKIN_YOUNG_MINOTAUR"),
    ("wk_edge", "GERMANIA_WOLFKIN_YOUNG_MINOTAUR"),

    # Boar-marked (levels 31-35)
    ("bm_entrance", "GERMANIA_BOARMARKED_WARRIOR"),
    ("bm_path_a", "GERMANIA_BOARMARKED_WARRIOR"),
    ("bm_training_yard", "GERMANIA_BOARMARKED_WARRIOR"),
    ("bm_sparring_ring", "GERMANIA_BOARMARKED_WARRIOR"),
    ("bm_perimeter", "GERMANIA_BOARMARKED_CYCLOPS"),
    ("bm_practice_ground", "GERMANIA_BOARMARKED_CYCLOPS"),
    ("bm_trophy_display", "GERMANIA_BOARMARKED_CYCLOPS"),
    ("bm_edge", "GERMANIA_BOARMARKED_CYCLOPS"),
    ("bm_path_b", "GERMANIA_BOARMARKED_VETERAN"),
    ("bm_cookfire", "GERMANIA_BOARMARKED_VETERAN"),
    ("bm_sleeping_a", "GERMANIA_BOARMARKED_VETERAN"),
    ("bm_sleeping_b", "GERMANIA_BOARMARKED_VETERAN"),

    # Raven's Watch (levels 35-39)
    ("rw_entrance", "GERMANIA_RAVENSWATCH_SCOUT"),
    ("rw_path_a", "GERMANIA_RAVENSWATCH_SCOUT"),
    ("rw_training_yard", "GERMANIA_RAVENSWATCH_SCOUT"),
    ("rw_lookout", "GERMANIA_RAVENSWATCH_SCOUT"),
    ("rw_perimeter", "GERMANIA_RAVENSWATCH_RAIDER"),
    ("rw_path_b", "GERMANIA_RAVENSWATCH_RAIDER"),
    ("rw_sparring_ring", "GERMANIA_RAVENSWATCH_RAIDER"),
    ("rw_edge", "GERMANIA_RAVENSWATCH_RAIDER"),

    # Storm-callers (levels 39-43)
    ("sc_entrance", "GERMANIA_STORMCALLER_GUARD"),
    ("sc_path_a", "GERMANIA_STORMCALLER_GUARD"),
    ("sc_perimeter", "GERMANIA_STORMCALLER_GUARD"),
    ("sc_path_b", "GERMANIA_STORMCALLER_ELITE"),
    ("sc_training_yard", "GERMANIA_STORMCALLER_ELITE"),
    ("sc_sparring_ring", "GERMANIA_STORMCALLER_ELITE"),

    # Contested Borderlands (levels 41-45)
    ("borderlands_entrance", "GERMANIA_BORDERLANDS_RAIDER"),
    ("borderlands_burned_camp", "GERMANIA_BORDERLANDS_RAIDER"),
    ("borderlands_ambush_ground", "GERMANIA_BORDERLANDS_RAIDER"),
    ("borderlands_old_battlefield", "GERMANIA_BORDERLANDS_RAIDER"),
    ("borderlands_ridge", "GERMANIA_BORDERLANDS_CYCLOPS"),
    ("borderlands_raiders_camp", "GERMANIA_BORDERLANDS_CYCLOPS"),
    ("borderlands_river_crossing", "GERMANIA_BORDERLANDS_CYCLOPS"),
    ("borderlands_broken_ground", "GERMANIA_BORDERLANDS_CYCLOPS"),
    ("borderlands_scout_post", "GERMANIA_BORDERLANDS_SCOUT"),
    ("borderlands_deep_thicket", "GERMANIA_BORDERLANDS_SCOUT"),
    ("borderlands_watch_fire", "GERMANIA_BORDERLANDS_SCOUT"),
    ("borderlands_last_stand", "GERMANIA_BORDERLANDS_SCOUT"),
    ("borderlands_approach_to_stormcallers", "GERMANIA_BORDERLANDS_SCOUT"),
]

combat_count = 0
for room_key, prototype_key in COMBAT_PLACEMENTS:
    obj = spawn(prototype_key)[0]
    obj.move_to(room_objs[room_key], quiet=True)
    combat_count += 1

# The Storm-callers' unique capstone champion.
champion = spawn("GERMANIA_BOSS_STORMCALLER_CHAMPION")[0]
champion.move_to(room_objs["sc_champions_ground"], quiet=True)
combat_count += 1

print("Spawned %d real combat NPCs across the settlement (including the capstone champion)." % combat_count)

# ----------------------------------------------------------------------
# 8. The Germanic weaponsmith
# ----------------------------------------------------------------------

from world.economy import GermanicWeaponsmith

weaponsmith = create.create_object(
    GermanicWeaponsmith, key="a Germanic weaponsmith", location=room_objs["smithy_stall"]
)
weaponsmith.db.desc = (
    "A broad-shouldered smith, real callouses and real burn scars on both "
    "hands - everything on display here is her own work, not imported "
    "Roman gear reskinned to look local."
)
weaponsmith.locks.add("get:false()")
print("Placed the Germanic weaponsmith in 'The Weaponsmith's Stall'.")

print(
    "Germania setup complete: %d rooms, %d exits, %d flavor NPCs, %d objects, "
    "%d combat NPCs, 1 weaponsmith." % (
        len(room_objs), exit_count, npc_count, obj_count, combat_count
    )
)
