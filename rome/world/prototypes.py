"""
Prototypes

A prototype is a simple way to create individualized instances of a
given typeclass. It is dictionary with specific key names.

For example, you might have a Sword typeclass that implements everything a
Sword would need to do. The only difference between different individual Swords
would be their key, description and some Attributes. The Prototype system
allows to create a range of such Swords with only minor variations. Prototypes
can also inherit and combine together to form entire hierarchies (such as
giving all Sabres and all Broadswords some common properties). Note that bigger
variations, such as custom commands or functionality belong in a hierarchy of
typeclasses instead.

A prototype can either be a dictionary placed into a global variable in a
python module (a 'module-prototype') or stored in the database as a dict on a
special Script (a db-prototype). The former can be created just by adding dicts
to modules Evennia looks at for prototypes, the latter is easiest created
in-game via the `olc` command/menu.

Prototypes are read and used to create new objects with the `spawn` command
or directly via `evennia.spawn` or the full path `evennia.prototypes.spawner.spawn`.

A prototype dictionary have the following keywords:

Possible keywords are:
- `prototype_key` - the name of the prototype. This is required for db-prototypes,
  for module-prototypes, the global variable name of the dict is used instead
- `prototype_parent` - string pointing to parent prototype if any. Prototype inherits
  in a similar way as classes, with children overriding values in their parents.
- `key` - string, the main object identifier.
- `typeclass` - string, if not set, will use `settings.BASE_OBJECT_TYPECLASS`.
- `location` - this should be a valid object or #dbref.
- `home` - valid object or #dbref.
- `destination` - only valid for exits (object or #dbref).
- `permissions` - string or list of permission strings.
- `locks` - a lock-string to use for the spawned object.
- `aliases` - string or list of strings.
- `attrs` - Attributes, expressed as a list of tuples on the form `(attrname, value)`,
  `(attrname, value, category)`, or `(attrname, value, category, locks)`. If using one
   of the shorter forms, defaults are used for the rest.
- `tags` - Tags, as a list of tuples `(tag,)`, `(tag, category)` or `(tag, category, data)`.
-  Any other keywords are interpreted as Attributes with no category or lock.
   These will internally be added to `attrs` (equivalent to `(attrname, value)`.

See the `spawn` command and `evennia.prototypes.spawner.spawn` for more info.
"""

## example of module-based prototypes using
## the variable name as `prototype_key` and
## simple Attributes
# from random import randint
#
# GOBLIN = {
# "key": "goblin grunt",
# "health": lambda: randint(20,30),
# "resists": ["cold", "poison"],
# "attacks": ["fists"],
# "weaknesses": ["fire", "light"],
# "tags": = [("greenskin", "monster"), ("humanoid", "monster")]
# }
#
# GOBLIN_WIZARD = {
# "prototype_parent": "GOBLIN",
# "key": "goblin wizard",
# "spells": ["fire ball", "lighting bolt"]
# }
#
# GOBLIN_ARCHER = {
# "prototype_parent": "GOBLIN",
# "key": "goblin archer",
# "attacks": ["short bow"]
# }
#
# This is an example of a prototype without a prototype
# (nor key) of its own, so it should normally only be
# used as a mix-in, as in the example of the goblin
# archwizard below.
# ARCHWIZARD_MIXIN = {
# "attacks": ["archwizard staff"],
# "spells": ["greater fire ball", "greater lighting"]
# }
#
# GOBLIN_ARCHWIZARD = {
# "key": "goblin archwizard",
# "prototype_parent" : ("GOBLIN_WIZARD", "ARCHWIZARD_MIXIN")
# }

ARGUS_NPC = {
    "key": "Argus",
    "aliases": ["argus", "guardian"],
    "typeclass": "evennia.objects.objects.DefaultCharacter",
    "desc": (
        "|wArgus Panoptes|n stands motionless beside the throne, a giant "
        "whose skin is covered, head to foot, in a hundred unblinking eyes. "
        "Some gaze at the door, others at the ceiling, others seemingly at "
        "nothing at all - and yet you have the distinct, uncomfortable "
        "sense that every single one of them is, in some sense, watching "
        "you. Hera set him here long ago, and not even death has managed "
        "to make him leave his post. |yNo one enters this chamber unseen.|n"
    ),
    "locks": "puppet:false()",
}



"""
----------------------------------------------------------------------------
COMBAT PROTOTYPES
----------------------------------------------------------------------------
Weapons, armor, and usable items for the combat system in world/combat.py.
Spawn these by name, e.g.:

    py from evennia.prototypes.spawner import spawn; spawn("DAGGER", location=self)

Remember spawn()'s location kwarg doesn't always reliably place the object -
if it doesn't show up where expected, find it with a global search and move
it with obj.move_to(location, quiet=True).
"""

BASEWEAPON = {"typeclass": "world.combat.CombatWeapon"}

BASEARMOR = {"typeclass": "world.combat.CombatArmor"}

DAGGER = {
    "prototype_parent": "BASEWEAPON",
    "price": 25,
    "damage_range": (10, 20),
    "accuracy_bonus": 30,
    "key": "a thin steel dagger",
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}

BROADSWORD = {
    "prototype_parent": "BASEWEAPON",
    "price": 50,
    "damage_range": (15, 30),
    "accuracy_bonus": 15,
    "key": "an iron broadsword",
    "weapon_type_name": "broadsword",
    "weapon_category": "heavy_blade",
    "two_handed": False,
}

GREATSWORD = {
    "prototype_parent": "BASEWEAPON",
    "price": 80,
    "damage_range": (20, 40),
    "accuracy_bonus": 0,
    "key": "a rune-etched greatsword",
    "weapon_type_name": "greatsword",
    "weapon_category": "heavy_blade",
    "two_handed": True,
}

GLADIUS = {
    "prototype_parent": "BASEWEAPON",
    "price": 35,
    "damage_range": (12, 24),
    "accuracy_bonus": 20,
    "key": "a Roman gladius",
    "weapon_type_name": "gladius",
    "weapon_category": "light_blade",
    "two_handed": False,
}

SPEAR = {
    "prototype_parent": "BASEWEAPON",
    "price": 55,
    "damage_range": (16, 28),
    "accuracy_bonus": 10,
    "key": "a bronze-tipped spear",
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}

TRIDENT = {
    "prototype_parent": "BASEWEAPON",
    "price": 65,
    "damage_range": (18, 30),
    "accuracy_bonus": 5,
    "key": "a gladiator's trident",
    "weapon_type_name": "trident",
    "weapon_category": "polearm",
    "two_handed": True,
}

JAVELIN = {
    "prototype_parent": "BASEWEAPON",
    "price": 40,
    "damage_range": (14, 26),
    "accuracy_bonus": 15,
    "key": "a hunting javelin",
    "weapon_type_name": "javelin",
    "weapon_category": "ranged",
    "two_handed": False,
}

SHORTBOW = {
    "prototype_parent": "BASEWEAPON",
    "price": 45,
    "damage_range": (12, 22),
    "accuracy_bonus": 20,
    "key": "a curved shortbow",
    "weapon_type_name": "shortbow",
    "weapon_category": "ranged",
    "two_handed": True,
}

WARAXE = {
    "prototype_parent": "BASEWEAPON",
    "price": 90,
    "damage_range": (25, 45),
    "accuracy_bonus": -10,
    "key": "a heavy two-handed waraxe",
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}

RITUAL_STAFF = {
    "prototype_parent": "BASEWEAPON",
    "price": 45,
    "damage_range": (6, 14),
    "accuracy_bonus": 25,
    "key": "a carved ritual staff",
    "weapon_type_name": "ritual staff",
    "weapon_category": "staff",
    "two_handed": True,
}

LEATHERARMOR = {
    "prototype_parent": "BASEARMOR",
    "price": 30,
    "damage_reduction": 2,
    "defense_modifier": -2,
    "armor_category": "light",
    "key": "a suit of leather armor",
}

SCALEMAIL = {
    "prototype_parent": "BASEARMOR",
    "price": 60,
    "damage_reduction": 4,
    "defense_modifier": -4,
    "armor_category": "medium",
    "key": "a suit of scale mail",
}

PLATEMAIL = {
    "prototype_parent": "BASEARMOR",
    "price": 100,
    "damage_reduction": 6,
    "defense_modifier": -6,
    "armor_category": "heavy",
    "key": "a suit of plate mail",
}

# ----------------------------------------------------------------------------
# ADDITIONAL EQUIPMENT SLOTS - shields and accessory armor (head/arms/hands/
# legs/feet). Shields contribute defense_modifier only, same as body armor's
# dodge side but never its damage_reduction side - see the design discussion
# this came from for why (a shield helps you avoid a hit landing at all;
# body armor softens the ones that do land - two different jobs, so they
# don't stack the same number twice). Accessory armor contributes flat
# stat_bonuses/resource_bonuses only, applied directly to the wearer on
# don/doff (world/combat.py) - it's never read by the combat damage/defense
# formulas at all, unlike body armor and shields.
#
# Shields carry armor_category (light/medium/heavy) same as body armor, so
# CLASS_ARMOR_PROFICIENCIES (world/combat.py) can gate both the same way.
# Accessory pieces don't - see is_armor_proficient's docstring for why a
# penalty wouldn't have anything to meaningfully bite into on a pure
# stat-bonus item the way it does on damage_reduction/defense_modifier.
# ----------------------------------------------------------------------------

PARMA = {
    "prototype_parent": "BASEARMOR",
    "price": 20,
    "damage_reduction": 0,
    "defense_modifier": 4,
    "armor_slot": "shield",
    "armor_category": "light",
    "key": "a small round parma shield",
}

CLIPEUS = {
    "prototype_parent": "BASEARMOR",
    "price": 45,
    "damage_reduction": 0,
    "defense_modifier": 7,
    "armor_slot": "shield",
    "armor_category": "medium",
    "key": "a bronze-faced clipeus",
}

SCUTUM = {
    "prototype_parent": "BASEARMOR",
    "price": 80,
    "damage_reduction": 0,
    "defense_modifier": 12,
    "armor_slot": "shield",
    "armor_category": "heavy",
    "key": "a curved legionary scutum",
}

# --- Head ---

PILEUS = {
    "prototype_parent": "BASEARMOR",
    "price": 15,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "head",
    "resource_bonuses": {"max_mp": 5},
    "key": "a simple felt pileus cap",
}

GALEA = {
    "prototype_parent": "BASEARMOR",
    "price": 35,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "head",
    "resource_bonuses": {"max_hp": 10},
    "key": "a bronze galea helmet",
}

CASSIS = {
    "prototype_parent": "BASEARMOR",
    "price": 55,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "head",
    "resource_bonuses": {"max_hp": 20},
    "key": "a plumed iron cassis helm",
}

# --- Arms ---

FASCIA_BRACHII = {
    "prototype_parent": "BASEARMOR",
    "price": 15,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "arms",
    "resource_bonuses": {"max_sp": 5},
    "key": "a pair of simple fascia brachii wraps",
}

MANICA = {
    "prototype_parent": "BASEARMOR",
    "price": 30,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "arms",
    "stat_bonuses": {"virtus": 1},
    "key": "a segmented manica arm-guard",
}

BRACHIALE = {
    "prototype_parent": "BASEARMOR",
    "price": 50,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "arms",
    "stat_bonuses": {"virtus": 2},
    "key": "a reinforced iron brachiale vambrace",
}

# --- Hands ---

CHIROTHECAE = {
    "prototype_parent": "BASEARMOR",
    "price": 15,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "hands",
    "resource_bonuses": {"max_mp": 5},
    "key": "a pair of simple chirothecae gloves",
}

FASCIA_MANUS = {
    "prototype_parent": "BASEARMOR",
    "price": 20,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "hands",
    "stat_bonuses": {"agilitas": 1},
    "key": "a pair of wrapped fascia manus",
}

MANICA_FERRATA = {
    "prototype_parent": "BASEARMOR",
    "price": 50,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "hands",
    "stat_bonuses": {"agilitas": 2},
    "key": "a pair of iron-plated manica ferrata gauntlets",
}

# --- Legs ---

FEMINALIA = {
    "prototype_parent": "BASEARMOR",
    "price": 15,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "legs",
    "resource_bonuses": {"max_sp": 5},
    "key": "a pair of simple feminalia leg-wraps",
}

OCREA = {
    "prototype_parent": "BASEARMOR",
    "price": 30,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "legs",
    "resource_bonuses": {"max_sp": 10},
    "key": "a pair of bronze ocrea greaves",
}

OCREA_FERRATA = {
    "prototype_parent": "BASEARMOR",
    "price": 50,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "legs",
    "resource_bonuses": {"max_sp": 20},
    "key": "a pair of iron-banded ocrea ferrata greaves",
}

# --- Feet ---

SOLEAE = {
    "prototype_parent": "BASEARMOR",
    "price": 15,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "feet",
    "resource_bonuses": {"max_hp": 5},
    "key": "a pair of simple leather soleae sandals",
}

CALIGAE = {
    "prototype_parent": "BASEARMOR",
    "price": 25,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "feet",
    "stat_bonuses": {"vigor": 1},
    "key": "a pair of studded caligae boots",
}

CALIGAE_FERRATAE = {
    "prototype_parent": "BASEARMOR",
    "price": 50,
    "damage_reduction": 0,
    "defense_modifier": 0,
    "armor_slot": "feet",
    "stat_bonuses": {"vigor": 2},
    "key": "a pair of hobnailed caligae ferratae boots",
}

# ----------------------------------------------------------------------------
# UNIQUE / DIVINE ITEMS - one-of-a-kind gear for specific god characters, not
# meant to be sold, found, or spawned in numbers. Deliberately break the
# usual armor tradeoff every mortal-tier armor above follows (heavier
# protection costs defense_modifier, trading dodge for damage reduction) -
# a god's own gear has no such cost. get:false() locks these to whoever
# they're equipped on; a true superuser bypasses that lock same as any
# other, so this only ever stops another player from taking it, never the
# god wearing it.
# ----------------------------------------------------------------------------

THUNDERBOLT_OF_JUPITER = {
    "prototype_parent": "BASEWEAPON",
    "key": "|Y|hthe Thunderbolt of Jupiter|n",
    "desc": (
        "|YA jagged spear of pure lightning|n, caught and bound into a shape "
        "a hand could hold - the air around it never quite stops crackling, "
        "and the faint smell of ozone follows it everywhere it moves. "
        "|wForged in no earthly forge|n, it does not so much strike a target "
        "as simply arrive there, the distance between wielder and target "
        "briefly ceasing to be a meaningful thing. |cLegend holds this is "
        "the very bolt that split the sky the day the Titans fell.|n"
    ),
    "weapon_type_name": "thunderbolt",
    "weapon_category": "polearm",
    "damage_range": (80, 150),
    "accuracy_bonus": 75,
    "two_handed": True,
    "locks": "get:false()",
}

AEGIS_OF_OLYMPUS = {
    "prototype_parent": "BASEARMOR",
    "key": "|Y|hthe Aegis of Olympus|n",
    "desc": (
        "|YA breastplate of hammered gold and storm-cloud grey|n, its "
        "surface shifting faintly like weather seen from a great height. "
        "|wLightning traces itself across the metal|n in slow, deliberate "
        "arcs, there and gone before the eye can follow. |cNo blade forged "
        "by mortal or god has ever left a mark on it.|n"
    ),
    "damage_reduction": 40,
    "defense_modifier": 30,
    "locks": "get:false()",
}

# Jupiter's remaining divine gear (head/arms/hands/legs/feet) - no shield;
# the Thunderbolt is deliberately two-handed, and CLASS_ARMOR_PROFICIENCIES
# aside, the same two-handed/shield exclusivity every mortal lives under
# applies to him too. One piece per core stat plus a resource-boosting
# pair of sandals, mirroring the mortal accessory pattern (one bonus type
# per piece) at a scale nothing mortal could ever wear.

DIADEM_OF_THE_SKY_FATHER = {
    "prototype_parent": "BASEARMOR",
    "key": "|Y|hthe Diadem of the Sky-Father|n",
    "desc": (
        "|YA circlet of hammered starlight|n, too bright to look at directly "
        "and yet somehow never blinding. |wSeven points crown it|n, said to "
        "mark the seven winds that answer to no one but him. |cWhen he "
        "turns his head, the stars themselves seem to lean in to listen.|n"
    ),
    "armor_slot": "head",
    "damage_reduction": 0,
    "defense_modifier": 0,
    "stat_bonuses": {"ingenium": 5},
    "locks": "get:false()",
}

STORMBOUND_VAMBRACES = {
    "prototype_parent": "BASEARMOR",
    "key": "|Y|hthe Stormbound Vambraces|n",
    "desc": (
        "|YForearm-guards of black storm-iron|n, veined through with the "
        "same restless lightning that runs the length of the Thunderbolt "
        "itself. |wThey hum faintly against the skin|n, as though bracing "
        "for a blow that never quite arrives. |cNo mortal smith has ever "
        "seen metal like this, let alone shaped it.|n"
    ),
    "armor_slot": "arms",
    "damage_reduction": 0,
    "defense_modifier": 0,
    "stat_bonuses": {"virtus": 5},
    "locks": "get:false()",
}

GAUNTLETS_OF_THE_THUNDERER = {
    "prototype_parent": "BASEARMOR",
    "key": "|Y|hthe Gauntlets of the Thunderer|n",
    "desc": (
        "|YGauntlets of gold-shot storm-cloud grey|n, each knuckle set "
        "with a single unblinking spark of captured lightning. |wThe grip "
        "never slips, the aim never wavers|n - these are the hands that "
        "have hurled ten thousand years of thunderbolts and never once "
        "missed. |cThey close around the Thunderbolt's haft like they "
        "were forged for no other purpose.|n"
    ),
    "armor_slot": "hands",
    "damage_reduction": 0,
    "defense_modifier": 0,
    "stat_bonuses": {"agilitas": 5},
    "locks": "get:false()",
}

GREAVES_OF_OLYMPUS = {
    "prototype_parent": "BASEARMOR",
    "key": "|Y|hthe Greaves of Olympus|n",
    "desc": (
        "|YGreaves of white-gold and storm-grey|n, engraved with the "
        "unbroken line of a mountain's silhouette against the sky. "
        "|wThey do not so much protect the legs beneath them as remind "
        "the wearer they are standing on the highest peak there is.|n "
        "|cOlympus itself is said to have lent them its own foundations.|n"
    ),
    "armor_slot": "legs",
    "damage_reduction": 0,
    "defense_modifier": 0,
    "stat_bonuses": {"vigor": 5},
    "locks": "get:false()",
}

STORM_TREADS_OF_JUPITER = {
    "prototype_parent": "BASEARMOR",
    "key": "|Y|hthe Storm-Treads of Jupiter|n",
    "desc": (
        "|YSandals woven from storm-cloud and gold thread|n, leaving no "
        "footprint on any surface they touch - cloud, marble, or the bare "
        "air itself. |wEach step arrives before the sound of it does|n, "
        "the way thunder always seems to lag a moment behind the flash "
        "that made it. |cWherever he walks, the sky over that place "
        "remembers it for a long time after.|n"
    ),
    "armor_slot": "feet",
    "damage_reduction": 0,
    "defense_modifier": 0,
    "resource_bonuses": {"max_hp": 200, "max_mp": 200, "max_sp": 200},
    "locks": "get:false()",
}

MEDKIT = {
    "key": "a medical kit",
    "aliases": ["medkit"],
    "desc": "A standard medical kit. It can be used a few times to heal wounds.",
    "item_func": "heal",
    "item_uses": 3,
    "item_consumable": True,
    "item_kwargs": {"healing_range": (15, 25)},
}

GLASS_BOTTLE = {
    "key": "a glass bottle",
    "desc": "An empty glass bottle.",
    # No item_func of its own (it's leftover residue, not a usable
    # item), so it needs this explicit tag to be picked up by the
    # item-decay sweep (find_decayed_items, world/combat.py) the same
    # way real consumables are via their item_func.
    "junk_eligible": True,
}

HEALTH_POTION = {
    "key": "a health potion",
    "desc": "A glass bottle full of a mystical potion that heals wounds when used.",
    "item_func": "heal",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"healing_range": (35, 50)},
}

REGEN_POTION = {
    "key": "a regeneration potion",
    "desc": "A glass bottle full of a mystical potion that regenerates wounds over time.",
    "item_func": "add_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"conditions": [("Regeneration", 10)]},
}

HASTE_POTION = {
    "key": "a haste potion",
    "desc": "A glass bottle full of a mystical potion that hastens its user.",
    "item_func": "add_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"conditions": [("Haste", 10)]},
}

BOMB = {
    "key": "a rotund bomb",
    "desc": "A large black sphere with a fuse at the end. Can be used on enemies in combat.",
    "item_func": "attack",
    "item_uses": 1,
    "item_consumable": True,
    "item_kwargs": {"damage_range": (25, 40), "accuracy": 25},
}

POISON_DART = {
    "key": "a poison dart",
    "desc": "A thin dart coated in deadly poison. Can be used on enemies in combat",
    "item_func": "attack",
    "item_uses": 1,
    "item_consumable": True,
    "item_kwargs": {
        "damage_range": (5, 10),
        "accuracy": 25,
        "inflict_condition": [("Poisoned", 10)],
    },
}

ANTIDOTE_POTION = {
    "key": "an antidote potion",
    "desc": "A glass bottle full of a mystical potion that cures poison when used.",
    "item_func": "cure_condition",
    "item_uses": 1,
    "item_consumable": "GLASS_BOTTLE",
    "item_kwargs": {"to_cure": ["Poisoned"]},
}

"""
----------------------------------------------------------------------------
FORUM ROMANUM - COMMERCIAL DISTRICT WARES
----------------------------------------------------------------------------
Flavor/trade goods for the Forum's shopkeepers - plain sellable items,
no item_func, same pattern as the Colosseum vendor's snacks/cushions.
"""

SCROLL_OF_POETRY = {
    "key": "a scroll of poetry",
    "desc": "A tightly-rolled papyrus scroll, a well-known poet's verses copied in a careful, practiced hand.",
    "price": 15,
}

SCROLL_OF_HISTORY = {
    "key": "a scroll of history",
    "desc": "A dense historical account, copied and re-copied enough times that a few passages have drifted from the original.",
    "price": 20,
}

# A real request from live playtesting - the city's gotten big enough
# that a new player has no mental map of how it fits together. Stocked
# at the bookseller specifically since a bookseller plausibly sells
# maps, and Booksellers' Corner (off the Forum, the game's actual
# geographic and narrative hub) is about as central and easy to reach
# as a shop gets. Deliberately a high-level district overview, not
# turn-by-turn directions - those would go stale the moment a new
# zone gets built, the way exact directions never do for a real city
# map either.
MAP_OF_ROME = {
    "key": "a map of Rome",
    "desc": (
        "|YA Map of Rome|n\n\n"
        "Unrolled, it shows the city's major districts in a clean, "
        "practiced hand - not turn-by-turn directions, just the shape "
        "of the place.\n\n"
        "|cThe Colosseum|n - a newcomer's first sight of the city: the "
        "holding cells, the Atrium of the Games, the Ludus training "
        "ground, and the deeper Arena Sands. A road east leads out "
        "through the city walls, toward Germania and the wider world.\n\n"
        "|cThe Forum Romanum|n - the true center of the city, and where "
        "most roads eventually lead. The Capitoline Hill rises beside "
        "it, home to the great state temples. The Argiletum leads north "
        "into the crowded Subura; the Market Stretch leads to Trajan's "
        "Market and the Library beyond it.\n\n"
        "|cThe Aventine and Palatine Hills|n - two of Rome's famous "
        "seven, both reached from the Forum's own southern approaches. "
        "The Palatine holds the Emperor's palace; the Aventine holds "
        "the old plebeian quarter and its own triad of gods.\n\n"
        "|cCampus Martius|n - the open muster ground north of the city "
        "proper, past the Mausoleum of Augustus and the walls "
        "themselves. The Pantheon and the Temple of Isis both stand "
        "along its roads.\n\n"
        "|cBeneath the city|n - the Cloaca Maxima, Rome's own sewers, "
        "run below everything, entered through grates near the Ludus, "
        "the Subura, and the Forum.\n\n"
        "A faded note in the margin adds: |xthe city keeps growing "
        "faster than any map can keep up with. Trust your own feet "
        "over this scroll if the two ever disagree.|n"
    ),
    "price": 25,
}

# Granted free to every new character at the end of chargen (see
# _apply_race_and_class, world/chargen_menu.py) - a direct response to
# two separate real new players both showing classic "where am I"
# behavior (repeatedly checking exits in every direction before
# committing to one). Deliberately its OWN prototype, not just handing
# out MAP_OF_ROME for free - the same nice, clean-hand shop map given
# away undercuts the reason anyone would ever spend the 25 gold on it.
# Same major-district information, cruder presentation - a fresh
# escapee from the Colosseum's cells wouldn't own a fine illustrated
# scroll anyway.
ROUGH_MAP_OF_ROME = {
    "key": "a rough sketch of Rome",
    "desc": (
        "|YA Rough Sketch of Rome|n\n\n"
        "Scratched onto a scrap of hide by someone who clearly wasn't a "
        "cartographer - crooked lines, a few words scrawled in charcoal "
        "over the shapes they're meant to label. Good enough to get a "
        "sense of the place, if not to be proud of.\n\n"
        "|cThe Colosseum|n - where you started: the holding cells, the "
        "Atrium of the Games, the Ludus, and the Arena Sands further "
        "in. A road east leads out through the walls entirely.\n\n"
        "|cThe Forum Romanum|n - the middle of everything, more or less "
        "where all the other lines on this sketch point back to. The "
        "Capitoline rises right beside it. A scratched arrow marked "
        "'Subura' points north; another marked 'market, library' points "
        "east.\n\n"
        "|cThe Aventine and Palatine Hills|n - both off the Forum's "
        "southern side. One word next to each: 'palace' for one hill, "
        "'temples' for the other, and the ink's too smudged to tell "
        "which word belongs to which anymore.\n\n"
        "|cCampus Martius|n - north past the walls, an open muster "
        "field with a few landmarks sketched along it.\n\n"
        "|cBelow all of it|n - a single scratched line simply reading "
        "'sewers - grates near Ludus, Subura, Forum.'\n\n"
        "Scrawled at the bottom, underlined twice: |xdon't trust this "
        "over your own two feet.|n"
    ),
    "price": 5,
}

GOLD_RING = {
    "key": "a gold ring",
    "desc": "A simple gold band, well-made but not showy - the kind of piece a citizen of modest means might actually afford.",
    "price": 60,
}

GOLD_BRACELET = {
    "key": "a gold bracelet",
    "desc": "A delicate gold bracelet, small links catching the light with every movement.",
    "price": 85,
}

VIAL_OF_PERFUME = {
    "key": "a vial of perfume",
    "desc": "A small glass vial of scented oil, the stopper sealed with a dab of wax.",
    "price": 25,
}

ROASTED_MEAT_SKEWER = {
    "key": "a roasted meat skewer",
    "desc": "A skewer of well-charred meat, still warm, sold fresh off the brazier.",
    "price": 4,
}

HONEYED_BREAD = {
    "key": "a piece of honeyed bread",
    "desc": "A dense little loaf, drizzled with honey until it's nearly too sticky to hold.",
    "price": 3,
}

# Trajan's Market wares - genuinely different from anything the Forum's
# own merchants sell, matching the market's real historical role as an
# import-heavy commercial hub rather than a reskin of existing goods.
SACK_OF_PEPPER = {
    "key": "a sack of Indian pepper",
    "desc": "A tightly-bound sack of dried peppercorns, carried the length of a trade route most people here couldn't point to on a map. Worth close to its weight in silver back where it started.",
    "price": 15,
}

JAR_OF_CINNAMON = {
    "key": "a jar of cinnamon bark",
    "desc": "Curled sticks of dried bark, packed into a sealed clay jar - the scent alone is enough to draw a crowd when the lid comes off.",
    "price": 12,
}

BUNDLE_OF_SAFFRON = {
    "key": "a bundle of saffron threads",
    "desc": "A small, carefully wrapped bundle of deep red-gold threads - by weight, one of the most expensive things sold anywhere in the market, and it isn't close.",
    "price": 30,
}

BOLT_OF_SILK = {
    "key": "a bolt of imported silk",
    "desc": "A full bolt of silk, impossibly smooth to the touch, carried overland from somewhere far past the empire's eastern edge. Half the price is the cloth; the other half is the distance it traveled.",
    "price": 50,
}

EMBROIDERED_SILK_SASH = {
    "key": "an embroidered silk sash",
    "desc": "A silk sash worked with fine embroidery, clearly meant for someone who wants their wealth noticed without having to say so.",
    "price": 35,
}

DYED_SILK_SCARF = {
    "key": "a dyed silk scarf",
    "desc": "A length of silk dyed a rich, even color no local wool ever quite manages - a small, wearable luxury.",
    "price": 20,
}


"""
----------------------------------------------------------------------------
COLOSSEUM NPCS
----------------------------------------------------------------------------
Non-combat flavor/guide NPCs use plain DefaultCharacter - no need for the
full CombatCharacter typeclass since they don't fight or cast. The Arena
Trainer DOES need hp/max_hp (set directly here) so it's a valid target for
the fight/attack commands in world/combat.py, and is tagged so
CombatRules.at_defeat() knows to grant freedom to whoever defeats it.
"""

OLD_MILO = {
    "key": "Old Milo",
    "typeclass": "evennia.objects.objects.DefaultCharacter",
    "desc": (
        "A wiry old man sits against the corridor wall, chains loose around "
        "wrists worn smooth by years of them. His eyes are sharp despite "
        "everything. He looks like he's seen a hundred new captives pass "
        "through here, and has advice for every one of them."
    ),
    "locks": "puppet:false()",
}

GUARD_TITUS = {
    "key": "Titus",
    "aliases": ["guard"],
    "typeclass": "evennia.objects.objects.DefaultCharacter",
    "desc": (
        "A broad-shouldered guard leans against the tunnel wall, spear "
        "resting loosely in one hand. He looks bored more than alert - "
        "which might just be your chance."
    ),
    "locks": "puppet:false()",
}

COLOSSEUM_HERALD = {
    "key": "the Colosseum Herald",
    "typeclass": "evennia.objects.objects.DefaultCharacter",
    "desc": (
        "Dressed in red and gold, the Herald stands ready to announce the "
        "day's games to anyone who'll listen, voice already hoarse from "
        "shouting over the crowd."
    ),
    "locks": "puppet:false()",
}

QUEST_CORRUPT_SCRIBE = {
    "key": "a nervous ballot-scribe",
    "aliases": ["scribe"],
    "typeclass": "world.combat.HostileNPC",
    "desc": (
        "A scribe who startles at every sound, a stack of visibly "
        "tampered vote tallies half-hidden under a bolt of cloth. "
        "Whatever he's been paid to falsify, he's clearly not cut out "
        "for what happens if he's actually caught doing it - see "
        "world/quests.py, the 'corrupt_official' quest's personal-"
        "instance spawn, not a persistent world NPC."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 3,
    "xp_reward": 40,
    "locks": "puppet:false()",
}

ARENA_TRAINER = {
    "key": "Rutilus the Trainer",
    "aliases": ["trainer", "rutilus"],
    "typeclass": "world.combat.HostileNPC",
    "desc": (
        "Scarred, sun-browned, and utterly calm, Rutilus has trained more "
        "gladiators than he can remember - and outlived most of them. He "
        "watches you with the flat, appraising look of a man deciding "
        "whether you're worth the effort."
    ),
    "player_class": "gladiator",
    "level": 1,
    "xp_reward": 25,
    "tags": [("colosseum_trainer", "npc_role")],
    "locks": "puppet:false()",
}

"""
----------------------------------------------------------------------------
ARENA FIGHTERS - the deeper Arena Sands, past the newbie escape questline
----------------------------------------------------------------------------
Real leveled opponents (up to 25), built with derive_npc_stats() in
world/combat.py so their HP/stats are honestly connected to the actual
leveling system - not hand-picked numbers with a "level" label pasted
on. Distinct from the Ludus trainers (which stay easy, teaching-focused
opponents) and from ARENA_TRAINER above (which exists purely to gate
the initial escape). These are genuine ongoing leveling content for
players who've already gotten out of the cells.

Persistent, respawning (world.combat.RespawningNPC) - one of each per
room, since these are meant to feel like real, individually meaningful
encounters rather than something to farm in bulk. respawn_delay scales
with tier: quick enough not to punish a low-level player still learning
the ropes, deliberately much longer for the Arena Master, an endgame
encounter that shouldn't feel readily available.
"""

"""
Deeper Sands rebalance: originally a levels 3-25 continuation
(newbie-adjacent, right after the Colosseum escape). Re-scoped by
direct request into genuine level 75+ endgame content instead - a
real reason for a mid/late-game character to come back to the
Colosseum, rather than something a level 6 character stumbles into on
the way to the Ludus (that's what the sewers are for now - see
DeeperSandsGateExit in world/colosseum.py). Same six-tier structure
and racial identities kept (recruit -> hunter -> brute -> duelist ->
champion -> master), just rescaled and re-armed - levels 75/82/88/93/
97/100 (the Arena Master capping out at the same level 100 "highest
rank a mortal can earn" the Legend achievement already uses),
xp_reward recomputed at the same ~6% of xp_for_level(level) ratio
every other real NPC in this game already lands on (confirmed against
the sewers' own deep-tier NPCs, not guessed).

These six are the one exception to "no NPC has an actually-equipped
wielded_weapon/worn_armor" (still true everywhere else, including the
Germanic warband fighters) - a direct follow-up request that their
gear be real, not just flavor text. See ARENA_FIGHTER_GEAR and
equip_arena_fighter() in world/combat.py (called once per fighter, at
creation) for the actual weapon/armor assignment matching each
fighter's own desc below, and ARENA_LOOT_* further down in this file
plus world/loot.py's roll_arena_loot_drop for what they drop on
defeat. The underlying toughness was always primarily from level
scaling (derive_npc_stats already scales HP/MP/SP and all four core
stats for real at these levels) - real gear stacks on top of that,
not instead of it.
"""

ARENA_FIGHTER_RECRUIT = {
    "key": "a hardened arena recruit",
    "aliases": ["recruit", "fighter"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Nothing recruit-like about him anymore despite the title - years "
        "on this exact sand have worn every wasted motion out of him. "
        "Scarred lorica segmentata, a gladius kept honed past regulation "
        "sharpness, and the flat, unhurried stare of someone who stopped "
        "being nervous a very long time ago."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 75,
    "xp_reward": 4383,
    "respawn_delay": 60,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

ARENA_FIGHTER_HUNTER = {
    "key": "a Centaur arena hunter",
    "aliases": ["hunter", "fighter", "centaur"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A Centaur fighter in banded barding that covers him from "
        "shoulder to flank, twin javelins slung across his back and a "
        "third already balanced in hand. He circles rather than charges - "
        "he has learned, the hard way, exactly how little he needs to."
    ),
    "race": "centaur",
    "player_class": "venator",
    "level": 82,
    "xp_reward": 5193,
    "respawn_delay": 90,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

ARENA_FIGHTER_BRUTE = {
    "key": "a Minotaur arena brute",
    "aliases": ["brute", "fighter", "minotaur"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A Minotaur in a mail hauberk stretched to its absolute limit "
        "across a chest built like a siege engine, a spiked maul resting "
        "on one shoulder as though it weighed nothing at all. Patient, in "
        "the specific way of something that has never once needed to "
        "rush and has the scars on other people to prove it."
    ),
    "race": "minotaur",
    "player_class": "barbarian",
    "level": 88,
    "xp_reward": 5939,
    "respawn_delay": 120,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

ARENA_FIGHTER_DUELIST = {
    "key": "a Harpy arena duelist",
    "aliases": ["duelist", "fighter", "harpy"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A Harpy duelist in a lacquered breastplate cut to leave her "
        "wings free, twin curved blades sheathed low across her hips. "
        "She watches for an opening with the unblinking patience of "
        "something that has fought - and won - more of these than "
        "she'll ever bother mentioning."
    ),
    "race": "harpy",
    "player_class": "gladiator",
    "level": 93,
    "xp_reward": 6596,
    "respawn_delay": 150,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

ARENA_FIGHTER_CHAMPION = {
    "key": "a Cyclops arena champion",
    "aliases": ["champion", "fighter", "cyclops"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A Cyclops in full legionary plate polished bright enough to "
        "throw back the torchlight, a massive scutum locked in close the "
        "way only someone who's actually survived a hundred real bouts "
        "holds one, and a spatha long enough that most opponents never "
        "close the distance it needs."
    ),
    "race": "cyclops",
    "player_class": "legionary",
    "level": 97,
    "xp_reward": 7146,
    "respawn_delay": 180,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

ARENA_FIGHTER_MASTER = {
    "key": "the Arena Master",
    "aliases": ["master", "fighter", "arena master"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Undefeated for longer than anyone keeping count can remember, "
        "armored in blackened plate that's clearly been fought in rather "
        "than just worn, a single massive war-hammer resting head-down in "
        "the sand at his feet. The Arena Master doesn't posture or warm "
        "up. He just waits - utterly still, utterly certain - for "
        "whoever's next foolish enough to try, at the very peak of what a "
        "mortal can become."
    ),
    "player_class": "gladiator",
    "level": 100,
    "xp_reward": 7571,
    "respawn_delay": 300,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

"""
----------------------------------------------------------------------------
ARENA FIGHTER LOOT - real drops on defeat (world/loot.py's
roll_arena_loot_drop), one weapon and one armor prototype per fighter,
matching that fighter's own equipped gear (see ARENA_FIGHTER_GEAR,
world/combat.py) rather than a shared random pool - each of the six
Arena Fighters is a distinct, named identity, not interchangeable
trash-mob population like the sewers, so a drop reads as "you took
this off the Brute specifically" rather than a generic arena reskin.
Deliberately their own named prototypes rather than the plain
GLADIUS/WARAXE/etc. base items (same reasoning as SEWER_LOOT_* -
see world/loot.py's own docstring) - price/damage_range/
damage_reduction/defense_modifier below are placeholders, overwritten
at spawn time by spawn_leveled_weapon/spawn_leveled_armor using the
defeated fighter's own level.
----------------------------------------------------------------------------
"""

ARENA_LOOT_RECRUIT_GLADIUS = {
    "prototype_parent": "BASEWEAPON",
    "price": 25,
    "damage_range": (10, 20),
    "accuracy_bonus": -5,
    "key": "the recruit's honed gladius",
    "desc": (
        "Kept past regulation sharpness for years on this exact sand - "
        "whoever carried this clearly never let its edge dull, no "
        "matter how the rest of him wore down."
    ),
    "weapon_type_name": "gladius",
    "weapon_category": "light_blade",
    "two_handed": False,
}

ARENA_LOOT_RECRUIT_ARMOR = {
    "prototype_parent": "BASEARMOR",
    "price": 30,
    "damage_reduction": 2,
    "defense_modifier": -2,
    "armor_category": "medium",
    "key": "scarred lorica segmentata",
    "desc": (
        "Banded plate scored with old strike-marks, every one of them "
        "a blow that didn't get through - proof this recruit earned "
        "his standing the hard way."
    ),
}

ARENA_LOOT_HUNTER_JAVELIN = {
    "prototype_parent": "BASEWEAPON",
    "price": 25,
    "damage_range": (12, 22),
    "accuracy_bonus": -3,
    "key": "the Centaur hunter's javelin",
    "desc": (
        "Balanced for a throw that never misses its window - the third "
        "of three the hunter always kept ready, and the only one that "
        "never actually left his hand."
    ),
    "weapon_type_name": "javelin",
    "weapon_category": "ranged",
    "two_handed": False,
}

ARENA_LOOT_HUNTER_ARMOR = {
    "prototype_parent": "BASEARMOR",
    "price": 30,
    "damage_reduction": 2,
    "defense_modifier": -2,
    "armor_category": "medium",
    "key": "Centaur banded barding",
    "desc": (
        "Fitted to cover shoulder to flank without ever slowing a "
        "circling stride - built for a fighter who wins by patience, "
        "not by standing still and trading blows."
    ),
}

ARENA_LOOT_BRUTE_WARAXE = {
    "prototype_parent": "BASEWEAPON",
    "price": 90,
    "damage_range": (25, 45),
    "accuracy_bonus": -10,
    "key": "the Minotaur brute's spiked maul",
    "desc": (
        "Heavy enough that most fighters need both hands just to "
        "raise it, let alone swing it the way the brute did - one-"
        "handed, like it weighed nothing at all."
    ),
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}

ARENA_LOOT_BRUTE_ARMOR = {
    "prototype_parent": "BASEARMOR",
    "price": 60,
    "damage_reduction": 4,
    "defense_modifier": -4,
    "armor_category": "heavy",
    "key": "a stretched mail hauberk",
    "desc": (
        "Stretched to its absolute limit across a chest built like a "
        "siege engine - taking it off him felt less like looting a "
        "corpse and more like disarming a catapult."
    ),
}

ARENA_LOOT_DUELIST_DAGGER = {
    "prototype_parent": "BASEWEAPON",
    "price": 25,
    "damage_range": (10, 20),
    "accuracy_bonus": 30,
    "key": "the Harpy duelist's curved blade",
    "desc": (
        "One of a matched pair, sheathed low and drawn fast - light "
        "enough to never once slow her down, sharp enough that it "
        "rarely needed a second cut."
    ),
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}

ARENA_LOOT_DUELIST_ARMOR = {
    "prototype_parent": "BASEARMOR",
    "price": 20,
    "damage_reduction": 1,
    "defense_modifier": -1,
    "armor_category": "light",
    "key": "a lacquered breastplate",
    "desc": (
        "Cut deliberately narrow across the shoulders to leave a "
        "Harpy's wings free - the kind of sacrifice only a fighter "
        "who's never once needed to block makes on purpose."
    ),
}

ARENA_LOOT_CHAMPION_BROADSWORD = {
    "prototype_parent": "BASEWEAPON",
    "price": 90,
    "damage_range": (18, 32),
    "accuracy_bonus": 7,
    "key": "the Cyclops champion's spatha",
    "desc": (
        "Long enough that most opponents never actually closed the "
        "distance it needs - a hundred real bouts of proof that reach "
        "wins more fights than desperation does."
    ),
    "weapon_type_name": "broadsword",
    "weapon_category": "heavy_blade",
    "two_handed": False,
}

ARENA_LOOT_CHAMPION_ARMOR = {
    "prototype_parent": "BASEARMOR",
    "price": 60,
    "damage_reduction": 4,
    "defense_modifier": -4,
    "armor_category": "heavy",
    "key": "polished legionary plate",
    "desc": (
        "Bright enough to throw back torchlight even now - the mark "
        "of a fighter who could afford to have his armor looking this "
        "good and still never needed to hide behind it."
    ),
}

ARENA_LOOT_MASTER_WARAXE = {
    "prototype_parent": "BASEWEAPON",
    "price": 90,
    "damage_range": (25, 45),
    "accuracy_bonus": -10,
    "key": "the Arena Master's war-hammer",
    "desc": (
        "Undefeated for longer than anyone keeping count can remember - "
        "this is the single most feared object that has ever rested "
        "head-down in this sand, and now it's yours."
    ),
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}

ARENA_LOOT_MASTER_ARMOR = {
    "prototype_parent": "BASEARMOR",
    "price": 60,
    "damage_reduction": 4,
    "defense_modifier": -4,
    "armor_category": "heavy",
    "key": "the Arena Master's blackened plate",
    "desc": (
        "Fought in, not just worn - every dent and scorch mark in this "
        "plate is a story about the one time someone almost won."
    ),
}

"""
----------------------------------------------------------------------------
LUDUS TRAINERS
----------------------------------------------------------------------------
Four tiers of training opponents for the Ludus (gladiator school), roughly
matched to levels 1-2, 3-5, 6-8, and 9-10.

Persistent, standing NPCs (world.combat.RespawningNPC) - @spawn these
directly into their rooms (see world/batch_ludus.ev), don't spawn them
via challenge. Each room gets three of the same tier so a few new
players arriving together never queue behind each other; the batch
file renames each copy with a distinguishing tag after spawning.
respawn_delay is short here deliberately - this is newbie/practice
content, not meant to make anyone wait long to try again.
"""

LUDUS_TRAINER_TIER1 = {
    "key": "a Ludus recruit trainer",
    "aliases": ["trainer", "recruit trainer"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A young trainer, barely more experienced than the recruits he "
        "drills, but patient with beginners and quick with a correction."
    ),
    "player_class": "legionary",
    "level": 2,
    "xp_reward": 15,
    "respawn_delay": 30,
    "locks": "puppet:false()",
}

LUDUS_TRAINER_TIER2 = {
    "key": "a Ludus weapons master",
    "aliases": ["trainer", "weapons master"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A veteran of a dozen minor bouts, the weapons master fights with "
        "the unhurried confidence of someone who's stopped being surprised "
        "by anything a challenger tries."
    ),
    "player_class": "speculator",
    "level": 4,
    "xp_reward": 40,
    "respawn_delay": 45,
    "locks": "puppet:false()",
}

LUDUS_TRAINER_TIER3 = {
    "key": "a Ludus beast-handler",
    "aliases": ["trainer", "beast-handler"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Scarred by claws as often as blades, the beast-handler trains "
        "fighters for the unpredictable chaos of facing something that "
        "doesn't fight by human rules."
    ),
    "player_class": "venator",
    "level": 7,
    "xp_reward": 90,
    "respawn_delay": 60,
    "locks": "puppet:false()",
}

LUDUS_TRAINER_TIER4 = {
    "key": "a Ludus champion",
    "aliases": ["trainer", "champion"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Undefeated in the Ludus for longer than most fighters have been "
        "training here at all. Facing the champion is the last real test "
        "before the games themselves stop feeling quite so frightening."
    ),
    "player_class": "barbarian",
    "level": 10,
    "xp_reward": 150,
    "respawn_delay": 90,
    "locks": "puppet:false()",
}

"""
----------------------------------------------------------------------------
AUGUR FAMILIAR
----------------------------------------------------------------------------
Spawned as a personal, disposable instance by Augur's Summon Familiar
spell (see world/combat.py spell_summon_familiar), same pattern as the
Ludus trainers. No xp_reward - defeating your own familiar shouldn't
earn XP, and no combat_trainer tag either, since it's not meant to
grant Colosseum escape or anything like that.
"""

AUGUR_FAMILIAR_TIER1 = {
    "key": "a great grey owl",
    "aliases": ["owl", "familiar"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "augur",
    "desc": (
        "A huge owl with unnervingly intelligent eyes, its feathers pale as "
        "moonlight. It came at its summoner's call, and watches everything "
        "else in the room with an attention that feels far too knowing for "
        "an ordinary bird."
    ),
    "hp": 40,
    "max_hp": 40,
    "locks": "puppet:false()",
}

AUGUR_FAMILIAR_TIER2 = {
    "key": "a golden eagle",
    "aliases": ["eagle", "familiar"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "augur",
    "desc": (
        "A golden eagle, wings easily spanning the width of a doorway, talons "
        "curved like sickles. Its cry sounds less like a bird and more like a "
        "verdict being read aloud."
    ),
    "hp": 80,
    "max_hp": 80,
    "locks": "puppet:false()",
}

AUGUR_FAMILIAR_TIER3 = {
    "key": "a bronze-feathered hawk of Apollo",
    "aliases": ["hawk", "familiar"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "augur",
    "desc": (
        "A hawk whose feathers catch the light like polished bronze, sacred "
        "to Apollo and lending some faint edge of his sight to whoever it "
        "flies for. It never quite blinks."
    ),
    "hp": 130,
    "max_hp": 130,
    "locks": "puppet:false()",
}

AUGUR_FAMILIAR_TIER4 = {
    "key": "a phoenix wreathed in golden fire",
    "aliases": ["phoenix", "familiar"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "augur",
    "desc": (
        "A bird of living flame, gold and crimson feathers trailing sparks "
        "that never quite burn anything they touch. Only the most favored "
        "Augurs ever call one down at all."
    ),
    "hp": 190,
    "max_hp": 190,
    "locks": "puppet:false()",
}

"""
----------------------------------------------------------------------------
HARUSPEX LEMURES
----------------------------------------------------------------------------
Spawned by Haruspex's Summon Lemures spell, same personal-instance
mechanism as Augur's familiars. Deliberately matches the exact same
HP curve (40/80/130/190) as AUGUR_FAMILIAR_TIER1-4 - both classes'
summon spells should scale with equal power at equal level, not one
quietly outscaling the other.
"""

HARUSPEX_LEMURES_TIER1 = {
    "key": "a whimpering lemur-spirit",
    "aliases": ["lemures", "spirit", "familiar"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "haruspex",
    "desc": (
        "A thin, restless shade, barely held together, drawn from the "
        "unburied dead. It flinches at every sound but obeys its summoner "
        "without question."
    ),
    "hp": 40,
    "max_hp": 40,
    "locks": "puppet:false()",
}

HARUSPEX_LEMURES_TIER2 = {
    "key": "a restless lemures",
    "aliases": ["lemures", "spirit", "familiar"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "haruspex",
    "desc": (
        "A shade with more shape and purpose than the newly-risen, its "
        "grasping hands leaving cold patches in the air wherever it moves."
    ),
    "hp": 80,
    "max_hp": 80,
    "locks": "puppet:false()",
}

HARUSPEX_LEMURES_TIER3 = {
    "key": "a vengeful lemures",
    "aliases": ["lemures", "spirit", "familiar"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "haruspex",
    "desc": (
        "A shade thick with old grievances, its outline sharpening into "
        "something almost human whenever it grows angry - which, bound to "
        "a Haruspex's will, is often."
    ),
    "hp": 130,
    "max_hp": 130,
    "locks": "puppet:false()",
}

HARUSPEX_LEMURES_TIER4 = {
    "key": "a lemures-lord, ancient and ravenous",
    "aliases": ["lemures", "spirit", "familiar"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "haruspex",
    "desc": (
        "Something that stopped being one restless spirit a long time ago "
        "and became a great many of them wearing a single shape. Only the "
        "most accomplished Haruspices can bind something like this to "
        "obedience at all."
    ),
    "hp": 190,
    "max_hp": 190,
    "locks": "puppet:false()",
}

HARUSPEX_FURY = {
    "key": "a vengeful Fury of the underworld",
    "aliases": ["fury", "spirit", "familiar"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "haruspex",
    "desc": (
        "A genuine mythic horror clawed straight out of the underworld, wings "
        "of tarnished bronze and a gaze that promises no mortal escapes its "
        "wrath. Even bound to a summoner's will, something this old barely "
        "tolerates the leash."
    ),
    "hp": 260,
    "max_hp": 260,
    "locks": "puppet:false()",
}

"""
----------------------------------------------------------------------------
VENATOR BEAST COMPANION
----------------------------------------------------------------------------
Spawned by Venator's Call of the Wild spell, same personal-instance
mechanism as Augur's familiars and Haruspex's Lemures. Deliberately
matches the exact same HP curve (40/80/130/190) as those two - all
three summon-capable classes should scale with equal power at equal
level, not one quietly outscaling the others.
"""

VENATOR_BEAST_TIER1 = {
    "key": "a lean gray wolf",
    "aliases": ["wolf", "companion"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "venator",
    "desc": (
        "A rangy gray wolf, ribs faintly visible beneath a scarred hide, "
        "eyes fixed on its handler and no one else. It came at the call "
        "of something it recognizes as kin."
    ),
    "hp": 40,
    "max_hp": 40,
    "locks": "puppet:false()",
}

VENATOR_BEAST_TIER2 = {
    "key": "a scarred hunting wolf",
    "aliases": ["wolf", "companion"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "venator",
    "desc": (
        "A heavier wolf than most, its coat crossed with old scars from "
        "hunts that clearly didn't go easily. It moves with the confidence "
        "of something that has never lost a fight it meant to win."
    ),
    "hp": 80,
    "max_hp": 80,
    "locks": "puppet:false()",
}

VENATOR_BEAST_TIER3 = {
    "key": "a massive dire boar",
    "aliases": ["boar", "companion"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "venator",
    "desc": (
        "A boar the size of a small cart, tusks yellowed and chipped from "
        "use, hide thick as old leather armor. Nothing about it suggests "
        "it has ever backed away from anything."
    ),
    "hp": 130,
    "max_hp": 130,
    "locks": "puppet:false()",
}

VENATOR_BEAST_TIER4 = {
    "key": "a legendary war-beast, scarred and unstoppable",
    "aliases": ["beast", "companion"],
    "typeclass": "world.combat.SummonedAlly",
    "pet_line": "venator",
    "desc": (
        "Something that stopped being simply a wolf or a boar a long time "
        "ago, shaped by a lifetime at the side of hunters who never lost. "
        "Only the most accomplished Venators ever earn a companion like this."
    ),
    "hp": 190,
    "max_hp": 190,
    "locks": "puppet:false()",
}

"""
----------------------------------------------------------------------------
COLOSSEUM SPECTATORS - pure flavor, unattackable, wandering
----------------------------------------------------------------------------
Same "no combat stats at all" pattern as Milo/Titus/Herald - these are
never meant to be fought, just seen. Spawn one, then set its
wander_rooms and attach world.colosseum.WanderingNPC to actually make
it move - see deploy notes for the exact commands, since wander_rooms
needs real room objects that can't be hardcoded into a static
prototype.
"""

COLOSSEUM_COMMONER = {
    "key": "a Roman commoner",
    "aliases": ["commoner", "citizen"],
    "typeclass": "evennia.objects.objects.DefaultCharacter",
    "desc": (
        "An ordinary Roman citizen, dressed for a long day of shouting "
        "and standing rather than anything formal. Right now they're "
        "entirely absorbed in whatever's happening down on the sand."
    ),
    "locks": "puppet:false()",
}

COLOSSEUM_NOBLE = {
    "key": "a wealthy patron",
    "aliases": ["patron", "noble"],
    "typeclass": "evennia.objects.objects.DefaultCharacter",
    "desc": (
        "Dressed well enough that the toga alone probably cost more than "
        "most of the crowd's yearly wages, this patron watches the games "
        "with the studied, faintly bored composure of someone who's seen "
        "better bouts than this one."
    ),
    "locks": "puppet:false()",
}

COLOSSEUM_VENDOR = {
    "key": "a Colosseum vendor",
    "aliases": ["vendor", "hawker"],
    "typeclass": "world.economy.NPCMerchant",
    "desc": (
        "A tray of something - nuts, watered wine, cheap cushions, it "
        "changes by the hour - hangs from a strap around their neck, and "
        "they call out prices to anyone who so much as glances their way."
    ),
    "shopname": "the vendor's tray",
    "locks": "puppet:false()",
}

VENDOR_NUTS = {
    "key": "a handful of roasted nuts",
    "price": 2,
    "desc": "Salted and still warm - the kind of thing you buy without really thinking about it.",
    "locks": "puppet:false()",
}

VENDOR_WATERED_WINE = {
    "key": "a cup of watered wine",
    "price": 3,
    "desc": "More water than wine, and priced accordingly - still, it's wet, and the sun is brutal today.",
    "locks": "puppet:false()",
}

LUDUS_WEAPONSMITH = {
    "key": "a Ludus weaponsmith",
    "aliases": ["weaponsmith", "smith"],
    "typeclass": "world.economy.LudusWeaponsmith",
    "desc": (
        "Forearms scarred by decades of forge-work, the weaponsmith barely "
        "looks up from the blade she's sharpening. Every fighter who's ever "
        "trained here has bought something from her at least once."
    ),
    "shopname": "the weaponsmith's stall",
    "locks": "puppet:false()",
}

# ----------------------------------------------------------------------------
# SPELL/SKILL TRAINERS - see world.combat.SpellSkillTrainer/CmdTrainer.
# Two trainers, one per learning type (SKILLS is class-gated to barbarian/
# gladiator/legionary/speculator/venator, SPELLS to augur/haruspex/medicus -
# checked directly against both dicts, a clean two-way split), rather than
# one per class.
# ----------------------------------------------------------------------------

LUDUS_WEAPONS_MASTER = {
    "key": "the Ludus weapons master",
    "aliases": ["weapons master", "trainer"],
    "typeclass": "world.combat.SpellSkillTrainer",
    "desc": (
        "Old scars map a lifetime of close calls across his forearms, but "
        "his stance never wavers - decades in the Ludus have worn away "
        "everything except what actually keeps a fighter alive. He watches "
        "new arrivals the way a smith checks a blade: not unkindly, just "
        "looking for where it might break."
    ),
    "teaches": "skills",
    "locks": "puppet:false()",
}

FLAMEN_TRAINER = {
    "key": "the Flamen of the Cella",
    "aliases": ["flamen", "trainer"],
    "typeclass": "world.combat.SpellSkillTrainer",
    "desc": (
        "Robed in unbleached wool and never quite still, the Flamen moves "
        "through the cella's incense-smoke like it doesn't concern him. He "
        "has taught the sky-signs, the blood-rites, and the healing arts to "
        "more petitioners than he can name - and judges each new one "
        "silently before he ever agrees to speak."
    ),
    "teaches": "spells",
    "locks": "puppet:false()",
}

"""
----------------------------------------------------------------------------
LUDUS WEAPONSMITH STOCK - three tiers (Novice/Veteran/Champion, roughly
levels 2/6/10 to match the Ludus's own tier bands above) of one weapon per
category plus all three body-armor and shield categories. Each tier gets
its own name and flavor text - never just the same item with bigger
numbers - while sharing the same weapon_type_name/armor_category as its
sibling tiers, so world.combat.compute_weapon_stats/compute_armor_stats
still drives the actual numbers. See LUDUS_WEAPONSMITH_STOCK below (and
world.economy.LudusWeaponsmith) for how these get spawned and priced.
----------------------------------------------------------------------------
"""

SMITH_DAGGER_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a notched practice dagger",
    "desc": (
        "Its edge has been dulled and reground more times than the smith "
        "can count - a first blade for someone who's never held one "
        "before, forgiving of a shaky grip."
    ),
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}

SMITH_DAGGER_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a blood-worn dagger",
    "desc": (
        "The leather grip has darkened with use, and a thin groove runs "
        "the length of the blade where a whetstone has passed a thousand "
        "times. This has drawn real blood before."
    ),
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}

SMITH_DAGGER_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a duelist's stiletto",
    "desc": (
        "Slim, balanced, and honed to a wicked point, this blade was "
        "forged for someone who wins fights in a single motion. The "
        "pommel bears a small victor's laurel etched into the steel."
    ),
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}

SMITH_GLADIUS_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "an unmarked training gladius",
    "desc": (
        "Standard-issue, mass-produced, indistinguishable from a hundred "
        "others racked beside it. It does the job."
    ),
    "weapon_type_name": "gladius",
    "weapon_category": "light_blade",
    "two_handed": False,
}

SMITH_GLADIUS_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a nicked veteran's gladius",
    "desc": (
        "Small dents run along the flat of the blade - each one a parry "
        "that held. Its owner clearly survived whatever put them there."
    ),
    "weapon_type_name": "gladius",
    "weapon_category": "light_blade",
    "two_handed": False,
}

SMITH_GLADIUS_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a gilt-hilted gladius",
    "desc": (
        "Gold leaf traces the hilt's grip, and the flat of the blade "
        "bears an etched name - some past champion's, worn nearly smooth "
        "by handling. The smith won't say how she came by it."
    ),
    "weapon_type_name": "gladius",
    "weapon_category": "light_blade",
    "two_handed": False,
}

SMITH_SPEAR_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a plain ash-wood spear",
    "desc": (
        "A straightforward hunting spear, more suited to driving off a "
        "stray dog than a gladiatorial bout, but sturdy enough to learn "
        "on."
    ),
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}

SMITH_SPEAR_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a battle-scarred spear",
    "desc": (
        "The wooden shaft has been re-wrapped in cord where old cracks "
        "were bound tight, and the bronze head shows the pitting of a "
        "blade that's actually seen use."
    ),
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}

SMITH_SPEAR_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a champion's leaf-bladed spear",
    "desc": (
        "Forged from a single dense billet, its head shaped like a "
        "laurel leaf and inlaid with a thin band of silver. Weighted for "
        "a fighter who's already proven they can use it."
    ),
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}

SMITH_SHORTBOW_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a beginner's shortbow",
    "desc": (
        "Light draw weight, forgiving string tension - built to teach "
        "proper form rather than put anyone down for good."
    ),
    "weapon_type_name": "shortbow",
    "weapon_category": "ranged",
    "two_handed": True,
}

SMITH_SHORTBOW_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a well-strung hunting bow",
    "desc": (
        "The wood has been oiled dark from handling, and the string "
        "shows the fraying of real, repeated use. Someone has clearly "
        "fed themselves with this."
    ),
    "weapon_type_name": "shortbow",
    "weapon_category": "ranged",
    "two_handed": True,
}

SMITH_SHORTBOW_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a horn-tipped recurve bow",
    "desc": (
        "Reinforced with strips of horn along the belly for a punishing "
        "draw weight, its limbs curve back on themselves like a smile. "
        "Not a beginner's weapon."
    ),
    "weapon_type_name": "shortbow",
    "weapon_category": "ranged",
    "two_handed": True,
}

SMITH_WARAXE_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a blunt-edged training axe",
    "desc": (
        "Head weighted for practice swings rather than a killing stroke "
        "- heavy enough to build the right muscles, dull enough not to "
        "end the lesson early."
    ),
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}

SMITH_WARAXE_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a chipped battle-axe",
    "desc": (
        "The edge carries small nicks where it's met bone rather than "
        "air. Whoever swung this last meant it."
    ),
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}

SMITH_WARAXE_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a bearded executioner's axe",
    "desc": (
        "A wide, curved head with a distinctive hooked 'beard' along the "
        "lower edge, built to hook a shield aside before the real blow "
        "lands. This is a crowd-favorite's weapon - the kind that ends "
        "fights, not just wins them."
    ),
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}

# Real gap found and fixed live: RITUAL_STAFF (the fixed chargen
# starting weapon for every caster class - Augur, Haruspex, Medicus)
# never had a leveled upgrade path anywhere in the game - the only
# other "ritual staff" prototype in existence (SEWER_LOOT_RITUAL_STAFF)
# turned out to have IDENTICAL stats, a pure flavor reskin, not a real
# power upgrade. A real player asked directly whether better weapons
# existed for their class and the honest answer was no. These three
# mirror every other SMITH_* weapon tier exactly (spawn_leveled_weapon
# fills in damage_range/accuracy_bonus/price at spawn time from
# weapon_type_name/weapon_category, same as every other tier here).
SMITH_STAFF_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a plain acolyte's staff",
    "desc": (
        "Unadorned ash wood, still smelling faintly of the workshop - "
        "a first staff for someone whose training in the old rites has "
        "barely begun."
    ),
    "weapon_type_name": "ritual staff",
    "weapon_category": "staff",
    "two_handed": True,
}

SMITH_STAFF_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a rune-bound staff",
    "desc": (
        "Bands of inscribed bronze wrap the shaft at even intervals, "
        "each one worn smooth by a hand that has called on it many "
        "times before."
    ),
    "weapon_type_name": "ritual staff",
    "weapon_category": "staff",
    "two_handed": True,
}

SMITH_STAFF_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a high priest's staff",
    "desc": (
        "Dark, oiled wood capped in gold, carved top to bottom with "
        "sky-signs and sacred verses - a staff carried by someone the "
        "gods have clearly not finished with yet."
    ),
    "weapon_type_name": "ritual staff",
    "weapon_category": "staff",
    "two_handed": True,
}

SMITH_LEATHER_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "a patched leather jerkin",
    "desc": "Cheap, thin, and mended more than once - better than nothing, and not much more.",
    "armor_category": "light",
}

SMITH_LEATHER_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "a supple leather cuirass",
    "desc": (
        "Well-oiled and broken in, this hide has been fitted to move "
        "with a fighter rather than against them."
    ),
    "armor_category": "light",
}

SMITH_LEATHER_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a studded champion's leather",
    "desc": (
        "Reinforced with rows of bronze studs and dyed a deep, "
        "deliberate red, this leather has been worn by someone the "
        "crowd already knows by name."
    ),
    "armor_category": "light",
}

SMITH_SCALE_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "a rough scale vest",
    "desc": "The bronze scales are uneven and loosely riveted - functional, if a little noisy.",
    "armor_category": "medium",
}

SMITH_SCALE_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "a battle-worn scale hauberk",
    "desc": (
        "Individual scales have been replaced piecemeal over time, "
        "giving it a mismatched, well-used look that speaks to real "
        "survival."
    ),
    "armor_category": "medium",
}

SMITH_SCALE_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a gilded scale cuirass",
    "desc": (
        "Each bronze scale has been polished to a mirror shine and "
        "edged in gold leaf - as much a statement to the crowd as it is "
        "protection."
    ),
    "armor_category": "medium",
}

SMITH_PLATE_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "a dented practice plate",
    "desc": (
        "Thick, heavy, and none too flattering, this suit was built to "
        "absorb a beating during training, not to look good doing it."
    ),
    "armor_category": "heavy",
}

SMITH_PLATE_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "a battle-forged plate cuirass",
    "desc": (
        "Hammered back into shape more than once, its surface a map of "
        "old dents that never quite came fully out."
    ),
    "armor_category": "heavy",
}

SMITH_PLATE_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a champion's ornamented plate",
    "desc": (
        "Embossed with a relief of crossed gladii across the breastplate "
        "and finished in blackened steel, this armor was clearly made "
        "for someone the Ludus expects to win."
    ),
    "armor_category": "heavy",
}

SMITH_PARMA_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "a worn wooden parma",
    "desc": (
        "Small, light, and scuffed from years of practice bouts - the "
        "kind of shield every recruit starts with."
    ),
    "armor_slot": "shield",
    "armor_category": "light",
}

SMITH_PARMA_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "a bronze-rimmed parma",
    "desc": (
        "Its wooden face bears the dents of blows that didn't land where "
        "they were aimed - proof it's done its job more than once."
    ),
    "armor_slot": "shield",
    "armor_category": "light",
}

SMITH_PARMA_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a champion's painted parma",
    "desc": (
        "Its face bears a bold painted eagle, wings spread, the kind of "
        "shield a crowd learns to recognize and cheer for."
    ),
    "armor_slot": "shield",
    "armor_category": "light",
}

SMITH_CLIPEUS_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "a plain bronze-faced clipeus",
    "desc": (
        "Solid and unremarkable, its bronze facing already showing the "
        "first scratches of real use."
    ),
    "armor_slot": "shield",
    "armor_category": "medium",
}

SMITH_CLIPEUS_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "a battle-dented clipeus",
    "desc": (
        "The bronze face carries a web of shallow dents, each one a blow "
        "that didn't get through."
    ),
    "armor_slot": "shield",
    "armor_category": "medium",
}

SMITH_CLIPEUS_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a champion's laureled clipeus",
    "desc": (
        "Its bronze face is embossed with a wreath of laurel leaves "
        "circling the boss - a shield made for someone expected to keep "
        "winning."
    ),
    "armor_slot": "shield",
    "armor_category": "medium",
}

SMITH_SCUTUM_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "a plain legionary scutum",
    "desc": (
        "Heavy, curved, and entirely without decoration - standard "
        "training issue, built to teach the weight before the finesse."
    ),
    "armor_slot": "shield",
    "armor_category": "heavy",
}

SMITH_SCUTUM_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "a battle-scarred scutum",
    "desc": (
        "Its curved face is scored with old sword-strikes, the wood "
        "beneath the hide showing through in more than one place."
    ),
    "armor_slot": "shield",
    "armor_category": "heavy",
}

SMITH_SCUTUM_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a champion's blazoned scutum",
    "desc": (
        "Painted with a bold thunderbolt motif across its curved face, "
        "this scutum belongs to a fighter the crowd already knows to "
        "watch."
    ),
    "armor_slot": "shield",
    "armor_category": "heavy",
}

COLOSSEUM_MENAGERIE_HANDLER = {
    "key": "a menagerie handler",
    "aliases": ["handler"],
    "typeclass": "evennia.objects.objects.DefaultCharacter",
    "desc": (
        "A handler leads a leashed leopard on a heavy chain, the animal "
        "pacing with the coiled, unhurried patience of something that "
        "knows exactly how strong it is. The handler looks considerably "
        "less calm about the arrangement than the leopard does."
    ),
    "locks": "puppet:false()",
}

# ----------------------------------------------------------------------
# CLOACA MAXIMA (sewer leveling zone) - RespawningNPC population.
# Same pattern as the Arena Fighters above: race/player_class/level set
# on the prototype, HostileNPC/AutoStatNPC derive real stats and a real
# class kit automatically. xp_reward values are interpolated against
# the Arena Fighters' own already-tuned curve (level 3->35 through
# level 25->550), not independently guessed. Tagged "sewer_npc" for the
# live setup script to find and spawn multiple instances of each into
# its assigned rooms - not every NPC needs a unique prototype, matching
# how Deeper Sands itself works.
# ----------------------------------------------------------------------

SEWER_LUDUS_RUNAWAY = {
    "key": "a runaway slave",
    "aliases": ["slave", "runaway"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Thin, wary, and armed with whatever he could grab on the way out "
        "- he's clearly still getting used to fighting for himself rather "
        "than for someone else's amusement."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 5,
    "xp_reward": 55,
    "respawn_delay": 45,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_SUBURA_FOOTPAD = {
    "key": "a Subura footpad",
    "aliases": ["footpad"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Quick, unbothered, and clearly no stranger to these tunnels - "
        "this is someone else's territory, and she knows it better than "
        "you ever will."
    ),
    "race": "human",
    "player_class": "speculator",
    "level": 5,
    "xp_reward": 55,
    "respawn_delay": 50,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_FORUM_DESERTER = {
    "key": "a deserting legionary",
    "aliases": ["deserter", "legionary"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Still in half his kit, clearly hiding from his own century - "
        "whatever he did to end up down here, he's decided it's worth "
        "fighting to keep quiet."
    ),
    "race": "human",
    "player_class": "legionary",
    "level": 6,
    "xp_reward": 65,
    "respawn_delay": 55,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_GANG_THUG = {
    "key": "a territorial gang thug",
    "aliases": ["thug", "gang"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "One of at least two rival groups claiming this junction as "
        "their own - he's not interested in explaining which one, only "
        "in making sure you leave."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 7,
    "xp_reward": 85,
    "respawn_delay": 70,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_GANG_SCOUT = {
    "key": "a rival gang scout",
    "aliases": ["scout"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Watching the junction from a bad angle he clearly thinks is a "
        "good one, reporting back to whoever sent him the moment "
        "anything worth reporting happens."
    ),
    "race": "human",
    "player_class": "venator",
    "level": 8,
    "xp_reward": 110,
    "respawn_delay": 75,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_CLOACA_BANDIT = {
    "key": "a Cloaca bandit",
    "aliases": ["bandit"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A real, organized bandit who's made these cart-scale tunnels a "
        "genuine home base - confident, well-armed, and entirely used to "
        "fighting on this ground."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 10,
    "xp_reward": 145,
    "respawn_delay": 90,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_HECATE_CULTIST = {
    "key": "a cultist of Hecate",
    "aliases": ["cultist"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Performing the Crossroads Queen's rites far from anyone who "
        "might object, three-faced amulet in hand - interrupted, and "
        "not remotely apologetic about the fact that she's armed."
    ),
    "race": "human",
    "player_class": "haruspex",
    "level": 11,
    "xp_reward": 160,
    "respawn_delay": 100,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_VIGILES_FUGITIVE = {
    "key": "a fugitive of the Vigiles",
    "aliases": ["fugitive"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Hiding from the city watch in a dead-end he's chosen specifically "
        "because it's easy to defend - whatever he's actually wanted for, "
        "he's not eager to find out what happens if he's caught."
    ),
    "race": "human",
    "player_class": "speculator",
    "level": 12,
    "xp_reward": 180,
    "respawn_delay": 110,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_SMUGGLER = {
    "key": "a sewer smuggler",
    "aliases": ["smuggler"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Working the flooded tunnels like they're a real trade route - "
        "which, for goods that need to avoid every checkpoint in the "
        "city, they genuinely are."
    ),
    "race": "human",
    "player_class": "venator",
    "level": 14,
    "xp_reward": 215,
    "respawn_delay": 120,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_FERAL_MUTANT = {
    "key": "a feral sewer mutant",
    "aliases": ["mutant"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Whatever this was before, years in the flooded dark have shaped "
        "it into something else entirely - pale, waterlogged, and "
        "hostile to anything that isn't already part of this place."
    ),
    "level": 15,
    "xp_reward": 235,
    "respawn_delay": 130,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_MINOTAUR_GLADIATOR = {
    "key": "a Minotaur gladiator",
    "aliases": ["minotaur", "gladiator"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Built for the arena, fighting far better down here in the "
        "cramped, flooded dark than any open sand would ever let him - "
        "the water barely seems to slow him down at all."
    ),
    "race": "minotaur",
    "player_class": "gladiator",
    "level": 16,
    "xp_reward": 260,
    "respawn_delay": 150,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_SETTLEMENT_GUARD = {
    "key": "a settlement guard",
    "aliases": ["guard"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A real, organized guard for the buried settlement's boundary - "
        "disciplined in a way nothing in the tunnels above quite "
        "managed to be."
    ),
    "race": "human",
    "player_class": "legionary",
    "level": 18,
    "xp_reward": 310,
    "respawn_delay": 160,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_SETTLEMENT_ENFORCER = {
    "key": "a settlement enforcer",
    "aliases": ["enforcer"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Whatever order the buried settlement actually keeps, she's "
        "clearly the one enforcing it - and treats an intruder as just "
        "one more piece of business to handle."
    ),
    "race": "human",
    "player_class": "barbarian",
    "level": 19,
    "xp_reward": 340,
    "respawn_delay": 170,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_CYCLOPS_BARBARIAN = {
    "key": "a feral Cyclops",
    "aliases": ["cyclops"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Whatever civilization this Cyclops once had has worn away "
        "entirely down here - it no longer distinguishes between prey "
        "and intruder, and hasn't for a long time."
    ),
    "race": "cyclops",
    "player_class": "barbarian",
    "level": 21,
    "xp_reward": 410,
    "respawn_delay": 200,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_NYMPH_AUGUR = {
    "key": "a Nymph augur",
    "aliases": ["nymph", "augur"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Reading omens from bird bones far from any actual sky, leading "
        "something down here that's clearly stopped being simple "
        "divination a long time ago."
    ),
    "race": "nymph",
    "player_class": "augur",
    "level": 22,
    "xp_reward": 440,
    "respawn_delay": 210,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_CISTERN_LURKER = {
    "key": "a cistern lurker",
    "aliases": ["lurker"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Something that has clearly made the deepest, oldest water in "
        "the entire network its own - it doesn't hunt so much as simply "
        "wait for you to be there."
    ),
    "level": 24,
    "xp_reward": 520,
    "respawn_delay": 280,
    "tags": [("sewer_npc", "npc_role")],
    "locks": "puppet:false()",
}

SEWER_BOSS_DROWNED_SENTINEL = {
    "key": "the Drowned Sentinel",
    "aliases": ["sentinel", "drowned sentinel"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Whatever this was meant to guard, it has clearly never once "
        "stopped - ancient, waterlogged, and entirely undiminished by "
        "however many centuries it's spent down here alone. Named, "
        "unique, and genuinely rare - this is the Cloaca Maxima's real "
        "final encounter, not a farmable stop along the way."
    ),
    "race": "cyclops",
    "player_class": "barbarian",
    "level": 25,
    "xp_reward": 600,
    "respawn_delay": 900,
    "tags": [("sewer_npc", "npc_role"), ("sewer_boss", "npc_role")],
    "locks": "puppet:false()",
}

# ----------------------------------------------------------------------
# CLOACA MAXIMA LOOT - genuinely distinct from both chargen's starting
# gear and the Ludus weaponsmith's SMITH_* shop stock, per direct
# request (a sewer drop shouldn't be indistinguishable from something
# a player already owns for free or could just buy). Reuses the same
# weapon_type_name/weapon_category/armor_category values the rest of
# the game's math depends on - compute_weapon_stats/compute_armor_stats
# (world/combat.py) key off those, not off the prototype's own name -
# so balance stays perfectly consistent with everything else; only the
# identity (key/desc) is new. Each is flavored to tie back to a
# specific tier/faction of the zone it drops in, rather than being
# generic reskins.
# ----------------------------------------------------------------------

SEWER_LOOT_GLADIUS = {
    "prototype_parent": "BASEWEAPON",
    "price": 25,
    "damage_range": (10, 20),
    "accuracy_bonus": -5,
    "key": "a corroded gladius",
    "desc": (
        "Pitted with rust and stained by years in the flooded dark, but "
        "the edge still bites - pried from a bandit who clearly isn't "
        "using it anymore."
    ),
    "weapon_type_name": "gladius",
    "weapon_category": "light_blade",
    "two_handed": False,
}

SEWER_LOOT_DAGGER = {
    "prototype_parent": "BASEWEAPON",
    "price": 25,
    "damage_range": (10, 20),
    "accuracy_bonus": 30,
    "key": "a smuggler's dagger",
    "desc": (
        "Balanced for close, fast work in cramped tunnels - exactly the "
        "kind of blade someone moving contraband through flooded "
        "passages would want close at hand."
    ),
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}

SEWER_LOOT_SPEAR = {
    "prototype_parent": "BASEWEAPON",
    "price": 25,
    "damage_range": (12, 22),
    "accuracy_bonus": 2,
    "key": "a settlement guard's spear",
    "desc": (
        "Well-maintained despite its surroundings - whoever carried "
        "this took real, disciplined pride in it, more than anything "
        "else found down here suggests."
    ),
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": False,
}

SEWER_LOOT_WARAXE = {
    "prototype_parent": "BASEWEAPON",
    "price": 90,
    "damage_range": (25, 45),
    "accuracy_bonus": -10,
    "key": "a bandit's notched waraxe",
    "desc": (
        "Heavy, brutal, and clearly used hard - the notches along its "
        "edge tell their own story about exactly how this bandit spent "
        "his time down here."
    ),
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}

SEWER_LOOT_RITUAL_STAFF = {
    "prototype_parent": "BASEWEAPON",
    "price": 45,
    "damage_range": (6, 14),
    "accuracy_bonus": 25,
    "key": "a Hecate-blessed ritual staff",
    "desc": (
        "Carved with the same three-faced sigil scratched into the "
        "cult's rite chamber walls - whoever carried this answered to "
        "the Crossroads Queen directly."
    ),
    "weapon_type_name": "ritual staff",
    "weapon_category": "staff",
    "two_handed": True,
}

SEWER_LOOT_SHORTBOW = {
    "prototype_parent": "BASEWEAPON",
    "price": 25,
    "damage_range": (8, 18),
    "accuracy_bonus": 20,
    "key": "a hunter's worn shortbow",
    "desc": (
        "The string's been replaced more than once, but the stave "
        "itself has seen real, extensive use - whoever hunted with "
        "this down here got good at it."
    ),
    "weapon_type_name": "shortbow",
    "weapon_category": "ranged",
    "two_handed": False,
}

SEWER_LOOT_LEATHER = {
    "prototype_parent": "BASEARMOR",
    "price": 30,
    "damage_reduction": 2,
    "defense_modifier": -2,
    "armor_category": "light",
    "key": "sewer-hardened leather",
    "desc": (
        "Treated, somehow, to actually hold up against the constant "
        "damp - stiffer and heavier than ordinary leather, but it "
        "clearly hasn't rotted through like it should have."
    ),
}

SEWER_LOOT_SCALE = {
    "prototype_parent": "BASEARMOR",
    "price": 60,
    "damage_reduction": 4,
    "defense_modifier": -4,
    "armor_category": "medium",
    "key": "waterlogged scale mail",
    "desc": (
        "Genuinely functional despite years of standing water - some "
        "of the scales have gone green, but none of them have actually "
        "failed."
    ),
}

SEWER_LOOT_PLATE = {
    "prototype_parent": "BASEARMOR",
    "price": 100,
    "damage_reduction": 6,
    "defense_modifier": -6,
    "armor_category": "heavy",
    "key": "a bandit's salvaged plate",
    "desc": (
        "Mismatched pieces, clearly scavenged from more than one "
        "source and hammered into something wearable - ugly, but it "
        "stops a blade exactly the same as anything prettier would."
    ),
}

# ----------------------------------------------------------------------------
# The Germanic Stronghold's combat population (levels 27-46), placed by
# world/setup_germania_live.py - the post-sewers leveling zone. Same
# HostileNPC/RespawningNPC pattern as the SEWER_* roster above:
# race/player_class/level set on the prototype, real stats and a real
# class-appropriate combat AI derived automatically (world.combat's
# AutoStatNPC/HostileNPC). xp_reward follows the same ~6% of that
# level's own xp_for_level convention the sewers/Ludus already use;
# respawn_delay follows the same linear extrapolation of the sewers'
# own tier-scaled delays. Real race/class variety across the roster,
# not a single reskinned type at increasing levels - a gap found live
# by direct question and fixed before this zone was even built.
# ----------------------------------------------------------------------------

# --- Wolf-kin (levels 27-31) ---

GERMANIA_WOLFKIN_RAIDER = {
    "key": "a Wolf-kin raider",
    "aliases": ["raider"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A young warrior, real wolf teeth strung around his neck as "
        "proof of something already earned, even this early in his "
        "own career."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 27,
    "xp_reward": 629,
    "respawn_delay": 317,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

GERMANIA_WOLFKIN_BRAWLER = {
    "key": "a Wolf-kin brawler",
    "aliases": ["brawler"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Loud, enthusiastic, and genuinely dangerous despite - or "
        "maybe because of - how little he seems to worry about it."
    ),
    "race": "human",
    "player_class": "barbarian",
    "level": 29,
    "xp_reward": 720,
    "respawn_delay": 342,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

GERMANIA_WOLFKIN_YOUNG_MINOTAUR = {
    "key": "a young Minotaur of the Wolf-kin",
    "aliases": ["minotaur"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Still visibly growing into his own raw strength, which "
        "doesn't make him any less dangerous to actually fight."
    ),
    "race": "minotaur",
    "player_class": "barbarian",
    "level": 31,
    "xp_reward": 818,
    "respawn_delay": 367,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

# --- Boar-marked (levels 31-35) ---

GERMANIA_BOARMARKED_WARRIOR = {
    "key": "a Boar-marked warrior",
    "aliases": ["warrior"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Scarred, confident, and visibly tested - this warband has "
        "actually fought, and it shows in the way he carries "
        "himself."
    ),
    "race": "human",
    "player_class": "barbarian",
    "level": 32,
    "xp_reward": 868,
    "respawn_delay": 379,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

GERMANIA_BOARMARKED_CYCLOPS = {
    "key": "a Boar-marked Cyclops",
    "aliases": ["cyclops"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, raw muscle even by this warband's own standards - "
        "genuinely feared even among warriors who don't scare easily."
    ),
    "race": "cyclops",
    "player_class": "barbarian",
    "level": 34,
    "xp_reward": 974,
    "respawn_delay": 404,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

GERMANIA_BOARMARKED_VETERAN = {
    "key": "a Boar-marked veteran",
    "aliases": ["veteran"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Older than most of the camp around him, real trophies from "
        "real fights earned over real years, not a single season."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 35,
    "xp_reward": 1030,
    "respawn_delay": 417,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

# --- Raven's Watch (levels 35-39) ---

GERMANIA_RAVENSWATCH_SCOUT = {
    "key": "a Raven's Watch scout",
    "aliases": ["scout"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Genuinely fast, genuinely observant - a Centaur built for "
        "covering ground, not holding it."
    ),
    "race": "centaur",
    "player_class": "venator",
    "level": 36,
    "xp_reward": 1086,
    "respawn_delay": 429,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

GERMANIA_RAVENSWATCH_RAIDER = {
    "key": "a Raven's Watch raider",
    "aliases": ["raider"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Lean and quick, real raven feathers marking her out even "
        "at a distance - built for a fast strike, not a long fight."
    ),
    "race": "human",
    "player_class": "venator",
    "level": 38,
    "xp_reward": 1204,
    "respawn_delay": 454,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

# --- Storm-callers (levels 39-43) ---

GERMANIA_STORMCALLER_GUARD = {
    "key": "a Storm-caller guard",
    "aliases": ["guard"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, disciplined muscle - the chieftain's own trust made "
        "visible in a Minotaur who takes that responsibility "
        "seriously."
    ),
    "race": "minotaur",
    "player_class": "barbarian",
    "level": 40,
    "xp_reward": 1327,
    "respawn_delay": 479,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

GERMANIA_STORMCALLER_ELITE = {
    "key": "a Storm-caller elite",
    "aliases": ["elite"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Genuinely dangerous in the air as much as on the ground - "
        "a Harpy warrior who's earned a real place among the "
        "chieftain's own best."
    ),
    "race": "harpy",
    "player_class": "venator",
    "level": 42,
    "xp_reward": 1456,
    "respawn_delay": 503,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

# --- Contested Borderlands (levels 41-45) ---

GERMANIA_BORDERLANDS_RAIDER = {
    "key": "a borderlands raider",
    "aliases": ["raider"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Belonging to no warband anyone here recognizes - real, "
        "contested territory draws exactly this kind of fighter."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 41,
    "xp_reward": 1391,
    "respawn_delay": 491,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

GERMANIA_BORDERLANDS_CYCLOPS = {
    "key": "a borderlands Cyclops",
    "aliases": ["cyclops"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Genuinely feral by now, whatever warband once claimed him "
        "long since forgotten out here."
    ),
    "race": "cyclops",
    "player_class": "barbarian",
    "level": 43,
    "xp_reward": 1523,
    "respawn_delay": 516,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

GERMANIA_BORDERLANDS_SCOUT = {
    "key": "a borderlands scout",
    "aliases": ["scout"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A real, dangerous Centaur, watching this contested ground "
        "the way only someone who's survived it repeatedly can."
    ),
    "race": "centaur",
    "player_class": "venator",
    "level": 45,
    "xp_reward": 1660,
    "respawn_delay": 541,
    "tags": [("germania_npc", "npc_role")],
    "locks": "puppet:false()",
}

# --- Capstone: the Storm-callers' unique champion (level 46) ---

GERMANIA_BOSS_STORMCALLER_CHAMPION = {
    "key": "Vidrik Storm-Marked",
    "aliases": ["vidrik", "champion"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "The chieftain's own champion, and it's obvious within a "
        "single look why - real, earned authority in a Minotaur "
        "who's never once needed to raise his voice to be obeyed. "
        "Few who reach this ground turn back, and fewer still walk "
        "away from what actually happens if they don't."
    ),
    "race": "minotaur",
    "player_class": "barbarian",
    "level": 46,
    "xp_reward": 2200,
    "respawn_delay": 1200,
    "tags": [("germania_npc", "npc_role"), ("germania_boss", "npc_role")],
    "locks": "puppet:false()",
}

# ----------------------------------------------------------------------------
# The Germanic weaponsmith's stock (world/economy.py's GermanicWeaponsmith,
# placed in "The Weaponsmith's Stall") - genuinely Germanic-named gear,
# not reskinned Roman items, per direct request. Reuses the existing
# weapon_type_name/armor_category balance tables wholesale (the display
# name is entirely separate from the balance lookup - "a worn seax" can
# use weapon_type_name "dagger" and get dagger's own real stats) rather
# than inventing a second, parallel item-power system. Three tiers
# (25/35/45) matching this zone's own level range, mirroring the
# Ludus weaponsmith's 2/6/10 three-tier shape.
# ----------------------------------------------------------------------------

GERMANIA_SEAX_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a worn seax",
    "desc": "A real, single-edged Germanic blade - well-used, not fancy.",
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}
GERMANIA_SEAX_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a well-balanced seax",
    "desc": "Real, careful smithing - this blade has clearly seen real fights and come out ahead.",
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}
GERMANIA_SEAX_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a masterwork seax",
    "desc": "Genuinely fine work - the kind of blade a warband's own champion actually carries.",
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}

GERMANIA_ANGON_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a plain angon",
    "desc": "A real, heavy throwing-and-thrusting spear - straightforward, effective, unglamorous.",
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}
GERMANIA_ANGON_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a reinforced angon",
    "desc": "Real, deliberate reinforcement along the shaft - built to survive real, repeated use.",
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}
GERMANIA_ANGON_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a champion's angon",
    "desc": "Genuinely fine balance and real reach - a weapon built for someone who's already proven themselves.",
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}

GERMANIA_FRANCISCA_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a plain francisca",
    "desc": "A real Germanic throwing axe - short-hafted, genuinely built to be thrown hard.",
    "weapon_type_name": "javelin",
    "weapon_category": "ranged",
    "two_handed": False,
}
GERMANIA_FRANCISCA_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a well-weighted francisca",
    "desc": "Real, careful balance - this one flies true more often than not.",
    "weapon_type_name": "javelin",
    "weapon_category": "ranged",
    "two_handed": False,
}
GERMANIA_FRANCISCA_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a masterwork francisca",
    "desc": "Genuinely fine smithing - a throwing axe good enough to be worth actually recovering afterward.",
    "weapon_type_name": "javelin",
    "weapon_category": "ranged",
    "two_handed": False,
}

GERMANIA_WARAXE_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a plain Germanic waraxe",
    "desc": "Real, heavy, and entirely unsubtle - exactly what it looks like.",
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}
GERMANIA_WARAXE_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a battle-worn Germanic waraxe",
    "desc": "Real, visible nicks along the edge - proof of real, repeated use, not neglect.",
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}
GERMANIA_WARAXE_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a champion's Germanic waraxe",
    "desc": "Genuinely fine, heavy craftsmanship - a real warband champion's own weapon of choice.",
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}

GERMANIA_LAMELLAR_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "worn lamellar armor",
    "desc": "Real overlapping plates, laced and worn - functional, unglamorous.",
    "armor_category": "medium",
}
GERMANIA_LAMELLAR_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "well-kept lamellar armor",
    "desc": "Real, careful maintenance - this warrior's own gear has clearly been looked after.",
    "armor_category": "medium",
}
GERMANIA_LAMELLAR_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a champion's lamellar armor",
    "desc": "Genuinely fine craftsmanship - real, deliberate reinforcement in every visible seam.",
    "armor_category": "medium",
}

GERMANIA_MAIL_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "a plain mail shirt",
    "desc": "Real, heavy ringmail - unglamorous, effective, exactly what it looks like.",
    "armor_category": "heavy",
}
GERMANIA_MAIL_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "a reinforced mail shirt",
    "desc": "Real, deliberate reinforcement at the vital points - a warrior who's actually been tested.",
    "armor_category": "heavy",
}
GERMANIA_MAIL_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a champion's mail hauberk",
    "desc": "Genuinely fine ringmail, real and heavy - the kind only a warband's own best actually wears.",
    "armor_category": "heavy",
}

"""
----------------------------------------------------------------------------
GERMANIA LOOT DROPS
----------------------------------------------------------------------------
Deliberately distinct flavor names from GermanicWeaponsmith's own shop
stock just above (seax/angon/francisca/waraxe/lamellar/mail) - same
principle world/loot.py's own SEWER_LOOT_* prototypes already
establish: a drop should feel like a genuine find, not a bare reskin
of something already purchasable. Reuses the exact same weapon_type_
name/armor_category balance lookups (world.combat.compute_weapon_
stats/compute_armor_stats), spawned and leveled by
world.loot.roll_germania_loot_drop exactly like the sewer's own drops.
"""

GERMANIA_LOOT_KNIFE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a bone-hilted raider's knife",
    "desc": (
        "Not a smith's work - whittled bone lashed to a blade taken off "
        "someone who no longer needed it. Whoever carried this made do "
        "with what a raid actually gave them."
    ),
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}

GERMANIA_LOOT_BOARSPEAR = {
    "prototype_parent": "BASEWEAPON",
    "key": "a raider's boar-spear",
    "desc": (
        "A heavy crossbar set just below the head - meant for a boar "
        "that won't stop coming even after the point goes in, and just "
        "as useful against a man who won't either."
    ),
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}

GERMANIA_LOOT_BEARDED_AXE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a chieftain's bearded axe",
    "desc": (
        "The blade curves back into a real hook, not just a wider "
        "edge - meant to catch a shield's rim and wrench it aside. "
        "Nobody hands this down to just anyone."
    ),
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}

GERMANIA_LOOT_HIDE = {
    "prototype_parent": "BASEARMOR",
    "key": "a stitched wolf-hide jerkin",
    "desc": (
        "Real wolf hide, cured and stitched close over the chest - "
        "light enough to move in, and the pelt itself is worth a "
        "story most people won't ask you to finish."
    ),
    "armor_category": "light",
}

GERMANIA_LOOT_BONEPLATE = {
    "prototype_parent": "BASEARMOR",
    "key": "a bone-plated war harness",
    "desc": (
        "Overlapping plates of boiled bone and horn, lashed to a "
        "leather harness - real, deliberate protection, built by "
        "someone who expected this to matter."
    ),
    "armor_category": "medium",
}

# ----------------------------------------------------------------------------
# THE AMBER COAST - a coastal Germanic trading town north of the
# Germanic Stronghold (world/batch_amber_coast_data.py and its Part
# 2/3 files, world/wilderness_amber_coast.py). Deliberately its own
# "amber_coast_npc" tag, NOT "germania_npc" - a separate population
# with its own loot table (world/loot.py's roll_amber_coast_loot_drop)
# so drops don't feel identical to the interior Stronghold's.
#
# Levels are the design document's own numbers +21 across the board -
# see world/wilderness_amber_coast.py's module docstring for exactly
# why (the doc assumed the interior Stronghold was levels 1-25; the
# real live Stronghold is 27-46, so this whole location bridges from
# that real cap instead of restarting below it).
#
# Racial casting is deliberately NOT a repeat of the Stronghold's own
# even Minotaur/Cyclops/Centaur/Harpy mix, by direct request (the
# concern: two "Germanic leveling areas" feeling repetitive) - each
# camp's race choices are tied to its actual job rather than being
# another generic fantasy-race shuffle: Wave-Riders lean human (a ship
# crew) with one Harpy mini-boss (a sea-survivor, not a repeat of the
# Stronghold's own scout-Harpy use); Iron Tide concentrates Minotaur/
# Cyclops muscle (a wall garrison has a real reason to want it); the
# Drowned Oath introduces Nymph - a playable race the Stronghold never
# uses at all - including a spellcasting Haruspex mini-boss (Wulfhild),
# the only non-melee warband leader among all eight combined; Amber
# Guard stays mostly human with one Centaur outrider for the caravan-
# escort role specifically.
# ----------------------------------------------------------------------------

# --- Wave-Riders (levels 51-55) ---

AMBER_WAVERIDER_DECKHAND = {
    "key": "a Wave-Rider deckhand",
    "aliases": ["deckhand"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Barefoot on packed sand as easily as a deck, this young "
        "raider clearly spends more time on the water than off it."
    ),
    "race": "human",
    "player_class": "venator",
    "level": 51,
    "xp_reward": 2106,
    "respawn_delay": 617,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_WAVERIDER_OARSMAN = {
    "key": "a Wave-Rider oarsman",
    "aliases": ["oarsman"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, hard muscle earned at an oar rather than a training "
        "yard - a very different kind of strength than the interior "
        "warbands build."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 52,
    "xp_reward": 2185,
    "respawn_delay": 630,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_WAVERIDER_HARPOONER = {
    "key": "a Wave-Rider harpooner",
    "aliases": ["harpooner"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A long iron harpoon rests easy in her hands - real, "
        "practiced skill at hitting something that's actively trying "
        "not to be hit."
    ),
    "race": "human",
    "player_class": "venator",
    "level": 52,
    "xp_reward": 2185,
    "respawn_delay": 630,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_WAVERIDER_CHAMPION = {
    "key": "a boasting champion",
    "aliases": ["champion"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Undefeated on the Boasting Stone for longer than most of "
        "this camp's own memory - real, earned standing, settled by "
        "real wrestling rather than any quieter hierarchy."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 53,
    "xp_reward": 2266,
    "respawn_delay": 642,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_WAVERIDER_ARMORER = {
    "key": "the Wave-Riders' armorer",
    "aliases": ["armorer"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Salt has already started working at every blade he tends, "
        "despite real, constant oiling - a losing fight he clearly "
        "intends to keep having anyway."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 53,
    "xp_reward": 2266,
    "respawn_delay": 642,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_WAVERIDER_SCAVENGER = {
    "key": "a starving drifter",
    "aliases": ["drifter"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Drawn in by the smell of drying fish and desperate enough "
        "not to care whose catch it actually is."
    ),
    "race": "human",
    "player_class": "venator",
    "level": 54,
    "xp_reward": 2348,
    "respawn_delay": 654,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_BOSS_SKALLA_HALF_DROWNED = {
    "key": "Skalla Half-Drowned",
    "aliases": ["skalla"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Survived a real wreck that should have killed her, and has "
        "led the Wave-Riders like she's daring the sea to try again. "
        "Real sea-glass and bone charms cover every seam of what "
        "she wears."
    ),
    "race": "harpy",
    "player_class": "venator",
    "level": 55,
    "xp_reward": 2431,
    "respawn_delay": 900,
    "tags": [("amber_coast_npc", "npc_role"), ("amber_coast_leader", "npc_role")],
    "locks": "puppet:false()",
}

# --- Iron Tide (levels 54-58) ---

AMBER_IRONTIDE_SHIELDBEARER = {
    "key": "an Iron Tide shield-bearer",
    "aliases": ["shieldbearer"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, disciplined stillness in the shield-wall line - this "
        "one has clearly drilled this exact stance more times than "
        "he could count."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 54,
    "xp_reward": 2348,
    "respawn_delay": 654,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_IRONTIDE_RECRUIT = {
    "key": "an Iron Tide recruit",
    "aliases": ["recruit"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Mid-drill and visibly still learning the shield-wall's real "
        "rhythm, sweat and real effort obvious even at a distance."
    ),
    "race": "human",
    "player_class": "barbarian",
    "level": 55,
    "xp_reward": 2431,
    "respawn_delay": 667,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_IRONTIDE_SENTRY = {
    "key": "an Iron Tide sentry",
    "aliases": ["sentry"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Watches the wall-watch logboard as closely as the wall "
        "itself - real, careful attention to a job that's genuinely "
        "this camp's whole reason for being."
    ),
    "race": "human",
    "player_class": "barbarian",
    "level": 55,
    "xp_reward": 2431,
    "respawn_delay": 667,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_IRONTIDE_VETERAN = {
    "key": "an Iron Tide veteran",
    "aliases": ["veteran"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, raw Minotaur strength backing up the shield-wall's "
        "own discipline - exactly the kind of muscle this camp was "
        "built to field."
    ),
    "race": "minotaur",
    "player_class": "barbarian",
    "level": 56,
    "xp_reward": 2516,
    "respawn_delay": 680,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_IRONTIDE_ENFORCER = {
    "key": "an Iron Tide enforcer",
    "aliases": ["enforcer"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Stands by the Punishment Post without ever quite relaxing - "
        "real, genuine size doing most of the actual talking here."
    ),
    "race": "cyclops",
    "player_class": "barbarian",
    "level": 56,
    "xp_reward": 2516,
    "respawn_delay": 680,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_IRONTIDE_DRILLMASTER = {
    "key": "an Iron Tide drillmaster",
    "aliases": ["drillmaster"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Runs this camp's real, repeated drills with a discipline "
        "that makes the interior warbands look genuinely loose by "
        "comparison."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 57,
    "xp_reward": 2602,
    "respawn_delay": 692,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_BOSS_BERHTWIN_OAKENSHIELD = {
    "key": "Berhtwin Oakenshield",
    "aliases": ["berhtwin"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, immovable Minotaur presence at his own command post - "
        "Berhtwin doesn't need to seek out a fight. Whatever comes at "
        "this wall meets him first, every time."
    ),
    "race": "minotaur",
    "player_class": "barbarian",
    "level": 58,
    "xp_reward": 2689,
    "respawn_delay": 900,
    "tags": [("amber_coast_npc", "npc_role"), ("amber_coast_leader", "npc_role")],
    "locks": "puppet:false()",
}

# --- The Drowned Oath (levels 57-61) ---

AMBER_DROWNEDOATH_VOTARY = {
    "key": "a Drowned Oath votary",
    "aliases": ["votary"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, quiet devotion visible in every movement - this "
        "warband fights for an oath first and a warlord second."
    ),
    "race": "human",
    "player_class": "venator",
    "level": 57,
    "xp_reward": 2602,
    "respawn_delay": 692,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_DROWNEDOATH_ADHERENT = {
    "key": "a Drowned Oath adherent",
    "aliases": ["adherent"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Ritual scars mark real, deliberate vows kept over real "
        "years - this warband's own steel serves the oath before "
        "anything else."
    ),
    "race": "human",
    "player_class": "barbarian",
    "level": 58,
    "xp_reward": 2689,
    "respawn_delay": 704,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_DROWNEDOATH_SHUNNED = {
    "key": "the shunned warrior",
    "aliases": ["shunned"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Held apart from the rest of the camp for an oath broken - "
        "real, genuine anger at being cast out has nowhere left to "
        "go but outward."
    ),
    "race": "human",
    "player_class": "barbarian",
    "level": 59,
    "xp_reward": 2778,
    "respawn_delay": 717,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_DROWNEDOATH_ARMORER = {
    "key": "a Drowned Oath armorer",
    "aliases": ["armorer"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Scores a small ritual notch into every blade before it "
        "ever leaves her hands - even this camp's steel answers to "
        "the oath first."
    ),
    "race": "nymph",
    "player_class": "venator",
    "level": 59,
    "xp_reward": 2778,
    "respawn_delay": 717,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_DROWNEDOATH_GUARD = {
    "key": "a Drowned Oath causeway-guard",
    "aliases": ["causeway-guard", "guard"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Watches the causeway to Nerthus's own isle without ever "
        "quite calling it guard duty - real, genuine reverence "
        "dressed up as a simple watch."
    ),
    "race": "human",
    "player_class": "barbarian",
    "level": 61,
    "xp_reward": 2960,
    "respawn_delay": 742,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_BOSS_WULFHILD_THE_SWORN = {
    "key": "Wulfhild the Sworn",
    "aliases": ["wulfhild"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Ritual marks cover nearly every visible inch of her, far "
        "more than any other warband leader on this coast carries. "
        "Real power moves through her that has nothing to do with "
        "steel at all."
    ),
    "race": "nymph",
    "player_class": "haruspex",
    "level": 60,
    "xp_reward": 2868,
    "respawn_delay": 900,
    "tags": [("amber_coast_npc", "npc_role"), ("amber_coast_leader", "npc_role")],
    "locks": "puppet:false()",
}

# --- The Amber Guard (levels 59-63) ---

AMBER_AMBERGUARD_ESCORT = {
    "key": "an Amber Guard escort",
    "aliases": ["escort"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, professional bearing that has nothing to do with "
        "warband pride and everything to do with protecting what "
        "she's actually paid to protect."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 59,
    "xp_reward": 2778,
    "respawn_delay": 717,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_AMBERGUARD_SENTINEL = {
    "key": "an Amber Guard sentinel",
    "aliases": ["sentinel"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Stands by the strongbox vault without ever quite relaxing - "
        "real wealth demands real, constant attention."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 61,
    "xp_reward": 2960,
    "respawn_delay": 742,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_AMBERGUARD_VETERAN = {
    "key": "an Amber Guard veteran",
    "aliases": ["veteran"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "The best-kept gear of any warband on this coast, worn by "
        "someone who's clearly earned the right to it."
    ),
    "race": "human",
    "player_class": "barbarian",
    "level": 61,
    "xp_reward": 2960,
    "respawn_delay": 742,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_AMBERGUARD_QUARTERMASTER = {
    "key": "an Amber Guard quartermaster",
    "aliases": ["quartermaster"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Keeps real, exact count of every weapon issued and returned "
        "- this camp's own discipline runs through ledgers as much "
        "as through steel."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 62,
    "xp_reward": 3052,
    "respawn_delay": 754,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_AMBERGUARD_OUTRIDER = {
    "key": "an Amber Guard outrider",
    "aliases": ["outrider"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, genuine speed built for one job - getting a caravan "
        "somewhere safely, and getting back just as fast if it isn't."
    ),
    "race": "centaur",
    "player_class": "venator",
    "level": 62,
    "xp_reward": 3052,
    "respawn_delay": 754,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_BOSS_INGVAR_COINWARD = {
    "key": "Ingvar Coin-Ward",
    "aliases": ["ingvar"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, careful authority in how he carries himself - Ingvar "
        "protects Hertha's own wealth like it's genuinely his to "
        "answer for, because in every way that matters, it is."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 63,
    "xp_reward": 3147,
    "respawn_delay": 900,
    "tags": [("amber_coast_npc", "npc_role"), ("amber_coast_leader", "npc_role")],
    "locks": "puppet:false()",
}

# --- Town-level authority (the Great Hall) ---

AMBER_BOSS_HERTHA_SEA_NIX = {
    "key": "Hertha Sea-Nix",
    "aliases": ["hertha"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, absolute authority over this entire coast, worn as "
        "easily as the amber set into her own hall's roof-beams. "
        "Every scar she carries is visible, none of them hidden."
    ),
    "race": "human",
    "player_class": "barbarian",
    "level": 68,
    "xp_reward": 3638,
    "respawn_delay": 1200,
    "tags": [("amber_coast_npc", "npc_role"), ("amber_coast_boss", "npc_role")],
    "locks": "puppet:false()",
}

# --- Nerthus's Sacred Isle (levels 58-63, deliberately sparse) ---

AMBER_SACREDISLE_BOGWIGHT = {
    "key": "a bog-wight",
    "aliases": ["bogwight"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Something that used to be a person, kept moving by whatever "
        "the bog-pool actually took from it in exchange."
    ),
    "race": "human",
    "player_class": "haruspex",
    "level": 58,
    "xp_reward": 2689,
    "respawn_delay": 704,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_SACREDISLE_BOGWIGHT_ELDER = {
    "key": "an elder bog-wight",
    "aliases": ["elder bogwight"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Older, stiller, and far more purposeful than the younger "
        "things sharing this bog - whatever it once was, it's been "
        "down here a genuinely long time."
    ),
    "race": "human",
    "player_class": "haruspex",
    "level": 61,
    "xp_reward": 2960,
    "respawn_delay": 742,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_GUARDIAN_VEILED_WAGON = {
    "key": "the Veiled Wagon's guardian",
    "aliases": ["guardian"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Bars the way to the Veiled Wagon without ever needing to "
        "say why - real, genuine authority that has nothing to do "
        "with Hertha's hall and everything to do with what's under "
        "that covering."
    ),
    "race": "nymph",
    "player_class": "haruspex",
    "level": 63,
    "xp_reward": 3147,
    "respawn_delay": 1200,
    "tags": [("amber_coast_npc", "npc_role"), ("amber_coast_boss", "npc_role")],
    "locks": "puppet:false()",
}

# --- Deeper Coastal Wilds capstone (levels 62-71) ---

AMBER_WILDS_CLIFFRAIDER = {
    "key": "a cliff raider",
    "aliases": ["raider"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Belongs to no warband on this coast - real, contested, "
        "uncontrolled ground draws exactly this kind of survivor."
    ),
    "race": "human",
    "player_class": "venator",
    "level": 62,
    "xp_reward": 3052,
    "respawn_delay": 754,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_WILDS_WRECKSCAVENGER = {
    "key": "a wreck-scavenger",
    "aliases": ["scavenger"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Picks over the old wreck-site with real, practiced care - "
        "whatever's worth taking here has clearly been fought over "
        "before."
    ),
    "race": "human",
    "player_class": "venator",
    "level": 64,
    "xp_reward": 3242,
    "respawn_delay": 780,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_WILDS_CAVEDWELLER = {
    "key": "a cave-dweller",
    "aliases": ["dweller"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Genuinely feral by now, real Cyclops strength the only "
        "thing that's kept it alive this far out."
    ),
    "race": "cyclops",
    "player_class": "barbarian",
    "level": 66,
    "xp_reward": 3438,
    "respawn_delay": 804,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_WILDS_OUTCAST = {
    "key": "an outcast",
    "aliases": ["outcast"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Fast, wary, and clearly used to real, sustained solitude - "
        "whatever put her out here, she hasn't gone back."
    ),
    "race": "centaur",
    "player_class": "venator",
    "level": 67,
    "xp_reward": 3537,
    "respawn_delay": 817,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_WILDS_DEEPCAVE_LURKER = {
    "key": "a deep-cave lurker",
    "aliases": ["lurker"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Real, genuine size fills the cave passage almost entirely - "
        "whatever it's waiting for, it's clearly patient about it."
    ),
    "race": "minotaur",
    "player_class": "barbarian",
    "level": 69,
    "xp_reward": 3741,
    "respawn_delay": 842,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_BOSS_ORMSTOOTH = {
    "key": "Ormstooth, the Unclaimed",
    "aliases": ["ormstooth"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "No warband, Roman patrol, or trade caravan has ever pushed "
        "this far north and come back to say much about it - and "
        "Ormstooth is the entire, real reason why."
    ),
    "race": "cyclops",
    "player_class": "barbarian",
    "level": 71,
    "xp_reward": 3949,
    "respawn_delay": 1800,
    "tags": [("amber_coast_npc", "npc_role"), ("amber_coast_boss", "npc_role")],
    "locks": "puppet:false()",
}

# ----------------------------------------------------------------------------
# The Amber Coast's own loot prototypes (world/loot.py's
# roll_amber_coast_loot_drop) - deliberately its own flavor set, not
# shared with the Germanic Stronghold's SEWER_LOOT_*/GERMANIA_LOOT_*
# tables, so a drop here doesn't feel like the same find repeated in
# a second "Germanic" zone. Amber-and-sea themed rather than the
# Stronghold's plain forged-iron flavor.
# ----------------------------------------------------------------------------

AMBER_LOOT_SEAX = {
    "prototype_parent": "BASEWEAPON",
    "key": "a sea-forged seax",
    "desc": (
        "A real, single-edged blade, its hilt wrapped in salt-"
        "stiffened cord - forged somewhere that clearly smelled of "
        "brine the whole time."
    ),
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
}

AMBER_LOOT_HARPOON_SPEAR = {
    "prototype_parent": "BASEWEAPON",
    "key": "a barbed harpoon-spear",
    "desc": (
        "A real fishing harpoon, reworked with a second barb for "
        "something that fights back on two legs instead of fins."
    ),
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
}

AMBER_LOOT_STORM_AXE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a storm-worked waraxe",
    "desc": (
        "Real amber inlay runs the length of the haft, pale gold "
        "against dark, weather-blackened iron."
    ),
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
}

AMBER_LOOT_TIDE_HIDE = {
    "prototype_parent": "BASEARMOR",
    "key": "a tide-cured hide vest",
    "desc": (
        "Real sealskin, cured against salt water in a way land-bound "
        "leather never has to be."
    ),
    "armor_category": "light",
}

AMBER_LOOT_AMBER_MAIL = {
    "prototype_parent": "BASEARMOR",
    "key": "an amber-set mail shirt",
    "desc": (
        "Real iron rings, a scattering of small amber beads worked "
        "into the collar - protection that's also, unmistakably, a "
        "real display of wealth."
    ),
    "armor_category": "medium",
}
# ----------------------------------------------------------------------------
# The Amber Coast's own Smith's Quarter Armory stock (world/economy.py's
# AmberCoastArmorer) - genuinely distinct flavor names from the
# Germanic Stronghold's own weaponsmith (seax/angon/francisca/waraxe/
# lamellar/mail), same reasoning as every other loot/shop table in
# this project: two "Germanic" vendors selling identically-flavored
# gear would read as repetitive. Three tiers (46/58/70) spanning this
# recalibrated zone's own 45-71 range, mirroring the Stronghold
# weaponsmith's own three-tier shape.
# ----------------------------------------------------------------------------

AC_SMITH_DIRK_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a whale-bone dirk",
    "desc": "A short blade with a real, carved whale-bone hilt - practical, not ceremonial.",
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}
AC_SMITH_DIRK_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a well-worn whale-bone dirk",
    "desc": "The hilt's carving has worn smooth with real, honest use.",
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}
AC_SMITH_DIRK_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a fine whale-bone dirk",
    "desc": "Real amber chips are set into the hilt's own carving - a blade meant to be seen as well as used.",
    "weapon_type_name": "dagger",
    "weapon_category": "light_blade",
    "two_handed": False,
}

AC_SMITH_GAFFSPEAR_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a plain gaff-spear",
    "desc": "A real fishing gaff reworked with a proper spearhead - practical dual heritage.",
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}
AC_SMITH_GAFFSPEAR_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a sturdy gaff-spear",
    "desc": "Real, reinforced binding at the haft's own weak point - built to actually last.",
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}
AC_SMITH_GAFFSPEAR_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a masterwork gaff-spear",
    "desc": "Real, expert balance from tip to butt-end - the work of someone who's made hundreds of these.",
    "weapon_type_name": "spear",
    "weapon_category": "polearm",
    "two_handed": True,
}

AC_SMITH_TIDEAXE_NOVICE = {
    "prototype_parent": "BASEWEAPON",
    "key": "a tide-tempered waraxe",
    "desc": "Quenched in real seawater during its own forging - a harder edge, the smith swears.",
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}
AC_SMITH_TIDEAXE_VETERAN = {
    "prototype_parent": "BASEWEAPON",
    "key": "a well-forged tide-tempered waraxe",
    "desc": "Real, visible skill in the blade's own even temper line.",
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}
AC_SMITH_TIDEAXE_CHAMPION = {
    "prototype_parent": "BASEWEAPON",
    "key": "a masterwork tide-tempered waraxe",
    "desc": "Real amber inlay traces the full length of the haft - this smith's own finest work.",
    "weapon_type_name": "waraxe",
    "weapon_category": "heavy_weapon",
    "two_handed": True,
}

AC_SMITH_SEALSKIN_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "a sealskin jerkin",
    "desc": "Real sealskin, cured against salt water in a way land-bound leather never has to be.",
    "armor_category": "light",
}
AC_SMITH_SEALSKIN_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "a reinforced sealskin jerkin",
    "desc": "Real, doubled stitching at every real stress point.",
    "armor_category": "light",
}
AC_SMITH_SEALSKIN_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a fine sealskin jerkin",
    "desc": "Real amber studs mark the collar - light protection that's also a real display of means.",
    "armor_category": "light",
}

AC_SMITH_FISHMAIL_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "a scaled fish-mail hauberk",
    "desc": "Real, overlapping metal scales, laced in a pattern borrowed from a fish's own hide.",
    "armor_category": "medium",
}
AC_SMITH_FISHMAIL_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "a well-kept fish-mail hauberk",
    "desc": "Real, careful maintenance keeps every scale bright despite the salt air.",
    "armor_category": "medium",
}
AC_SMITH_FISHMAIL_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a masterwork fish-mail hauberk",
    "desc": "Real silver-washed scales catch the light - protection built to also be seen.",
    "armor_category": "medium",
}

AC_SMITH_WHALEBONE_NOVICE = {
    "prototype_parent": "BASEARMOR",
    "key": "a whalebone-plated cuirass",
    "desc": "Real, overlapping whalebone plates lashed to a heavy leather harness.",
    "armor_category": "heavy",
}
AC_SMITH_WHALEBONE_VETERAN = {
    "prototype_parent": "BASEARMOR",
    "key": "a reinforced whalebone-plated cuirass",
    "desc": "Real, doubled plating over the chest and shoulders both.",
    "armor_category": "heavy",
}
AC_SMITH_WHALEBONE_CHAMPION = {
    "prototype_parent": "BASEARMOR",
    "key": "a masterwork whalebone-plated cuirass",
    "desc": "Real amber-set rivets hold every plate - genuinely the finest heavy armor this coast produces.",
    "armor_category": "heavy",
}

# ----------------------------------------------------------------------------
# The Amber Trader's stock (world/economy.py's AmberTrader) - a pure
# flavor-goods vendor, same shape as the Colosseum vendor/Forum
# goldsmith/perfumer (no weapon/armor mechanics, just a real price on
# a real curio) - amber jewelry and curios specifically, tying
# directly into the whole location's own premise.
# ----------------------------------------------------------------------------

AC_AMBER_PENDANT = {
    "key": "a polished amber pendant",
    "desc": "Real amber, warm gold against its own leather cord - simple, and genuinely lovely for it.",
    "price": 40,
}
AC_AMBER_BEAD_BRACELET = {
    "key": "an amber bead bracelet",
    "desc": "A real string of small, matched amber beads - not fine work, but honest work.",
    "price": 25,
}
AC_AMBER_CARVED_FIGURE = {
    "key": "a carved amber figure",
    "desc": "A small, real animal shape worked into a single piece of amber - real, patient craft.",
    "price": 65,
}
AC_AMBER_RAW_CHUNK = {
    "key": "a raw amber chunk",
    "desc": "Unworked, real amber straight from the trade - a real investment for anyone who works stone or wood themselves.",
    "price": 90,
}

# ----------------------------------------------------------------------------
# The Amber Coast's lighter, connective-zone population (Coastal Road,
# Outer Palisade, Harbor District, Sea-Nix's Hall barracks, Terp Mound
# Quarter, Trading Quarter, Shipyard, Fishing & Salt Flats) - real but
# deliberately lower-density than the Four Warbands, matching the
# design document's own framing of these as transition/civilian zones
# rather than the primary leveling backbone.
# ----------------------------------------------------------------------------

AMBER_ROAD_BANDIT = {
    "key": "a coastal bandit",
    "aliases": ["bandit"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": "Preys on traders working the delta road - real, opportunistic danger, not an organized warband.",
    "race": "human",
    "player_class": "venator",
    "level": 47,
    "xp_reward": 1803,
    "respawn_delay": 567,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_PALISADE_WARDEN = {
    "key": "a gate warden",
    "aliases": ["warden"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": "Watches the outer gate with real, unhurried attention - trade demands letting strangers in, not trusting them blindly.",
    "race": "human",
    "player_class": "gladiator",
    "level": 48,
    "xp_reward": 1877,
    "respawn_delay": 580,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_HARBOR_TOUGH = {
    "key": "a harbor tough",
    "aliases": ["tough"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": "Real, casual menace at the edge of the harbor's own crowd - the kind of trouble a busy dock always seems to attract.",
    "race": "human",
    "player_class": "venator",
    "level": 50,
    "xp_reward": 2028,
    "respawn_delay": 604,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_HARBOR_SMUGGLER = {
    "key": "a smuggler",
    "aliases": ["smuggler"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": "Nervous, quick, and genuinely dangerous if actually cornered - whatever's in those crates isn't meant to be found.",
    "race": "human",
    "player_class": "venator",
    "level": 51,
    "xp_reward": 2106,
    "respawn_delay": 617,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_HALL_GUARD = {
    "key": "a hearth-companion guard",
    "aliases": ["guard"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": "One of Hertha's own real, trusted hearth-companions - visible discipline in every stance.",
    "race": "human",
    "player_class": "gladiator",
    "level": 54,
    "xp_reward": 2348,
    "respawn_delay": 654,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_TERPMOUND_THIEF = {
    "key": "a petty thief",
    "aliases": ["thief"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": "Real, opportunistic trouble in an otherwise quiet residential quarter - quick hands, quicker feet.",
    "race": "human",
    "player_class": "venator",
    "level": 49,
    "xp_reward": 1952,
    "respawn_delay": 592,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_TRADE_ENFORCER = {
    "key": "a dispute enforcer",
    "aliases": ["enforcer"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": "Hertha's own real authority made visible right at the barter square's edge - commercial disputes rarely escalate twice.",
    "race": "human",
    "player_class": "gladiator",
    "level": 52,
    "xp_reward": 2185,
    "respawn_delay": 630,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_SHIPYARD_GUARD = {
    "key": "a shipyard guard",
    "aliases": ["guard"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": "Watches over real, valuable timber and pitch stores - a working yard is also a real theft target.",
    "race": "human",
    "player_class": "gladiator",
    "level": 53,
    "xp_reward": 2266,
    "respawn_delay": 642,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

AMBER_SALTFLAT_SCAVENGER = {
    "key": "a tideflat scavenger",
    "aliases": ["scavenger"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": "Works the salt flats' own edges for whatever the tide leaves behind, and isn't always particular about whose catch it is.",
    "race": "human",
    "player_class": "venator",
    "level": 50,
    "xp_reward": 2028,
    "respawn_delay": 604,
    "tags": [("amber_coast_npc", "npc_role")],
    "locks": "puppet:false()",
}

# ----------------------------------------------------------------------------
# Purchasable pets (world/economy.py's PetVendor, world/combat.py's
# CmdBuyPet) - level 10+, gold-bought companions with a genuinely
# different lifecycle from a spell-summoned pet (world.combat.
# PurchasedPet's own docstring has the full reasoning): they persist
# across fights, follow their owner automatically, and survive a
# logout/login cycle, only actually gone once explicitly dismissed.
# Deliberately modest stats, below even Augur's own entry-level
# Summon Familiar tier - this is a starter utility pet available
# well before any class's own summon spell unlocks, not a
# replacement for one.
# ----------------------------------------------------------------------------

PET_HOUND = {
    "key": "a loyal hunting hound",
    "aliases": ["hound", "dog"],
    "typeclass": "world.combat.PurchasedPet",
    "pet_line": "purchased",
    "desc": (
        "A real, scarred veteran of the hunt, utterly devoted to "
        "whoever feeds it. It stays close, ears up, always watching "
        "for the next real threat."
    ),
    "hp": 35,
    "max_hp": 35,
    "locks": "puppet:false()",
}

PET_HAWK = {
    "key": "a trained messenger hawk",
    "aliases": ["hawk"],
    "typeclass": "world.combat.PurchasedPet",
    "pet_line": "purchased",
    "desc": (
        "A real, hooded hunting hawk, calm on the wrist and genuinely "
        "fierce the moment it's actually needed."
    ),
    "hp": 35,
    "max_hp": 35,
    "locks": "puppet:false()",
}
