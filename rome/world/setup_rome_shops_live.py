"""
One-time live setup for the Rome-proper shops: places each new
merchant NPC in its chosen room. Run once via
`evennia shell < world/setup_rome_shops_live.py` after deploying
world/economy.py and world/prototypes.py. Safe to re-run - each
placement is guarded by a typeclass check per room, matching
world/setup_factions_live.py's own idempotency pattern (this is also
what makes it safe to add a 7th entry, ForumTailor, later and re-run
the whole script - the first six are just skipped as already present).

Room choices and why:
  - SuburaApothecary -> Market Row - Back Stalls (Subura) - already
    the Subura's own market district, empty of any NPC.
  - SuburaProvisioner -> Market Row - The Stalls (Subura) - the
    Subura's own docstring flagged "a real budget shop here is a good,
    contained follow-up" when the district was first built; this is
    that follow-up.
  - BathsOilVendor -> The Baths - Apodyterium - the actual changing
    room a bather passes through first, before the palaestra/
    frigidarium/tepidarium/caldarium sequence.
  - ForumScribe -> Scribes and Notaries for Hire - that room's own
    description already says scribes work there ("a row of small
    writing desks, each manned by a scribe available for hire"), but
    no actual NPC was ever placed - this fills a real, pre-existing
    gap rather than inventing a new room.
  - ForumWineMerchant -> The Merchants' Fountain Plaza - central,
    empty, and part of the Forum's own commercial district.
  - LudusOutfitter -> Ludus Entrance - already the game's own combat-
    gear commerce hub (the weaponsmith, both spell/skill trainers, the
    pet trainer all stand here already); "near the Ludus" as
    originally proposed literally means this room.
  - ForumTailor -> Cloth Merchants and Tailors - same "room's own
    description already implies this NPC, but none was ever placed"
    gap as ForumScribe ("a tailor measures a customer with practiced,
    rapid efficiency" - world/batch_forum_data.py). Added later, once
    a pacifist needed somewhere to actually buy cosmetic-only clothing
    after real body armor/shields were closed off to them.
"""

from evennia.utils import search, create

from world.economy import (
    SuburaApothecary,
    SuburaProvisioner,
    BathsOilVendor,
    ForumScribe,
    ForumWineMerchant,
    LudusOutfitter,
    ForumTailor,
)

SHOP_PLACEMENTS = [
    (
        SuburaApothecary, "Market Row - Back Stalls", "Aviola the herbalist",
        "A wiry old woman with stained fingers and a sharper eye for a "
        "wound than any physician twice her price - her stall is just a "
        "plank across two barrels, bundles of dried herbs hanging above it.",
    ),
    (
        SuburaProvisioner, "Market Row - The Stalls", "Rufa the baker",
        "Flour dusts her arms to the elbow and never quite washes off. "
        "Her stall smells like the one good thing in this whole market - "
        "warm bread, meat pies, and a wheel of cheese cut fresh to order.",
    ),
    (
        BathsOilVendor, "The Baths - Apodyterium", "Nikias the oil-seller",
        "A small, precise Greek freedman with a table of flasks and jars "
        "arranged with real care - oils, soap, balm, and a rack of bronze "
        "strigils polished bright enough to double as a mirror.",
    ),
    (
        ForumScribe, "Scribes and Notaries for Hire", "Pollio the scribe",
        "Ink-stained to the wrist, hunched over his writing desk with the "
        "posture of a man who has spent decades at it. Beside the letters "
        "and contracts he drafts for hire, a few of his own wares sit in "
        "a neat row - ink, sealed scrolls, and a tonic he swears by.",
    ),
    (
        ForumWineMerchant, "The Merchants' Fountain Plaza", "Vinicius the wine merchant",
        "A stout, red-faced man standing over a cart of amphorae, cups, "
        "and skeins, calling out vintages to anyone who slows down near "
        "his stall.",
    ),
    (
        LudusOutfitter, "Ludus Entrance", "Old Ennius the outfitter",
        "A grizzled former gladiator who never quite left the Ludus, now "
        "running a stall of the practical things a fighter actually "
        "needs before a real fight - medical kits, potions, and a few "
        "things meant to be thrown at someone else.",
    ),
    (
        ForumTailor, "Cloth Merchants and Tailors", "Vibia the tailor",
        "Quick, precise hands and a mouth full of pins, taking a "
        "customer's measure without ever seeming to slow down. Bolts "
        "of plain, undyed cloth are stacked behind her - nothing "
        "fancy, but always ready to be cut and stitched on the spot.",
    ),
]

for typeclass, room_name, npc_name, desc in SHOP_PLACEMENTS:
    rooms = search.search_object(room_name, typeclass="typeclasses.rooms.Room")
    if not rooms:
        print("SKIPPED %s - room '%s' not found" % (npc_name, room_name))
        continue
    room = rooms[0]

    existing = [obj for obj in room.contents if obj.is_typeclass(typeclass, exact=False)]
    if existing:
        print("SKIPPED %s - a %s is already present in %s" % (
            npc_name, typeclass.__name__, room_name
        ))
        continue

    npc = create.create_object(typeclass, key=npc_name, location=room)
    npc.db.desc = desc
    npc.locks.add("get:false()")
    print("Placed %s (%s) in %s, stocking %d items" % (
        npc_name, typeclass.__name__, room_name, len(npc.contents)
    ))
