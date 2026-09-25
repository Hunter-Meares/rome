"""
Achievement definitions for the evennia.contrib.game_systems.achievements
contrib. Loaded via ACHIEVEMENT_CONTRIB_MODULES = ["world.achievements"]
in server/conf/settings.py.

Deliberately kept to a small, reliable set tied to data/events already
confirmed to exist in the game, rather than guessing at NPC tagging
that hasn't been verified - see world/combat.py (at_defeat,
award_xp's level-up branch) and world/economy.py (_buy) for where
track_achievements() actually gets called for each of these.

CAUTION: the achievements contrib registers EVERY module-level dict in
this file as an achievement, so never add helper data (a mapping, a
table) as a module-level dict here - keep it in the module that uses it.
Functions are fine.
"""


def track_and_announce(character, category, tracking, count=1):
    """
    track_achievements() + announce_achievements() in one call, for a real
    player character only (an NPC has no .account and is skipped) - the
    shape every call site wants, instead of each repeating the same three
    lines. Pass category=/tracking= as keyword literals at the call site:
    tests_achievements.py finds each achievement's wiring by scanning for
    exactly that.
    """
    if not getattr(character, "account", None):
        return
    from evennia.contrib.game_systems.achievements import track_achievements

    announce_achievements(
        character, track_achievements(character, category=category, tracking=tracking, count=count)
    )


def announce_achievements(character, completed_keys):
    """
    Sends a vivid, celebratory announcement for each newly-completed
    achievement. Call this with whatever track_achievements() itself
    returns - it always returns an iterable of keys for anything
    newly completed by that call, empty if nothing completed - so
    every call site (world/combat.py, world/economy.py) just passes
    that return value straight through rather than each one building
    its own announcement independently.

    Also feeds the rumor system (world/rumors.py) - every real
    completion gets remembered so opted-in NPCs can mention it later.
    This is the one shared place every achievement completion already
    flows through, so nothing else needed to change to plug this in.
    """
    if not completed_keys:
        return

    from evennia.contrib.game_systems.achievements import get_achievement
    from world.rumors import record_rumor
    from world.titles import ACHIEVEMENT_TITLES, grant_earned_title

    for key in completed_keys:
        data = get_achievement(key)
        if not data:
            continue
        name = data.get("name", key)
        desc = data.get("desc", "")

        lines = [
            "",
            "|Y*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*|n",
            "|W  ACHIEVEMENT UNLOCKED|n",
            "|C  %s|n" % name,
        ]
        if desc:
            lines.append("|w  %s|n" % desc)
        lines.append("|Y*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*|n")
        lines.append("")

        character.msg("\n".join(lines))
        record_rumor(character.key, name)

        title = ACHIEVEMENT_TITLES.get(key)
        if title:
            grant_earned_title(character, title)

FIRST_ESCAPE = {
    "key": "first_escape",
    "name": "Free at Last",
    "desc": "Defeat the trainer in the Colosseum and earn your freedom.",
    "category": "colosseum",
    "tracking": "escaped",
}

FIRST_BLOOD = {
    "key": "first_blood",
    "name": "First Blood",
    "desc": "Defeat your first opponent in combat.",
    "category": "defeat",
    "tracking": "any_npc",
    "count": 1,
}

BATTLE_HARDENED = {
    "key": "battle_hardened",
    "name": "Battle-Hardened",
    "desc": "Defeat 25 opponents in combat.",
    "category": "defeat",
    "tracking": "any_npc",
    "count": 25,
    "prereqs": "first_blood",
}

LEGEND = {
    "key": "legend",
    "name": "Legend",
    "desc": "Reach level 100 - the highest rank a mortal can earn.",
    "category": "level",
    "tracking": "hundred",
}

FIRST_PURCHASE = {
    "key": "first_purchase",
    "name": "A Fine Purchase",
    "desc": "Buy something from a merchant for the first time.",
    "category": "buy",
    "tracking": "any",
}

# Two entries for a non-combat playstyle (world/pacifism.py). A
# leveling-milestone achievement was deliberately withheld at first -
# real math showed quests alone can't sustain leveling past level 2-3
# for a pure pacifist (secession_memory + ceres_favor = 90 XP, short
# of even the 95 XP xp_for_level() needs to reach level 3, with the
# rest of the game's quests gated behind levels a pacifist had no way
# to reach). IRON_WILL below was added once world/gathering.py +
# world/recipes.py shipped a real repeatable non-combat XP loop in
# the same session, making level 10 honestly achievable (~30 craft-
# and-sell cycles of the one recipe that exists so far) rather than
# unachievable or a rounding-margin fluke.
THE_PEACEABLE = {
    "key": "the_peaceable",
    "name": "The Peaceable",
    "desc": "Lay down your arms for good and become a pacifist.",
    "category": "pacifism",
    "tracking": "became",
}

IRON_WILL = {
    "key": "iron_will",
    "name": "Iron Will",
    "desc": "Reach level 10 as a pacifist, without ever raising a hand in combat.",
    "category": "level",
    "tracking": "pacifist_ten",
}


# ----------------------------------------------------------------------------
# EARLY-GAME MILESTONES - a quick run of wins across a new player's first
# hours, for BOTH playstyles (a fighter and a pacifist crafter each hit
# several of these in their first session). Added from a direct request to
# make the first hour feel rewarding; each is announced with the usual banner
# and gossiped about by NPCs, and a few grant an earned title (world/
# titles.py's ACHIEVEMENT_TITLES). Counts run concurrently (no prereqs) so
# "25" means exactly 25.
# ----------------------------------------------------------------------------

FIRST_GATHER = {
    "key": "first_gather",
    "name": "Fruits of the Land",
    "desc": "Gather a material from the wild for the first time.",
    "category": "gather",
    "tracking": "any",
}

FIRST_CRAFT = {
    "key": "first_craft",
    "name": "Apprentice's Hands",
    "desc": "Craft your first item.",
    "category": "craft",
    "tracking": "any",
}

CRAFT_25 = {
    "key": "craft_25",
    "name": "Steady Hands",
    "desc": "Craft 25 items - the work has stopped being new.",
    "category": "craft",
    "tracking": "any",
    "count": 25,
}

FIRST_SALE = {
    "key": "first_sale",
    "name": "Open for Business",
    "desc": "Sell something to a merchant for the first time.",
    "category": "sell",
    "tracking": "any",
}

FIRST_QUEST = {
    "key": "first_quest",
    "name": "A Task Well Done",
    "desc": "Complete your first quest.",
    "category": "quest",
    "tracking": "any",
}

QUESTS_5 = {
    "key": "quests_5",
    "name": "The Reliable",
    "desc": "Complete five quests - the sort of person Rome's citizens ask twice.",
    "category": "quest",
    "tracking": "any",
    "count": 5,
}

FIRST_LESSON = {
    "key": "first_lesson",
    "name": "Quick Study",
    "desc": "Learn your first spell or skill from a trainer.",
    "category": "learn",
    "tracking": "any",
}

FIRST_PARTY_KILL = {
    "key": "first_party_kill",
    "name": "Stronger Together",
    "desc": "Help defeat an enemy as part of a party.",
    "category": "defeat",
    "tracking": "party_kill",
}

LEVEL_5 = {
    "key": "level_5",
    "name": "Finding Your Feet",
    "desc": "Reach level 5.",
    "category": "level",
    "tracking": "five",
}

LEVEL_10 = {
    "key": "level_10",
    "name": "Seasoned",
    "desc": "Reach level 10.",
    "category": "level",
    "tracking": "ten",
}

LEVEL_25 = {
    "key": "level_25",
    "name": "Veteran of Rome",
    "desc": "Reach level 25.",
    "category": "level",
    "tracking": "twentyfive",
}

BEYOND_THE_WALLS = {
    "key": "beyond_the_walls",
    "name": "Beyond the Walls",
    "desc": "Step out through the Porta Flaminia onto the wilderness road for the first time.",
    "category": "explore",
    "tracking": "wilderness",
}

THE_LONG_ROAD = {
    "key": "the_long_road",
    "name": "The Long Road",
    "desc": "Walk the whole wilderness road and reach the Germanic Stronghold.",
    "category": "explore",
    "tracking": "germania",
}

TWICE_BORN = {
    "key": "twice_born",
    "name": "Twice-Born",
    "desc": "Return from the Underworld.",
    "category": "death",
    "tracking": "returned",
}

