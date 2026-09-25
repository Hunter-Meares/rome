"""
One-time live setup for the Herbalist profession's crafting location -
Market Row - Back Stalls (the Subura), right where Aviola the
herbalist (world.economy.SuburaApothecary) already deals in exactly
this trade. Places the apothecary's mortar Herbalist recipes require
(world/recipes.py's HerbalistRecipe).

Deliberately does NOT set the room's own db.gather_resource - a real
correction, by direct feedback ("why would free herbs just be sitting
in a market? herbs should be gathered in the wilderness"). Herbs are
now gathered on Rome's own wilderness forest tiles instead (see
world/wilderness_rome.py, alongside timber) - this room is where you
CRAFT the tonic, not where you FIND the herbs, exactly mirroring
Faber's own split between the mine (gathering) and the Smithy
(crafting). If this script is ever re-run against a room that still
has a leftover db.gather_resource="herbs" from before this fix, it's
cleared here too.

Run once via `evennia shell < world/setup_herbalist_live.py`. Not
idempotent - re-running duplicates the mortar.
"""

from evennia.utils import search
from evennia.prototypes.spawner import spawn

room = search.search_object("Market Row - Back Stalls", typeclass="typeclasses.rooms.Room")
if not room:
    raise SystemExit("ABORTED: could not find the real 'Market Row - Back Stalls' room live.")
room = room[0]

mortar = spawn("APOTHECARY_MORTAR")[0]
mortar.location = room
room.attributes.remove("gather_resource")

print("Placed the apothecary's mortar at Market Row - Back Stalls:", mortar)
