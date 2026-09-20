"""
The Amber Coast - a coastal Germanic trading town north of the
Germanic Stronghold, reached via the wilderness stretch in
world/wilderness_amber_coast.py. Full design: a 144-room location per
the user's own detailed design document (a coastal river-delta trading
town near the Danish frontier, ruled by war-leader Hertha Sea-Nix and
a separate Nerthus cult authority, with a real harbor, four distinct
warbands, a trading quarter, and a capstone stretch of coastal wilds).

Built in the same validated, in-memory, no-live-database-touched
pattern as every prior zone this project - see
world/batch_germania_data.py's own docstring for the convention this
follows. Levels are the design doc's own numbers +21 across the board
- see world/wilderness_amber_coast.py's module docstring for exactly
why (the doc assumed the interior Stronghold was levels 1-25; the real
live Stronghold is 27-46, so the whole location is shifted to bridge
from that real cap instead of restarting below it).

THIS FILE COVERS PART 1 OF THE FULL 144-ROOM DESIGN (56 rooms):
  Zone A - Coastal Road (10, levels 43-48)
  Zone B - Outer Palisade & Harbor Approach (10, levels 47-51)
  Zone C - The Harbor District (14, levels 49-55)
  Zone D - The Sea-Nix's Hall (10, levels 53-59)
  Zone G - The Trading Quarter (12, levels 50-56)
Remaining zones (Four Warbands, Terp Mound Quarter, Shipyard & Drydock,
Fishing & Salt Flats, Nerthus's Sacred Isle, Deeper Coastal Wilds
capstone - 88 rooms) are built in follow-up batch files, each wired
into this one's own exits rather than duplicating anything here.

Every room description weaves at least two real colors, deliberately -
amber/gold (|Y) is the location's own signature recurring color, tied
directly to the trade the whole settlement exists because of.

Run this file directly (`python3 world/batch_amber_coast_data.py`) to
validate room count and exit references before executing anything
against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ======================================================================
# ZONE A - Coastal Road (10 rooms, levels 43-48)
# The land route in from the Stronghold's own wilderness road,
# following the river delta down toward salt air and gulls.
# ======================================================================

room(
    "ac_road_delta_1",
    "The River Delta - Upper Reach",
    """|GReed beds close in|n on both sides as the trail drops toward
    the delta proper, the ground going soft and dark underfoot. |cA
    slow, brown channel|n runs parallel to the path, thick with
    silt carried down from country far inland.""",
    "amber_coast_road",
)

room(
    "ac_road_delta_2",
    "The River Delta - Reed Channel",
    """|GTall reeds|n, taller than a person, crowd the trail into a
    single narrow file. |wA heron|n stands motionless in the shallows,
    unbothered by anyone passing this close.""",
    "amber_coast_road",
)

room(
    "ac_road_delta_3",
    "The River Delta - Braided Water",
    """|cThe river splits here|n into a dozen shallow, braided
    channels, none deep enough to swim but all of them cold. |GReed
    and mud|n stretch in every direction, the trail marked by a line
    of driven stakes rather than any real path.""",
    "amber_coast_road",
)

room(
    "ac_road_delta_4",
    "The River Delta - Lower Marsh",
    """|GThe marsh opens wider|n here, the reeds thinning just enough
    to see how far the wet ground actually runs. |wA half-sunk amphora
    shard|n, unmistakably Roman, sits half-buried in the mud - proof
    of contact, not conquest.""",
    "amber_coast_road",
)

room(
    "ac_road_dune_1",
    "Rising Ground - First Rise",
    """|yThe ground finally rises|n out of the marsh, dry underfoot
    for the first time in a while. |GScrub grass and low brush|n
    cling to the slope, the delta falling away behind.""",
    "amber_coast_road",
)

room(
    "ac_road_dune_2",
    "Rising Ground - Dune Scrub",
    """|ySparse, wind-bent scrub|n covers rolling dune country here,
    sand working into the trail itself. |cA cold wind|n carries the
    first unmistakable smell of open water.""",
    "amber_coast_road",
)

room(
    "ac_road_dune_3",
    "Rising Ground - The Last Rise",
    """|yThe trail crests a final dune|n, sand and scrub grass giving
    way to a long downward slope. |wGulls wheel overhead|n, loud and
    unbothered, the first real sign of the coast itself.""",
    "amber_coast_road",
)

room(
    "ac_road_ford_1",
    "The River-Mouth Ford - Near Bank",
    """|cThe river meets the sea here|n, wide and shallow at low
    water, treacherous at high. |GWeed-slick stones|n mark a real,
    if uncomfortable, crossing point.""",
    "amber_coast_road",
)

room(
    "ac_road_ford_2",
    "The River-Mouth Ford - Far Bank",
    """|cCold water|n runs fast around your ankles even at the
    ford's shallowest point. |wSalt-bleached driftwood|n litters the
    far bank, evidence of exactly how far the tide reaches.""",
    "amber_coast_road",
)

room(
    "ac_first_sight",
    "First Sight of the Sea",
    """|cThe sea opens out ahead|n, grey and vast, further than
    anything the interior ever prepared you for. |YFar off, a thread
    of pale smoke|n rises against the sky - the town, close now.
    |wGulls circle in real numbers overhead|n, and the wind carries
    salt, tar, and woodsmoke together for the first time.""",
    "amber_coast_road",
)


# ======================================================================
# ZONE B - Outer Palisade & Harbor Approach (10 rooms, levels 47-51)
# ======================================================================

room(
    "ac_palisade_camp_1",
    "The Trader's Camp - Outer Ring",
    """|YCarts and pack-goods|n sit stacked under makeshift oiled-cloth
    covers, traders waiting their turn at the gate beyond. |wSmoke from
    a dozen small fires|n drifts low across the churned, muddy ground.""",
    "amber_coast_palisade",
)

room(
    "ac_palisade_camp_2",
    "The Trader's Camp - Common Fire",
    """|YA shared fire|n burns at the center of the waiting camp,
    ringed by traders swapping real news and rumor in half a dozen
    accents. |wNobody here is in any particular hurry|n - the gate
    opens when the gate opens.""",
    "amber_coast_palisade",
)

room(
    "ac_palisade_camp_3",
    "The Trader's Camp - Livestock Pens",
    """|wRough timber pens|n hold goats and a few nervous cattle,
    livestock brought in for trade rather than for eating. |GMud and
    trampled straw|n cover every inch of open ground here.""",
    "amber_coast_palisade",
)

room(
    "ac_palisade_outer_gate",
    "The Outer Gate",
    """|wA log palisade|n rises here, real and imposing but not
    paranoid - the gate stands open more often than closed, because
    trade demands it. |YAmber-inlaid carvings|n along the gateposts
    mark this as more than a simple war-camp entrance.""",
    "amber_coast_palisade",
)

room(
    "ac_palisade_guard_walk",
    "The Guard Walk",
    """|wA raised timber walkway|n runs along the inside of the
    palisade, sentries pacing it in loose, unhurried rotation.
    |cA cold sea wind|n cuts across the open walk from every
    direction.""",
    "amber_coast_palisade",
)

room(
    "ac_palisade_checkpoint",
    "The Inner Checkpoint",
    """|wA second, lighter barrier|n stands here - less a wall than a
    formality, checked by a bored-looking warrior more interested in
    who's carrying goods than who's carrying weapons. |YCoin, clearly,
    talks louder than steel in this town|n.""",
    "amber_coast_palisade",
)

room(
    "ac_palisade_watchfire_1",
    "A Watch-Fire on the Wall",
    """|rA fire pit|n burns low here, tended around the clock by
    whichever sentry drew the short straw. |wThe sea is visible from
    here|n, grey and restless beyond the palisade's own timber line.""",
    "amber_coast_palisade",
)

room(
    "ac_palisade_watchfire_2",
    "A Second Watch-Fire",
    """|rAnother fire|n, another sentry, this one watching the
    marsh-side approach rather than the sea. |GReed and mudflat|n
    stretch out beyond the wall in this direction.""",
    "amber_coast_palisade",
)

room(
    "ac_palisade_sentry_post",
    "A Raised Sentry Post",
    """|wA crude wooden tower|n gives real, useful sight over the
    whole approach - the delta behind, the harbor ahead. |YWhoever
    built this understood exactly what a trading town needs to see
    coming|n.""",
    "amber_coast_palisade",
)

room(
    "ac_palisade_inner_road",
    "The Inner Road",
    """|wA packed-earth road|n runs from the checkpoint down toward
    the sound of real activity ahead - hammering, shouting, the
    unmistakable noise of a working harbor. |YThe smell of tar and
    amber-oil|n grows stronger with every step.""",
    "amber_coast_palisade",
)


# ======================================================================
# ZONE C - The Harbor District (14 rooms, levels 49-55)
# The town's real identity - the busiest, most NPC-dense public space.
# ======================================================================

room(
    "ac_harbor_main_quay",
    "The Main Quay",
    """|wLong timber quays|n stretch out over the water, thick with
    dockhands hauling crates and coiled rope underfoot. |YAmber and
    furs|n move across this exact ground every single day, the whole
    reason this town exists at all.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_beach_launch",
    "The Beach Launch",
    """|cShallow surf|n rolls in against a stretch of open beach,
    longships drawn up above the tideline in neat rows. |wTar-blackened
    hulls|n bake in whatever sun makes it through the coastal haze.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_departure_point",
    "The Departure Point",
    """|cOpen water|n stretches out past the last of the moored ships
    here, gulls diving at scraps thrown from a nearby gutting-table.
    |wThis is as far out over the water as dry ground goes|n.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_cargo_yard_1",
    "The Cargo Yard - Amber Stores",
    """|YRaw amber|n, some pieces the size of a fist, sits stacked in
    open crates under careful guard. |wThe whole yard smells faintly
    resinous|n, sweet in a way nothing else here does.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_cargo_yard_2",
    "The Cargo Yard - Fur Stores",
    """|wBundled furs|n, wolf and bear and something less identifiable,
    hang from open-sided racks to air out. |GThe smell of raw hide|n
    is thick enough to taste.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_warehouse_1",
    "A Timber Warehouse",
    """|wA low, long timber building|n, packed floor to roof with
    goods waiting for the next real tide. |YA locked strongbox|n
    sits visibly guarded near the door - somebody's real wealth,
    not left to chance.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_warehouse_2",
    "A Second Warehouse - Smuggler's Corner",
    """|wCrates here sit stacked a little too carefully|n, gaps left
    for something that isn't officially being stored. |rA nervous-
    looking dockhand|n watches anyone who lingers too long.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_dockworker_row_1",
    "Dockworker Housing - Row One",
    """|wRough timber shacks|n stand packed shoulder to shoulder,
    built for people who live close to the work rather than close to
    comfort. |GLaundry|n hangs between them, salt-stiffened and
    never quite dry.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_dockworker_row_2",
    "Dockworker Housing - Row Two",
    """|wA second row of packed housing|n, louder than the first -
    real arguments, real laughter, the ordinary noise of people
    living close together. |YA child's amber trinket|n sits
    forgotten on a windowsill.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_dockworker_row_3",
    "Dockworker Housing - The Common Well",
    """|wA shared well|n stands at the center of the dockworker
    rows, worn smooth by generations of rope and bucket. |cCold,
    clean water|n is the one reliable comfort in this crowded
    corner of town.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_tidepool_1",
    "The Tide-Pool Flats",
    """|cShallow pools|n sit exposed at low water, crabs and small
    fish trapped until the tide returns for them. |GSlick, weed-
    covered stone|n makes for treacherous footing here.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_tidepool_2",
    "The Reef Shelf",
    """|cA low reef|n breaks the surface at low tide, dark shapes
    moving in the deeper water just beyond it. |wSomething down
    there|n occasionally takes real interest in anyone wading too
    far out.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_foreign_quarter_1",
    "The Foreign Quarter - The Roman Factor's Stall",
    """|wA small, neatly-kept stall|n stands oddly out of place among
    the harbor's rough timber - genuinely Roman construction, genuinely
    tolerated. |YA ledger and a set of Roman scales|n sit on the
    counter, doing brisk, careful business.""",
    "amber_coast_harbor",
)

room(
    "ac_harbor_foreign_quarter_2",
    "The Foreign Quarter - The Baltic Trader's Stall",
    """|YAmber of every color|n, from pale honey to deep, near-black
    red, sits displayed with real pride here. |wA trader who's clearly
    come a very long way|n watches the harbor with the calm patience
    of someone who's done this a hundred times.""",
    "amber_coast_harbor",
)


# ======================================================================
# ZONE D - The Sea-Nix's Hall (10 rooms, levels 53-59)
# ======================================================================

room(
    "ac_hall_approach",
    "The Hall Approach",
    """|wA steep, packed-earth path|n climbs from the harbor toward
    the town's highest ground, the noise of the docks falling away
    below. |YCarved amber markers|n line the way, each one worn
    smooth by touching hands.""",
    "amber_coast_hall",
)

room(
    "ac_hall_inner_gate",
    "The Hall's Inner Gate",
    """|wA second palisade|n rings the hall compound, separate from
    the harbor's own outer wall - a real, deliberate line between the
    town's public face and its seat of power. |rTwo spears crossed|n
    mark the gate until a guard clears the way through.""",
    "amber_coast_hall",
)

room(
    "ac_hall_great_hall",
    "The Great Hall of Hertha Sea-Nix",
    """|YAmber set into the very roof-beams|n catches whatever light
    makes it through the smoke-hole above, scattering warm gold
    across a hall built for real authority. |wHertha Sea-Nix herself|n
    holds court here, hearth-companions at her back, in a room that
    makes no attempt to hide what it actually is.""",
    "amber_coast_hall",
)

room(
    "ac_hall_barracks_1",
    "Hearth-Companion Barracks - East Row",
    """|wTight, well-kept sleeping rows|n line this side of the
    compound, gear racked with real discipline. |YEven here, small
    amber charms|n hang above more than one bedroll.""",
    "amber_coast_hall",
)

room(
    "ac_hall_barracks_2",
    "Hearth-Companion Barracks - West Row",
    """|wA second barracks row|n, quieter at this hour, most of its
    occupants out on duty elsewhere in the hall compound. |rWeapon
    oil and old smoke|n hang in the air.""",
    "amber_coast_hall",
)

room(
    "ac_hall_barracks_3",
    "The Hearth-Companions' Common Room",
    """|rA long fire pit|n runs down the center of this shared room,
    hearth-companions off duty trading real stories over it. |wThe
    talk quiets, just slightly, whenever a stranger walks in|n.""",
    "amber_coast_hall",
)

room(
    "ac_hall_armory",
    "The Hall Armory",
    """|wRacked weapons|n line every wall here, better-kept and
    better-made than anything in the warband camps below. |YAmber-
    inlaid sword hilts|n mark pieces reserved for Hertha's own
    hearth-companions specifically.""",
    "amber_coast_hall",
)

room(
    "ac_hall_war_council",
    "The War-Council Chamber",
    """|wA low table|n, scarred and stained, dominates this small
    room - real decisions get made here, away from the Great Hall's
    own performance of authority. |rA map scratched directly into the
    tabletop|n shows more of the coast than seems entirely safe to
    display.""",
    "amber_coast_hall",
)

room(
    "ac_hall_vault",
    "The Treasure Vault",
    """|YReal wealth|n sits stacked and guarded here - raw amber,
    Roman coin, worked gold - proof of exactly how much a trading
    town's chieftain actually profits from controlling the harbor.
    |wTwo guards|n watch the single door without ever quite relaxing.""",
    "amber_coast_hall",
)

room(
    "ac_hall_terrace",
    "The Sea-Facing Terrace",
    """|cThe whole grey sweep of the sea|n opens out from this private
    terrace, the harbor's noise reduced to a distant murmur below.
    |YA single amber-inlaid bench|n faces the water - clearly someone's
    real, private place to think.""",
    "amber_coast_hall",
)


# ======================================================================
# ZONE G - The Trading Quarter (12 rooms, levels 50-56) - SHOPS HERE
# ======================================================================

room(
    "ac_trade_barter_square_1",
    "The Barter Square - North Half",
    """|YGoods of every origin|n change hands here in the open air,
    haggling conducted in a real mix of languages. |wCanvas awnings|n
    snap in the coastal wind overhead.""",
    "amber_coast_trade",
)

room(
    "ac_trade_barter_square_2",
    "The Barter Square - South Half",
    """|wA second cluster of open stalls|n spills out from the first,
    the whole square loud with real, ongoing commerce. |YA scale for
    weighing amber|n sits set up permanently at its center.""",
    "amber_coast_trade",
)

room(
    "ac_trade_amber_trader",
    "The Amber Trader's Stall",
    """|YAmber jewelry and worked curios|n fill every surface of this
    crowded stall, pale gold to deep red-brown. |wThe trader here buys
    as eagerly as she sells|n - raw amber, furs, anything a traveler
    might have picked up worth turning into coin.""",
    "amber_coast_trade",
)

room(
    "ac_trade_smiths_armory",
    "The Smith's Quarter Armory",
    """|rForge-heat|n rolls out from this stall in real waves, weapons
    and armor racked in every direction. |wGear here runs a clear step
    above anything the interior stronghold ever offered|n.""",
    "amber_coast_trade",
)

room(
    "ac_trade_storage_1",
    "Amber Trader's Storage",
    """|YCrated amber|n, sorted by size and color with real care, fills
    this narrow storeroom behind the main stall. |wThe air smells
    faintly, pleasantly resinous|n.""",
    "amber_coast_trade",
)

room(
    "ac_trade_storage_2",
    "Armory Storage",
    """|wRaw iron and half-finished blades|n crowd this back room,
    waiting on the smith's own attention. |rBanked coals|n glow low in
    a secondary forge pit.""",
    "amber_coast_trade",
)

room(
    "ac_trade_stall_1",
    "A Food Vendor's Stall",
    """|wSmoked fish and dried meat|n hang in neat rows, a real,
    practical business rather than a flavor one. |GThe smell of
    woodsmoke|n clings to everything here.""",
    "amber_coast_trade",
)

room(
    "ac_trade_stall_2",
    "A Cloth and Hide Stall",
    """|wDyed wool and worked hide|n hang displayed on simple wooden
    frames, colors more vivid than the town's usual muted palette.
    |YA thread of amber beads|n is worked into more than one piece.""",
    "amber_coast_trade",
)

room(
    "ac_trade_stall_3",
    "A Carver's Stall",
    """|wBone and antler carvings|n sit displayed alongside a few
    pieces of worked amber, a craftsman clearly proud of blending the
    two. |YSmall amber-eyed figurines|n seem to be his real specialty.""",
    "amber_coast_trade",
)

room(
    "ac_trade_dispute_ground",
    "The Dispute Ground",
    """|rA cleared, packed-earth square|n where commercial arguments
    get settled - sometimes by words, sometimes not. |wHertha's own
    authority|n visibly extends this far into the town's daily
    business, enforced by whoever's on duty here.""",
    "amber_coast_trade",
)

room(
    "ac_trade_enforcement_post",
    "The Enforcement Post",
    """|wA small guard post|n watches over the Dispute Ground, ready
    to step in before an argument becomes something worse. |rA short
    length of chain|n hangs visibly by the door - a real, if rarely
    used, threat.""",
    "amber_coast_trade",
)

room(
    "ac_trade_records_stall",
    "The Toll-Keeper's Stall",
    """|wA scribe|n sits here tallying tolls and trade taxes with
    real, unhurried precision. |YA stack of wax tablets|n records
    exactly how much of this town's wealth flows through Hertha's
    own hands first.""",
    "amber_coast_trade",
)


TOTAL_ROOM_COUNT_EXPECTED = 56

LINKS = [
    # Zone A - Coastal Road (chain from the wilderness handoff point)
    ("ac_first_sight", "south", "ac_road_ford_2", "north"),
    ("ac_road_ford_2", "south", "ac_road_ford_1", "north"),
    ("ac_road_ford_1", "south", "ac_road_dune_3", "north"),
    ("ac_road_dune_3", "south", "ac_road_dune_2", "north"),
    ("ac_road_dune_2", "south", "ac_road_dune_1", "north"),
    ("ac_road_dune_1", "south", "ac_road_delta_4", "north"),
    ("ac_road_delta_4", "south", "ac_road_delta_3", "north"),
    ("ac_road_delta_3", "south", "ac_road_delta_2", "north"),
    ("ac_road_delta_2", "south", "ac_road_delta_1", "north"),
    # ac_road_delta_1's own "south" is the wilderness crossover -
    # wired live by setup_amber_coast_wilderness(), not here.

    # Zone A -> Zone B
    ("ac_first_sight", "east", "ac_palisade_camp_1", "west"),

    # Zone B - Outer Palisade & Harbor Approach
    ("ac_palisade_camp_1", "east", "ac_palisade_camp_2", "west"),
    ("ac_palisade_camp_2", "east", "ac_palisade_camp_3", "west"),
    ("ac_palisade_camp_2", "north", "ac_palisade_outer_gate", "south"),
    ("ac_palisade_outer_gate", "north", "ac_palisade_guard_walk", "south"),
    ("ac_palisade_guard_walk", "east", "ac_palisade_watchfire_1", "west"),
    ("ac_palisade_guard_walk", "west", "ac_palisade_watchfire_2", "east"),
    ("ac_palisade_guard_walk", "north", "ac_palisade_checkpoint", "south"),
    ("ac_palisade_checkpoint", "east", "ac_palisade_sentry_post", "west"),
    ("ac_palisade_checkpoint", "north", "ac_palisade_inner_road", "south"),

    # Zone B -> Zone C
    ("ac_palisade_inner_road", "north", "ac_harbor_main_quay", "south"),

    # Zone C - The Harbor District
    ("ac_harbor_main_quay", "east", "ac_harbor_beach_launch", "west"),
    ("ac_harbor_beach_launch", "east", "ac_harbor_departure_point", "west"),
    ("ac_harbor_main_quay", "west", "ac_harbor_cargo_yard_1", "east"),
    ("ac_harbor_cargo_yard_1", "west", "ac_harbor_cargo_yard_2", "east"),
    ("ac_harbor_cargo_yard_1", "north", "ac_harbor_warehouse_1", "south"),
    ("ac_harbor_cargo_yard_2", "north", "ac_harbor_warehouse_2", "south"),
    ("ac_harbor_warehouse_1", "west", "ac_harbor_dockworker_row_1", "east"),
    ("ac_harbor_dockworker_row_1", "west", "ac_harbor_dockworker_row_2", "east"),
    ("ac_harbor_dockworker_row_2", "south", "ac_harbor_dockworker_row_3", "north"),
    ("ac_harbor_main_quay", "southwest", "ac_harbor_tidepool_1", "northeast"),
    ("ac_harbor_tidepool_1", "south", "ac_harbor_tidepool_2", "north"),
    ("ac_harbor_main_quay", "north", "ac_harbor_foreign_quarter_1", "south"),
    ("ac_harbor_foreign_quarter_1", "east", "ac_harbor_foreign_quarter_2", "west"),

    # Zone C -> Zone G (Trading Quarter, off the Foreign Quarter's own commerce)
    ("ac_harbor_foreign_quarter_2", "north", "ac_trade_barter_square_1", "south"),

    # Zone G - The Trading Quarter
    ("ac_trade_barter_square_1", "east", "ac_trade_barter_square_2", "west"),
    ("ac_trade_barter_square_1", "north", "ac_trade_amber_trader", "south"),
    ("ac_trade_barter_square_2", "north", "ac_trade_smiths_armory", "south"),
    ("ac_trade_amber_trader", "east", "ac_trade_storage_1", "west"),
    ("ac_trade_smiths_armory", "east", "ac_trade_storage_2", "west"),
    ("ac_trade_barter_square_1", "west", "ac_trade_stall_1", "east"),
    ("ac_trade_stall_1", "west", "ac_trade_stall_2", "east"),
    ("ac_trade_stall_2", "west", "ac_trade_stall_3", "east"),
    ("ac_trade_barter_square_2", "east", "ac_trade_dispute_ground", "west"),
    ("ac_trade_dispute_ground", "east", "ac_trade_enforcement_post", "west"),
    ("ac_trade_dispute_ground", "south", "ac_trade_records_stall", "north"),

    # Zone C -> Zone D (Sea-Nix's Hall) - first of the Hall's two
    # required separate approaches (the doc's own "never a dead-end"
    # requirement), direct from the harbor.
    ("ac_harbor_main_quay", "northeast", "ac_hall_approach", "southeast"),

    # Zone G -> Zone D - the Hall's SECOND, separate approach, off the
    # Trading Quarter instead.
    ("ac_trade_barter_square_2", "northeast", "ac_hall_approach", "southwest"),

    # Zone D - The Sea-Nix's Hall
    ("ac_hall_approach", "north", "ac_hall_inner_gate", "south"),
    ("ac_hall_inner_gate", "north", "ac_hall_great_hall", "south"),
    ("ac_hall_great_hall", "east", "ac_hall_barracks_1", "west"),
    ("ac_hall_great_hall", "west", "ac_hall_barracks_2", "east"),
    ("ac_hall_barracks_1", "south", "ac_hall_barracks_3", "north"),
    ("ac_hall_barracks_2", "southeast", "ac_hall_barracks_3", "northwest"),
    ("ac_hall_great_hall", "north", "ac_hall_armory", "south"),
    ("ac_hall_armory", "north", "ac_hall_war_council", "south"),
    ("ac_hall_war_council", "west", "ac_hall_vault", "east"),
    ("ac_hall_great_hall", "southeast", "ac_hall_terrace", "northwest"),
]

# Flavor NPCs and lookable objects for this part of the build - the
# remaining zones (warbands, secondary zones, Sacred Isle, capstone)
# add their own in follow-up batch files rather than here. Hertha
# Sea-Nix herself is NOT listed here - she's a real, fightable combat
# NPC (world/prototypes.py's AMBER_BOSS_HERTHA_SEA_NIX), placed
# directly in ac_hall_great_hall by the live setup script's combat
# placement pass, not a flavor Character. Listing her here too would
# have created a harmless duplicate standing right next to her own
# real, fightable self.
NPCS = [
    ("ac_trade_records_stall", "a toll-keeper", "flavor",
     """|wA scribe|n, ink-stained fingers moving over wax tablets with
     real, practiced speed.""", None),
    ("ac_harbor_foreign_quarter_1", "a Roman factor", "flavor",
     """|wNeatly dressed|n despite the harbor's mud, a set of Roman
     scales never far from his hands.""", None),
    ("ac_harbor_foreign_quarter_2", "a Baltic amber-trader", "flavor",
     """|YAmber of every shade|n laid out with real pride in front of
     her - she's clearly come a very long way to sell it.""", None),
]

OBJECTS = [
    ("ac_road_delta_4", "a half-sunk amphora shard",
     """|wA broken piece of unmistakably Roman pottery|n, half-buried
     in the delta mud - proof of contact with the empire, not
     conquest by it."""),
    ("ac_first_sight", "a worn trail-marker",
     """|YA weathered post|n, amber beads knotted into a cord around
     its top - someone's small, private offering for a safe
     arrival."""),
    ("ac_harbor_cargo_yard_1", "a crate of raw amber",
     """|YRough, unpolished amber|n, some pieces the size of a fist,
     packed in straw for the next real voyage."""),
    ("ac_hall_vault", "Hertha's strongbox",
     """|YReal wealth|n, carefully counted and stacked - amber, Roman
     coin, worked gold - locked behind iron banding even here, deep
     inside a guarded hall."""),
    ("ac_hall_war_council", "a coastline map",
     """|rScratched directly into the tabletop|n, showing more of the
     surrounding coast - and further inland - than seems entirely
     safe to leave on display."""),
]

ECHOES = {
    "ac_harbor_main_quay": [
        "|wSomeone shouts an order down the length of the quay.|n",
        "|YA cart of amber creaks past, closely watched.|n",
    ],
    "ac_trade_barter_square_1": [
        "|wReal haggling breaks out somewhere nearby, good-natured for now.|n",
    ],
    "ac_hall_great_hall": [
        "|wThe hearth-fire pops and settles.|n",
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

    all_keys = set(ROOMS.keys())

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
    queue = ["ac_road_delta_1"]
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
        errors.append("Unreachable rooms: %s" % sorted(unreachable))

    for entry in NPCS:
        room_key = entry[0]
        if room_key not in all_keys:
            errors.append("NPC references unknown room: %s" % room_key)
    for room_key, _, _ in OBJECTS:
        if room_key not in all_keys:
            errors.append("Object references unknown room: %s" % room_key)
    for room_key in ECHOES:
        if room_key not in all_keys:
            errors.append("Echo references unknown room: %s" % room_key)

    return errors


if __name__ == "__main__":
    print("Loaded %d rooms (Part 1 of 144 - Coastal Road, Outer Palisade, Harbor, Hall, Trading Quarter)." % len(ROOMS))
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
