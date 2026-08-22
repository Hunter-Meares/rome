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
        "bonus Max HP and Max MP on top of your race and class's normal "
        "totals, and provides a flat reduction to incoming damage, "
        "independent of and in addition to whatever armor you're "
        "wearing. High-Vigor characters are simply harder to bring down.",
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
    managed_keys = (
        list(RACES.keys())
        + list(CLASSES.keys())
        + list(STAT_HELP.keys())
        + ["races", "classes", "corestats", "groupcombat", "gold", "trade", "achievements"]
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
            "race and class and visible any time with the 'stats' command.\n\n"
            "Type 'help <stat name>' for details on any of these:\n\n" + stat_list
        ),
        db_lock_storage="view:all()",
    )

    # --- Group combat / sides overview ---
    HelpEntry.objects.create(
        db_key="groupcombat",
        db_help_category="Combat",
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
            "own AoE.\n\n"
            "See 'help party' and 'help fight' for the specific commands."
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

    total = len(RACES) + len(CLASSES) + len(STAT_HELP) + 7
    print("Created %d help entries." % total)