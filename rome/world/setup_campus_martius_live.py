"""
One-time live setup for Campus Martius (including the Mausoleum of
Augustus) and the geographic-accuracy retrofit road connecting it to
the already-built Pantheon.

Creates all 36 new rooms and 35 new exits (37 links minus the 2 that
are retrofits, see below) from world/batch_campus_martius_data.py,
then performs the actual retrofit: finds the two real, already-live
exit objects -

  - Via Triumphalis's (room #664) existing "north" exit, currently
    pointing straight at Pantheon Approach
  - Pantheon Approach's existing "south" exit, currently pointing
    straight back at Via Triumphalis

- and repoints each one's `destination` in place (keeping their
existing keys/aliases, NOT deleting and recreating them) so a 7-room
road now sits between them instead of a single direct hop. The
Pantheon's own 6 rooms, its NPC, and its altar object are completely
untouched by this script - only the two exit objects' destinations
change.

Run once via `evennia shell < world/setup_campus_martius_live.py`.
Not idempotent - re-running duplicates everything (and would try to
re-repoint exits that are already repointed, which is harmless but
pointless).

REAL BUG FOUND LIVE, FIXED SEPARATELY - not in this file's own logic,
since it already ran once and isn't meant to be re-run, but worth
recording here for anyone reading this as a retrofit template later.
RETROFIT_LINKS below (step 4) skips two LINKS entries on the
assumption that "repointing the two existing exits already covers
both directions of the connection" - it doesn't. Repointing
`vt_north_exit.destination` only makes the FORWARD hop (Via
Triumphalis -> onto the new road) work; it does nothing for the
REVERSE hop the skipped LINKS entry
("existing_via_triumphalis", "north", "road_market_stalls", "south")
would otherwise have created (a real "south" exit AT
road_market_stalls, back to Via Triumphalis). Same gap at the far end
- repointing `pa_south_exit.destination` only makes Pantheon Approach
-> Campus Hub work forward; the skipped entry
("campus_hub", "north", "existing_pantheon_approach", "south") never
created campus_hub's own "north" exit back to the Pantheon. Net
effect: the entire 7-room road plus the Pantheon's own 6 rooms (13
rooms in total) were walkable IN, one-way, and had no exit leading
back out via the same route - confirmed live via
world/worldcheck.py's check_reachability(), then fixed by manually
creating the two missing return exits directly (road_market_stalls
"south" -> Via Triumphalis; campus_hub "north" -> Pantheon Approach).
If retrofitting another already-built connection this same way in the
future, repoint-in-place still only ever fixes ONE direction per
existing exit - the LINKS entries for the OTHER direction at each
anchor point still need to actually run, not be silently skipped.
"""

from evennia.utils import search, create

from world.batch_campus_martius_data import ROOMS, LINKS, NPCS, OBJECTS, ECHOES

CHARACTER_TYPECLASS = "typeclasses.characters.Character"
OBJECT_TYPECLASS = "typeclasses.objects.Object"

# ----------------------------------------------------------------------
# 1. Create all 36 rooms
# ----------------------------------------------------------------------

room_objs = {}
for key, data in ROOMS.items():
    room = create.create_object("typeclasses.rooms.Room", key=data["name"])
    room.db.desc = data["desc"]
    room.tags.add(data["zone"], category="zone")
    room_objs[key] = room

print("Created %d rooms." % len(room_objs))

# ----------------------------------------------------------------------
# 2. Find the two real anchor rooms
# ----------------------------------------------------------------------

via_triumphalis_candidates = search.search_object("Via Triumphalis", typeclass="typeclasses.rooms.Room")
pantheon_approach_candidates = search.search_object("Approach to the Pantheon", typeclass="typeclasses.rooms.Room")

if not via_triumphalis_candidates:
    raise SystemExit("ABORTED: could not find the real 'Via Triumphalis' room live.")
if not pantheon_approach_candidates:
    raise SystemExit("ABORTED: could not find the real 'Approach to the Pantheon' room live.")

via_triumphalis = via_triumphalis_candidates[0]
pantheon_approach = pantheon_approach_candidates[0]

# ----------------------------------------------------------------------
# 3. The retrofit: repoint the two existing exits, don't delete/recreate
# ----------------------------------------------------------------------

vt_north_exit = next((e for e in via_triumphalis.exits if e.key == "north"), None)
pa_south_exit = next((e for e in pantheon_approach.exits if e.key == "south"), None)

if not vt_north_exit:
    raise SystemExit("ABORTED: Via Triumphalis has no 'north' exit to retrofit - check for prior changes.")
if not pa_south_exit:
    raise SystemExit("ABORTED: Pantheon Approach has no 'south' exit to retrofit - check for prior changes.")

if vt_north_exit.destination != pantheon_approach:
    raise SystemExit(
        "ABORTED: Via Triumphalis's 'north' exit doesn't point at Pantheon Approach as expected "
        "(points at %r instead) - not safe to retrofit blindly." % vt_north_exit.destination
    )
if pa_south_exit.destination != via_triumphalis:
    raise SystemExit(
        "ABORTED: Pantheon Approach's 'south' exit doesn't point at Via Triumphalis as expected "
        "(points at %r instead) - not safe to retrofit blindly." % pa_south_exit.destination
    )

vt_north_exit.destination = room_objs["road_market_stalls"]
pa_south_exit.destination = room_objs["campus_hub"]

print("Retrofit complete: Via Triumphalis 'north' now leads onto the new road; "
      "Pantheon Approach 'south' now leads to the Campus Martius hub.")

# ----------------------------------------------------------------------
# 4. Wire every other (genuinely new) exit, bidirectionally
# ----------------------------------------------------------------------

RETROFIT_LINKS = {
    ("existing_via_triumphalis", "north", "road_market_stalls", "south"),
    ("campus_hub", "north", "existing_pantheon_approach", "south"),
}

exit_count = 0
for from_key, from_dir, to_key, to_dir in LINKS:
    if (from_key, from_dir, to_key, to_dir) in RETROFIT_LINKS:
        continue
    from_room = room_objs[from_key]
    to_room = room_objs[to_key]
    create.create_object(
        "typeclasses.exits.Exit", key=from_dir, location=from_room, destination=to_room
    )
    create.create_object(
        "typeclasses.exits.Exit", key=to_dir, location=to_room, destination=from_room
    )
    exit_count += 2

print("Created %d new exits (plus the 2 retrofitted in place)." % exit_count)

# ----------------------------------------------------------------------
# 5. NPCs
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
# 6. Lookable scenery objects
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
# 7. Room echoes
# ----------------------------------------------------------------------

echo_count = 0
for room_key, lines in ECHOES.items():
    room = room_objs[room_key]
    room.db.echo_messages = lines
    room.scripts.add("world.colosseum.ColosseumEcho")
    echo_count += 1

print("Set echoes on %d rooms." % echo_count)
print("Campus Martius setup complete: %d rooms, %d new exits + 2 retrofitted, %d NPCs, %d objects." % (
    len(room_objs), exit_count, npc_count, obj_count,
))
