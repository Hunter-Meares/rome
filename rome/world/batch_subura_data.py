"""
The Subura - a validated, in-memory description of every room, exit,
NPC, object, and echo before anything touches the live database.
Follows the exact same pattern batch_forum_data.py established (data +
a standalone validator, no Django needed) for the same reason: at 16
new rooms this is small enough to hand-check, but the validator still
catches an exit-direction collision or an unreachable room before a
single database write happens, rather than after.

Attaches to the real, already-built "Toward the Argiletum" room (#767)
via its unused "south" exit - that room's only existing exit is
"north" (back to the Auctioneer's Platform), so "south" is free and
matches its own flavor text ("the road bends north, toward the Subura
beyond" - narrated from the direction of arrival, not a claim that
"north" itself continues onward).

Deliberately built as a genuine tonal contrast to the Forum/Capitoline:
dense, working-class, non-monumental. The back-alley network has a
real loop in it (alley_west_loop connects through to the tavern's back
room), not just a tree of dead ends - the plan explicitly called for
"genuinely maze-like, non-linear by design."

The Subura's market NPCs are flavor only, not real NPCMerchants - the
existing flavor-goods merchants (Forum bookseller/goldsmith/etc.) each
have their own bespoke stock list with no shared "cheap goods" prototype
set to reuse, and inventing one wasn't asked for. A real budget shop
here is a good, contained follow-up, not something half-built now.

Run this file directly (`python3 batch_subura_data.py`) to validate
before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ------------------------------------------------------------------
# Entry + fountain plaza hub
# ------------------------------------------------------------------

room(
    "subura_entry",
    "Where the Forum Ends",
    """|YThe paving changes first|n - fitted marble giving way, a few steps at a time, to packed dirt and cracked brick. The buildings close in overhead, upper floors leaning toward each other until the strip of sky between them narrows to almost nothing. |wThe noise changes too|n: no more distant senatorial murmur, just shouting, close and constant, from a dozen directions at once. Somewhere above, someone empties a basin out a window without checking who's below. This is the Subura, and Rome's grandeur has quietly, entirely, stopped applying.""",
    "subura",
)

room(
    "subura_fountain_plaza",
    "The Subura Fountain",
    """|cA public fountain|n, its stone basin chipped and stained but never dry, sits at the center of a plaza too small for how many people are using it. Women fill jars, children dare each other to climb the rim, and an old man has claimed the one patch of shade for a nap no one's willing to disturb. |wThis is the Subura's real town square|n - not built for the purpose, just settled into it by force of habit, generation after generation.""",
    "subura",
)

# ------------------------------------------------------------------
# Insula blocks (5 rooms)
# ------------------------------------------------------------------

room(
    "insula_courtyard",
    "Insula Courtyard",
    """|wA narrow courtyard|n between two towering insulae, laundry strung overhead in every direction until the sky is more cloth than open air. The buildings rise five and six stories on either side - wood-framed, plaster patched over plaster, none of it looking especially confident about the floors above. |YChildren's voices|n carry down from somewhere too high to see.""",
    "subura",
)

room(
    "insula_lower_hall",
    "Insula Ground Floor",
    """|wA cramped entry hall|n just inside the insula proper, walls damp at the base and a stairwell disappearing upward into gloom. A row of doors, most missing their original latches, lead off to single-room lodgings that hold entire families. |cThe smell of a dozen different cooking fires|n fights for space in the close air.""",
    "subura",
)

room(
    "insula_stairwell",
    "A Groaning Stairwell",
    """|wA wooden staircase|n climbs the inside of the insula, each step announcing itself with a different creak. There's no rail past the second landing - it broke off some time ago and nobody's gotten around to it. |YLight comes only from narrow gaps|n where the plaster's cracked away from the frame.""",
    "subura",
)

room(
    "insula_upper_floor",
    "Upper Floor Landing",
    """|wA landing high enough that the stairwell's creaking has become genuinely alarming underfoot.|n A single window, more hole than window, looks out over the Subura's rooftops - a chaotic sprawl of tile, thatch, and hung washing stretching in every direction. |cThe floor here has a noticeable, permanent list to one side.|n""",
    "subura",
)

room(
    "insula_collapsed_corner",
    "The Collapsed Corner",
    """|rHalf a room, essentially|n - the outer wall gave way at some point in the building's history, and rather than fix it, someone simply boarded off what was left and kept living in the rest. |wCharred beams|n along one edge suggest the collapse and a fire were the same event, or close to it. Insulae fail like this often enough that nobody here treats it as remarkable.""",
    "subura",
)

# ------------------------------------------------------------------
# Household shrine (1 room)
# ------------------------------------------------------------------

room(
    "household_shrine",
    "A Household Shrine",
    """|YA small niche shrine|n built into the base of the insula wall, no grander than a modest doorway - a couple of crude clay figures, a stub of candle, a scattering of old offerings gone to dust. This is the household god, the lares, prayed to far more often by the people who actually live here than any god in the Forum's marble temples ever is. |wSomeone has kept it swept clean|n, even if nothing else on this street is.""",
    "subura",
)

# ------------------------------------------------------------------
# Crowded street market (3 rooms)
# ------------------------------------------------------------------

room(
    "subura_market_entrance",
    "Market Row Entrance",
    """|YThe fountain plaza's noise thickens into something denser here|n - stalls packed shoulder to shoulder, awnings overlapping, the whole street narrowed to a single crowded lane. Prices are shouted, not posted. |wNothing here costs what the Forum's shops charge|n, and nothing here is quite as good, either. Everyone seems fine with that trade.""",
    "subura",
)

room(
    "subura_market_stalls",
    "Market Row - The Stalls",
    """|YStall after stall|n, crammed close enough that browsing one means standing in three others' way. Secondhand cloth, dented cookware, vegetables a day past their best, cheap oil lamps - the Subura's actual daily economy, loud and constant. |cA cutpurse's whole career|n could be built on a crowd this dense, and more than one probably has been.""",
    "subura",
)

room(
    "subura_market_alley",
    "Market Row - Back Stalls",
    """|wThe market thins and roughens|n toward its far end - the stalls here sell what didn't sell up front, at prices that keep dropping the later in the day it gets. A few vendors don't bother with a stall at all, just a blanket on the ground and whatever they're moving today, no questions especially welcome.""",
    "subura",
)

# ------------------------------------------------------------------
# Tavern / popina (2 rooms)
# ------------------------------------------------------------------

room(
    "tavern_common_room",
    "The Leaking Amphora",
    """|YA popina|n - Rome's real working-class tavern, nothing like the Forum's respectable dining. A long stone counter holds sunken jars of wine and something that might generously be called stew; a handful of rickety tables fill the rest of the room, every one of them occupied. |wThis is where the Subura actually talks to itself|n - rumor, complaint, and half-true gossip all changing hands as freely as the wine.""",
    "subura",
)

room(
    "tavern_back_room",
    "The Back Room",
    """|wA smaller room|n behind the main counter, curtained off rather than walled - private enough for business that shouldn't be overheard, not private enough to actually guarantee it. A single low table, a few stools, and a second, unmarked door in the back wall that most patrons out front pretend not to notice.""",
    "subura",
)

# ------------------------------------------------------------------
# Back-alley network (3 rooms, genuinely non-linear)
# ------------------------------------------------------------------

room(
    "alley_junction",
    "A Crooked Junction",
    """|wThree ways meet here|n in a space too irregular to call an intersection - buildings crowd in at odd angles, leaving only the gaps between them to walk through. No two of the three ways look more promising than the others. |cSomeone is always watching this junction|n, even when it looks empty.""",
    "subura",
)

room(
    "alley_east_dead_end",
    "A Dead-End Alley",
    """|wThe alley simply stops|n against a blank wall, high enough that climbing it isn't a real option. That hasn't stopped this corner from being used constantly - it's exactly private enough for the kind of transaction that needs a wall at its back and only one way anyone could approach from.""",
    "subura",
)

room(
    "alley_west_loop",
    "A Doubling-Back Alley",
    """|wThe alley bends sharply|n behind a row of buildings, easy to lose your bearings in if you didn't come this way on purpose. Anyone who has, though, knows it comes out somewhere useful - a narrow, unmarked gap in the wall just ahead leads directly into the back of a building most people only ever enter from the front.""",
    "subura",
)

ROOM_COUNT_EXPECTED = 16


# ============================================================
# LINKS
# ============================================================

LINKS = [
    ("existing_argiletum_stub", "south", "subura_entry", "north"),
    ("subura_entry", "south", "subura_fountain_plaza", "north"),

    ("subura_fountain_plaza", "east", "subura_market_entrance", "west"),
    ("subura_market_entrance", "east", "subura_market_stalls", "west"),
    ("subura_market_stalls", "south", "subura_market_alley", "north"),

    ("subura_fountain_plaza", "west", "insula_courtyard", "east"),
    # Retrofitted live to a real world.doors.DescriptiveDoor pair -
    # a real tenement building deserves a real door. Historical LINKS
    # data (the live setup script already ran and isn't meant to be
    # re-run against a populated DB).
    ("insula_courtyard", "west", "insula_lower_hall", "east"),
    ("insula_courtyard", "south", "household_shrine", "north"),
    ("insula_lower_hall", "up", "insula_stairwell", "down"),
    ("insula_stairwell", "up", "insula_upper_floor", "down"),
    ("insula_upper_floor", "east", "insula_collapsed_corner", "west"),

    ("subura_fountain_plaza", "south", "alley_junction", "north"),
    ("alley_junction", "east", "alley_east_dead_end", "west"),
    ("alley_junction", "west", "alley_west_loop", "east"),
    ("alley_west_loop", "south", "tavern_back_room", "north"),
    ("tavern_back_room", "west", "tavern_common_room", "east"),
    # Retrofitted live to a real door - see the insula comment above.
    ("tavern_common_room", "north", "subura_market_alley", "south"),
]


# ============================================================
# NPCS
# ============================================================
# Each entry: (room_key, name, desc, kind, extra)

NPCS = [
    (
        "tavern_common_room", "the tavern keeper", "static",
        "A heavyset woman running the counter with the tired, unshakeable "
        "authority of someone who has broken up more fights than she can "
        "count and expects to break up several more tonight. She hears "
        "everything said in this room, whether or not she looks like "
        "she's listening.",
        None,
    ),
    (
        "alley_east_dead_end", "the fence", "static",
        "A thin, sharp-eyed man who deals in goods nobody asks the origin "
        "of, conducting business from the same dead-end corner often "
        "enough that it's practically his office. Quick to smile, "
        "quicker to notice if you're wasting his time.",
        None,
    ),
    (
        "alley_west_loop", "a hired enforcer", "static",
        "A former legionary, discharged or deserted depending who's "
        "telling it, built like the wall he's leaning against. He doesn't "
        "say much - he doesn't need to. Whoever he's working for tonight, "
        "it isn't hard to guess.",
        None,
    ),
    (
        "subura_market_stalls", "a cutpurse", "wander",
        "Young, quick, and doing an excellent job of looking like just "
        "another face in the market crowd - right up until a purse "
        "that was full a moment ago isn't anymore.",
        ["subura_market_stalls", "subura_market_entrance", "subura_market_alley"],
    ),
    (
        "alley_junction", "a wary lookout", "static",
        "Leaning in the junction like he's got nowhere to be, eyes moving "
        "to every approach anyway. Whoever's actually doing business "
        "nearby is paying him to make sure nobody arrives unannounced.",
        None,
    ),
    (
        "insula_lower_hall", "a laundress", "static",
        "Elbow-deep in a washtub that never seems to empty, trading news "
        "with anyone who passes as easily as she trades gossip for gossip. "
        "If something happened in this insula today, she already knows.",
        None,
    ),
    (
        "household_shrine", "an old veteran", "static",
        "An old man who spends most of his day sitting near the shrine, "
        "missing two fingers on his left hand and entirely willing to "
        "tell you how, at length, whether you asked or not. His stories "
        "get better, not more accurate, with each retelling.",
        None,
    ),
    (
        "subura_fountain_plaza", "a fountain crowd", "wander",
        "Whoever happens to be at the fountain right now - a woman filling "
        "a jar, a pair of children daring each other closer to the edge, "
        "someone just resting in the one patch of shade. The faces change; "
        "the crowd never really thins.",
        ["subura_fountain_plaza", "subura_market_entrance", "insula_courtyard"],
    ),
]


# ============================================================
# OBJECTS - lookable scenery, matching the Forum's get:false() pattern
# ============================================================

OBJECTS = [
    (
        "alley_junction", "the wanted notice board",
        "A weathered board nailed up at the junction, layered thick with "
        "notices - runaway slaves, unpaid debts, a face or two wanted for "
        "worse. Most are torn, faded, or scrawled over with someone else's "
        "message entirely. New ones go up here whenever there's coin "
        "behind them."
    ),
    (
        "tavern_common_room", "graffiti scratched into the counter",
        "Someone's carved a crude joke about a local magistrate into the "
        "wood, old enough that the edges have gone smooth and dark with "
        "handling. Whoever wrote it is long gone; the joke, apparently, "
        "was worth keeping."
    ),
    (
        "insula_stairwell", "graffiti on the plaster",
        "A scrawled tally of names and dates, half-legible, alongside a "
        "crude drawing no one's bothered to explain. Real Roman graffiti "
        "was rarely dignified - insults, boasts, and jokes scratched into "
        "any surface that would hold them, and this stairwell is no "
        "exception."
    ),
    (
        "household_shrine", "the household gods",
        "A pair of small clay figures, worn nearly featureless from "
        "handling, representing the lares - the household's own guardian "
        "spirits. No temple statue gets touched this often. This is the "
        "religion the Subura actually practices, daily, without ceremony."
    ),
    (
        "insula_collapsed_corner", "the charred beams",
        "Blackened wood along the collapsed wall's edge, the fire's cause "
        "long since forgotten or never known in the first place. Insulae "
        "burn and fall with grim regularity in this city - this is simply "
        "the closest anyone's had to actually look at the aftermath."
    ),
]


# ============================================================
# ECHOES
# ============================================================

ECHOES = {
    "subura_fountain_plaza": [
        "|cWater splashes as someone else's jar overflows the basin.|n",
        "|YAn argument breaks out over whose turn it is at the fountain.|n",
        "|wA child's laughter cuts briefly through the general noise.|n",
    ],
    "subura_market_stalls": [
        "|YA vendor shouts a price, then a lower one, then a lower one still.|n",
        "|cSomeone yelps - a purse just changed hands without its owner's help.|n",
    ],
    "tavern_common_room": [
        "|wSomeone starts a story that's clearly been told, and embellished, before.|n",
        "|YA cup slams down on the counter, demanding a refill.|n",
        "|cA burst of laughter erupts from a table in the corner.|n",
    ],
    "alley_junction": [
        "|xFootsteps echo somewhere close, then stop.|n",
        "|wA shape in a doorway shifts, watching, then goes still again.|n",
    ],
    "insula_courtyard": [
        "|YA basin's worth of water splashes down from an upper window, barely missing anyone.|n",
        "|wLaundry lines creak overhead in a breeze that doesn't reach the ground.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_argiletum_stub"}

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
    queue = ["existing_argiletum_stub"]
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
    print("Loaded %d new rooms (attaches to existing room #767, 'Toward the Argiletum')." % len(ROOMS))
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
