"""
The road north from the Germanic Stronghold to the Amber Coast - a
second, independent bounded wilderness stretch, built the exact same
way world/wilderness_rome.py built the original Rome-to-Germania road
(one recycled room standing in for a whole (x, y) grid, real DB cost
staying tiny regardless of how large the map reads to a player), by
direct request: "at least 50 rooms (roads) northish of the other
germanic settlement... surrounded by wilderness with aggro bandits
like the other germanic settlement."

This is deliberately a SEPARATE, parallel system from wilderness_rome.py
rather than an extension of it - a second WildernessScript with its
own map provider, its own GLOBAL_SCRIPTS entry, and its own bounded
grid, exactly mirroring that module's architecture rather than trying
to graft a second road onto the first script's single coordinate
space. See wilderness_rome.py's own module docstring for the two
underlying problems this pattern solves (DB cost, "don't want players
to get lost in infinite wilderness").

This road is explicitly NOT the same thing as the Amber Coast design
document's own "Coastal Road" section (10 hand-authored rooms - reed
marsh, dune scrub, a river-mouth ford, "First Sight of the Sea" -
levels 43-48 after the recalibration below). That 10-room stretch is
part of the Amber Coast's own 144-room authored zone, built later, and
is the actual final approach into the town proper. This module is the
long, repeating wilderness BETWEEN the Stronghold and that authored
approach - the "at least 50 rooms of road with aggro bandits" the
request specifically asked for as separate infrastructure.

Level recalibration, worth stating plainly: the Amber Coast design
document assumes the interior Germanic Stronghold is "levels 1-25" and
scales its own 25-50 range against that assumption. The REAL, live
Stronghold spans levels 27-46 (GERMANIA_* prototypes in
world/prototypes.py, capping at Vidrik Storm-Marked, level 46) - a
material mismatch, not a rounding difference. Every level number from
the design doc is shifted +21 when actually built, so the whole
location bridges cleanly from the real Stronghold's 46 cap instead of
restarting at 24. This puts the recalibrated Amber Coast at roughly
45-71, which lines up well below the Deeper Sands' real 75+ floor
(world/colosseum.py's DeeperSandsGateExit) - Stronghold (27-46) ->
Amber Coast (45-71) -> Deeper Sands (75+) -> godhood (101+) reads as a
genuine, unbroken progression rather than two zones fighting over the
same level band. This module's own ENCOUNTER_LEVELS below already
reflect that shift; the authored town (built separately, later) needs
the same +21 applied to every level the design doc quotes.

One-time live setup, once this module, its GLOBAL_SCRIPTS entry, and
the Amber Coast town's own first room all exist (deliberately NOT
wired live until there's a real destination at the far end - see
setup_amber_coast_wilderness's own docstring):

    py from world.wilderness_amber_coast import setup_amber_coast_wilderness as s; s()
"""

import random

from evennia import DefaultExit
from evennia.contrib.grid import wilderness
from evennia.utils import create

from world.wilderness_rome import FixedWildernessRoom

# --- Map bounds -------------------------------------------------------

# y=0 is the threshold just past "The Contested Ridge" (the Germanic
# Stronghold's own northernmost room); y=ROAD_LENGTH is where the
# authored Amber Coast's own "Coastal Road" picks up. 50 "legs" of
# road, matching the request's own "at least 50 rooms" floor exactly
# rather than padding past it for its own sake - the original
# Rome-Germania road used 25 legs for a ~1,500km/2-month journey, and
# this stretch (Stronghold to a Baltic-facing river delta, further but
# not dramatically so) doubling that abstraction is proportionate.
ROAD_LENGTH = 50

WIDTH = 10

WILDERNESS_NAME = "amber_coast_road"


# --- Terrain bands ------------------------------------------------------
# Deliberately distinct from wilderness_rome.py's farmland-to-forest
# arc - this road starts in the Stronghold's own borderlands (already
# forest) and trends toward marsh/dune/coast, matching the Amber
# Coast's own "river delta facing the Danish straits" premise. No
# "final_approach into a settlement" band at the very end the way the
# original road has one - that role belongs to the authored Coastal
# Road, not this wilderness stretch, so the last band here is still
# genuinely wild (dune_approach), just with the first real hints of
# the town's smoke on the final leg.

def _band(y):
    if y <= 10:
        return "borderland_fringe"
    if y <= 20:
        return "highland_moor"
    if y <= 30:
        return "fen_country"
    if y <= 40:
        return "salt_marsh"
    return "dune_approach"


_ROAD_NAMES = {
    "borderland_fringe": "A Trail Through the Borderland Fringe",
    "highland_moor": "A Trail Across the Highland Moor",
    "fen_country": "A Trail Through Fen Country",
    "salt_marsh": "A Trail Through the Salt Marsh",
    "dune_approach": "A Trail Through the Rising Dunes",
}

_ROAD_DESCS = {
    "borderland_fringe": [
        """|gThe contested borderlands thin out|n behind you, the
        packed-earth trail continuing north into territory no
        warband bothers to claim. |wStill forest, still real
        ground|n - just nobody's ground in particular anymore.""",
        """|gOld, half-grown-over cart ruts|n mark this trail - once
        traveled more than it is now. The forest presses in on both
        sides, quieter than the borderlands' own restless violence.""",
    ],
    "highland_moor": [
        """|yOpen, wind-scoured moorland|n replaces the forest here,
        heather and bare stone underfoot. |wThe trail is easy to
        lose|n in the low light, marked mostly by worn patches in
        the heather.""",
        """|yLow hills roll out|n in every direction, treeless and
        exposed. The wind carries something colder than it did back
        in the borderlands - a real hint of what's ahead.""",
    ],
    "fen_country": [
        """|GThe ground turns soft and uncertain|n, real fen country
        now - reed beds and standing water crowding close to the
        trail. |wEvery step off the packed path risks a soaking|n.""",
        """|GBlack, waterlogged earth|n stretches out on either side,
        threaded with narrow channels of still water. The trail
        survives here only because someone keeps deliberately
        maintaining it.""",
    ],
    "salt_marsh": [
        """|cThe first real taste of salt air|n reaches you here, gulls
        crying somewhere out of sight. |wThe fen has given way to
        genuine salt marsh|n - brackish, reeking faintly of the sea.""",
        """|cReed and brackish water|n stretch toward a horizon you
        can't quite see yet. |wThe trail runs along a low, built-up
        causeway|n through it - somebody's real engineering, holding
        back the marsh.""",
    ],
    "dune_approach": [
        """|wReal dunes rise ahead|n, pale grass clinging to shifting
        sand. |YThe sea itself is close now|n - the marsh smell has
        turned fully to salt and open water.""",
        """|wThe trail climbs over low, wind-carved dunes|n, sand
        working its way into everything. |YSomewhere ahead, faint
        against the wind, something that might be woodsmoke.|n""",
    ],
}

_OFFROAD_NAMES = {
    "borderland_fringe": "The Borderland Fringe",
    "highland_moor": "The Highland Moor",
    "fen_country": "Fen Country",
    "salt_marsh": "The Salt Marsh",
    "dune_approach": "The Rising Dunes",
}

_OFFROAD_DESCS = {
    "borderland_fringe": [
        """|gUnclaimed forest|n, thick enough that the trail
        disappears from sight within a few steps of leaving it.
        Nobody's watching this ground - which isn't the same as it
        being safe.""",
        """|gDense, untended woodland|n, old enough that no warband's
        axe has ever touched it. Quiet, in a way the borderlands
        never quite managed.""",
    ],
    "highland_moor": [
        """|yBare, rolling moor|n in every direction, heather and
        exposed stone. Nothing to break the wind out here at all.""",
        """|yA low rise of open heath|n, easy to see a long way from
        - and just as easy to be seen from, just as far.""",
    ],
    "fen_country": [
        """|GStanding water and reed beds|n make for slow, unpleasant
        going. The ground doesn't trust your weight out here.""",
        """|GA maze of narrow, waterlogged channels|n, easy to lose
        the trail in if you wander too far from it.""",
    ],
    "salt_marsh": [
        """|cBrackish marsh water|n pools everywhere underfoot, reed
        beds taller than a person in places. The sea is close, even
        if you still can't see it.""",
        """|cTidal mud and reed|n stretch out around you, gulls
        wheeling somewhere overhead. Genuinely easy to get stuck out
        here.""",
    ],
    "dune_approach": [
        """|wShifting dune grass|n covers uneven, sand-heavy ground.
        The sound of real surf carries clearly now, somewhere close.""",
        """|wOpen dune country|n, salt-scoured and sparse. Whatever
        lives out here has the sea a lot closer than the forest.""",
    ],
}

# Encounter levels - see this module's own docstring for the +21
# recalibration this whole location uses to bridge from the real
# Stronghold's 27-46 range rather than the design doc's assumed 1-25.
# Ramps from just above the Stronghold's own cap (46) up to the
# authored Coastal Road's own starting band (43-48 after the same
# shift), rather than restarting low.
_ENCOUNTER_LEVELS = {
    "borderland_fringe": (44, 47),
    "highland_moor": (46, 49),
    "fen_country": (47, 50),
    "salt_marsh": (48, 51),
    "dune_approach": (49, 52),
}

# Same discipline wilderness_rome.py's own note documents: real
# playable races/classes only, banded by terrain, escalating with
# distance rather than one flat pool. Coastal-flavored names distinct
# from the Stronghold's own warband naming (Wolf-kin/Boar-marked/
# Raven's Watch/Storm-callers) - these are unaffiliated wild threats
# on the road, not any of the Amber Coast's own four named warbands
# (which are persistent, placed NPCs, not random encounters).
_ENCOUNTER_NAMES = {
    "borderland_fringe": [
        ("an unclaimed raider", "human", "barbarian"),
        ("a forest scout", "centaur", "venator"),
    ],
    "highland_moor": [
        ("a moor bandit", "human", "gladiator"),
        ("a Harpy skirmisher", "harpy", "venator"),
    ],
    "fen_country": [
        ("a fen-lurker", "human", "venator"),
        ("a Cyclops wanderer", "cyclops", "barbarian"),
    ],
    "salt_marsh": [
        ("a marsh raider", "human", "barbarian"),
        ("a Minotaur outrider", "minotaur", "barbarian"),
    ],
    "dune_approach": [
        ("a dune raider", "human", "venator"),
        ("a Minotaur outrider", "minotaur", "barbarian"),
    ],
}

ENCOUNTER_CHANCE = 0.2
_ENCOUNTER_TAG = ("wilderness_encounter", "wilderness")

ENCOUNTER_CLEANUP_SECONDS = 600


def _cleanup_encounter_npc(npc):
    """Module-level, not a closure - see wilderness_rome.py's own
    identical note on why (persistent delay serialization)."""
    if not npc or not npc.pk:
        return
    from evennia.utils import delay
    from world.combat import COMBAT_RULES

    if COMBAT_RULES.is_in_combat(npc):
        delay(60, _cleanup_encounter_npc, npc, persistent=True)
        return
    npc.delete()


def _schedule_encounter_cleanup(npc, in_seconds=ENCOUNTER_CLEANUP_SECONDS):
    from evennia.utils import delay

    delay(in_seconds, _cleanup_encounter_npc, npc, persistent=True)


def _aggro_on_sight(npc, caller, room):
    """Identical mechanism to wilderness_rome.py's own _aggro_on_sight
    - see that function's docstring for the full reasoning (reuses
    CombatTurnHandler's real pending_fighters handoff, respects an
    active Sanctuary, no-ops for non-player movers)."""
    if not caller or not getattr(caller, "has_account", False):
        return

    from world.combat import COMBAT_RULES, CombatTurnHandler

    if not COMBAT_RULES.try_break_sanctuary(npc, caller):
        room.msg_contents("%s is here." % npc.key)
        return

    room.msg_contents("|r%s lunges out and attacks!|n" % npc.key)
    room.ndb.pending_fighters = [npc, caller]
    room.scripts.add(CombatTurnHandler)


AMBER_COAST_ENTRY_ROOM = "The River Delta - Upper Reach"


def _ensure_boundary_exit(room, coordinates):
    """Identical pattern to wilderness_rome.py's own
    _ensure_boundary_exit - see that function's docstring for why this
    has to be checked/corrected on every at_prepare_room call rather
    than set once."""
    x, y = coordinates
    should_leave = (x == 0 and y == ROAD_LENGTH)

    north_exit = None
    for ex in room.exits:
        if ex.key == "north":
            north_exit = ex
            break
    if not north_exit:
        return

    is_leave_exit = north_exit.is_typeclass(LeaveAmberCoastWildernessExit, exact=True)
    if should_leave and not is_leave_exit:
        north_exit.delete()
        create.create_object(
            "world.wilderness_amber_coast.LeaveAmberCoastWildernessExit",
            key="north", aliases=["n"], location=room, destination=room,
        )
    elif not should_leave and is_leave_exit:
        north_exit.delete()
        create.create_object(
            wilderness.WildernessExit,
            key="north", aliases=["n"], location=room, destination=room,
        )


class LeaveAmberCoastWildernessExit(DefaultExit):
    """The real crossover from this wilderness's north edge (0,
    ROAD_LENGTH) into the authored Amber Coast's own "The River Delta
    - Upper Reach" room (the first room of its own 10-room Coastal
    Road sequence, world/batch_amber_coast_data.py) - identical
    mechanism to wilderness_rome.LeaveGermaniaWildernessExit."""

    def at_traverse(self, traversing_object, target_location, **kwargs):
        from evennia.utils import search

        real_room = search.search_object(
            AMBER_COAST_ENTRY_ROOM, typeclass="typeclasses.rooms.Room"
        )
        if not real_room:
            traversing_object.msg(
                "Something's wrong - the way ahead doesn't lead anywhere right now."
            )
            return False

        traversing_object.msg(
            "|wThe dunes finally break - reed and standing water ahead, the first real delta ground.|n"
        )
        traversing_object.move_to(real_room[0], quiet=False, move_type="teleport")
        return True


class AmberCoastWildernessMapProvider(wilderness.WildernessMapProvider):
    # Fixes the same real at_object_receive()/move_type incompatibility
    # between the wilderness contrib and current Evennia core that
    # RomeWildernessMapProvider's own FixedWildernessRoom (world/
    # wilderness_rome.py) fixes for the original road - see that
    # class's own docstring for the full account.
    room_typeclass = FixedWildernessRoom

    def is_valid_coordinates(self, wildernessscript, coordinates):
        x, y = coordinates
        if y < 0 or y > ROAD_LENGTH:
            return False
        if abs(x) > WIDTH:
            return False
        return True

    def get_location_name(self, coordinates):
        x, y = coordinates
        band = _band(y)
        if x == 0:
            return _ROAD_NAMES[band]
        return _OFFROAD_NAMES[band]

    def at_prepare_room(self, coordinates, caller, room):
        x, y = coordinates
        band = _band(y)

        _ensure_boundary_exit(room, coordinates)

        for old in list(room.contents):
            if old.tags.get(_ENCOUNTER_TAG[0], category=_ENCOUNTER_TAG[1]):
                old.delete()

        if x == 0:
            room.ndb.active_desc = random.choice(_ROAD_DESCS[band])
            if y > 0 and y % 5 == 0:
                room.ndb.active_desc += (
                    "\n\n|YA weathered trail-marker notes the distance ahead: "
                    "|w%d miles to the coast.|n" % (15 * (ROAD_LENGTH - y))
                )
        else:
            room.ndb.active_desc = random.choice(_OFFROAD_DESCS[band])

        # See world/wilderness_rome.py's identical comment - a
        # pacifist (world/pacifism.py) can't be attacked by any NPC,
        # so no encounter spawns for them here either.
        if caller and caller.db.pacifist:
            pass
        elif caller and random.random() < ENCOUNTER_CHANCE:
            low, high = _ENCOUNTER_LEVELS[band]
            level = random.randint(low, high)
            name, race, player_class = random.choice(_ENCOUNTER_NAMES[band])
            npc = create.create_object(
                "world.combat.HostileNPC",
                key=name,
                location=room,
                attributes=[
                    ("race", race),
                    ("player_class", player_class),
                    ("level", level),
                    ("xp_reward", int(20 * level ** 1.9 * 0.06)),
                    ("desc", "Something out here that clearly isn't looking for company."),
                ],
            )
            npc.tags.add(_ENCOUNTER_TAG[0], category=_ENCOUNTER_TAG[1])
            npc.locks.add("get:false()")
            _schedule_encounter_cleanup(npc)
            _aggro_on_sight(npc, caller, room)


class AmberCoastWildernessScript(wilderness.WildernessScript):
    """Identical reload-survival pattern to
    wilderness_rome.GermaniaWildernessScript - see that class's own
    docstring for the two real bugs this fixes (GLOBAL_SCRIPTS
    registration for creation, at_server_start() called by hand for
    restoration, since Evennia's generic script-restart machinery
    skips non-ticking scripts)."""

    def at_script_creation(self):
        super().at_script_creation()
        self.db.mapprovider = AmberCoastWildernessMapProvider()


def setup_amber_coast_wilderness():
    """
    Wires the entrance exit from "The Contested Ridge" (the Germanic
    Stronghold's own northernmost room, world/batch_germania_data.py)
    into this wilderness. Deliberately NOT called as part of any
    automatic setup - this must only be run once the Amber Coast's own
    "The River Delta - Upper Reach" room genuinely exists live, or this
    creates a real, live dead-end door out of the Stronghold leading
    to a wilderness stretch with no way to actually finish crossing
    (LeaveAmberCoastWildernessExit would fail search_object and refuse
    to move the player, which is at least not silently broken, but
    still isn't a real deliverable to expose to players before the
    destination exists).

    Run once, in-game, as Developer/superuser, after a reload has
    picked up the GLOBAL_SCRIPTS entry AND the Amber Coast's first
    room has been placed:

        py from world.wilderness_amber_coast import setup_amber_coast_wilderness as s; s()
    """
    from evennia.utils import search

    ridge = search.search_object(
        "The Contested Ridge", typeclass="typeclasses.rooms.Room"
    )
    if not ridge:
        raise SystemExit("ABORTED: could not find 'The Contested Ridge' live.")
    ridge = ridge[0]

    if any(e.key == "north" for e in ridge.exits):
        return "Entrance exit already exists - nothing to do."

    create.create_object(
        "world.wilderness_amber_coast.EnterAmberCoastWildernessExit",
        key="north",
        location=ridge,
        destination=None,
    )
    return "Entrance wired up."


def _get_wilderness_script():
    """Identical to wilderness_rome.py's own _get_wilderness_script -
    see its docstring for why this bypasses the contrib's own
    enter_wilderness() helper (exact-typeclass filtering misses any
    subclass)."""
    import evennia

    return getattr(evennia.GLOBAL_SCRIPTS, WILDERNESS_NAME, None)


class EnterAmberCoastWildernessExit(DefaultExit):
    """A one-way entrance into the Amber Coast wilderness map, from
    "The Contested Ridge." Identical mechanism to
    wilderness_rome.EnterWildernessExit - no return exit built here on
    purpose, 'recall' is the way back."""

    def at_traverse(self, traversing_object, target_location, **kwargs):
        script = _get_wilderness_script()
        if not script:
            traversing_object.msg("Something's wrong - the trail north doesn't lead anywhere right now.")
            return False

        if not traversing_object.at_pre_move(None):
            return False
        traversing_object.location.msg_contents(
            "%s heads north, off the ridge and into open country." % traversing_object.key,
            exclude=[traversing_object],
        )
        script.move_obj(traversing_object, (0, 0))
        traversing_object.msg(
            "|wThe borderlands fall away behind you - a long trail north, toward the sea.|n"
        )
        traversing_object.at_post_move(None)
        return True

    def at_failed_traverse(self, traversing_object):
        traversing_object.msg("Something's wrong - the trail north doesn't lead anywhere right now.")
