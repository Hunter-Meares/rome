"""
The Aventine Hill - a validated, in-memory description of every room,
exit, NPC, and object before anything touches the live database. Same
pattern as every zone before it: data + a standalone validator, no
Django needed, run before a single database write happens.

Attaches to the real, already-built "The Far Garden" room (part of
Palatine Hill, world/batch_palatine_data.py) via its unused "south"
exit - confirmed live to be the room's only current exit besides
"west," and thematically apt: a secluded perimeter garden is exactly
where a path off the hill, away from the palace's public face, would
plausibly begin. Real geography backs the direction too - the
Aventine rises on the far side of the valley the Palatine's southern
slope looks down into (the same valley that would eventually hold the
Circus Maximus).

Geographic-accuracy scale (see world/batch_library_data.py's docstring
for the full model): real straight-line distance between the Palatine
and the Aventine is roughly 800m-1.2km, several times farther than
either the Library's or the Domus Aurea's gap (both under 500m, both
given a 1-room floor connector). This is the first zone in the
expansion that actually earns a real multi-room road rather than the
floor value - 4 connector rooms, tracing the historically real path
down off the Palatine, across the valley, and up the Aventine's own
slope.

Also the site of a genuine, deliberate tonal contrast the user's
original proposal called for: the Aventine was historically the
plebeian stronghold (the secessio plebis - Rome's common people
literally withdrawing here in protest, more than once, until the
patrician Senate met their demands) and home to the Aventine Triad
(Ceres, Liber, and Libera) - the plebeians' own gods, deliberately
distinct from the patrician Capitoline Triad (Jupiter, Juno, Minerva)
already built atop the Capitoline. Imperial-era Aventine also became
a fashionable, wealthy residential district, and sat directly above
Rome's real river port (the Emporium) and Monte Testaccio - an actual
hill made almost entirely of broken, discarded amphorae, a genuinely
strange and real feature of the ancient city.

Run this file directly (`python3 batch_aventine_data.py`) to validate
before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ------------------------------------------------------------------
# Connector (4 rooms) - the geographic-accuracy road, see docstring
# ------------------------------------------------------------------

room(
    "aventine_road_descent",
    "The Descent from the Palatine",
    """|wA narrow path|n drops away from the palace grounds' quieter edge, switching back twice before the noise of the Palatine fades behind you entirely. |YRome's grandest hill|n gives way, step by step, to open ground that answers to no single household at all.""",
    "aventine_road",
)

room(
    "aventine_road_valley",
    "Along the Circus Maximus Valley",
    """|YA long, open valley|n runs between the two hills, flat enough that a crowd could gather here in real numbers if it ever needed to. |wSome say a proper racing track will eventually fill this exact stretch of ground|n - for now, it's just a wide, unclaimed lowland, grass worn thin by whoever's already taken to cutting through it.""",
    "aventine_road",
)

room(
    "aventine_road_ford",
    "Fording the Valley Stream",
    """|cA shallow stream|n crosses the valley floor here, easy enough to wade in dry weather, considerably less so after real rain. |wA few flat stones|n, clearly placed on purpose, offer an imperfect but appreciated alternative to simply getting wet.""",
    "aventine_road",
)

room(
    "aventine_road_climb",
    "The Climb to the Aventine",
    """|wThe ground rises again|n on the valley's far side, the path narrowing as it switches back up the Aventine's own slope. |YThe city changes character with every step upward|n - whatever waits at the top has never quite belonged to the same Rome as the hill just crossed behind you.""",
    "aventine_road",
)

# ------------------------------------------------------------------
# Hub (2 rooms)
# ------------------------------------------------------------------

room(
    "aventine_plaza",
    "The Aventine Plaza",
    """|YAn open plaza|n marking the true summit of the climb, roads branching off toward every corner of the district beyond it. |wUnlike the Forum's studied grandeur|n, this plaza feels lived-in rather than performed for - real foot traffic, real errands, none of it staged for anyone watching.""",
    "aventine",
)

room(
    "aventine_fountain_plaza",
    "The Aventine Fountain Plaza",
    """|cA smaller plaza|n built around a plain, working fountain - no grand statuary, just clean water and a wide stone basin worn smooth by generations of hands and jars. |wThis is where the district's actual daily business gets discussed|n, plaza gossip doing the same job here that the Forum's Rostra does uphill and across the valley.""",
    "aventine",
)

# ------------------------------------------------------------------
# Temple of Diana Aventina (4 rooms)
# ------------------------------------------------------------------

room(
    "aventine_diana_portico",
    "Portico of the Temple of Diana",
    """|YA columned portico|n fronts the temple, more restrained in scale than the Capitoline's great state temples - fitting, for a goddess whose real domain has always been the wild edge of things rather than the city's own center.""",
    "aventine",
)

room(
    "aventine_diana_cella",
    "Temple of Diana Aventina - Main Cella",
    """|wThe goddess's cult statue|n stands at the far end of the cella, bow in hand, gaze fixed somewhere past the worshippers in front of her rather than on them directly. |YThis temple predates much of the city's grander architecture|n - one of Rome's oldest federal shrines, older than most of what stands on the Capitoline.""",
    "aventine",
)

room(
    "aventine_diana_grove",
    "The Sacred Grove",
    """|gA small planted grove|n behind the temple, deliberately left less manicured than a formal garden - Diana's own domain has never been the tended and the ordered. |wA hush settles here|n that the plaza just downhill never quite manages.""",
    "aventine",
)

room(
    "aventine_diana_priestess",
    "The Priestess's Chamber",
    """|wA modest private chamber|n behind the cella, records of offerings and festival dates kept in careful order on a single shelf. |YFar less ceremony surrounds this priesthood|n than the Vestals' famous discipline across the valley - Diana's service asks for devotion, not spectacle.""",
    "aventine",
)

# ------------------------------------------------------------------
# The Aventine Triad - Ceres, Liber, and Libera (4 rooms)
# ------------------------------------------------------------------

room(
    "aventine_triad_courtyard",
    "Courtyard of the Aventine Triad",
    """|YA shared courtyard|n serving both cellae beyond it - Ceres on one side, Liber and Libera on the other. |wThis is the plebeians' own answer to the Capitoline Triad uphill and across the valley|n: where Jupiter, Juno, and Minerva watch over the patrician state, these three have always belonged to everyone else.""",
    "aventine",
)

room(
    "aventine_triad_ceres_cella",
    "Cella of Ceres",
    """|wA statue of Ceres|n stands crowned with wheat, offerings of grain and bread left at her feet by visitors who understand her domain in the most literal, immediate way possible. |YRome's grain supply is treated as a matter of state|n; this temple has always treated it as a matter of survival instead.""",
    "aventine",
)

room(
    "aventine_triad_liber_cella",
    "Cella of Liber and Libera",
    """|YTwo statues share this cella|n, Liber and Libera together - wine, fertility, and a real, specific association with plebeian freedom that the patrician state has never fully been comfortable with. |wFresh offerings here skew heavily toward wine|n, unsurprisingly.""",
    "aventine",
)

room(
    "aventine_aediles_office",
    "Office of the Plebeian Aediles",
    """|wA working office|n attached directly to the temple - the plebeian aediles' own base, historically tied to this exact shrine rather than any grander state building. |YGrain distribution records, market regulations, and festival funding all get decided from a room considerably less impressive than the decisions themselves.""",
    "aventine",
)

# ------------------------------------------------------------------
# Secession memorial (3 rooms)
# ------------------------------------------------------------------

room(
    "aventine_secession_plaza",
    "Plaza of the First Secession",
    """|YA modest plaza|n, nowhere near as grand as anything in the Forum, but genuinely significant - this is where Rome's plebeians are said to have withdrawn entirely from the city, more than once, until the patrician Senate finally agreed to real concessions. |wThe patricians never much liked commemorating that|n; the plebeians made sure it got commemorated anyway.""",
    "aventine",
)

room(
    "aventine_secession_stone",
    "The Secession Stone",
    """|wA plain stone marker|n, worn smooth by weather and by hands that have touched it for reasons ranging from reverence to simple habit. |YAn inscription names the year of the first withdrawal|n, plain lettering with none of the Forum's carved grandiosity - a commoners' monument, built by and for commoners.""",
    "aventine",
)

room(
    "aventine_elder_home",
    "The Elder's House",
    """|wA small, plain house|n just off the memorial plaza, its owner apparently content to live in the shadow of the very history he likes to talk about. |YAn old man's voice carries faintly from inside|n, recounting some version of the secession to whoever's willing to listen this time.""",
    "aventine",
)

# ------------------------------------------------------------------
# Residential quarter (4 rooms)
# ------------------------------------------------------------------

room(
    "aventine_wealthy_street",
    "Street of the New Aristocracy",
    """|YA street lined with genuinely fine houses|n, newer money than the Palatine's old imperial pedigree but no less determined to show it. |wThe Aventine's reputation has shifted hard|n in recent generations - from plebeian stronghold to fashionable address, without ever quite losing the memory of what it used to be.""",
    "aventine",
)

room(
    "aventine_domus_a_atrium",
    "Domus Fortunata - Atrium",
    """|wA well-appointed atrium|n, the household's wealth on comfortable, unhurried display - fine mosaic underfoot, a modest but genuine impluvium catching rainwater at the center of the room.""",
    "aventine",
)

room(
    "aventine_domus_a_garden",
    "Domus Fortunata - Garden",
    """|gA private garden|n behind the atrium, small but carefully tended - considerably more modest than the Palatine's grounds, but built on the exact same principle: a house that can afford unproductive, purely decorative space has clearly arrived.""",
    "aventine",
)

room(
    "aventine_domus_b_atrium",
    "Domus Marcella - Atrium",
    """|wA second grand atrium|n, this household's taste running toward bold color rather than restraint - painted walls in deep reds and golds, a clear statement from a family with something to prove and the means to prove it loudly.""",
    "aventine",
)

# ------------------------------------------------------------------
# Temple of Juno Regina (3 rooms)
# ------------------------------------------------------------------

room(
    "aventine_juno_portico",
    "Portico of the Temple of Juno Regina",
    """|YA columned portico|n, distinct from the Capitoline's Temple of Juno Moneta - this is Juno in a different aspect entirely, brought to Rome from a conquered rival city and given a home of her own rather than folded into an existing shrine.""",
    "aventine",
)

room(
    "aventine_juno_cella",
    "Temple of Juno Regina - Main Cella",
    """|wThe cult statue here|n carries itself with a foreign formality, subtly different in style from anything Roman-made - a reminder that this goddess arrived from elsewhere, brought home deliberately rather than always having belonged here.""",
    "aventine",
)

room(
    "aventine_juno_side_shrine",
    "Side Shrine of Juno Regina",
    """|wA smaller shrine|n off the main cella, older and plainer offerings collecting undisturbed in a corner few visitors bother to check. |YWhoever tends this temple|n clearly has more urgent priorities most days than dusting its quieter corners.""",
    "aventine",
)

# ------------------------------------------------------------------
# River, Emporium, and Monte Testaccio (7 rooms)
# ------------------------------------------------------------------

room(
    "aventine_market_street",
    "Aventine Market Street",
    """|YA busy street|n of small shops and stalls, considerably less polished than the wealthy quarter just uphill - this is where the Aventine's older, working character still shows through clearest.""",
    "aventine",
)

room(
    "aventine_river_descent",
    "Descent Toward the River",
    """|wThe street slopes down|n toward the Tiber, the smell of the river and the noise of real commerce both growing stronger with every step - Rome's grandest architecture has never been down this way, but its actual trade has always depended on it.""",
    "aventine",
)

room(
    "aventine_porta_trigemina",
    "The Porta Trigemina",
    """|YAn old gate|n in the city's boundary wall, worn smooth by centuries of cart traffic passing through toward the river port beyond it. |wEverything Rome imports by water|n eventually passes through a gate exactly like this one.""",
    "aventine",
)

room(
    "aventine_emporium_yard",
    "The Emporium Yard",
    """|YA vast open yard|n, Rome's real commercial river port - goods from across the empire arrive here first, long before any of it reaches a Forum shop or a noble household's table. |wThe noise and motion here rival the Forum's own|n, with none of the Forum's civic self-importance attached to it.""",
    "aventine",
)

room(
    "aventine_emporium_warehouse",
    "An Emporium Warehouse",
    """|wRow after row of storage|n, amphorae and crates stacked to the rafters - oil, wine, grain, and goods from provinces most of the dockworkers handling them will never actually see.""",
    "aventine",
)

room(
    "aventine_testaccio_slope",
    "The Slope of Monte Testaccio",
    """|rBroken pottery crunches underfoot|n with every step - this entire rise is built from centuries of discarded amphorae, each one used once to carry oil upriver and then deliberately smashed and stacked rather than reused. |wAn entire hill|n, made exclusively out of what the port didn't need anymore.""",
    "aventine",
)

room(
    "aventine_testaccio_summit",
    "Summit of Monte Testaccio",
    """|YFrom up here|n, the scale of the thing finally makes sense - an artificial hill of broken pottery, tall enough to look out over the Emporium's yards and warehouses and a real stretch of the river beyond them. |wA strange monument|n, built entirely by accident, one smashed jar at a time.""",
    "aventine",
)

room(
    "aventine_river_docks",
    "The River Docks",
    """|cThe Tiber itself runs past here|n, barges and smaller craft tied up along a real working dock. |wDockworkers move with the same practiced urgency|n as Trajan's Market's own crowd, cargo changing hands in a rhythm that never seems to fully stop.""",
    "aventine",
)

ROOM_COUNT_EXPECTED = 32


# ============================================================
# LINKS
# ============================================================

LINKS = [
    ("existing_far_garden", "south", "aventine_road_descent", "north"),
    ("aventine_road_descent", "south", "aventine_road_valley", "north"),
    ("aventine_road_valley", "south", "aventine_road_ford", "north"),
    ("aventine_road_ford", "south", "aventine_road_climb", "north"),
    ("aventine_road_climb", "south", "aventine_plaza", "north"),

    ("aventine_plaza", "east", "aventine_diana_portico", "west"),
    ("aventine_plaza", "west", "aventine_triad_courtyard", "east"),
    ("aventine_plaza", "south", "aventine_fountain_plaza", "north"),

    ("aventine_diana_portico", "north", "aventine_diana_cella", "south"),
    ("aventine_diana_cella", "east", "aventine_diana_grove", "west"),
    ("aventine_diana_cella", "north", "aventine_diana_priestess", "south"),

    ("aventine_triad_courtyard", "north", "aventine_triad_ceres_cella", "south"),
    ("aventine_triad_courtyard", "south", "aventine_triad_liber_cella", "north"),
    ("aventine_triad_ceres_cella", "east", "aventine_aediles_office", "west"),

    ("aventine_fountain_plaza", "east", "aventine_secession_plaza", "west"),
    ("aventine_secession_plaza", "north", "aventine_secession_stone", "south"),
    ("aventine_secession_plaza", "south", "aventine_elder_home", "north"),

    ("aventine_fountain_plaza", "west", "aventine_wealthy_street", "east"),
    ("aventine_wealthy_street", "north", "aventine_domus_a_atrium", "south"),
    ("aventine_domus_a_atrium", "east", "aventine_domus_a_garden", "west"),
    ("aventine_wealthy_street", "south", "aventine_domus_b_atrium", "north"),
    ("aventine_wealthy_street", "west", "aventine_juno_portico", "east"),

    ("aventine_juno_portico", "north", "aventine_juno_cella", "south"),
    ("aventine_juno_cella", "east", "aventine_juno_side_shrine", "west"),

    ("aventine_fountain_plaza", "south", "aventine_market_street", "north"),
    ("aventine_market_street", "south", "aventine_river_descent", "north"),
    ("aventine_river_descent", "south", "aventine_porta_trigemina", "north"),
    ("aventine_porta_trigemina", "south", "aventine_emporium_yard", "north"),
    ("aventine_emporium_yard", "east", "aventine_emporium_warehouse", "west"),
    ("aventine_emporium_yard", "west", "aventine_testaccio_slope", "east"),
    ("aventine_testaccio_slope", "up", "aventine_testaccio_summit", "down"),
    ("aventine_emporium_yard", "south", "aventine_river_docks", "north"),
]


# ============================================================
# NPCS
# ============================================================
# Each entry: (room_key, name, desc, kind, extra)
#   kind "static"    - plain DefaultCharacter, stays put
#   kind "wander"    - DefaultCharacter + WanderingNPC script

NPCS = [
    (
        "aventine_diana_cella", "the priestess of Diana", "static",
        "A calm, weathered woman tending the goddess's cella with a "
        "quiet self-sufficiency that matches Diana's own domain - "
        "little ceremony, no crowd of assistants, just steady, "
        "unhurried devotion.",
        None,
    ),
    (
        "aventine_diana_grove", "a grove attendant", "static",
        "A younger attendant sweeping fallen leaves from the grove's "
        "paths without much apparent enthusiasm for undoing what the "
        "trees are just going to do again tomorrow.",
        None,
    ),
    (
        "aventine_triad_ceres_cella", "a priest of Ceres", "static",
        "A practical, plainspoken man who talks about the grain "
        "supply with the same gravity most priests reserve for the "
        "gods themselves - in this cella, the two subjects are barely "
        "distinguishable anyway.",
        None,
    ),
    (
        "aventine_aediles_office", "a plebeian aedile's clerk", "static",
        "A harried clerk buried in grain-distribution records and "
        "market complaints, working through a stack of petitions with "
        "the specific weariness of someone who knows tomorrow's stack "
        "will be exactly as tall.",
        None,
    ),
    (
        "aventine_elder_home", "the old man who remembers", "static",
        "An elderly man who has clearly told this story more times "
        "than he can count and shows no sign of tiring of it - the "
        "secession, as he tells it, wasn't ancient history handed down "
        "secondhand, but something his own family has never once let "
        "the neighborhood forget.",
        None,
    ),
    (
        "aventine_juno_cella", "a priestess of Juno Regina", "static",
        "A dignified woman tending a goddess whose worship, even here, "
        "still carries a faint trace of somewhere else - the accent in "
        "her own ritual phrasing gives away that this cult's roots "
        "aren't originally Roman at all.",
        None,
    ),
    (
        "aventine_wealthy_street", "a well-dressed resident", "wander",
        "Whoever's currently out enjoying the Street of the New "
        "Aristocracy at a leisurely pace, dressed carefully enough to "
        "make clear they belong to one of the households lining it "
        "rather than just passing through.",
        ["aventine_wealthy_street", "aventine_domus_a_atrium", "aventine_domus_b_atrium"],
    ),
    (
        "aventine_domus_a_garden", "a household servant", "static",
        "A servant tending Domus Fortunata's small garden with real, "
        "unforced care - not every household chore gets done with this "
        "much attention, and this one clearly gets more than most.",
        None,
    ),
    (
        "aventine_emporium_yard", "a customs official", "static",
        "An official checking incoming cargo against a manifest with "
        "the specific, unhurried thoroughness of someone whose job "
        "exists entirely to slow other people down - politely, but "
        "without exception.",
        None,
    ),
    (
        "aventine_emporium_warehouse", "a warehouse foreman", "static",
        "A foreman directing the movement of amphorae and crates with "
        "short, practiced calls, tracking more moving inventory in his "
        "head at once than most clerks manage with a written ledger.",
        None,
    ),
    (
        "aventine_testaccio_slope", "a pottery scavenger", "static",
        "A scavenger picking through the broken shards for anything "
        "still whole enough to be worth the effort - a strange, "
        "patient trade, performed on top of an entire hill built "
        "specifically because everything here was already judged "
        "worthless once.",
        None,
    ),
    (
        "aventine_river_docks", "a dockworker", "wander",
        "Whoever's currently hauling cargo along the docks - barges "
        "arrive on their own schedule, not anyone else's, and the work "
        "here never quite stops long enough to notice who's doing it "
        "at any given moment.",
        ["aventine_river_docks", "aventine_emporium_yard", "aventine_porta_trigemina"],
    ),
    (
        "aventine_fountain_plaza", "a fountain crowd", "wander",
        "Whoever's currently gathered at the fountain - a household "
        "servant filling jars, a pair of neighbors trading real news "
        "and rumor in equal measure, someone just resting in the "
        "shade for a moment before continuing on.",
        ["aventine_fountain_plaza", "aventine_plaza", "aventine_market_street"],
    ),
]


# ============================================================
# OBJECTS - lookable scenery, get:false() locked
# ============================================================

OBJECTS = [
    (
        "aventine_secession_stone", "the secession inscription",
        "Plain, deep-cut lettering naming the year the plebeians "
        "first withdrew from the city entirely - no ornamentation, no "
        "flourish, just a date and a fact the patrician state would "
        "clearly have preferred to leave unrecorded."
    ),
    (
        "aventine_triad_ceres_cella", "the statue of Ceres",
        "A statue crowned in carved wheat, offerings of grain and "
        "fresh bread left at her feet - the plebeians' own goddess of "
        "the harvest, worshipped here with an urgency the Capitoline's "
        "state cults have never quite needed to match."
    ),
    (
        "aventine_testaccio_summit", "the broken shards",
        "A closer look at the hill's actual surface: thousands upon "
        "thousands of broken amphora fragments, each one stamped with "
        "a maker's mark from some province or workshop, compacted into "
        "the ground underfoot by the sheer weight of everything piled "
        "above it."
    ),
    # Real bug found live: Diana's and Juno Regina's cellas already
    # described their own statue in prose (bow in hand; foreign
    # formality), and Liber/Libera's cella described two, but none of
    # the three had an actual examinable Object - same gap already
    # fixed for the Capitoline Triad and Caesar's temple. New detail
    # below in each case, not a restatement of the room's own desc.
    (
        "aventine_diana_cella", "the cult statue of Diana",
        "A hunting hound is carved crouched at her heel, ears back and "
        "body angled toward the door rather than up at her - alert to "
        "something beyond the room, the way a real hound would be, "
        "rather than posed for the goddess's own benefit."
    ),
    (
        "aventine_triad_liber_cella", "the statues of Liber and Libera",
        "A carved vine, heavy with grape clusters, winds from Liber's "
        "wrist across the space between the two figures to twine "
        "around Libera's - the one point the sculptor let the pair "
        "actually touch, linking them at the base rather than leaving "
        "them merely side by side."
    ),
    (
        "aventine_juno_cella", "the cult statue of Juno Regina",
        "Her diadem is cut in a sharp, geometric pattern unlike any "
        "other stonework on the hill - no local mason's other work in "
        "the city quite matches it, whatever workshop first carved her "
        "clearly learned its trade somewhere else entirely."
    ),
]


# ============================================================
# ECHOES
# ============================================================

ECHOES = {
    "aventine_fountain_plaza": [
        "|cWater splashes steadily into the fountain's worn stone basin.|n",
        "|wTwo neighbors trade gossip in low, unhurried voices nearby.|n",
    ],
    "aventine_emporium_yard": [
        "|YA foreman shouts an order somewhere across the yard.|n",
        "|wCargo thuds down from a cart, checked off against a manifest.|n",
        "|cGulls call somewhere overhead, drawn in by the smell of the river.|n",
    ],
    "aventine_testaccio_slope": [
        "|rA loose shard shifts and crunches somewhere further up the slope.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_far_garden"}

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
    queue = ["existing_far_garden"]
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
    print("Loaded %d new rooms (attaches to existing 'The Far Garden', Palatine Hill)." % len(ROOMS))
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
