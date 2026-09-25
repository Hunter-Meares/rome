"""
Help entry setup

A one-time setup script that creates in-game help topics for every
race, class, and core stat - pulling content directly from the RACES
and CLASSES dicts in world/chargen_menu.py rather than duplicating
that text by hand, so the help files can never drift out of sync with
what chargen actually shows.

Run this once, in-game, as Developer/superuser:

    py from world.help_setup import create_all_help_entries; create_all_help_entries()

Safe to re-run any time content changes - it deletes and recreates
every entry it manages, rather than leaving stale duplicates behind.
"""

from evennia.help.models import HelpEntry

from world.chargen_menu import RACES, CLASSES
from world.factions import FACTIONS


STAT_HELP = {
    "virtus": (
        "Virtus (Strength)",
        "Raw physical power. Virtus adds directly to damage dealt with "
        "melee and heavy weapons - swords, axes, mauls, spears, anything "
        "that isn't a bow or a light blade. High-Virtus characters hit "
        "hard in close combat. It has no effect on spellcasting or "
        "ranged weapons.",
    ),
    "agilitas": (
        "Agilitas (Agility)",
        "Speed, precision, and reflexes. Agilitas affects four separate "
        "things: your accuracy in combat, your defense (how hard you are "
        "to hit), your initiative (how likely you are to act early in a "
        "fight), and your damage with ranged weapons and light blades "
        "specifically (daggers, gladii, bows, javelins). It's the closest "
        "thing to an all-purpose combat stat in the game.",
    ),
    "ingenium": (
        "Ingenium (Intelligence)",
        "Magical aptitude. Ingenium increases both the accuracy and the "
        "power of your spells - damage spells hit harder, healing spells "
        "restore more. It has no effect on physical weapon damage or "
        "SP-based skills. Only casters (Augur, Medicus, Haruspex) get "
        "much practical benefit from investing in this.",
    ),
    "vigor": (
        "Vigor (Constitution)",
        "Physical toughness and endurance. Vigor grants a small amount of "
        "bonus Max HP on top of your race and class's normal total, and "
        "provides a flat reduction to incoming damage, independent of "
        "and in addition to whatever armor you're wearing. High-Vigor "
        "characters are simply harder to bring down.",
    ),
}


def _format_stat_mods(mods):
    """Turns a stat_mods dict into a readable one-line summary, skipping zeros."""
    labels = {
        "virtus": "Virtus", "agilitas": "Agilitas",
        "ingenium": "Ingenium", "vigor": "Vigor",
    }
    parts = []
    for key, label in labels.items():
        val = mods.get(key, 0)
        if val:
            sign = "+" if val > 0 else ""
            parts.append("%s%d %s" % (sign, val, label))
    return ", ".join(parts) if parts else "No core stat bonuses."


def create_all_help_entries():
    from world.racial_abilities import RACIAL_ABILITIES

    managed_keys = (
        list(RACES.keys())
        + list(CLASSES.keys())
        + list(STAT_HELP.keys())
        + ["races", "classes", "corestats", "statup", "sp", "groupcombat", "gold", "bounty", "quest", "godbounty", "godquest", "religion", "godreligion", "titles", "pacifism", "godpacifism", "gathering", "crafting", "faber", "herbalist", "recall", "beyond the walls", "newbie", "trade", "achievements", "languages", "trainers", "pvp", "mailsystem", "factions", "targeting", "death", "dismiss", "roleplay", "description", "rules", "racial", "shortcuts", "beseech", "armor", "naming", "trivia", "pets", "buypet", "row", "socials"]
        + [skill for data in FACTIONS.values() for skill in data["skills"]]
        + list(RACIAL_ABILITIES.keys())
    )

    # Clean slate for anything this script manages, so re-running it
    # after content changes doesn't leave stale duplicate entries.
    HelpEntry.objects.filter(db_key__in=managed_keys).delete()

    # --- Races ---
    for race_key, data in RACES.items():
        traits = ", ".join(data.get("traits", []))
        abilities = "\n".join("  - %s" % a for a in data.get("abilities", []))
        stat_summary = _format_stat_mods(data.get("stat_mods", {}))
        text = (
            "|w%s|n\n\n"
            "%s\n\n"
            "|wTraits:|n %s\n\n"
            "|wAbilities:|n\n%s\n\n"
            "|wCore stat bonuses:|n %s"
            % (data["display"], data["desc"].strip(), traits, abilities, stat_summary)
        )
        HelpEntry.objects.create(
            db_key=race_key,
            db_help_category="Races",
            db_entrytext=text,
            db_lock_storage="view:all()",
        )

    # --- Classes ---
    for class_key, data in CLASSES.items():
        abilities = "\n".join("  - %s" % a for a in data.get("abilities", []))
        stat_summary = _format_stat_mods(data.get("stat_mods", {}))
        text = (
            "|w%s|n\n\n"
            "%s\n\n"
            "|wRole:|n %s\n\n"
            "|wSignature abilities:|n\n%s\n\n"
            "|wStarting gear:|n %s\n\n"
            "|wCore stat bonuses:|n %s\n\n"
            "See |wspellinfo|n or |wskillinfo|n in-game for this class's full ability list."
            % (
                data["display"], data["theme"], data["role"], abilities,
                data["gear_desc"], stat_summary,
            )
        )
        HelpEntry.objects.create(
            db_key=class_key,
            db_help_category="Classes",
            db_entrytext=text,
            db_lock_storage="view:all()",
        )

    # --- Core stats (individual) ---
    for stat_key, (title, body) in STAT_HELP.items():
        HelpEntry.objects.create(
            db_key=stat_key,
            db_help_category="Stats",
            db_entrytext="|w%s|n\n\n%s" % (title, body),
            db_lock_storage="view:all()",
        )

    # --- Index/overview pages ---
    race_list = "\n".join("  %s - %s" % (k, v["display"]) for k, v in RACES.items())
    HelpEntry.objects.create(
        db_key="races",
        db_help_category="Races",
        db_entrytext=(
            "|wPlayable Races|n\n\n"
            "Type 'help <race name>' for details on any of these:\n\n" + race_list
        ),
        db_lock_storage="view:all()",
    )

    class_list = "\n".join("  %s - %s" % (k, v["display"]) for k, v in CLASSES.items())
    HelpEntry.objects.create(
        db_key="classes",
        db_help_category="Classes",
        db_entrytext=(
            "|wPlayable Classes|n\n\n"
            "Type 'help <class name>' for details on any of these:\n\n" + class_list
        ),
        db_lock_storage="view:all()",
    )

    stat_list = "\n".join("  %s" % k for k in STAT_HELP.keys())
    HelpEntry.objects.create(
        db_key="corestats",
        db_help_category="Stats",
        db_entrytext=(
            "|wCore Stats|n\n\n"
            "Every character has four core stats, set at creation by your "
            "race and class and visible any time with the 'stats' command. "
            "They can also grow after chargen - see 'help statup'.\n\n"
            "Type 'help <stat name>' for details on any of these:\n\n" + stat_list
        ),
        db_lock_storage="view:all()",
    )

    # --- Post-chargen stat growth ---
    HelpEntry.objects.create(
        db_key="statup",
        db_help_category="Stats",
        db_entrytext=(
            "|wStat Growth|n\n\n"
            "Every 3rd level (3, 6, 9, ...) grants one unspent stat "
            "point. Spend it with:\n\n"
            "  statup                - see your unspent points and caps\n"
            "  statup <stat>          - virtus, agilitas, ingenium, or "
            "vigor\n"
            "  statup hp|mp|sp        - a flat resource boost instead - "
            "a real choice any time, not just once a stat is capped\n\n"
            "Every core stat has a lifetime cap. |wAgilitas caps at 18 for "
            "every race|n - it powers accuracy directly, and the math "
            "breaks down past that point (hits would start landing "
            "regardless of the roll). Virtus, ingenium, and vigor cap at "
            "20 normally, or 22 if that stat is already your race's "
            "established specialty (check 'help <race>' for your own "
            "leans)."
        ),
        db_lock_storage="view:all()",
    )

    # --- Stamina Points (SP) ---
    HelpEntry.objects.create(
        db_key="sp",
        db_help_category="Stats",
        db_entrytext=(
            "|wStamina Points (SP)|n\n\n"
            "SP fuels combat skills (see 'help useskill') - most skills "
            "cost somewhere between a handful and a couple dozen SP to "
            "use, shown on each skill's own help entry.\n\n"
            "|wSP also fuels movement itself.|n Every step you take through "
            "an exit costs 1 SP, on top of anything you spend on skills. "
            "This applies everywhere, not just in combat or on especially "
            "long roads - a short walk barely dents your pool, but "
            "crossing real distance across the city adds up. If you run "
            "out mid-journey, you won't be able to keep moving until you "
            "recover some back.\n\n"
            "Resting ('help rest') restores HP, MP, and SP together over "
            "time - if a long trip runs you dry, resting partway through "
            "is the normal way to finish it. Your current SP is always "
            "visible with 'stats'. SP grows automatically as you level, "
            "and you can put a stat point toward more of it directly - "
            "see 'help statup'.\n\n"
            "Gods and the dead are exempt from the movement cost - a god "
            "isn't bound by mortal limits, and the dead have no strength "
            "to spend in the first place (their HP/MP/SP all stay at 0 "
            "until they return to life, but they can still move freely)."
        ),
        db_lock_storage="view:all()",
    )

    # --- Group combat / sides overview ---
    HelpEntry.objects.create(
        db_key="groupcombat",
        # Deliberately "General", not "Combat" - a real bug found live:
        # Evennia's help index shows real commands (help_category from
        # each Command class) and topics like this one (db_help_category
        # here) as two entirely separate top-level sections ("Commands"
        # and "Game & World"), each independently bucketed by category
        # name with no cross-section dedup. Giving a topic the same
        # category name as a real command group (28 commands already
        # use help_category="combat") doesn't merge them - it just
        # prints "-- Combat --" twice, once per section, which reads as
        # a broken/duplicated menu to a player even though nothing was
        # actually duplicated. Matches every other standalone mechanics
        # topic (gold, trade, achievements) already filed under General.
        db_help_category="General",
        db_entrytext=(
            "|wGroup Combat & Sides|n\n\n"
            "Every fighter in a battle is on a side - who's fighting with "
            "you, and who's fighting against you. In a one-on-one duel "
            "('fight <target>' or 'challenge'), this is simple: it's just "
            "the two of you.\n\n"
            "|wWhen it gets bigger:|n\n"
            "  - 'fight all' groups everyone present by party. Your whole "
            "party fights as a single side against everyone else in the "
            "room - not as separate individuals. See 'help party' for how "
            "to form one.\n"
            "  - Joining a fight already in progress puts you on the side "
            "of any party member who's already in it. If none of your "
            "party is involved, you join as your own, independent side.\n"
            "  - Summoned allies (familiars, beasts, and similar) always "
            "fight on their summoner's side, regardless of party status.\n\n"
            "|wWhy this matters:|n\n"
            "  - A fight only ends once just one side has anyone left "
            "standing - not just one individual fighter. A full party can "
            "win together without the fight ending the moment their first "
            "ally is defeated.\n"
            "  - Area-of-effect spells and skills (and the 'enemies' "
            "target keyword) automatically avoid hitting your own side - "
            "you won't catch your own party, or your own summon, in your "
            "own AoE.\n"
            "  - |wA real party (not just two unrelated attackers) earns a "
            "20% bonus to the whole XP pool|n on a kill, on top of the "
            "usual fair split by how much damage each of you actually "
            "dealt - a genuine reason to group up, not just a wash.\n\n"
            "See 'help party' and 'help fight' for the specific commands."
        ),
        db_lock_storage="view:all()",
    )

    # --- Targeting & disambiguation ---
    HelpEntry.objects.create(
        db_key="targeting",
        db_help_category="General",
        db_entrytext=(
            "|wTargeting & Disambiguation|n\n\n"
            "Whenever you name something - 'look trainer', 'consider "
            "recruit', 'fight guard', 'cast heal = ally' - the game "
            "matches it against whatever's actually there. If more than "
            "one thing matches (three identical trainers standing "
            "together, say), the game just picks one for you rather than "
            "stopping to ask - in every case like that, it genuinely "
            "doesn't matter which one you get.\n\n"
            "|wIf you ever need a SPECIFIC one|n out of several matches, "
            "put the number first: |w2-trainer|n targets the second match "
            "for 'trainer', |w3-guard|n the third, and so on. This works "
            "anywhere you'd normally type a target's name."
        ),
        db_lock_storage="view:all()",
    )

    # --- Death, and getting back from it ---
    HelpEntry.objects.create(
        db_key="death",
        db_help_category="General",
        db_entrytext=(
            "|wDeath|n\n\n"
            "Dying works very differently depending on how far you've come.\n\n"
            "|wLevel 5 and below:|n death is gentle. The gods aren't finished "
            "with you yet - you're returned immediately to the holding cells "
            "beneath the Colosseum, fully healed, with no penalty at all. "
            "This early on, dying is a stumble, not a real setback.\n\n"
            "|wLevel 6 and above:|n death is real. Your spirit is torn away "
            "to the Underworld, arriving on the far shore of a dark river "
            "with your HP, MP, and SP all at zero - you can still walk "
            "freely, but you can't fight, cast, or use a skill until you're "
            "alive again. Dying at this stage also costs half your progress "
            "toward your next level - unless you've devoted yourself to "
            "Pluto, lord of the dead (see 'help religion'), whose favor "
            "eases that loss and, at its highest tier, removes it entirely.\n\n"
            "|wGetting back:|n\n"
            "  - |wSolve the riddle|n at the Threshold of Return, deep in "
            "the Underworld. Answer correctly and you're returned to the "
            "living immediately - no outside help needed, if you can work "
            "it out.\n"
            "  - |wA Medicus's Blessing of Asclepius|n can resurrect you "
            "directly from anywhere in the world of the living - but only "
            "once Charon has actually ferried you across, roughly 15 "
            "minutes after you die. The wait is real, not a formality; a "
            "Medicus can't reach you before Charon arrives.\n\n"
            "Once you're alive again: level 5-and-under characters wake in "
            "the holding cells, same as any early death. Level 6+ "
            "characters instead wake in the Temple of Jupiter Optimus "
            "Maximus on the Capitoline - by then, being pulled back by the "
            "king of the gods himself fits better than the cells.\n\n"
            "|wWorth knowing:|n you can't 'recall' your way out of the "
            "Underworld once you're there - the riddle and the Blessing of "
            "Asclepius are the only two ways back."
        ),
        db_lock_storage="view:all()",
    )

    # --- Roleplay enforcement ---
    roleplay_entry = HelpEntry.objects.create(
        db_key="roleplay",
        db_help_category="General",
        db_entrytext=(
            "|wRoleplay|n\n\n"
            "Rome: The Eternal City is a roleplay-enforced MUD. This isn't "
            "just a combat sandbox with a Roman coat of paint - you're "
            "expected to stay in character, speak and act as your "
            "character would, and put real effort into your poses, "
            "emotes, and dialogue. Lean on your |wsdesc|n rather than "
            "your literal character name when describing yourself - see "
            "'help description' for exactly how your description, "
            "sdesc, and mask differ, with examples.\n\n"
            "|wThe gods are watching.|n This is truer here than in most "
            "settings - the gods of Rome are not an abstraction, and they "
            "take a real, personal interest in how mortals conduct "
            "themselves. Poor roleplay, or a refusal to roleplay at all, "
            "does not go unnoticed and can draw real divine displeasure. "
            "Vivid, immersive, effortful roleplay, on the other hand, is "
            "the surest way to catch a god's favor.\n\n"
            "In short: play your part well, and Olympus may smile on you. "
            "Play it poorly, or not at all, and you may find the gods far "
            "less forgiving than the mortals around you."
        ),
        db_lock_storage="view:all()",
    )
    roleplay_entry.aliases.add("rp")

    # --- Rules ---
    HelpEntry.objects.create(
        db_key="rules",
        db_help_category="General",
        db_entrytext=(
            "|wRules & Expectations|n\n\n"
            "Rome: The Eternal City is a roleplay-enforced world, not a "
            "combat sandbox with a Roman coat of paint. These rules exist "
            "to keep that story safe, fair, and worth telling - for you, "
            "and for everyone playing it alongside you. See 'help "
            "roleplay' for what's expected of your roleplay specifically, "
            "and 'help description' for the tools (description, sdesc, "
            "mask) you'll use to actually play it.\n\n"
            "|wOne Character, One Voice|n\n"
            "Multiple characters per account are welcome - this is about "
            "playing them honestly, not about how many you keep.\n"
            "  - No multiplaying: never run two of your own characters at "
            "once to be in two places, cover both sides of a scene, or "
            "back yourself up in a fight.\n"
            "  - No self-dealing: don't trade gold or gear between your "
            "own characters, or otherwise use one to prop up another. "
            "Earn what your character has honestly.\n"
            "  - Commit to the scene: don't quietly switch characters "
            "mid-scene to change how it plays out.\n\n"
            "|wCode of Conduct|n\n"
            "  - Respect comes first: no hate speech, harassment, or "
            "discriminatory language, in character or out. Real people "
            "are on the other side of every character you meet.\n"
            "  - Honor story boundaries: respect other players' comfort "
            "levels and the boundaries they set for their characters' "
            "stories. Consent matters, especially for major or permanent "
            "plot impact.\n"
            "  - Follow staff in events: during staff-run events and "
            "conflict resolution, follow directions promptly.\n\n"
            "|wGame Mechanics & Fair Play|n\n"
            "  - No metagaming: using out-of-character knowledge to "
            "influence in-character decisions isn't fair to players who "
            "earned their information honestly.\n"
            "  - No powergaming: don't force outcomes on unwilling "
            "players. Let actions have real, contestable stakes.\n"
            "  - No cheating: macros, scripts, bots, or any other "
            "automation to play the game for you are never allowed. Play "
            "it yourself, every time.\n"
            "  - Combat has real weight: death and defeat carry real "
            "consequences that scale with your character's experience "
            "(see 'help death'). Don't expect to talk your way out of a "
            "fight's outcome after the fact.\n"
            "  - Exploits get reported, not exploited: found a bug that "
            "breaks the game in your favor? Report it rather than take "
            "advantage of it.\n\n"
            "|wEnforcement|n\n"
            "Infractions may result in warnings, temporary suspensions, "
            "or bans depending on severity. Staff decisions are made with "
            "the health of the community in mind. But staff aren't the "
            "only ones watching - poor conduct can also draw a more "
            "immediate, in-fiction response from the gods themselves. "
            "Consider both before you act."
        ),
        db_lock_storage="view:all()",
    )

    # --- Description vs. sdesc vs. mask ---
    description_entry = HelpEntry.objects.create(
        db_key="description",
        db_help_category="General",
        db_entrytext=(
            "|wDescription, Sdesc, and Mask|n\n\n"
            "These three sound similar and all change what people see "
            "about you, but they're genuinely different tools - here's "
            "exactly how, with examples.\n\n"
            "|wYour description (desc)|n\n"
            "Your physical appearance - what someone sees when they "
            "'look' directly at you by name. Set an initial one at "
            "character creation, and change it any time afterward with "
            "'setdesc'.\n"
            "  Usage: setdesc <description>\n"
            "  Example: setdesc A tall, sun-weathered gladiator, a "
            "jagged scar running the length of his jaw.\n\n"
            "|wYour sdesc (short description)|n\n"
            "The short label everyone else sees INSTEAD of your real "
            "character name - in room listings, combat messages, poses, "
            "emotes, everywhere. This is your everyday in-character "
            "identity, and you can change it any time.\n"
            "  Usage: sdesc <short description>\n"
            "  Example: sdesc a tall, sun-weathered gladiator\n"
            "  Result: others see \"A tall, sun-weathered gladiator "
            "arrives from the north\" instead of your real name.\n"
            "Note the leading 'a' in that example - the game never adds "
            "one for you, for sdesc or mask alike. Leave it out and "
            "everyone reads a grammatically broken line instead.\n"
            "Other players can give you a personal nickname with 'recog "
            "<your sdesc> as <alias>' - once they have, they'll keep "
            "seeing that alias instead of your sdesc, even if you change "
            "your sdesc later. Recognition tracks who you actually are, "
            "not your current sdesc text.\n\n"
            "|wA mask|n\n"
            "NOT just another sdesc change, even though it looks like "
            "one - a mask is a flagged, reversible disguise with real "
            "mechanical teeth. It's the one thing that actually breaks "
            "an existing 'recog' someone has on you, which a plain sdesc "
            "change never does.\n"
            "  Usage: mask <new sdesc>\n"
            "  Example: mask a hooded merchant\n"
            "  Result: \"You wear a mask as 'a hooded merchant "
            "[masked]'.\" - the '[masked]' tag is automatic, so everyone "
            "can tell you're disguised even if they can't tell who you "
            "really are. Anyone who had you recog'd stops recognizing "
            "you while masked.\n"
            "  To remove it: unmask - restores your real sdesc exactly, "
            "no need to retype it.\n\n"
            "Bottom line: description ('setdesc') is your actual "
            "physical look, sdesc is the everyday identity label others "
            "see instead of your name, and mask is a temporary, "
            "detectable disguise you put on and take back off - not a "
            "casual way to relabel yourself."
        ),
        db_lock_storage="view:all()",
    )
    description_entry.aliases.add("desc")

    # --- Pets (summoned and purchased) ---
    HelpEntry.objects.create(
        db_key="pets",
        db_help_category="General",
        db_entrytext=(
            "|wPets|n\n\n"
            "Two different ways to get a companion, with two different "
            "lifetimes:\n\n"
            "|wSummoned|n - Augur's Summon Familiar, Haruspex's Summon "
            "Lemures/Summon Fury, or Venator's Call of the Wild. Only lasts "
            "as long as the fight it was cast in - it's gone the moment you "
            "flee, are defeated, or the fight ends.\n\n"
            "|wPurchased|n - buy one outright from a pet vendor (see 'help "
            "buypet'), level 10+. A purchased pet stays with you "
            "permanently: it follows you automatically between rooms, "
            "survives you logging off and back in, and fights at your side "
            "in every fight from then on. It's only ever actually gone if "
            "it's defeated in combat (0 HP - a real, permanent loss, not "
            "something that heals back on its own) or if you 'dismiss' it "
            "yourself.\n\n"
            "You can only have one active companion at a time, of either "
            "kind - buying or summoning a new one while you already have "
            "one active is refused, not silently swapped, so a purchased "
            "pet can never be lost by accident. 'dismiss' it first if you "
            "want to switch.\n\n"
            "A pet doesn't earn you any XP or gold on its own - only "
            "damage you personally deal counts toward a kill's reward, so "
            "you'll always want to be an active part of the fight "
            "yourself, not just along for the ride.\n\n"
            "See 'help row' for how a pet standing in the front row can "
            "protect you if you fall back to the back row."
        ),
        db_lock_storage="view:all()",
    )

    HelpEntry.objects.create(
        db_key="buypet",
        db_help_category="General",
        db_entrytext=(
            "|wBuying a Pet|n\n\n"
            "Usage:\n"
            "  buypet\n"
            "  buypet <name>\n\n"
            "Buys a permanent companion pet from a pet vendor standing in "
            "the same room as you - requires level 10. With no argument, "
            "lists what that vendor currently has for sale. See 'help "
            "pets' for how a purchased pet's lifetime actually works."
        ),
        db_lock_storage="view:all()",
    )

    HelpEntry.objects.create(
        db_key="dismiss",
        db_help_category="General",
        db_entrytext=(
            "|wDismiss (or Banish) a Pet|n\n\n"
            "Usage:\n"
            "  dismiss\n"
            "  banish\n\n"
            "Sends away your active pet for good - whichever one you've "
            "currently got, summoned or purchased, since only one can be "
            "active at a time. Works anywhere, whether you're standing "
            "next to your pet or not, and whether you're in combat or out "
            "of it.\n\n"
            "|wWhat happens automatically:|n a summoned pet is also "
            "released on its own if you flee/disengage from a fight, if "
            "you're defeated, or once the fight ends - it never outlives "
            "the fight it was cast for. A purchased pet is different: "
            "fleeing or being defeated yourself just sends it home to your "
            "side, fully healed, not away for good - 'dismiss' (or the "
            "pet's own defeat in combat) is the only thing that actually "
            "gets rid of one. See 'help pets' for the full picture."
        ),
        db_lock_storage="view:all()",
    )

    # --- Front row / back row positioning ---
    HelpEntry.objects.create(
        db_key="row",
        db_help_category="General",
        db_entrytext=(
            "|wFront Row / Back Row|n\n\n"
            "Usage:\n"
            "  row\n"
            "  row front\n"
            "  row back\n\n"
            "Front (the default) means any enemy can freely target you "
            "with a basic attack or a physical skill.\n\n"
            "Back means an enemy's basic attacks and physical skills "
            "can't reach you at all, as long as at least one of your own "
            "allies (a party member, or a pet, which always starts in "
            "the front row) is still standing in the front row with you. "
            "The moment your last front-row ally falls, you become "
            "reachable again immediately - and if that ally was a pet "
            "defending you, you're automatically pulled back to the "
            "front row yourself at that same moment.\n\n"
            "This is a real, hard restriction in both directions for "
            "basic attacks and physical skills - your own attacks and "
            "skills can't reach a protected enemy either, unless you're "
            "wielding a polearm or a ranged weapon (a bow, a javelin, a "
            "spear), which have the reach to strike into the back row "
            "directly. A dagger or an unarmed attack does not.\n\n"
            "|wSpells are the one exception|n - a spell always reaches "
            "its target regardless of row, on both sides. Magic isn't "
            "constrained by who's standing where the way a physical "
            "attack is, and it's the only way a caster with no reach "
            "weapon can ever damage a protected target at all. Falling "
            "back to the back row protects you from being hit by "
            "weapons and physical skills - it does nothing against an "
            "enemy spellcaster.\n\n"
            "Can be set any time, not just mid-fight, so you can position "
            "yourself before a fight even starts."
        ),
        db_lock_storage="view:all()",
    )

    # --- Social commands (emotes) ---
    HelpEntry.objects.create(
        db_key="socials",
        db_help_category="General",
        db_entrytext=(
            "|wSocial Commands|n\n\n"
            "Usage:\n"
            "  <social>\n"
            "  <social> <target>\n\n"
            "A quick, one-word gesture or reaction - a lighter option than "
            "a full 'emote' when you just want a simple beat. Works with "
            "or without a target; targeting yourself just shows the plain, "
            "untargeted version.\n\n"
            "|wFriendly:|n smile, grin, laugh, chuckle, wave, hug, embrace, "
            "cuddle, kiss, nuzzle, pat, highfive, handshake, comfort, "
            "toast, snuggle\n\n"
            "|wPlayful:|n wink, giggle, snicker, smirk, tease, poke, "
            "tickle, nudge, flirt, dance, twirl, blush, tongue, purr\n\n"
            "|wSympathetic:|n sigh, cry, sob, weep, pout, frown, whimper, "
            "shiver, tremble, mourn, console, grieve\n\n"
            "|wHostile:|n glare, scowl, sneer, spit, snarl, growl, hiss, "
            "slap, shove, mock, scoff, snort, eyeroll, point, threaten, "
            "curse\n\n"
            "|wGestures:|n nod, headshake, shrug, salute, bow, kneel, "
            "stretch, yawn, cough, sneeze, faint, stumble, clap, cheer\n\n"
            "|wRoman-flavored:|n toga, libation, thumbsdown, thumbsup, "
            "acclaim, wardoff, evileye, auspex\n\n"
            "A handful of these (stretch, yawn, sneeze, faint, toga, "
            "wardoff, auspex) don't have a targeted form at all - they're "
            "solitary by nature."
        ),
        db_lock_storage="view:all()",
    )

    # --- Gold & the economy ---
    HelpEntry.objects.create(
        db_key="gold",
        db_help_category="General",
        db_entrytext=(
            "|wGold & the Economy|n\n\n"
            "Gold is a simple running total, not something you carry as "
            "physical coins - check your current balance any time with "
            "'stats'.\n\n"
            "|wEarning gold:|n\n"
            "  - Defeating an NPC in combat pays gold automatically, "
            "scaled by how tough that NPC actually is - a low-level "
            "Ludus trainer pays out much less than an Arena Fighter or "
            "the Arena Master.\n"
            "  - If you bring an NPC down as a group, the reward splits "
            "fairly based on how much damage each person actually dealt "
            "- not an equal split, and not winner-take-all for whoever "
            "landed the last hit.\n\n"
            "|wSpending gold:|n\n"
            "  - Find a merchant and type 'shop' to browse what they "
            "have for sale. Merchants never run out of stock, however "
            "many people buy from them.\n"
            "  - You can also sell items of your own back to a "
            "merchant, from that same 'shop' menu - they'll pay half of "
            "an item's normal value, a genuine used-goods price rather "
            "than what it originally cost new.\n\n"
            "See 'help shop' for the actual command."
        ),
        db_lock_storage="view:all()",
    )

    # --- Bounty board ---
    HelpEntry.objects.create(
        db_key="bounty",
        db_help_category="General",
        db_entrytext=(
            "|wThe Bounty Board|n\n\n"
            "A real, physical board near the Forum's Rostra - the same "
            "spot Romans actually posted public notices. It offers "
            "repeatable jobs: hunt down a specific number of a specific "
            "kind of hostile in the Cloaca Maxima, then report back for "
            "a real reward on top of whatever you'd already earn from "
            "the kills themselves.\n\n"
            "|wUsage (while standing at the board):|n\n"
            "  bounty            - check your current bounty, or how to get one\n"
            "  bounty accept     - take a fresh bounty, matched to your own level\n"
            "  bounty turnin     - collect your reward once you've finished\n"
            "  bounty abandon    - give up your current bounty, no penalty\n\n"
            "One bounty at a time. Finishing the kill count doesn't pay "
            "out by itself - you have to actually come back and turn it "
            "in. Your bounty is personal to you; a friend fighting "
            "alongside you can be working their own, completely "
            "different bounty off the exact same fight, and a real "
            "party also earns a separate bonus on the fight's own "
            "combat XP for grouping up - see 'help groupcombat'."
        ),
        db_lock_storage="view:all()",
    )

    # --- Quests ---
    HelpEntry.objects.create(
        db_key="quest",
        db_help_category="General",
        db_entrytext=(
            "|wQuests|n\n\n"
            "One-time, narrative objectives from specific NPCs - unlike "
            "the bounty board, a quest doesn't repeat once you've "
            "finished it, and it usually has a real story behind it "
            "rather than just a kill count.\n\n"
            "|wUsage:|n\n"
            "  quest             - talk to a quest-giver standing here\n"
            "  quest <npc>       - be explicit, if a room ever has more "
            "than one quest-giver\n"
            "  quest log         - your quest journal: what you've "
            "started, which step you're on and what to do next, what's "
            "ready to turn in, and what's finished (also just 'quests', "
            "and it works anywhere, even next to a quest-giver)\n\n"
            "|wFinding quests:|n When you walk into a room with a "
            "quest-giver who has something for you, a line appears "
            "under the room description ('A moneylender looks like they "
            "have something for you'). Nothing starts until you type "
            "'quest' - there's no penalty for waiting, and a quest never "
            "expires. Once you've started it, the hint goes away; when "
            "the objective is done it comes back to tell you to report "
            "in.\n\n"
            "|wProgress:|n Checking back with a quest-giver while it's in "
            "progress reminds you what they're waiting on; checking back "
            "once you've finished pays out your reward, and you'll see "
            "'Quest objective complete' the moment the objective itself "
            "is done. Nothing auto-completes - you still report back in "
            "person.\n\n"
            "|wMulti-step quests:|n Some quests are a chain - go here, "
            "speak to someone, then deal with whoever's behind it. Each "
            "step's objective is shown when you start it and again in "
            "'quest log'. A 'talk' step is finished by typing 'quest' "
            "while standing next to the person you've been sent to. If "
            "you're sent after someone and they slip away (or you were "
            "away a while), they'll be back where they were hiding.\n\n"
            "|wClass bonuses:|n Every quest is open to everyone - but "
            "some quest-givers take particular notice of a certain "
            "class. If yours is the one they're looking for, you'll "
            "hear an extra line or two from them, and a little extra "
            "gold and experience when you turn it in (your reward "
            "message says so). There's never anything you can't do "
            "because of your class."
        ),
        db_lock_storage="view:all()",
    )

    # --- God-only oversight for bounties/quests ---
    # Not hidden - matches every other god command in this game
    # (godlevel, wizinvis, etc. have no help lock either; the real
    # gate is the level check inside each command's own func()) - just
    # kept in its own topic instead of the player-facing "bounty"/
    # "quest" entries above.
    #
    # "God Commands", not "Admin": a real bug found live - these are
    # help TOPICS (db_help_category), shown by Evennia's help index in
    # a completely separate section from real commands (help_category
    # on a Command class), with no dedup between the two. 11 real
    # commands already use help_category="admin" (ban, wall, godlevel,
    # etc.) - reusing that exact name here didn't group these topics
    # alongside them, it just printed "-- Admin --" a second time in
    # the other section, reading as a broken/duplicated menu. These
    # three are also conceptually distinct from server-admin tooling
    # anyway (ban/wall/shutdown) - a dedicated category is the more
    # honest label, not just the tidier one.
    HelpEntry.objects.create(
        db_key="godbounty",
        db_help_category="God Commands",
        db_entrytext=(
            "|wBounty Oversight (god-only)|n\n\n"
            "  bounty list      - every player currently holding an active "
            "bounty, and their progress\n"
            "  bounty catalog   - every tier and target the board can "
            "actually offer, plus the board's own current location\n\n"
            "Both work from anywhere, not just standing at the board."
        ),
        db_lock_storage="view:attr_gt(level, 100)",
    )

    HelpEntry.objects.create(
        db_key="godquest",
        db_help_category="God Commands",
        db_entrytext=(
            "|wQuest Oversight (god-only)|n\n\n"
            "  quest list       - every player with any quest activity at "
            "all (in progress, ready to turn in, or completed)\n"
            "  quest catalog    - every quest that exists, its giver, that "
            "giver's current real location, and its reward\n\n"
            "Both work from anywhere, not just standing near a giver."
        ),
        db_lock_storage="view:attr_gt(level, 100)",
    )

    # --- Religion & piety ---
    HelpEntry.objects.create(
        db_key="religion",
        db_help_category="General",
        db_entrytext=(
            "|wReligion & Piety|n\n\n"
            "A mortal's personal devotion to one of the 14 gods - "
            "distinct from becoming a god yourself (the Cursus "
            "Divinorum) and distinct from faction membership (a real "
            "political/social affiliation, not a religious one - you "
            "can hold both at once).\n\n"
            "|wJoining:|n 'pray' at one of the gods' real temples "
            "(implicitly worships that temple's own god), or 'pray "
            "<god>' at the Pantheon's Altar of All Gods for any of the "
            "14. You'll be warned first - only 'pray <god> confirm' "
            "actually joins. It's permanent: only your religion's "
            "Pontifex, or a god, can release you afterward ('expel').\n\n"
            "|wGaining favor:|n praying doesn't earn favor by itself - "
            "it comes from actually doing something in your god's own "
            "domain. Right now that's real for four gods: Mars (every "
            "7 combat kills), Mercury (every 7 trades), Apollo (every "
            "7 heals cast), and Pluto (each time you die and return). "
            "The rest are joinable, but honestly have no real trigger "
            "yet.\n\n"
            "|wPayoff:|n a real passive bonus at Devoted (75 piety) and "
            "a bigger one at Beloved (150) - Mars: melee damage, "
            "Mercury: a shop discount, Apollo: healing power, Pluto: a "
            "reduced (then zero) XP penalty on death. Check 'stats' or "
            "'religion' for your own standing.\n\n"
            "|wDiscipline:|n your religion's Pontifex (or a god) can "
            "'blemish' you for acting against your god's values - "
            "always requires a stated reason, always logged."
        ),
        db_lock_storage="view:all()",
    )

    HelpEntry.objects.create(
        db_key="godreligion",
        db_help_category="God Commands",
        db_entrytext=(
            "|wReligion Oversight (god-only)|n\n\n"
            "  pontifex <god> = <player>   - appoint a religion's Pontifex, "
            "mirrors 'factionleader' exactly\n"
            "  blemish <player> = <reason> - reduce a member's piety; "
            "Pontifex-or-god, reason required, logged, 1-hour cooldown "
            "per (discipliner, target)\n"
            "  expel <player> = <reason>   - permanently remove someone "
            "from their religion; Pontifex-or-god, reason required, "
            "logged; piety is kept, not erased\n"
            "  religion log <god>          - that religion's recent "
            "induct/blemish/expel activity, for real accountability "
            "over the two commands above\n\n"
            "No religion is blocked from functioning just because it has "
            "no Pontifex yet - a god can always act in their place."
        ),
        db_lock_storage="view:attr_gt(level, 100)",
    )

    # --- New player orientation ---
    newbie_entry = HelpEntry.objects.create(
        db_key="newbie",
        db_help_category="General",
        db_entrytext=(
            "|wSo You Just Woke Up in a Cell|n\n\n"
            "Here's the whole arc, start to finish - each step links to a "
            "real help topic with the actual details. If you'd rather get "
            "one quick suggestion instead of re-reading this, try 'journey' "
            "any time.\n\n"
            "|w0. Not interested in fighting at all?|n You can request "
            "that right now, before doing anything else - 'help pacifism' "
            "explains what it means and what it costs. It's a real, "
            "permanent choice, so read it before you decide.\n\n"
            "|w1. Get out.|n You're a captive underneath the Colosseum. "
            "'fight' your way out the direct way, or go quiet - 'sneak' "
            "past the guards, then 'solve' the riddle you find. Either way "
            "gets you free. See 'help fight' and 'help sneak'.\n\n"
            "|w2. The Ludus.|n Real, safe training - start at the Weapons "
            "Yard; the Wrestling Pit, Beast Taming Ring, and Champions' "
            "Court open up as you level. Use 'trainer' in any of them to "
            "see what your class can learn there, and 'statup' when you "
            "earn a stat point (every 3 levels). |x(A pacifist - 'help "
            "pacifism' - can still use 'trainer'/'learn'/'statup' here "
            "freely, just not 'challenge' - see step 2b below instead.)|n"
            "\n\n"
            "|w2b. Chosen pacifism instead?|n Skip the Ludus's own "
            "fighting - head to the Germanic Stronghold's Smithy "
            "('help crafting') to gather iron ore and timber and forge "
            "your first item for free, or to Market Row - Back Stalls "
            "in the Subura ('help gathering') to gather herbs for a "
            "healing tonic. Either is a real, repeatable way to earn "
            "gold and level from level 1 without ever touching combat.\n\n"
            "|w3. The Cloaca Maxima.|n Once the Ludus stops being a real "
            "challenge, the sewers beneath Rome are the real next grind - "
            "grates from the Ludus, the Subura, or the Forum all lead "
            "down. Six real depth tiers, roughly levels 5 through 25. "
            "|x(Not for a pacifist - keep progressing through crafting "
            "tiers instead; see 'help crafting'.)|n\n\n"
            "|w4. There's more to Rome than fighting.|n 'achievements', "
            "'bounty', and 'quest' all give you real, structured things to "
            "chase. 'help gathering' and 'help crafting' are a real, "
            "repeatable way to earn gold and experience without any "
            "combat at all, if that's more your speed. Walk the city "
            "itself, too - the Forum, the Capitoline, "
            "the Aventine, Campus Martius are all real, explorable places "
            "with their own history. Keep your eyes open as you go - Rome "
            "has genuine depth (real factions, real devotion to the gods) "
            "that isn't handed to you on a list. If you go looking, you'll "
            "find it.\n\n"
            "|w5. Beyond the Walls.|n Once you're strong, Rome's new "
            "northern gate - the Porta Flaminia - opens onto real "
            "wilderness and a long road to a genuine Germanic stronghold, "
            "roughly levels 25 to 45. It's a long way from home, and the "
            "road itself isn't safe - 'recall' gets you back the moment "
            "you've had enough.\n\n"
            "General tips: 'rest' to recover between fights, 'disengage' "
            "if one's going badly, 'stats' any time to check where you "
            "stand, 'help shortcuts' once typing out the same spell/skill "
            "command every turn gets old, and 'help' for absolutely "
            "everything else."
        ),
        db_lock_storage="view:all()",
    )
    newbie_entry.aliases.add("tutorial")
    newbie_entry.aliases.add("getting started")
    newbie_entry.aliases.add("start")

    # --- Beyond the Walls (Germania) ---
    HelpEntry.objects.create(
        db_key="beyond the walls",
        db_help_category="General",
        db_entrytext=(
            "|wBeyond the Walls|n\n\n"
            "Rome finally has a real northern gate - the Porta Flaminia, "
            "reachable from Campus Martius's Centuriate Assembly Ground. "
            "Past it, the Via Flaminia runs north through genuine "
            "wilderness - farmland giving way to scrubland, then forest, "
            "then deep woods, for a real, long march (milestones mark "
            "the distance the whole way). Wandering off the road is "
            "fine and even encouraged - it's real, if repeating, "
            "wilderness in every direction, though it doesn't go on "
            "forever. Random encounters get more dangerous the further "
            "north you go, so come ready for a fight, not just a walk.\n\n"
            "At the road's end: a full Germanic stronghold, built "
            "nothing like Rome - a wooden palisade, a chieftain's Great "
            "Hall, a sacred grove, and four distinct warband camps "
            "(Wolf-kin, Boar-marked, Raven's Watch, the Storm-callers), "
            "each tougher than the last, plus the genuinely dangerous "
            "Contested Borderlands. This is real leveling content for "
            "characters roughly 25-45 - a natural next step once the "
            "sewers stop being worth the trip. A Germanic weaponsmith "
            "sells real local gear (seaxes, angons, franciscas, "
            "waraxes, lamellar and mail), and Germanic is one of the "
            "languages you can learn (see 'help languages') - but only "
            "from a trainer who's actually here.\n\n"
            "It's a genuinely long way from home - 'recall' (see 'help "
            "recall') is the fast way back once you're ready to return."
        ),
        db_lock_storage="view:all()",
    )

    # --- Recall ---
    HelpEntry.objects.create(
        db_key="recall",
        db_help_category="General",
        db_entrytext=(
            "|wRecall|n\n\n"
            "  recall\n\n"
            "Teleports you back to the Temple of Jupiter Optimus Maximus "
            "on the Capitoline - the same place a level 6+ character "
            "returns to after death. Blocked while in combat, and on a "
            "10-minute cooldown afterward, so it's meant for getting "
            "back from somewhere genuinely far away, not as an "
            "escape-from-a-fight button."
        ),
        db_lock_storage="view:all()",
    )

    # --- Earned titles ---
    HelpEntry.objects.create(
        db_key="titles",
        db_help_category="General",
        db_entrytext=(
            "|wEarned Titles|n\n\n"
            "A title granted automatically for a real accomplishment - "
            "an achievement, a quest, or reaching Beloved with a god - "
            "as distinct from the ordinary 'title' command's free-text "
            "custom title. Both can show at once wherever there's "
            "room ('stats', 'look'); the 'who' list only has room for "
            "one and shows your earned title there if you have one "
            "active.\n\n"
            "Your very first earned title activates automatically. "
            "After that:\n"
            "  titles             - list everything you've earned\n"
            "  titles set <name>  - switch which one is shown\n"
            "  titles clear       - show no earned title\n\n"
            "Earning a second (or third) title never overrides an "
            "already-active one - use 'titles set' to switch."
        ),
        db_lock_storage="view:all()",
    )

    # --- Pacifism ---
    HelpEntry.objects.create(
        db_key="pacifism",
        db_help_category="General",
        db_entrytext=(
            "|wPacifism|n\n\n"
            "A real, permanent opt-out of combat entirely - not just "
            "PvP. A pacifist can never attack, and can never be "
            "attacked by, another player or any creature, anywhere in "
            "the game: the wilderness roads, a duel, a kill quest, all "
            "of it. You can request this the moment you start playing, "
            "before you've done anything else.\n\n"
            "|wUsage:|n\n"
            "  pacifism          - see what it costs and what it means\n"
            "  pacifism confirm  - actually do it\n\n"
            "This is a weighty, one-way choice, the same way joining a "
            "faction is - only a god can restore your right to fight "
            "afterward, and you can't undo it yourself. You also can't "
            "switch at all if you've ever killed another player (no "
            "exceptions - that door closes for good the moment it "
            "happens), while you're actively in a fight, or for a "
            "while after your last real combat action.\n\n"
            "|wYou give up your gear to do this.|n Every weapon and "
            "piece of armor you're wearing comes off the moment you "
            "confirm - ordinary gear is just set aside, but anything "
            "one of a kind is lost for good, not merely dropped.\n\n"
            "|wWhat's left to do?|n Everything that isn't a fight: "
            "explore the whole city, chase any quest whose steps are "
            "'visit' or 'talk' (a kill quest simply won't be offered to "
            "you), and every social/roleplay system in the game works "
            "exactly the same either way. Escaping the Colosseum's "
            "holding cells is itself entirely non-combat already - "
            "'sneak' past the guard, then 'solve' the riddle you find - "
            "so you never have to fight your way free either. 'help "
            "gathering' and 'help crafting' are your real, repeatable "
            "way to earn gold and experience without ever fighting - "
            "not just a handful of one-time quests.\n\n"
            "|wYour spells and skills aren't all useless.|n Every one is "
            "individually flagged as combat-only or non-combat-only (or "
            "both) - 'spellinfo'/'skillinfo' on a specific one will tell "
            "you which. Anything not flagged combat-only still works for "
            "you exactly as it would for anyone else (a heal, a buff, "
            "most utility effects); only the ones flagged combat-only are "
            "permanently closed off, since you can never enter a fight to "
            "use them.\n\n"
            "|wStats and leveling work exactly the same for you|n - the "
            "same stat point every 3 levels, spent with 'statup' "
            "exactly as anyone else's would be. Virtus, Agilitas, "
            "Ingenium, and Vigor genuinely do nothing for someone who "
            "never fights, though, so the flat HP/MP/SP option 'statup' "
            "already offers is usually the more useful pick for you - "
            "especially SP, since ordinary movement still costs it "
            "('help sp') and that's the one resource that actually "
            "matters day to day for getting around."
        ),
        db_lock_storage="view:all()",
    )

    HelpEntry.objects.create(
        db_key="godpacifism",
        db_help_category="God Commands",
        db_entrytext=(
            "|wgodpacifism|n (god-only)\n\n"
            "Usage:\n"
            "  godpacifism <character>\n\n"
            "Restores a pacifist's right to fight - see 'help pacifism' "
            "for why this is deliberately not something a player can "
            "undo themselves. Does not return any gear that was "
            "destroyed on the way in; that loss was explicit and final "
            "at the time."
        ),
        db_lock_storage="view:all()",
    )

    # --- Gathering & crafting ---
    HelpEntry.objects.create(
        db_key="gathering",
        db_help_category="General",
        db_entrytext=(
            "|wGathering|n\n\n"
            "A real, repeatable, entirely non-combat way to earn "
            "materials and level - see 'help crafting' for what to do "
            "with what you gather.\n\n"
            "|wUsage:|n\n"
            "  gather   (also 'forage', 'mine' - all the same command)\n\n"
            "Some places might have a real material waiting: wooded "
            "stretches of the wilderness road north of Rome for timber, "
            "the Ore Vein Shaft (off the Germanic Stronghold's Smithy) "
            "for iron ore. Walking in is never a guarantee, though - "
            "you'll get a real message the moment something is actually "
            "there to take ('You spot...'), so keep exploring if a "
            "particular spot comes up empty. There's nothing to fight "
            "and no risk either way - a pacifist ('help pacifism') can "
            "do this exactly as freely as anyone else.\n\n"
            "|wCommon vs. rare:|n timber is common and refreshes for you "
            "in a few minutes; iron ore is rare and refreshes for you "
            "roughly once a day - worth the trip, not something to farm "
            "repeatedly in one sitting. Either way, once you've actually "
            "gathered somewhere, you personally can gather that same "
            "kind of material again once its own time has passed - "
            "nobody else's gathering affects your own."
        ),
        db_lock_storage="view:all()",
    )

    HelpEntry.objects.create(
        db_key="crafting",
        db_help_category="General",
        db_entrytext=(
            "|wCrafting|n\n\n"
            "Turn gathered materials into something worth real gold and "
            "experience - a genuine, repeatable non-combat path to "
            "leveling, not just a one-time quest. See 'help gathering' "
            "for where materials come from.\n\n"
            "|wTwo professions exist so far, and they're unrelated to "
            "each other|n - each has its own materials, its own fixed "
            "crafting location, and its own separate skill that only "
            "rises by practicing that profession specifically:\n"
            "  |YFaber|n (smithing) - weapons and armor. See 'help "
            "faber'.\n"
            "  |YHerbalist|n (alchemy) - healing potions. See 'help "
            "herbalist'.\n\n"
            "|wUsage (same commands for either profession):|n\n"
            "  craft <recipe>       - automatically uses whatever you're "
            "carrying (and whatever fixed tool is in the room) that the "
            "recipe needs\n"
            "  recipes              - see everything you could make, "
            "from both professions, what it needs, and whether you "
            "already know it\n"
            "  learnrecipe <recipe> - learn a recipe above tier 1 from "
            "a trainer standing with you (costs gold)\n\n"
            "|wTiers:|n each profession's first recipe needs no training "
            "at all - anyone can attempt it the moment they have the "
            "materials and are standing at that profession's tool, so "
            "starting out never requires gold you don't have yet. Every "
            "recipe past that has to be learned in person from a "
            "trainer, the same way learning a spell or skill already "
            "works - fund it from selling what your free starting "
            "recipe makes. A higher tier means a genuinely stronger "
            "item AND a genuinely better reward - there's no benefit to "
            "grinding an easy recipe forever once a harder one is "
            "within reach.\n\n"
            "|wSkill:|n each craft attempt is checked against your own "
            "skill in that profession, which starts at 0 and rises with "
            "practice - a failed attempt keeps your materials and still "
            "counts toward getting better, so there's never nothing to "
            "show for trying.\n\n"
            "|wSelling:|n a crafted item, or a raw material you'd rather "
            "not use yourself, is sold through the ordinary 'shop' menu "
            "at any merchant - crafted goods pay both gold and "
            "experience on sale, raw materials pay gold only. Selling "
            "further from Rome pays a real bonus, and so does selling to "
            "a merchant who actually deals in that kind of goods (a "
            "weaponsmith pays extra for weapons or armor, an apothecary "
            "pays extra for potions) - real reasons to think about where "
            "you sell, not just carry everything back to the nearest "
            "shop."
        ),
        db_lock_storage="view:all()",
    )

    HelpEntry.objects.create(
        db_key="faber",
        db_help_category="General",
        db_entrytext=(
            "|wFaber (Smithing)|n\n\n"
            "The blacksmithing profession - turns iron ore and timber "
            "into real weapons and armor. See 'help crafting' for the "
            "commands ('craft', 'recipes', 'learnrecipe') and 'help "
            "gathering' for where ore and timber come from.\n\n"
            "|wWhere:|n every Faber recipe needs the smithing forge at "
            "The Smithy Forge (Germanic Stronghold, right by the Ore "
            "Vein Shaft) - it's a fixture, not something you carry, so "
            "you have to actually be standing there to craft.\n\n"
            "|wRecipes (lowest tier first):|n\n"
            "  iron shortsword  - needs no training, anyone can start "
            "the moment they have 1 iron ore and 1 timber\n"
            "  iron lorica      - armor, needs training from the Faber "
            "trainer at the Smithy\n"
            "  iron war-spear   - needs training, the toughest Faber "
            "recipe so far\n\n"
            "Faber has its own skill (separate from Herbalist's) that "
            "only improves by actually attempting Faber recipes."
        ),
        db_lock_storage="view:all()",
    )

    HelpEntry.objects.create(
        db_key="herbalist",
        db_help_category="General",
        db_entrytext=(
            "|wHerbalist (Alchemy)|n\n\n"
            "The potion-brewing profession - turns healing herbs into "
            "real, usable consumables. See 'help crafting' for the "
            "commands ('craft', 'recipes', 'learnrecipe') and 'help "
            "gathering' for where herbs come from.\n\n"
            "|wWhere:|n every Herbalist recipe needs the apothecary's "
            "mortar at Market Row - Back Stalls (the Subura) - it's a "
            "fixture, not something you carry, so you have to actually "
            "be standing there to craft.\n\n"
            "|w\"Free\" doesn't mean handed to you|n - it means the "
            "recipe itself needs no gold or trainer to learn, exactly "
            "like Faber's own starting recipe. You still have to gather "
            "your own herbs and actually succeed at the craft attempt "
            "(a skill check, same as Faber) - nothing here is given away "
            "for nothing.\n\n"
            "|wRecipes (lowest tier first):|n\n"
            "  healing tonic - needs no training, anyone can start the "
            "moment they have 1 bundle of healing herbs\n"
            "  antidote      - cures Poisoned, needs training from a "
            "Herbalist trainer, costs more herbs\n\n"
            "Herbalist has its own skill (separate from Faber's) that "
            "only improves by actually attempting Herbalist recipes."
        ),
        db_lock_storage="view:all()",
    )

    # --- Player-to-player trading (barter contrib) ---
    HelpEntry.objects.create(
        db_key="trade",
        db_help_category="General",
        db_entrytext=(
            "|wTrading with Other Players|n\n\n"
            "A safe way to exchange items and gold with another player - "
            "unlike a plain 'give', neither side can be left holding "
            "nothing after handing something over. The trade only "
            "actually happens once BOTH people explicitly agree.\n\n"
            "|wStarting a trade:|n\n"
            "  trade <name>: <optional message>\n"
            "The other person accepts the same way - 'trade <your name>' "
            "- to actually begin negotiating.\n\n"
            "|wWhile trading:|n\n"
            "  offer <item(s)>  - put item(s) on the table (comma-separate "
            "for more than one)\n"
            "  evaluate <item>  - look closely at something offered to you\n"
            "  accept           - agree to the current offer (both sides "
            "must accept for anything to change hands)\n"
            "  decline          - back out of the trade entirely\n\n"
            "Nothing is exchanged until both people accept - changing your "
            "offer after the other person accepts requires them to accept "
            "again."
        ),
        db_lock_storage="view:all()",
    )

    # --- Achievements ---
    HelpEntry.objects.create(
        db_key="achievements",
        db_help_category="General",
        db_entrytext=(
            "|wAchievements|n\n\n"
            "Certain milestones - fights won, gold earned, levels "
            "reached - are tracked automatically as you play. Check your "
            "own progress any time with:\n\n"
            "  achievements          - see everything, done and in "
            "progress\n"
            "  achievements/done     - see only what you've completed\n"
            "  achievements/progress - see only what's still in progress\n\n"
            "You can also search by name, e.g. 'achievements legend' to "
            "check one specifically. Achievements aren't announced with "
            "any special fanfare when completed - checking in on them "
            "yourself is part of the fun."
        ),
        db_lock_storage="view:all()",
    )

    # --- Racial abilities ---
    HelpEntry.objects.create(
        db_key="racial",
        db_help_category="General",
        db_entrytext=(
            "|wRacial Abilities|n\n\n"
            "Your race grants you one or two innate abilities of its own, "
            "on top of whatever your class teaches - see 'help race' for "
            "each race's own. Unlike spells and skills, these are yours "
            "from the moment you're created: no trainer, no gold, no "
            "learning required. They cost no MP or SP either - only a "
            "cooldown limits how often you can call on one.\n\n"
            "  racialinfo             - see your own racial abilities, "
            "their cooldowns, and what they do\n"
            "  racial <ability>       - use one (aliased 'race')\n"
            "  racial <ability> = <target>  - use one on a specific "
            "target, where it applies\n\n"
            "Not every race's listed traits are built yet - some (like a "
            "Human's Command Presence or a Cyclops's Forge Mastery) are "
            "purely social or crafting-flavored, with no matching system "
            "in the game yet. 'racialinfo' only ever lists what's actually "
            "usable right now."
        ),
        db_lock_storage="view:all()",
    )

    # --- Individual racial abilities ---
    #
    # Same reasoning and pattern as the individual faction abilities
    # below - pulled directly from world.racial_abilities.
    # RACIAL_ABILITIES so these can't drift from the real mechanics,
    # and so 'help <ability name>' actually finds something instead of
    # a false-positive fuzzy match on an unrelated topic. Real,
    # confirmed live gap: a player twice asked in-character how to use
    # Boon of the Wilds, and 'help boon of the wilds' was matching
    # "Wild Rite of Bacchus" - a real cult topic that happens to share
    # the word "wild" - instead of anything relevant, since no entry
    # for the ability itself existed at all.
    from world.racial_abilities import RACIAL_ABILITIES

    for ability_name, data in RACIAL_ABILITIES.items():
        HelpEntry.objects.create(
            db_key=ability_name,
            db_help_category="General",
            db_entrytext=(
                "|w%s|n\n\n"
                "An innate %s racial ability (cooldown: %d turn%s). No "
                "MP/SP cost, no trainer needed - see 'help racial'.\n\n"
                "  racial %s%s\n\n"
                "%s"
            ) % (
                ability_name.title(),
                data["race"].title(),
                data["cooldown"],
                "" if data["cooldown"] == 1 else "s",
                ability_name,
                "" if data["target"] == "self" else " = <target>",
                data["desc"],
            ),
            db_lock_storage="view:all()",
        )

    # --- Factions ---
    HelpEntry.objects.create(
        db_key="factions",
        db_help_category="General",
        db_entrytext=(
            "|wFactions|n\n\n"
            "Eight factions are active in the world, each represented by a "
            "unique recruiter NPC somewhere in the city. Requires level 10.\n\n"
            "|rJoining a faction is a lifelong commitment for your character, "
            "not something to take lightly.|n Standing with a recruiter and "
            "typing 'faction join <name>' does not join you immediately - the "
            "recruiter will warn you plainly first that there is no walking "
            "away from this on your own once you're in. Only after you "
            "confirm with 'faction join <name> confirm' does it actually "
            "take effect.\n\n"
            "  faction                    - see your faction and rank\n"
            "  faction join <name>        - hear the recruiter's warning "
            "(matches either their name or the faction's own name)\n"
            "  faction join <name> confirm - actually join, having heard it\n"
            "  faction leave              - see below\n\n"
            "You can only ever belong to one faction at a time, and once "
            "you're a member, |wthere is no switching to a different one "
            "either|n - that would just be leaving through the back door, "
            "so it's blocked the same way outright leaving is. Joining "
            "grants a small set of faction-only abilities (see 'skillinfo') "
            "and connects you to that faction's private channel "
            "automatically.\n\n"
            "Ranks are member and leader - a faction has exactly one leader "
            "at a time, designated by a god. |wAn ordinary member cannot "
            "leave a faction on their own, full stop|n - getting one out "
            "requires a real petition, either their faction's leader or a "
            "god using 'faction expel <char>'. A leader's own 'faction "
            "leave' only sheds the leadership role, not membership itself - "
            "they drop to an ordinary member (the faction goes leaderless "
            "until a god names someone new) and are just as bound to it for "
            "life as anyone else afterward; leaving the faction entirely "
            "still takes a god's 'expel', leader or not. A faction's leader "
            "(and any god) can also 'faction invest <char> = <faction>' to "
            "add someone directly.\n\n"
            "The eight factions: Imperial Legion, Praetorian Order, "
            "Hellenic Resistance, Cult of Mithras, Orphic Mysteries, Cult "
            "of Hecate, Cult of Bacchus, and Collegium Umbrae."
        ),
        db_lock_storage="view:all()",
    )

    # --- Individual faction abilities ---
    #
    # Pulled directly from world.combat.SKILLS (the same "desc"/"cost"/
    # "level_required"/"command_name" fields skillinfo itself reads),
    # not re-typed here, so these entries can't drift from the real
    # mechanics the way a hand-written duplicate could.
    from world.combat import SKILLS

    for faction_key, data in FACTIONS.items():
        for skill_name in data["skills"]:
            skill_data = SKILLS[skill_name]
            command_name = skill_data.get("command_name")
            usage = (
                "  %s\n\n" % command_name
                if command_name
                else "  skill %s = <target>\n\n" % skill_name
            )
            cost = skill_data.get("cost", 0)
            cost_text = "%d SP" % cost if cost else "Free"
            HelpEntry.objects.create(
                db_key=skill_name,
                db_help_category="Factions",
                db_entrytext=(
                    "|w%s|n\n\n"
                    "A %s ability (level %d, %s). See 'faction' to join.\n\n"
                    "%s"
                    "%s"
                ) % (
                    skill_name.title(),
                    data["name"],
                    skill_data.get("level_required", 10),
                    cost_text,
                    usage,
                    skill_data.get("desc", ""),
                ),
                db_lock_storage="view:all()",
            )

    # --- Spell/skill trainers ---
    HelpEntry.objects.create(
        db_key="trainers",
        db_help_category="General",
        db_entrytext=(
            "|wTrainers|n\n\n"
            "Learning a new spell or skill costs gold and requires "
            "finding the right trainer in person - 'learn' refuses "
            "from anywhere else, even if you've got the gold and the "
            "level for it.\n\n"
            "Two trainers exist, one per learning path:\n"
            "  - The |wLudus weapons master|n (Ludus Entrance) teaches "
            "combat skills - Legionary, Gladiator, Barbarian, "
            "Speculator, and Venator.\n"
            "  - The |wFlamen of the Cella|n (Main Cella, Temple of "
            "Jupiter, Capitoline Hill) teaches magic spells - Augur, "
            "Haruspex, and Medicus.\n\n"
            "Once you're standing with the right one:\n"
            "  trainer (or 'train')    - see everything they can "
            "teach your class, its level requirement, and its gold "
            "cost, split into known / ready now / not yet available\n"
            "  learn <name>            - learn it, whether it's a "
            "spell or a skill - your class only ever has one of the "
            "two, so there's no ambiguity\n\n"
            "Cost scales with how powerful the spell/skill is - a "
            "level 1 pick is cheap, a level 90 one is a real "
            "investment. See 'help gold' for how to earn it."
        ),
        db_lock_storage="view:all()",
    )

    # --- Trivia (Hecate's Roman epithet) ---
    HelpEntry.objects.create(
        db_key="trivia",
        db_help_category="General",
        db_entrytext=(
            "|wTrivia|n\n\n"
            "|xThe Romans rarely spoke Hecate's Greek name at a crossroads "
            "after dark - they called her Trivia instead, \"of the three "
            "roads,\" where her shrines were traditionally kept.|n\n\n"
            "Trivia is simply the Roman name for Hecate, goddess of "
            "magic, crossroads, and the boundary between the living and "
            "the dead - the same figure behind the Cult of Hecate. See "
            "'help factions' for how faction membership actually works; "
            "this topic exists just to answer the name itself."
        ),
        db_lock_storage="view:all()",
    )

    # --- Beseech (divine intervention) ---
    HelpEntry.objects.create(
        db_key="beseech",
        db_help_category="General",
        db_entrytext=(
            "|wBeseech|n\n\n"
            "|xNot every prayer is a vow. Sometimes a mortal simply has "
            "nowhere else to turn, and cries out - not to the god they've "
            "sworn themselves to, but to whichever god might actually be "
            "listening. The gods hear every such plea, whether or not it "
            "was addressed to them by name.|n\n\n"
            "|wUsage:|n beseech <god> = <message>\n\n"
            "Works from anywhere, to any of the 14 gods, regardless of "
            "your own religion (or lack of one) - unlike 'pray', which "
            "is the formal ritual for actually joining a religion at a "
            "shrine. Your plea is announced in the room as a real scene, "
            "and reaches every god currently playing, not just followers "
            "of that one deity.\n\n"
            "This has no mechanical effect of its own - no piety, no "
            "guaranteed reply. It's a pure roleplay hook: what happens "
            "next is entirely up to whichever god chooses to answer, and "
            "how. See 'help religion' for how piety actually works."
        ),
        db_lock_storage="view:all()",
    )

    # --- Naming ---
    HelpEntry.objects.create(
        db_key="naming",
        db_help_category="General",
        db_entrytext=(
            "|wNaming Your Character|n\n\n"
            "|xRome is set at the height of the Empire - the illusion "
            "matters, and a single out-of-place name breaks it for "
            "everyone else in the room, not just you.|n\n\n"
            "Your name should sound like it could genuinely belong to "
            "someone living in that world - a citizen, a slave, a "
            "freedman, a foreign trader, a soldier - Roman, Greek, or "
            "otherwise period-appropriate. It doesn't need to be "
            "historically famous, just plausible.\n\n"
            "|wWhat doesn't fit:|n modern words or phrases, internet "
            "usernames, meme references, real-world brand names, or "
            "anything that reads as a joke rather than a person who "
            "lives here. If a name wouldn't make sense shouted across "
            "the Forum in 100 AD, it doesn't belong in Rome.\n\n"
            "We're still in Player Testing, so this isn't strictly "
            "enforced yet - but a god may ask you to pick something "
            "else if your name breaks the setting, and it's much "
            "easier to get it right the first time than to get used "
            "to a name and then have to change it later."
        ),
        db_lock_storage="view:all()",
    )

    # --- Armor & weapon proficiency ---
    armor_entry = HelpEntry.objects.create(
        db_key="armor",
        db_help_category="General",
        db_entrytext=(
            "|wArmor & Weapon Proficiency|n\n\n"
            "Every class handles certain weapons and certain armor "
            "weight tiers 'at full effectiveness' - anything outside "
            "that still works, it's just worse. Nothing is ever fully "
            "blocked; picking up a stranger's weapon or wearing a "
            "lucky drop is always a real option, just a costlier one "
            "outside your own kit.\n\n"
            "|wWeapon categories, by class:|n\n"
            "  - Augur, Medicus, Haruspex: Staff, Light Blade\n"
            "  - Speculator: Light Blade, Ranged\n"
            "  - Venator: Ranged, Polearm\n"
            "  - Gladiator, Legionary: Light Blade, Heavy Blade, Polearm\n"
            "  - Barbarian: Heavy Weapon, Heavy Blade\n\n"
            "|wWhat those categories actually are:|n\n"
            "  - Light Blade - dagger, gladius\n"
            "  - Heavy Blade - broadsword, greatsword\n"
            "  - Polearm - spear, trident\n"
            "  - Ranged - javelin, shortbow\n"
            "  - Heavy Weapon - waraxe\n"
            "  - Staff - ritual staff\n\n"
            "|wArmor weight tiers, by class:|n\n"
            "  - Augur, Medicus, Haruspex, Speculator: Light only\n"
            "  - Venator: Light, Medium\n"
            "  - Gladiator, Legionary: Light, Medium, Heavy\n"
            "  - Barbarian: Medium, Heavy\n\n"
            "|wThe actual penalty:|n\n"
            "  - Wielding a weapon outside your proficiency: -20 "
            "accuracy on every attack, and 25% less damage on every "
            "hit that lands.\n"
            "  - Wearing armor or a shield outside your proficiency: "
            "-20 defense (easier to hit) for each mismatched piece - "
            "a mismatched shield AND breastplate both apply their own "
            "separate penalty.\n\n"
            "Not sure what category or weight tier something actually "
            "is? Use 'inspect <item>' on it - see 'help inspect'."
        ),
        db_lock_storage="view:all()",
    )
    armor_entry.aliases.add("weapons")
    armor_entry.aliases.add("proficiency")

    # --- Shortcuts (the built-in 'nick' command) ---
    HelpEntry.objects.create(
        db_key="shortcuts",
        db_help_category="General",
        db_entrytext=(
            "|wShortcuts|n\n\n"
            "Typing out 'cast <spell> = <target>' or 'skill <skill> = "
            "<target>' every single turn gets old fast, especially for "
            "a spell/skill you use constantly. 'nick' (a built-in "
            "command, not something specific to this game) lets you "
            "define your own personal shortcuts, with arguments:\n\n"
            "  nick fb $1 = cast fireball = $1\n"
            "  fb goblin              (now casts fireball on the goblin)\n\n"
            "  nick hl = skill hold the line\n"
            "  hl                     (no argument needed for this one)\n\n"
            "Nicks are entirely personal - nobody else sees or is "
            "affected by the ones you set. 'nicks' lists everything "
            "you've defined so far, and 'nick/delete <string or "
            "number>' removes one. See 'help nick' for the full "
            "syntax, including matching multiple arguments at once."
        ),
        db_lock_storage="view:all()",
    )

    # --- PvP conduct ---
    HelpEntry.objects.create(
        db_key="pvp",
        db_help_category="General",
        db_entrytext=(
            "|wPlayer vs. Player Combat|n\n\n"
            "Yes, you can fight another player. 'fight <name>' and "
            "'attack' don't check whether your target is flesh and "
            "blood or a trainer dummy - nothing in the rules stops "
            "you. What matters is why.\n\n"
            "|wThe rule, stated plainly:|n\n"
            "PvP must come from real in-character justification - "
            "roleplay, not impulse. A grudge, an insult that can't "
            "stand, betrayed trust, a duel of honor, a Cult's or "
            "faction's business, a blood feud your character actually "
            "has a reason to carry. If you can't say - in character - "
            "why your sword is out, it shouldn't be. Attacking someone "
            "with no in-character reason at all, to grief, to farm "
            "them for XP, or to settle a score that's actually yours "
            "and not your character's, is not roleplay. It's a rules "
            "violation, full stop.\n\n"
            "|wWhat happens if you break it:|n\n"
            "Jupiter deals justice to the gods of Olympus themselves - "
            "he was never going to look away from a mortal who draws "
            "blood without cause. Violate this rule and the response "
            "will be swift, direct, and entirely at the discretion of "
            "the gods watching. There is no warning shot and no "
            "appeal once it lands. What form it takes is theirs to "
            "decide, not yours to negotiate - so don't test it to "
            "find out.\n\n"
            "|wOne place this never applies, justified or not:|n\n"
            "No fight can be started in the Underworld, full stop. "
            "The afterlife is not an arena - not for the newly dead, "
            "not for anyone else standing in it.\n\n"
            "See 'help jupiter' and 'help gods' for who's actually "
            "watching."
        ),
        db_lock_storage="view:all()",
    )

    # --- In-character mail (game_systems.mail contrib, character half) ---
    HelpEntry.objects.create(
        db_key="mailsystem",
        db_help_category="General",
        db_entrytext=(
            "|wIn-Character Mail|n\n\n"
            "Send letters to other characters, in character - a real "
            "way to reach someone who isn't online right now, or to "
            "leave a written record of something in the story. Only "
            "the in-character half of this system is installed here: "
            "mail goes between CHARACTERS, not between out-of-"
            "character accounts, and it only works while you're "
            "actually logged in and playing - there's no OOC mailbox "
            "to check.\n\n"
            "|wCommands:|n\n"
            "  mail                                    - see everything "
            "in your mailbox\n"
            "  mail <#>                                - read a "
            "specific message\n"
            "  mail <name>=<subject>/<message>         - send a "
            "letter (comma-separate names to send to more than one "
            "character at once)\n"
            "  mail/reply <#>=<message>                - reply, with "
            "the original message attached beneath\n"
            "  mail/forward <name>=<#>[/<message>]     - forward a "
            "message on to someone else, with an optional note of "
            "your own\n"
            "  mail/delete <#>                         - delete a "
            "message\n\n"
            "Nothing here is announced out loud - checking your mail "
            "is entirely your character's own business."
        ),
        db_lock_storage="view:all()",
    )

    # --- Languages (rplanguage contrib) ---
    HelpEntry.objects.create(
        db_key="languages",
        db_help_category="General",
        db_entrytext=(
            "|wLanguages|n\n\n"
            "Every character starts knowing only Latin, the setting's own "
            "common tongue. Everything you say, pose, or emote goes out in "
            "whichever language you're currently speaking - anyone nearby "
            "who doesn't know that language hears it scrambled into real, "
            "consistent-sounding nonsense (not a flat 'you don't "
            "understand' message), the same way overhearing an unfamiliar "
            "real language sounds like noise you can still tell apart from "
            "other noise.\n\n"
            "Four more languages exist to learn: Greek, Celtic, Germanic, "
            "and Egyptian - each with its own distinct sound when "
            "scrambled, not the same gibberish under a different label. "
            "Each needs a real trainer who actually speaks it, a minimum "
            "level, and gold - not picked up on your own:\n\n"
            "  Greek (level 1) - a Greek scholar, the Greek Reading Room, "
            "the Library\n"
            "  Celtic (level 5) - a Gallic trader, the Wing of Foreign "
            "Curiosities, Trajan's Market\n"
            "  Egyptian (level 10) - a priest of Isis, the Priest's "
            "Chamber, the Temple of Isis\n"
            "  Germanic (level 15) - nobody in Rome teaches it yet; its "
            "trainer lives at the Germanic settlement itself, far to "
            "the north past the Porta Flaminia\n\n"
            "Each language also has its own display color, so you can tell "
            "which one you're hearing at a glance even when the words are "
            "scrambled: |wLatin|n, |cGreek|n, |gCeltic|n, |yEgyptian|n, "
            "|rGermanic|n.\n\n"
            "|wCommands:|n\n"
            "  speak                  - show what you're currently "
            "speaking, and everything you know\n"
            "  speak <language>       - switch which language you speak\n"
            "  learnlanguage <language> - learn a new one from a trainer "
            "standing in the same room as you\n\n"
            "Gods (level 101 and above) understand every language "
            "unconditionally, regardless of what they've 'learned' - "
            "nothing is ever scrambled for them.\n\n"
            "Very short words can occasionally come out dropped entirely "
            "rather than garbled, for grammars that don't cover that exact "
            "word length - this reads as extra scrambling, not a bug."
        ),
        db_lock_storage="view:all()",
    )

    # Real count, not a hand-maintained formula - the old
    # `len(RACES) + len(CLASSES) + len(STAT_HELP) + 11` had already
    # drifted stale (dozens of standalone topics added since "+11"
    # was accurate), silently under-reporting every run without
    # actually affecting which entries got created.
    total = HelpEntry.objects.filter(db_key__in=managed_keys).count()
    print("Created %d help entries." % total)