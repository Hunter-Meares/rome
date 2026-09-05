"""
Rome's Wall & Gate - the first piece of the "Beyond the Walls" project
(wilderness, the road to Germania, the Germanic stronghold). A
validated, in-memory description of every room, exit, NPC, and object
before anything touches the live database. Same pattern as every
prior build this session.

Historical framing, decided deliberately rather than glossed over:
Rome at the height of its power (the Pax Romana period this whole
project is grounded in) genuinely had no major defensive walls - the
real Aurelian Walls weren't built until roughly a century later,
during the Crisis of the Third Century. This is treated as an
intentional, acknowledged step ahead of the project's usual timeframe,
justified by how much mechanical and narrative value a real gate
boundary provides (a real, working door; a place for a "you've left
Rome" transition; an anchor point for the wilderness and the road
north).

Attaches to the real, already-built "The Centuriate Assembly Ground"
room in Campus Martius (world/batch_campus_martius_data.py) via its
unused "west" exit - the correct real spot for this: that room is
explicitly described as open muster ground *outside the Pomerium*
(the sacred boundary of the city proper), immediately south of the
already-built Mausoleum of Augustus, which historically sat near the
actual Aurelian Wall's eventual line. Named "Porta Flaminia" after
the real gate the real Via Flaminia departed from - the actual
historical road north out of Rome toward Cisalpine Gaul and,
eventually, the Rhine frontier.

Run this file directly (`python3 world/batch_wall_gate_data.py`) to
validate before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


room(
    "wall_city_side",
    "Inside the Gate - City Side",
    """|wOrdinary Roman streets give way here|n to something more deliberate - paving stones give up their usual chaos of shopfronts and insulae for a wide, cleared approach, the great grey mass of the Porta Flaminia rising ahead. |YGuards stand posted at proper intervals|n rather than the loose watchfulness of the streets behind you; this close to the wall, Rome starts taking its own boundary seriously.""",
    "wall_gate",
)

room(
    "wall_gatehouse",
    "The Gatehouse Interior",
    """|wA cramped guardroom|n built into the wall's own thickness - a watch log chained to a writing table, a few narrow cots, a brazier that never quite goes cold. |YEvery traveler through the Porta Flaminia gets logged here|n, in principle if not always in diligent practice; the log itself is thick with entries in a dozen different hands.""",
    "wall_gate",
)

room(
    "wall_gate_passage",
    "The Porta Flaminia",
    """|wA genuine gate|n, iron-bound oak thick enough to stop a battering ram for at least a little while, set into a wall broad enough to walk through rather than merely past. |YCarved above the archway|n, weathered but still legible, a dedication names this the northern gate of Rome - the one every road to Cisalpine Gaul, and everything beyond it, actually starts from.""",
    "wall_gate",
)

room(
    "wall_walkway_east",
    "Atop the Wall - Facing the City",
    """|YA stone walkway|n runs along the wall's own crest, wide enough for two guards to pass each other without breaking stride. Looking back over the parapet, |wall of Rome spreads out below|n - rooftops, smoke, the distant gilded roofline of the Capitoline catching whatever light the day has to offer. From up here the city reads as one single, continuous thing, in a way it never quite does from inside it.""",
    "wall_gate",
)

room(
    "wall_walkway_west",
    "Atop the Wall - Facing Outward",
    """|YThe same walkway|n, a stretch further along, and the view has already changed completely. |wRome falls away behind|n and ahead there's only open country - fields, then scrub, then the dark suggestion of forest at the very edge of sight. The difference between the two views, from the same stretch of wall, says more about the empire's edge than either view could say alone.""",
    "wall_gate",
)

room(
    "wall_watchtower",
    "The Watchtower",
    """|wA squat stone tower|n rising a full story above the wall itself, built for exactly one purpose - seeing trouble before it arrives. |YA lookout keeps a genuinely careful watch|n over the northern approach; nothing about their posture here is the relaxed, routine boredom of the gatehouse below.""",
    "wall_gate",
)

room(
    "wall_outside_shadow",
    "Outside the Gate - the Wall's Shadow",
    """|wThe gate falls behind you|n, and Rome's noise thins out almost immediately - the shouting of the markets, the constant background hum of a few hundred thousand people, all of it dropping to something closer to quiet. |YThe wall's own long shadow still falls across this stretch of ground|n most of the day; whatever's ahead, it hasn't started yet, not quite.""",
    "wall_gate",
)

room(
    "wall_road_start",
    "The Road's True Start",
    """|wHere, finally, Rome is genuinely behind you.|n The wall's shadow doesn't reach this far; the road ahead runs north in a long, straight, deliberate Roman line, engineered the way every real Roman road is engineered - built to last, built to be marched on. |YA single worn milestone|n stands at the road's edge, the first of what will be many.""",
    "wall_gate",
)

ROOM_COUNT_EXPECTED = 8


LINKS = [
    ("existing_assembly_ground", "west", "wall_city_side", "east"),
    ("wall_city_side", "north", "wall_gatehouse", "south"),
    ("wall_gatehouse", "up", "wall_walkway_east", "down"),
    ("wall_walkway_east", "west", "wall_walkway_west", "east"),
    ("wall_walkway_west", "up", "wall_watchtower", "down"),
    ("wall_gate_passage", "west", "wall_outside_shadow", "east"),
    ("wall_outside_shadow", "west", "wall_road_start", "east"),
]

# The gate itself is a real door (world.doors.DescriptiveDoor), linked
# between wall_city_side and wall_gate_passage - handled separately
# in setup_wall_gate_live.py rather than through the plain LINKS list
# above, since a door needs its two sides' db.return_exit set to each
# other (see world/doors.py's module docstring).
DOOR_LINK = ("wall_city_side", "west", "wall_gate_passage", "east")


NPCS = [
    (
        "wall_city_side", "a gate guard", "static",
        "Standing a proper, disciplined post rather than the looser "
        "watchfulness of an ordinary street corner - this close to "
        "the wall, Rome takes its own boundary seriously, and so does "
        "she.",
        None,
    ),
    (
        "wall_gatehouse", "the watch-captain", "static",
        "Older than the guards under him, and visibly less interested "
        "in small talk than in the watch log open on the table in "
        "front of him - every name that passes through the Porta "
        "Flaminia is, at least in theory, his responsibility.",
        None,
    ),
    (
        "wall_gate_passage", "a gate guard", "static",
        "Posted directly at the gate itself, close enough to the "
        "actual door to be the first and last word on whether it "
        "opens for anyone in particular.",
        None,
    ),
    (
        "wall_watchtower", "a lookout", "static",
        "Watching the northern approach with a careful, unhurried "
        "attention that has nothing routine about it - whatever "
        "she's watching for, she takes the possibility of it "
        "seriously.",
        None,
    ),
]


OBJECTS = [
    (
        "wall_gatehouse", "a watch log",
        "A heavy, chained ledger, its pages thick with entries in a "
        "dozen different hands - names, dates, and the occasional "
        "terse note from a guard who clearly didn't trust whoever "
        "they were logging."
    ),
    (
        "wall_road_start", "a worn milestone",
        "A stone marker, weathered but legible, the first of a long "
        "line that will mark this road's entire length. |wRome, it "
        "notes plainly, is now one mile behind.|n"
    ),
]


ECHOES = {
    "wall_walkway_west": [
        "|wWind moves steadily along the open wall-top here.|n",
        "|cA hawk circles lazily somewhere beyond the wall.|n",
    ],
    "wall_road_start": [
        "|wThe road runs north in a long, straight line, exactly as far as you can see.|n",
    ],
}


def _reverse_dir(d):
    pairs = {
        "north": "south", "south": "north",
        "east": "west", "west": "east",
        "up": "down", "down": "up",
        "northeast": "southwest", "southwest": "northeast",
        "northwest": "southeast", "southeast": "northwest",
    }
    return pairs.get(d)


def validate():
    errors = []

    all_keys = set(ROOMS.keys()) | {"existing_assembly_ground"}

    if len(ROOMS) != ROOM_COUNT_EXPECTED:
        errors.append("Expected %d rooms, got %d" % (ROOM_COUNT_EXPECTED, len(ROOMS)))

    names = [r["name"] for r in ROOMS.values()]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        errors.append("Duplicate room names: %s" % dupes)

    all_links = LINKS + [DOOR_LINK]

    for a, da, b, db in all_links:
        if a not in all_keys:
            errors.append("Link references unknown room: %s" % a)
        if b not in all_keys:
            errors.append("Link references unknown room: %s" % b)
        if _reverse_dir(da) is None or _reverse_dir(db) is None:
            errors.append("Unrecognized direction in link %s" % ((a, da, b, db),))

    used_directions = {}
    for a, da, b, db in all_links:
        used_directions.setdefault(a, []).append(da)
        used_directions.setdefault(b, []).append(db)
    for room_key, dirs in used_directions.items():
        seen = set()
        for d in dirs:
            if d in seen:
                errors.append("Room '%s' has a duplicate '%s' exit" % (room_key, d))
            seen.add(d)

    adjacency = {}
    for a, da, b, db in all_links:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    visited = set()
    queue = ["existing_assembly_ground"]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                queue.append(neighbor)

    unreachable = set(ROOMS.keys()) - visited
    if unreachable:
        errors.append("Unreachable rooms: %s" % unreachable)

    for entry in NPCS:
        room_key = entry[0]
        if room_key not in all_keys:
            errors.append("NPC references unknown room: %s" % room_key)
    for room_key, _, _ in OBJECTS:
        if room_key not in all_keys:
            errors.append("Object references unknown room: %s" % room_key)
    for room_key in ECHOES:
        if room_key not in all_keys:
            errors.append("Echo references unknown room: %s" % room_key)

    return errors


if __name__ == "__main__":
    print("Loaded %d new rooms (attaches to existing 'The Centuriate Assembly Ground')." % len(ROOMS))
    print("Loaded %d links (+1 door link), %d NPCs, %d objects, %d rooms with echoes." % (
        len(LINKS), len(NPCS), len(OBJECTS), len(ECHOES)
    ))
    errs = validate()
    if errs:
        print("\nVALIDATION FAILED (%d errors):" % len(errs))
        for e in errs:
            print(" -", e)
    else:
        print("\nValidation passed: no duplicate names, no exit collisions, "
              "full connectivity, all references resolve.")
