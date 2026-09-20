"""
One-time live setup for the Amber Coast (world/batch_amber_coast_data.py
+ its Part 2/Part 3 files): creates all 144 rooms and their exits,
places flavor NPCs and lookable objects, spawns the real combat
population (~83 placements across every zone, matching the design
document's own "~85-105 spawns" estimate), and places the two shops
(the Amber Trader, the Smith's Quarter Armory).

Mirrors world/setup_germania_live.py's exact structure and
conventions. Does NOT wire the wilderness crossover exit from "The
Contested Ridge" - that's a separate, deliberate final step
(world.wilderness_amber_coast.setup_amber_coast_wilderness()), run
only after this script confirms "The River Delta - Upper Reach" is
live, so the crossing is never exposed with no real destination.

Run once via `evennia shell < world/setup_amber_coast_live.py`. Not
idempotent - re-running duplicates everything.
"""

from evennia.utils import search, create
from evennia.prototypes.spawner import spawn

from world.batch_amber_coast_data import ROOMS, LINKS, NPCS, OBJECTS, ECHOES
from world.batch_amber_coast_data_2 import WARBAND_LINKS
from world.batch_amber_coast_data_3 import LINKS_PART3

CHARACTER_TYPECLASS = "typeclasses.characters.Character"
OBJECT_TYPECLASS = "typeclasses.objects.Object"

ALL_LINKS = LINKS + WARBAND_LINKS + LINKS_PART3

# ----------------------------------------------------------------------
# 1. Create all 144 rooms
# ----------------------------------------------------------------------

room_objs = {}
for key, data in ROOMS.items():
    room = create.create_object("typeclasses.rooms.Room", key=data["name"])
    room.db.desc = data["desc"]
    room.tags.add(data["zone"], category="zone")
    room_objs[key] = room

print("Created %d rooms." % len(room_objs))

# ----------------------------------------------------------------------
# 2. Wire every internal exit, bidirectionally.
# ----------------------------------------------------------------------

exit_count = 0
for from_key, from_dir, to_key, to_dir in ALL_LINKS:
    from_room = room_objs[from_key]
    to_room = room_objs[to_key]
    create.create_object(
        "typeclasses.exits.Exit", key=from_dir, location=from_room, destination=to_room
    )
    create.create_object(
        "typeclasses.exits.Exit", key=to_dir, location=to_room, destination=from_room
    )
    exit_count += 2

print("Created %d internal exits." % exit_count)

# ----------------------------------------------------------------------
# 3. Confirm the wilderness crossover can find this zone once wired -
#    LeaveAmberCoastWildernessExit (world/wilderness_amber_coast.py)
#    looks up "The River Delta - Upper Reach" by name at traversal
#    time; nothing needs to be created here for that side, just verify
#    it now exists.
# ----------------------------------------------------------------------

if not search.search_object("The River Delta - Upper Reach", typeclass="typeclasses.rooms.Room"):
    raise SystemExit("ABORTED: 'The River Delta - Upper Reach' was not created - crossover exit will fail.")
print("Confirmed 'The River Delta - Upper Reach' exists for the wilderness crossover exit.")

# ----------------------------------------------------------------------
# 4. Flavor NPCs
# ----------------------------------------------------------------------

npc_count = 0
for room_key, name, kind, desc, extra in NPCS:
    room = room_objs[room_key]
    npc = create.create_object(CHARACTER_TYPECLASS, key=name, location=room)
    npc.db.desc = desc
    npc.locks.add("get:false()")
    npc_count += 1

print("Spawned %d flavor NPCs." % npc_count)

# ----------------------------------------------------------------------
# 5. Lookable scenery objects
# ----------------------------------------------------------------------

obj_count = 0
for room_key, name, desc in OBJECTS:
    room = room_objs[room_key]
    obj = create.create_object(OBJECT_TYPECLASS, key=name, location=room)
    obj.db.desc = desc
    obj.locks.add("get:false()")
    obj_count += 1

print("Created %d scenery objects." % obj_count)

# ----------------------------------------------------------------------
# 6. Room echoes
# ----------------------------------------------------------------------

echo_count = 0
for room_key, lines in ECHOES.items():
    room = room_objs[room_key]
    room.db.echo_messages = lines
    room.scripts.add("world.colosseum.ColosseumEcho")
    echo_count += 1

print("Set echoes on %d rooms." % echo_count)

# ----------------------------------------------------------------------
# 7. The real, persistent combat population - ~83 placements, matching
#    the design document's own "~85-105 spawns" estimate. Every AMBER_*
#    combat prototype gets real, mechanically-active gear automatically
#    (RespawningNPC.at_object_post_creation -> equip_amber_coast_npc,
#    world/combat.py) - "a real risk of death," by direct request.
# ----------------------------------------------------------------------

COMBAT_PLACEMENTS = [
    # --- Coastal Road (light, transition-zone density) ---
    ("ac_road_delta_3", "AMBER_ROAD_BANDIT"),
    ("ac_road_dune_2", "AMBER_ROAD_BANDIT"),
    ("ac_road_ford_1", "AMBER_ROAD_BANDIT"),

    # --- Outer Palisade & Harbor Approach ---
    ("ac_palisade_outer_gate", "AMBER_PALISADE_WARDEN"),
    ("ac_palisade_guard_walk", "AMBER_PALISADE_WARDEN"),
    ("ac_palisade_checkpoint", "AMBER_PALISADE_WARDEN"),
    ("ac_palisade_sentry_post", "AMBER_PALISADE_WARDEN"),
    ("ac_palisade_watchfire_1", "AMBER_PALISADE_WARDEN"),
    ("ac_palisade_watchfire_2", "AMBER_PALISADE_WARDEN"),

    # --- The Harbor District ---
    ("ac_harbor_main_quay", "AMBER_HARBOR_TOUGH"),
    ("ac_harbor_beach_launch", "AMBER_HARBOR_TOUGH"),
    ("ac_harbor_cargo_yard_1", "AMBER_HARBOR_TOUGH"),
    ("ac_harbor_cargo_yard_2", "AMBER_HARBOR_TOUGH"),
    ("ac_harbor_warehouse_1", "AMBER_HARBOR_TOUGH"),
    ("ac_harbor_warehouse_2", "AMBER_HARBOR_SMUGGLER"),
    ("ac_harbor_warehouse_2", "AMBER_HARBOR_SMUGGLER"),
    ("ac_harbor_dockworker_row_1", "AMBER_HARBOR_TOUGH"),
    ("ac_harbor_dockworker_row_2", "AMBER_HARBOR_TOUGH"),
    ("ac_harbor_tidepool_1", "AMBER_HARBOR_TOUGH"),

    # --- The Sea-Nix's Hall ---
    ("ac_hall_great_hall", "AMBER_BOSS_HERTHA_SEA_NIX"),
    ("ac_hall_inner_gate", "AMBER_HALL_GUARD"),
    ("ac_hall_barracks_1", "AMBER_HALL_GUARD"),
    ("ac_hall_barracks_2", "AMBER_HALL_GUARD"),
    ("ac_hall_barracks_3", "AMBER_HALL_GUARD"),
    ("ac_hall_armory", "AMBER_HALL_GUARD"),
    ("ac_hall_war_council", "AMBER_HALL_GUARD"),

    # --- Terp Mound Quarter (light, residential density) ---
    ("tm_gathering_1", "AMBER_TERPMOUND_THIEF"),
    ("tm_gathering_2", "AMBER_TERPMOUND_THIEF"),
    ("tm_pen_1", "AMBER_TERPMOUND_THIEF"),

    # --- The Trading Quarter (low density - meant to feel safer) ---
    ("ac_trade_dispute_ground", "AMBER_TRADE_ENFORCER"),
    ("ac_trade_enforcement_post", "AMBER_TRADE_ENFORCER"),

    # --- Shipyard & Drydock ---
    ("sy_drydock_1", "AMBER_SHIPYARD_GUARD"),
    ("sy_timber_1", "AMBER_SHIPYARD_GUARD"),
    ("sy_timber_2", "AMBER_SHIPYARD_GUARD"),
    ("sy_shipwright_1", "AMBER_SHIPYARD_GUARD"),

    # --- Fishing & Salt Flats ---
    ("fsf_salt_1", "AMBER_SALTFLAT_SCAVENGER"),
    ("fsf_smoke_1", "AMBER_SALTFLAT_SCAVENGER"),
    ("fsf_tideflat_1", "AMBER_SALTFLAT_SCAVENGER"),

    # --- Warband 1: The Wave-Riders (levels 51-55) ---
    ("wr_landing_fire", "AMBER_WAVERIDER_DECKHAND"),
    ("wr_landing_fire", "AMBER_WAVERIDER_HARPOONER"),
    ("wr_sleeping", "AMBER_WAVERIDER_OARSMAN"),
    ("wr_sleeping", "AMBER_WAVERIDER_DECKHAND"),
    ("wr_boasting_stone", "AMBER_WAVERIDER_CHAMPION"),
    ("wr_weapon_racks", "AMBER_WAVERIDER_ARMORER"),
    ("wr_drying_racks", "AMBER_WAVERIDER_SCAVENGER"),
    ("wr_leader_tent", "AMBER_BOSS_SKALLA_HALF_DROWNED"),

    # --- Warband 2: The Iron Tide (levels 54-58) ---
    ("it_drill_yard", "AMBER_IRONTIDE_SHIELDBEARER"),
    ("it_drill_yard", "AMBER_IRONTIDE_RECRUIT"),
    ("it_wall_watch", "AMBER_IRONTIDE_SENTRY"),
    ("it_shield_stores", "AMBER_IRONTIDE_VETERAN"),
    ("it_sleeping", "AMBER_IRONTIDE_SHIELDBEARER"),
    ("it_sleeping", "AMBER_IRONTIDE_RECRUIT"),
    ("it_punishment_post", "AMBER_IRONTIDE_ENFORCER"),
    ("it_common_fire", "AMBER_IRONTIDE_DRILLMASTER"),
    ("it_common_fire", "AMBER_IRONTIDE_SENTRY"),
    ("it_leader_post", "AMBER_BOSS_BERHTWIN_OAKENSHIELD"),

    # --- Warband 3: The Drowned Oath (levels 57-61) ---
    ("do_common_fire", "AMBER_DROWNEDOATH_VOTARY"),
    ("do_common_fire", "AMBER_DROWNEDOATH_ADHERENT"),
    ("do_sleeping", "AMBER_DROWNEDOATH_ADHERENT"),
    ("do_sleeping", "AMBER_DROWNEDOATH_VOTARY"),
    ("do_shunning_hut", "AMBER_DROWNEDOATH_SHUNNED"),
    ("do_weapon_racks", "AMBER_DROWNEDOATH_ARMORER"),
    ("do_causeway_watch", "AMBER_DROWNEDOATH_GUARD"),
    ("do_leader_tent", "AMBER_BOSS_WULFHILD_THE_SWORN"),

    # --- Warband 4: The Amber Guard (levels 59-63) ---
    ("ag_common_fire", "AMBER_AMBERGUARD_ESCORT"),
    ("ag_common_fire", "AMBER_AMBERGUARD_ESCORT"),
    ("ag_strongbox_vault", "AMBER_AMBERGUARD_SENTINEL"),
    ("ag_sleeping", "AMBER_AMBERGUARD_VETERAN"),
    ("ag_sleeping", "AMBER_AMBERGUARD_VETERAN"),
    ("ag_weapon_racks", "AMBER_AMBERGUARD_QUARTERMASTER"),
    ("ag_muster_yard", "AMBER_AMBERGUARD_OUTRIDER"),
    ("ag_muster_yard", "AMBER_AMBERGUARD_OUTRIDER"),
    ("ag_leader_tent", "AMBER_BOSS_INGVAR_COINWARD"),

    # --- Nerthus's Sacred Isle (deliberately sparse) ---
    ("ni_grove_1", "AMBER_SACREDISLE_BOGWIGHT"),
    ("ni_votive_shore_1", "AMBER_SACREDISLE_BOGWIGHT_ELDER"),
    ("ni_veiled_wagon", "AMBER_GUARDIAN_VEILED_WAGON"),

    # --- Deeper Coastal Wilds (capstone) ---
    ("dcw_cliff_1", "AMBER_WILDS_CLIFFRAIDER"),
    ("dcw_cliff_2", "AMBER_WILDS_CLIFFRAIDER"),
    ("dcw_wreck_1", "AMBER_WILDS_WRECKSCAVENGER"),
    ("dcw_cave_1", "AMBER_WILDS_CAVEDWELLER"),
    ("dcw_cave_2", "AMBER_WILDS_OUTCAST"),
    ("dcw_cave_3", "AMBER_WILDS_DEEPCAVE_LURKER"),
    ("dcw_capstone", "AMBER_BOSS_ORMSTOOTH"),
]

combat_count = 0
for room_key, prototype_key in COMBAT_PLACEMENTS:
    obj = spawn(prototype_key)[0]
    obj.move_to(room_objs[room_key], quiet=True)
    combat_count += 1

print("Spawned %d real combat NPCs across the Amber Coast." % combat_count)

# ----------------------------------------------------------------------
# 8. The two shops
# ----------------------------------------------------------------------

from world.economy import AmberCoastArmorer, AmberTrader

armorer = create.create_object(
    AmberCoastArmorer, key="a Smith's Quarter armorer", location=room_objs["ac_trade_smiths_armory"]
)
armorer.db.desc = (
    "Forge-scarred hands and a real, exacting eye - everything on display "
    "here is a clear step above anything the interior Stronghold's own "
    "smith produces."
)
armorer.locks.add("get:false()")

trader = create.create_object(
    AmberTrader, key="the Amber Trader", location=room_objs["ac_trade_amber_trader"]
)
trader.db.desc = (
    "Amber jewelry and curios cover every surface within reach - and she "
    "buys as eagerly as she sells, raw amber and furs both."
)
trader.locks.add("get:false()")

print("Placed the Smith's Quarter Armory and the Amber Trader.")

print(
    "Amber Coast setup complete: %d rooms, %d exits, %d flavor NPCs, %d objects, "
    "%d combat NPCs, 2 shops." % (
        len(room_objs), exit_count, npc_count, obj_count, combat_count
    )
)
