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
    "key": "a suit of leather armor",
}

SCALEMAIL = {
    "prototype_parent": "BASEARMOR",
    "price": 60,
    "damage_reduction": 4,
    "defense_modifier": -4,
    "key": "a suit of scale mail",
}

PLATEMAIL = {
    "prototype_parent": "BASEARMOR",
    "price": 100,
    "damage_reduction": 6,
    "defense_modifier": -6,
    "key": "a suit of plate mail",
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

MEDKIT = {
    "key": "a medical kit",
    "aliases": ["medkit"],
    "desc": "A standard medical kit. It can be used a few times to heal wounds.",
    "item_func": "heal",
    "item_uses": 3,
    "item_consumable": True,
    "item_kwargs": {"healing_range": (15, 25)},
}

GLASS_BOTTLE = {"key": "a glass bottle", "desc": "An empty glass bottle."}

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

ARENA_FIGHTER_RECRUIT = {
    "key": "a green arena recruit",
    "aliases": ["recruit", "fighter"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Barely past his first real fight, this recruit still fights like "
        "someone who's watched more bouts than he's actually had. Eager, "
        "sloppy, and dangerous mainly to himself."
    ),
    "race": "human",
    "player_class": "gladiator",
    "level": 3,
    "xp_reward": 35,
    "respawn_delay": 60,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

ARENA_FIGHTER_HUNTER = {
    "key": "a Centaur arena hunter",
    "aliases": ["hunter", "fighter", "centaur"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A Centaur fighter, javelin in hand, moving with the restless energy "
        "of something that would rather be running open ground than "
        "standing on sand. He's adapted. Mostly."
    ),
    "race": "centaur",
    "player_class": "venator",
    "level": 8,
    "xp_reward": 110,
    "respawn_delay": 90,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

ARENA_FIGHTER_BRUTE = {
    "key": "a Minotaur arena brute",
    "aliases": ["brute", "fighter", "minotaur"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A Minotaur built like a siege engine, breathing slow through "
        "flared nostrils, patient in the specific way of something that "
        "has never once needed to rush."
    ),
    "race": "minotaur",
    "player_class": "barbarian",
    "level": 12,
    "xp_reward": 180,
    "respawn_delay": 120,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

ARENA_FIGHTER_DUELIST = {
    "key": "a Harpy arena duelist",
    "aliases": ["duelist", "fighter", "harpy"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A Harpy duelist, wings half-mantled, watching for any opening "
        "with the unblinking patience of something that has fought - and "
        "won - more of these than she'll ever bother mentioning."
    ),
    "race": "harpy",
    "player_class": "gladiator",
    "level": 16,
    "xp_reward": 260,
    "respawn_delay": 150,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

ARENA_FIGHTER_CHAMPION = {
    "key": "a Cyclops arena champion",
    "aliases": ["champion", "fighter", "cyclops"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "A Cyclops in full legionary plate, somehow both massive and "
        "precise, shield locked in close the way only someone who's "
        "actually survived a hundred bouts holds one."
    ),
    "race": "cyclops",
    "player_class": "legionary",
    "level": 20,
    "xp_reward": 380,
    "respawn_delay": 180,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
}

ARENA_FIGHTER_MASTER = {
    "key": "the Arena Master",
    "aliases": ["master", "fighter", "arena master"],
    "typeclass": "world.combat.RespawningNPC",
    "desc": (
        "Undefeated for longer than anyone keeping count can remember, the "
        "Arena Master doesn't posture or warm up. He just waits - utterly "
        "still, utterly certain - for whoever's next foolish enough to try."
    ),
    "player_class": "gladiator",
    "level": 25,
    "xp_reward": 550,
    "respawn_delay": 300,
    "tags": [("arena_fighter", "npc_role")],
    "locks": "puppet:false()",
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
    "typeclass": "world.economy.NPCMerchant",
    "desc": (
        "Forearms scarred by decades of forge-work, the weaponsmith barely "
        "looks up from the blade she's sharpening. Every fighter who's ever "
        "trained here has bought something from her at least once."
    ),
    "shopname": "the weaponsmith's stall",
    "locks": "puppet:false()",
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