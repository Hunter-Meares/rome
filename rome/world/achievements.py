"""
Achievement definitions for the evennia.contrib.game_systems.achievements
contrib. Loaded via ACHIEVEMENT_CONTRIB_MODULES = ["world.achievements"]
in server/conf/settings.py.

Deliberately kept to a small, reliable set tied to data/events already
confirmed to exist in the game, rather than guessing at NPC tagging
that hasn't been verified - see world/combat.py (at_defeat,
award_xp's level-up branch) and world/economy.py (_buy) for where
track_achievements() actually gets called for each of these.
"""


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