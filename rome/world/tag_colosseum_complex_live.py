"""
One-off live script: tags every room in the Colosseum/Ludus/Deeper Sands
complex with world.crime.COLOSSEUM_COMPLEX_ZONE_TAG, via a real
reachability walk - same pattern as world/tag_rome_proper_live.py.

Needed for world.crime.is_crime_jurisdiction(): killing or stealing from
this zone's dense population of grind/leveling NPCs is never a crime
(log_crime's own account check already excludes any victim without a real
player behind them, everywhere), but a PLAYER attacking or killing another
PLAYER here should be exactly as illegal as it is on a Rome street, unless
it's a sanctioned duel. Guards still never patrol this zone (Rome proper
only) - this tag only ever feeds crime DETECTION, never guard placement.

The walk starts from "Colosseum Main Entrance" (the room just past the
boundary world/tag_rome_proper_live.py's own walk stops at) and follows
every ordinary exit, EXCEPT into a room already tagged either Rome proper
(world.crime.ROME_PROPER_ZONE_TAG) or the sewers
(world.crime.SEWERS_ZONE_TAG, already applied live by
world/setup_sewers_live.py to every Cloaca Maxima room) - stopping at
whatever's already tagged is more robust than hand-listing exact reverse
boundary exits, and both of those zones are already fully tagged live by
the time this ever needs to run.

Run via `evennia shell < world/tag_colosseum_complex_live.py` (or paste
into a live shell), any time after both world/tag_rome_proper_live.py and
world/setup_sewers_live.py have already run. Idempotent - safe to run
again after building new Colosseum-complex content.
"""

from evennia.objects.models import ObjectDB
from world.crime import COLOSSEUM_COMPLEX_ZONE_TAG, ROME_PROPER_ZONE_TAG, SEWERS_ZONE_TAG

ANCHOR_ROOM_KEY = "Colosseum Main Entrance"

_STOP_TAGS = (ROME_PROPER_ZONE_TAG, SEWERS_ZONE_TAG)


def _already_out_of_scope(room):
    return any(room.tags.get(key, category=category) for key, category in _STOP_TAGS)


def tag_colosseum_complex_zone():
    anchor = ObjectDB.objects.filter(db_key=ANCHOR_ROOM_KEY).first()
    if not anchor:
        print("ERROR: anchor room '%s' not found - aborting." % ANCHOR_ROOM_KEY)
        return
    if _already_out_of_scope(anchor):
        print("ERROR: anchor room '%s' is already tagged Rome proper or sewers - aborting." % ANCHOR_ROOM_KEY)
        return

    key, category = COLOSSEUM_COMPLEX_ZONE_TAG
    seen = {anchor}
    queue = [anchor]
    newly_tagged = 0

    while queue:
        room = queue.pop()
        if not room.tags.get(key, category=category):
            room.tags.add(key, category=category)
            newly_tagged += 1

        for exit_obj in room.contents:
            destination = getattr(exit_obj, "destination", None)
            if not destination or destination in seen:
                continue
            # evennia.objects.objects.DefaultExit, not this project's own
            # typeclasses.exits.Exit - matches tag_rome_proper_live.py's
            # own fix for the same real doors (world/doors.py).
            if not exit_obj.is_typeclass("evennia.objects.objects.DefaultExit", exact=False):
                continue
            seen.add(destination)
            if _already_out_of_scope(destination):
                print("  (stopped at boundary) %s -[%s]-> %s" % (room.db_key, exit_obj.db_key, destination.db_key))
                continue
            queue.append(destination)

    print("Colosseum complex: %d rooms reachable, %d newly tagged (of %d already tagged before this run)." % (
        len(seen), newly_tagged, len(seen) - newly_tagged
    ))


tag_colosseum_complex_zone()
