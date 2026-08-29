"""
Trajan's Market - a validated, in-memory description of every room,
exit, NPC, and object before anything touches the live database. Same
pattern as batch_forum_data.py / batch_subura_data.py: data + a
standalone validator, no Django needed, run before a single database
write happens.

Attaches to the real, already-built "The Market Stretch" room (#760)
via its unused "west" exit (its existing exits are east/north/south) -
a food-market room is a natural, thematically consistent jumping-off
point toward a larger market complex, and "west" was simply free.

Genuinely expands the existing economy system rather than just adding
flavor rooms: two real NPCMerchants (a spice trader, an imported-silk
merchant) stock genuinely new item prototypes (see world/prototypes.py)
that don't overlap with anything the Forum's own merchants sell.

Run this file directly (`python3 batch_trajan_market_data.py`) to
validate before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ------------------------------------------------------------------
# Ground level (5 rooms) - central arcade + great hall + 4 trade wings
# ------------------------------------------------------------------

room(
    "trajan_arcade_entrance",
    "Arcade of Trajan's Market",
    """|YA covered arcade|n opens off the street, brick-vaulted overhead in a way nothing in the Forum's marble precinct quite matches - this is commerce built for function first, grandeur second. Shopfronts line both walls in neat, identical arches, each one a separate small business behind its own counter. |wThe crowd here moves with real purpose|n, not the Forum's leisurely browsing.""",
    "trajan_market",
)

room(
    "trajan_great_hall",
    "The Great Hall",
    """|YThe arcade opens into a genuinely vast vaulted hall|n, tiered galleries visible rising overhead on more than one level - by a wide margin the largest covered commercial space in the city. Voices from a dozen different transactions blend into a single steady roar under the high brick vault. |wSome historians will someday call this the world's first shopping mall|n, and standing here, it's not hard to see why.""",
    "trajan_market",
)

room(
    "trajan_spice_wing",
    "The Spice Wing",
    """|YThe air here is thick enough to taste|n - pepper, cinnamon, cumin, saffron, sacks and jars of it stacked floor to ceiling behind narrow counters. |gEvery vendor in this wing sells some variation of the same thing|n: flavor that started its journey somewhere the buyers will never see.""",
    "trajan_market",
)

room(
    "trajan_textile_wing",
    "The Silk and Textile Wing",
    """|wBolts of cloth hang from every available beam|n, color and texture ranging from ordinary local wool to fabric so fine it barely seems to exist in the hand. |YThe silk merchants keep their best stock behind the counter|n, not on display - shown only to buyers who look like they can actually afford it.""",
    "trajan_market",
)

room(
    "trajan_pottery_wing",
    "The Pottery and Glass Wing",
    """|cShelves of pottery and glassware|n line this wing, from plain everyday cookware to pieces thin and clear enough to seem more like captured light than actual glass. |wA single dropped tray here represents a genuinely bad day|n for whoever's carrying it.""",
    "trajan_market",
)

room(
    "trajan_exotic_wing",
    "The Wing of Foreign Curiosities",
    """|YThe quietest of the market's wings|n, and the strangest - carved ivory, incense of unfamiliar origin, small animals in cages that nobody local can name. |gWhatever this wing is selling|n, it wasn't grown or made anywhere near Rome.""",
    "trajan_market",
)

# ------------------------------------------------------------------
# Upper level (5 rooms)
# ------------------------------------------------------------------

room(
    "trajan_upper_gallery",
    "Upper Gallery",
    """|wA gallery running above the Great Hall|n, open along one side so the noise and motion of the floor below carries straight up. From here the hall's real scale finally becomes obvious - shop after shop, tier after tier, more of the market than any single ground-floor room lets you see at once.""",
    "trajan_market",
)

room(
    "trajan_grain_dole_hall",
    "The Grain Dole Hall",
    """|YA long, plain hall|n, entirely unlike the market's commercial wings - no goods for sale here, just orderly lines of citizens and a row of officials checking names against a roll before measuring out grain. |wThe cura annonae|n, Rome calls it: the free grain dole that has kept more than one hungry crowd from becoming a dangerous one.""",
    "trajan_market",
)

room(
    "trajan_upper_shops_a",
    "Upper Level Shops - East Row",
    """|wA row of smaller shops|n along the upper gallery, quieter and less crowded than the ground floor's wings - the kind of space a business takes once it's established enough not to need the busiest foot traffic in the building.""",
    "trajan_market",
)

room(
    "trajan_upper_shops_b",
    "Upper Level Shops - West Row",
    """|wAnother row of upper shops|n, mirroring the row across the gallery - a few stand empty, shutters closed, waiting on a tenant. Even Trajan's Market, for all its scale, doesn't run at full capacity every season.""",
    "trajan_market",
)

room(
    "trajan_scribes_office",
    "Grain Dole Records Office",
    """|wA cramped office|n just off the grain hall, shelves packed with wax tablets and papyrus rolls recording who's owed grain, who's collected it, and who hasn't in long enough to need checking on. |YThe record-keeping here|n is, if anything, more organized than the hall it serves.""",
    "trajan_market",
)

# ------------------------------------------------------------------
# Rooftop terrace + administrative office (2 rooms)
# ------------------------------------------------------------------

room(
    "trajan_rooftop_terrace",
    "Market Rooftop Terrace",
    """|cThe market's uppermost terrace|n, built directly into the slope of the hill behind it - from here the ground simply continues upward into the hillside at your back, while the whole market complex and a real stretch of the city spread out below. |wA genuinely rare vantage point|n, and a popular one for exactly that reason.""",
    "trajan_market",
)

room(
    "trajan_admin_office",
    "Market Administration Office",
    """|wA cluttered office|n handling the unglamorous business that keeps the market running - stall permits, tax assessments, the occasional dispute between neighboring shopkeepers. |YA ledger sits permanently open|n on the main desk, columns of names and sums in a clerk's careful hand.""",
    "trajan_market",
)

ROOM_COUNT_EXPECTED = 13


# ============================================================
# LINKS
# ============================================================

LINKS = [
    ("existing_market_stretch", "west", "trajan_arcade_entrance", "east"),
    ("trajan_arcade_entrance", "west", "trajan_great_hall", "east"),

    ("trajan_great_hall", "north", "trajan_spice_wing", "south"),
    ("trajan_great_hall", "south", "trajan_textile_wing", "north"),
    ("trajan_great_hall", "west", "trajan_pottery_wing", "east"),
    ("trajan_pottery_wing", "south", "trajan_exotic_wing", "north"),
    ("trajan_great_hall", "up", "trajan_upper_gallery", "down"),

    ("trajan_upper_gallery", "north", "trajan_grain_dole_hall", "south"),
    ("trajan_upper_gallery", "south", "trajan_upper_shops_a", "north"),
    ("trajan_upper_gallery", "east", "trajan_upper_shops_b", "west"),
    ("trajan_upper_gallery", "west", "trajan_rooftop_terrace", "east"),
    ("trajan_grain_dole_hall", "north", "trajan_scribes_office", "south"),
    ("trajan_upper_shops_a", "south", "trajan_admin_office", "north"),
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
        "trajan_spice_wing", "a spice trader", "merchant",
        "A weathered trader presiding over sacks and jars of spice from "
        "half a dozen countries, quick to name-drop exactly which trade "
        "route each one traveled - whether or not it's true.",
        ["SACK_OF_PEPPER", "JAR_OF_CINNAMON", "BUNDLE_OF_SAFFRON"],
    ),
    (
        "trajan_textile_wing", "an imported-silk merchant", "merchant",
        "An impeccably dressed merchant who handles every bolt of silk "
        "like it's already sold, patient with lookers but visibly "
        "uninterested in anyone who can't afford to become a buyer.",
        ["BOLT_OF_SILK", "EMBROIDERED_SILK_SASH", "DYED_SILK_SCARF"],
    ),
    (
        "trajan_grain_dole_hall", "a grain-dole administrator", "static",
        "A tired-looking official checking names against a long roll "
        "with the patient thoroughness of someone who's done this exact "
        "task every single day for years and expects to do it for years "
        "more.",
        None,
    ),
    (
        "trajan_pottery_wing", "an appraiser", "static",
        "A sharp-eyed woman who examines glassware and pottery for "
        "buyers nervous about being cheated, charging a small fee to "
        "tell them honestly whether they're about to be.",
        None,
    ),
    (
        "trajan_exotic_wing", "a curiosities dealer", "static",
        "A soft-spoken dealer surrounded by things from places most "
        "customers couldn't find on a map, happy to talk at length about "
        "any of it to anyone who'll actually listen.",
        None,
    ),
    (
        "trajan_great_hall", "a market crowd", "wander",
        "Whoever happens to be moving through the Great Hall right now - "
        "a shopper comparing prices between wings, a porter hauling "
        "goods somewhere, a child towed along by an impatient parent.",
        ["trajan_great_hall", "trajan_arcade_entrance", "trajan_upper_gallery"],
    ),
]


# ============================================================
# OBJECTS - lookable scenery, get:false() locked
# ============================================================

OBJECTS = [
    (
        "trajan_scribes_office", "the grain-dole ledger",
        "An enormous ledger, permanently open, page after page of names "
        "and dates recording who has drawn their share of Rome's free "
        "grain and when. It's added to every single day the dole runs."
    ),
    (
        "trajan_admin_office", "the permit ledger",
        "A second, smaller ledger tracking stall permits and tax "
        "assessments - considerably less dramatic than the grain-dole "
        "rolls next door, but just as essential to the market actually "
        "functioning."
    ),
    (
        "trajan_great_hall", "the vaulted brick ceiling",
        "The hall's high, curved brick ceiling, engineered to span a "
        "space this size without a single interior column blocking the "
        "floor - a genuine feat of construction most of the shoppers "
        "below never once look up to appreciate."
    ),
]


# ============================================================
# ECHOES
# ============================================================

ECHOES = {
    "trajan_great_hall": [
        "|YA dozen overlapping conversations blend into one steady roar under the vault.|n",
        "|cA porter shouts for people to clear a path, hauling goods through the crowd.|n",
        "|wSomewhere above, footsteps cross the upper gallery.|n",
    ],
    "trajan_spice_wing": [
        "|gThe smell of cinnamon and pepper hangs thick enough to taste.|n",
        "|YA vendor extols the virtues of saffron to anyone who'll stop walking.|n",
    ],
    "trajan_grain_dole_hall": [
        "|wA name is called out, checked against the roll, and grain is measured out.|n",
        "|cThe line shuffles forward another few feet.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_market_stretch"}

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
    queue = ["existing_market_stretch"]
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
    print("Loaded %d new rooms (attaches to existing room #760, 'The Market Stretch')." % len(ROOMS))
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
