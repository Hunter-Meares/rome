"""
One-time live repair: bring every ALREADY-EXISTING food and drink item in line
with its prototype's `consume_verb` / `consume_restore` / effect setup.

world/prototypes.py's food prototypes carry `consume_verb` ("eat"/"drink") -
which routes them to world/food.py's eat/drink commands instead of `use` - and
`consume_restore` (what HP/MP/SP they restore); the formerly `item_func:
"heal"` foods had that heal converted into `consume_restore`. But a prototype
change only reaches items spawned AFTER it (CLAUDE.md gotcha #20), so every
existing copy (each shop's own display item, and any a player already bought)
still has the old attributes. This walks every object tagged as spawned from a
consume_verb prototype and syncs it.

The synced attributes are set to the prototype's value, or REMOVED if the
prototype no longer has them (so a converted food loses its old heal
item_func). `item_uses` is only filled in if missing, so a partly-drunk
amphora keeps its remaining servings. Safe to re-run.

Run once via `evennia shell < world/repair_food_flags_live.py`, then
`evennia reload` (the running server may have some of these objects cached -
gotcha #16).
"""

from evennia.objects.models import ObjectDB
from evennia.prototypes.spawner import PROTOTYPE_TAG_CATEGORY

import world.prototypes as prototypes

SYNCED = ("consume_verb", "consume_restore", "item_func", "item_kwargs", "item_consumable")

total = fixed = 0
for name, proto in sorted(vars(prototypes).items()):
    if not (isinstance(proto, dict) and proto.get("consume_verb")):
        continue
    objs = ObjectDB.objects.filter(
        db_tags__db_key=name.lower(), db_tags__db_category=PROTOTYPE_TAG_CATEGORY
    ).distinct()
    changed = 0
    for obj in objs:
        total += 1
        touched = False
        for attr in SYNCED:
            if attr in proto:
                if obj.attributes.get(attr) != proto[attr]:
                    obj.attributes.add(attr, proto[attr])
                    touched = True
            elif obj.attributes.has(attr):
                obj.attributes.remove(attr)
                touched = True
        if "item_uses" in proto and not obj.attributes.has("item_uses"):
            obj.attributes.add("item_uses", proto["item_uses"])
            touched = True
        if touched:
            changed += 1
            fixed += 1
    print("%-28s %d object(s), %d updated" % (name, objs.count(), changed))

print("Done: %d food/drink objects checked, %d updated." % (total, fixed))
