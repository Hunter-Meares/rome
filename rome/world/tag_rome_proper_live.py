"""
One-off live script: tags every room in "Rome proper" with
world.crime.ROME_PROPER_ZONE_TAG, via a real reachability walk (the same
pattern the Underworld's own no-combat-zone tagging used) rather than a
hand-typed room list - so it stays correct if the city ever grows.

Owner's own definition: "Rome is everything reachable without leaving
through a gate." The walk starts from The Forum Romanum's central plaza (a
real, well-connected hub - the Curia, the temple cluster, the Subura,
Trajan's Market, and the Clivus Capitolinus up to the Capitoline are all
reachable from it with no special-casing) and follows every ordinary exit,
EXCEPT the three boundaries explicitly excluded:

  - The Porta Flaminia gate door (Inside the Gate - City Side <-> The
    Porta Flaminia) - the wall, the road beyond it, and the wilderness are
    never Rome proper.
  - The Colosseum boundary (Colosseum Main Entrance <-> The Meta Sudans) -
    the whole Colosseum/Ludus/Deeper Sands complex is excluded for now
    (tutorial-adjacent, its own already-distinct zone).
  - The three sewer grates (Ludus Entrance, The Subura Fountain, Basilica
    Julia - Rear Exit, each via an exit/door literally named "grate") -
    the Cloaca Maxima is its own zone, not Rome proper.

The Underworld, the wilderness road, Germania, and the Amber Coast are
never reachable from Rome proper by ordinary exit-walking at all (the
Underworld specifically has NO walkable connection - see CLAUDE.md), so
they need no explicit stop; only the three boundaries above are ever
actually crossable from inside the walk.

Run via `evennia shell < world/tag_rome_proper_live.py` (or paste into a
live shell). Idempotent - safe to run again after building new Rome-proper
content; it will just add the tag to whatever's newly reachable.
"""

from evennia.objects.models import ObjectDB
from world.crime import ROME_PROPER_ZONE_TAG

ANCHOR_ROOM_KEY = "The Forum Romanum - Central Plaza"

# (room key exits are checked FROM, exit key never to be crossed) - the
# three excluded boundaries, checked by the room's own key and the exit's
# own key so this doesn't depend on object ids that could differ between
# installs.
BLOCKED_EXITS = {
    ("Inside the Gate - City Side", "west"),
    ("The Porta Flaminia", "east"),
    ("Colosseum Main Entrance", "south"),
    ("The Meta Sudans", "north"),
    ("Ludus Entrance", "grate"),
    ("The Subura Fountain", "grate"),
    ("Basilica Julia - Rear Exit", "grate"),
}


def _is_blocked(room, exit_obj):
    return (room.db_key, exit_obj.db_key) in BLOCKED_EXITS


def tag_rome_proper_zone():
    anchor = ObjectDB.objects.filter(db_key=ANCHOR_ROOM_KEY).first()
    if not anchor:
        print("ERROR: anchor room '%s' not found - aborting." % ANCHOR_ROOM_KEY)
        return

    key, category = ROME_PROPER_ZONE_TAG
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
            # Checked against the root evennia.objects.objects.DefaultExit,
            # not this project's own typeclasses.exits.Exit - a real door
            # (world/doors.py's DescriptiveDoor, used at the Porta Flaminia
            # and every sewer grate) inherits from the contrib's own
            # SimpleDoor(DefaultExit) directly, never from this project's
            # Exit subclass, so checking the narrower class would silently
            # skip every door in the walk.
            if not exit_obj.is_typeclass("evennia.objects.objects.DefaultExit", exact=False):
                continue
            if _is_blocked(room, exit_obj):
                print("  (stopped at boundary) %s -[%s]-> %s" % (room.db_key, exit_obj.db_key, destination.db_key))
                continue
            seen.add(destination)
            queue.append(destination)

    print("Rome proper: %d rooms reachable, %d newly tagged (of %d already tagged before this run)." % (
        len(seen), newly_tagged, len(seen) - newly_tagged
    ))


tag_rome_proper_zone()
