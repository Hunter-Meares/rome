"""
The quest framework - the second of the two systems requested
(bounties, then quests), giving specific existing NPCs a real
mechanical payoff rather than being purely narrative color.

Design, matching what was agreed before any of this was built:
  - A generic per-character quest log (db.quest_log, a plain
    {quest_key: state} dict) rather than a bespoke attribute per
    quest, unlike the earlier one-off scripted Colosseum escape
    sequence - reusable for any future quest with zero new attributes.
  - Step types restricted to "kill" and "visit" for v1 - no fetch/
    deliver items, same simplicity call already made for bounties.
    Both starter quests below are single-objective (accept -> do the
    one thing -> report back), so quest state is just a 3-value
    string ("in_progress" / "ready" / "completed") rather than a
    step-index counter - the QUESTS dict's own shape (one step's
    worth of fields directly on the quest, not a "steps" list) is
    honest about that rather than pretending to support multi-step
    chains this doesn't actually implement yet. A real multi-step
    quest, if ever wanted, is a genuine extension of this shape, not
    a rewrite of it.
  - Starting/checking/turning in all happen through ONE command
    ('quest', no argument in the common case) used near a quest-giver
    - the same implicit-room-target convention CmdChallenge already
    established for "the relevant NPC is whoever's standing here,"
    rather than a longer 'ask <npc> about quest'. An optional
    explicit 'quest <npc>' is supported for the day a room ever has
    more than one giver, though neither starter quest needs it.
  - Shared plumbing with bounties, not a second parallel
    implementation: iter_damage_contributors (world/combat.py) is the
    one bit of boilerplate both this file's kill-step crediting and
    world/bounties.py's credit_bounty_progress would otherwise
    duplicate - safely skipping a None/deleted damage_log entry (see
    gotcha #2 in CLAUDE.md).

Two starter quests, both built entirely from content that already
existed before this file did:
  - "secession_memory": the Aventine's own elder ("the old man who
    remembers", already live) wants proof you've actually seen the
    real Secession Stone (already a lookable object in the same
    zone) - a pure "visit" quest, zero new combat content.
  - "corrupt_official": the Saepta Julia's election official (already
    live) wants a corrupt vote-tallying scribe dealt with - a "kill"
    quest against QUEST_CORRUPT_SCRIBE (world/prototypes.py), spawned
    fresh per player via the same CombatRules.spawn_personal_npc
    mechanism already used for Colosseum instance opponents and
    Augur/Haruspex summons, then relocated into the Shopping Gallery
    for a bit of "he's hiding nearby" flavor rather than confronting
    the player immediately in the officials' own room. Note:
    spawn_personal_npc renames the spawned object's `.key` to
    "<original> (<player>'s opponent)" - matched here via an explicit
    db.quest_key stamped on the object right after spawning, not by
    the (now-renamed) key, so that rename doesn't affect matching at
    all.
"""

from evennia import Command

QUESTS = {
    "secession_memory": {
        "name": "Memory of the Secession",
        "giver_key": "the old man who remembers",
        "level_required": 1,
        "step_type": "visit",
        "target_room": "The Secession Stone",
        "reward_gold": 30,
        "reward_xp": 40,
        "intro": (
            "|wThe old man leans forward.|n \"You want to hear the real "
            "story? Fine - but don't take my word alone for any of it. "
            "Go and read the stone yourself, up the way. Then come back "
            "and tell me you still think it's just an old man's tale.\""
        ),
        "reminder": (
            "\"Well? Have you actually gone and read the stone yet, or "
            "are you just here to listen to me talk?\""
        ),
        "complete": (
            "|wThe old man nods slowly.|n \"Good. Now you've seen it with "
            "your own eyes - not just heard it from mine. That's worth "
            "something to me.\""
        ),
    },
    "corrupt_official": {
        "name": "The Corrupt Count",
        "giver_key": "an election official",
        "level_required": 1,
        "step_type": "kill",
        "npc_prototype": "QUEST_CORRUPT_SCRIBE",
        "spawn_room": "Saepta Julia - Shopping Gallery",
        "reward_gold": 50,
        "reward_xp": 80,
        "intro": (
            "|wThe official lowers their voice.|n \"Between us - the "
            "tallies from this district don't add up, and I know exactly "
            "why. There's a scribe hiding out in the shopping gallery "
            "who's been paid to falsify the count. Deal with him, and "
            "there's real coin in it for you.\""
        ),
        "reminder": (
            "\"The scribe's still out there in the gallery, as far as I "
            "know. Handle it, and come find me.\""
        ),
        "complete": (
            "|wThe official exhales, visibly relieved.|n \"Word travels "
            "fast down here - I heard what happened to him. Rome's "
            "elections aren't perfect, but they're a little more honest "
            "today because of you.\""
        ),
    },
}


def start_quest(character, quest_key):
    """
    Marks the quest in_progress and, for a "kill" quest, spawns its
    personal-instance target NPC. Called from CmdQuest the first time
    a character interacts with a given giver.
    """
    quest = QUESTS[quest_key]
    log = character.db.quest_log or {}
    log[quest_key] = "in_progress"
    character.db.quest_log = log

    if quest["step_type"] == "kill":
        from evennia.utils import search
        from world.combat import COMBAT_RULES

        npc = COMBAT_RULES.spawn_personal_npc(quest["npc_prototype"], character)
        npc.db.quest_key = quest_key

        destinations = search.search_object(quest["spawn_room"], typeclass="typeclasses.rooms.Room")
        if destinations:
            npc.move_to(destinations[0], quiet=True)


def credit_quest_kill(defeated):
    """
    Called from CombatRules.at_defeat, gated directly on the defeated
    NPC's own db.quest_key being set (stamped by start_quest, not
    derived from anything Evennia's spawner does on its own - see
    gotcha #13 in CLAUDE.md for why that distinction matters) rather
    than nested inside the "any NPC with xp_reward" gate world/
    bounties.py's credit_bounty_progress shares with the ordinary XP/
    gold/loot hooks - a quest NPC's identity shouldn't depend on
    whether it happens to carry an xp_reward at all.
    """
    from world.combat import iter_damage_contributors

    quest_key = defeated.db.quest_key
    if not quest_key or quest_key not in QUESTS:
        return

    damage_log = defeated.db.damage_log or {}
    for contributor in iter_damage_contributors(damage_log):
        log = contributor.db.quest_log or {}
        if log.get(quest_key) != "in_progress":
            continue
        log[quest_key] = "ready"
        contributor.db.quest_log = log
        contributor.msg(
            "|YQuest objective complete: %s. Return to report back.|n"
            % QUESTS[quest_key]["name"]
        )


def check_quest_visit(character):
    """
    Called from CombatCharacter.at_post_move - checks every
    in-progress "visit"-type quest the character has against their
    new location.
    """
    location = character.location
    if not location:
        return

    log = character.db.quest_log or {}
    changed = False
    for quest_key, state in log.items():
        if state != "in_progress":
            continue
        quest = QUESTS.get(quest_key)
        if not quest or quest["step_type"] != "visit":
            continue
        if location.key == quest["target_room"]:
            log[quest_key] = "ready"
            changed = True
            character.msg(
                "|YQuest objective complete: %s. Return to report back.|n"
                % quest["name"]
            )
    if changed:
        character.db.quest_log = log


def list_all_quest_activity():
    """
    God-only oversight (`quest list`): every real player character
    with any quest-log activity at all, one row per (character,
    quest) pair - includes completed quests, not just active ones,
    since a god wanting a feel for "is anyone finishing these" needs
    that too. Live player state, not the static definitions - see
    quest_catalog() for that.
    """
    from world.combat import all_player_characters

    labels = {"in_progress": "in progress", "ready": "ready to turn in", "completed": "completed"}
    lines = []
    for character in all_player_characters():
        log = character.db.quest_log or {}
        for quest_key, state in log.items():
            quest = QUESTS.get(quest_key)
            if not quest:
                continue
            lines.append(
                "  %-20s %-30s %s"
                % (character.key, quest["name"], labels.get(state, state))
            )

    if not lines:
        return "No players have any quest activity."
    return "|wQuest Activity|n\n" + "\n".join(lines)


def quest_catalog():
    """
    God-only oversight (`quest list`): every quest that exists,
    reading QUESTS directly so a future quest added there shows up
    automatically with no changes needed here. The giver's location is
    looked up live off the real NPC object rather than hardcoded, so
    it can never drift out of sync with reality - if a giver's own
    location is ever wrong here, that's a real, visible sign the NPC
    itself has gone missing or been moved, not a stale reference doc.
    """
    from evennia.utils import search

    lines = []
    for quest_key, quest in QUESTS.items():
        givers = search.search_object(quest["giver_key"])
        location = givers[0].location.key if givers and givers[0].location else "not currently placed"
        lines.append(
            "|w%s|n\n  giver: %s (%s)\n  type: %s  reward: %dg/%dxp"
            % (
                quest["name"], quest["giver_key"], location,
                quest["step_type"], quest["reward_gold"], quest["reward_xp"],
            )
        )
    return "|wQuests|n\n\n" + "\n\n".join(lines)


class CmdQuest(Command):
    """
    Start, check, or turn in a quest with whichever quest-giver is
    standing in the room with you, or review your whole quest log.

    Usage:
      quest
      quest <npc>

    Use this near a real quest-giver to start a quest they offer (if
    you haven't already), see a reminder of what they're waiting on
    (if you're still working on it), or turn it in for your reward
    (once you've actually finished it). A completed quest is done for
    good - most won't repeat.

    With no quest-giver in the room, 'quest' instead shows your own
    quest log - everything you've started, finished, or still have
    outstanding.
    """

    key = "quest"
    aliases = ["quests"]
    help_category = "general"

    def func(self):
        caller = self.caller
        arg = self.args.strip().lower()

        # God-only oversight subcommands - checked first so they work
        # from anywhere and can't be shadowed by the giver-lookup
        # below (which would otherwise just silently fall through to
        # the caller's OWN log, since no giver is ever named "list").
        # See world/help_setup.py's separate "godquest" topic - kept
        # out of this command's own docstring/the player-facing
        # "quest" help entry on purpose.
        if arg in ("list", "catalog"):
            if (caller.db.level or 0) <= 100:
                caller.msg("Only gods can do that.")
                return
            if arg == "list":
                caller.msg(list_all_quest_activity())
            else:
                caller.msg(quest_catalog())
            return

        givers = {}
        for quest_key, quest in QUESTS.items():
            matches = [obj for obj in caller.location.contents if obj.key == quest["giver_key"]]
            if matches and (not arg or arg in matches[0].key.lower()):
                givers[quest_key] = matches[0]

        if not givers:
            self._show_log(caller)
            return

        quest_key, giver = next(iter(givers.items()))
        quest = QUESTS[quest_key]
        log = caller.db.quest_log or {}
        state = log.get(quest_key)

        if state is None:
            if (caller.db.level or 1) < quest["level_required"]:
                caller.msg("%s doesn't think you're ready for this yet." % giver.key)
                return
            start_quest(caller, quest_key)
            caller.msg(quest["intro"])
        elif state == "in_progress":
            caller.msg(quest["reminder"])
        elif state == "ready":
            caller.db.gold = (caller.db.gold or 0) + quest["reward_gold"]
            from world.combat import COMBAT_RULES
            COMBAT_RULES.award_xp(caller, quest["reward_xp"])
            log[quest_key] = "completed"
            caller.db.quest_log = log
            caller.msg(quest["complete"])
            caller.msg("|Y+%d gold, +%d XP.|n" % (quest["reward_gold"], quest["reward_xp"]))
            from world.titles import QUEST_TITLES, grant_earned_title
            title = QUEST_TITLES.get(quest_key)
            if title:
                grant_earned_title(caller, title)
        elif state == "completed":
            caller.msg("%s has nothing more for you." % giver.key)

    def _show_log(self, caller):
        log = caller.db.quest_log or {}
        if not log:
            caller.msg("You have no quests. Find a quest-giver and use 'quest' near them.")
            return

        labels = {"in_progress": "in progress", "ready": "ready to turn in", "completed": "completed"}
        lines = ["|wYour Quests:|n"]
        for quest_key, state in log.items():
            quest = QUESTS.get(quest_key)
            if not quest:
                continue
            lines.append("  %s - %s" % (quest["name"], labels.get(state, state)))
        caller.msg("\n".join(lines))
