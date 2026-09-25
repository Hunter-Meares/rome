"""
One-time live repair: give every ALREADY-EXISTING food and drink item its
`consume_verb` (and, for the four items that used to be pure flavor, their
new small effect).

world/prototypes.py's food prototypes now carry `consume_verb` ("eat" /
"drink"), which routes them to world/food.py's eat/drink commands instead of
`use` - but a prototype change only reaches items spawned AFTER it
(CLAUDE.md gotcha #20). Every loaf, cheese and cup of wine a player already
bought, and every shop's own display copy, still has the old attributes and
would keep answering "not a usable item" to `use` while `eat` refused it as
"not something you eat". This walks every object tagged as spawned from a
consume_verb prototype and fills in whatever it is missing.

Only fills in attributes the object does NOT already have, so a partly-
drunk amphora keeps its remaining uses. Safe to re-run.

Run once via `evennia shell < world/repair_food_flags_live.py`, then
`evennia reload` (the running server may have some of these objects cached -
gotcha #16).
"""

from evennia.objects.models import ObjectDB
from evennia.prototypes.spawner import PROTOTYPE_TAG_CATEGORY

import world.prototypes as prototypes

ATTRS = ("consume_verb", "item_func", "item_uses", "item_consumable", "item_kwargs")

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
        for attr in ATTRS:
            if attr in proto and not obj.attributes.has(attr):
                obj.attributes.add(attr, proto[attr])
                touched = True
        if touched:
            changed += 1
            fixed += 1
    print("%-28s %d object(s), %d updated" % (name, objs.count(), changed))

print("Done: %d food/drink objects checked, %d updated." % (total, fixed))
