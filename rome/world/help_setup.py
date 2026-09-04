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
        + ["races", "classes", "corestats", "statup", "sp", "groupcombat", "gold", "bounty", "quest", "godbounty", "godquest", "religion", "godreligion", "titles", "recall", "beyond the walls", "newbie", "trade", "achievements", "languages", "trainers", "pvp", "mailsystem", "factions"]
        + [skill for data in FACTIONS.values() for skill in data["skills"]]
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
            "own AoE.\n"
            "  - |wA real party (not just two unrelated attackers) earns a "
            "20% bonus to the whole XP pool|n on a kill, on top of the "
            "usual fair split by how much damage each of you actually "
            "dealt - a genuine reason to group up, not just a wash.\n\n"
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
            "  quest             - interact with a quest-giver standing "
            "here, or (with none present) review your own quest log\n"
            "  quest <npc>       - be explicit, if a room ever has more "
            "than one quest-giver\n\n"
            "Standing near a quest-giver with nothing started yet offers "
            "their quest; checking back while it's in progress reminds "
            "you what they're waiting on; checking back once you've "
            "actually finished it pays out your reward. Nothing here "
            "auto-completes just because you happened to finish the "
            "objective somewhere else - you still have to go report "
            "back in person."
        ),
        db_lock_storage="view:all()",
    )

    # --- God-only oversight for bounties/quests ---
    # Not hidden - matches every other god command in this game
    # (godlevel, wizinvis, etc. have no help lock either; the real
    # gate is the level check inside each command's own func()) - just
    # kept in its own topic instead of the player-facing "bounty"/
    # "quest" entries above, the same separation those other god
    # commands already get via help_category "admin".
    HelpEntry.objects.create(
        db_key="godbounty",
        db_help_category="Admin",
        db_entrytext=(
            "|wBounty Oversight (god-only)|n\n\n"
            "  bounty list      - every player currently holding an active "
            "bounty, and their progress\n"
            "  bounty catalog   - every tier and target the board can "
            "actually offer, plus the board's own current location\n\n"
            "Both work from anywhere, not just standing at the board."
        ),
        db_lock_storage="view:all()",
    )

    HelpEntry.objects.create(
        db_key="godquest",
        db_help_category="Admin",
        db_entrytext=(
            "|wQuest Oversight (god-only)|n\n\n"
            "  quest list       - every player with any quest activity at "
            "all (in progress, ready to turn in, or completed)\n"
            "  quest catalog    - every quest that exists, its giver, that "
            "giver's current real location, and its reward\n\n"
            "Both work from anywhere, not just standing near a giver."
        ),
        db_lock_storage="view:all()",
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
        db_help_category="Admin",
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
        db_lock_storage="view:all()",
    )

    # --- New player orientation ---
    newbie_entry = HelpEntry.objects.create(
        db_key="newbie",
        db_help_category="General",
        db_entrytext=(
            "|wSo You Just Woke Up in a Cell|n\n\n"
            "Here's the whole arc, start to finish - each step links to a "
            "real help topic with the actual details. If you'd rather get "
            "one quick suggestion instead of re-reading this, try 'whatnow' "
            "any time.\n\n"
            "|w1. Get out.|n You're a captive underneath the Colosseum. "
            "'fight' your way out the direct way, or go quiet - 'sneak' "
            "past the guards, then 'solve' the riddle you find. Either way "
            "gets you free. See 'help fight' and 'help sneak'.\n\n"
            "|w2. The Ludus.|n Real, safe training - start at the Weapons "
            "Yard; the Wrestling Pit, Beast Taming Ring, and Champions' "
            "Court open up as you level. Use 'trainer' in any of them to "
            "see what your class can learn there, and 'statup' when you "
            "earn a stat point (every 3 levels).\n\n"
            "|w3. The Cloaca Maxima.|n Once the Ludus stops being a real "
            "challenge, the sewers beneath Rome are the real next grind - "
            "grates from the Ludus, the Subura, or the Forum all lead "
            "down. Six real depth tiers, roughly levels 5 through 25.\n\n"
            "|w4. There's more to Rome than fighting.|n 'achievements', "
            "'bounty', and 'quest' all give you real, structured things to "
            "chase. Walk the city itself, too - the Forum, the Capitoline, "
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
            "stand, and 'help' for absolutely everything else."
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

    total = len(RACES) + len(CLASSES) + len(STAT_HELP) + 11
    print("Created %d help entries." % total)