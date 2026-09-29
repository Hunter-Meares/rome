"""
One-time live setup for crime-and-punishment phase 2's City Guards and
the Carcer holding cell.

Spawns 32 CityGuard NPCs (14 level 25, 12 level 50, 6 level 75 - "a
variety... a few level 75", per direct request) into random rooms drawn
from world.crime.ROME_PROPER_ZONE_TAG's own live-tagged room set,
wander_rooms set to that SAME full room set so each one patrols the
whole city rather than a small fixed beat, and attaches
world.guards.GuardPatrolScript to each. Also creates the one placeholder
Carcer holding-cell room (world.jail.CARCER_TAG) - deliberately minimal,
no exits of its own; the real Carcer complex is explicitly deferred
(rome_mud_todo.md) until this mechanical core is proven out live.

Run via `evennia shell < world/setup_guards_live.py`, any time after
world/tag_rome_proper_live.py has already tagged the city. Not
idempotent for the guards themselves (running twice spawns 32 more) -
guard against accidental re-runs the same way world/setup_sewers_live.py
already documents for its own one-time population. The Carcer room
creation IS guarded (skipped if one already exists), so re-running only
risks duplicate guards, never a duplicate cell.
"""

from random import choice

from evennia.prototypes.spawner import spawn
from evennia.utils import create, search

import world.prototypes as protos
from world.crime import ROME_PROPER_ZONE_TAG
from world.guards import GuardPatrolScript
from world.jail import CARCER_TAG

# (prototype, count) - see world/prototypes.py's own City Guard block for
# each one's level/xp_reward/gear tier.
POPULATION = [
    (protos.CITY_GUARD_RECRUIT, 7),
    (protos.CITY_GUARD_VIGILE, 7),
    (protos.CITY_GUARD_VETERAN, 6),
    (protos.CITY_GUARD_SERGEANT, 6),
    (protos.CITY_GUARD_CENTURION, 3),
    (protos.CITY_GUARD_TRIBUNE, 3),
]

proper_key, proper_category = ROME_PROPER_ZONE_TAG
rome_rooms = list(search.search_tag(proper_key, category=proper_category))
if not rome_rooms:
    print("ERROR: no rooms tagged Rome proper - run world/tag_rome_proper_live.py first. Aborting.")
else:
    guard_count = 0
    for prototype, count in POPULATION:
        for _ in range(count):
            guard = spawn(prototype)[0]
            guard.move_to(choice(rome_rooms), quiet=True)
            guard.db.wander_rooms = rome_rooms
            guard.scripts.add(GuardPatrolScript)
            guard_count += 1
    print("Spawned %d City Guards across %d Rome-proper rooms." % (guard_count, len(rome_rooms)))

cell_key, cell_category = CARCER_TAG
existing_cell = search.search_tag(cell_key, category=cell_category)
if existing_cell:
    print("Carcer holding cell already exists (%s) - skipped." % existing_cell[0].key)
else:
    cell = create.create_object("typeclasses.rooms.Room", key="The Carcer - Holding Cell")
    cell.db.desc = (
        "A low, windowless cell cut into the bedrock beneath the city - damp stone, "
        "a single guttering lamp, and no door a prisoner could ever hope to reach on "
        "their own. Iron rings are set into the far wall, though nothing in this "
        "room is escapable by any means an ordinary hand could manage."
    )
    cell.tags.add(cell_key, category=cell_category)
    print("Created the Carcer holding cell: %s" % cell.key)
