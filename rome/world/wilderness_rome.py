"""
Rome's wilderness - the wilderness contrib (evennia.contrib.grid.wilderness),
bounded and customized rather than used raw. Two distinct problems
this solves, both raised directly:

1. "Mass wilderness" surrounding a single main road, without hand-
   authoring hundreds of individual Room objects for something meant
   to repeat by design ("it's okay to repeat descriptions for the
   same type of wilderness"). The wilderness contrib is built exactly
   for this - one room object recycled to represent a whole (x, y)
   grid, real DB cost staying tiny no matter how large the map reads
   to a player.

2. "I don't want players to get lost in infinite wilderness." The
   contrib's default map provider is genuinely unbounded - explicitly
   documented as such. RomeWildernessMapProvider below overrides
   is_valid_coordinates to hard-bound the map instead: y is the road
   toward the Germanic settlement (0 = the Porta Flaminia's threshold,
   ROAD_LENGTH = the settlement's own outer edge), x is how far off
   the road a player can wander to either side before hitting a real,
   named edge - not a silent wall, an actual "you go no further this
   way" refusal.

The x=0 column is the road itself - a real, authored-feeling path
with occasional milestones - genuinely distinct in tone from the
open wilderness to either side, exactly as requested: "similar or the
same description with occasional signs" on the road, "repeat
descriptions for the same type of wilderness" off it. Terrain shifts
in bands as y increases - farmland near the city, thinning to
scrubland, then forest, then deep woods - the same tonal arc as the
original design brief, just delivered as description bands over a
coordinate grid instead of individually hand-authored rooms.

Random wilderness encounters (the "bandits" ask) use the contrib's
own at_prepare_room hook - called every time a room is freshly
activated for whoever just moved into it - to roll a chance and spawn
a temporary NPC in fresh each visit, rather than permanently seeding
NPCs at fixed coordinates (which would fight the contrib's own room-
recycling model; see the module's own note on why persistent seeding
doesn't fit here). Any encounter left over from a previous visit is
cleared first, so a recycled room never carries stale monsters into
someone else's independent roll.

One-time live setup, once this module and its setup script both
exist:

    py from world.wilderness_rome import setup_germania_wilderness as s; s()
"""

import random

from evennia import DefaultExit
from evennia.contrib.grid import wilderness
from evennia.utils import create

# --- Map bounds -------------------------------------------------------

# y=0 is the threshold just past the Porta Flaminia ("The Road's True
# Start"); y=ROAD_LENGTH is the settlement's own outer edge, where the
# (not-yet-built) Germanic stronghold picks up. ~25 "legs" of road,
# each one abstractly standing in for a real day or more of the
# ~1,500km, ~2-month march this represents - not literal 1:1 scale,
# which would need thousands of rooms, but a real journey rather than
# a stroll.
ROAD_LENGTH = 25

# How far off the road a player can wander to either side before
# hitting the map's hard edge - real wandering room, not infinite.
WIDTH = 10

WILDERNESS_NAME = "germania_road"


# --- Terrain bands, by y (matches the original tonal-arc design) -----

def _band(y):
    if y <= 5:
        return "farmland"
    if y <= 10:
        return "scrubland"
    if y <= 16:
        return "forest_edge"
    if y <= 22:
        return "deep_woods"
    return "final_approach"


_ROAD_NAMES = {
    "farmland": "A Road Through the Countryside",
    "scrubland": "A Road Through Open Scrubland",
    "forest_edge": "A Road Along the Forest's Edge",
    "deep_woods": "A Road Through the Deep Woods",
    "final_approach": "A Road Through the Last Stretch of Wilderness",
}

_ROAD_DESCS = {
    "farmland": [
        """|gVineyards and tended fields|n spread out on either side
        of the road, still recognizably Roman - this is the empire's
        own countryside, worked and orderly, not yet the wild.""",
        """|gTerraced fields|n run alongside the paved road here,
        small herds grazing the hills beyond them. |wRome's hand is
        still visibly on this land|n, even this far from the gate.""",
    ],
    "scrubland": [
        """|yThe cultivated fields have thinned out|n, giving way to
        open, unclaimed scrub. |wThe road runs straight through it
        regardless|n - engineered ground doesn't care what's grown
        on either side of it.""",
        """|ySparse grass and low brush|n cover the rolling ground on
        both sides of the road now. Fewer farms, fewer people -
        Rome's grip on this stretch is looser than it was a few
        miles back.""",
    ],
    "forest_edge": [
        """|GTrees crowd closer to the road|n here, the first real
        suggestion of forest rather than open country. |wThe paving
        stones are a little rougher underfoot|n - maintained less
        often, this far out.""",
        """|GThe tree line presses in|n from both sides, dense enough
        now to lose sight of the horizon. The road itself hasn't
        changed - still straight, still deliberate - but everything
        around it plainly has.""",
    ],
    "deep_woods": [
        """|gGenuinely deep woods|n now, the canopy thick enough to
        dim the road even at midday. |wFewer signs of maintenance|n -
        a fallen branch here, a cracked paving stone there, nobody's
        gotten around to clearing.""",
        """|gThe forest presses close|n on both sides, old growth
        that's never seen a Roman axe. The road persists anyway, a
        stubborn straight line through country that clearly doesn't
        want it there.""",
    ],
    "final_approach": [
        """|wSmoke rises|n somewhere ahead through the trees, and the
        unmistakable shapes of timber construction - not stone, never
        stone out here - are visible at the edge of sight. |YThe
        settlement is close now.|n""",
        """|wThe woods begin to thin|n just enough to make out real
        structures ahead - a palisade, watchfires, the shape of a
        settlement that was never going to be built the Roman way.""",
    ],
}

_OFFROAD_NAMES = {
    "farmland": "Open Farmland",
    "scrubland": "Sparse Scrubland",
    "forest_edge": "The Forest's Edge",
    "deep_woods": "Deep Forest",
    "final_approach": "Wilderness Near the Settlement",
}

_OFFROAD_DESCS = {
    "farmland": [
        """|gCultivated fields|n stretch out in every direction,
        vines and grain both worked by hands you can't see from here.
        It's mostly clear, quiet, and unremarkable.""",
        """|gA gently sloping pasture|n, a few grazing animals paying
        you no attention at all. Rome's countryside, ordinary and
        undramatic.""",
    ],
    "scrubland": [
        """|ySparse, wind-bent grass|n covers ground too poor or too
        far from water to bother cultivating. Nothing much moves out
        here.""",
        """|yLow scrub and bare patches of dry earth|n stretch out
        around you, the road a thin grey line somewhere back the way
        you came.""",
    ],
    "forest_edge": [
        """|GScattered trees|n, not yet a real forest but getting
        there - the road feels farther away out here than it
        actually is.""",
        """|GThe tree cover thickens unevenly|n around you, patches
        of open ground between stands of real woodland.""",
    ],
    "deep_woods": [
        """|gDense, old forest|n presses in on every side, the light
        dim even this far from evening. Easy to lose your bearings
        out here.""",
        """|gTangled undergrowth and old-growth trunks|n make for
        slow going. The forest doesn't feel especially glad to have
        you in it.""",
    ],
    "final_approach": [
        """|wThinning trees|n and the distant sound of a settlement
        somewhere off through the woods - close enough now that
        wandering feels riskier than it did further south.""",
        """|wOpen patches of cleared ground|n dot the forest here,
        worked by hands that clearly aren't Roman.""",
    ],
}

# Level bands for random encounters, roughly matching a player's own
# expected level on this stretch of the journey (post-sewers, level
# 25, climbing toward the settlement's 25-45 range) - modest, real
# danger while traveling, not the main leveling content, which is the
# settlement itself.
_ENCOUNTER_LEVELS = {
    "farmland": (24, 27),
    "scrubland": (26, 30),
    "forest_edge": (29, 34),
    "deep_woods": (33, 39),
    "final_approach": (37, 43),
}

# Banded by terrain, not one flat pool - a real gap found by direct
# question ("are you using a variety of races/classes?"): the original
# 3-entry pool was all race="human", including "a hungry wolf" (a
# mismatch this game's race system doesn't really have room for - no
# playable race is a literal animal, matching how every other "feral"
# NPC in the game is already built from a real humanoid race+class
# pair rather than something outside that system). Rebuilt with real
# variety AND a deliberate escalation - human threats close to Rome,
# the same non-human races the Germanic settlement's own warband
# camps are designed around (Minotaur/Cyclops muscle, Centaur
# scouts, Harpy skirmishers) showing up as the terrain gets wilder,
# previewing the destination rather than introducing it out of
# nowhere at the settlement's own gate.
_ENCOUNTER_NAMES = {
    "farmland": [
        ("a wandering bandit", "human", "gladiator"),
        ("a Subura footpad", "human", "speculator"),
    ],
    "scrubland": [
        ("a wandering bandit", "human", "gladiator"),
        ("a deserting legionary", "human", "legionary"),
    ],
    "forest_edge": [
        ("a forest raider", "human", "venator"),
        ("a Centaur scout", "centaur", "venator"),
    ],
    "deep_woods": [
        ("a Centaur scout", "centaur", "venator"),
        ("a Cyclops raider", "cyclops", "barbarian"),
    ],
    "final_approach": [
        ("a Minotaur warrior", "minotaur", "barbarian"),
        ("a Harpy skirmisher", "harpy", "venator"),
    ],
}

ENCOUNTER_CHANCE = 0.2
_ENCOUNTER_TAG = ("wilderness_encounter", "wilderness")

# A room only gets its stale encounter cleared out (see at_prepare_room
# below) the next time someone actually walks back into that exact
# (x, y) - which, on a bounded but still very large map, might be
# never. Without this, an encounter nobody fights would sit in the
# database forever once its room gets recycled out from under it
# (recycling clears the room's contents' location, not the objects
# themselves - a real gap, found live: 7 orphaned NPCs turned up in a
# single test walk). This is the backstop: every spawned encounter
# deletes itself after ENCOUNTER_CLEANUP_SECONDS regardless of whether
# its room ever gets revisited, unless it's actively being fought,
# in which case it reschedules rather than vanishing mid-fight.
ENCOUNTER_CLEANUP_SECONDS = 600


def _cleanup_encounter_npc(npc):
    """
    Module-level (not a closure) specifically so this can be scheduled
    with persistent=True below - a closure over npc wouldn't survive
    being serialized for a persistent delayed task, so a reload
    between spawn and cleanup would silently lose the callback and
    leak the NPC right back into the same problem this exists to fix.
    """
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
    """
    Forces combat to start immediately between npc and whoever just
    walked in on it, by direct request - the one place in the entire
    game a hostile NPC attacks on sight rather than waiting for the
    player to type 'fight' first (every other NPC anywhere, including
    the Germanic Stronghold's own persistent warband population,
    keeps the normal player-initiated convention; this is deliberately
    scoped to just the wilderness road, to make leaving Rome's gates
    feel genuinely dangerous rather than a guided tour).

    Reuses the exact same mechanism CmdFight itself uses
    (world.combat.CombatTurnHandler's own pending_fighters handoff),
    not a bespoke duel - so turn order still comes from a real,
    fair roll_init roll (an ambushed player isn't guaranteed to lose
    the first exchange, just to not get a choice about whether the
    fight happens at all), and an active Medicus Sanctuary still
    holds exactly like it does against a player-initiated fight.

    No-ops for anything without a real account (the encounter's own
    self-cleanup timer, or some future non-player mover, shouldn't be
    able to trigger this).
    """
    if not caller or not getattr(caller, "has_account", False):
        return

    from world.combat import COMBAT_RULES, CombatTurnHandler

    if not COMBAT_RULES.try_break_sanctuary(npc, caller):
        room.msg_contents("%s is here." % npc.key)
        return

    room.msg_contents("|r%s lunges out and attacks!|n" % npc.key)
    room.ndb.pending_fighters = [npc, caller]
    room.scripts.add(CombatTurnHandler)


GERMANIA_SETTLEMENT_ENTRY_ROOM = "The Palisade Gate"


def _ensure_boundary_exit(room, coordinates):
    """
    The wilderness's own room-recycling model means the same physical
    room object represents a different (x, y) tile every time someone
    new moves into it - so a special "leave the wilderness here" exit
    can't just be added once and left alone, or it would misfire the
    next time this exact room shell gets reused for a completely
    different, non-boundary coordinate (silently teleporting someone
    to the settlement from the middle of nowhere). Checked and
    corrected on every single at_prepare_room call instead: the
    settlement's north edge (0, ROAD_LENGTH) gets a real
    LeaveGermaniaWildernessExit in place of the standard "north"
    WildernessExit; every other coordinate gets the standard one
    restored if this room shell happens to have carried the special
    one over from a previous visitor.
    """
    x, y = coordinates
    should_leave = (x == 0 and y == ROAD_LENGTH)

    north_exit = None
    for ex in room.exits:
        if ex.key == "north":
            north_exit = ex
            break
    if not north_exit:
        return

    is_leave_exit = north_exit.is_typeclass(LeaveGermaniaWildernessExit, exact=True)
    if should_leave and not is_leave_exit:
        north_exit.delete()
        create.create_object(
            "world.wilderness_rome.LeaveGermaniaWildernessExit",
            key="north", aliases=["n"], location=room, destination=room,
        )
    elif not should_leave and is_leave_exit:
        north_exit.delete()
        create.create_object(
            wilderness.WildernessExit,
            key="north", aliases=["n"], location=room, destination=room,
        )


class LeaveGermaniaWildernessExit(DefaultExit):
    """
    The real crossover from the wilderness's north edge (0,
    ROAD_LENGTH) into the actual, authored Germanic Stronghold - see
    _ensure_boundary_exit's own docstring for why this can't just be a
    normal, permanently-placed exit. A genuine room-to-room move via
    move_to() (not a coordinate shift like WildernessExit uses),
    which already correctly triggers the wilderness's own cleanup on
    the way out (the exact same path CmdRecall already proved works
    from anywhere in the wilderness).
    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        from evennia.utils import search

        real_room = search.search_object(
            GERMANIA_SETTLEMENT_ENTRY_ROOM, typeclass="typeclasses.rooms.Room"
        )
        if not real_room:
            traversing_object.msg(
                "Something's wrong - the way ahead doesn't lead anywhere right now."
            )
            return False

        traversing_object.msg(
            "|wThe wilderness finally, genuinely ends - a real palisade rises ahead.|n"
        )
        traversing_object.move_to(real_room[0], quiet=False, move_type="teleport")
        return True


class RomeWildernessMapProvider(wilderness.WildernessMapProvider):
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
                    "\n\n|YA worn milestone marks this spot: |w%d miles to Rome.|n"
                    % (25 * (ROAD_LENGTH - y))
                )
        else:
            room.ndb.active_desc = random.choice(_OFFROAD_DESCS[band])

        if caller and random.random() < ENCOUNTER_CHANCE:
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


class GermaniaWildernessScript(wilderness.WildernessScript):
    """
    Two real, separate bugs were found live getting reload-survival to
    actually work, not one:

    1. create_wilderness() (the original version of this module) makes
       a plain WildernessScript with no persistent registration -
       nothing recreates it if it's ever missing, and nothing
       guarantees it exists before players start using it after a
       true process restart. Fixed by registering this typeclass as a
       GLOBAL_SCRIPTS entry (server/conf/settings.py) instead -
       Evennia creates and tracks it reliably on every boot.

    2. GLOBAL_SCRIPTS alone was NOT enough, and this is the one that
       actually broke movement: Evennia's generic script-restart
       machinery (the thing that's supposed to call a script's own
       at_server_start(), the hook this class inherits from
       WildernessScript to restore every room's ndb.wildernessscript)
       only resumes scripts with a real ticking interval - this
       script has none, it's a pure data container. Verified directly
       from inside a real reload: logging every room's
       ndb.wildernessscript right at boot showed None. The actual fix
       is in server/conf/at_server_startstop.py's at_server_start() -
       the one hook Evennia guarantees fires on every boot regardless
       of script intervals - which explicitly calls this script's
       at_server_start() by hand.

    (A third, easier trap along the way: testing this via `evennia
    shell` invocations gives EACH one its own separate Python process
    with its own empty ndb space, completely disconnected from the
    live server's - querying ndb through a one-off shell can never
    prove or disprove reload-survival either way. The real check has
    to run from inside the live server process itself, e.g. via this
    same at_server_start() hook.)
    """

    def at_script_creation(self):
        super().at_script_creation()
        self.db.mapprovider = RomeWildernessMapProvider()


def setup_germania_wilderness():
    """
    Wires the real entrance exit from "The Road's True Start"
    (world/batch_wall_gate_data.py) into the wilderness - the
    wilderness script itself is created and kept running by Evennia's
    own GLOBAL_SCRIPTS machinery (see server/conf/settings.py's
    GLOBAL_SCRIPTS["germania_road"]), not by this function. Idempotent
    - safe to run again any time. Run once, in-game, as Developer/
    superuser, after a reload has picked up the GLOBAL_SCRIPTS entry:

        py from world.wilderness_rome import setup_germania_wilderness as s; s()
    """
    from evennia.utils import search

    road_start = search.search_object(
        "The Road's True Start", typeclass="typeclasses.rooms.Room"
    )
    if not road_start:
        raise SystemExit("ABORTED: could not find 'The Road's True Start' live.")
    road_start = road_start[0]

    if any(e.key == "north" for e in road_start.exits):
        return "Entrance exit already exists - nothing to do."

    create.create_object(
        "world.wilderness_rome.EnterWildernessExit",
        key="north",
        location=road_start,
        destination=None,
    )
    return "Entrance wired up."


def _get_wilderness_script():
    """
    Returns the live GermaniaWildernessScript, or None. Deliberately
    NOT WildernessScript.objects.filter(db_key=...) - a real bug found
    live: Evennia's typeclass-bound managers filter by EXACT typeclass,
    so WildernessScript.objects (what the contrib's own
    enter_wilderness() uses internally) never finds a
    GermaniaWildernessScript instance at all, silently failing every
    single time. evennia.GLOBAL_SCRIPTS.<key> - the same lookup
    GLOBAL_SCRIPTS itself uses - finds it correctly regardless of
    subclassing, so this bypasses the contrib's own helper function
    entirely rather than trying to work around its manager.
    """
    import evennia

    return getattr(evennia.GLOBAL_SCRIPTS, WILDERNESS_NAME, None)


class EnterWildernessExit(DefaultExit):
    """
    A one-way entrance into the Germania wilderness map, from "The
    Road's True Start." Doesn't move the traverser to a normal room -
    finds the live wilderness script directly (see
    _get_wilderness_script's own docstring for why not the contrib's
    own enter_wilderness() helper) and calls its move_obj() to drop
    the traverser at (0, 0), the road's own starting tile. Getting
    back to Rome from inside the wilderness is what 'recall' is for
    (see world/combat.py's CmdRecall) - there's no return exit built
    here on purpose.
    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        script = _get_wilderness_script()
        if not script:
            traversing_object.msg("Something's wrong - the road north doesn't lead anywhere right now.")
            return False

        if not traversing_object.at_pre_move(None):
            return False
        traversing_object.location.msg_contents(
            "%s heads north, off toward the wilderness." % traversing_object.key,
            exclude=[traversing_object],
        )
        script.move_obj(traversing_object, (0, 0))
        traversing_object.msg(
            "|wThe last real houses of Rome fall behind you - open country ahead now.|n"
        )
        traversing_object.at_post_move(None)
        return True

    def at_failed_traverse(self, traversing_object):
        traversing_object.msg("Something stops you from heading that way.")
