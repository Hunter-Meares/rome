"""
One-time live setup expanding the Ore Vein Shaft from a single gather
room into a real, ~25-room mine complex - a direct follow-up request
once the original 2-room version turned out to be too cramped for the
same "walk around and get lucky" gathering-discovery mechanic
(world/gathering.py's announce_gather_spot) the wilderness already
uses: with nowhere to explore, "keep looking" just meant walking in
and out of the same tiny space. This gives it real ground to cover -
4 branches off a central junction, with several distinct vein rooms
scattered through them, rather than one single fixed gather point.

Deliberately reuses "The Ore Vein Shaft" (the original room, #5859)
as the hub these branches connect off, rather than replacing it - it
keeps its own existing description, the old miner NPC, and its own
gather flag (still a real vein among several now, not the only one).
Matches this project's own "extend, don't replace" precedent for
retrofitting already-built content.

Every new vein room sets db.gather_uses_wilderness_chance = True
(world/gathering.py) - a real, multi-room complex like this genuinely
has ground to explore, unlike a single fixed room, so it uses the
same lower, meaningful-exploration chance the wilderness does, not
the "nowhere else to look" high chance a single-room node like the
Herbalist's stall keeps using.

A small bank of repeated description variants per branch (not 24
fully bespoke paragraphs) - the same "repeating descriptions for
similar content is fine" convention already authorized for the
wilderness's own off-road tiles.

Run once via `evennia shell < world/setup_ore_mine_complex_live.py`.
Not idempotent - re-running duplicates the whole complex.
"""

import random

from evennia.utils import search, create

shaft = search.search_object("The Ore Vein Shaft", typeclass="typeclasses.rooms.Room")
if not shaft:
    raise SystemExit("ABORTED: could not find the real 'The Ore Vein Shaft' room live.")
shaft = shaft[0]

TUNNEL_DESCS = {
    "junction": [
        "|xSeveral rough-cut passages meet here|n, low ceilings shored up with "
        "timber props that have clearly been replaced more than once. Pick "
        "marks radiate outward in every direction - whoever's been working "
        "this mine has been at it a long time."
    ],
    "upper": [
        "|xA narrow gallery|n slopes gently upward, the rock here paler and "
        "drier than the passages below. Old chisel marks run in neat, "
        "patient rows along one wall.",
        "|xThe upper gallery|n continues, air noticeably cooler here, a thin "
        "seam of quartz catching what little light reaches this far in.",
    ],
    "lower": [
        "|xThe passage dips lower|n, the rock damp and dark, water finding "
        "its own slow way down toward some unseen sump.",
        "|xDeeper still|n, the lower gallery narrows enough that you have to "
        "duck under a leaning support beam to keep going.",
    ],
    "flooded": [
        "|xAnkle-deep water|n covers the floor here, black and cold, the "
        "passage's own low point collecting whatever seeps in from above.",
        "|xThe flooded cut|n continues, careful footing needed on stone worn "
        "slick by standing water.",
    ],
    "old": [
        "|xAn older, abandoned working|n - the timber props here are grey "
        "with age, and nobody's swung a pick in this stretch for a very "
        "long time.",
        "|xFurther into the old working|n, the tunnel shows real signs of a "
        "long-ago collapse, carefully shored back open rather than dug fresh.",
    ],
}

VEIN_DESCS = [
    "A real vein of iron ore runs visibly through the rock wall here, "
    "rust-streaked and clearly workable.",
    "Pick marks cluster thick around a rich seam of ore in the wall - "
    "this spot has clearly been worked before, and clearly still has "
    "more to give.",
    "A dark, heavy vein cuts through the stone at chest height - real "
    "iron ore, not just discoloration.",
]


def _make_room(key, desc):
    room = create.create_object("typeclasses.rooms.Room", key=key, attributes=[("desc", desc)])
    return room


def _link(a, dir_a, b, dir_b):
    create.create_object("typeclasses.exits.Exit", key=dir_a, location=a, destination=b)
    create.create_object("typeclasses.exits.Exit", key=dir_b, location=b, destination=a)


def _build_branch(junction, first_dir, first_back_dir, tunnel_count, tunnel_bank, vein_count, branch_name):
    """Builds a linear chain of `tunnel_count` tunnel rooms off
    `junction` - the first hop uses a real compass direction
    (first_dir/first_back_dir, so the junction has 4 distinct named
    exits, one per branch), every hop after that just "deeper"/"back"
    - ending in `vein_count` real vein rooms branching off the last
    tunnel room."""
    prev = junction
    for i in range(tunnel_count):
        desc = random.choice(tunnel_bank)
        room = _make_room("%s - Tunnel %d" % (branch_name, i + 1), desc)
        if i == 0:
            _link(prev, first_dir, room, first_back_dir)
        else:
            _link(prev, "deeper", room, "back")
        prev = room

    veins = []
    vein_dirs = ["north", "south", "east", "west"]
    for i in range(vein_count):
        desc = random.choice(VEIN_DESCS)
        vein = _make_room("%s - a Rich Vein" % branch_name, desc)
        vein.db.gather_resource = "iron_ore"
        vein.db.gather_uses_wilderness_chance = True
        d = vein_dirs[i % len(vein_dirs)]
        create.create_object("typeclasses.exits.Exit", key=d, location=prev, destination=vein)
        create.create_object("typeclasses.exits.Exit", key="back", location=vein, destination=prev)
        veins.append(vein)
    return veins


junction = _make_room("The Deep Junction", TUNNEL_DESCS["junction"][0])
create.create_object("typeclasses.exits.Exit", key="down", location=shaft, destination=junction)
create.create_object("typeclasses.exits.Exit", key="up", location=junction, destination=shaft)

all_veins = []
all_veins += _build_branch(junction, "north", "south", 4, TUNNEL_DESCS["upper"], 2, "Upper Gallery")
all_veins += _build_branch(junction, "south", "north", 4, TUNNEL_DESCS["lower"], 2, "Lower Gallery")
all_veins += _build_branch(junction, "east", "west", 4, TUNNEL_DESCS["flooded"], 2, "The Flooded Cut")
all_veins += _build_branch(junction, "west", "east", 3, TUNNEL_DESCS["old"], 2, "The Old Working")

total_new = 1 + 4 + 4 + 4 + 3 + len(all_veins)  # junction + 4 branches' tunnels + their veins
print("Built the Deep Junction + 4 branches: %d new rooms, %d real vein rooms." % (total_new, len(all_veins)))
print("Total ore mine complex (including the original Ore Vein Shaft): %d rooms." % (total_new + 1))
