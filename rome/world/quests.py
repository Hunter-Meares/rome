"""
The quest framework - the second of the two systems requested
(bounties, then quests), giving specific existing NPCs a real
mechanical payoff rather than being purely narrative color.

Design, matching what was agreed before any of this was built:
  - A generic per-character quest log (db.quest_log, a plain
    {quest_key: state} dict) rather than a bespoke attribute per
    quest, unlike the earlier one-off scripted Colosseum escape
    sequence - reusable for any future quest with zero new attributes.
  - Step types: "kill", "visit", and (added later) "talk" - no
    fetch/deliver items, same simplicity call already made for
    bounties. A quest is one or more steps worked through in order. The
    original two starter quests are single-objective (accept -> do the
    one thing -> report back) and are still written the flat original
    way; a quest with several steps carries an explicit "steps" list
    instead. Coarse state stays the plain 3-value string in
    db.quest_log ("in_progress" / "ready" / "completed") either way,
    with which step an in-progress quest is on kept separately in
    db.quest_steps - see the STEPS block below.
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

Nine more quests were added on top of those two, in the same flat
single-step shape (one giver, one kill-or-visit objective, gold + XP +
an optional title). Two multi-step investigations ("missing_quaestor",
"vestals_flame") followed once steps existed. Constraints worth knowing
before adding another:

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
        "objective": "Go and read the Secession Stone on the Aventine, then report back to the old man who remembers.",
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
        "objective": "Find the corrupt scribe hiding in the Saepta Julia's Shopping Gallery and deal with him.",
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
        "objective": "Visit the herbalist's stall at Market Row - Back Stalls, in the Subura.",
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
        "objective": "Find the grain-skimming factor at An Emporium Warehouse and stop him.",
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
        "objective": "Deal with the loan-shark's enforcer in A Dead-End Alley, in the Subura.",
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
        "objective": "Visit the Outer Altar at the Temple of Julius Caesar and see what mourners leave there.",
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
        "objective": "Bring down the Vigiles deserter hiding in A Hidden Alcove, deep in the Cloaca Maxima.",
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
        "objective": "Find the Grove of Champions, beyond the gates of Elysium.",
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
        "objective": "Find out what day it is at the Regia's Calendar Archive.",
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
        "objective": "Look in on A Half-Buried Chamber beneath the Domus Aurea.",
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
        "objective": "Deal with the tomb-robber in the Chamber of Urns, inside the Mausoleum of Augustus.",
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
    # ------------------------------------------------------------------
    # Multi-step quests: an explicit "steps" list instead of the flat
    # single-step fields (see the STEPS block further down). Both are
    # investigations, and both use every step type between them.
    # ------------------------------------------------------------------
    "missing_quaestor": {
        "name": "The Missing Quaestor",
        "giver_key": "a treasury clerk",
        "level_required": 8,
        "reward_gold": 110,
        "reward_xp": 350,
        "intro": (
            "|wThe treasury clerk keeps glancing at the vault door.|n \"A "
            "junior quaestor was auditing the Aerarium's ledgers three "
            "nights ago. He didn't come in the next morning - and neither "
            "did the ledgers he was working from. The guard on the vault "
            "was on watch that night; start with him. And be quiet about "
            "it. Whoever's behind this has friends in this building.\""
        ),
        "reminder": (
            "\"Any word yet? The longer he's missing, the fewer answers "
            "we'll have.\""
        ),
        "complete": (
            "|wThe clerk exhales, long and unsteady.|n \"So he wasn't the "
            "thief - he was the man who caught the thief. I'll see the "
            "Treasury's books corrected and his name cleared. Thank you - "
            "and thank the gods someone in this city still checks a "
            "ledger.\""
        ),
        "steps": [
            {
                "type": "talk",
                "npc_key": "a treasury guard",
                "objective": "Ask the treasury guard in the Temple of Saturn's Treasury Vault what he saw that night.",
                "reminder": "\"The guard down in the vault was on watch that night. Ask him - he may not volunteer it.\"",
                "advance": (
                    "|wThe treasury guard shifts uneasily.|n \"I saw him go, "
                    "aye. The quaestor slipped out by the Basilica Julia's "
                    "rear passage near midnight, a satchel under his arm. He "
                    "wasn't alone - two men followed him, and he didn't look "
                    "like a man leaving by choice. The rear grate down to the "
                    "sewers was hanging open by morning.\""
                ),
            },
            {
                "type": "visit",
                "target_room": "Beneath the Basilica Grate",
                "objective": "Go down to the sewer grate beneath the Basilica Julia - the room called Beneath the Basilica Grate.",
                "reminder": "\"The guard says he vanished through the grate under the Basilica Julia. Go and look.\"",
                "advance": (
                    "|wThe grate's bars are bent outward, and the stone around "
                    "it is scuffed with fresh boot-scrapes - several sets. "
                    "Whatever happened here, it wasn't quiet.|n"
                ),
            },
            {
                "type": "visit",
                "target_room": "The Records Drop",
                "objective": "Follow the drains to The Records Drop and search for the quaestor's ledgers.",
                "reminder": "\"Follow the drains from that grate. A satchel doesn't just vanish - somewhere down there it ended up.\"",
                "advance": (
                    "|wHalf-buried in the muck: a leather satchel, split open, "
                    "and torn ledger pages swollen with damp. The figures on "
                    "them don't match the Treasury's own books - not by a "
                    "wide margin. Someone was skimming, and the quaestor had "
                    "found out. Beside the satchel, a boot-print that isn't "
                    "his, heading deeper in.|n"
                ),
            },
            {
                "type": "kill",
                "npc_prototype": "QUEST_QUAESTOR_FIXER",
                "spawn_room": "The Last Dressed Stones",
                "objective": "Find the man who followed the quaestor down - he's gone to ground near The Last Dressed Stones.",
                "reminder": "\"Whoever followed him down there is still in the Cloaca, near the last of the dressed stones. Finish it.\"",
            },
        ],
        "class_bonus": {
            "classes": ["speculator"],
            "bonus_gold": 28,
            "bonus_xp": 88,
            "intro": (
                "|x\"You've the eye for figures that don't add up. This is "
                "exactly the kind of thing you were made for.\"|n"
            ),
            "complete": (
                "|x\"You followed the money the way it ought to be "
                "followed. A little extra for the trouble.\"|n"
            ),
        },
    },
    "vestals_flame": {
        "name": "The Vestal's Flame",
        "giver_key": "the Pontifex's attendant",
        "level_required": 15,
        "reward_gold": 350,
        "reward_xp": 750,
        "intro": (
            "|wThe Pontifex's attendant speaks barely above a whisper.|n "
            "\"The Sacred Fire of Vesta has gone out. It has burned "
            "unbroken for longer than Rome has had emperors - and if it "
            "isn't found to be sabotage, the Vestals will be blamed, and "
            "you know what that means for them. The Pontifex wants this "
            "looked into quietly. Begin at the hearth itself.\""
        ),
        "reminder": (
            "\"The Pontifex grows impatient. Every hour the fire stays "
            "dark, the city's luck runs thinner. Please - hurry.\""
        ),
        "complete": (
            "|wThe attendant closes his eyes for a long moment.|n \"The "
            "fire will be relit at dawn, and the Vestals will keep their "
            "place. The Pontifex will hear who kept the flame this night - "
            "and Rome will never know how close it came.\""
        ),
        "steps": [
            {
                "type": "visit",
                "target_room": "Temple of Vesta - the Sacred Fire",
                "objective": "Examine the Sacred Fire in the Temple of Vesta.",
                "reminder": "\"Begin at the hearth itself - the Temple of Vesta. See what the fire left behind.\"",
                "advance": (
                    "|wThe hearth is cold - and it should never be, not ever. "
                    "Around the hearth-stone the marble is scored with fresh "
                    "pry-marks, and caught on a splinter is a shred of coarse "
                    "cloth no Vestal would ever wear. The fire didn't fail. "
                    "Someone put it out.|n"
                ),
            },
            {
                "type": "talk",
                "npc_key": "a calendar priest",
                "objective": "Ask the calendar priest in the Regia's Calendar Archive about the fire-watch roster.",
                "reminder": "\"The calendar priest at the Regia keeps the fire-watch rosters. Something about them troubled me - ask him.\"",
                "advance": (
                    "|wThe calendar priest goes very still.|n \"The duty "
                    "roster for the fire-watch was altered three nights ago. "
                    "The hand is a copyist's - careful, practiced - but the "
                    "payment came from the Subura, from a man who hires out "
                    "for this kind of work. You'll find him in a "
                    "doubling-back alley off the market row, if you know "
                    "where to look.\""
                ),
            },
            {
                "type": "kill",
                "npc_prototype": "QUEST_FLAME_SABOTEUR",
                "spawn_room": "A Doubling-Back Alley",
                "objective": "Find the saboteur hiding in A Doubling-Back Alley, in the Subura.",
                "reminder": "\"The priest says the man who did it is in a doubling-back alley in the Subura. End this.\"",
            },
        ],
        "class_bonus": {
            "classes": ["augur"],
            "bonus_gold": 85,
            "bonus_xp": 190,
            "intro": (
                "|x\"An augur. The Pontifex will be relieved - a dead flame "
                "is the gravest omen there is, and you'll know how to read "
                "it.\"|n"
            ),
            "complete": (
                "|x\"You understood the omen as well as the crime. The "
                "College will hear of it. Take a little more.\"|n"
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


# ----------------------------------------------------------------------------
# STEPS
# ----------------------------------------------------------------------------
# A quest is a list of one or more steps, worked through in order. Most
# quests here are still a single step, written the original flat way
# (step_type/target_room/etc. directly on the quest) - get_steps()
# normalizes that into a one-item list, so nothing about an existing quest
# or an existing player's quest_log had to change. A multi-step quest
# instead carries an explicit "steps" list (see e.g. "missing_quaestor").
#
# Progress lives in TWO places, deliberately kept apart so the original
# 3-value quest_log ("in_progress"/"ready"/"completed") means exactly what
# it always did: quest_log stays the coarse state, and a separate
# db.quest_steps {quest_key: step_index} records which step an in_progress
# quest is currently on (absent = step 0, which is also what every quest
# already in progress before this existed reads as).
#
# Step types:
#   "visit" - arrive in target_room.
#   "kill"  - defeat a personal-instance NPC (npc_prototype) that is
#             spawned when the step begins and placed in spawn_room.
#   "talk"  - use 'quest' while standing with the NPC named npc_key
#             (anyone, not only the giver). This is what lets an
#             investigation send you to a witness.
# Every step needs an "objective" (what the player is told to do, and what
# the quest log shows). A step may also carry "advance" (story text shown
# the moment the step is completed - the witness's answer, what you find at
# the scene) and "reminder" (the giver's words if you ask them mid-step;
# falls back to the quest's own "reminder").

STEP_TYPES = ("kill", "visit", "talk")


def get_steps(quest):
    """A quest's steps as a list of step dicts (see the block above)."""
    if "steps" in quest:
        return quest["steps"]
    step = {"type": quest["step_type"]}
    for field in ("target_room", "npc_prototype", "spawn_room", "objective", "reminder", "advance"):
        if field in quest:
            step[field] = quest[field]
    return [step]


def get_step_index(character, quest_key):
    """Which step (0-based) an in-progress quest is on. Clamped to a real
    step, so a stale or corrupt value can never index off the end."""
    idx = (character.db.quest_steps or {}).get(quest_key, 0)
    steps = get_steps(QUESTS[quest_key])
    return max(0, min(idx, len(steps) - 1))


def current_step(character, quest_key):
    idx = get_step_index(character, quest_key)
    return idx, get_steps(QUESTS[quest_key])[idx]


def objective_text(step):
    """What the player is told to do for this step. Every real quest
    defines one explicitly (tests_quests.py enforces it); the fallback is
    only so a half-written step can't crash the log."""
    if step.get("objective"):
        return step["objective"]
    if step["type"] == "visit":
        return "Go to %s." % step.get("target_room", "the place you were sent")
    if step["type"] == "kill":
        return "Find and defeat your target in %s." % step.get("spawn_room", "the place you were sent")
    return "Speak with %s." % step.get("npc_key", "the person you were sent to")


def _set_step_index(character, quest_key, idx):
    steps = dict(character.db.quest_steps or {})
    steps[quest_key] = idx
    character.db.quest_steps = steps


def _clear_progress(character, quest_key):
    """Drops the step/target bookkeeping once a quest is turned in."""
    for attr in ("quest_steps", "quest_targets"):
        data = dict(character.attributes.get(attr) or {})
        if quest_key in data:
            del data[quest_key]
            character.attributes.add(attr, data)


def _spawn_kill_target(character, quest_key, idx, step):
    """
    Spawns this step's personal-instance target and remembers it on the
    character (db.quest_targets) so ensure_kill_target() can tell later
    whether it still exists. Stamped with the step index too, so a target
    left over from an EARLIER step can never be credited toward a later
    one.
    """
    from evennia.utils import search
    from world.combat import COMBAT_RULES

    npc = COMBAT_RULES.spawn_personal_npc(step["npc_prototype"], character)
    npc.db.quest_key = quest_key
    npc.db.quest_step = idx

    targets = dict(character.db.quest_targets or {})
    targets[quest_key] = npc
    character.db.quest_targets = targets

    destinations = search.search_object(step["spawn_room"], typeclass="typeclasses.rooms.Room")
    if destinations:
        npc.move_to(destinations[0], quiet=True)
    return npc


def begin_step(character, quest_key, idx):
    """Makes `idx` the current step, spawning its target if it's a kill."""
    _set_step_index(character, quest_key, idx)
    step = get_steps(QUESTS[quest_key])[idx]
    if step["type"] == "kill":
        _spawn_kill_target(character, quest_key, idx, step)


def start_quest(character, quest_key):
    """
    Marks the quest in_progress and begins its first step (for a "kill"
    step, spawning its personal-instance target NPC). Called from
    CmdQuest the first time a character interacts with a given giver.
    """
    log = character.db.quest_log or {}
    log[quest_key] = "in_progress"
    character.db.quest_log = log
    begin_step(character, quest_key, 0)


def advance_quest(character, quest_key):
    """
    The current step's objective has just been met. Moves to the next
    step (telling the player what it is), or - if that was the last step
    - marks the quest ready to turn in.
    """
    quest = QUESTS[quest_key]
    steps = get_steps(quest)
    idx = get_step_index(character, quest_key)
    step = steps[idx]

    if idx + 1 < len(steps):
        character.msg("|YObjective complete: %s|n" % objective_text(step))
        if step.get("advance"):
            character.msg(step["advance"])
        begin_step(character, quest_key, idx + 1)
        character.msg("|wNext objective:|n %s" % objective_text(steps[idx + 1]))
        return

    if step.get("advance"):
        character.msg(step["advance"])
    log = character.db.quest_log or {}
    log[quest_key] = "ready"
    character.db.quest_log = log
    character.msg(
        "|YQuest objective complete: %s. Return to report back.|n" % quest["name"]
    )


def quest_target_is_live(npc):
    """
    True if `npc` is a quest target its owner still needs - the quest is
    in progress and on the very step this NPC was spawned for. Used by
    InstanceCleanupTimer and `cleanupnpcs` to leave it alone.

    Real, confirmed gap this closes: InstanceCleanupTimer deletes ANY
    personal-instance NPC that isn't mid-fight after 10 minutes, with no
    exemption for quest targets - so a player who accepted a kill quest
    and then took longer than that to reach the target (a walk to the
    sewers, a logout) found it gone, and the quest could never be
    finished. That affected the original "corrupt_official" quest as
    well as the newer ones. (ensure_kill_target below is the second line
    of defence for when a target goes missing anyway.)
    """
    quest_key = npc.db.quest_key
    owner = npc.db.instance_owner
    if not quest_key or quest_key not in QUESTS or not owner or not owner.pk:
        return False
    if (owner.db.quest_log or {}).get(quest_key) != "in_progress":
        return False
    idx, step = current_step(owner, quest_key)
    return step["type"] == "kill" and idx == (npc.db.quest_step or 0)


def ensure_kill_target(character, quest_key):
    """
    If the quest's current step is a kill and its target no longer
    exists, spawns a fresh one. Returns True only if it had to respawn.

    A target already alive is left alone, including one spawned before
    this bookkeeping existed (no db.quest_targets entry): those are
    found by owner + quest_key and adopted rather than duplicated.
    """
    idx, step = current_step(character, quest_key)
    if step["type"] != "kill":
        return False

    target = (character.db.quest_targets or {}).get(quest_key)
    if target is not None and target.pk:
        return False

    from world.combat import HostileNPC

    for npc in HostileNPC.objects.filter(db_attributes__db_key="quest_key"):
        if npc.pk and npc.db.quest_key == quest_key and npc.db.instance_owner == character:
            targets = dict(character.db.quest_targets or {})
            targets[quest_key] = npc
            character.db.quest_targets = targets
            return False

    _spawn_kill_target(character, quest_key, idx, step)
    return True


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

    Only counts toward a character whose quest is on the very step this
    NPC was spawned for (db.quest_step, absent = 0), so killing a target
    from an earlier step can't skip anyone ahead.
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
        idx, step = current_step(contributor, quest_key)
        if step["type"] != "kill" or idx != (defeated.db.quest_step or 0):
            continue
        advance_quest(contributor, quest_key)


def check_quest_visit(character):
    """
    Called from CombatCharacter.at_post_move. For every in-progress quest:
    completes a "visit" step if the character just arrived at its target
    room, and - as a second line of defence - quietly respawns a "kill"
    step's target if the character has just walked into the room it
    belongs in and it has gone missing.
    """
    location = character.location
    if not location:
        return

    log = character.db.quest_log or {}
    for quest_key, state in list(log.items()):
        if state != "in_progress":
            continue
        if quest_key not in QUESTS:
            continue
        idx, step = current_step(character, quest_key)
        if step["type"] == "visit" and location.key == step["target_room"]:
            advance_quest(character, quest_key)
        elif step["type"] == "kill" and location.key == step["spawn_room"]:
            ensure_kill_target(character, quest_key)


def quest_entry_hint(character):
    """
    Called from CombatCharacter.at_post_move for real players. A
    one-line nudge, shown after the room description, if someone here
    has a quest the character is eligible to start, or is waiting to
    hear the result of one they've finished.

    Real, confirmed gap this closes: nothing anywhere told a player a
    quest-giver had anything to offer - a giver is just an NPC standing
    in a room, and starting a quest needed the player to already know to
    type 'quest' next to them. Shown on every entry until the quest is
    started (rather than once) since it's a single short line for
    someone who is, by definition, standing exactly where the quest is,
    and a missed one-time hint would mean never finding it. There's
    deliberately no accept/decline prompt: a quest costs nothing to
    start, can't be failed, and never expires, so a confirmation would
    just be friction.
    """
    location = character.location
    if not location:
        return
    log = character.db.quest_log or {}
    for quest_key, quest in QUESTS.items():
        giver = next((obj for obj in location.contents if obj.key == quest["giver_key"]), None)
        if not giver:
            continue
        name = giver.key[0].upper() + giver.key[1:]
        state = log.get(quest_key)
        if state == "ready":
            character.msg(
                "|y%s is waiting to hear how it went. (Type |wquest|y to report back.)|n" % name
            )
        elif (
            state is None
            and (character.db.level or 1) >= quest["level_required"]
            and not (character.db.pacifist and any(step["type"] == "kill" for step in get_steps(quest)))
        ):
            character.msg(
                "|y%s looks like they have something for you. (Type |wquest|y to hear what.)|n" % name
            )


def build_quest_log(character):
    """
    The player-facing quest log text, or None if they've never started
    one. In-progress quests first (with which step they're on and what
    to do next), then ready-to-turn-in (and who to report to), then
    completed.
    """
    log = character.db.quest_log or {}
    entries = [(key, state) for key, state in log.items() if key in QUESTS]
    if not entries:
        return None

    order = {"in_progress": 0, "ready": 1, "completed": 2}
    entries.sort(key=lambda entry: order.get(entry[1], 3))
    labels = {"in_progress": "in progress", "ready": "ready to turn in", "completed": "completed"}

    lines = ["|wYour Quests:|n"]
    for quest_key, state in entries:
        quest = QUESTS[quest_key]
        steps = get_steps(quest)
        label = labels.get(state, state)
        if state == "in_progress" and len(steps) > 1:
            label += " (step %d of %d)" % (get_step_index(character, quest_key) + 1, len(steps))
        lines.append("  %s - %s" % (quest["name"], label))
        if state == "in_progress":
            _idx, step = current_step(character, quest_key)
            lines.append("      |x%s|n" % objective_text(step))
        elif state == "ready":
            lines.append("      |xReturn to %s to report back.|n" % quest["giver_key"])
    return "\n".join(lines)


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
    God-only oversight (`quest catalog`): every quest that exists,
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
        steps = get_steps(quest)
        if len(steps) == 1:
            kind = steps[0]["type"]
        else:
            kind = "%d steps: %s" % (len(steps), " > ".join(step["type"] for step in steps))
        entry = (
            "|w%s|n\n  giver: %s (%s)\n  type: %s  reward: %dg/%dxp"
            % (
                quest["name"], quest["giver_key"], location,
                kind, quest["reward_gold"], quest["reward_xp"],
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
      quest log
      quest <npc>
      quests

    Use this near a real quest-giver to start a quest they offer (if
    you haven't already), see a reminder of what they're waiting on
    (if you're still working on it), or turn it in for your reward
    (once you've actually finished it). A completed quest is done for
    good - most won't repeat.

    Some quests take several steps - visiting a place, questioning
    someone, dealing with a target - worked through in order. You're
    told each time a step is done and what comes next. To question
    someone as part of a quest, stand with them and use 'quest'.

    'quest log' (or just 'quests') always shows your own quest log -
    everything you've started, finished, or still have outstanding,
    including what you need to do next - even standing right next to
    a quest-giver. With no quest-giver or quest contact in the room,
    plain 'quest' shows it too.
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

        # The log, on request - checked before the giver lookup so it
        # works next to a quest-giver too (plain 'quest' there interacts
        # with the giver instead, which used to make the log unreachable
        # anywhere near one).
        if arg == "log" or self.cmdstring == "quests":
            self._show_log(caller)
            return

        # A "talk" step: stand with the person the quest sent you to.
        if self._try_talk_step(caller):
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
            if caller.db.pacifist and any(step["type"] == "kill" for step in get_steps(quest)):
                caller.msg(
                    "%s takes one look at you and thinks better of it - this "
                    "isn't a task for someone who's laid down arms." % giver.key
                )
                return
            start_quest(caller, quest_key)
            caller.msg(quest["intro"])
            bonus = class_bonus_for(caller, quest)
            if bonus:
                caller.msg(bonus["intro"])
            caller.msg("|wObjective:|n %s" % objective_text(get_steps(quest)[0]))
        elif state == "in_progress":
            _idx, step = current_step(caller, quest_key)
            caller.msg(step.get("reminder") or quest["reminder"])
            if ensure_kill_target(caller, quest_key):
                caller.msg(
                    "|x(Whoever you were after has gone to ground again - "
                    "you'll find them back where they were hiding.)|n"
                )
            caller.msg("|wObjective:|n %s" % objective_text(step))
        elif state == "ready":
            bonus = class_bonus_for(caller, quest)
            gold = quest["reward_gold"] + (bonus["bonus_gold"] if bonus else 0)
            xp = quest["reward_xp"] + (bonus["bonus_xp"] if bonus else 0)
            caller.db.gold = (caller.db.gold or 0) + gold
            from world.combat import COMBAT_RULES
            COMBAT_RULES.award_xp(caller, xp)
            log[quest_key] = "completed"
            caller.db.quest_log = log
            _clear_progress(caller, quest_key)
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
            from world.achievements import track_and_announce

            track_and_announce(caller, category="quest", tracking="any")
        elif state == "completed":
            caller.msg("%s has nothing more for you." % giver.key)

    def _try_talk_step(self, caller):
        """
        If any of the caller's in-progress quests is currently waiting
        on a "talk" step with someone standing in this room, completes
        it and returns True. Anyone can be a contact, not just the
        quest's own giver, and it only triggers for a quest actually
        on that step - so standing near the same NPC for an unrelated
        reason does nothing.
        """
        if not caller.location:
            return False
        log = caller.db.quest_log or {}
        for quest_key, state in list(log.items()):
            if state != "in_progress" or quest_key not in QUESTS:
                continue
            _idx, step = current_step(caller, quest_key)
            if step["type"] != "talk":
                continue
            if any(obj.key == step["npc_key"] for obj in caller.location.contents):
                advance_quest(caller, quest_key)
                return True
        return False

    def _show_log(self, caller):
        text = build_quest_log(caller)
        if text is None:
            caller.msg("You have no quests. Find a quest-giver and use 'quest' near them.")
            return
        caller.msg(text)
