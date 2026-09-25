"""
One-time live setup for the Herbalist profession's crafting trainer -
teaches recipes above tier 1 (see world/craft_commands.py's
CmdLearnRecipe, world/recipes.py's AntidoteRecipe) for gold. Placed at
"Market Row - Back Stalls", the same room already holding the
apothecary's mortar (world/setup_herbalist_live.py) and Aviola the
herbalist's own stall - the natural hub for this profession.

A real gap found live: the Herbalist profession shipped with a real,
gated (KNOWN_BY_DEFAULT=False) antidote recipe and no trainer anywhere
who could actually teach it - 'learnrecipe antidote' would have failed
for every player with "no one here can teach you that," forever,
mirroring the exact reason world/setup_faber_trainer_live.py exists
for Faber's own gated recipes. This closes that gap the same way.

Run once via `evennia shell < world/setup_herbalist_trainer_live.py`.
Not idempotent - re-running duplicates the trainer.
"""

from evennia.utils import search, create

room = search.search_object("Market Row - Back Stalls", typeclass="typeclasses.rooms.Room")
if not room:
    raise SystemExit("ABORTED: could not find the real 'Market Row - Back Stalls' room live.")

trainer = create.create_object(
    "world.craft_commands.CraftTrainer",
    key="a Herbalist apprentice",
    location=room[0],
    attributes=[
        (
            "desc",
            "Aviola's apprentice, hands stained green from crushed herbs. "
            "Younger and less patient than her mistress, but she knows "
            "the mortar and its recipes well enough to teach anyone "
            "willing to learn properly - and to pay for the lesson.",
        ),
        ("teaches_profession", "herbalist"),
    ],
)

print("Created the Herbalist trainer at Market Row - Back Stalls:", trainer)
