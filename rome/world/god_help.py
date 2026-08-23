"""
God/pantheon help entries

A one-time setup script creating in-game help topics for the RP
expectations around gods (level 101+ characters) and for the Roman
pantheon itself - one entry per deity. Kept separate from
world/help_setup.py (races/classes/stats) since this is lore/RP
content rather than character-build reference material, but follows
the exact same pattern: managed keys get deleted and recreated on
every run, so re-running after an edit never leaves stale duplicates.

Run this once, in-game, as Developer/superuser:

    py from world.god_help import create_god_help_entries; create_god_help_entries()
"""

from evennia.help.models import HelpEntry


PANTHEON = {
    "jupiter": (
        "Jupiter",
        "King of the gods, master of sky and thunder. Jupiter's word is law on "
        "Olympus as much as it is in the Senate he's said to favor - Rome's own "
        "authority is supposed to be a reflection of his. He rarely intervenes "
        "directly; when he does, no one mistakes it for anything less than the "
        "sky itself taking notice. Sacred animal: the eagle. Symbol: the "
        "thunderbolt. Roman equivalent of the Greek Zeus.",
        "King of the Sky",
    ),
    "juno": (
        "Juno",
        "Queen of the gods, protector of the Roman state and guardian of women "
        "and marriage. Where Jupiter rules by force, Juno rules by will - "
        "watchful, exacting, and not easily crossed. Rome's mint once stood in "
        "her temple precinct; to this day 'moneta,' the root of 'money' itself, "
        "carries her name. Sacred animal: the peacock. Roman equivalent of the "
        "Greek Hera.",
        "Queen of the Gods",
    ),
    "neptune": (
        "Neptune",
        "Lord of the sea, and by extension of horses, earthquakes, and every "
        "sailor's fate the moment they leave sight of shore. Rome was never a "
        "purely seafaring people the way the Greeks were, but no fleet left "
        "port, and no general crossed water to fight a war, without a prayer "
        "left for Neptune first. Symbol: the trident. Roman equivalent of the "
        "Greek Poseidon.",
        "Lord of the Sea",
    ),
    "minerva": (
        "Minerva",
        "Goddess of wisdom, strategy, and craft - not the chaos of battle "
        "itself, but the calculation that wins it. Patron of artisans, "
        "weavers, and anyone whose skill is sharpened by thought rather than "
        "muscle. Said to have sprung fully formed and fully armed from "
        "Jupiter's own skull. Sacred animal: the owl. Roman equivalent of the "
        "Greek Athena.",
        "Goddess of Wisdom",
    ),
    "mars": (
        "Mars",
        "God of war - but war as Rome understood it: disciplined, purposeful, "
        "and glorious rather than simply savage. Second only to Jupiter in "
        "the honor paid him, and with good reason: Roman legend holds that "
        "Mars himself fathered Romulus, the city's founder. Every legion that "
        "ever marched carried his favor as much as its own standards. Sacred "
        "animal: the wolf. Roman equivalent of the Greek Ares.",
        "God of War",
    ),
    "venus": (
        "Venus",
        "Goddess of love, beauty, and desire - and, through Aeneas, the "
        "divine ancestor the Julian family (and by extension, Rome itself) "
        "claimed descent from. Far more politically significant in Rome than "
        "her Greek counterpart ever was in Athens; more than one general has "
        "built her a temple in gratitude for a battle he was certain her "
        "favor decided. Roman equivalent of the Greek Aphrodite.",
        "Goddess of Love",
    ),
    "ceres": (
        "Ceres",
        "Goddess of the harvest, grain, and the fertility of the earth "
        "itself. Rome's grain dole - the free bread that has kept more than "
        "one crowd from rioting - is, in the truest sense, her gift "
        "administered by mortal hands. Her festival, the Cerealia, marks the "
        "turning of the agricultural year. Roman equivalent of the Greek "
        "Demeter.",
        "Goddess of the Harvest",
    ),
    "diana": (
        "Diana",
        "Goddess of the hunt, the moon, and wild places untouched by the "
        "city. Fiercely independent, she answers to no husband and keeps her "
        "own company in the deep woods - a goddess for anyone who's ever felt "
        "more at home outside Rome's walls than within them. Sacred animal: "
        "the stag. Roman equivalent of the Greek Artemis.",
        "Goddess of the Hunt",
    ),
    "vulcan": (
        "Vulcan",
        "God of fire, the forge, and every craftsman who works metal for a "
        "living. Lame from birth (or from a fall from Olympus, depending who "
        "tells it) and married to Venus herself - a match as mismatched as "
        "any in the old stories. Every weapon carried into the arena, and "
        "every legion's steel, is said to owe him something. Roman "
        "equivalent of the Greek Hephaestus.",
        "God of the Forge",
    ),
    "mercury": (
        "Mercury",
        "Messenger of the gods, and patron of merchants, travelers, and - "
        "less flatteringly - thieves. Quick-tongued and quicker on his feet, "
        "the one god equally comfortable in the Forum's marketplace stalls "
        "and at Jupiter's own side. Symbol: the winged sandal. Roman "
        "equivalent of the Greek Hermes.",
        "Messenger of the Gods",
    ),
    "bacchus": (
        "Bacchus",
        "God of wine, festivity, and the loosening of ordinary restraint. "
        "Worship of Bacchus has always run a little wilder than the rest of "
        "the pantheon's - the Senate itself once moved to restrict his "
        "rites when they grew too unruly for the city's comfort. Sacred "
        "plant: the grapevine. Roman equivalent of the Greek Dionysus.",
        "God of Wine",
    ),
    "pluto": (
        "Pluto",
        "Lord of the Underworld and of the dead who dwell there - not cruel "
        "so much as simply final, presiding over a realm where every debt "
        "comes due and no rank buys an exception. Rarely named aloud without "
        "cause; Romans have always preferred to speak of the dead's realm "
        "obliquely rather than summon its master's attention directly. "
        "Roman equivalent of the Greek Hades.",
        "Lord of the Underworld",
    ),
    "vesta": (
        "Vesta",
        "Goddess of the hearth, home, and the sacred fire of Rome itself - "
        "tended without interruption by the Vestal Virgins in the Forum, "
        "since a single night of that flame going dark is said to threaten "
        "the city's very survival. The quietest of the pantheon, and in some "
        "ways the most load-bearing: Rome's household gods all answer, in "
        "the end, to her. Roman equivalent of the Greek Hestia.",
        "Goddess of the Hearth",
    ),
}


def create_god_help_entries():
    managed_keys = ["god", "gods"] + list(PANTHEON.keys())

    HelpEntry.objects.filter(db_key__in=managed_keys).delete()

    gods_text = (
        "|wGods among mortals|n\n\n"
        "A character of level 101 or higher is exactly what the game calls "
        "them: a literal, living god, walking among mortals with the full "
        "weight of divine power behind them. Not a powerful adventurer, not "
        "a title - a god, the same kind of being the temples are built for "
        "and the festivals are held for.\n\n"
        "This has real, practical consequences for how you play around one:\n\n"
        "- Treat their presence as genuinely extraordinary. If a god actually "
        "appeared in front of you, you would not shrug it off - you would "
        "feel it. React that way. Reverence, awe, fear, desperate hope for "
        "favor - whatever fits your character, but not indifference.\n"
        "- Their word carries weight your character has no standing to "
        "casually dismiss. Rudeness to a god should feel like a real risk "
        "your character is taking, not a throwaway line.\n"
        "- A god's power is not roleplay flavor - it's real. Slay, "
        "resurrection, teleportation with a signature arrival no mortal can "
        "fake - these aren't things to argue with in-character; they are "
        "simply what a god can do.\n\n"
        "Use |whelp god's name|n (e.g. |wjupiter|n, |wpluto|n) to read about "
        "each member of the pantheon specifically - which domain they hold, "
        "and what a scene with them might reasonably feel like."
    )

    HelpEntry.objects.create(
        db_key="god",
        db_help_category="Lore",
        db_entrytext=gods_text,
        db_lock_storage="view:all()",
    )
    HelpEntry.objects.create(
        db_key="gods",
        db_help_category="Lore",
        db_entrytext=gods_text,
        db_lock_storage="view:all()",
    )

    for key, (display, desc, domain) in PANTHEON.items():
        text = "|w%s|n - %s\n\n%s" % (display, domain, desc)
        HelpEntry.objects.create(
            db_key=key,
            db_help_category="Lore",
            db_entrytext=text,
            db_lock_storage="view:all()",
        )
