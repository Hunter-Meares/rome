"""
Exploration tracking - the tiered explorer achievements (world/
achievements.py: Wanderer, Well-Traveled, Explorer, Cartographer).

Remembers which real, authored rooms a player character has ever stood in
(`db.visited_rooms`, a set of room ids) and feeds each NEW one to the
achievement system, so the four tiers are simply the same progress counted
to four different targets.

What deliberately does NOT count:
  - Wilderness tiles. Each road is ONE recycled room object standing in for
    hundreds of coordinates with repeating descriptions (Rome's road is ~500
    tiles, the Amber Coast's ~1,000) - counting them would make the top
    tiers trivial. Only genuinely authored rooms count.
  - Gods (level over 100): they teleport everywhere and their private
    Olympus rooms would count for nothing anyway.
  - NPCs (no persistent .account) - this is a player milestone.

About 775 rooms are ordinary, mortal-reachable ones (the ~800 total less
Olympus and a handful of test rooms), so the tiers sit at roughly an eighth,
a third, under half, and three quarters of the world. Existing players start
counting from the day this shipped - nothing recorded where they'd been
before, and the analytics room trails are too approximate to seed from.
"""

WILDERNESS_ROOM_TYPECLASS = "evennia.contrib.grid.wilderness.wilderness.WildernessRoom"


def counts_for_exploration(character, room):
    """True if `character` standing in `room` is a real player in a real,
    authored room - see the module docstring for what is excluded."""
    from world.factions import GOD_LEVEL_THRESHOLD

    if not room or not getattr(character, "account", None):
        return False
    if (character.db.level or 1) > GOD_LEVEL_THRESHOLD:
        return False
    if room.is_typeclass(WILDERNESS_ROOM_TYPECLASS, exact=False):
        return False
    return True


def record_room_visit(character, room=None):
    """Remembers `room` (default: where the character is now) and, if it's
    new to them, counts it toward the explorer achievements. Returns True
    if it was a new room."""
    room = room or character.location
    if not counts_for_exploration(character, room):
        return False

    visited = character.db.visited_rooms
    if visited is None:
        visited = set()
    if room.id in visited:
        return False
    visited.add(room.id)
    character.db.visited_rooms = visited

    from world.achievements import track_and_announce

    track_and_announce(character, category="explore", tracking="rooms")
    return True
