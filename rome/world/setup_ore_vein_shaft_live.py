"""
One-time live setup for the Ore Vein Shaft - a small (2-room) new mine
attached to the Germanic Stronghold's already-built Smithy, giving
iron ore (world/gathering.py, world/recipes.py's Faber recipes) a
real, safe place to be gathered outside Rome. Deliberately minimal:
this isn't a new zone in the scale of the Aventine/Amber Coast builds,
just enough real geography to make "mine ore, walk it to the forge,
craft, sell" a genuine place-to-place loop rather than an abstract
mechanic with nowhere to stand.

Attached via a NEW "down" exit from "The Smithy Forge" (ore feeding a
forge is the obvious, natural connection) rather than repointing any
existing exit - this is new content, not a retrofit of an
already-built connection, so it doesn't need that pattern (see
CLAUDE.md's Pantheon retrofit entry for when that pattern DOES apply).

Deliberately safe: no hostile NPCs, no encounters, nothing that could
expose a pacifist (world/pacifism.py) to combat just for walking in to
gather - the same standard the wilderness's own timber-gathering
tiles already meet.

Run once via `evennia shell < world/setup_ore_vein_shaft_live.py`. Not
idempotent - re-running duplicates everything.
"""

from evennia.utils import search, create

anchors = search.search_object("The Smithy Forge", typeclass="typeclasses.rooms.Room")
if not anchors:
    raise SystemExit("ABORTED: could not find the real 'The Smithy Forge' room live.")
smithy = anchors[0]

entrance = create.create_object(
    "typeclasses.rooms.Room",
    key="A Narrow Mine Entrance",
    attributes=[
        (
            "desc",
            "A low, timber-braced opening cut into the hillside behind the "
            "Smithy, propped every few feet against collapse. Cool air and "
            "the smell of wet stone drift up from the dark below - someone "
            "clearly comes and goes here often enough to keep the way "
            "clear.",
        )
    ],
)

shaft = create.create_object(
    "typeclasses.rooms.Room",
    key="The Ore Vein Shaft",
    attributes=[
        (
            "desc",
            "The passage ends in a rough, low-ceilinged chamber where a "
            "vein of rust-streaked iron ore runs visibly through the rock "
            "wall, pale in the light of whatever you're carrying. Pick "
            "marks and a scattering of loose rubble show this vein gets "
            "worked, if never quite worked out.",
        ),
        ("gather_resource", "iron_ore"),
    ],
)

create.create_object("typeclasses.exits.Exit", key="down", location=smithy, destination=entrance)
create.create_object("typeclasses.exits.Exit", key="up", location=entrance, destination=smithy)
create.create_object("typeclasses.exits.Exit", key="in", location=entrance, destination=shaft, aliases=["shaft"])
create.create_object("typeclasses.exits.Exit", key="out", location=shaft, destination=entrance)

miner = create.create_object(
    "typeclasses.characters.Character",
    key="a weathered old miner",
    location=shaft,
    attributes=[
        (
            "desc",
            "Grey-bearded and permanently stooped, with iron dust worked so "
            "deep into his hands it's less a stain than a second skin. He "
            "watches you work the vein without much interest - he's seen "
            "plenty of hopeful strangers come through here before you.",
        )
    ],
)
miner.locks.add("puppet:false()")

print("Created the Ore Vein Shaft (2 rooms) off The Smithy Forge, with the gathering flag set.")
