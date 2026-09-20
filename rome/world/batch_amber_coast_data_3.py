"""
The Amber Coast - PART 3 OF THE 144-ROOM DESIGN (52 rooms), completing
the full location:
  Zone F - Terp Mound Quarter (12, levels 48-54)
  Zone H - Shipyard & Drydock (8, levels 52-58)
  Zone J - Fishing & Salt Flats (10, levels 49-55)
  Zone I - Nerthus's Sacred Isle (10, levels 55-63)
  Zone K - Deeper Coastal Wilds capstone (12, levels 61-71)

Extends the same live ROOMS dict Part 1/2 build - import order matters
(this file's own room() calls assume Part 1 and Part 2 have already
run and populated ROOMS). Same +21 level recalibration as the rest of
the location (see world/wilderness_amber_coast.py's docstring).

The Deeper Coastal Wilds capstone deliberately has TWO real entrances
converging into one network before its own final chamber - reached
"through the Amber Guard camp OR along the shore past the salt flats,"
per the design doc's own suggestion - rather than two fully separate
dead-end paths.
"""

from world.batch_amber_coast_data import ROOMS, room
from world.batch_amber_coast_data_2 import WARBAND_LINKS  # ensures Part 2 has run


# ======================================================================
# ZONE F - Terp Mound Quarter (12 rooms, levels 48-54)
# Residential quarter on raised earthen mounds - the "everyday people"
# zone, off the Trading Quarter.
# ======================================================================

room(
    "tm_gathering_1",
    "The West Well",
    """|wA raised earthen mound|n supports this whole corner of the
    quarter, real flood-country engineering holding it above the wet
    ground. |cA shared well|n stands at its center, worn smooth by
    generations of use.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_household_1",
    "A Net-Mender's Household",
    """|wA modest terp-mound home|n, nets and cordage drying across
    every available surface. |GA quiet, unhurried household|n, clearly
    used to this exact work.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_household_2",
    "A Bone-Carver's Household",
    """|wSmall bone and antler carvings|n cover a low worktable here,
    some barely started, some nearly finished. |YA few pieces are set
    with real amber chips|n.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_pen_1",
    "The Goat Pens",
    """|wA low fenced enclosure|n holds a real, restless handful of
    goats. |GTrampled straw and mud|n cover the ground in every
    direction.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_pen_2",
    "The Goose Pens",
    """|wA second, smaller pen|n holds geese loud enough to serve as a
    real, functioning alarm for the whole quarter. |GFeathers|n drift
    across the mound in the coastal wind.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_gathering_2",
    "The East Well",
    """|wA second raised mound|n, its own shared well ringed by low
    benches. |YAn old woman|n reads real omens in the gulls wheeling
    overhead, for anyone who asks.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_household_3",
    "An Elder's Household",
    """|wA well-kept mound home|n, real authority in how carefully
    everything here is arranged. |YA small amber charm|n hangs above
    the doorway.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_household_4",
    "A Weaver's Household",
    """|wA loom|n dominates this small home, real cloth in progress
    stretched across it. |GDyed wool|n hangs drying from every
    available beam.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_household_5",
    "A Fisherfolk Household",
    """|wNets and a real, well-used boat hook|n lean against the wall
    here - this household clearly works the tide flats, not the
    harbor proper. |cSalt air|n has gotten into everything.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_household_6",
    "A Quiet Household",
    """|wA small, unremarkable mound home|n, real everyday life visible
    in every worn detail. |GNothing here draws particular attention|n
    - which is exactly the point.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_shrine_1",
    "A Household Shrine - Ancestor Post",
    """|wA carved wooden post|n, worn smooth, marks this small shrine
    to household ancestors - distinct from the Nerthus cult proper.
    |YSmall amber offerings|n rest at its base.""",
    "amber_coast_terp_mounds",
)

room(
    "tm_shrine_2",
    "A Household Shrine - Hearth Gods",
    """|rA small, permanently-tended fire|n marks this shrine to the
    household's own hearth gods. |wReal, quiet devotion|n is visible
    in how well-kept it is.""",
    "amber_coast_terp_mounds",
)


# ======================================================================
# ZONE H - Shipyard & Drydock (8 rooms, levels 52-58)
# ======================================================================

room(
    "sy_drydock_1",
    "The Drydock - Outer Slip",
    """|wA real longship|n sits hauled up on wooden rollers here, hull
    exposed for repair. |rFresh pitch|n gleams wet along several
    seams.""",
    "amber_coast_shipyard",
)

room(
    "sy_drydock_2",
    "The Drydock - Inner Slip",
    """|wA second hull|n, further along in its repair, real shipwrights
    working over it with genuine focus. |wSawdust and wood shavings|n
    cover the ground throughout.""",
    "amber_coast_shipyard",
)

room(
    "sy_timber_1",
    "The Timber Yard - Rough Stock",
    """|wStacked raw timber|n, some pieces enormous, waits here for
    real shaping. |GBark still clings|n to more than a few of them.""",
    "amber_coast_shipyard",
)

room(
    "sy_timber_2",
    "The Timber Yard - Pitch Works",
    """|rBoiling pitch|n fills the air with real, acrid smoke - a
    genuine hazard alongside the actual craft. |wWorkers here move
    with visible, practiced caution|n.""",
    "amber_coast_shipyard",
)

room(
    "sy_timber_3",
    "The Timber Yard - Shaped Planks",
    """|wFinished planks|n, shaped and smoothed, stack in careful,
    ready rows. |YA real amber-oil finish|n has been worked into
    several of them.""",
    "amber_coast_shipyard",
)

room(
    "sy_shipwright_1",
    "The Shipwright's Hall - Outer Room",
    """|wTools of a real, exacting trade|n hang from every wall,
    each one clearly maintained with genuine care. |wSketched hull
    designs|n cover a nearby table.""",
    "amber_coast_shipyard",
)

room(
    "sy_shipwright_2",
    "The Shipwright's Hall - Inner Workshop",
    """|wThe master shipwright's own real workspace|n, more tools and
    half-finished fittings than anywhere else in the yard. |rForge-
    heat|n rolls from a small dedicated hearth in the corner.""",
    "amber_coast_shipyard",
)

room(
    "sy_half_built_ship",
    "The Half-Built Ship",
    """|wA genuine longship skeleton|n rises here, ribs exposed,
    clearly months from completion. |YSomething about seeing a real
    ship half-made|n is more striking than seeing one finished.""",
    "amber_coast_shipyard",
)


# ======================================================================
# ZONE J - Fishing & Salt Flats (10 rooms, levels 49-55)
# ======================================================================

room(
    "fsf_salt_1",
    "The Salt Pans - First Works",
    """|wShallow evaporation pans|n stretch out across flat, diked
    ground. |YReal, hard-won salt|n crusts visibly at every pan's
    edge.""",
    "amber_coast_salt_flats",
)

room(
    "fsf_salt_2",
    "The Salt Pans - Second Works",
    """|wMore pans|n continue here, workers raking real crystallized
    salt into waiting baskets. |cThe smell of brine|n is constant.""",
    "amber_coast_salt_flats",
)

room(
    "fsf_salt_3",
    "The Salt Pans - Storage",
    """|wSacked salt|n, this town's own second real export alongside
    amber, waits stacked for the next trade run. |YEven this looks
    like real, careful wealth|n.""",
    "amber_coast_salt_flats",
)

room(
    "fsf_smoke_1",
    "The Fish-Drying Racks",
    """|wLong racks|n hold split fish curing in the coastal wind.
    |Gulls wheel constantly|n, held off by nothing more than habit
    and shouted threats.""",
    "amber_coast_salt_flats",
)

room(
    "fsf_smoke_2",
    "The Smokehouse - Outer Room",
    """|rThick woodsmoke|n fills this low timber building, real fish
    hanging in every direction. |wThe smell clings to everything|n,
    including anyone who lingers too long.""",
    "amber_coast_salt_flats",
)

room(
    "fsf_smoke_3",
    "The Smokehouse - Inner Room",
    """|rA banked, carefully tended fire|n smolders here, real,
    practiced control over exactly how much smoke it produces.
    |wRows of finished, smoked fish|n hang ready for market.""",
    "amber_coast_salt_flats",
)

room(
    "fsf_tideflat_1",
    "The Tide Flats - Outer Mud",
    """|GThick, dark mud|n stretches out at low tide, real and
    genuinely difficult to cross quickly. |wSomething small|n
    occasionally darts underfoot.""",
    "amber_coast_salt_flats",
)

room(
    "fsf_tideflat_2",
    "The Tide Flats - Channel Crossing",
    """|cA shallow tidal channel|n cuts through the mud here, crossed
    by a real line of driven stakes. |GEasy to lose your footing|n if
    you're not paying attention.""",
    "amber_coast_salt_flats",
)

room(
    "fsf_hut_1",
    "A Fisherfolk Hut - First",
    """|wA small, weathered hut|n, nets and traps stacked against
    every outer wall. |GReal, ordinary coastal life|n, unremarkable
    and unbothered.""",
    "amber_coast_salt_flats",
)

room(
    "fsf_hut_2",
    "A Fisherfolk Hut - Last House",
    """|wThe last real house|n before open coastline takes over
    entirely. |wBeyond here|n, the shore belongs to whatever
    actually lives on it.""",
    "amber_coast_salt_flats",
)


# ======================================================================
# ZONE I - Nerthus's Sacred Isle (10 rooms, levels 55-63)
# A tidal island, reached by causeway from the Drowned Oath's own
# Causeway Watch.
# ======================================================================

room(
    "ni_causeway_1",
    "The Causeway - Landward End",
    """|cA pale line of packed stone|n runs out across open water here,
    visible only because the tide happens to be right. |wCross now|n,
    or wait for it to be right again.""",
    "amber_coast_sacred_isle",
)

room(
    "ni_causeway_2",
    "The Causeway - Island End",
    """|cWater laps at the stone|n on both sides here, the isle itself
    now close enough to make out real detail. |GReed and salt marsh|n
    grow right up to the causeway's edge.""",
    "amber_coast_sacred_isle",
)

room(
    "ni_grove_1",
    "The Sacred Grove - Outer Ring",
    """|GOld, wind-bent trees|n ring this part of the isle, planted or
    grown this way nobody quite remembers. |wThe air feels genuinely
    different here|n, quieter than it has any real reason to be.""",
    "amber_coast_sacred_isle",
)

room(
    "ni_grove_2",
    "The Sacred Grove - West Ring",
    """|GDense, deliberately untouched growth|n crowds close here, the
    isle's own wildness allowed to simply exist. |wNothing about this
    place invites a fight|n.""",
    "amber_coast_sacred_isle",
)

room(
    "ni_grove_3",
    "The Sacred Grove - East Ring",
    """|GThe grove continues|n on this side, real reverence visible in
    how carefully the ground itself is kept undisturbed. |YSmall
    amber offerings|n rest in the roots of more than one tree.""",
    "amber_coast_sacred_isle",
)

room(
    "ni_veiled_wagon",
    "The Veiled Wagon Shrine",
    """|wA real, covered wagon|n stands here, untouched by anyone but
    the priestess herself - Nerthus's own cult-object, exactly as
    described by those who've heard of this place secondhand.
    |YSomething about it demands real, genuine quiet|n.""",
    "amber_coast_sacred_isle",
)

room(
    "ni_priestess",
    "The Priestess's Dwelling",
    """|wA small, simple dwelling|n, its keeper devoted entirely to
    the isle and what it holds. |GReed matting|n covers the floor,
    plain and unadorned.""",
    "amber_coast_sacred_isle",
)

room(
    "ni_bog_pool",
    "The Bog-Pool",
    """|GDark, still water|n sits held in a natural hollow, real
    votive offerings visible just beneath the surface. |wSomething
    here has clearly been given up on purpose, more than once|n.""",
    "amber_coast_sacred_isle",
)

room(
    "ni_votive_shore_1",
    "The Votive Shore - First Stretch",
    """|cWaterline and reed|n meet here, isolated even by the isle's
    own already-quiet standards. |YSmall offerings|n rest half-buried
    in the wet sand.""",
    "amber_coast_sacred_isle",
)

room(
    "ni_votive_shore_2",
    "The Votive Shore - Furthest Point",
    """|cThe isle's own edge|n, water on every side but the way you
    came. |wThis is as far as Nerthus's own ground actually extends|n.""",
    "amber_coast_sacred_isle",
)


# ======================================================================
# ZONE K - Deeper Coastal Wilds (capstone, 12 rooms, levels 61-71)
# Two real entrances - through the Amber Guard camp, or along the
# shore past the salt flats - converging before the final chamber.
# ======================================================================

room(
    "dcw_cliff_1",
    "The Sea-Cliff Path - First Stretch",
    """|wA narrow path|n climbs along real, exposed sea-cliffs here,
    wind strong enough to matter. |cThe drop to the water|n is a long
    one.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_cliff_2",
    "The Sea-Cliff Path - Windswept Stretch",
    """|wThe path narrows further|n, real care required with every
    step. |cSalt spray|n reaches even this high above the water.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_cliff_3",
    "The Sea-Cliff Path - Furthest Point",
    """|wThe cliff path ends|n at a genuine outcrop, nothing ahead but
    open water and whatever holds this ground uncontested. |YFar
    below, real surf|n breaks white against the rocks.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_overlook_1",
    "Overlook - Facing the Strait",
    """|cThe strait itself opens out|n from here, grey water reaching
    toward a coastline you can't quite make out. |YThis is the
    northernmost real point of anything the tribe controls|n.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_overlook_2",
    "Overlook - The Edge of the Known Coast",
    """|cWater in every direction that matters|n, the land behind you
    the only real certainty left. |wWhatever lies further north|n is
    somebody else's story to tell.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_wreck_1",
    "The Wreck-Site - Hull",
    """|wA real, broken hull|n lies half-buried in the sand here,
    old enough that nobody alive remembers the wreck itself. |wSalt
    and time|n have worked at it for years.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_wreck_2",
    "The Wreck-Site - Scattered Cargo",
    """|wReal, scattered cargo|n lies half-buried alongside the wreck,
    whatever wasn't worth salvaging at the time. |YA glint of
    something valuable|n might still be worth a careful look.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_cave_1",
    "The Sea-Cave Complex - Entrance",
    """|wA dark opening|n leads into the cliff face here, tide-worn
    smooth over real, unmeasured time. |cWater drips steadily|n
    somewhere further in.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_cave_2",
    "The Sea-Cave Complex - Tidal Pool Chamber",
    """|cA real tidal pool|n fills much of this chamber, rising and
    falling with the sea outside. |wSomething moves|n in the deeper
    water more than once.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_cave_3",
    "The Sea-Cave Complex - Narrow Passage",
    """|wThe cave narrows|n here, real care needed to keep from
    scraping stone on every side. |cThe sound of the sea|n echoes
    strangely through the passage.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_cave_4",
    "The Sea-Cave Complex - Deep Chamber",
    """|wThe cave opens|n into a real, high chamber, old bones and
    older driftwood scattered across the floor. |YSomething has
    clearly claimed this place|n.""",
    "amber_coast_deeper_wilds",
)

room(
    "dcw_capstone",
    "The Furthest Reach",
    """|wThe cave ends|n in a real, final chamber - whatever holds
    this ground uncontested is here, and has been for a long time.
    |YNo warband, Roman patrol, or trade caravan has ever pushed
    this far north and come back to say much about it|n.""",
    "amber_coast_deeper_wilds",
)


TOTAL_ROOM_COUNT_EXPECTED = 56 + 36 + 52  # Parts 1 + 2 + 3 = 144

LINKS_PART3 = [
    # Zone F - Terp Mound Quarter, off the Trading Quarter.
    ("ac_trade_stall_3", "west", "tm_gathering_1", "east"),
    ("tm_gathering_1", "north", "tm_household_1", "south"),
    ("tm_gathering_1", "south", "tm_household_2", "north"),
    ("tm_gathering_1", "west", "tm_pen_1", "east"),
    ("tm_pen_1", "west", "tm_pen_2", "east"),
    ("tm_gathering_1", "northeast", "tm_gathering_2", "southwest"),
    ("tm_gathering_2", "north", "tm_household_3", "south"),
    ("tm_gathering_2", "south", "tm_household_4", "north"),
    ("tm_gathering_2", "east", "tm_shrine_1", "west"),
    ("tm_shrine_1", "east", "tm_shrine_2", "west"),
    ("tm_household_3", "east", "tm_household_5", "west"),
    ("tm_household_4", "east", "tm_household_6", "west"),

    # Zone H - Shipyard & Drydock, off the Harbor District.
    ("ac_harbor_cargo_yard_2", "west", "sy_drydock_1", "east"),
    ("sy_drydock_1", "north", "sy_drydock_2", "south"),
    ("sy_drydock_2", "north", "sy_timber_1", "south"),
    ("sy_timber_1", "east", "sy_timber_2", "west"),
    ("sy_timber_2", "east", "sy_timber_3", "west"),
    ("sy_timber_3", "north", "sy_shipwright_1", "south"),
    ("sy_shipwright_1", "east", "sy_shipwright_2", "west"),
    ("sy_shipwright_2", "north", "sy_half_built_ship", "south"),

    # Zone J - Fishing & Salt Flats, off the Terp Mound Quarter.
    ("tm_pen_2", "south", "fsf_salt_1", "north"),
    ("fsf_salt_1", "east", "fsf_salt_2", "west"),
    ("fsf_salt_2", "east", "fsf_salt_3", "west"),
    ("fsf_salt_3", "south", "fsf_smoke_1", "north"),
    ("fsf_smoke_1", "east", "fsf_smoke_2", "west"),
    ("fsf_smoke_2", "east", "fsf_smoke_3", "west"),
    ("fsf_smoke_3", "south", "fsf_tideflat_1", "north"),
    ("fsf_tideflat_1", "east", "fsf_tideflat_2", "west"),
    ("fsf_tideflat_2", "south", "fsf_hut_1", "north"),
    ("fsf_hut_1", "east", "fsf_hut_2", "west"),

    # Zone I - Nerthus's Sacred Isle, causeway off the Drowned Oath.
    ("do_causeway_watch", "south", "ni_causeway_1", "north"),
    ("ni_causeway_1", "south", "ni_causeway_2", "north"),
    ("ni_causeway_2", "south", "ni_grove_1", "north"),
    ("ni_grove_1", "east", "ni_grove_2", "west"),
    ("ni_grove_1", "west", "ni_grove_3", "east"),
    ("ni_grove_2", "north", "ni_veiled_wagon", "south"),
    ("ni_grove_3", "north", "ni_priestess", "south"),
    ("ni_priestess", "east", "ni_bog_pool", "west"),
    ("ni_bog_pool", "south", "ni_votive_shore_1", "north"),
    ("ni_votive_shore_1", "east", "ni_votive_shore_2", "west"),

    # Zone K - Deeper Coastal Wilds capstone - TWO entrances.
    # Entrance 1: through the Amber Guard camp.
    ("ag_muster_yard", "north", "dcw_cliff_1", "south"),
    ("dcw_cliff_1", "north", "dcw_cliff_2", "south"),
    ("dcw_cliff_2", "north", "dcw_cliff_3", "south"),
    ("dcw_cliff_3", "east", "dcw_overlook_1", "west"),
    ("dcw_overlook_1", "north", "dcw_overlook_2", "south"),
    # Entrance 2: along the shore, past the salt flats.
    ("fsf_hut_2", "south", "dcw_wreck_1", "north"),
    ("dcw_wreck_1", "east", "dcw_wreck_2", "west"),
    ("dcw_wreck_2", "north", "dcw_cave_1", "south"),
    ("dcw_cave_1", "east", "dcw_cave_2", "west"),
    # The two entrances converge here.
    ("dcw_overlook_1", "south", "dcw_cave_2", "north"),
    ("dcw_cave_2", "east", "dcw_cave_3", "west"),
    ("dcw_cave_3", "east", "dcw_cave_4", "west"),
    ("dcw_cave_4", "north", "dcw_capstone", "south"),
]
