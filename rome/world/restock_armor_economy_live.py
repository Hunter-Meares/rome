"""
One-off live script: restocks the already-spawned Germanic weaponsmith
and Smith's Quarter armorer with their new shield/accessory entries
(world/economy.py's own GERMANIA_WEAPONSMITH_STOCK/AMBER_COAST_ARMORY_
STOCK additions, Sep 30's armor-economy expansion) - these were appended
to each shop's own STOCK constant AFTER both NPCs were already spawned
live, so at_object_creation (which only ever runs once, at creation -
see gotcha #20 in CLAUDE.md) never picked them up.

Run via `evennia shell < world/restock_armor_economy_live.py`, any time
after deploying world/economy.py and world/prototypes.py. Not
idempotent - re-running would add a second copy of each new item, same
caveat as world/setup_sewers_live.py's own one-time population.

The new Rome Armorer herself is a brand-new NPC, not a restock of an
existing one - see world/setup_rome_shops_live.py (already extended
with her own placement entry) for that half of this expansion.
"""

from evennia.utils import search

from world.economy import _stock_merchant

GERMANIA_NEW_STOCK = [
    ("GERMANIA_ROUNDSHIELD_NOVICE", 25),
    ("GERMANIA_ROUNDSHIELD_VETERAN", 35),
    ("GERMANIA_ROUNDSHIELD_CHAMPION", 45),
    ("GERMANIA_ARMORER_HELM", 50),
    ("GERMANIA_ARMORER_VAMBRACES", 50),
    ("GERMANIA_ARMORER_GAUNTLETS", 50),
    ("GERMANIA_ARMORER_GREAVES", 50),
    ("GERMANIA_ARMORER_BOOTS", 50),
]

AMBER_NEW_STOCK = [
    ("AC_SMITH_WAVEGUARD_NOVICE", 46),
    ("AC_SMITH_WAVEGUARD_VETERAN", 58),
    ("AC_SMITH_WAVEGUARD_CHAMPION", 70),
    ("AMBER_ARMORER_HELM", 50),
    ("AMBER_ARMORER_VAMBRACES", 50),
    ("AMBER_ARMORER_GAUNTLETS", 50),
    ("AMBER_ARMORER_GREAVES", 50),
    ("AMBER_ARMORER_BOOTS", 50),
]

germanic = search.search_object("a Germanic weaponsmith", typeclass="world.economy.GermanicWeaponsmith")
if germanic:
    _stock_merchant(germanic[0], GERMANIA_NEW_STOCK)
    print("Restocked %s with %d new items (now %d total)." % (
        germanic[0].key, len(GERMANIA_NEW_STOCK), len(germanic[0].contents)
    ))
else:
    print("ERROR: 'a Germanic weaponsmith' not found live - is Germania built yet?")

amber = search.search_object("a Smith's Quarter armorer", typeclass="world.economy.AmberCoastArmorer")
if amber:
    _stock_merchant(amber[0], AMBER_NEW_STOCK)
    print("Restocked %s with %d new items (now %d total)." % (
        amber[0].key, len(AMBER_NEW_STOCK), len(amber[0].contents)
    ))
else:
    print("ERROR: 'a Smith's Quarter armorer' not found live - is the Amber Coast built yet?")
