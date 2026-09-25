"""
One-time live repair: turn the Colosseum's wandering hawker into a real
merchant.

A real player report (Sep 18): "the room with the Colosseum vendor has
no shop when using shop command." Confirmed live - "a Colosseum vendor"
(wanders between the Atrium of the Games and Beneath the Stands) was a
plain typeclasses.characters.Character with no shopname and no wares at
all, even though world/prototypes.py's COLOSSEUM_VENDOR prototype
specifies world.economy.NPCMerchant and stocks (VENDOR_NUTS,
VENDOR_WATERED_WINE). `shop` looks for an NPCMerchant in the room, so
it correctly found nothing.

Repairs the existing object in place (swap_typeclass, no attributes
cleaned) rather than deleting/recreating it, so it keeps its
wandering_npc script and beat. Safe to re-run: the swap is a no-op once
done, and wares are only added if the vendor is holding none.

Run once via `evennia shell < world/repair_colosseum_vendor_live.py`,
then `evennia reload` so the live server drops its cached copy of the
old typeclass (CLAUDE.md gotcha #16).
"""

from evennia.objects.models import ObjectDB
from evennia.prototypes.spawner import spawn

vendors = ObjectDB.objects.filter(db_key="a Colosseum vendor")
if vendors.count() != 1:
    raise SystemExit("ABORTED: expected exactly one 'a Colosseum vendor', found %d." % vendors.count())
vendor = vendors[0]

if vendor.db_typeclass_path != "world.economy.NPCMerchant":
    vendor.swap_typeclass("world.economy.NPCMerchant", clean_attributes=False)
    vendor = ObjectDB.objects.get(id=vendor.id)

vendor.db.shopname = "the vendor's tray"
vendor.db.distance_bonus = vendor.db.distance_bonus or 1.0

if not vendor.contents:
    for proto in ("VENDOR_NUTS", "VENDOR_WATERED_WINE"):
        spawn(proto)[0].move_to(vendor, quiet=True)

print(
    "Colosseum vendor is now %s in %s, selling: %s (scripts kept: %s)"
    % (
        vendor.db_typeclass_path,
        vendor.location,
        [(w.key, w.db.price) for w in vendor.contents],
        [s.key for s in vendor.scripts.all()],
    )
)
