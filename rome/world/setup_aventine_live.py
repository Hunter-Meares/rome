"""
One-time live setup for the Aventine Hill: creates all 32 rooms and 32
exits from world/batch_aventine_data.py (28 Aventine-proper rooms + a
4-room geographic-accuracy road), attaches to the real, already-built
"The Far Garden" (Palatine Hill) via its previously-unused "south"
exit, and populates the flavor NPCs and lookable scenery objects.

Run once via `evennia shell < world/setup_aventine_live.py`. Not
idempotent - re-running duplicates everything.
"""

from evennia.utils import search, create

from world.batch_aventine_data import ROOMS, LINKS, NPCS, OBJECTS, ECHOES

CHARACTER_TYPECLASS = "typeclasses.characters.Character"
OBJECT_TYPECLASS = "typeclasses.objects.Object"

# ----------------------------------------------------------------------
# 1. Create all 32 rooms
# ----------------------------------------------------------------------

room_objs = {}
for key, data in ROOMS.items():
    room = create.create_object("typeclasses.rooms.Room", key=data["name"])
    room.db.desc = data["desc"]
    room.tags.add("aventine", category="zone")
    room_objs[key] = room

print("Created %d rooms." % len(room_objs))

# ----------------------------------------------------------------------
# 2. Wire the connector exit to the real, already-built anchor room,
#    then every internal exit, bidirectionally.
# ----------------------------------------------------------------------

anchors = search.search_object("The Far Garden", typeclass="typeclasses.rooms.Room")
if not anchors:
    raise SystemExit("ABORTED: could not find the real 'The Far Garden' room live.")
anchor_room = anchors[0]

exit_count = 0
for from_key, from_dir, to_key, to_dir in LINKS:
    from_room = anchor_room if from_key == "existing_far_garden" else room_objs[from_key]
    to_room = anchor_room if to_key == "existing_far_garden" else room_objs[to_key]
    create.create_object(
        "typeclasses.exits.Exit", key=from_dir, location=from_room, destination=to_room
    )
    create.create_object(
        "typeclasses.exits.Exit", key=to_dir, location=to_room, destination=from_room
    )
    exit_count += 2

print("Created %d exits (including the connector to The Far Garden)." % exit_count)

# ----------------------------------------------------------------------
# 3. NPCs
# ----------------------------------------------------------------------

npc_count = 0
for room_key, name, kind, desc, extra in NPCS:
    room = room_objs[room_key]
    npc = create.create_object(CHARACTER_TYPECLASS, key=name, location=room)
    npc.db.desc = desc
    npc.locks.add("get:false()")
    if kind == "wander":
        wander_rooms = [room_objs[k] for k in extra]
        npc.db.wander_rooms = wander_rooms
        npc.scripts.add("world.colosseum.WanderingNPC")
    npc_count += 1

print("Spawned %d NPCs." % npc_count)

# ----------------------------------------------------------------------
# 4. Lookable scenery objects
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
# 5. Room echoes
# ----------------------------------------------------------------------

echo_count = 0
for room_key, lines in ECHOES.items():
    room = room_objs[room_key]
    room.db.echo_messages = lines
    room.scripts.add("world.colosseum.ColosseumEcho")
    echo_count += 1

print("Set echoes on %d rooms." % echo_count)
print("Aventine setup complete: %d rooms, %d exits, %d NPCs, %d objects." % (
    len(room_objs), exit_count, npc_count, obj_count,
))
