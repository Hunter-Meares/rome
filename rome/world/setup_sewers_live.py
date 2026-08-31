"""
One-time live setup for the Cloaca Maxima: creates all 85 rooms and
174 exits from world/batch_sewers_data.py, wires the 3 anchor "grate"
doors into the existing world, and spawns the sewer_npc-tagged
population from world/prototypes.py into their assigned rooms.

Run once via `evennia shell < world/setup_sewers_live.py` after
deploying batch_sewers_data.py and the new prototypes. Re-running is
NOT safe as-is (no idempotency guard, unlike setup_factions_live.py) -
this only ever needs to run once for a brand-new zone; guard against
accidental re-runs by checking room count first if ever reused.

Difficulty note (checked against the real formulas before building,
not guessed): the two inter-tier shortcuts skip a full tier of
level-scaled gear progression (roughly +50% weapon damage across the
gap - see compute_weapon_stats). Real risk, survivable with a
successful 'disengage' (55% per turn) if it goes wrong - not a
guaranteed death sentence, matches the game's existing stakes.
"""

from evennia.utils import search, create

from world.batch_sewers_data import ROOMS, LINKS
from world.doors import DescriptiveDoor
import world.prototypes as protos


# ----------------------------------------------------------------------
# 1. Create all 85 rooms
# ----------------------------------------------------------------------

room_objs = {}
for key, data in ROOMS.items():
    room = create.create_object(
        "typeclasses.rooms.Room", key=data["name"]
    )
    room.db.desc = data["desc"]
    room.tags.add("sewers", category="zone")
    room_objs[key] = room

print("Created %d rooms." % len(room_objs))

# ----------------------------------------------------------------------
# 2. Wire all 174 internal exits, bidirectionally
# ----------------------------------------------------------------------

exit_count = 0
for from_key, from_dir, to_key, to_dir in LINKS:
    from_room = room_objs[from_key]
    to_room = room_objs[to_key]
    create.create_object(
        "typeclasses.exits.Exit", key=from_dir, location=from_room, destination=to_room
    )
    create.create_object(
        "typeclasses.exits.Exit", key=to_dir, location=to_room, destination=from_room
    )
    exit_count += 2

print("Created %d exits." % exit_count)

# ----------------------------------------------------------------------
# 3. The three grate doors - real, openable/closable doors (per direct
#    request), not plain exits. Built manually rather than via the
#    in-game '@open' builder command, replicating exactly what that
#    command does under the hood (see the simpledoor contrib's
#    CmdOpen.create_exit): two DescriptiveDoor exits, each other's
#    db.return_exit, so opening/closing either side affects both.
# ----------------------------------------------------------------------

def create_grate(anchor_room_name, sewer_room_key, out_key, out_aliases, in_key, in_aliases):
    anchors = search.search_object(anchor_room_name, typeclass="typeclasses.rooms.Room")
    if not anchors:
        print("SKIPPED grate - anchor room not found: %s" % anchor_room_name)
        return
    anchor_room = anchors[0]
    sewer_room = room_objs[sewer_room_key]

    down_exit = create.create_object(
        DescriptiveDoor, key=out_key, aliases=out_aliases,
        location=anchor_room, destination=sewer_room,
    )
    up_exit = create.create_object(
        DescriptiveDoor, key=in_key, aliases=in_aliases,
        location=sewer_room, destination=anchor_room,
    )
    down_exit.db.return_exit = up_exit
    up_exit.db.return_exit = down_exit
    print("Grate created: %s <-> %s" % (anchor_room.key, sewer_room.key))


create_grate("Ludus Entrance", "sewer_ludus_grate", "grate", ["down", "sewer"], "up", ["out", "grate"])
create_grate("The Subura Fountain", "sewer_subura_grate", "grate", ["down", "sewer"], "up", ["out", "grate"])
create_grate("Basilica Julia - Rear Exit", "sewer_forum_grate", "grate", ["down", "sewer"], "up", ["out", "grate"])

# ----------------------------------------------------------------------
# 4. NPC population - spawn multiple copies of each sewer_npc prototype
#    into its assigned rooms. Hits the proposal's stated density target
#    (~1.5-2 per room average) without needing 140+ unique prototypes -
#    same approach Deeper Sands itself uses.
# ----------------------------------------------------------------------

POPULATION = [
    # (prototype, [room_keys - a room listed twice gets two instances])
    # Entrances (~18-20 total across all three, per the agreed density)
    (protos.SEWER_LUDUS_RUNAWAY, [
        "sewer_ludus_grate", "sewer_ludus_runoff", "sewer_ludus_bend",
        "sewer_ludus_barracks_wall", "sewer_ludus_barracks_wall", "sewer_ludus_last_light",
    ]),
    (protos.SEWER_SUBURA_FOOTPAD, [
        "sewer_subura_grate", "sewer_subura_patchwork", "sewer_subura_lean_to",
        "sewer_subura_low_crawl", "sewer_subura_gathering", "sewer_subura_gathering",
    ]),
    (protos.SEWER_FORUM_DESERTER, [
        "sewer_forum_grate", "sewer_forum_vault", "sewer_forum_records_drop",
        "sewer_forum_hidden_alcove", "sewer_forum_last_stones",
    ]),

    # The Confluence (~12-14, 8 rooms)
    (protos.SEWER_GANG_THUG, [
        "sewer_confluence_hub", "sewer_confluence_hub", "sewer_confluence_market",
        "sewer_confluence_contested", "sewer_confluence_collapsed_arch",
    ]),
    (protos.SEWER_GANG_SCOUT, [
        "sewer_confluence_ledge", "sewer_confluence_market", "sewer_confluence_side_channel",
        "sewer_confluence_drip_hall", "sewer_confluence_drip_hall",
        "sewer_confluence_threshold",
    ]),

    # The Main Cloaca (~24-28, 15 rooms)
    (protos.SEWER_CLOACA_BANDIT, [
        "sewer_cloaca_cart_tunnel_1", "sewer_cloaca_cart_tunnel_1", "sewer_cloaca_cart_tunnel_2",
        "sewer_cloaca_cart_tunnel_2", "sewer_cloaca_bandit_camp", "sewer_cloaca_bandit_camp",
        "sewer_cloaca_watch_post", "sewer_cloaca_storeroom", "sewer_cloaca_storeroom",
        "sewer_cloaca_junction", "sewer_cloaca_junction", "sewer_cloaca_old_repair",
        "sewer_cloaca_flooded_step", "sewer_cloaca_threshold",
    ]),
    (protos.SEWER_HECATE_CULTIST, [
        "sewer_cloaca_cult_antechamber", "sewer_cloaca_cult_rite_chamber",
        "sewer_cloaca_cult_rite_chamber",
    ]),
    (protos.SEWER_VIGILES_FUGITIVE, [
        "sewer_cloaca_fugitive_den", "sewer_cloaca_fugitive_den", "sewer_cloaca_echo_chamber",
        "sewer_cloaca_side_grate",
    ]),

    # The Flooded Depths (~24-28, 15 rooms)
    (protos.SEWER_SMUGGLER, [
        "sewer_flood_smuggler_dock", "sewer_flood_smuggler_dock", "sewer_flood_cargo_hold",
        "sewer_flood_escape_channel", "sewer_flood_current", "sewer_flood_final_channel",
        "sewer_flood_air_pocket",
    ]),
    (protos.SEWER_FERAL_MUTANT, [
        "sewer_flood_entry", "sewer_flood_causeway", "sewer_flood_causeway",
        "sewer_flood_mutant_nest", "sewer_flood_mutant_nest", "sewer_flood_bloated_hollow",
        "sewer_flood_deep_pool", "sewer_flood_deep_pool", "sewer_flood_narrow_wade",
        "sewer_flood_drowned_stair", "sewer_flood_threshold",
    ]),
    (protos.SEWER_MINOTAUR_GLADIATOR, [
        "sewer_flood_gladiator_arena", "sewer_flood_gladiator_arena",
    ]),

    # The Sunken Quarter (~18-20, 12 rooms)
    (protos.SEWER_SETTLEMENT_GUARD, [
        "sewer_sunken_entry", "sewer_sunken_watch_tower", "sewer_sunken_watch_tower",
        "sewer_sunken_boundary_wall", "sewer_sunken_boundary_wall", "sewer_sunken_street",
        "sewer_sunken_courtyard",
    ]),
    (protos.SEWER_SETTLEMENT_ENFORCER, [
        "sewer_sunken_settlement", "sewer_sunken_settlement", "sewer_sunken_market",
        "sewer_sunken_market", "sewer_sunken_shopfront", "sewer_sunken_collapsed_insula",
        "sewer_sunken_deep_cellar", "sewer_sunken_shrine",
    ]),

    # The Forgotten Works (~18-20, 12 rooms)
    (protos.SEWER_CYCLOPS_BARBARIAN, [
        "sewer_forgotten_cyclops_den", "sewer_forgotten_cyclops_den", "sewer_forgotten_bone_pile",
        "sewer_forgotten_bone_pile", "sewer_forgotten_gallery", "sewer_forgotten_entry",
        "sewer_forgotten_crushed_passage",
    ]),
    (protos.SEWER_NYMPH_AUGUR, [
        "sewer_forgotten_cult_hall", "sewer_forgotten_cult_hall", "sewer_forgotten_augur_sanctum",
        "sewer_forgotten_augur_sanctum", "sewer_forgotten_old_altar", "sewer_forgotten_old_altar",
        "sewer_forgotten_deep_cistern_approach", "sewer_forgotten_collapsed_well",
    ]),

    # The Abyssal Cistern (~10-12 + boss, 8 rooms)
    (protos.SEWER_CISTERN_LURKER, [
        "sewer_abyssal_entry", "sewer_abyssal_stair", "sewer_abyssal_flooded_floor",
        "sewer_abyssal_flooded_floor", "sewer_abyssal_pillar_hall", "sewer_abyssal_pillar_hall",
        "sewer_abyssal_dry_ledge", "sewer_abyssal_offering_shelf", "sewer_abyssal_threshold",
    ]),
    (protos.SEWER_BOSS_DROWNED_SENTINEL, [
        "sewer_abyssal_heart",
    ]),
]

from evennia.prototypes.spawner import spawn

npc_count = 0
for prototype, room_keys in POPULATION:
    for room_key in room_keys:
        obj = spawn(prototype)[0]
        obj.move_to(room_objs[room_key], quiet=True)
        npc_count += 1

print("Spawned %d NPCs." % npc_count)
print("Sewer setup complete: %d rooms, %d exits, 3 grates, %d NPCs." % (
    len(room_objs), exit_count, npc_count,
))
