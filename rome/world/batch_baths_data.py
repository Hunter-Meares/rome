"""
The Baths (a neighborhood balneum, not a grand imperial Thermae) - a
validated, in-memory description of every room, exit, NPC, and object
before anything touches the live database. Same pattern as every prior
build this session.

Attaches to the real, already-built "Insula Courtyard" room (#2641,
part of the Subura) via its unused "north" exit - smaller neighborhood
baths genuinely were dotted through residential districts exactly like
this, blocks from the insulae they served, distinct in character from
a monumental standalone Thermae complex.

The two "gossiping regulars" use the existing NPCChatter script's
built-in db.tells_rumors/db.rumor_chance feature (world/colosseum.py) -
already fully built, no new code needed. This is the "rotate in
current server news" idea from the original plan, delivered as the
one-line integration it actually is.

Run this file directly (`python3 batch_baths_data.py`) to validate
before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


room(
    "baths_entrance",
    "The Baths - Apodyterium",
    """|wA changing room|n, wall niches cut in neat rows for clothes and sandals - the kind of thing that seems trivial until someone's robe goes missing, which the attendant here insists has never once happened on her watch. |YThe air already carries a faint trace of steam|n drifting in from deeper inside.""",
    "baths",
)

room(
    "baths_palaestra",
    "The Palaestra",
    """|YAn open exercise yard|n, sand-floored, where regulars work up a real sweat before ever touching the water - wrestling, ball games, or just brisk laps around the perimeter. |wRomans bathe after exercising, not instead of it|n, and this yard is the reason the baths feel earned rather than merely indulgent.""",
    "baths",
)

room(
    "baths_frigidarium",
    "The Frigidarium",
    """|cA plunge pool of genuinely cold water|n dominates this room, the shock of it audible in every gasp from whoever's just gotten in. |wThis is the bracing first real step of bathing proper|n - unpleasant for exactly as long as it takes to stop noticing.""",
    "baths",
)

room(
    "baths_tepidarium",
    "The Tepidarium",
    """|YA warm, gently heated room|n, meant less as a destination than a transition - the body adjusting gradually from the frigidarium's shock toward the caldarium's real heat ahead. |wConversation flows easiest here|n, the temperature comfortable enough to actually linger in.""",
    "baths",
)

room(
    "baths_caldarium",
    "The Caldarium",
    """|rThe hot room|n, air thick and close, a heated pool along one wall steaming gently. |wThe floor itself is warm underfoot|n - genuinely warm, not just from the air - heated from below by machinery most bathers never think about and never see.""",
    "baths",
)

room(
    "baths_hypocaust",
    "The Hypocaust",
    """|rA cramped service crawlspace|n beneath the caldarium, low enough to bend double in, dominated by a wood-fed furnace whose heat rises through a raised floor and hollow wall-flues to warm every room above. |wThis is the actual engineering|n behind the caldarium's warm floor and the tepidarium's gentle heat - genuinely clever, and genuinely unglamorous, for exactly the same reason.""",
    "baths",
)

room(
    "baths_unctorium",
    "The Unctorium",
    """|YA smaller room|n set aside for oiling and massage, low couches arranged for exactly that purpose. |wStrigils and small flasks of scented oil|n sit ready on a side table - Romans clean themselves with oil and a scraper here, not soap.""",
    "baths",
)

room(
    "baths_lounge_a",
    "Social Lounge - East",
    """|wA comfortable lounge|n just off the entrance, couches arranged for conversation rather than bathing. Business, politics, and gossip all get traded here as freely as at any tavern - the baths are as much a social institution as a hygienic one, and this room is where that's most obvious.""",
    "baths",
)

room(
    "baths_lounge_b",
    "Social Lounge - West",
    """|wA second lounge|n, quieter than the first, favored by regulars who'd rather read than talk - though the two activities blend together here more often than either group would probably admit.""",
    "baths",
)

room(
    "baths_library",
    "The Baths' Library",
    """|YA small library room|n, genuinely unexpected in a bathhouse to anyone who's never visited a larger Roman one - a few dozen scrolls racked along one wall, available to any bather who wants something to read between rooms. |wA detail most visitors don't expect until they're standing in it.|n""",
    "baths",
)

room(
    "baths_attendant_station",
    "Attendant's Station",
    """|wA small station near the entrance|n, towels stacked in neat piles, a low bench for whoever's waiting their turn. The balneatores - the bath attendants - work out of here, keeping the whole complex running with a steady, unglamorous competence nobody tips them enough for.""",
    "baths",
)

ROOM_COUNT_EXPECTED = 11


LINKS = [
    ("existing_insula_courtyard", "north", "baths_entrance", "south"),
    ("baths_entrance", "north", "baths_palaestra", "south"),
    ("baths_entrance", "east", "baths_lounge_a", "west"),
    ("baths_entrance", "west", "baths_attendant_station", "east"),
    ("baths_palaestra", "north", "baths_frigidarium", "south"),
    ("baths_frigidarium", "east", "baths_tepidarium", "west"),
    ("baths_tepidarium", "east", "baths_caldarium", "west"),
    ("baths_tepidarium", "north", "baths_unctorium", "south"),
    ("baths_caldarium", "down", "baths_hypocaust", "up"),
    ("baths_lounge_a", "east", "baths_lounge_b", "west"),
    ("baths_lounge_b", "north", "baths_library", "south"),
]


NPCS = [
    (
        "baths_attendant_station", "a bath attendant", "static",
        "A brisk, efficient woman who's clearly done this job long "
        "enough to have opinions about every regular who walks through - "
        "which robe niche someone always forgets, who never tips, who "
        "always does.",
        None,
    ),
    (
        "baths_unctorium", "a masseur", "static",
        "A broad-shouldered man with permanently oil-slicked forearms, "
        "working a client's shoulders with the unhurried confidence of "
        "someone who's heard every complaint the human back can produce.",
        None,
    ),
]

# Chatter-only NPCs (NPCChatter + tells_rumors, wired up directly in
# the apply script rather than via the generic NPCS list above, since
# they need extra db attributes NPCS doesn't carry).
CHATTER_NPCS = [
    (
        "baths_lounge_a", "a gossiping regular",
        [
            "Have you heard what they're saying about the new arrivals at the Colosseum?",
            "I'm telling you, the wine's watered down more than it used to be.",
            "My cousin swears he saw a god walking the Forum yesterday.",
        ],
    ),
    (
        "baths_lounge_b", "a quieter regular",
        [
            "Some of us come here to read, not to listen to gossip.",
            "The scrolls in that library aren't as dull as they look.",
        ],
    ),
]


OBJECTS = [
    (
        "baths_unctorium", "a set of strigils",
        "Curved bronze scrapers, lined up by size on the side table - "
        "the actual tool Romans use to clean themselves, dragged across "
        "oiled skin to scrape away oil, sweat, and grime together. No "
        "soap involved at any point."
    ),
]


ECHOES = {
    "baths_caldarium": [
        "|rSteam curls thickly off the heated pool's surface.|n",
        "|wThe floor's warmth is a constant, quiet presence underfoot.|n",
    ],
    "baths_frigidarium": [
        "|cSomeone gasps audibly as they lower themselves into the cold water.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_insula_courtyard"}

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
    queue = ["existing_insula_courtyard"]
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
    for room_key, _, _ in CHATTER_NPCS:
        if room_key not in all_keys:
            errors.append("Chatter NPC references unknown room: %s" % room_key)
    for room_key, _, _ in OBJECTS:
        if room_key not in all_keys:
            errors.append("Object references unknown room: %s" % room_key)
    for room_key in ECHOES:
        if room_key not in all_keys:
            errors.append("Echo references unknown room: %s" % room_key)

    return errors


if __name__ == "__main__":
    print("Loaded %d new rooms (attaches to existing room #2641, 'Insula Courtyard')." % len(ROOMS))
    print("Loaded %d links, %d NPCs, %d chatter NPCs, %d objects, %d rooms with echoes." % (
        len(LINKS), len(NPCS), len(CHATTER_NPCS), len(OBJECTS), len(ECHOES)
    ))
    errs = validate()
    if errs:
        print("\nVALIDATION FAILED (%d errors):" % len(errs))
        for e in errs:
            print(" -", e)
    else:
        print("\nValidation passed: no duplicate names, no exit collisions, "
              "full connectivity, all references resolve.")
