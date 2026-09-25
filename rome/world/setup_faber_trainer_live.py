"""
One-time live setup for Faber's crafting trainer - teaches recipes
above tier 1 (see world/craft_commands.py's CmdLearnRecipe,
world/recipes.py's IronLoricaRecipe/IronWarSpearRecipe) for gold.
Placed at "The Smithy Forge" - the same room already anchoring the
Ore Vein Shaft (world/setup_ore_vein_shaft_live.py) and the Germanic
weaponsmith's own stall, the natural hub for this profession.

Run once via `evennia shell < world/setup_faber_trainer_live.py`. Not
idempotent - re-running duplicates the trainer.
"""

from evennia.utils import search, create

smithy = search.search_object("The Smithy Forge", typeclass="typeclasses.rooms.Room")
if not smithy:
    raise SystemExit("ABORTED: could not find the real 'The Smithy Forge' room live.")

trainer = create.create_object(
    "world.craft_commands.CraftTrainer",
    key="a Faber master smith",
    location=smithy[0],
    attributes=[
        (
            "desc",
            "Older than the working smiths around him, and slower with "
            "the hammer these days, but there's little about ironwork he "
            "hasn't done himself at least once. He watches new hands at "
            "the forge with the patient, faintly critical eye of someone "
            "who's willing to teach, if asked properly.",
        ),
        ("teaches_profession", "faber"),
    ],
)

print("Created the Faber trainer at The Smithy Forge:", trainer)
