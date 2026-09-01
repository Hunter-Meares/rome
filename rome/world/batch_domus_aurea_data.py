"""
The Domus Aurea (Nero's Golden House) - a validated, in-memory
description of every room, exit, NPC, and object before anything
touches the live database. Same pattern as every zone before it:
data + a standalone validator, no Django needed, run before a single
database write happens.

Attaches to the real, already-built "The Meta Sudans" room (#658, the
Colosseum's own entry-hub plaza) via its unused "south" exit - Meta
Sudans already has real roads branching west (Via Sacra, to the
Forum) and east (Via Triumphalis, to the Pantheon/Campus Martius);
adding a third road south continues that same hub design rather than
introducing a new pattern.

Geographic-accuracy scale (see world/batch_library_data.py's docstring
for the full model): the real Domus Aurea's surviving remains sit on
the Oppian Hill only a few hundred meters from the Colosseum - Nero's
palace grounds are, historically, the *same ground* the Colosseum was
later built on (the palace's artificial lake was drained and filled
to build the amphitheater itself; the palace's own Colossus statue is
where "Colosseum" gets its name). This is the single shortest gap of
anything in the whole 5-part expansion - shorter even than the
Library's gap to Trajan's Market - so it gets the same floor value:
one connector room, not a real road.

Run this file directly (`python3 batch_domus_aurea_data.py`) to
validate before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ------------------------------------------------------------------
# Approach (1 room)
# ------------------------------------------------------------------

room(
    "domus_aurea_approach",
    "The Buried Slope",
    """|wA short rise|n climbs away from the plaza, the ground underfoot
    oddly uneven - packed earth and rubble rather than honest paving,
    as though something else were filled in beneath it. |YAn old,
    weathered marker|n still names what stood here before the fill: the
    Golden House, Nero's own palace, most of it deliberately buried
    within a few years of his death and never fully reclaimed since.""",
    "domus_aurea",
)

# ------------------------------------------------------------------
# Entrance wing (4 rooms)
# ------------------------------------------------------------------

room(
    "domus_aurea_vestibule",
    "The Grand Vestibule",
    """|YA vast entrance hall|n, half its original height lost to the
    fill packed in around it, forcing anyone inside to stoop where a
    Roman of Nero's own court would have walked upright. |wA colossal
    bronze statue once stood in the courtyard just outside these
    walls|n - moved away and repurposed generations ago, though the
    building whose name it eventually gave still stands close enough
    to hear from here.""",
    "domus_aurea",
)

room(
    "domus_aurea_colossus_court",
    "Court of the Colossus",
    """|wAn open court|n, empty now where a genuinely enormous bronze
    figure once stood - Nero, cast in the guise of the sun god, tall
    enough to be visible from well outside the palace grounds. |YThe
    statue is long gone|n, relocated and eventually reworked into
    something else entirely, but the plinth marks where thirty meters
    of solid bronze once dominated this exact spot.""",
    "domus_aurea",
)

room(
    "domus_aurea_octagonal_room",
    "The Octagonal Hall",
    """|YAn eight-sided chamber|n unlike anything else in the palace,
    ringed with smaller rooms opening off each face - engineering this
    ambitious hasn't been attempted again since. |wCourt rumor always
    insisted the dome overhead once turned slowly, like the sky
    itself|n; nothing here confirms or denies it, and no one alive
    actually saw it happen.""",
    "domus_aurea",
)

room(
    "domus_aurea_dome_chamber",
    "Beneath the Dome",
    """|wA narrow service space|n tucked directly under the octagonal
    hall's famous dome, thick with the smell of old rope and worked
    timber. |YWhatever mechanism the rotation rumor depends on|n, if it
    ever existed at all, would have to have lived in a room exactly
    like this one - though nothing resembling working machinery
    remains to settle the question either way.""",
    "domus_aurea",
)

# ------------------------------------------------------------------
# Grotto / fresco wing (4 rooms)
# ------------------------------------------------------------------

room(
    "domus_aurea_grotto_corridor",
    "The Painted Corridor",
    """|YWalls covered edge to edge in painted fantasy|n - garlands,
    imaginary creatures, architecture that couldn't actually stand,
    all rendered in colors still startling despite everything the
    burial did to this place. |wFuture generations who eventually dig
    their way back in here|n will apparently find this exact style
    strange enough to invent a whole new word for it.""",
    "domus_aurea",
)

room(
    "domus_aurea_nymphaeum",
    "The Nymphaeum",
    """|cA fountain grotto|n, shell-encrusted niches lining a room built
    entirely around the sound and sight of moving water. |wThe fountain
    itself has long since gone dry|n, but the shells and colored glass
    set into the walls still catch what little light reaches this deep
    into the buried complex.""",
    "domus_aurea",
)

room(
    "domus_aurea_hidden_fresco_room",
    "A Half-Buried Chamber",
    """|wA smaller room|n, partially collapsed, one whole wall still
    bearing a fresco in near-perfect condition under a protective layer
    of packed earth. |YSomeone with steadier nerves than sense|n has
    scratched their own name into the plaster near the doorway, small
    and almost apologetic, next to artwork centuries older than they
    are.""",
    "domus_aurea",
)

room(
    "domus_aurea_collapsed_wing",
    "The Collapsed Wing",
    """|rPart of the ceiling has come down entirely here|n, rubble and
    fallen plaster blocking what was clearly once a much larger room.
    |wDaylight leaks through a crack far overhead|n, the only light in
    this whole stretch of corridor that isn't carried in by hand.""",
    "domus_aurea",
)

# ------------------------------------------------------------------
# Living wing (5 rooms)
# ------------------------------------------------------------------

room(
    "domus_aurea_banquet_hall",
    "The Great Banquet Hall",
    """|YA hall built for feasts that were also, unmistakably, political
    theater|n - Nero's guests dined here under the same painted fantasy
    covering every other room in the complex, reclining on couches
    arranged for maximum visibility of exactly who sat closest to the
    host.""",
    "domus_aurea",
)

room(
    "domus_aurea_private_baths",
    "Nero's Private Baths",
    """|wA small private bathing suite|n, modest by comparison to the
    grand public baths built elsewhere in the city, but entirely
    Nero's own - no crowds, no strangers, water piped in specifically
    for a single household's use.""",
    "domus_aurea",
)

room(
    "domus_aurea_pleasure_garden",
    "The Pleasure Gardens",
    """|gWhat was once a genuinely enormous landscaped garden|n,
    reduced now to a single buried courtyard - trees, fountains, and
    grazing animals reportedly filled these grounds in Nero's day,
    an artificial countryside built inside the city itself.""",
    "domus_aurea",
)

room(
    "domus_aurea_lake_shore",
    "Shore of the Drained Lake",
    """|cA long, low room|n that once opened directly onto an artificial
    lake at the heart of the palace grounds - drained and filled not
    long after Nero's death, the ground leveled over for an amphitheater
    the whole city would eventually come to know by an entirely
    different name.""",
    "domus_aurea",
)

room(
    "domus_aurea_private_chambers",
    "Nero's Private Chambers",
    """|YA personal chamber|n, smaller and less performative than the
    reception spaces elsewhere in the complex - the actual private life
    of a man whose public one was built, quite literally, on an
    unprecedented scale.""",
    "domus_aurea",
)

# ------------------------------------------------------------------
# Service wing (4 rooms)
# ------------------------------------------------------------------

room(
    "domus_aurea_treasury",
    "The Looted Treasury",
    """|wA long storage room|n, empty shelving and wall niches the only
    evidence of what it once held - Greek statuary and artwork gathered
    from across the provinces, most of it stripped out and redistributed
    generations ago.""",
    "domus_aurea",
)

room(
    "domus_aurea_servant_wing",
    "Servants' Wing",
    """|wA plain, cramped wing|n, utterly unlike the grandeur everywhere
    else in the palace - the household staff who actually kept this
    entire complex running lived in rooms barely large enough to lie
    down in.""",
    "domus_aurea",
)

room(
    "domus_aurea_buried_passage",
    "A Buried Passage",
    """|rA half-collapsed corridor|n, packed rubble narrowing the
    passage to barely shoulder-width in places - foundation fill from
    whatever was eventually built over this section of the palace,
    pressing down from directly above.""",
    "domus_aurea",
)

room(
    "domus_aurea_caretaker_room",
    "The Caretaker's Room",
    """|wA small, lived-in room|n, entirely out of place among the ruins
    around it - a cot, a lamp, a table with a half-eaten meal. Someone
    is clearly down here often enough to have made themselves
    genuinely comfortable.""",
    "domus_aurea",
)

ROOM_COUNT_EXPECTED = 18


# ============================================================
# LINKS
# ============================================================

LINKS = [
    ("existing_meta_sudans", "south", "domus_aurea_approach", "north"),
    ("domus_aurea_approach", "south", "domus_aurea_vestibule", "north"),

    ("domus_aurea_vestibule", "east", "domus_aurea_colossus_court", "west"),
    ("domus_aurea_vestibule", "south", "domus_aurea_octagonal_room", "north"),
    ("domus_aurea_octagonal_room", "up", "domus_aurea_dome_chamber", "down"),

    ("domus_aurea_octagonal_room", "west", "domus_aurea_grotto_corridor", "east"),
    ("domus_aurea_grotto_corridor", "south", "domus_aurea_nymphaeum", "north"),
    ("domus_aurea_grotto_corridor", "west", "domus_aurea_hidden_fresco_room", "east"),
    ("domus_aurea_nymphaeum", "west", "domus_aurea_collapsed_wing", "east"),

    ("domus_aurea_octagonal_room", "east", "domus_aurea_banquet_hall", "west"),
    ("domus_aurea_banquet_hall", "south", "domus_aurea_private_baths", "north"),
    ("domus_aurea_banquet_hall", "east", "domus_aurea_pleasure_garden", "west"),
    ("domus_aurea_pleasure_garden", "south", "domus_aurea_lake_shore", "north"),
    ("domus_aurea_pleasure_garden", "east", "domus_aurea_private_chambers", "west"),

    ("domus_aurea_vestibule", "west", "domus_aurea_treasury", "east"),
    ("domus_aurea_treasury", "south", "domus_aurea_servant_wing", "north"),
    ("domus_aurea_servant_wing", "west", "domus_aurea_buried_passage", "east"),
    ("domus_aurea_buried_passage", "south", "domus_aurea_caretaker_room", "north"),
]


# ============================================================
# NPCS
# ============================================================
# Each entry: (room_key, name, desc, kind, extra)
#   kind "static"    - plain DefaultCharacter, stays put
#   kind "wander"    - DefaultCharacter + WanderingNPC script

NPCS = [
    (
        "domus_aurea_caretaker_room", "the site caretaker", "static",
        "A quiet, dust-covered man who has apparently made a genuine "
        "home for himself in the ruins of a dead emperor's palace, "
        "unbothered by the company he keeps down here. He knows every "
        "passable corridor in the complex and doesn't especially "
        "mind sharing that knowledge, for a price or otherwise.",
        None,
    ),
    (
        "domus_aurea_hidden_fresco_room", "an antiquarian", "static",
        "A visitor crouched close to the fresco, lamp held at an angle "
        "meant to catch every detail without casting a shadow over it - "
        "the kind of careful attention that suggests this isn't idle "
        "curiosity but something closer to genuine study.",
        None,
    ),
    (
        "domus_aurea_grotto_corridor", "a lost wanderer", "wander",
        "Whoever's currently turned around somewhere in the painted "
        "corridors - the buried palace's layout has a way of confusing "
        "even people who swear they know it, and this is generally "
        "whoever's most recently proven that true.",
        ["domus_aurea_grotto_corridor", "domus_aurea_nymphaeum", "domus_aurea_hidden_fresco_room"],
    ),
]


# ============================================================
# OBJECTS - lookable scenery, get:false() locked
# ============================================================

OBJECTS = [
    (
        "domus_aurea_colossus_court", "the empty plinth",
        "A massive stone base, entirely out of proportion to anything "
        "currently standing on it - built to support roughly thirty "
        "meters of solid bronze, a statue long since moved elsewhere "
        "and reworked into something bearing no resemblance to its "
        "original subject."
    ),
    (
        "domus_aurea_hidden_fresco_room", "the scratched name",
        "A name carved into the plaster near the doorway, small and "
        "slightly unsteady, clearly added long after the fresco beside "
        "it was painted - proof that this room has been rediscovered "
        "and quietly visited more than once since its original burial."
    ),
    (
        "domus_aurea_lake_shore", "the old waterline",
        "A faint discoloration running along the lower wall, the last "
        "visible trace of where an artificial lake once lapped against "
        "this exact room - drained, filled, and built over within a "
        "few short years of the palace's fall from favor."
    ),
]


# ============================================================
# ECHOES
# ============================================================

ECHOES = {
    "domus_aurea_grotto_corridor": [
        "|wA drip of water echoes somewhere further down the painted corridor.|n",
        "|YLamp-smoke has left a faint dark smudge across one of the older frescoes.|n",
    ],
    "domus_aurea_octagonal_room": [
        "|cA faint draft stirs through the octagonal hall, source unclear.|n",
        "|wSomeone traces the dome's curve overhead, testing the old rumor for themselves.|n",
    ],
    "domus_aurea_collapsed_wing": [
        "|rA small trickle of loose plaster dust sifts down from the broken ceiling.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_meta_sudans"}

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
    queue = ["existing_meta_sudans"]
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
    print("Loaded %d new rooms (attaches to existing room #658, 'The Meta Sudans')." % len(ROOMS))
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
