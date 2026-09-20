"""
The Amber Coast - PART 2 OF THE 144-ROOM DESIGN: The Four Warbands
(36 rooms), the location's primary leveling backbone. Extends the same
ROOMS/LINKS the Part 1 file (world/batch_amber_coast_data.py) builds -
import that module first, this one keeps adding to its live ROOMS dict
and its own separate WARBAND_LINKS list (merged at setup time).

Per the design document's own post-draft note: each camp keeps a small
shared skeleton (approach, common fire, leader's tent) but at least
3-4 of its 9 rooms are unique to what that specific warband actually
does, so four camps don't read as one reskinned block. Preserved
exactly here - see each camp's own comment for which rooms are its
unique ones.

Levels are the design doc's own numbers +21 (see
world/wilderness_amber_coast.py's module docstring for why): Wave-
Riders 30-34 -> 51-55, Iron Tide 33-37 -> 54-58, Drowned Oath 36-40 ->
57-61, Amber Guard 38-42 -> 59-63.
"""

from world.batch_amber_coast_data import ROOMS, room


# ======================================================================
# WARBAND 1 - The Wave-Riders (9 rooms, levels 51-55)
# Younger raiders, ship-crews, closest to the harbor. Unique rooms:
# Net-Mending Yard, The Boasting Stone, The Drying Rack Line, The
# Launch Point.
# ======================================================================

room(
    "wr_approach",
    "Wave-Riders' Approach",
    """|wA whale-rib arch|n, weathered pale by real years of salt
    wind, marks the entrance to this camp - unmistakably a sea-going
    crew's own territory. |cGull cries|n carry constantly from the
    beach just beyond.""",
    "amber_coast_wave_riders",
)

room(
    "wr_landing_fire",
    "The Landing Fire",
    """|rA driftwood fire|n burns here, ringed by younger raiders
    trading real stories of the last real run. |wNets and salt-
    stiffened rope|n hang drying nearby.""",
    "amber_coast_wave_riders",
)

room(
    "wr_net_yard",
    "The Net-Mending Yard",
    """|wRows of real fishing and boarding nets|n hang stretched for
    mending, torn in ways that tell their own real story. |GAn old
    hand|n works a bone needle through the cordage without ever
    looking up.""",
    "amber_coast_wave_riders",
)

room(
    "wr_sleeping",
    "Wave-Riders' Sleeping Rows",
    """|wRough lean-tos|n, built for speed rather than comfort, line
    this stretch of packed sand. |cSalt air|n has gotten into
    everything stored here.""",
    "amber_coast_wave_riders",
)

room(
    "wr_boasting_stone",
    "The Boasting Stone",
    """|wA single, real weathered boulder|n serves as this camp's
    entire system of rank - climbed, stood on, and defended in real
    wrestling matches rather than settled by simple seniority.
    |YA crowd gathers here more often than not|n.""",
    "amber_coast_wave_riders",
)

room(
    "wr_weapon_racks",
    "Weapon Racks - Boarding Gear",
    """|wBoarding axes and long iron gaffs|n hang racked here, a
    visibly different loadout from anything a land warband carries.
    |rSalt has already started working at the iron|n despite real,
    constant oiling.""",
    "amber_coast_wave_riders",
)

room(
    "wr_drying_racks",
    "The Drying Rack Line",
    """|wLong wooden racks|n hold split fish drying in the coastal
    wind - this camp doubles as a real food-processing site for the
    whole town. |GGulls circle constantly|n, kept off only by a
    watchful, ill-tempered raider.""",
    "amber_coast_wave_riders",
)

room(
    "wr_leader_tent",
    "Skalla Half-Drowned's Tent",
    """|wA tent stitched from real sailcloth|n rather than hide, marks
    Skalla apart from every land-warband leader in the region. |cSea-
    glass and bone charms|n hang from every seam.""",
    "amber_coast_wave_riders",
)

room(
    "wr_launch_point",
    "The Launch Point",
    """|cThe crew's own private stretch of beach|n, a longship drawn
    half out of the surf and ready to go. |wThis is where a Wave-
    Rider actually leaves|n, not through the camp's own front arch.""",
    "amber_coast_wave_riders",
)


# ======================================================================
# WARBAND 2 - The Iron Tide (9 rooms, levels 54-58)
# The town's main land-defense force, garrisoned on the inland wall.
# Unique rooms: The Drill Yard, Wall-Watch Rotation Room, Shield
# Stores, The Punishment Post, Wall Egress.
# ======================================================================

room(
    "it_approach",
    "Iron Tide Approach",
    """|wA packed, well-trodden path|n leads off the inner palisade
    road toward real, disciplined activity ahead. |rShouted drill
    commands|n carry clearly from further in.""",
    "amber_coast_iron_tide",
)

room(
    "it_drill_yard",
    "The Drill Yard",
    """|rShield-wall drills|n run here in genuine, repeated formation
    - this camp trains like it expects to actually need it. |wPacked
    earth|n has been worn hard and flat by real, constant use.""",
    "amber_coast_iron_tide",
)

room(
    "it_wall_watch",
    "The Wall-Watch Rotation Room",
    """|wA scarred logboard|n tracks sentry shifts along the inland
    wall in real, careful detail - this camp's whole reason for being
    is right there on that board. |rTally marks|n cover every inch of
    available space.""",
    "amber_coast_iron_tide",
)

room(
    "it_shield_stores",
    "Shield Stores",
    """|wRacked shield-wall equipment|n fills this room, distinct from
    the Wave-Riders' own boarding gear entirely. |rFresh paint|n marks
    more than one shield's face, reapplied after real use.""",
    "amber_coast_iron_tide",
)

room(
    "it_sleeping",
    "Iron Tide Sleeping Rows",
    """|wTight, uniform barracks rows|n reflect a far more hierarchical
    culture than the Wave-Riders' own loose lean-tos. |rEverything here
    is arranged with real, deliberate order|n.""",
    "amber_coast_iron_tide",
)

room(
    "it_punishment_post",
    "The Punishment Post",
    """|rA single, scarred timber post|n stands alone here - this
    camp's discipline runs by the post, not by any contest. |wNobody
    lingers here without real reason to|n.""",
    "amber_coast_iron_tide",
)

room(
    "it_common_fire",
    "Iron Tide Common Fire",
    """|rA disciplined, orderly fire|n, warriors seated in real,
    habitual rows rather than any loose scatter. |wConversation here
    is quieter than in any other camp|n.""",
    "amber_coast_iron_tide",
)

room(
    "it_leader_post",
    "Berhtwin Oakenshield's Post",
    """|wA real command post|n, not a tent - Berhtwin clearly expects
    to be found exactly here, at any hour. |rA shield-wall diagram|n
    is scratched directly into the ground beside it.""",
    "amber_coast_iron_tide",
)

room(
    "it_wall_egress",
    "The Wall Egress",
    """|wA real sally-gate|n opens straight onto the palisade itself
    here, not toward any beach - this camp's whole purpose made
    physically obvious. |rThe wood is scarred|n from real, repeated
    use.""",
    "amber_coast_iron_tide",
)


# ======================================================================
# WARBAND 3 - The Drowned Oath (9 rooms, levels 57-61)
# Bound by a Nerthus oath, camped nearest the causeway to the sacred
# isle. Unique rooms: The Oath-Stone, The Shunning Hut, Water-Blessing
# Trough, Causeway Watch.
# ======================================================================

room(
    "do_approach",
    "Drowned Oath Approach",
    """|wHung offerings|n mark this camp's entrance, not weapons -
    small bundles of reed and bone swaying in the sea wind. |cThe
    smell of brackish water|n is stronger here than anywhere else in
    the town.""",
    "amber_coast_drowned_oath",
)

room(
    "do_oath_stone",
    "The Oath-Stone",
    """|wA real, standing stone|n, worn smooth where countless hands
    have marked their vow against it. |YNothing else in this whole
    town carries the same weight this stone does|n.""",
    "amber_coast_drowned_oath",
)

room(
    "do_common_fire",
    "Drowned Oath Common Fire",
    """|rA quiet, ritual-marked fire|n burns here, the talk around it
    noticeably more solemn than any other camp's. |GReed offerings|n
    smolder at its edge rather than burning cleanly.""",
    "amber_coast_drowned_oath",
)

room(
    "do_sleeping",
    "Drowned Oath Sleeping Rows",
    """|wSimple, unadorned bedrolls|n line this stretch of ground -
    this warband keeps little that isn't already promised elsewhere.
    |GDamp reed matting|n covers the floor throughout.""",
    "amber_coast_drowned_oath",
)

room(
    "do_shunning_hut",
    "The Shunning Hut",
    """|wA hut set deliberately apart|n from the rest of the camp -
    where an oath-breaker is held, genuinely alone, until the warband
    decides what comes next. |rSomething inside clearly resents being
    there|n.""",
    "amber_coast_drowned_oath",
)

room(
    "do_weapon_racks",
    "Weapon Racks - Votive Blades",
    """|wSpears and votive-marked blades|n hang here, each one
    scored with a small ritual notch. |YEven this camp's steel serves
    the oath first|n.""",
    "amber_coast_drowned_oath",
)

room(
    "do_water_trough",
    "The Water-Blessing Trough",
    """|cA small ritual basin|n, fed by a narrow channel from the
    tidal flats beyond, where new gear is blessed before it's ever
    carried. |GReed and pale stone|n ring the water's edge.""",
    "amber_coast_drowned_oath",
)

room(
    "do_leader_tent",
    "Wulfhild the Sworn's Tent",
    """|wRitual marks|n cover nearly every surface here, far more
    visibly than any of the other three warband leaders carry.
    |YAmber and bone charms|n hang in careful, deliberate patterns.""",
    "amber_coast_drowned_oath",
)

room(
    "do_causeway_watch",
    "Causeway Watch",
    """|cThe causeway to Nerthus's own sacred isle|n begins here,
    visible even at high tide as a pale line beneath the water.
    |wThis warband guards it informally|n, without ever quite calling
    themselves guards.""",
    "amber_coast_drowned_oath",
)


# ======================================================================
# WARBAND 4 - The Amber Guard (9 rooms, levels 59-63)
# Hertha's personal veterans, escorting trade caravans and guarding
# the wealthiest cargo. Unique rooms: The Ledger Room, Strongbox
# Vault, Caravan Muster Yard.
# ======================================================================

room(
    "ag_approach",
    "Amber Guard Approach",
    """|wA short, well-kept path|n connects this camp directly to the
    Hall's own outer gate - proximity to power made physically
    obvious. |YEven the ground here looks better cared for|n.""",
    "amber_coast_amber_guard",
)

room(
    "ag_common_fire",
    "Amber Guard Common Fire",
    """|rA well-tended fire|n burns at this camp's center, its warriors
    noticeably better-equipped than anything seen in the other three
    camps. |YAmber trim|n marks more than one piece of gear here.""",
    "amber_coast_amber_guard",
)

room(
    "ag_ledger_room",
    "The Ledger Room",
    """|wCargo manifests|n cover a real, dedicated writing table here,
    a scribe tallying exactly what's owed to whom. |YThis camp's whole
    job is protecting wealth in transit|n, and the room proves it.""",
    "amber_coast_amber_guard",
)

room(
    "ag_strongbox_vault",
    "Strongbox Vault",
    """|YA secondary vault|n, smaller than Hertha's own but real -
    cargo too valuable to leave in the harbor's ordinary warehouses.
    |wTwo guards|n watch it without ever quite relaxing.""",
    "amber_coast_amber_guard",
)

room(
    "ag_sleeping",
    "Amber Guard Sleeping Rows",
    """|wThe best-appointed barracks in the whole town|n, real
    furnishings rather than bare bedrolls. |YEven off duty, this
    warband lives well|n.""",
    "amber_coast_amber_guard",
)

room(
    "ag_weapon_racks",
    "Weapon Racks - Escort Gear",
    """|wThe best-geared loadout of any of the four camps|n, weapons
    and armor kept in genuinely immaculate condition. |YAmber-inlaid
    fittings|n mark pieces reserved for real veterans only.""",
    "amber_coast_amber_guard",
)

room(
    "ag_muster_yard",
    "The Caravan Muster Yard",
    """|wReal escort details form up here|n before a caravan run,
    distinct from any simple drill ground - this is departure
    infrastructure, built for exactly one purpose. |YLoaded pack-
    frames|n wait in a neat, ready row.""",
    "amber_coast_amber_guard",
)

room(
    "ag_leader_tent",
    "Ingvar Coin-Ward's Tent",
    """|wA tent as well-appointed as anything in the Hall itself|n,
    Ingvar's own real closeness to Hertha made obvious at a glance.
    |YA locked strongbox|n sits visible, deliberately unhidden.""",
    "amber_coast_amber_guard",
)

room(
    "ag_hall_egress",
    "Hall Egress",
    """|wThis camp's own private path|n ties directly into the Sea-
    Nix's Hall approach - Ingvar's veterans never need to walk through
    the general town to reach Hertha directly. |YWell-worn stone|n
    marks a route used constantly.""",
    "amber_coast_amber_guard",
)


WARBAND_ROOM_COUNT = 36

WARBAND_LINKS = [
    # Wave-Riders - entrance off the harbor's beach launch, exit
    # (The Launch Point) back to the harbor's departure point - two
    # real routes in/out, matching the non-linearity principle even
    # within a single camp.
    ("ac_harbor_beach_launch", "north", "wr_approach", "south"),
    ("wr_approach", "north", "wr_landing_fire", "south"),
    ("wr_landing_fire", "north", "wr_net_yard", "south"),
    ("wr_landing_fire", "east", "wr_sleeping", "west"),
    ("wr_landing_fire", "west", "wr_boasting_stone", "east"),
    ("wr_boasting_stone", "north", "wr_weapon_racks", "south"),
    ("wr_weapon_racks", "north", "wr_drying_racks", "south"),
    ("wr_drying_racks", "north", "wr_leader_tent", "south"),
    ("wr_leader_tent", "east", "wr_launch_point", "west"),
    ("wr_launch_point", "south", "ac_harbor_departure_point", "north"),

    # Iron Tide - entrance off the inner palisade road, egress (Wall
    # Egress) onto the palisade itself via the checkpoint.
    ("ac_palisade_inner_road", "east", "it_approach", "west"),
    ("it_approach", "east", "it_drill_yard", "west"),
    ("it_drill_yard", "north", "it_wall_watch", "south"),
    ("it_drill_yard", "east", "it_shield_stores", "west"),
    ("it_wall_watch", "east", "it_sleeping", "west"),
    ("it_shield_stores", "north", "it_sleeping", "south"),
    ("it_sleeping", "east", "it_punishment_post", "west"),
    ("it_punishment_post", "south", "it_common_fire", "north"),
    ("it_common_fire", "east", "it_leader_post", "west"),
    ("it_leader_post", "north", "it_wall_egress", "south"),
    ("it_wall_egress", "east", "ac_palisade_checkpoint", "west"),

    # Drowned Oath - entrance off the harbor's reef shelf (coastal,
    # nearest the water), causeway watch reserved for the Sacred
    # Isle link (built in Part 3).
    ("ac_harbor_tidepool_2", "south", "do_approach", "north"),
    ("do_approach", "south", "do_oath_stone", "north"),
    ("do_oath_stone", "south", "do_common_fire", "north"),
    ("do_common_fire", "east", "do_sleeping", "west"),
    ("do_sleeping", "south", "do_shunning_hut", "north"),
    ("do_common_fire", "west", "do_weapon_racks", "east"),
    ("do_weapon_racks", "south", "do_water_trough", "north"),
    ("do_common_fire", "south", "do_leader_tent", "north"),
    ("do_leader_tent", "east", "do_causeway_watch", "west"),

    # Amber Guard - both approach and egress tie into the Hall zone
    # directly, deliberately never touching the general town.
    ("ac_hall_inner_gate", "east", "ag_approach", "west"),
    ("ag_approach", "east", "ag_common_fire", "west"),
    ("ag_common_fire", "north", "ag_ledger_room", "south"),
    ("ag_common_fire", "south", "ag_strongbox_vault", "north"),
    ("ag_strongbox_vault", "east", "ag_sleeping", "west"),
    ("ag_sleeping", "north", "ag_weapon_racks", "south"),
    ("ag_weapon_racks", "east", "ag_muster_yard", "west"),
    ("ag_muster_yard", "south", "ag_leader_tent", "north"),
    ("ag_leader_tent", "east", "ag_hall_egress", "west"),
    ("ac_hall_approach", "east", "ag_hall_egress", "south"),
]
