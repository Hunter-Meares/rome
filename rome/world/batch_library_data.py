"""
The Bibliotheca Ulpia (Library of Rome) - a validated, in-memory
description of every room, exit, NPC, and object before anything
touches the live database. Same pattern as batch_trajan_market_data.py
/ batch_pantheon_data.py: data + a standalone validator, no Django
needed, run before a single database write happens.

Attaches to the real, already-built "Market Rooftop Terrace" room
(part of Trajan's Market, world/batch_trajan_market_data.py) via its
unused "down" exit - the terrace's own flavor text already frames it
as the market's highest point looking down over "the whole market
complex and a real stretch of the city," and the real Bibliotheca
Ulpia sat immediately behind Trajan's Market, flanking Trajan's Column
inside the Forum of Trajan. Historically the two complexes were close
enough to be considered one project (same architect, same emperor,
built together) - so unlike every other zone built so far, this one
needs only the shortest possible "journey," not a real road.

--------------------------------------------------------------------
GEOGRAPHIC-ACCURACY SCALE MODEL (first use of this system - reused
and extended for every zone that follows, including retrofits to
already-built connections):

Real approximate straight-line distances anchor a relative, not
literal, scale. There is no fixed room-per-meter ratio, because the
existing 407-room map was never built to one - the goal is that
FARTHER real pairs get proportionally MORE connecting rooms than
CLOSER real pairs, calibrated against connections that already exist:

  - Forum <-> Trajan's Market (already built, single "west" exit,
    room #760): real distance ~300-400m. Treated as the short end of
    the scale - already adequately represented by 0 extra rooms.
  - Trajan's Market <-> Bibliotheca Ulpia (this batch): real distance
    ~75-150m (same forum complex) - shorter than the Forum/Trajan's
    gap above, so it gets LESS than that gap's already-adequate zero
    rooms would suggest is a floor. One single connector room
    ("library_approach") is used anyway, purely because a same-tick
    transition between two full zones with no threshold at all reads
    strangely in play - this is the floor value for "any real gap
    that isn't literally the same room," not a distance-derived
    figure.
  - Colosseum/Forum <-> Pantheon's real historical site in the Campus
    Martius: real distance ~1.8-2km, several times longer than either
    gap above. The Pantheon is CURRENTLY attached with a single
    unused exit at room #664 ("Via Triumphalis") - this is the clear
    case of an already-built connection that is far too short for its
    real distance, and is the first retrofit target under the new
    standing requirement. Not resolved in this batch; flagged here so
    the room-count logic stays consistent when that road is built.

This batch's own connector (1 room) is therefore calibrated as "the
floor," not "a full road" - the Library is the one location in the
whole 5-part expansion proposal that is genuinely close enough in
real life not to need one.
--------------------------------------------------------------------

Run this file directly (`python3 batch_library_data.py`) to validate
before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ------------------------------------------------------------------
# Approach (1 room) - the geographic-accuracy connector, see docstring
# ------------------------------------------------------------------

room(
    "library_approach",
    "Colonnaded Walk to the Libraries",
    """|wA short covered colonnade|n curls down and around from the market's rooftop terrace, the noise of commerce fading fast behind you. Ahead, past the last column, a different kind of building entirely comes into view - lower, quieter, no shopfronts anywhere in sight. |YA carved marker names the buildings ahead as the twin libraries of the Forum of Trajan|n, built alongside the market in the same breath, by the same emperor's hand.""",
    "library",
)

# ------------------------------------------------------------------
# Central plaza + column (4 rooms)
# ------------------------------------------------------------------

room(
    "library_entrance_plaza",
    "Plaza of the Twin Libraries",
    """|YTwo matching buildings face each other|n across an open plaza, identical in scale and ambition, distinguished only by the language carved above each entrance. |wOne reads in Latin; the other in Greek|n - Rome's official position, built in stone, that a proper library needs both. Between them, visible past the plaza's far edge, a column rises far higher than either roofline.""",
    "library",
)

room(
    "library_column_courtyard",
    "Trajan's Column Courtyard",
    """|YThe column dominates everything here|n - a single unbroken shaft of marble, carved in a continuous spiraling frieze from base to capital, climbing higher than either library flanking it. |wSmall figures in relief|n - legionaries, engineers, a river god, an emperor addressing his troops - march upward around the column in an unbroken procession that no one standing at ground level can follow past the first few turns.""",
    "library",
)

room(
    "library_column_balcony",
    "Column Viewing Balcony",
    """|wA narrow balcony|n projects from the library's upper floor, built for exactly one purpose: bringing a viewer close enough to actually see the column's higher carvings, which vanish into illegible detail from the courtyard below. |YFrom here|n, a particular scene comes into focus - a bridge under construction, a detail no one at street level has ever properly appreciated.""",
    "library",
)

room(
    "library_philosophers_court",
    "The Philosophers' Court",
    """|wA small open courtyard|n behind the column, benches arranged in loose facing rows beneath a scattering of plane trees. |YRaised voices carry from here at most hours|n - a debate over a text no one in the courtyard actually agrees on, conducted with more heat than the subject probably warrants.""",
    "library",
)

# ------------------------------------------------------------------
# Latin wing (3 rooms)
# ------------------------------------------------------------------

room(
    "library_latin_hall",
    "The Latin Library - Main Hall",
    """|YRow after row of cylindrical cubicula|n line the walls, each slot holding a tightly rolled scroll with its title tag hanging free for easy reading. |wThe hall is built entirely of stone and faced marble|n, a deliberate precaution - papyrus and fire have never been friends, and this collection is not meant to be replaceable.""",
    "library",
)

room(
    "library_latin_reading_room",
    "Latin Reading Room",
    """|wLong tables|n run the length of this quieter side-room, each lit by a high clerestory window rather than an open flame - the same fire precaution as the main hall, extended to wherever anyone actually sits and reads. |YA few readers|n work through unrolled scrolls in near-total silence, weights on each end holding the papyrus flat.""",
    "library",
)

room(
    "library_latin_archive",
    "Latin Scroll Archive",
    """|wDeeper shelving|n than the main hall's public collection, older scrolls and duplicate copies packed in tighter rows. |YA numbered system|n on each shelf face lets the staff find a specific work quickly - a small miracle of organization for a room holding this much material.""",
    "library",
)

# ------------------------------------------------------------------
# Greek wing (3 rooms)
# ------------------------------------------------------------------

room(
    "library_greek_hall",
    "The Greek Library - Main Hall",
    """|YA mirror of the Latin hall across the plaza|n, down to the same stone construction and the same cylindrical cubicula - only the script on every scroll tag differs. |wRome's own literature is younger than Greece's by centuries|n, and this hall's far larger collection is a quiet acknowledgment of exactly that.""",
    "library",
)

room(
    "library_greek_reading_room",
    "Greek Reading Room",
    """|wA reading room built to the Latin wing's exact specifications|n, long tables and clerestory light included, though the readers here skew toward a different crowd - tutors, visiting scholars, and more than one senator's son working through a text his father can no longer help him with.""",
    "library",
)

room(
    "library_greek_archive",
    "Greek Scroll Archive",
    """|wThe Greek wing's deeper stock|n, philosophy and history packed shelf to shelf with medical and mathematical treatises few outside this room ever ask to see. |YA faint must hangs in the air|n - even careful stone construction can't fully stop centuries of papyrus from slowly aging.""",
    "library",
)

room(
    "library_restricted_archive",
    "The Restricted Archive",
    """|YA locked vault|n behind the Latin archive's deepest shelving, holding material the library doesn't display to casual readers - imperial correspondence, sensitive census records, and at least one shelf nobody without real authority is permitted to even name. |wA single lamp burns here|n, carefully, and only when someone with a reason to be here actually is.""",
    "library",
)

# ------------------------------------------------------------------
# Service wing (4 rooms)
# ------------------------------------------------------------------

room(
    "library_scriptorium",
    "The Scriptorium",
    """|wA working room|n, nothing like the hushed reading rooms above - a dozen copyists bent over slanted desks, each producing a fresh duplicate of some aging original one careful character at a time. |YThe library's whole collection exists because of exactly this unglamorous, repetitive labor|n, performed daily by people whose names will never appear on any scroll they copy.""",
    "library",
)

room(
    "library_head_librarian_office",
    "Office of the Chief Librarian",
    """|wA well-appointed office|n, considerably grander than the scriptorium next door - befitting the *procurator bibliothecarum*, the imperial post responsible for both libraries at once. |YShelves here hold not scrolls but records|n: acquisition lists, copyist assignments, and a running account of exactly what the collection is still missing.""",
    "library",
)

room(
    "library_map_room",
    "The Map Room",
    """|YA single enormous map covers the far wall|n, rendered in inlaid stone and pigment rather than ink - the known world as Rome currently understands it, provinces and roads picked out in careful detail. |wVisitors linger here longer than anywhere else in the building|n, tracing routes with a finger toward places they'll likely never actually see.""",
    "library",
)

room(
    "library_delivery_room",
    "Scroll Receiving Room",
    """|wA plain back room|n, crates and satchels of newly arrived scrolls stacked awaiting inspection before they're either shelved or handed to the scriptorium for copying. |YThe least dignified room in either library|n, and arguably the one that keeps both of them actually growing.""",
    "library",
)

ROOM_COUNT_EXPECTED = 16


# ============================================================
# LINKS
# ============================================================

LINKS = [
    ("existing_market_rooftop_terrace", "down", "library_approach", "up"),
    ("library_approach", "north", "library_entrance_plaza", "south"),

    ("library_entrance_plaza", "east", "library_latin_hall", "west"),
    ("library_entrance_plaza", "west", "library_greek_hall", "east"),
    ("library_entrance_plaza", "north", "library_column_courtyard", "south"),
    ("library_entrance_plaza", "down", "library_scriptorium", "up"),

    ("library_column_courtyard", "up", "library_column_balcony", "down"),
    ("library_column_courtyard", "north", "library_philosophers_court", "south"),

    ("library_latin_hall", "north", "library_latin_reading_room", "south"),
    ("library_latin_hall", "east", "library_latin_archive", "west"),
    ("library_latin_archive", "north", "library_restricted_archive", "south"),

    ("library_greek_hall", "north", "library_greek_reading_room", "south"),
    ("library_greek_hall", "west", "library_greek_archive", "east"),

    ("library_scriptorium", "east", "library_head_librarian_office", "west"),
    ("library_scriptorium", "west", "library_map_room", "east"),
    ("library_scriptorium", "south", "library_delivery_room", "north"),
]


# ============================================================
# NPCS
# ============================================================
# Each entry: (room_key, name, desc, kind, extra)
#   kind "static"    - plain DefaultCharacter, stays put
#   kind "wander"    - DefaultCharacter + WanderingNPC script
#   kind "merchant"  - NPCMerchant, extra is a list of prototype keys

NPCS = [
    (
        "library_head_librarian_office", "the Chief Librarian", "static",
        "A precise, unhurried woman who holds the imperial post of "
        "procurator bibliothecarum - responsible, on paper, for every "
        "scroll in both buildings. She speaks about the collection the "
        "way a general might speak about an army: with real pride, and "
        "real awareness of exactly what it's still missing.",
        None,
    ),
    (
        "library_scriptorium", "a copyist", "static",
        "A copyist hunched over a slanted desk, stylus moving in short, "
        "practiced strokes across fresh papyrus - a duplicate of some "
        "aging scroll taking shape one careful character at a time, with "
        "no sign of looking up any time soon.",
        None,
    ),
    (
        "library_latin_reading_room", "a Latin scholar", "static",
        "An older man working steadily through an unrolled scroll, two "
        "weights holding it flat, lips moving faintly as he reads - a "
        "habit that's clearly outlasted whatever reason he originally "
        "had for reading aloud in the first place.",
        None,
    ),
    (
        "library_greek_reading_room", "a visiting tutor", "static",
        "A tutor working through a Greek text with the focused urgency "
        "of someone preparing tomorrow's lesson rather than reading for "
        "its own sake, occasionally muttering a phrase under his breath "
        "as if testing how it will sound taught aloud.",
        None,
    ),
    (
        "library_philosophers_court", "a philosopher", "wander",
        "Whoever's currently holding forth in the Philosophers' Court - "
        "the debate changes daily, the volume never does, and the actual "
        "resolution of any given argument seems to matter less than the "
        "arguing itself.",
        ["library_philosophers_court", "library_column_courtyard", "library_entrance_plaza"],
    ),
    (
        "library_delivery_room", "a delivery clerk", "static",
        "A clerk checking a fresh crate of scrolls against a manifest, "
        "sorting each one toward either the shelves or the scriptorium "
        "next door depending on whether the library already owns a "
        "usable copy.",
        None,
    ),
]


# ============================================================
# OBJECTS - lookable scenery, get:false() locked
# ============================================================

OBJECTS = [
    (
        "library_column_courtyard", "Trajan's Column",
        "A single unbroken marble shaft, carved from base to capital "
        "with a continuous spiraling frieze depicting the emperor's "
        "campaigns - legionaries building bridges, addressing troops, "
        "crossing rivers, in a procession that climbs higher than "
        "anyone standing here can actually follow with the naked eye."
    ),
    (
        "library_map_room", "the great map",
        "An enormous map of the known world, rendered in inlaid stone "
        "and pigment rather than ink - provinces, roads, and rivers "
        "picked out in careful, deliberate detail. Whoever commissioned "
        "it clearly intended it to outlast every scroll in the building "
        "around it."
    ),
    (
        "library_restricted_archive", "the sealed shelf",
        "A single shelf near the back of the vault, its scrolls bound "
        "with cord and wax seals rather than left loose like everything "
        "else in the archive - whatever they contain, someone decided "
        "long ago that reading them shouldn't be casual."
    ),
]


# ============================================================
# ECHOES
# ============================================================

ECHOES = {
    "library_scriptorium": [
        "|wA stylus scratches steadily across fresh papyrus.|n",
        "|YA copyist mutters a mis-copied line and starts the passage over.|n",
    ],
    "library_philosophers_court": [
        "|YAn argument rises briefly in volume before subsiding again.|n",
        "|wSomeone quotes a line no one else in the courtyard quite agrees with.|n",
        "|cA bench creaks as another listener settles in to watch the debate.|n",
    ],
    "library_column_courtyard": [
        "|wA visitor tilts their head back, trying and failing to follow the frieze past the first few turns.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_market_rooftop_terrace"}

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
    queue = ["existing_market_rooftop_terrace"]
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
        if entry[2] == "wander":
            for wr in entry[4]:
                if wr not in all_keys:
                    errors.append("Wander room unknown: %s" % wr)
    for room_key, _, _ in OBJECTS:
        if room_key not in all_keys:
            errors.append("Object references unknown room: %s" % room_key)
    for room_key in ECHOES:
        if room_key not in all_keys:
            errors.append("Echo references unknown room: %s" % room_key)

    return errors


if __name__ == "__main__":
    print("Loaded %d new rooms (attaches to existing Trajan's Market Rooftop Terrace)." % len(ROOMS))
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
