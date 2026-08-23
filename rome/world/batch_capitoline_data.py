"""
Capitoline Hill world data - validated, in-memory description of every
room, exit, NPC, object, and echo before anything touches the live
database. Same methodology as world/batch_forum_data.py: build as pure
Python data, run the standalone validate() below (no Django needed) to
catch duplicate names/exit collisions/unreachable rooms BEFORE a single
live write happens.

Connects to the existing Forum build by continuing north from the live
room "Clivus Capitolinus - Near the Summit" (already built, already
ends with the flavor line "a road that simply continues further than
this city has built" - this is that continuation). Deliberately reached
only via the Forum's own Clivus Capitolinus, not directly from the
Colosseum - matching real Roman geography, where the Capitoline sits
much closer to the Forum than to where the Colosseum would later stand;
the existing Colosseum -> Meta Sudans -> Via Sacra -> Forum -> Clivus
Capitolinus chain already encodes that relative distance without
needing any new invented "pace-count" road segments.

The Asylum (Zone 2) and the grove path (Zone 2, room 3) are the two
real branch points - deliberately not a single corridor up the hill.
The Capitolium (Jupiter's temple, the main summit) and the Arx (the
separate northern citadel peak) are genuinely different destinations
from the Asylum, not a forced sequence; the Tarpeian Rock and the
minor temples are optional detours off the grove path, not on the
route to either summit at all.

Run this file directly (`python3 world/batch_capitoline_data.py`) to
validate before executing anything against the live game.
"""

# ============================================================
# ROOMS
# ============================================================

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ------------------------------------------------------------------
# ZONE 1 - Upper Clivus Capitolinus (4 rooms). Continues north from
# the existing live room "Clivus Capitolinus - Near the Summit".
# ------------------------------------------------------------------

room(
    "clivus_final_base",
    "Clivus Capitolinus - the Final Ascent",
    """|YThe road steepens sharply here|n, the last real climb before the summit proper. The Forum's noise has finally started to thin behind you, replaced by something quieter and more deliberate - the sound of a place people come to on purpose, not just pass through.""",
    "clivus_final",
)

room(
    "clivus_final_switchback",
    "Clivus Capitolinus - the Upper Switchback",
    """|YThe road bends hard against the hillside|n, and for a moment the climb stops fighting you. A |wweathered roadside altar|n stands tucked into the bend, small offerings - a coin, a wilted garland - left by travelers who didn't want to climb the whole way to a real temple to ask for an easy road.""",
    "clivus_final",
)

room(
    "clivus_final_approach",
    "Upper Approach to the Capitoline",
    """|YThe grade eases at last|n, and the Temple of Jupiter's roofline is finally visible whole rather than in glimpses - gilded, immense, exactly as imposing as it's supposed to be. |cThe air itself feels different up here|n, thinner and somehow more formal.""",
    "clivus_final",
)

room(
    "asylum_threshold",
    "The Asylum's Threshold",
    """|YThe road opens without warning into a flat saddle of ground|n between two rising summits - the way the whole hill has been quietly building toward this point without saying so. Old trees crowd the near edge of a grove ahead, and the road itself seems unsure whether it's still a road or has already become something older.""",
    "clivus_final",
)

# ------------------------------------------------------------------
# ZONE 2 - The Asylum (3 rooms) - the real non-linear hub.
# ------------------------------------------------------------------

room(
    "asylum_grove",
    "The Asylum Grove",
    """|YOld, gnarled trees crowd around a worn stone altar|n at the low point between the Capitoline's two summits - this, tradition holds, is where Romulus himself once opened a sanctuary to any fugitive or outcast willing to come help populate his young city. |cWhatever you think of the story|n, the grove still carries something of that old promise: paths lead off in every direction from here, toward the Capitolium ahead, the Arx above, and quieter places besides.""",
    "asylum",
)

room(
    "asylum_sanctuary_stone",
    "The Sanctuary Stone",
    """|YA single weathered stone|n stands apart from the grove's trees, its surface worn nearly smooth, though a shallow inscription is still just barely legible if you know where to look. |wThis is said to mark the exact spot|n where Romulus stood when he declared this ground a refuge - a small claim, easy to miss, resting on an enormous one.""",
    "asylum",
)

room(
    "asylum_grove_path",
    "A Quiet Grove Path",
    """|YA narrower path breaks off from the main grove|n, winding between the trees toward quieter corners of the hill - away from both summits, toward places most visitors never bother to find. The crowd noise from the Forum, faint even at the Asylum, disappears entirely back here.""",
    "asylum",
)

# ------------------------------------------------------------------
# ZONE 3 - Main summit plateau (4 rooms) - approach to the Capitolium.
# ------------------------------------------------------------------

room(
    "summit_stairway_foot",
    "Foot of the Great Stairway",
    """|WA truly enormous stairway rises ahead of you|n, cut from pale stone and wide enough for a dozen people to climb it shoulder to shoulder - and on the right day, that's exactly what happens. |YThe Temple of Jupiter Optimus Maximus|n waits at its head, close enough now to feel less like a destination and more like a presence.""",
    "summit",
)

room(
    "summit_east_plateau",
    "Eastern Plateau",
    """|YOpen paved ground|n stretches along the temple's eastern approach, plenty of room for a crowd to gather - and on triumph days, a crowd does, packed shoulder to shoulder to watch a general's procession complete its climb to give thanks at the temple that started the whole tradition of triumphs in the first place.""",
    "summit",
)

room(
    "summit_west_plateau",
    "Western Plateau",
    """|cA quieter stretch of open ground|n on the temple's western side, popular with people who want the view more than the crowd. |WFrom here the whole city spreads out below|n - the Tiber a pale ribbon in the distance, rooftops and temple pediments layered all the way to the horizon.""",
    "summit",
)

room(
    "summit_stairway_top",
    "Top of the Great Stairway",
    """|WThe stairway ends at the temple's own portico|n, immense columns rising directly ahead, close enough now to make out individual details in the carved pediment above. |YThis is the last open ground before the temple itself|n - triumphal processions end here, and new consuls have climbed these exact steps to swear their oath of office for longer than anyone can precisely say.""",
    "summit",
)

# ------------------------------------------------------------------
# ZONE 4 - Temple of Jupiter Optimus Maximus (7 rooms) - the centerpiece.
# ------------------------------------------------------------------

room(
    "temple_portico",
    "The Temple Portico",
    """|WColumns rise on every side|n, each one wider than a person can reach around, holding up a roofline gilded bright enough to hurt to look at directly in full sun. |YThis is the single most important religious site in Rome|n, and the portico makes sure you feel that before you've even stepped inside - the cella ahead, quieter side chambers to either side.""",
    "temple",
)

room(
    "temple_cella_jupiter",
    "Main Cella - Jupiter",
    """|YA massive cult statue of Jupiter dominates the chamber|n, seated, thunderbolt in hand, gilded details on the ceiling scattering what little light reaches this deep into the temple across the floor in slow, shifting patterns. |WThis is the room the entire complex exists to hold|n - everything else on this hill, in some sense, is an approach to this one chamber.""",
    "temple",
)

room(
    "temple_cella_juno",
    "Side Chamber - Juno",
    """|mA separate, quieter chamber|n holds its own cult statue - Juno, regal and composed, set apart from her husband's grander central hall by more than just a wall. |cThe air here feels deliberately calmer|n, watched over rather than dominated.""",
    "temple",
)

room(
    "temple_cella_minerva",
    "Side Chamber - Minerva",
    """|WA third chamber balances Juno's|n on the cella's other side, Minerva's own cult statue rendered with an owl at her feet and a spear at rest rather than raised - wisdom held in reserve, not war on display. Together the three chambers make up the Capitoline Triad, the heart of Roman state religion under one roof.""",
    "temple",
)

room(
    "temple_oath_antechamber",
    "The Oath Antechamber",
    """|YA smaller, formal chamber|n opens off the portico, bare of the grander decoration found deeper in the temple - deliberately so. |wEvery incoming consul has sworn their oath of office in this exact room|n at the start of each year, political power and religious sanction meeting in the same short ceremony.""",
    "temple",
)

room(
    "temple_offerings_hall",
    "The Offerings Hall",
    """|YCenturies of triumphal dedications crowd this long hall|n - captured standards, victory wreaths gone dull with age, arms and armor stripped from enemies whose names have mostly been forgotten even as their weapons remain. |cEvery triumphant general in Roman history has left something here.|n""",
    "temple",
)

room(
    "temple_inner_sanctum",
    "The Inner Sanctum",
    """|KA restricted chamber|n sits behind the main cella, accessible in-story only to the temple's own priesthood - you're only standing here at all because someone with real standing let you. |YA locked reliquary|n holds what the priests guard most closely; the air feels held, deliberately still.""",
    "temple",
)

# ------------------------------------------------------------------
# ZONE 5 - The Arx (5 rooms) - the citadel, a genuinely separate peak.
# ------------------------------------------------------------------

room(
    "arx_approach",
    "The Arx Approach",
    """|YA narrower, more exposed path|n climbs toward the hill's northern summit, distinctly separate terrain from the wide processional ground around Jupiter's temple. |cThe wind picks up noticeably here|n - this side of the hill has always been built for watching, not for ceremony.""",
    "arx",
)

room(
    "arx_watchpoint",
    "The Watch Point",
    """|WA real lookout|n, used for exactly what it looks built for - watching the ground below and the horizon beyond it for anything worth raising an alarm over. |YThe view stretches for miles|n on a clear day, the whole city and the countryside past it laid out below.""",
    "arx",
)

room(
    "arx_temple_moneta",
    "Temple of Juno Moneta",
    """|mA more modest temple|n than Jupiter's, but no less genuinely important - this is Juno in her aspect as Moneta, "the Warner," credited with once alerting Rome itself to danger. |YThe word for money descends directly from her name|n, struck here for generations before the word ever meant anything else.""",
    "arx",
)

room(
    "arx_mint_workshop",
    "The Mint Workshop",
    """|YHeat and noise fill this working chamber|n, attached directly to Juno Moneta's own temple - this is where Roman coinage is actually struck, hammer falling on die, blank silver and bronze becoming currency one careful strike at a time. |cEvery coin that ever crossed your palm may have started exactly here.|n""",
    "arx",
)

room(
    "arx_geese_enclosure",
    "The Sacred Geese",
    """|YA fenced enclosure holds Juno's sacred geese|n, kept and fed at public expense in gratitude for a night, generations ago, when their honking alone is credited with waking the garrison in time to stop a Gallic raiding party from climbing this exact hill unseen. |wThey are, by all accounts, still just as loud.|n""",
    "arx",
)

# ------------------------------------------------------------------
# ZONE 6 - Tarpeian Rock (3 rooms) - a genuinely ominous detour.
# ------------------------------------------------------------------

room(
    "tarpeian_approach",
    "The Tarpeian Approach",
    """|KThe path grows noticeably quieter here|n, fewer people about, conversation dropping to something closer to a murmur without anyone quite deciding to do it. |cSomething about this stretch of the hill discourages loitering.|n""",
    "tarpeian",
)

room(
    "tarpeian_cliff_edge",
    "The Tarpeian Rock",
    """|KA sheer cliff drops away without warning|n, the city spread out far below in a way that reads less like a view and more like a warning. |wThis is where traitors have historically been thrown|n - the drop is real, and standing at its edge makes that fact impossible to treat as just a story.""",
    "tarpeian",
)

room(
    "tarpeian_base",
    "The Base of the Rock",
    """|KA narrow path winds down to the foot of the cliff|n, reached this way rather than by the obvious shorter route straight down. |cThe ground here has a heaviness to it|n that has nothing to do with the terrain - this is where the fallen have historically been recovered, and the space holds that history without needing to say much about it.""",
    "tarpeian",
)

# ------------------------------------------------------------------
# ZONE 7 - Minor temples & shrines (4 rooms).
# ------------------------------------------------------------------

room(
    "temple_veiovis",
    "Temple of Veiovis",
    """|gA small, strange temple|n dedicated to Veiovis - a minor god, young in every depiction, sometimes read as a kind of anti-Jupiter or an echo of the underworld tucked improbably close to Jupiter's own grand house. |cThe stonework here feels older and less certain of itself|n than anything on the main summit.""",
    "minor_temples",
)

room(
    "temple_fides",
    "Temple of Fides",
    """|WA quiet, dignified temple|n to Fides - Good Faith personified, patron of oaths and treaties both between people and between states. |YFittingly close to where consuls swear their own oaths nearby|n, though this temple keeps a far smaller crowd.""",
    "minor_temples",
)

room(
    "roadside_shrine_minor",
    "A Minor Roadside Shrine",
    """|gAn easy shrine to miss|n, small and unadorned, tended by a single attendant for a god most visitors don't recognize by name and don't stop to ask about. |cA few humble offerings|n - bread, a handful of coins - sit at its base regardless.""",
    "minor_temples",
)

room(
    "stonemason_yard",
    "A Stonemason's Yard",
    """|yBlocks of half-worked stone|n and stacked scaffolding fill this practical, unglamorous yard - every temple on this hill needs constant restoration, and this is where that endless, unglamorous work actually happens. |cChisels ring against stone somewhere nearby, a working-class counterpoint to all the sacred grandeur around it.|n""",
    "minor_temples",
)

# ============================================================
# LINKS - (room_a, dir_a, room_b, dir_b). "existing_clivus_near_top"
# is the special key mapping to the real, already-built live room
# "Clivus Capitolinus - Near the Summit".
# ============================================================

LINKS = [
    # --- Zone 1: Upper Clivus Capitolinus ---
    ("existing_clivus_near_top", "north", "clivus_final_base", "south"),
    ("clivus_final_base", "north", "clivus_final_switchback", "south"),
    ("clivus_final_switchback", "north", "clivus_final_approach", "south"),
    ("clivus_final_approach", "north", "asylum_threshold", "south"),

    # --- Zone 2: The Asylum (real branch point) ---
    ("asylum_threshold", "north", "asylum_grove", "south"),
    ("asylum_grove", "east", "asylum_sanctuary_stone", "west"),
    ("asylum_grove", "west", "asylum_grove_path", "east"),
    ("asylum_grove", "north", "summit_stairway_foot", "south"),
    ("asylum_grove", "up", "arx_approach", "down"),
    ("asylum_grove_path", "west", "temple_veiovis", "east"),
    ("asylum_grove_path", "south", "tarpeian_approach", "north"),

    # --- Zone 3: Main summit plateau ---
    ("summit_stairway_foot", "east", "summit_east_plateau", "west"),
    ("summit_stairway_foot", "west", "summit_west_plateau", "east"),
    ("summit_stairway_foot", "north", "summit_stairway_top", "south"),
    ("summit_stairway_top", "north", "temple_portico", "south"),

    # --- Zone 4: Temple of Jupiter Optimus Maximus ---
    ("temple_portico", "north", "temple_cella_jupiter", "south"),
    ("temple_portico", "west", "temple_oath_antechamber", "east"),
    ("temple_portico", "east", "temple_offerings_hall", "west"),
    ("temple_cella_jupiter", "west", "temple_cella_juno", "east"),
    ("temple_cella_jupiter", "east", "temple_cella_minerva", "west"),
    ("temple_cella_jupiter", "north", "temple_inner_sanctum", "south"),

    # --- Zone 5: The Arx ---
    ("arx_approach", "north", "arx_watchpoint", "south"),
    ("arx_watchpoint", "north", "arx_temple_moneta", "south"),
    ("arx_temple_moneta", "east", "arx_mint_workshop", "west"),
    ("arx_temple_moneta", "west", "arx_geese_enclosure", "east"),

    # --- Zone 6: Tarpeian Rock ---
    ("tarpeian_approach", "east", "tarpeian_cliff_edge", "west"),
    ("tarpeian_approach", "south", "tarpeian_base", "north"),

    # --- Zone 7: Minor temples & shrines ---
    ("temple_veiovis", "north", "temple_fides", "south"),
    ("temple_veiovis", "south", "stonemason_yard", "north"),
    ("temple_fides", "east", "roadside_shrine_minor", "west"),
]

# ============================================================
# NPCS - (room_key, name, kind, desc, extra)
# kind: "static" (extra=None), "wander" (extra=list of room_keys)
# ============================================================

NPCS = [
    (
        "asylum_grove", "Old Pontius", "static",
        "A beggar who has lived in this grove for decades, treated by "
        "regulars with a strange, old-fashioned respect that has "
        "nothing to do with his rags - the sanctuary tradition this "
        "ground was founded on technically still means something, even "
        "now, and everyone here seems to know it.",
        None,
    ),
    (
        "temple_cella_jupiter", "the Flamen Dialis", "static",
        "Jupiter's own high priest, robed in white wool and bound by "
        "an almost absurd number of ritual restrictions unique to his "
        "office - he cannot touch iron, cannot look upon an armed "
        "column, cannot spend a night away from his own bed. He moves "
        "through the cella like every step is being watched, because "
        "in his own understanding of the world, it is.",
        None,
    ),
    (
        "arx_watchpoint", "Watch-Captain Rufio", "static",
        "A career soldier posted to the Arx lookout, entirely "
        "unromantic about the legends surrounding the hill he's spent "
        "years standing watch on. He's heard every story about the "
        "geese and the sanctuary and the rock a hundred times each, "
        "and treats all of them with the same flat, professional "
        "shrug.",
        None,
    ),
    (
        "roadside_shrine_minor", "Sella", "static",
        "An elderly shrine-keeper, no title to speak of, tending a god "
        "most visitors couldn't name if asked. She's kept this small "
        "shrine swept and lit for longer than most of the state "
        "priests up the hill have been alive.",
        None,
    ),
    (
        "summit_stairway_top", "a temple guard", "static",
        "A guard posted at the temple's own entrance, more ceremonial "
        "than strictly necessary - nobody seriously threatens the "
        "Temple of Jupiter Optimus Maximus - but present anyway, "
        "because some duties exist to be seen as much as performed.",
        None,
    ),
    (
        "summit_east_plateau", "a pilgrim", "wander",
        "A traveler who has clearly come some real distance specifically "
        "to see this temple, craning their neck at the roofline with "
        "the unguarded expression of someone who didn't expect it to "
        "actually be this impressive up close.",
        ["summit_east_plateau", "summit_west_plateau", "summit_stairway_foot"],
    ),
    (
        "clivus_final_approach", "a breathless litter-bearer", "wander",
        "One of a team carrying an empty litter back down the hill, "
        "taking the climb at a pace that suggests the return trip is "
        "considerably less urgent than whatever delivery just happened "
        "at the top.",
        ["clivus_final_approach", "clivus_final_switchback", "clivus_final_base"],
    ),
]

# ============================================================
# OBJECTS - (room_key, obj_name, obj_desc)
# ============================================================

OBJECTS = [
    (
        "clivus_final_switchback", "the roadside altar",
        "A small, weathered altar tucked into the bend of the road, "
        "covered in modest offerings - a coin here, a wilted garland "
        "there - left by travelers who wanted a blessing for the climb "
        "without detouring to a real temple to ask for one."
    ),
    (
        "asylum_sanctuary_stone", "the sanctuary inscription",
        "A shallow inscription cut into the sanctuary stone, worn "
        "nearly to illegibility by weather and centuries of curious "
        "hands tracing the letters anyway. What remains legible names "
        "this ground a refuge, open to any who reach it - the exact "
        "claim the grove is named for."
    ),
    (
        "temple_inner_sanctum", "the Sibylline Books",
        "A locked reliquary holds a collection of prophetic texts, "
        "consulted only in times of genuine crisis and only by special "
        "appointment of the Senate itself. Nobody outside the "
        "priesthood has read them in living memory - their reputation "
        "rests entirely on the handful of times they're said to have "
        "actually mattered."
    ),
    (
        "temple_offerings_hall", "a captured legionary standard",
        "A weathered military standard, clearly not Roman-made, "
        "mounted with a small plaque too faded now to read. Someone, "
        "once, took this from an enemy at real cost and gave it to the "
        "god rather than keep it."
    ),
    (
        "temple_offerings_hall", "a golden victory wreath",
        "A wreath of hammered gold laurel leaves, dulled with age but "
        "unmistakably ceremonial - the kind of thing awarded, not "
        "bought, for a triumph considered genuinely worth commemorating."
    ),
    (
        "temple_offerings_hall", "a shattered barbarian shield",
        "A large shield, foreign in make, split nearly in two by "
        "whatever blow ended the fight it was carried into. Left here "
        "not as a trophy of the enemy's skill, but of exactly the "
        "opposite."
    ),
    (
        "arx_mint_workshop", "a rack of coin dies",
        "Iron dies lined up in careful rows, each one engraved in "
        "reverse with the design that will be struck into the next "
        "batch of coinage - a portrait, an eagle, a god's profile, "
        "waiting to be hammered into blank metal one strike at a time."
    ),
    (
        "tarpeian_cliff_edge", "a weathered warning inscription",
        "A short inscription cut into the stone near the cliff's edge, "
        "old enough that its exact wording has softened with weather - "
        "but its point, standing here, needs no translation."
    ),
]

# ============================================================
# ECHOES - room_key -> list of ambient messages
# ============================================================

ECHOES = {
    "clivus_final_base": [
        "|YA cart loaded with offerings creaks past, headed the same direction you are.|n",
        "|cA distant priest's chant drifts down from somewhere above.|n",
    ],
    "asylum_grove": [
        "|gSomewhere in the old trees, a bird you can't quite see keeps calling, the same three notes, over and over.|n",
        "|cLeaves stir in a breeze that doesn't seem to reach the ground.|n",
    ],
    "summit_stairway_foot": [
        "|YSomewhere below, in the city proper, a horn sounds - the kind used to signal a procession is on its way.|n",
        "|WSunlight catches the temple's gilded roofline and scatters for a moment, blinding.|n",
    ],
    "temple_cella_jupiter": [
        "|YThe gilded ceiling catches what little light reaches this deep into the temple, scattering it in slow, shifting patterns across the floor.|n",
        "|cSomewhere unseen, incense smoke curls upward in a thin, unbroken line.|n",
    ],
    "arx_geese_enclosure": [
        "|wThe geese stir at nothing you can see, a ripple of noise passing through the flock and then falling quiet again - just as it's said they once did, the night the Gauls tried to climb the hill unseen.|n",
    ],
    "tarpeian_cliff_edge": [
        "|KThe wind moves differently out here than anywhere else on the hill - louder, colder, like it's trying to push you back the way you came.|n",
    ],
}


# ============================================================
# VALIDATION
# ============================================================

_DIR_OPPOSITES = {
    "north": "south", "south": "north",
    "east": "west", "west": "east",
    "up": "down", "down": "up",
    "in": "out", "out": "in",
    "northeast": "southwest", "southwest": "northeast",
    "northwest": "southeast", "southeast": "northwest",
}


def _reverse_dir(d):
    return _DIR_OPPOSITES.get(d)


def validate():
    errors = []

    all_keys = set(ROOMS.keys()) | {"existing_clivus_near_top"}

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
    queue = ["existing_clivus_near_top"]
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
                    errors.append("NPC wander_rooms references unknown room: %s" % wr)

    for room_key, _obj_name, _obj_desc in OBJECTS:
        if room_key not in all_keys:
            errors.append("Object references unknown room: %s" % room_key)

    for room_key in ECHOES:
        if room_key not in all_keys:
            errors.append("Echo references unknown room: %s" % room_key)

    return errors


if __name__ == "__main__":
    errs = validate()
    if errs:
        print("VALIDATION FAILED:")
        for e in errs:
            print(" -", e)
    else:
        print("Validation passed. %d rooms, %d links, %d NPCs, %d objects, %d echo rooms." % (
            len(ROOMS), len(LINKS), len(NPCS), len(OBJECTS), len(ECHOES)
        ))
