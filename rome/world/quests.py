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

Nine more quests were added on top of those two, all still within this
same single-objective shape (one giver, one kill-or-visit objective,
gold + XP + an optional title) - deliberately, since that's all the
engine actually supports. Two constraints worth knowing before adding
another:

  - One giver can only ever offer ONE quest. CmdQuest matches a giver
    by exact key in the caller's room and always offers the first
    matching quest in QUESTS order, so a second quest sharing a
    giver_key would never be reachable. Every quest here uses its own
    distinct giver.
  - A "kill" quest's npc_prototype must NOT be a RespawningNPC
    (unlike the persistent sewer/arena fighters) - at_defeat sends a
    RespawningNPC through its respawn branch before it ever reaches
    the personal-instance delete branch, so a quest target built that
    way would come back to life instead of staying dead. Use a plain
    HostileNPC, as QUEST_CORRUPT_SCRIBE and the other quest targets in
    world/prototypes.py do.

Optional per-quest "class_bonus": a class-FLAVORED bonus, deliberately
not a class LOCK. Every quest stays open to everyone - a matching class
just gets a line or two of extra recognition from the giver plus a
small flat gold/XP top-up on turn-in. With a player base this small, a
hard lock would put most of any given quest's audience out of reach and
leave a player who wandered up to the "wrong" giver staring at a
refusal. Shape:

    "class_bonus": {
        "classes": ["augur"],      # who it applies to (lowercase class keys)
        "bonus_gold": 15,
        "bonus_xp": 60,
        "intro": "...",            # shown right after the normal intro
        "complete": "...",         # shown right after the normal turn-in
    },
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
    # ------------------------------------------------------------------
    # Nine early/mid quests, each pulling a new player toward a
    # different corner of a zone that otherwise had nothing to DO in it,
    # and between them giving every one of the eight classes a matching
    # class_bonus somewhere. Ordered roughly by level_required.
    # ------------------------------------------------------------------
    "ceres_favor": {
        "name": "Ceres Asks a Favor",
        "giver_key": "a priest of Ceres",
        "level_required": 2,
        "step_type": "visit",
        "target_room": "Market Row - Back Stalls",
        "reward_gold": 30,
        "reward_xp": 50,
        "intro": (
            "|wThe priest of Ceres presses a small coin into your palm.|n "
            "\"The harvest rites call for a particular herb, and the woman "
            "who sells it keeps her stall in the back of the Subura's "
            "market row - a poor walk for a man my age. Go and find her. "
            "Buy something useful while you're there; the coin is yours "
            "to spend.\""
        ),
        "reminder": (
            "\"Have you made it out to the herbalist's stall in the "
            "Subura's back market row yet? The rites won't wait "
            "forever.\""
        ),
        "complete": (
            "|wThe priest of Ceres smiles, warmer than before.|n \"You've "
            "seen her stall, then - good. Now you know where a person goes "
            "when they're ill and the temple's too far. Remember it; Rome "
            "will make you need it.\""
        ),
        "class_bonus": {
            "classes": ["medicus"],
            "bonus_gold": 8,
            "bonus_xp": 15,
            "intro": (
                "|xThe priest studies you a moment. \"A healer, unless I "
                "mistake it. Then you'll want to see her stock for "
                "yourself.\"|n"
            ),
            "complete": (
                "|x\"A healer knows a good stall on sight. Keep it in "
                "mind - I suspect the two of you will have a great deal "
                "to talk about.\"|n"
            ),
        },
    },
    "grain_doesnt_add_up": {
        "name": "The Grain Doesn't Add Up",
        "giver_key": "a grain-dole administrator",
        "level_required": 3,
        "step_type": "kill",
        "npc_prototype": "QUEST_GRAIN_SKIMMER",
        "spawn_room": "An Emporium Warehouse",
        "reward_gold": 45,
        "reward_xp": 80,
        "intro": (
            "|wThe administrator taps the ledger without looking up.|n "
            "\"Forty sacks short, three months running - and the dole "
            "doesn't feed itself. I can't leave this hall, but I know "
            "where the sacks go: a factor's been skimming out of an "
            "Emporium warehouse, down by the river. Find him. Make it "
            "stop.\""
        ),
        "reminder": (
            "\"The factor's still down at the Emporium warehouse, as far "
            "as I know. Every day he's out there, somebody's family goes "
            "a little hungrier. Go on.\""
        ),
        "complete": (
            "|wThe administrator lets out a long breath and closes the "
            "ledger.|n \"The counts will take months to untangle, but "
            "they'll stop getting worse. That's more than I had this "
            "morning.\""
        ),
        "class_bonus": {
            "classes": ["speculator"],
            "bonus_gold": 12,
            "bonus_xp": 20,
            "intro": (
                "|xHe glances at you a moment longer. \"You've the look of "
                "someone who reads a ledger for what it doesn't say. Good. "
                "I'll pay for that.\"|n"
            ),
            "complete": (
                "|xHe slides a little extra across the table. \"For the "
                "eye. Most people would have hit him first and asked what "
                "he'd taken later.\"|n"
            ),
        },
    },
    "alley_debts": {
        "name": "Debts in the Dead-End Alley",
        "giver_key": "a moneylender",
        "level_required": 4,
        "step_type": "kill",
        "npc_prototype": "QUEST_LOAN_ENFORCER",
        "spawn_room": "A Dead-End Alley",
        "reward_gold": 55,
        "reward_xp": 110,
        "intro": (
            "|wThe moneylender doesn't look up from counting coins.|n "
            "\"Business is business, and I don't lend to fools. But "
            "there's a man in a dead-end alley off the Subura who's been "
            "leaning on my clients - telling them to pay him instead of "
            "me. That's my money he's frightening out of their pockets. "
            "Discourage him. Permanently, if he insists.\""
        ),
        "reminder": (
            "\"He's still working that dead-end alley in the Subura. "
            "Every day he does, another client pays the wrong man. "
            "Go.\""
        ),
        "complete": (
            "|wThe moneylender counts your payment twice, out of "
            "habit.|n \"Don't look at me like that. I lend at a fair rate "
            "and I don't break legs. He did. Whatever you think of me, "
            "you did the neighborhood a service.\""
        ),
        "class_bonus": {
            "classes": ["gladiator"],
            "bonus_gold": 14,
            "bonus_xp": 28,
            "intro": (
                "|xHe eyes your scars. \"You've been in a real fight "
                "before. Good - this one will want to talk with his fists "
                "first.\"|n"
            ),
            "complete": (
                "|x\"An arena hand - I should have guessed. A little "
                "extra, for a job done the way it ought to be.\"|n"
            ),
        },
    },
    "mourners_leave": {
        "name": "What Mourners Leave",
        "giver_key": "a somber historian",
        "level_required": 5,
        "step_type": "visit",
        "target_room": "Temple of Julius Caesar - the Outer Altar",
        "reward_gold": 40,
        "reward_xp": 110,
        "intro": (
            "|wThe historian looks up from a half-finished scroll.|n \"I "
            "write about the Ides of March. The senators, the daggers - "
            "everyone writes that part. I want the part nobody writes: "
            "what ordinary Romans still leave at the altar where Caesar "
            "was burned. Go and look. Then come back and tell me what "
            "you saw.\""
        ),
        "reminder": (
            "\"Have you been to the altar at the Temple of Julius Caesar "
            "yet? Go and look properly - don't just glance.\""
        ),
        "complete": (
            "|wThe historian writes for a long moment, then sets down the "
            "stylus.|n \"Small things, left by small people - that's the "
            "true measure of a man. Thank you. This will go in the "
            "book.\""
        ),
    },
    "watch_wants_a_name": {
        "name": "The Watch Wants a Name",
        "giver_key": "Watch-Captain Rufio",
        "level_required": 6,
        "step_type": "kill",
        "npc_prototype": "QUEST_VIGILES_DESERTER",
        "spawn_room": "A Hidden Alcove",
        "reward_gold": 90,
        "reward_xp": 220,
        "intro": (
            "|wCaptain Rufio doesn't bother with pleasantries.|n \"One of "
            "my own - a Vigiles man - took the fire-brigade's payroll and "
            "ran, down into the Cloaca. He's holed up in some hidden "
            "alcove where the old drains meet. I can't take my men into "
            "the tunnels for one thief. You can. Bring him down.\""
        ),
        "reminder": (
            "\"The deserter's still down in the Cloaca, somewhere in a "
            "hidden alcove. Every day he's loose, my men wonder whether "
            "staying honest is worth it.\""
        ),
        "complete": (
            "|wRufio's jaw tightens, then loosens a fraction.|n \"Good. "
            "The men will hear he didn't get away with it. That matters "
            "more than the coin ever did.\""
        ),
        "class_bonus": {
            "classes": ["venator"],
            "bonus_gold": 22,
            "bonus_xp": 55,
            "intro": (
                "|x\"You've the look of someone who tracks for a living. "
                "The sewers are just another forest, if you squint.\"|n"
            ),
            "complete": (
                "|x\"A hunter's work, and clean. Take a little extra - the "
                "Watch can spare it for a job done right.\"|n"
            ),
        },
    },
    "unquiet_shade": {
        "name": "The Unquiet Shade",
        "giver_key": "a shade at the water's edge",
        "level_required": 6,
        "step_type": "visit",
        "target_room": "Grove of Champions",
        "reward_gold": 70,
        "reward_xp": 200,
        "intro": (
            "|wThe shade at the water's edge turns toward you, its outline "
            "wavering like a reflection in disturbed water.|n \"I drank "
            "from the river to forget the war, and I forgot too much - "
            "my general's name, my own. They say the champions who are "
            "remembered keep their names in a grove beyond the gates of "
            "Elysium. I can't cross on my own. Go and look for me, and "
            "then tell me what it is to be remembered.\""
        ),
        "reminder": (
            "\"Have you found the Grove of Champions yet? I've waited so "
            "long. A little longer is nothing.\""
        ),
        "complete": (
            "|wThe shade's outline steadies for the first time.|n \"So "
            "the remembered still carry their names. Then perhaps I'll "
            "find mine yet. Thank you - I think I can wait more easily "
            "now.\""
        ),
        "class_bonus": {
            "classes": ["haruspex"],
            "bonus_gold": 18,
            "bonus_xp": 50,
            "intro": (
                "|x\"You speak to the dead like one who's had practice. "
                "That gives me hope.\"|n"
            ),
            "complete": (
                "|x\"You didn't flinch from me. Most living folk do. Take "
                "a little more, for the kindness.\"|n"
            ),
        },
    },
    "boundary_stone_question": {
        "name": "The Boundary Stone's Question",
        "giver_key": "a watchful augur",
        "level_required": 8,
        "step_type": "visit",
        "target_room": "The Regia - Calendar Archive",
        "reward_gold": 60,
        "reward_xp": 250,
        "intro": (
            "|wThe augur doesn't take his eyes off the sky.|n \"The birds "
            "are restless, and I can't tell whether it's the weather or "
            "the day. If the calendar marks today as nefas - ill-omened - "
            "I've no business taking the auspices at all. The calendar "
            "priests keep their records in the Regia's archive. Go and "
            "ask what the day is. Then come and tell me.\""
        ),
        "reminder": (
            "\"Have you been to the Regia's calendar archive yet? I can't "
            "read these birds until I know what day it is.\""
        ),
        "complete": (
            "|wThe augur finally lowers his gaze.|n \"Ah. That explains "
            "the birds. Thank you - I'd have read them wrong, and a "
            "wrongly read omen is worse than none.\""
        ),
        "class_bonus": {
            "classes": ["augur"],
            "bonus_gold": 15,
            "bonus_xp": 62,
            "intro": (
                "|x\"You're of the augural college yourself? Then you know "
                "exactly why I can't simply guess.\"|n"
            ),
            "complete": (
                "|x\"One augur to another - you saw the problem at once. "
                "Take a little more; you've earned it.\"|n"
            ),
        },
    },
    "silent_chamber": {
        "name": "The Silent Chamber",
        "giver_key": "the site caretaker",
        "level_required": 10,
        "step_type": "visit",
        "target_room": "A Half-Buried Chamber",
        "reward_gold": 80,
        "reward_xp": 320,
        "intro": (
            "|wThe caretaker wrings his hands.|n \"An antiquarian went "
            "down to a half-buried chamber below the palace three days "
            "ago - said he'd only be an hour. Nobody's seen him since. "
            "I'm paid to mind the ruins, not to go crawling into them. "
            "Would you go and look?\""
        ),
        "reminder": (
            "\"Have you looked in on that half-buried chamber yet? I "
            "keep imagining the worst.\""
        ),
        "complete": (
            "|wThe caretaker sags with relief.|n \"Alive, cataloguing, "
            "and quite unaware three days have passed? That sounds "
            "exactly like him. Thank you - I'd have spent the whole night "
            "imagining worse.\""
        ),
        "class_bonus": {
            "classes": ["barbarian"],
            "bonus_gold": 20,
            "bonus_xp": 80,
            "intro": (
                "|x\"You don't look the sort to frighten easily in old "
                "ruins. Good - I'll admit I'm a coward.\"|n"
            ),
            "complete": (
                "|x\"Not everyone would have walked into Nero's Golden "
                "House alone and unbothered. A little extra.\"|n"
            ),
        },
    },
    "tomb_robber": {
        "name": "The Tomb-Robber",
        "giver_key": "the tomb's caretaker",
        "level_required": 12,
        "step_type": "kill",
        "npc_prototype": "QUEST_TOMB_ROBBER",
        "spawn_room": "The Chamber of Urns",
        "reward_gold": 120,
        "reward_xp": 500,
        "intro": (
            "|wThe caretaker keeps his voice low, as if the tomb might "
            "overhear.|n \"Somebody's been in the Chamber of Urns. "
            "Nothing taken that I can prove - but the seals are "
            "scratched, and I've heard digging at night. This is "
            "Augustus's own resting place. I'm no fighter. Would you "
            "deal with whoever it is?\""
        ),
        "reminder": (
            "\"He's still in the Chamber of Urns, as far as I can tell. "
            "Every night he digs, the first Emperor's tomb grows a "
            "little less sacred.\""
        ),
        "complete": (
            "|wThe caretaker bows his head toward the inner chamber.|n "
            "\"The dead are quiet again. I'll see the seals repaired and "
            "the record kept - your name will be in it, if you like.\""
        ),
        "class_bonus": {
            "classes": ["legionary"],
            "bonus_gold": 30,
            "bonus_xp": 125,
            "intro": (
                "|x\"You've the bearing of one of the Emperor's own "
                "soldiers. This tomb was built for the man who raised "
                "your legions - I'd be grateful for a soldier's hand.\"|n"
            ),
            "complete": (
                "|x\"A soldier defending his emperor's rest. Take a "
                "little more - Augustus would have wanted it.\"|n"
            ),
        },
    },
}


def class_bonus_for(character, quest):
    """
    The quest's class_bonus dict if `character`'s class is one it
    applies to, else None - see this module's own docstring for why
    this is a bonus and not a lock. A quest with no class_bonus at all,
    or a character with no class set, is simply None: every quest
    behaves exactly as before for anyone the bonus doesn't match.
    """
    bonus = quest.get("class_bonus")
    if not bonus:
        return None
    player_class = (character.db.player_class or "").lower()
    if player_class and player_class in bonus.get("classes", []):
        return bonus
    return None


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
        entry = (
            "|w%s|n\n  giver: %s (%s)\n  type: %s  reward: %dg/%dxp"
            % (
                quest["name"], quest["giver_key"], location,
                quest["step_type"], quest["reward_gold"], quest["reward_xp"],
            )
        )
        bonus = quest.get("class_bonus")
        if bonus:
            entry += "\n  class bonus: %s +%dg/+%dxp" % (
                "/".join(bonus["classes"]), bonus["bonus_gold"], bonus["bonus_xp"],
            )
        lines.append(entry)
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
            bonus = class_bonus_for(caller, quest)
            if bonus:
                caller.msg(bonus["intro"])
        elif state == "in_progress":
            caller.msg(quest["reminder"])
        elif state == "ready":
            bonus = class_bonus_for(caller, quest)
            gold = quest["reward_gold"] + (bonus["bonus_gold"] if bonus else 0)
            xp = quest["reward_xp"] + (bonus["bonus_xp"] if bonus else 0)
            caller.db.gold = (caller.db.gold or 0) + gold
            from world.combat import COMBAT_RULES
            COMBAT_RULES.award_xp(caller, xp)
            log[quest_key] = "completed"
            caller.db.quest_log = log
            caller.msg(quest["complete"])
            if bonus:
                caller.msg(bonus["complete"])
            caller.msg(
                "|Y+%d gold, +%d XP.|n%s"
                % (gold, xp, " |x(class bonus included)|n" if bonus else "")
            )
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
