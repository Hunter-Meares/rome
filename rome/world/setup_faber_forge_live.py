"""
One-time live setup for the smithing forge Faber's recipes now
require (world/recipes.py's FaberRecipe, a real "craft at a fixed
location" requirement added by direct design request). Placed at "The
Smithy Forge" - the same room already anchoring the Ore Vein Shaft and
the Faber trainer.

Run once via `evennia shell < world/setup_faber_forge_live.py`. Not
idempotent - re-running duplicates the forge.
"""

from evennia.utils import search, create

smithy = search.search_object("The Smithy Forge", typeclass="typeclasses.rooms.Room")
if not smithy:
    raise SystemExit("ABORTED: could not find the real 'The Smithy Forge' room live.")

from evennia.prototypes.spawner import spawn

forge = spawn("FABER_FORGE")[0]
forge.location = smithy[0]

print("Placed the smithing forge at The Smithy Forge:", forge)
