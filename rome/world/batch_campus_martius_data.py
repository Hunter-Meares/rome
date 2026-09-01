"""
Campus Martius (including the Mausoleum of Augustus) and the retrofit
road connecting it to the already-built Pantheon - a validated,
in-memory description of every room, exit, NPC, and object before
anything touches the live database. Same pattern as every zone before
it: data + a standalone validator, no Django needed, run before a
single database write happens.

--------------------------------------------------------------------
THE RETROFIT (the first one actually built, not just flagged)

The Pantheon has been attached to Via Triumphalis (room #664) by a
single direct exit since it was built. Per world/batch_library_data.py's
geographic-accuracy scale model, the real distance between that area
and the Pantheon's actual historical site in the Campus Martius is
roughly 1.8-2km - several times farther than the Aventine's own
800m-1.2km gap, which already earned a real 4-room road. This gap
earns a real 7-room road.

Per direct instruction, this does NOT delete or rebuild the Pantheon's
existing 6 rooms, NPC, or altar object, and does NOT delete either
existing exit. Instead, world/setup_campus_martius_live.py finds the
two real, already-live exit objects - Via Triumphalis's "north" exit
(currently -> pantheon_approach) and Pantheon Approach's "south" exit
(currently -> Via Triumphalis) - and repoints their `destination`
in place, splicing 7 new road rooms into the middle. Both exits keep
their existing keys/aliases; a player who already knew "north from
Via Triumphalis leads toward the Pantheon" is still right, it's just
a genuinely longer trip now. The Pantheon's own 6 rooms are otherwise
completely untouched.

--------------------------------------------------------------------
CAMPUS MARTIUS ITSELF

Historically a large floodplain outside the sacred city boundary (the
Pomerium) - genuinely too big and too "outside" for the tight urban
fabric built everywhere else so far, used historically for military
musters and the Centuriate Assembly (armed citizens couldn't legally
assemble inside the Pomerium, so this is where that specific kind of
civic business actually happened). Real features included here: the
Ara Pacis (Augustus's Altar of Peace, its famous processional reliefs
still intact enough for modern museums to admire), the Saepta Julia
(a real voting-hall complex - not a generic "third temple," the
actual mechanism ordinary Romans cast ballots in), the Iseum Campense
(Temple of Isis - deliberately, explicitly a foreign cult, distinct in
architecture and priesthood from every other temple built anywhere
else in the game so far), and the Porticus of Pompey (a real
colonnaded portico complex - and, not incidentally, the actual site of
Julius Caesar's assassination, a genuinely dramatic real-history hook
sitting right there for the taking).

The Mausoleum of Augustus is built here too (8 rooms, per the user's
own proposal, which flagged it as needing no pushback) - correcting a
real error in that same proposal's own summary table, which called it
"already built." Only the Pantheon was actually live before this
session; the Mausoleum is entirely new.

Run this file directly (`python3 batch_campus_martius_data.py`) to
validate before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ------------------------------------------------------------------
# The retrofit road (7 rooms) - see docstring
# ------------------------------------------------------------------

room(
    "road_market_stalls",
    "Via Triumphalis - Past the Market Stalls",
    """|YThe road continues past a scattering of small stalls|n, none
    of them permanent enough to rate a real market's name - a fruit
    seller, a cobbler, someone reselling secondhand tools. |wOrdinary
    city business|n, entirely unconcerned with the grander architecture
    behind you.""",
    "via_triumphalis_road",
)

room(
    "road_crossroads",
    "A Busy Crossroads",
    """|wSeveral streets meet here|n in the kind of tangle that has
    nothing to do with any planned design - carts, pedestrians, and at
    least one argument over right-of-way all competing for the same
    small patch of paving.""",
    "via_triumphalis_road",
)

room(
    "road_insula_row",
    "Via Triumphalis - Insula Row",
    """|wA stretch of ordinary apartment blocks|n lines the road here,
    laundry strung between upper windows, nothing about the
    architecture suggesting anyone important lives behind any of these
    doors. |YMost of Rome actually looks like this|n, monumental
    architecture being very much the exception rather than the rule.""",
    "via_triumphalis_road",
)

room(
    "road_shrine",
    "A Roadside Shrine",
    """|YA small shrine|n set into a wall niche, a minor household or
    crossroads god tended by whoever happens to be passing rather than
    any formal priesthood. |wA few wilted flowers and a coin or two|n
    mark it as recently visited, if not exactly lavishly.""",
    "via_triumphalis_road",
)

room(
    "road_pomerium_stone",
    "The Pomerium Boundary Stone",
    """|YA weathered stone marker|n, inscribed with formal lettering
    naming this exact spot as the edge of the Pomerium - the sacred
    boundary of the city itself, not just its walls. |wArmed soldiers
    and sitting magistrates both lose certain powers the instant they
    cross this line|n, in either direction; the ground ahead answers to
    genuinely different rules than the ground behind.""",
    "via_triumphalis_road",
)

room(
    "road_open_stretch",
    "The Open Road Beyond the Pomerium",
    """|gThe dense city finally falls away|n, buildings thinning out
    into open, undeveloped ground. |wThe change is immediate and
    obvious|n - less noise, more sky, a very different Rome than the
    one just crossed through to get here.""",
    "via_triumphalis_road",
)

room(
    "road_campus_threshold",
    "Threshold of the Campus Martius",
    """|YThe road crests a last low rise|n, and the Campus Martius
    opens up ahead in full - a genuinely vast flat expanse, far larger
    than any single space built anywhere else in the city so far,
    dotted with temples, colonnades, and open muster ground.""",
    "via_triumphalis_road",
)

ROAD_ROOM_COUNT_EXPECTED = 7

# ------------------------------------------------------------------
# Hub / open field (3 rooms)
# ------------------------------------------------------------------

room(
    "campus_hub",
    "The Campus Martius",
    """|YAn open crossing point|n at the heart of the district, roads
    and colonnades branching off in every direction. |wNo single
    building dominates here|n the way the Capitoline's temples dominate
    their own hill - this is a district defined by open space first,
    architecture second.""",
    "campus_martius",
)

room(
    "campus_open_field",
    "The Open Field",
    """|gA genuinely enormous open field|n, kept deliberately clear of
    permanent construction - this ground has real, specific civic uses
    that need exactly this much empty space. |wSoldiers drill here|n
    on some days; on others, the field fills with citizens for
    business that could never legally happen inside the city proper.""",
    "campus_martius",
)

room(
    "campus_assembly_ground",
    "The Centuriate Assembly Ground",
    """|YA section of the field marked out|n for the Centuriate
    Assembly - the specific body of armed, property-owning citizens
    that elects Rome's highest magistrates. |wThe Pomerium legally
    keeps armed men out of the city itself|n, which is the entire
    reason this assembly has always had to meet all the way out here.""",
    "campus_martius",
)

# ------------------------------------------------------------------
# The Ara Pacis (4 rooms)
# ------------------------------------------------------------------

room(
    "ara_pacis_precinct_wall",
    "The Ara Pacis - Precinct Wall",
    """|YAn elaborately carved marble wall|n encloses the altar
    entirely, every surface given over to relief carving - garlands,
    ritual instruments, and processions that turn a simple altar
    enclosure into one of the most genuinely accomplished sculptural
    achievements in the entire city.""",
    "ara_pacis",
)

room(
    "ara_pacis_reliefs",
    "The Processional Reliefs",
    """|wA long carved procession|n wraps the enclosure's outer face -
    the Emperor's own family, priests, and attendants, walking in
    formal ritual order toward the altar itself. |YEvery figure here
    was clearly a real, specific person once|n, though most visitors
    can no longer say for certain which is which.""",
    "ara_pacis",
)

room(
    "ara_pacis_altar",
    "The Altar of Augustan Peace",
    """|YThe altar itself|n stands at the enclosure's center, raised on
    a low platform reached by a short flight of steps. |wDedicated to
    a peace that was, by the time this was built, still a genuinely
    novel thing|n for the city to be openly celebrating rather than
    simply assuming.""",
    "ara_pacis",
)

room(
    "ara_pacis_priests_chamber",
    "Ara Pacis - Priest's Chamber",
    """|wA small chamber|n behind the altar, holding the ritual
    implements needed for the altar's regular sacrifices - considerably
    less grand than the carved enclosure outside it, but no less
    necessary to the whole thing actually functioning.""",
    "ara_pacis",
)

# ------------------------------------------------------------------
# The Saepta Julia (5 rooms)
# ------------------------------------------------------------------

room(
    "saepta_entrance",
    "The Saepta Julia - Entrance Colonnade",
    """|YA long colonnaded entrance|n leads into the voting complex -
    a building whose entire purpose is mechanical rather than
    devotional, closer in spirit to the Forum's civic architecture
    than to anything built for a god.""",
    "saepta_julia",
)

room(
    "saepta_courtyard",
    "Saepta Julia - Central Courtyard",
    """|wAn open courtyard|n at the complex's heart, roads branching
    off toward the voting enclosures on one side and a row of shops on
    the other - on non-election days, this building earns its keep as
    ordinary commercial space instead.""",
    "saepta_julia",
)

room(
    "saepta_voting_hall",
    "The Voting Enclosures",
    """|YRows of narrow wooden enclosures|n, each one built to let a
    single citizen cast a ballot with a real, if imperfect, measure of
    privacy. |wThis is the actual physical mechanism of a Roman
    election|n, considerably less glamorous than either the candidates
    or the outcome usually manage to be.""",
    "saepta_julia",
)

room(
    "saepta_election_officials",
    "Office of the Election Officials",
    """|wA cramped office|n given over to the officials who actually
    run an election - tallying ballots, checking citizen rolls,
    settling disputes that inevitably arise over both. |YThe real work
    of Roman democracy|n happens in rooms exactly this unglamorous.""",
    "saepta_julia",
)

room(
    "saepta_gallery",
    "Saepta Julia - Shopping Gallery",
    """|wA row of shops|n lines this gallery, doing brisk business on
    every day the voting enclosures next door sit empty. |YA building
    built for democracy|n, apparently, still has bills to pay between
    elections.""",
    "saepta_julia",
)

# ------------------------------------------------------------------
# The Temple of Isis (5 rooms)
# ------------------------------------------------------------------

room(
    "isis_approach",
    "Approach to the Temple of Isis",
    """|YThe architecture shifts entirely|n here - no Roman column
    order looks quite like this. Carved motifs unfamiliar to every
    other temple in the city mark this ground as belonging to a
    genuinely foreign cult, tolerated and even fashionable, but never
    folded into Rome's own official religion.""",
    "temple_isis",
)

room(
    "isis_courtyard",
    "The Egyptian Courtyard",
    """|wA courtyard flanked by imported statuary|n - a real obelisk,
    carved sphinxes, forms that look nothing like anything on the
    Capitoline or in the Forum. |YEverything here was either shipped
    from Egypt directly|n or carved locally in careful, deliberate
    imitation of exactly that style.""",
    "temple_isis",
)

room(
    "isis_main_sanctuary",
    "The Sanctuary of Isis",
    """|YThe goddess's statue|n stands in a sanctuary that feels
    deliberately unlike every other cella in the city - dimmer,
    stranger, built around mysteries this temple's own priesthood
    doesn't share with casual visitors.""",
    "temple_isis",
)

room(
    "isis_priest_chamber",
    "The Priest's Chamber",
    """|wA priest's private chamber|n, its occupant recognizable on
    sight by a shaved head and plain white linen robes - conventions
    that mark this priesthood as visibly, deliberately distinct from
    every other temple's clergy in the city.""",
    "temple_isis",
)

room(
    "isis_sacred_pool",
    "The Sacred Pool",
    """|cA still, shallow pool|n, central to rites that draw explicitly
    on the goddess's real association with the Nile's own life-giving
    floods - a genuinely different relationship with water than
    anything the Baths' purely practical bathing sequence represents.""",
    "temple_isis",
)

# ------------------------------------------------------------------
# The Porticus of Pompey (4 rooms)
# ------------------------------------------------------------------

room(
    "portico_of_pompey",
    "The Portico of Pompey",
    """|YA vast colonnaded portico|n, part of a theater complex built
    by one of the Republic's own great generals - a building genuinely
    old enough, and significant enough, to have outlived the political
    order it was built to celebrate.""",
    "porticoes",
)

room(
    "portico_colonnade_walk",
    "A Long Colonnade Walk",
    """|wRow after row of columns|n stretch off in careful, repeating
    perspective, shade and open air alternating with every few steps -
    exactly the kind of unhurried walking space the Campus Martius has
    room to spare for.""",
    "porticoes",
)

room(
    "portico_assassination_site",
    "The Curia of Pompey",
    """|YA meeting hall attached to the portico|n, used on occasion for
    real Senate business when the Curia Julia itself isn't available.
    |wA particular date is still spoken of here in careful, lowered
    voices|n - this is the exact room where Julius Caesar was killed by
    his own Senate colleagues, a fact the building's current, ordinary
    use does very little to soften.""",
    "porticoes",
)

room(
    "portico_gardens",
    "The Portico Gardens",
    """|gA planted garden walk|n runs along the portico's outer edge,
    considerably more relaxed in mood than the somber hall just around
    the corner - proof that even a building with real, heavy history
    attached to it still has to function as ordinary public space most
    days.""",
    "porticoes",
)

# ------------------------------------------------------------------
# The Mausoleum of Augustus (8 rooms)
# ------------------------------------------------------------------

room(
    "mausoleum_approach",
    "Approach to the Mausoleum of Augustus",
    """|YA wide processional approach|n leads toward an enormous
    circular structure ahead - a scale of tomb no private citizen, and
    very few emperors since, has ever attempted to match.""",
    "mausoleum",
)

room(
    "mausoleum_obelisk_court",
    "The Obelisk Court",
    """|wTwin obelisks|n flank the entrance, imported at real expense
    specifically to mark this exact building as something beyond an
    ordinary tomb. |YEven in death|n, apparently, the founder of the
    Empire wasn't interested in being understated.""",
    "mausoleum",
)

room(
    "mausoleum_res_gestae",
    "The Res Gestae Pillars",
    """|YTwo great bronze pillars|n stand here, inscribed edge to edge
    with Augustus's own account of his life's achievements, written in
    his own words and posted for any literate visitor to read in full.
    |wA man who ruled an empire|n still apparently felt the need to
    make sure his own version of events got the last word.""",
    "mausoleum",
)

room(
    "mausoleum_outer_ring",
    "The Outer Ring",
    """|wA circular passage|n running the full width of the structure,
    concentric with several more rings still further in - the actual
    architecture of the tomb is built in genuinely massive, repeating
    circles, each one nested inside the last.""",
    "mausoleum",
)

room(
    "mausoleum_caretaker_room",
    "The Caretaker's Chamber",
    """|wA small, plain room|n set aside for whoever tends this
    structure day to day - lamps, cleaning tools, and a single stool,
    entirely unremarkable except for the scale of the building
    surrounding it.""",
    "mausoleum",
)

room(
    "mausoleum_inner_passage",
    "The Inner Passage",
    """|YA narrower, darker corridor|n leads deeper into the structure,
    the outer ring's daylight fading fast behind you. |wFew visitors
    ever actually make it this far in|n; most turn back at the outer
    ring, satisfied with having seen the building's exterior scale.""",
    "mausoleum",
)

room(
    "mausoleum_urn_chamber",
    "The Chamber of Urns",
    """|wNiche after niche|n line this chamber's walls, each one
    holding a funerary urn belonging to a member of the ruling family -
    generations of a single household, gathered here in careful,
    permanent order.""",
    "mausoleum",
)

room(
    "mausoleum_augustus_chamber",
    "The Central Chamber",
    """|YAt the very heart of the structure|n, a single chamber holds
    the founder of the Empire's own urn - considerably plainer than
    the scale of the building around it might suggest, and quieter
    than anywhere else in the entire complex. |wEven here|n, the man
    apparently didn't need the final room to shout as loud as everything
    leading up to it.""",
    "mausoleum",
)

CAMPUS_ROOM_COUNT_EXPECTED = 29  # hub(3) + ara pacis(4) + saepta(5) + isis(5) + porticoes(4) + mausoleum(8)
TOTAL_ROOM_COUNT_EXPECTED = ROAD_ROOM_COUNT_EXPECTED + CAMPUS_ROOM_COUNT_EXPECTED  # 36


# ============================================================
# LINKS
# ============================================================
# "existing_via_triumphalis" and "existing_pantheon_approach" are
# special-cased in the setup script: these two links are NOT new
# exits, they're the destination-rewire of the two real, already-live
# exits described in the module docstring.

LINKS = [
    ("existing_via_triumphalis", "north", "road_market_stalls", "south"),
    ("road_market_stalls", "north", "road_crossroads", "south"),
    ("road_crossroads", "north", "road_insula_row", "south"),
    ("road_insula_row", "north", "road_shrine", "south"),
    ("road_shrine", "north", "road_pomerium_stone", "south"),
    ("road_pomerium_stone", "north", "road_open_stretch", "south"),
    ("road_open_stretch", "north", "road_campus_threshold", "south"),
    ("road_campus_threshold", "north", "campus_hub", "south"),

    ("campus_hub", "north", "existing_pantheon_approach", "south"),
    ("campus_hub", "east", "ara_pacis_precinct_wall", "west"),
    ("campus_hub", "west", "saepta_entrance", "east"),
    ("campus_hub", "down", "campus_open_field", "up"),

    ("campus_open_field", "north", "campus_assembly_ground", "south"),
    ("campus_open_field", "east", "portico_of_pompey", "west"),
    ("campus_open_field", "west", "isis_approach", "east"),

    ("campus_assembly_ground", "north", "mausoleum_approach", "south"),

    ("ara_pacis_precinct_wall", "north", "ara_pacis_reliefs", "south"),
    ("ara_pacis_reliefs", "north", "ara_pacis_altar", "south"),
    ("ara_pacis_altar", "east", "ara_pacis_priests_chamber", "west"),

    ("saepta_entrance", "west", "saepta_courtyard", "east"),
    ("saepta_courtyard", "north", "saepta_voting_hall", "south"),
    ("saepta_courtyard", "south", "saepta_gallery", "north"),
    ("saepta_voting_hall", "west", "saepta_election_officials", "east"),

    ("isis_approach", "west", "isis_courtyard", "east"),
    ("isis_courtyard", "north", "isis_main_sanctuary", "south"),
    ("isis_courtyard", "south", "isis_sacred_pool", "north"),
    ("isis_main_sanctuary", "west", "isis_priest_chamber", "east"),

    ("portico_of_pompey", "north", "portico_colonnade_walk", "south"),
    ("portico_of_pompey", "east", "portico_gardens", "west"),
    ("portico_colonnade_walk", "east", "portico_assassination_site", "west"),

    ("mausoleum_approach", "north", "mausoleum_obelisk_court", "south"),
    ("mausoleum_obelisk_court", "north", "mausoleum_res_gestae", "south"),
    ("mausoleum_res_gestae", "north", "mausoleum_outer_ring", "south"),
    ("mausoleum_outer_ring", "east", "mausoleum_caretaker_room", "west"),
    ("mausoleum_outer_ring", "north", "mausoleum_inner_passage", "south"),
    ("mausoleum_inner_passage", "north", "mausoleum_urn_chamber", "south"),
    ("mausoleum_urn_chamber", "north", "mausoleum_augustus_chamber", "south"),
]


# ============================================================
# NPCS
# ============================================================
# Each entry: (room_key, name, desc, kind, extra)
#   kind "static"    - plain DefaultCharacter, stays put
#   kind "wander"    - DefaultCharacter + WanderingNPC script

NPCS = [
    (
        "road_pomerium_stone", "a watchful augur", "static",
        "An augur stationed near the boundary stone, less concerned "
        "with any individual traveler than with quietly noting the "
        "general state of the sky and the birds crossing it - the "
        "Pomerium itself is his actual jurisdiction, in a sense no "
        "ordinary magistrate's is.",
        None,
    ),
    (
        "road_crossroads", "a street crowd", "wander",
        "Whoever's currently tangled up in the crossroads' usual chaos "
        "- a cart driver, a pedestrian cutting through traffic at real "
        "personal risk, someone loudly certain they had the right of "
        "way.",
        ["road_crossroads", "road_market_stalls", "road_insula_row"],
    ),
    (
        "campus_hub", "a recruiting officer", "static",
        "An officer taking down names for the legions, working the "
        "edge of the open field with the patient persistence of "
        "someone who knows exactly how many of today's conversations "
        "will actually turn into a recruit.",
        None,
    ),
    (
        "campus_assembly_ground", "a centurion overseeing muster", "static",
        "A centurion watching a formation drill with the flat, "
        "unimpressed expression of someone who has personally overseen "
        "several hundred formations considerably worse than this one.",
        None,
    ),
    (
        "ara_pacis_altar", "a priest of the Altar of Peace", "static",
        "A priest tending an altar dedicated to something most temples "
        "in the city never quite bother commemorating directly - peace "
        "itself, treated here as an achievement worth its own formal "
        "cult.",
        None,
    ),
    (
        "ara_pacis_reliefs", "a sculptor's restorer", "static",
        "A restorer working carefully at one corner of the carved "
        "procession, matching new stone to old with a level of patience "
        "that suggests this exact repair has already taken considerably "
        "longer than planned.",
        None,
    ),
    (
        "saepta_voting_hall", "a citizen casting a ballot", "static",
        "A citizen working through the voting enclosure's simple but "
        "genuinely private mechanism, treating the whole process with "
        "more evident seriousness than the size of the room around it "
        "might suggest it deserves.",
        None,
    ),
    (
        "saepta_election_officials", "an election official", "static",
        "An official cross-checking a citizen roll against a stack of "
        "counted ballots, radiating the specific weariness of someone "
        "whose job exists entirely to be scrutinized by people who lost.",
        None,
    ),
    (
        "isis_main_sanctuary", "a priest of Isis", "static",
        "A priest with a shaved head and plain white linen robes, "
        "tending rites that borrow nothing from any Roman temple's own "
        "conventions - a genuinely different religious tradition, "
        "practiced here in full rather than adapted to fit in.",
        None,
    ),
    (
        "isis_sacred_pool", "an acolyte", "static",
        "A young acolyte performing a slow water rite at the pool's "
        "edge, movements deliberate and unhurried in a way that reads "
        "as real devotion rather than rote performance.",
        None,
    ),
    (
        "portico_of_pompey", "a philosopher", "wander",
        "Whoever's currently walking the portico's long colonnade at a "
        "contemplative pace, apparently more interested in the act of "
        "walking and thinking than in reaching any particular "
        "destination.",
        ["portico_of_pompey", "portico_colonnade_walk", "portico_gardens"],
    ),
    (
        "portico_assassination_site", "a somber historian", "static",
        "A visitor standing quietly near the hall's center, clearly "
        "not here by accident - the kind of person who comes to a room "
        "like this specifically because of what happened in it, not in "
        "spite of it.",
        None,
    ),
    (
        "mausoleum_approach", "a mausoleum guard", "static",
        "A guard stationed at the tomb's grand approach, posture "
        "considerably more formal here than anywhere else in the open, "
        "informal sprawl of the Campus Martius around it.",
        None,
    ),
    (
        "mausoleum_caretaker_room", "the tomb's caretaker", "static",
        "A caretaker who speaks about the ruling family's ashes with a "
        "matter-of-fact familiarity that comes only from tending the "
        "same small set of rooms, undisturbed, for a very long time.",
        None,
    ),
]


# ============================================================
# OBJECTS - lookable scenery, get:false() locked
# ============================================================

OBJECTS = [
    (
        "road_pomerium_stone", "the Pomerium marker",
        "A formally inscribed boundary stone, lettering still crisp "
        "despite the weather - a legal and religious line, not just a "
        "geographic one, that changes what certain kinds of Roman "
        "power are even allowed to do on either side of it."
    ),
    (
        "ara_pacis_reliefs", "the carved procession",
        "A long relief carving wrapping the altar's enclosure wall - "
        "real, identifiable figures from the Emperor's own household "
        "walking in formal religious procession, rendered with a level "
        "of individual detail most public monuments never bother with."
    ),
    (
        "saepta_voting_hall", "a voting urn",
        "A plain ceramic urn set at the end of one voting enclosure, "
        "waiting to receive a ballot - the entire weight of a Roman "
        "election ultimately comes down to a citizen's hand reaching "
        "into something exactly this unglamorous."
    ),
    (
        "isis_courtyard", "the imported obelisk",
        "A genuine Egyptian obelisk, hauled across the sea at "
        "real expense specifically to stand here - covered in "
        "hieroglyphs that essentially no one in the city can actually "
        "read, which doesn't appear to bother anyone."
    ),
    (
        "mausoleum_res_gestae", "the Res Gestae inscription",
        "Two bronze pillars, inscribed edge to edge with Augustus's "
        "own written account of his achievements - a first-person "
        "record, in his own words, of exactly how he wants his life to "
        "be remembered."
    ),
]


# ============================================================
# ECHOES
# ============================================================

ECHOES = {
    "campus_hub": [
        "|wA distant formation calls out a drill cadence somewhere across the field.|n",
        "|YThe open sky overhead feels genuinely different from the tight city streets behind you.|n",
    ],
    "saepta_voting_hall": [
        "|wA low murmur of citizens moving through the voting enclosures fills the hall.|n",
    ],
    "isis_sacred_pool": [
        "|cWater ripples gently across the sacred pool's still surface.|n",
    ],
    "mausoleum_augustus_chamber": [
        "|wThe chamber holds a genuine, heavy silence, undisturbed by anything from the complex outside it.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_via_triumphalis", "existing_pantheon_approach"}

    if len(ROOMS) != TOTAL_ROOM_COUNT_EXPECTED:
        errors.append("Expected %d rooms, got %d" % (TOTAL_ROOM_COUNT_EXPECTED, len(ROOMS)))

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

    unreachable = (set(ROOMS.keys()) | {"existing_pantheon_approach"}) - visited
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
    print("Loaded %d new rooms (%d road + %d Campus Martius/Mausoleum)." % (
        len(ROOMS), ROAD_ROOM_COUNT_EXPECTED, CAMPUS_ROOM_COUNT_EXPECTED
    ))
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
