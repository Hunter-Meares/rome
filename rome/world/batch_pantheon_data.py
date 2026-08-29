"""
The Pantheon - a validated, in-memory description of every room, exit,
NPC, and object before anything touches the live database. Same
pattern as the Forum/Subura/Trajan's Market builds.

Attaches to the real, already-built "Via Triumphalis" room (#664) via
its unused "north" exit - its existing desc already says the road
"curves north, toward districts of the city not [yet built]," so this
isn't just a free direction, it's the specific one the room's own
flavor text already promised.

Deliberately small and self-contained per the original plan - the
Pantheon's real appeal is the oculus and the "dedicated to all the
gods" contrast with every single-deity temple built so far, not scale.

Run this file directly (`python3 batch_pantheon_data.py`) to validate
before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


room(
    "pantheon_approach",
    "Approach to the Pantheon",
    """|YA columned portico|n rises ahead, granite shafts taller than anything on this stretch of road, supporting a triangular pediment cut with an inscription in deep, formal lettering. |wUnlike the Forum's temples|n, crowded shoulder to shoulder with their neighbors, this one stands with real room to breathe around it - a building confident enough not to need company.""",
    "pantheon",
)

room(
    "pantheon_rotunda",
    "The Pantheon - The Rotunda",
    """|YThe dome overhead is almost impossible to look away from|n - a perfect, unsupported half-sphere of concrete, coffered in receding squares that draw the eye up and up toward a single circular opening at the very peak. |cThe oculus|n - the dome's open eye - lets in a shaft of daylight that swings slowly across the floor as the hours pass, the only light this vast round room has or needs. |wNo interior columns break the space at all|n; the dome simply holds itself up, exactly as it's held itself up for longer than anyone present has been alive.""",
    "pantheon",
)

room(
    "pantheon_niche_east",
    "Eastern Niche",
    """|wA deep niche|n set into the rotunda's curving wall, its own small vaulted ceiling distinct from the great dome outside it. A minor god's statue stands here in permanent, quiet shadow - not the building's main devotion, but not forgotten either.""",
    "pantheon",
)

room(
    "pantheon_niche_west",
    "Western Niche",
    """|wA second niche|n, mirroring the eastern one across the rotunda, holding a different god's likeness in the same respectful half-light. Small offerings - a coin, a sprig of dried herb - collect on the ledge at the statue's feet regardless of which god the rotunda's altar is technically for.""",
    "pantheon",
)

room(
    "pantheon_altar",
    "The Altar of All Gods",
    """|YThe rotunda's main altar|n, positioned directly beneath the dome's highest point - on a clear day, the oculus's shaft of light falls almost exactly here at midday, whether by design or by a coincidence nobody's willing to call accidental. |wUnlike every other temple built so far|n, no single god's name is carved above this altar. It is dedicated, plainly, to all of them at once.""",
    "pantheon",
)

room(
    "pantheon_side_chamber",
    "Priest's Chamber",
    """|wA small, plain room|n behind the altar, entirely lacking the rotunda's grandeur - a writing desk, a shelf of records, a narrow cot. Whoever tends a temple built for every god at once apparently doesn't need much room of their own to do it.""",
    "pantheon",
)

ROOM_COUNT_EXPECTED = 6


LINKS = [
    ("existing_via_triumphalis", "north", "pantheon_approach", "south"),
    ("pantheon_approach", "north", "pantheon_rotunda", "south"),
    ("pantheon_rotunda", "east", "pantheon_niche_east", "west"),
    ("pantheon_rotunda", "west", "pantheon_niche_west", "east"),
    ("pantheon_rotunda", "north", "pantheon_altar", "south"),
    ("pantheon_altar", "east", "pantheon_side_chamber", "west"),
]


NPCS = [
    (
        "pantheon_rotunda", "the Pantheon's priest", "static",
        "A calm, unhurried man in plain temple robes, entirely without "
        "the elaborate ritual bearing of the Capitoline's Flamen - "
        "tending an altar built for every god at once apparently calls "
        "for a lighter touch than tending one built for a single "
        "demanding king of the sky.",
        None,
    ),
]


OBJECTS = [
    (
        "pantheon_rotunda", "the oculus",
        "A perfect circular opening at the dome's peak, open straight "
        "to the sky - no glass, no covering, nothing between this room "
        "and the weather. Rain falls straight through it during a storm "
        "and simply evaporates off the floor afterward; sun swings "
        "across the coffered ceiling in a slow arc through the day. It "
        "is, by a wide margin, the most talked-about single feature of "
        "any building in the city."
    ),
    (
        "pantheon_approach", "the dedicatory inscription",
        "Deep-cut lettering across the portico's pediment, formal enough "
        "that even those who can't read Latin quickly recognize it as "
        "an inscription of real importance - the building's dedication, "
        "naming who raised it, carved to outlast every person who ever "
        "reads it."
    ),
]


ECHOES = {
    "pantheon_rotunda": [
        "|cA shaft of daylight through the oculus shifts slightly across the floor.|n",
        "|wA pigeon's wingbeats echo oddly off the dome's curve overhead.|n",
        "|YVoices in the rotunda carry strangely, the dome bending every sound.|n",
        "|cA few drops of rain drift straight down through the oculus, evaporating before they land.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_via_triumphalis"}

    if len(ROOMS) != ROOM_COUNT_EXPECTED:
        errors.append("Expected %d rooms, got %d" % (ROOM_COUNT_EXPECTED, len(ROOMS)))

    names = [r["name"] for r in ROOMS.values()]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        errors.append("Duplicate room names: %s" % dupes)

    for a, da, b, db in LINKS:
        if a not in all_keys:
            errors.append("Link references unknown room: %s" % a)
        if b not in all_keys:
            errors.append("Link references unknown room: %s" % b)
        if _reverse_dir(da) is None or _reverse_dir(db) is None:
            errors.append("Unrecognized direction in link %s" % ((a, da, b, db),))

    used_directions = {}
    for a, da, b, db in LINKS:
        used_directions.setdefault(a, []).append(da)
        used_directions.setdefault(b, []).append(db)
    for room_key, dirs in used_directions.items():
        seen = set()
        for d in dirs:
            if d in seen:
                errors.append("Room '%s' has a duplicate '%s' exit" % (room_key, d))
            seen.add(d)

    adjacency = {}
    for a, da, b, db in LINKS:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    visited = set()
    queue = ["existing_via_triumphalis"]
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
    print("Loaded %d new rooms (attaches to existing room #664, 'Via Triumphalis')." % len(ROOMS))
    print("Loaded %d links, %d NPCs, %d objects, %d rooms with echoes." % (
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
