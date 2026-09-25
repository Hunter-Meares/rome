"""
Gathering - the solo, in-the-field half of the crafting economy
(world/recipes.py is the other half: turning what's gathered here
into something sellable). Deliberately simple: a room flagged with a
resource type, and a per-character real-time cooldown per resource,
rather than shared, depletable per-room node state.

Real design tradeoff, made deliberately: the original design doc
talks about resources "respawning" (timber fast, mined ore slow),
which reads like shared per-location node state. Implementing genuine
shared state on a WILDERNESS room specifically is a real complication
this project has already hit before (see world/wilderness_rome.py's
own module docstring on the recycled-room-represents-every-coordinate
problem, and its _schedule_encounter_cleanup for the kind of extra
bookkeeping that shared state needs) - the wilderness contrib only
ever gives a coordinate its own room object while someone is actually
standing there, so two different players at two different coordinates
already can't see each other's gathering state, but persisting "this
exact tile is depleted until such-and-such time" across visits would
still need its own coordinate-keyed storage the same way encounter
cleanup does.

A per-character cooldown produces the IDENTICAL player-facing result
("you can gather this again in about N") without any of that
complexity, and fits this project's own "low population, mostly
solo" design philosophy even better than shared depletion would -
nobody is ever competing over a node, which is the whole point of a
solo-viable economy.

Where resources are actually placed:
  - "timber" (common, fast respawn) - off-road tiles in the wilderness
    road's own "forest_edge"/"deep_woods" bands (world/wilderness_
    rome.py's at_prepare_room sets room.ndb.gather_resource).
  - "iron_ore" (rare, ~once-a-day respawn) - "The Ore Vein Shaft", a
    small new room off the Germanic Stronghold's existing Smithy (see
    world/setup_ore_vein_shaft_live.py), which sets db.gather_resource
    persistently (a real authored room, not a recycled one, so a
    plain db Attribute is fine here - no per-coordinate concern).

Selling what's gathered (raw, or crafted into something via
world/recipes.py) happens through the ordinary shop 'sell' flow
already built in world/economy.py - nothing new needed there beyond
giving each material/craft item a real db.price, plus a per-merchant
db.distance_bonus for selling further from Rome.

FINDING a resource is its own separate roll, added by direct design
request: gathering originally worked "stand in the right room, type
gather, always succeeds (subject only to your own cooldown)" - too
easy, and it rewarded parking in one spot rather than actually
exploring. announce_gather_spot() (called from CombatCharacter.
at_post_move, mirroring world/wilderness_rome.py's own
ENCOUNTER_CHANCE mechanism almost exactly) rolls SPOT_CHANCE on every
real move into an eligible room; a hit sets a character-local
ndb.gather_spot and prints a "you spot..." message, a miss says
nothing at all. `gather` itself now additionally requires that flag
to be set - walking into a wooded tile no longer guarantees anything
is there to take, only that there MIGHT be, and you have to actually
move around (and get a little lucky) to find out.
"""

import random
import time

from evennia import Command
from evennia.prototypes.spawner import spawn

# Chance, per real move into an eligible room, that a resource is
# actually there to gather right now - independent of, and checked
# before, the character's own per-resource cooldown (no point
# "finding" something you can't take yet).
SPOT_CHANCE = 0.4

SPOT_MESSAGES = {
    "timber": (
        "|YYou spot a fallen, sun-dried log half-buried in the "
        "underbrush - good timber, if you take it now.|n"
    ),
    "iron_ore": (
        "|YA vein catches the light in the rock wall, rust-streaked "
        "and clearly workable.|n"
    ),
}

# Every gatherable material: which prototype it spawns, its display
# name for messages, and its cooldown in real seconds. "Common" vs
# "rare" is a deliberate design axis, not just a tuning number - see
# rome_mud_todo.md's crafting section for the "timber fast, mined ore
# ~once/day" framing this matches directly.
GATHERABLE_MATERIALS = {
    "timber": {
        "prototype": "RAW_TIMBER",
        "cooldown": 300,  # 5 real minutes - common, always around
    },
    "iron_ore": {
        "prototype": "RAW_IRON_ORE",
        "cooldown": 86400,  # ~once a day - rare, worth the trip
    },
}


def gather_resource_here(character):
    """The resource key available in character's current room, or
    None. Checks ndb first (a recycled wilderness tile) then db (a
    real, permanently-authored room like the Ore Vein Shaft)."""
    location = character.location
    if not location:
        return None
    resource = location.ndb.gather_resource
    if resource is None:
        resource = location.db.gather_resource
    return resource if resource in GATHERABLE_MATERIALS else None


def cooldown_remaining(character, resource):
    """Real seconds left before character can gather this resource
    again, 0 or less if ready now."""
    cooldowns = character.db.gather_cooldowns or {}
    last = cooldowns.get(resource, 0)
    elapsed = time.time() - last
    return max(0, GATHERABLE_MATERIALS[resource]["cooldown"] - elapsed)


def announce_gather_spot(character):
    """
    Called on every real move (CombatCharacter.at_post_move). Clears
    any previous spot first - a find is only good for the room you
    found it in, not carried forward - then rolls fresh for the
    character's current room. Silent on a miss, same as the
    wilderness's own ENCOUNTER_CHANCE roll.
    """
    character.ndb.gather_spot = None
    resource = gather_resource_here(character)
    if not resource:
        return
    if cooldown_remaining(character, resource) > 0:
        # Nothing to spot if they couldn't gather it yet anyway.
        return
    if random.random() < SPOT_CHANCE:
        character.ndb.gather_spot = resource
        character.msg(SPOT_MESSAGES.get(resource, "You spot something worth gathering here."))


def _format_remaining(seconds):
    if seconds < 120:
        return "%d seconds" % int(seconds)
    minutes = seconds / 60
    if minutes < 120:
        return "%d minutes" % int(minutes)
    return "%d hours" % int(minutes / 60)


class CmdGather(Command):
    """
    Gather a raw material from wherever you're standing.

    Usage:
      gather

    Some places - a wooded stretch of wilderness, a mine shaft - might
    have a real material waiting, but walking in is never a guarantee
    - you'll see a real message the moment there's actually something
    to take, so keep moving and looking if this spot comes up empty.
    There's nothing to fight and no risk involved either way; a
    pacifist can do this exactly as freely as anyone else. Once you've
    gathered somewhere, you personally need to wait before that same
    kind of material is available to you again - common materials
    (timber) refresh in minutes, rarer ones (mined ore) take much
    longer.
    """

    key = "gather"
    aliases = ["forage", "mine"]
    help_category = "general"

    def func(self):
        caller = self.caller
        resource = gather_resource_here(caller)
        if not resource:
            caller.msg("There's nothing to gather here.")
            return

        remaining = cooldown_remaining(caller, resource)
        if remaining > 0:
            caller.msg(
                "You've already taken what you could find here recently - "
                "try again in about %s." % _format_remaining(remaining)
            )
            return

        if caller.ndb.gather_spot != resource:
            caller.msg(
                "There's nothing to actually gather right here, right "
                "now - keep exploring and look around."
            )
            return

        obj = spawn(GATHERABLE_MATERIALS[resource]["prototype"])[0]
        obj.move_to(caller, quiet=True)
        caller.ndb.gather_spot = None

        cooldowns = caller.db.gather_cooldowns or {}
        cooldowns[resource] = time.time()
        caller.db.gather_cooldowns = cooldowns

        caller.msg("You gather %s." % obj.key)
        caller.location.msg_contents(
            "%s gathers something from the surroundings." % caller, exclude=caller
        )
