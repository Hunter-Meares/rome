"""
Rome chargen menu

A character creation EvMenu for Rome: The Eternal City, built on top of
Evennia's character_creator contrib. Flow:

    welcome -> choose race -> choose class -> choose name -> confirm -> end

Race and class data lives in the RACES and CLASSES dicts below - update
those to add/adjust options rather than touching the menu node logic.

MECHANICAL NOTE: Signature abilities listed for each race/class are not
yet implemented as real commands - they're stored as flavor text on the
character (char.db.class_abilities / char.db.race_abilities) so they
display and can be referenced, but they don't do anything mechanically
yet. Building them out as real Commands (using world/combat.py's
CombatRules as a model) is a good next project once basic combat is
solid. Stat bonuses (HP/MP/SP) and starting gear/spells ARE applied for
real, using the systems in world/combat.py.
"""

from typeclasses.characters import Character

from evennia.prototypes.spawner import spawn
from evennia.utils import dedent

#########################################################
#             PRESENTATION HELPERS
#########################################################
# A direct request to make chargen feel considered rather than a form
# to fill out: Roman numeral option labels, a step tracker showing the
# journey's shape, and distinct per-race/per-class accent colors and
# quotes (see RACES/CLASSES below). None of this touches game
# mechanics - purely how the same choices are presented.

_ROMAN_NUMERALS = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
}


def _to_roman(n):
    """
    Small, deliberately non-general lookup rather than a real
    subtractive-notation algorithm - chargen never has more than a
    handful of options on any one page (8 classes is the current
    max), so a full algorithm would be solving a much bigger problem
    than this actually has.
    """
    return _ROMAN_NUMERALS.get(n, str(n))


# (step number, total steps, step name) per node - a direct request
# for a visible "II of V" style tracker so chargen reads as a journey
# with a real arc instead of an open-ended sequence of menus. The
# *_info detail pages (race_info/class_info) share their parent
# page's step, since picking a specific race/class to read about
# doesn't advance you to a new stage of the process.
_TOTAL_STEPS = 5
_STEP_INFO = {
    "menunode_choose_race": (1, "Choose Your Race"),
    "menunode_race_info": (1, "Choose Your Race"),
    "menunode_choose_class": (2, "Choose Your Path"),
    "menunode_class_info": (2, "Choose Your Path"),
    "menunode_choose_gender": (3, "A Matter of Birth"),
    "menunode_choose_name": (4, "Name Yourself"),
    "menunode_confirm_name": (5, "Confirm Your Name"),
}


def _numbered_option(index, desc, goto):
    """
    Builds one menu option with a Roman-numeral display key, while
    still accepting the plain digit as real input - the same dual-key
    pattern this menu already used for Yes/No ("key": ("Yes", "y")).
    A direct request to make chargen's option lists read as
    considered rather than a bare, auto-numbered form; costs nothing
    mechanically since the functional input never changes.
    """
    numeral = _to_roman(index)
    return {"key": (numeral, str(index)), "desc": desc, "goto": goto}


def _step_header(nodename):
    """
    Returns a one-line "|c[Step II of V -- Choose Your Path]|n" style
    header for the given node, or "" for a node with no entry in
    _STEP_INFO (the welcome page and the end screen - neither is
    really a "step" in the choice sequence).
    """
    info = _STEP_INFO.get(nodename)
    if not info:
        return ""
    step, name = info
    return "|c[Step %s of %s -- %s]|n\n\n" % (
        _to_roman(step), _to_roman(_TOTAL_STEPS), name
    )


#########################################################
#                    RACE DATA
#########################################################

RACES = {
    "human": {
        "display": "Human (Roman Citizen)",
        "color": "|w",
        "quote": '"I need no monstrous blood to conquer - only will, and Rome behind me."',
        "desc": dedent(
            """\
            Versatile and adaptable, excelling in civic life, trade, and warfare. Roman citizens navigate politics and command with ease.
            """
        ),
        "traits": ["Social Savvy", "Adaptable"],
        "abilities": [
            "Command Presence - bonus to leadership/diplomacy",
            "Civic Access - hold/influence positions",
        ],
        # No stat bonuses - humans are the flexible baseline.
        "stat_mods": {"max_hp": 0, "max_mp": 0, "max_sp": 0, "virtus": 0, "agilitas": 0, "ingenium": 0, "vigor": 0},
    },
    "minotaur": {
        "display": "Minotaur (Labyrinth Born)",
        "color": "|420",
        "quote": '"The maze does not frighten me. I was built to break through walls, not wander them."',
        "desc": dedent(
            """\
            Powerful warriors, descendants of bulls and humans. Fearsome in combat and adept at navigating complex terrain like mazes or fortresses.
            """
        ),
        "traits": ["Strength", "Resilience"],
        "abilities": [
            "Bull Rush - knock enemies back",
            "Labyrinth Sense - never get lost in complex terrain",
        ],
        "stat_mods": {"max_hp": 20, "max_mp": -5, "max_sp": 0, "virtus": 3, "agilitas": 0, "ingenium": 0, "vigor": 1},
    },
    "centaur": {
        "display": "Centaur (Forest Guardian)",
        "color": "|140",
        "quote": '"I have run these woods since before Rome had a wall to hide behind."',
        "desc": dedent(
            """\
            Half-human, half-horse, roaming the wilds as protectors of forests. Skilled archers and scouts, combining intelligence with equine speed and strength.
            """
        ),
        "traits": ["Strength", "Agility"],
        "abilities": [
            "Galloping Charge - powerful close-quarters attack",
            "Forest Tracker - excellent movement and tracking in nature",
        ],
        "stat_mods": {"max_hp": 5, "max_mp": 0, "max_sp": 15, "virtus": 2, "agilitas": 2, "ingenium": 0, "vigor": 0},
    },
    "harpy": {
        "display": "Harpy (Windborne Seeker)",
        "color": "|335",
        "quote": '"The wind does not ask permission to enter a room. Neither do I."',
        "desc": dedent(
            """\
            Winged humanoids tied to storms and mountains. Skilled scouts and aerial warriors, perfect for reconnaissance and hit-and-run tactics.
            """
        ),
        "traits": ["Flight", "Keen Senses"],
        "abilities": [
            "Aerial Assault - bonus attacks from above",
            "Skyward Scout - traverse terrain faster, spot hidden foes",
        ],
        "stat_mods": {"max_hp": -5, "max_mp": 0, "max_sp": 20, "virtus": 0, "agilitas": 2, "ingenium": 2, "vigor": 0},
    },
    "nymph": {
        "display": "Nymph (Descendants of the Wild)",
        "color": "|151",
        "quote": '"What\'s left of the wild in me is small, but it does not forget."',
        "desc": dedent(
            """\
            Though their name is drawn from the immortal nature-spirits of old, playable Nymphs are mortal - descendants of a union between nymph and mortal, carrying a fading echo of that divine parent's power. Not goddesses themselves, but never quite ordinary either.
            """
        ),
        "traits": ["Nature Affinity", "Healing"],
        "abilities": [
            "Boon of the Wilds - heal allies",
            "Elemental Ward - temporary elemental protection",
        ],
        "stat_mods": {"max_hp": -5, "max_mp": 20, "max_sp": 0, "virtus": 0, "agilitas": 0, "ingenium": 3, "vigor": 0},
    },
    "cyclops": {
        "display": "Cyclops (Titanic Brute)",
        "color": "|222",
        "quote": '"Two eyes see too much and trust too little. One eye, and I have never been fooled."',
        "desc": dedent(
            """\
            Enormous one-eyed giants famed for strength and craftsmanship. Formidable in battle and expert siege engineers shaping the outcome of conflicts.
            """
        ),
        "traits": ["Strength", "Endurance"],
        "abilities": [
            "Crushing Blow - massive melee damage",
            "Forge Mastery - craft/repair weapons faster",
            "Intimidating Presence - reduce enemy morale",
        ],
        "stat_mods": {"max_hp": 30, "max_mp": -10, "max_sp": -5, "virtus": 3, "agilitas": 0, "ingenium": 0, "vigor": 2},
    },
}

_RACE_ORDER = ["human", "minotaur", "centaur", "harpy", "nymph", "cyclops"]


def _leans_caster(stat_mods):
    """
    True if ingenium (spell power) is this race or class's single
    highest core stat, False if some other stat is uniquely highest,
    or None if there's a tie for highest (including, but not limited
    to, all four core stats being equal) - meaning no clear leaning
    either way.

    That None case matters in two distinct ways: a fully balanced
    entry like Human (all stats equal, typically all zero) needs it,
    or it would incorrectly appear to "lean physical" purely because
    virtus happens to be checked first when nothing actually wins.
    And a deliberately flexible entry - built with two stats tied for
    the top, e.g. Harpy's Agilitas/Ingenium split after the race/class
    synergy discussion - needs the SAME check, not just the special
    case of every stat being equal. An earlier version of this only
    caught the full-tie case, which meant a genuine two-way tie at
    the top still silently resolved to whichever stat came first in
    the core_stats tuple - the exact bug this function exists to
    avoid, just reappearing at the top instead of across the board.

    Used instead of a plain "do the two primary stats match exactly"
    check - that turned out too strict, flagging ordinary variation
    within the physical stats (e.g. Human/Legionary, Virtus vs Vigor)
    as if it were as significant as a genuine physical-race/caster-
    class mismatch. The real, meaningful divide worth a heads-up is
    specifically caster-leaning vs not.
    """
    core_stats = ("virtus", "agilitas", "ingenium", "vigor")
    values = {s: stat_mods.get(s, 0) for s in core_stats}
    highest = max(values.values())
    if list(values.values()).count(highest) > 1:
        return None
    return max(values, key=values.get) == "ingenium"


def _format_abilities(abilities):
    """
    Formats a list of "Name - description" ability strings with the
    name in gold and the description plain, instead of one flat,
    uncolored block of text.
    """
    lines = []
    for entry in abilities:
        if " - " in entry:
            name, desc = entry.split(" - ", 1)
            lines.append(" |Y%s|n - %s" % (name, desc))
        else:
            lines.append(" %s" % entry)
    return "\n".join(lines)

#########################################################
#                   CLASS DATA
#########################################################

# starting_spells: spells auto-added to spells_known at chargen end
#     (must match a key in world.combat.SPELLS)
# starting_gear: prototype names (from world/prototypes.py) to spawn
#     and equip automatically. Weapons get auto-wielded, armor auto-donned.
# For classes whose "real" starting gear doesn't have a prototype yet
# (ritual staff, gladius, pilum, etc.), the closest existing equivalent
# is used as a placeholder - swap these out once you've built proper
# prototypes for them in world/prototypes.py.

CLASSES = {
    "augur": {
        "display": "Augur (Light - Mage/Support)",
        "color": "|553",
        "quote": '"The birds cross the sky in patterns no accident could produce. I have only learned to read what was already written."',
        "theme": "Priestly diviners who read signs from the sky and birds to grant foresight and favor.",
        "role": "Support caster - buffs, predictive effects, and short-range battlefield control.",
        "abilities": [
            "Birdsight - reveal hidden enemies or traps in a small area for a short time",
            "Favour of the Sky - grant an ally a temporary luck/crit bonus",
            "Auspice - a short predictive buff that reduces incoming damage for a target",
        ],
        "gear_desc": "Light leather-reinforced robe, ritual staff, felt cap, wraps, sandals - no shield",
        "stat_mods": {"virtus": 0, "agilitas": 0, "ingenium": 3, "vigor": 0},
        "starting_gear": [
            "RITUAL_STAFF",
            "LEATHERARMOR",
            "PILEUS",
            "FASCIA_BRACHII",
            "CHIROTHECAE",
            "FEMINALIA",
            "SOLEAE",
        ],
        "starting_spells": ["cure wounds"],
    },
    "medicus": {
        "display": "Medicus (Light - Healer/Support)",
        "color": "|455",
        "quote": '"Every wound has a story. Mine is simply to make sure it isn\'t the last chapter."',
        "theme": "Battlefield physicians trained in wound-care, herb-lore, and the old belief that healing hands carry a touch of the divine.",
        "role": "Primary healer - sustained HP recovery, cleansing harmful conditions, and keeping the party standing.",
        "abilities": [
            "Field Dressing - a strong single-target heal, fast enough to use mid-combat",
            "Antidote - cures poison and other harmful conditions on an ally",
            "Triage - a group-wide heal, weaker per-target but reaching everyone nearby",
        ],
        "gear_desc": "Satchel of herbs and bandages, a simple probe, leather-reinforced field tunic, light wraps and sandals - no shield",
        "stat_mods": {"virtus": 0, "agilitas": 0, "ingenium": 2, "vigor": 1},
        "starting_gear": [
            "DAGGER",
            "LEATHERARMOR",
            "PILEUS",
            "FASCIA_BRACHII",
            "CHIROTHECAE",
            "FEMINALIA",
            "SOLEAE",
        ],
        "starting_spells": ["cure wounds", "field dressing", "antidote"],
    },
    "haruspex": {
        "display": "Haruspex (Light - Offense Caster)",
        "color": "|300",
        "quote": '"The entrails do not lie, even when the man reading them wishes they would."',
        "theme": "Etruscan-influenced ritualists who use blood rites and curses.",
        "role": "Offensive caster - curses, damage-over-time, and dark rituals.",
        "abilities": [
            "Rite of the Entrails - place a curse that reveals weaknesses and increases damage taken",
            "Blood Sacrament - convert a portion of the caster's health to power a devastating ritual",
            "Mark of Decay - damage-over-time effect that saps enemy strength",
        ],
        "gear_desc": "Light leather-banded ritual garb, sacrificial blade (ceremonial), bone talismans, light wraps and sandals - no shield",
        "stat_mods": {"virtus": 0, "agilitas": 0, "ingenium": 3, "vigor": 0},
        "starting_gear": [
            "DAGGER",
            "LEATHERARMOR",
            "PILEUS",
            "FASCIA_BRACHII",
            "CHIROTHECAE",
            "FEMINALIA",
            "SOLEAE",
        ],
        "starting_spells": ["mark of decay"],
    },
    "speculator": {
        "display": "Speculator (Medium - Rogue/Scout)",
        "color": "|114",
        "quote": '"You never saw me. That\'s rather the point."',
        "theme": "Spies and scouts for commanders - masters of infiltration, intelligence, and assassination.",
        "role": "Stealth DPS and utility - traps, poisons, reconnaissance.",
        "abilities": [
            "Sneak - turn nearly invisible, making yourself much harder to hit",
            "Ambush - burst from hiding to start a fight with a guaranteed bonus on your first strike",
            "Backstab - bonus damage against a target who hasn't yet acted",
        ],
        "gear_desc": "Leather jerkin, daggers, utility kit (lockpicks, disguise), light wraps and sandals - no shield",
        "stat_mods": {"virtus": 0, "agilitas": 3, "ingenium": 0, "vigor": 0},
        "starting_gear": [
            "DAGGER",
            "LEATHERARMOR",
            "PILEUS",
            "FASCIA_BRACHII",
            "CHIROTHECAE",
            "FEMINALIA",
            "SOLEAE",
        ],
        "starting_spells": [],
        "starting_skills": ["sneak"],
    },
    "venator": {
        "display": "Venator (Medium - Ranger/Hunter)",
        "color": "|321",
        "quote": '"The frontier doesn\'t care how brave you are. It only cares if you\'re paying attention."',
        "theme": "Frontier hunters and trackers who patrol the wild boundaries of the empire.",
        "role": "Ranged DPS and control - tracking, traps, and animal companions.",
        "abilities": [
            "Mark - lowers a target's accuracy for a short time",
            "Piercing Shot - an armor-ignoring ranged strike",
            "Call of the Wild - summon a beast companion that scales with your level",
        ],
        "gear_desc": "Leather mail (light), hunting javelins, bronze helm, arm-guard, gloves, greaves, boots - no shield",
        "stat_mods": {"virtus": 1, "agilitas": 2, "ingenium": 0, "vigor": 0},
        "starting_gear": [
            "JAVELIN",
            "LEATHERARMOR",
            "GALEA",
            "MANICA",
            "FASCIA_MANUS",
            "OCREA",
            "CALIGAE",
        ],
        "starting_spells": [],
        "starting_skills": ["mark"],
    },
    "gladiator": {
        "display": "Gladiator (Medium - Arena Fighter)",
        "color": "|530",
        "quote": '"The crowd remembers a good death. I intend to give them a good life instead - mine."',
        "theme": "Trained combatants of the arena; versatile weapon specialists who survive by skill and showmanship.",
        "role": "Versatile midline fighter - crowd control, showy finishers, weapon specializations.",
        "abilities": [
            "Feint - lowers a target's accuracy for a short time",
            "Gory Finish - a real execute against targets already below 20% HP",
            "Riposte - the next hit you take triggers an immediate counter-attack",
        ],
        "gear_desc": "Scale armor (medium), broadsword, bronze-faced clipeus shield, helm, arm-guard, gloves, greaves, boots",
        "stat_mods": {"virtus": 2, "agilitas": 1, "ingenium": 0, "vigor": 0},
        "starting_gear": [
            "BROADSWORD",
            "SCALEMAIL",
            "CLIPEUS",
            "GALEA",
            "MANICA",
            "FASCIA_MANUS",
            "OCREA",
            "CALIGAE",
        ],
        "starting_spells": [],
        "starting_skills": ["feint"],
    },
    "legionary": {
        "display": "Legionary (Heavy - Tank)",
        "color": "|224",
        "quote": '"I am one shield in a wall of shields. Alone I am nothing. Together, we do not break."',
        "theme": "The disciplined core of Rome's armies; masters of formation and defense.",
        "role": "Tank and group protector - shields, stances, formation-based buffs.",
        "abilities": [
            "Hold the Line - grants a temporary defense boost",
            "Testudo - forms a shield wall, granting your whole party a defense boost at once",
            "Gladius Cleave - a close-range cleave striking up to three enemies at once",
        ],
        "gear_desc": "Heavy plate mail, broadsword, scutum (large shield), plumed helm, vambrace, gauntlets, greaves, hobnailed boots",
        "stat_mods": {"virtus": 0, "agilitas": 0, "ingenium": 0, "vigor": 3},
        "starting_gear": [
            "BROADSWORD",
            "PLATEMAIL",
            "SCUTUM",
            "CASSIS",
            "BRACHIALE",
            "MANICA_FERRATA",
            "OCREA_FERRATA",
            "CALIGAE_FERRATAE",
        ],
        "starting_spells": [],
        "starting_skills": ["hold the line"],
    },
    "barbarian": {
        "display": "Barbarian (Heavy - Berserker/Heavy Fighter)",
        "color": "|400",
        "quote": '"Rome calls it savagery. I call it honesty. My sword does not pretend to be anything other than what it is."',
        "theme": "Non-Roman heavy fighters from the frontiers - savage, powerful, and less disciplined but devastating in open combat.",
        "role": "Heavy DPS and disruption - rage mechanics, area bursts, and raw power.",
        "abilities": [
            "Rage of the North - grants a damage boost at the cost of your own defense",
            "Thundering Maul - a heavy strike that requires a two-handed weapon in hand",
            "War Cry - lowers the accuracy of up to three enemies at once",
        ],
        "gear_desc": "Mixed scale and hide armor, two-handed greatsword, plumed helm, vambrace, gauntlets, greaves, hobnailed boots - no shield, both hands are full",
        "stat_mods": {"virtus": 3, "agilitas": 0, "ingenium": 0, "vigor": 0},
        "starting_gear": [
            "GREATSWORD",
            "SCALEMAIL",
            "CASSIS",
            "BRACHIALE",
            "MANICA_FERRATA",
            "OCREA_FERRATA",
            "CALIGAE_FERRATAE",
        ],
        "starting_spells": [],
        "starting_skills": ["rage of the north"],
    },
}

_CLASS_ORDER = ["augur", "medicus", "haruspex", "speculator", "venator", "gladiator", "legionary", "barbarian"]


#########################################################
#                   Welcome Page
#########################################################


def menunode_welcome(caller):
    """Starting page."""
    text = dedent(
        """\
        |Y=====================================================|n
        |YBefore you stands the threshold of a new life|n
        |Y=====================================================|n

        Somewhere between the |rSenate|n and the |rarena|n, the |gfrontier|n
        and the |mshadowed places|n between, a life is waiting that has not
        yet been lived. You are about to decide whose.

        What you are, what you have become skilled at, and what you will
        be called - three questions, three answers, and Rome will have a
        new name to reckon with. You may pause this journey at any point
        and take it up again later with |wcharcreate|n.
        """
    )
    help = "You can explain the commands for exiting and resuming more specifically here."
    options = {"desc": "Let the Fates begin their work", "goto": "menunode_choose_race"}
    return (text, help), options


#########################################################
#                   Choose Race
#########################################################


def menunode_choose_race(caller, raw_string="", **kwargs):
    """List of races to learn about and choose from."""
    caller.new_char.db.chargen_step = "menunode_choose_race"

    text = _step_header("menunode_choose_race") + dedent(
        """\
        |YThe Fates weigh what you are|n

        Before a name, before a purpose, comes the flesh you were born
        into - or the shape fate carved for you instead. These are
        starting templates, not a cage: roleplay can, and should, exceed
        what a mechanical label promises. Choose one to hear what it says
        of itself.
        """
    )
    help = "Race affects your HP/MP/SP starting bonuses and gives you flavor abilities."
    options = []
    for i, race_key in enumerate(_RACE_ORDER, start=1):
        race = RACES[race_key]
        options.append(
            _numbered_option(
                i,
                "%s%s|n" % (race.get("color", ""), race["display"]),
                ("menunode_race_info", {"race_key": race_key}),
            )
        )
    return (text, help), options


def menunode_race_info(caller, raw_string="", race_key=None, **kwargs):
    """Detail page for a single race, with the option to select it."""
    if not race_key or race_key not in RACES:
        caller.new_char.db.chargen_step = "menunode_choose_race"
        return "Something went wrong. Please try again.", None

    race = RACES[race_key]
    color = race.get("color", "")

    traits_str = ", ".join(race["traits"])
    abilities_str = _format_abilities(race["abilities"])

    # A real, previously-reported bug: interpolating race["desc"] (which
    # carries its own trailing newline - see RACES's own dedent() calls)
    # or abilities_str (whose own lines are indented to match
    # _format_abilities' own single-leading-space convention, not this
    # function's 8-space source-code indentation) INSIDE a dedent()
    # call breaks dedent's own common-prefix calculation - it computes
    # the SMALLEST indentation across every line of the *final*,
    # already-interpolated string, so any interpolated line with a
    # different indentation than this template's own literal lines
    # drags that minimum down, leaving the template's own lines
    # under-stripped. Fixed by building each interpolated, multi-line
    # piece as its own already-clean unit, concatenated after dedent()
    # has already run on the plain template around it - not (mis)dedented
    # together with them.
    text = (
        _step_header("menunode_race_info")
        + dedent(
            f"""\
            {color}{race["display"]}|n

            |c{race["desc"].strip()}|n

            |x{race.get("quote", "")}|n

            |wNature:|n |g{traits_str}|n

            |wGifts:|n
            """
        )
        + abilities_str
        + "\n"
    )
    help = "Choose this race to move on, or go back to browse the others."

    options = [
        {
            "desc": f"Become a {race['display']}",
            "goto": (_set_race, {"race_key": race_key}),
        },
        {
            "key": ("(Back)", "back", "b"),
            "desc": "See other races",
            "goto": "menunode_choose_race",
        },
    ]
    return (text, help), options


def _set_race(caller, raw_string="", race_key=None, **kwargs):
    if not race_key:
        return "menunode_choose_race"

    char = caller.new_char
    race = RACES[race_key]

    char.db.race = race_key
    char.db.race_display = race["display"]
    # Store abilities as flavor text for now - see module docstring.
    char.db.race_abilities = race["abilities"]

    return "menunode_choose_class"


#########################################################
#                   Choose Class
#########################################################


def menunode_choose_class(caller, raw_string="", **kwargs):
    """List of classes to learn about and choose from."""
    caller.new_char.db.chargen_step = "menunode_choose_class"

    text = _step_header("menunode_choose_class") + dedent(
        """\
        |YThe path you will walk|n

        What you are is settled. What you will spend your life doing is
        not - that is a discipline, a craft, a role earned through
        training rather than birth. Roleplay, background, and your own
        choices will define you well beyond any mechanical label.
        """
    )
    help = "Class determines your starting gear and any spells you begin knowing."
    options = []
    for i, class_key in enumerate(_CLASS_ORDER, start=1):
        pclass = CLASSES[class_key]
        options.append(
            _numbered_option(
                i,
                "%s%s|n" % (pclass.get("color", ""), pclass["display"]),
                ("menunode_class_info", {"class_key": class_key}),
            )
        )
    options.append(
        {
            "key": ("(Back)", "back", "b"),
            "desc": "Go back and change your race",
            "goto": "menunode_choose_race",
        }
    )
    return (text, help), options


def menunode_class_info(caller, raw_string="", class_key=None, **kwargs):
    """Detail page for a single class, with the option to select it."""
    if not class_key or class_key not in CLASSES:
        caller.new_char.db.chargen_step = "menunode_choose_class"
        return "Something went wrong. Please try again.", None

    pclass = CLASSES[class_key]
    color = pclass.get("color", "")
    abilities_str = _format_abilities(pclass["abilities"])

    # Same real bug and same fix as menunode_race_info above -
    # abilities_str's own lines (single-leading-space, per
    # _format_abilities) can't be interpolated inside this template's
    # own dedent() call without dragging its common-prefix calculation
    # down and under-stripping every other line in the template.
    text = (
        _step_header("menunode_class_info")
        + dedent(
            f"""\
            {color}{pclass["display"]}|n

            |wTheme:|n |c{pclass["theme"]}|n
            |wRole:|n |g{pclass["role"]}|n

            |x{pclass.get("quote", "")}|n

            |wGifts:|n
            """
        )
        + abilities_str
        + "\n\n"
        + dedent(
            f"""\
            |wEquipped for War:|n {pclass["gear_desc"]}
            """
        )
    )
    help = "Choose this class to move on, or go back to browse the others."

    options = [
        {
            "desc": f"Become {'an' if pclass['display'][0] in 'AEIOU' else 'a'} {pclass['display']}",
            "goto": (_set_class, {"class_key": class_key}),
        },
        {
            "key": ("(Back)", "back", "b"),
            "desc": "See other classes",
            "goto": "menunode_choose_class",
        },
    ]
    return (text, help), options


def _set_class(caller, raw_string="", class_key=None, **kwargs):
    if not class_key:
        return "menunode_choose_class"

    char = caller.new_char
    pclass = CLASSES[class_key]

    char.db.player_class = class_key
    char.db.class_display = pclass["display"]
    # Store abilities as flavor text for now - see module docstring.
    char.db.class_abilities = pclass["abilities"]

    # Gentle, informational-only heads-up specifically when a
    # physical-leaning race pairs with a caster class or vice versa -
    # the genuinely notable kind of mismatch, not ordinary variation
    # within the physical stats. Never blocks the choice, just makes
    # the trade-off visible up front instead of a player discovering
    # it confused a few levels in. See _leans_caster above.
    race_key = char.db.race
    if race_key and race_key in RACES:
        race_caster = _leans_caster(RACES[race_key]["stat_mods"])
        class_caster = _leans_caster(pclass["stat_mods"])
        if race_caster is not None and class_caster is not None and race_caster != class_caster:
            if class_caster:
                note = (
                    "{race}'s natural strengths lean physical rather than magical - "
                    "{pclass} will still work, you'll just be playing a bit against "
                    "type as a spellcaster."
                )
            else:
                note = (
                    "{race}'s natural strengths lean magical rather than physical - "
                    "{pclass} will still work, you'll just be playing a bit against "
                    "type physically."
                )
            caller.msg(
                "|y(A quick note: "
                + note.format(race=RACES[race_key]["display"], pclass=pclass["display"])
                + " Nothing wrong with that combination, just worth knowing.)|n"
            )

    return "menunode_choose_gender"


#########################################################
#                  Choosing a Gender
#########################################################


def menunode_choose_gender(caller, raw_string="", **kwargs):
    """Gender selection - used for pronouns and the default mask description."""
    caller.new_char.db.chargen_step = "menunode_choose_gender"

    text = _step_header("menunode_choose_gender") + dedent(
        """\
        |YA matter of birth|n

        Before Rome knows your name, it will know how to speak of you -
        the small, constant thing that shapes every sentence said about
        you from here on. This is used for pronouns and for how you're
        described by default, before you set anything more specific
        yourself.
        """
    )
    help = "You can always change this later, and it never restricts race or class choice."
    options = [
        _numbered_option(1, "Male", (_set_gender, {"gender": "male"})),
        _numbered_option(2, "Female", (_set_gender, {"gender": "female"})),
        _numbered_option(3, "Neuter", (_set_gender, {"gender": "neuter"})),
    ]
    return (text, help), options


def _set_gender(caller, raw_string="", gender=None, **kwargs):
    char = caller.new_char
    char.db.gender = gender or "neuter"

    # If charcreate <name> = <desc> already provided a real, available
    # name, world/character_creator.py's ContribCmdCharCreate sets
    # this exact flag - skip the otherwise-redundant name prompt and
    # go straight to confirming it. Checking an explicit flag set at
    # the moment the name was actually validated, rather than trying
    # to infer this after the fact from what the key looks like.
    if char.db.chargen_prefilled_name:
        return "menunode_confirm_name"
    return "menunode_choose_name"


#########################################################
#                Choosing a Name
#########################################################


def menunode_choose_name(caller, raw_string="", **kwargs):
    """Name selection"""
    char = caller.new_char
    char.db.chargen_step = "menunode_choose_name"

    if error := kwargs.get("error"):
        prompt_text = f"{error}. What name will you offer instead?"
    else:
        prompt_text = "Speak the name you would be known by, and Rome will listen."

    text = _step_header("menunode_choose_name") + dedent(
        f"""\
        |YName yourself|n

        A name is the one thing even the gods cannot choose for you.

        |c{prompt_text}|n
        """
    )

    help = "You'll have a chance to change your mind before confirming, even if the name is free."
    options = {"key": "_default", "goto": _check_charname}
    return (text, help), options


def _check_charname(caller, raw_string="", **kwargs):
    """Check and confirm name choice"""
    charname = raw_string.strip()
    charname = caller.account.normalize_username(charname)

    candidates = Character.objects.filter_family(db_key__iexact=charname)
    if len(candidates):
        return (
            "menunode_choose_name",
            {
                "error": f"|rThe name {charname} is already borne by someone else in "
                f"Rome|n.\n\nEnter a different name."
            },
        )
    else:
        caller.new_char.key = charname
        return "menunode_confirm_name"


def menunode_confirm_name(caller, raw_string="", **kwargs):
    """Confirm the name choice"""
    char = caller.new_char

    text = _step_header("menunode_confirm_name") + (
        f"The name |Y{char.key}|n is yet unclaimed in Rome's records. "
        f"Will you bear it?"
    )
    options = [
        {"key": ("Yes", "y"), "goto": "menunode_end"},
        {"key": ("No", "n"), "goto": _reject_name},
    ]
    return text, options


def _reject_name(caller, raw_string="", **kwargs):
    """
    Handles 'No' at the confirm-name step - resets the character's
    key back to the account default, so menunode_choose_name (a
    genuine, always-shown prompt now, no skip-logic of its own)
    starts clean for picking something different.
    """
    caller.new_char.key = caller.account.key
    return "menunode_choose_name"


#########################################################
#                     The End
#########################################################


def _apply_race_and_class(character):
    """
    Applies the mechanical effects of the chosen race and class:
    stat bonuses, starting gear, and starting spells. Called once,
    at the end of chargen.
    """
    race_key = character.db.race
    class_key = character.db.player_class

    # --- Race: apply stat bonuses on top of CombatCharacter's base stats ---
    if race_key and race_key in RACES:
        mods = RACES[race_key]["stat_mods"]
        character.db.max_hp += mods["max_hp"]
        character.db.max_mp += mods["max_mp"]
        character.db.max_sp += mods["max_sp"]
        character.db.virtus += mods.get("virtus", 0)
        character.db.agilitas += mods.get("agilitas", 0)
        character.db.ingenium += mods.get("ingenium", 0)
        character.db.vigor += mods.get("vigor", 0)

    # --- Class: apply its own core stat bonuses on top of race's ---
    if class_key and class_key in CLASSES:
        class_mods = CLASSES[class_key].get("stat_mods", {})
        character.db.virtus += class_mods.get("virtus", 0)
        character.db.agilitas += class_mods.get("agilitas", 0)
        character.db.ingenium += class_mods.get("ingenium", 0)
        character.db.vigor += class_mods.get("vigor", 0)

    # --- Derived: Vigor and Ingenium each feed a small amount into Max
    # HP/MP, on top of the flat race modifiers above - a character who
    # ends up with high Vigor (Cyclops Legionary, say) should end up
    # tankier than the flat race number alone would suggest.
    character.db.max_hp += (character.db.vigor - 10) * 2
    character.db.max_mp += (character.db.ingenium - 10) * 2
    character.db.hp = character.db.max_hp
    character.db.mp = character.db.max_mp
    character.db.sp = character.db.max_sp

    # --- Class: starting spells known ---
    if class_key and class_key in CLASSES:
        for spell_name in CLASSES[class_key]["starting_spells"]:
            if spell_name not in character.db.spells_known:
                character.db.spells_known.append(spell_name)

        # --- Class: starting skills known (non-caster classes) ---
        for skill_name in CLASSES[class_key].get("starting_skills", []):
            if skill_name not in character.db.skills_known:
                character.db.skills_known.append(skill_name)

        # --- Class: starting gear, spawned and auto-equipped ---
        # Local import: world/combat.py has its own deferred import of
        # RACES/CLASSES from this module (to avoid a circular import at
        # module-load time) - mirroring that same caution here rather
        # than importing combat.py at the top of this file.
        from world.combat import (
            ARMOR_SLOT_ATTRS,
            apply_equipment_bonuses,
            compute_weapon_stats,
            compute_armor_stats,
        )

        # Weapons and body armor now get their stats from the level-
        # scaled formula instead of each prototype's static hardcoded
        # values, but pinned to a fixed level rather than the
        # character's real starting level (1) - solving backward
        # against every existing weapon/armor's real stats showed
        # today's starting gear already corresponds to roughly level
        # 3-5 under the formula (every category landed in that same
        # band independently), so spawning at the character's actual
        # level 1 would be a real, unintended nerf nobody asked for.
        # Level 4 keeps chargen's power level exactly where it already
        # was - shields and accessories are untouched, they were never
        # part of the level-formula system to begin with.
        CHARGEN_GEAR_LEVEL = 4

        for prototype_name in CLASSES[class_key]["starting_gear"]:
            try:
                obj = spawn(prototype_name)[0]
                # spawn()'s location kwarg is unreliable - move explicitly.
                obj.move_to(character, quiet=True)
                # Auto-equip: weapons get wielded; armor/shields/
                # accessories go into whichever slot their own
                # db.armor_slot names (defaults to "body" if unset).
                if obj.is_typeclass("world.combat.CombatWeapon", exact=True):
                    damage_range, accuracy_bonus, price = compute_weapon_stats(
                        obj.db.weapon_type_name, CHARGEN_GEAR_LEVEL
                    )
                    obj.db.damage_range = damage_range
                    obj.db.accuracy_bonus = accuracy_bonus
                    obj.db.price = price
                    obj.db.item_level = CHARGEN_GEAR_LEVEL
                    character.db.wielded_weapon = obj
                elif obj.is_typeclass("world.combat.CombatArmor", exact=True):
                    slot = obj.db.armor_slot or "body"
                    if slot == "body":
                        reduction, defense_modifier, price = compute_armor_stats(
                            obj.db.armor_category, CHARGEN_GEAR_LEVEL
                        )
                        obj.db.damage_reduction = reduction
                        obj.db.defense_modifier = defense_modifier
                        obj.db.price = price
                        obj.db.item_level = CHARGEN_GEAR_LEVEL
                    setattr(character.db, ARMOR_SLOT_ATTRS[slot], obj)
                    apply_equipment_bonuses(character, obj)
            except Exception:
                # Prototype not found (e.g. a class references gear that
                # hasn't been built yet) - skip it rather than crash
                # character creation. Check world/prototypes.py to add it.
                character.msg(
                    "|y(Note: starting gear '%s' isn't set up yet - ask staff.)|n" % prototype_name
                )

        # Accessory gear above may have raised max_hp/max_mp/max_sp after
        # they were already set to full a few lines up - re-sync so a
        # freshly created character always starts at full health/mana/
        # stamina, not below the new (higher) max.
        character.db.hp = character.db.max_hp
        character.db.mp = character.db.max_mp
        character.db.sp = character.db.max_sp

    # --- Default sdesc: "a female cyclops" instead of the generic
    # rpsystem fallback ("a normal person"), built from the actual
    # race and gender chosen. Still fully player-changeable later via
    # the normal sdesc command - this just sets a sensible starting
    # point instead of a bland placeholder. Uses execute_cmd rather
    # than touching the sdesc handler's storage directly, so this is
    # guaranteed to go through the exact same mechanism the sdesc
    # command itself uses.
    if race_key:
        gender = character.db.gender or "neuter"
        if gender == "male":
            default_sdesc = "a male %s" % race_key
        elif gender == "female":
            default_sdesc = "a female %s" % race_key
        else:
            default_sdesc = "a %s" % race_key
        character.execute_cmd("sdesc %s" % default_sdesc)

    # --- Default title: an in-character marker of being fresh out of
    # the holding cells, rather than starting with no title at all.
    # "the Untested" reads as a real gladiator-world title (unproven in
    # the arena yet) rather than an out-of-character "new player" label
    # - fully player-changeable afterward via the normal 'title'
    # command, same as sdesc above.
    character.db.custom_title = "the Untested"

def menunode_end(caller, raw_string=""):
    """End-of-chargen cleanup."""
    char = caller.new_char

    _apply_race_and_class(char)

    char.attributes.remove("chargen_step")

    race_display = char.db.race_display or "Unknown"
    class_display = char.db.class_display or "Unknown"
    race_data = RACES.get(char.db.race, {})
    class_data = CLASSES.get(char.db.player_class, {})
    race_color = race_data.get("color", "|c")
    class_color = class_data.get("color", "|c")

    # A direct request for the single moment in chargen that most
    # deserves real weight - this used to be the flattest page of all
    # of them, a plain "Congratulations" banner, despite being the one
    # actual rite-of-passage moment in the whole sequence.
    text = dedent(
        f"""\
        |Y=====================================================|n
        |YIt is done.|n
        |Y=====================================================|n

        The name |Y{char.key}|n is entered into Rome's records, and will
        not be struck from them again while you draw breath. Let it be
        known: {race_color}{race_display}|n by birth, {class_color}{class_display}|n
        by craft - two truths that will follow you through every gate,
        every arena, every threshold still ahead.

        |gHP:|n {char.db.hp}/{char.db.max_hp}  |cMP:|n {char.db.mp}/{char.db.max_mp}  |ySP:|n {char.db.sp}/{char.db.max_sp}

        |YA tip before you go:|n other players may be online right now, even
        if you can't see them from here. Type |wpublic <message>|n at any
        time to talk to everyone connected - a simple "hello!" is a great
        way to start. If nobody answers right away, that's alright too -
        try |wwho|n to see who's around, and give it a little time.

        Rome has stood a thousand years. It will stand for however long
        you decide to matter to it. |YWelcome, {char.key}. Walk well.|n
        """
    )

    # WelcomeCellRoom normally fires the cell-arrival orientation via
    # at_object_receive - but a character's very first location is
    # set as part of creation itself, not a real move, so that
    # movement hook never actually fires for a brand-new character.
    # Triggering it explicitly here guarantees it happens regardless,
    # rather than depending on hook timing that doesn't apply yet.
    if not char.db.seen_cell_intro:
        char.db.seen_cell_intro = True
        from typeclasses.rooms import _send_cell_intro
        _send_cell_intro(char)

    return text, None