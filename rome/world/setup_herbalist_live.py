"""
One-time live setup for the Herbalist profession's real location -
Market Row - Back Stalls (the Subura), right where Aviola the
herbalist (world.economy.SuburaApothecary) already deals in exactly
this trade. Places the apothecary's mortar Herbalist recipes require
(world/recipes.py's HerbalistRecipe) and sets the room's own
db.gather_resource so herbs can actually be found there.

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
room.db.gather_resource = "herbs"

print("Placed the apothecary's mortar and set gather_resource='herbs' at Market Row - Back Stalls:", mortar)
