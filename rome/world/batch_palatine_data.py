"""
Palatine Hill (the Imperial Palace) - a validated, in-memory
description of every room, exit, NPC, and object before anything
touches the live database. Same pattern as every prior build this
session.

Attaches to the real, already-built "The Regia - Sacrificial
Courtyard" room (#744) via its unused "east" exit - the Regia's real
historical location was genuinely at the foot of the Palatine Hill,
adjacent to the Forum and the Vestal complex, making this the most
geographically honest attachment point available rather than an
arbitrary one.

The approach is gated with the existing LevelGateExit (world/colosseum.py,
already used for the Ludus's internal tiers) rather than a
faction-reputation system, which doesn't exist in-game yet - a real,
working restriction using what's actually built, not a placeholder
pretending a bigger system exists.

Dropped one room from the original 14-room plan: the "viewing box
overlooking the Circus Maximus" doesn't make sense to build since
Circus Maximus itself doesn't exist yet (see the build-order review -
no chariot-racing mechanic exists in the codebase). Add it later, as a
single room, whenever Circus Maximus actually gets built - not before.

Run this file directly (`python3 batch_palatine_data.py`) to validate
before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


room(
    "palatine_gate",
    "The Palatine Gate",
    """|YA guarded gate|n marks the boundary between the Forum's public ground and the hill rising behind it - the Palatine, where the word "palace" itself comes from. |rTwo Praetorians stand here|n, spears crossed loosely but ready, sizing up everyone who approaches with the specific, practiced assessment of men deciding whether someone belongs.""",
    "palatine",
)

room(
    "palatine_outer_courtyard",
    "Outer Courtyard",
    """|wA broad courtyard|n just inside the gate, paved in stone too fine for a mere antechamber - a clear statement, before a visitor ever reaches the palace proper, of exactly whose ground they're standing on. Attendants cross it on errands too important to explain to anyone who asks.""",
    "palatine",
)

room(
    "palatine_reception_hall",
    "The Grand Reception Hall",
    """|YA vast hall|n where the Emperor receives visitors and petitioners, its scale calculated to make anyone who enters feel precisely as small as intended. Columns rise to a coffered ceiling far overhead; a raised dais at the far end makes unmistakably clear where all real attention in this room eventually goes.""",
    "palatine",
)

room(
    "palatine_quarters_antechamber",
    "Imperial Quarters - Antechamber",
    """|wA private antechamber|n, guarded even more closely than the halls outside it - the actual threshold between the palace's public performance and its genuinely private life. Very few people who aren't already trusted ever see past this room.""",
    "palatine",
)

room(
    "palatine_quarters_inner",
    "Imperial Quarters - Inner Chamber",
    """|YThe Emperor's own private chamber|n, deliberately spare compared to the reception hall's calculated grandeur - fine furnishings, but arranged for actual living rather than display. Power, up close, apparently still needs somewhere ordinary to sleep.""",
    "palatine",
)

room(
    "palatine_dining_hall",
    "The Imperial Dining Hall",
    """|wA long dining hall|n, couches arranged for the reclining feasts that double as real political theater - imperial banquets settle alliances and reputations as often as they settle appetites. |YThe table is always set|n, whether or not anyone important is currently using it.""",
    "palatine",
)

room(
    "palatine_garden_courtyard",
    "Peristyle Garden",
    """|gA colonnaded garden courtyard|n, genuinely Roman in style - a covered walkway framing an open central plot of trimmed plants and a small fountain. Considerably quieter than anywhere else in the palace, and clearly meant to be.""",
    "palatine",
)

room(
    "palatine_garden_far",
    "The Far Garden",
    """|gA second, more secluded garden|n, tucked behind the peristyle's outer wall - fewer statues, fewer attendants, more actual privacy. Whoever comes here generally wants to be left alone, and generally is.""",
    "palatine",
)

room(
    "palatine_admin_wing",
    "Administrative Wing",
    """|wA busy wing|n given over entirely to the paperwork an empire apparently can't run without - correspondence, provincial reports, requests for audiences that will mostly never be granted. The actual machinery of government looks a great deal less glamorous than the throne room down the hall.""",
    "palatine",
)

room(
    "palatine_archive",
    "Imperial Archive",
    """|wRoom after room's worth of records|n compressed into careful shelving - decrees, correspondence, and the accumulated paperwork of however many years this palace has stood. A clerk's error here could quietly outlast an emperor's own reign.""",
    "palatine",
)

room(
    "palatine_barracks",
    "Praetorian Barracks",
    """|rA barracks room|n given over entirely to the Praetorian Guard's presence on the hill - the Emperor's own soldiers, closer to him at all times than any legion at the frontier ever gets. Weapons racked in neat rows say plainly what this room is actually for.""",
    "palatine",
)

room(
    "palatine_shrine",
    "The Emperor's Private Shrine",
    """|YA small personal shrine|n, distinct from any state temple - the Emperor's own household gods, tended privately rather than through the great public rites performed in his name elsewhere in the city. Even a man treated as half-divine, apparently, keeps a god or two of his own to answer to.""",
    "palatine",
)

room(
    "palatine_kitchens",
    "The Palace Kitchens",
    """|wA large, constantly busy kitchen|n, feeding a household far larger than just the Emperor's own family - guards, attendants, clerks, and whichever petitioners are important enough to be fed while they wait. |gThe smell of roasting meat|n dominates everything else in the room.""",
    "palatine",
)

ROOM_COUNT_EXPECTED = 13


LINKS = [
    ("existing_regia_courtyard", "east", "palatine_gate", "west"),
    ("palatine_gate", "north", "palatine_outer_courtyard", "south"),
    # Retrofitted live to a real world.doors.DescriptiveDoor pair - the
    # Emperor's own palace building deserved a real door, not a plain
    # exit. Historical LINKS data (the live setup script already ran
    # and isn't meant to be re-run against a populated DB).
    ("palatine_outer_courtyard", "north", "palatine_reception_hall", "south"),
    ("palatine_reception_hall", "east", "palatine_quarters_antechamber", "west"),
    ("palatine_quarters_antechamber", "east", "palatine_quarters_inner", "west"),
    ("palatine_reception_hall", "west", "palatine_dining_hall", "east"),
    ("palatine_outer_courtyard", "east", "palatine_garden_courtyard", "west"),
    ("palatine_garden_courtyard", "east", "palatine_garden_far", "west"),
    ("palatine_outer_courtyard", "west", "palatine_admin_wing", "east"),
    ("palatine_admin_wing", "west", "palatine_archive", "east"),
    ("palatine_admin_wing", "south", "palatine_barracks", "north"),
    ("palatine_reception_hall", "north", "palatine_shrine", "south"),
    ("palatine_dining_hall", "south", "palatine_kitchens", "north"),
]


# Gate config applied directly in the apply script (LevelGateExit needs
# db.min_level/db.gate_flavor set after creation, which the generic
# exit-creation loop below doesn't know about).
GATE_MIN_LEVEL = 10
GATE_FLAVOR = "the Palatine"


NPCS = [
    (
        "palatine_gate", "a Praetorian gate guard", "static",
        "A Praetorian who has clearly turned away more people than he's "
        "ever waved through, entirely unbothered by however important "
        "any of them claimed to be at the time.",
        None,
    ),
    (
        "palatine_reception_hall", "the imperial chamberlain", "static",
        "A precise, unhurried man who controls access to the Emperor "
        "more completely than any guard on the gate - the actual "
        "gatekeeper of this palace is a steward with a ledger, not a "
        "soldier with a spear.",
        None,
    ),
    (
        "palatine_garden_courtyard", "a courtier", "static",
        "Dressed a step above practical, drifting through the garden "
        "with the studied idleness of someone who is, in fact, working "
        "very hard right now, just not in a way that looks like it.",
        None,
    ),
    (
        "palatine_admin_wing", "an imperial clerk", "static",
        "Buried in correspondence, moving through provincial reports "
        "with the flat, practiced speed of someone for whom an empire's "
        "worth of paperwork stopped being remarkable years ago.",
        None,
    ),
    (
        "palatine_barracks", "a Praetorian", "wander",
        "One of the Emperor's own guard, off duty but never quite "
        "relaxed, moving between the barracks and the wing they're "
        "actually posted to watch.",
        ["palatine_barracks", "palatine_admin_wing", "palatine_outer_courtyard"],
    ),
]


OBJECTS = [
    (
        "palatine_reception_hall", "the imperial dais",
        "A raised platform at the hall's far end, a single ornate chair "
        "positioned to be the first thing anyone entering the room "
        "actually sees. Empty or not, nobody in this hall stops facing "
        "it for long."
    ),
    (
        "palatine_archive", "a shelf of imperial decrees",
        "Row after row of sealed documents, official government seals "
        "pressed into wax on every one - decrees, appointments, and "
        "correspondence that shaped policy for a province most of the "
        "clerks filing it will never actually visit."
    ),
    (
        "palatine_shrine", "the household lares",
        "Small figures of the Emperor's own household gods, tended here "
        "privately - a quieter, more personal echo of the same lares "
        "any ordinary Roman family keeps, regardless of how far above "
        "ordinary the family living here otherwise is."
    ),
]


ECHOES = {
    "palatine_reception_hall": [
        "|wFootsteps echo across the hall's polished floor, unhurried and deliberate.|n",
        "|YA petitioner's request is heard, and answered with careful, noncommittal words.|n",
    ],
    "palatine_admin_wing": [
        "|wThe scratch of styluses on wax tablets is nearly constant here.|n",
        "|cA clerk mutters a number under his breath, checking it twice.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_regia_courtyard"}

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
    queue = ["existing_regia_courtyard"]
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
    print("Loaded %d new rooms (attaches to existing room #744, 'The Regia - Sacrificial Courtyard')." % len(ROOMS))
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
