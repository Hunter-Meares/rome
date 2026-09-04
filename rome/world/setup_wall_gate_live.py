"""
One-time live setup for Rome's Wall & Gate (world/batch_wall_gate_data.py):
creates all 8 rooms and 7 plain exits, plus the Porta Flaminia's real
working door (world.doors.DescriptiveDoor), attaches to the real,
already-built "The Centuriate Assembly Ground" via its previously
unused "west" exit, and populates the guard NPCs and scenery objects.

Run once via `evennia shell < world/setup_wall_gate_live.py`. Not
idempotent - re-running duplicates everything. If ever reused, guard
by checking room count first.
"""

from evennia.utils import search, create

from world.batch_wall_gate_data import ROOMS, LINKS, DOOR_LINK, NPCS, OBJECTS, ECHOES

CHARACTER_TYPECLASS = "typeclasses.characters.Character"
OBJECT_TYPECLASS = "typeclasses.objects.Object"

# ----------------------------------------------------------------------
# 1. Create all 8 rooms
# ----------------------------------------------------------------------

room_objs = {}
for key, data in ROOMS.items():
    room = create.create_object("typeclasses.rooms.Room", key=data["name"])
    room.db.desc = data["desc"]
    room.tags.add("wall_gate", category="zone")
    room_objs[key] = room

print("Created %d rooms." % len(room_objs))

# ----------------------------------------------------------------------
# 2. Wire the connector exit to the real, already-built anchor room,
#    then every plain internal exit, bidirectionally.
# ----------------------------------------------------------------------

anchors = search.search_object("The Centuriate Assembly Ground", typeclass="typeclasses.rooms.Room")
if not anchors:
    raise SystemExit("ABORTED: could not find the real 'The Centuriate Assembly Ground' room live.")
anchor_room = anchors[0]

exit_count = 0
for from_key, from_dir, to_key, to_dir in LINKS:
    from_room = anchor_room if from_key == "existing_assembly_ground" else room_objs[from_key]
    to_room = anchor_room if to_key == "existing_assembly_ground" else room_objs[to_key]
    create.create_object(
        "typeclasses.exits.Exit", key=from_dir, location=from_room, destination=to_room
    )
    create.create_object(
        "typeclasses.exits.Exit", key=to_dir, location=to_room, destination=from_room
    )
    exit_count += 2

print("Created %d plain exits (including the connector to Campus Martius)." % exit_count)

# ----------------------------------------------------------------------
# 3. The Porta Flaminia's actual working door - a real
#    world.doors.DescriptiveDoor pair, db.return_exit linked both
#    ways, starting open (matching every other exit's default state).
# ----------------------------------------------------------------------

from_key, from_dir, to_key, to_dir = DOOR_LINK
from_room = room_objs[from_key]
to_room = room_objs[to_key]

door_out = create.create_object(
    "world.doors.DescriptiveDoor", key=from_dir, location=from_room, destination=to_room
)
door_in = create.create_object(
    "world.doors.DescriptiveDoor", key=to_dir, location=to_room, destination=from_room
)
door_out.db.return_exit = door_in
door_in.db.return_exit = door_out
door_out.setdesc("A genuine, iron-bound oak gate, thick enough to stop a battering ram.")
door_out.locks.add("traverse:true()")
door_in.locks.add("traverse:true()")

print("Created the Porta Flaminia's working door (open by default).")

# ----------------------------------------------------------------------
# 4. Guard NPCs
# ----------------------------------------------------------------------

npc_count = 0
for room_key, name, kind, desc, extra in NPCS:
    room = room_objs[room_key]
    npc = create.create_object(CHARACTER_TYPECLASS, key=name, location=room)
    npc.db.desc = desc
    npc.locks.add("get:false()")
    if room_key == "wall_gate_passage":
        # The last guard players pass before actually stepping out -
        # a real, in-character warning about the wilderness beyond,
        # added once the road actually became genuinely dangerous
        # (auto-aggro wilderness encounters, direct request).
        npc.db.chatter_lines = [
            "Stay wary out there. Plenty who leave through this gate don't come back the same.",
            "Whatever's beyond that wall doesn't wait to be provoked - it'll come at you the moment it sees you.",
            "The road looks quiet enough from here. It isn't, once you're on it.",
        ]
        npc.scripts.add("world.colosseum.NPCChatter")
    npc_count += 1

print("Spawned %d NPCs." % npc_count)

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
print("Wall & Gate setup complete: %d rooms, %d plain exits + 1 door, %d NPCs, %d objects." % (
    len(room_objs), exit_count, npc_count, obj_count,
))
