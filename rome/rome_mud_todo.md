# Rome MUD — To-Do List

_Compiled from our working session on Evennia upgrade + combat system rebuild. Updated after the full 8-class implementation, Colosseum expansion, NPC AI, doors work, and — this pass — a full automated-test build-out, a live-database audit, and the Underworld-expansion duplicate-content cleanup._

**Housekeeping note on this file itself**: this is the first time it's actually lived at `rome_mud_todo.md` in the repo — `CLAUDE.md` has referenced it as "maintained alongside actual work" for a while, but it wasn't actually present on disk before now. Worth keeping it here going forward so it stays in sync with the code instead of living only in chat history.

---

## 🎲 Ludus level gate, rumor system, auditing, housekeeping — ✅ this session

Follow-up round after reviewing this file and asking "what's next" - a mix of quick cleanup, one real gap fix, and two small new systems.

- [x] **Ludus level-gated, matching the Deeper Sands pattern.** New generic `LevelGateExit` (`world/colosseum.py`, sibling to the existing `DeeperSandsGateExit` - left untouched rather than refactored onto the new class, since it's already live and there's no value in the risk of touching working, deployed content to deduplicate ~10 lines). Applied live to the Ludus's three progression exits: Wrestling Pit requires level 3+ (NPCs are level 4), Beast Taming Ring level 5+ (NPCs level 7), Champions' Court level 7+ (NPCs level 10). Weapons Yard (level 2 NPCs) and the entrance itself stay open to anyone - a level 1 can no longer walk straight into the hardest fight in the Ludus with nothing but flavor text as a warning, resolving the decision this file had been flagging as open.
- [x] **Rumor system built** (`world/rumors.py`). A persistent global `RumorStore` script remembers the last 20 real achievement completions. `world/achievements.py`'s `announce_achievements()` - the one shared choke point every `track_achievements()` call site already routes through - now also records a rumor there, so no other call site needed to change. `NPCChatter` gained an opt-in `db.tells_rumors` flag (default off - not every NPC's flavor fits gossiping) plus `db.rumor_chance` (default 30%); enabled live on the two heralds (Colosseum Herald, the Forum's wandering herald) as the initial, thematically obvious rollout. Other NPCs can opt in later with one attribute.
- [x] **Auditing contrib enabled** (`evennia.contrib.utils.auditing`) - logs every command a player sends to `server/logs/audit_YYYY-MM-DD.log` (JSON, one file per day) for QA/incident investigation. `SERVER_SESSION_CLASS = AuditedServerSession`, `AUDIT_IN = True`, `AUDIT_OUT = False` (server broadcasts back to clients deliberately left off - the contrib's own docs warn one broadcast to everyone online becomes one log line *per connected player*, a lot of volume for little investigative value). The contrib's default `AUDIT_MASKS` already scrub passwords out of login/character-creation commands before anything is written. Confirmed live via the module's own startup log line ("Auditing module online... Audit record User input: True, output: False") - verified carefully since this changes `SERVER_SESSION_CLASS`, affecting how every session connects, not just a routine content change.
- [x] **Housekeeping**: deleted three confirmed-dead `.ev` files (`batch_podium_ring.ev`, `batch_underworld_expansion.ev` v1, `batch_cmds.ev`) and `world/tb_range.py`, discovered newly orphaned *and already broken* - its own `from . import tb_basic` dependency had been deleted at some earlier point without following this file's own sequencing note that was supposed to gate that deletion, leaving it dead code with a broken import nothing happened to trigger. Investigated three previously-flagged live-database items (Throne Room test daggers/dummy, a stray "dummy" object, the two Underworld NPCs reportedly stuck in inventory) - **all three turned out to already be resolved**, nothing left to actually clean up.
- [x] **CLAUDE.md drift fixed**: achievement count (was stale at 8, actually 5 - Free at Last, First Blood, Battle-Hardened, Legend, A Fine Purchase), the old "God tier (level 101, Zeus)" note rewritten for the full Cursus Divinorum ladder and the Zeus → Jupiter rename, the Underworld section updated from "a real, wanted future project, not started" to built-and-confirmed, and the testing section's file/test counts brought current (12 files, 244 tests, up from the stale "11 tests in tests_chargen.py" reference).
- [ ] **Colosseum "Games"/tournament event - discussed, not built.** Asked for more detail on how this would actually work before committing to it. Recommended design: not a fully-automated NPC-only spectacle (low engagement - players would just be watching, not playing) and not a full PvP bracket either (the current player base is small enough that reliably filling a bracket is a real risk, and it reintroduces PvP-balance/griefing concerns this game hasn't had to deal with yet). Instead: an admin-triggered or scheduled "Games day" window where a themed gauntlet of NPCs becomes fightable in the arena, spectator reactions scale up during the window (the `spectator_react()` system built earlier this session is already the right hook for this), a live leaderboard tracks performance for the window's duration, and top performers get a real reward (gold, an achievement, a title/cosmetic regalia - ties into the earned-titles idea elsewhere in this file). Reuses the fully-built PvE combat system rather than needing new PvP balance work or a bracket-matchmaking system. A real PvP bracket stays a plausible *later* expansion once the player base is bigger, not the starting design.

---

## 🏛️ Capitoline Hill — ✅ built, 30 rooms, non-linear by design

Follows the same validate-first methodology as the Forum build (`world/batch_capitoline_data.py` - pure data, offline BFS/collision/duplicate-name validation before a single live write).

- [x] **30 rooms across 7 zones**, matching the requested reference layout closely: Upper Clivus Capitolinus (4, continuing the existing Forum stub), the Asylum (3 - the real non-linear hub between the two summits), the main summit plateau (4), the Temple of Jupiter Optimus Maximus (7 - portico, the Capitoline Triad's three cellae, the oath antechamber, the offerings hall, a gated inner sanctum), the Arx (5 - a genuinely separate northern peak, Temple of Juno Moneta, the mint, the sacred geese), the Tarpeian Rock (3, a deliberate detour), and 4 minor temples/shrines.
- [x] **Genuinely non-linear**: the Asylum Grove and the Grove Path are real multi-way branch points (up to 5 exits each) - the main summit, the Arx, the Tarpeian Rock, and the minor temples are all separate destinations reachable from the same hub, not a forced sequence up one corridor.
- [x] **Connects only through the Forum's existing Clivus Capitolinus** (not directly from the Colosseum) - continues live room #753 ("...Near the Summit") north, matching real Roman geography where the Capitoline sits much closer to the Forum than to where the Colosseum stands; the existing multi-zone chain between them already encodes that relative distance without inventing new "pace-count" filler road.
- [x] 7 NPCs (Old Pontius the Asylum beggar, the Flamen Dialis in Jupiter's own cella, Watch-Captain Rufio at the Arx lookout, Sella at the minor shrine, a temple guard, a wandering pilgrim, a wandering litter-bearer), all 7 with chatter via `NPCChatter`.
- [x] 8 examinable objects (the Sibylline Books, a roadside altar, the sanctuary inscription, three distinct offerings-hall trophies, a rack of coin dies, a cliff-edge warning inscription) and 6 rooms with ambient echoes.
- [x] **The Inner Sanctum is gated** (`traverse:perm(Builder)`) - priest-only in-story, a placeholder lock until a real reputation/quest system exists to open it properly.
- [x] **Caught and fixed a real bug before it could confuse anyone**: my first draft room-named "Clivus Capitolinus - a Quiet Switchback" duplicated an existing Forum room's exact name (that room already exists as the dead-end scenic detour off "...Near the Summit") - my own offline validator can only catch duplicates *within* the new batch, not against what's already live, so this only surfaced during the live post-build audit. Renamed to "...the Upper Switchback"; re-verified game-wide afterward (251 total rooms, 0 collisions, 0 missing aliases, 0 duplicate names).

---

## ⚡ Cursus Divinorum — god tier system, languages, builder menu — ✅ built this session

A large, multi-part session: a real SMAUG-inspired god rank ladder, a working language/scrambled-speech system, an in-game builder menu, and a genuine bug fix for `cleanupnpcs`'s root cause. Full design discussion happened first as a published plan artifact before any code changed, per explicit request.

- [x] **Six-rung god ladder (levels 101–106), each mapped to a real Evennia permission.** `GOD_TIERS` in `world/combat.py`: 101 Novus Deus (no permission - genuine probationary rung, immortal but no admin commands), 102 Auspex (Helper), 103 Aedilis (Builder), 104 Praeses (Admin), 105 Numen Regnant (Developer), 106 Rex Divum (never assignable via command - only ever describes whoever already holds the true superuser account). `rank_title()` now returns the real tier name instead of a flat "GOD" for anything over 100.
- [x] **`godlevel`/`advance` command** - genuinely general-purpose, not god-only: sets any character's level anywhere from 1 to 105 (106 is permanently unassignable through it), and for 102-105 also grants/revokes the matching Evennia permission automatically so rank and real command access can never drift apart. Tracks what it granted (`db.godlevel_permission`) so a later demotion cleanly removes the old permission instead of piling up. Requires Praeses (104)+ to use, and you can never grant a rank with more authority than your own.
- [x] **`slay` fixed - a real bug, not just a design gap.** Previously only checked the *caller's* level was over 100; never checked the target's, so any god could slay any other god, Rex Divum included. Now refuses outright if the target is also over level 100 - no god can slay another, full stop.
- [x] **`wizinvis` - genuinely new, didn't exist in Evennia core or this project.** Relative invisibility: hidden from anyone whose level is lower than your own (room contents/look, via a new `access()` override on `CombatCharacter` checking the `view` access type), fully visible to anyone at or above your level or any true superuser. Also suppresses movement/divine-teleport announcements while active, filtered the same way (`typeclasses/characters.py`'s `announce_move_from/to`).
- [x] **`restore` and `snoop` - both genuinely new.** `restore <char>` fully heals HP/MP/SP (102+). `snoop <char>` silently relays everything a target receives to the snooper via a new `CombatCharacter.msg()` override, prefixed so it's distinguishable from the snooper's own surroundings - the target is never told. Output-only (not raw keystrokes), by design.
- [x] **`cleanupnpcs`'s actual root cause fixed**, not just the symptom. Traced to `spawn_personal_npc`'s 10-minute safety-net timer being a plain `delay(600, callback=obj.delete)` - confirmed not reload-safe, the exact same failure mode already fixed three times elsewhere in this project (`RespawnTimer`/`CharonTimer`/`SanctuaryTimer`). Replaced with a new persistent `InstanceCleanupTimer` Script mirroring `SanctuaryTimer`'s exact pattern. `cleanupnpcs` itself stays as a rare safety net, no longer a routine chore.
- [x] **Language system - `rplanguage` (an existing, unused Evennia contrib) actually wired in.** Five languages defined with distinct phoneme/grammar/vowel palettes (`world/languages.py`): Latin, Greek, Celtic, Germanic, Egyptian. Every character starts knowing (and speaking) only Latin. New `CombatCharacter.process_language()` override (the real rpsystem listener-side hook) treats every utterance - plain `say` included, not just explicitly-tagged emotes - as spoken in the speaker's current `db.speaking` language; anyone who doesn't know it hears it scrambled via `rplanguage.obfuscate_language`. Gods (101+) understand every language unconditionally, same "truth cuts through everything" spirit as the existing mask-seeing behavior. New `speak`/`learnlanguage` commands (`world/languages.py`).
- [x] **In-game builder menu - `evennia.contrib.base_systems.building_menu` wired in** (`world/building_menu.py`, new `build`/`redit` command, Aedilis/103+). Menu-driven room editing (title, description via `EvEditor`, exits - `new <dir> = <dest>` auto-creates the standard-direction return exit too, tags) with no Python or batch scripts required. NPCs/weapons/armor deliberately NOT duplicated here - Evennia's own stock `spawn` command (`spawn/list modules`, `spawn <key>`) already covers creating anything in `world/prototypes.py` well; `build`'s own help text points to it instead of rebuilding it.
- [x] **Zeus → Jupiter rename completed** (character was already partially renamed when this session picked it up; finished the rest live): level set to 106, `divine_presence` synced to `"jupiter"`, rooms #69 (`Jupiter's Throne Room`) and #169 (`Jupiter's Private Chambers`) renamed, the `zeus` tag on #69 swapped for `jupiter`. `DIVINE_ANNOUNCE_MESSAGES` in `typeclasses/characters.py` had all 13 keys renamed from Greek to Roman (zeus→jupiter, hera→juno, poseidon→neptune, demeter→ceres, athena→minerva, artemis→diana, ares→mars, aphrodite→venus, hephaestus→vulcan, hermes→mercury, dionysus→bacchus, hades→pluto, hecate→trivia) for consistency with the rest of the game.
- [x] **Olympus area (26 rooms from #69) given two real loop connections**, addressing the "pure tree, no loops" finding from the planning pass: Storm Watch ↔ Celestial Observatory, and Vault of Thunderbolts ↔ Armory of Olympus. **Caught and fixed a real bug of my own making here**: the first pass collided the new Vault↔Armory exit with Armory's pre-existing `south` exit to Council Chamber - exactly the class of bug this project has repeatedly caught via live auditing. Renamed to `down`/`east` before it shipped; re-verified game-wide afterward (221 total rooms, 0 collisions, 0 missing aliases, 0 duplicate names).
- [x] **Help entries**: stock Evennia scaffolding `"evennia"` topic deleted from `world/help_entries.py`. New `world/god_help.py` (same delete-and-recreate pattern as `help_setup.py`) adds a `god`/`gods` entry setting real RP expectations (gods are literal divine beings, not admins in costume - treat a scene with one accordingly) plus one entry per pantheon member: Jupiter, Juno, Neptune, Minerva, Mars, Venus, Ceres, Diana, Vulcan, Mercury, Bacchus, Pluto, Vesta. New commands (`godlevel`, `wizinvis`, `restore`, `snoop`, `speak`, `learnlanguage`, `build`) all have complete docstrings, Evennia's normal auto-help mechanism - no separate DB entries needed for those.
- [ ] **Known limitation, not a regression**: `rplanguage`'s translation engine occasionally drops very short words to nothing (rather than a garbled equivalent) for grammars/phonemes that don't cover that exact word length - confirmed live across all 5 languages. Reads as *more* scrambled, not broken, so left as-is rather than hand-tuning phoneme coverage.
- [x] **Follow-up round, same session**: `godlevel` now also sets race_display to "Olympian" on ascension (Jupiter's own race already used "Olympian" as manual flavor before this system existed); the character's mortal race/class is preserved and restored automatically on a later demotion back to 100 or below. The Forum's `NPCChatter` script now routes every line through each listener's own `process_language` hook (same mechanism player speech uses) rather than a blind broadcast - Rome's NPCs default to speaking Latin, the city's own lingua franca, `db.chatter_language` overrides it per-NPC if one should ever speak something else. The Forum's wandering herald (was only cycling through the Central Plaza/Rostra/Comitium cluster) now also visits the Merchants' Fountain Plaza, so its already-working chatter is actually reachable there. The `god`/`gods` help entry's framing was cleaned up per feedback - dropped the "not an admin wearing a costume" line entirely rather than drawing an IC/OOC distinction the text didn't need to make.
- [x] **Corrected after live feedback**: level and class had briefly gotten swapped from what actually reads well. Level/rank (`rank_title()`) shows the *specific* Cursus Divinorum tier again (Novus Deus, Auspex, Aedilis, Praeses, Numen Regnant, Rex Divum) - that's the number that says how senior a god is. `class_display` is what's flattened to a plain "Divine" for every god regardless of tier via `godlevel` - class no longer tries to encode a second thing there too. Removed the short-lived `god_domain()`/`god_tier_name()` helpers that only existed to support the swapped version.
- [x] **Real, significant bug found and fixed: ambient NPC scripts were never actually ticking.** Every NPC/room script built via this project's standard `evennia shell` batch-scripting workflow (`NPCChatter`, `WanderingNPC`, `ColosseumEcho`) starts its repeat timer in that short-lived shell process, which exits before the script ever survives one real pause/resume cycle in the live server - so Evennia's normal reload-time recovery (which only resumes a *recorded* pause, not a from-scratch start) silently did nothing for it, forever. `db_is_active` stayed `True`, looking perfectly healthy, while the script never fired again. Confirmed live: **34 of 34 `NPCChatter` scripts had fired zero times since creation** - every talking NPC in the game, including the reported-silent Forum herald - and roughly half of `WanderingNPC`/`ColosseumEcho`'s instances were in the same state. Fixed with a new shared `SelfHealingRepeatScript` base (`world/colosseum.py`) overriding `at_server_start()` - a hook Evennia calls on *every* reload for *every* active script regardless of pause state - to force-start a real task if none is running. Confirmed live via temporary diagnostic logging that every previously-silent script now fires correctly and repeatedly on schedule. Worth remembering for any future script class built the same way: `scripts.add()` inside an `evennia shell` script needs this same self-healing base, or it'll silently never run.
- [x] **Resurrection destination now depends on level.** Both the Underworld riddle-solve path and the resurrection spell already routed through the same `CombatRules.resurrect()`, so this was one fix: level 5 and below still return to the holding cells beneath the Colosseum; level 6+ now return to the Temple of Jupiter Optimus Maximus on the Capitoline (room tagged `capitoline_resurrection_point`, category `capitoline`).
- [x] **Who list**: the plain (non-admin) table no longer shows an Idle column - not something a regular player needs to see, admin/full tables are untouched. The freed width went to the Title column instead (30 → 42 chars), so longer custom titles don't get cropped as aggressively.
- [x] **`world/help_entries.py` deleted entirely** (it held only the stock "evennia" scaffolding topic, removed earlier and never replaced) along with `FILE_HELP_ENTRY_MODULES` in settings - the empty file was logging a spurious `[EE] "Could not find file-help module"` on every single reload.
- [x] **Shared MOTD module + `motd`/`news` command** (`world/motd.py`). Login and the new command both read from one `get_motd()` instead of two copies that could drift apart. Added a dated "Recent updates" section (2-3 lines, player-facing) and documented in `CLAUDE.md` that it should be updated after any major player-facing change - not admin-only/internal ones.
- [x] **Legacy account cleanup, no code involved - a live-database decision, not a bug fix.** Investigated all 24 non-superuser accounts (some dating back to 2025-04-30, long before this project's git history begins) for characters that predated or never completed the current race/class/stat chargen system. Found 14 completely empty character shells (garbled auto-generated names like `8MWwHSEikG` - Evennia's own fallback when `charcreate` never got a name, consistent with the pre-fix `charcreate` bug documented in this file's gotchas - `race_display`/`class_display`/`level`/all four core stats all `None`, not even placed anywhere in the world) plus one partial case (`sarah_connor` - had race/class/level but null core stats, a likely chargen-interruption rather than a pre-system character). Two characters checked out as genuinely complete and were left untouched (`xalin`, `Kerinia`). Per the account holder's decision: **deleted all 15 broken characters**, cleaned up the dangling `_playable_characters` references on their accounts (see gotcha #2 - an unfixed dangling reference resolves to literal `None`, not a safely-detectable deleted object), and left all 24 accounts themselves intact - any of these players logging back in with no character will simply go through chargen fresh, same as a brand-new player.

---

## 🏛️ Rome the city — first real world-building has started

Previously "not started, still fully open." A first, deliberately small piece is now live in the actual game database (not just source code - see the housekeeping note on live-DB scripting below).

- [x] **Colosseum now actually connects to something.** Colosseum Main Entrance's long-standing "the roads leading there are, for now, still being paved" placeholder is resolved - a real `south` exit now leads to a new hub plaza.
- [x] **The Meta Sudans built as the city's entry hub** - a real historical choice, not an arbitrary one: this monumental fountain plaza genuinely stood right outside the Colosseum, at the junction of the roads toward the Forum. Deliberately chosen over starting a generic grid - see the design discussion: ancient Rome wasn't grid-planned (that's more a Roman *military camp*/colonial-town pattern), and building a large network of anonymous intersections before any real destinations exist is harder to verify than named landmark rooms, not easier - directly informed by how much live-database auditing the Underworld duplicate-content cleanup needed.
- [x] Two real historical roads branch from the plaza: **Via Sacra** (west, the actual ancient processional road toward the Forum - this is the anchor point for wherever the Forum gets built next) and **Via Triumphalis** (east, left open toward "districts not yet built").
- [x] **A real, interactive fountain object in the Meta Sudans** - lookable, `get:false()` locked so it can never be picked up, with periodic ambient water-sound echoes via the existing `ColosseumEcho` script (no new code needed - this mechanism already existed from the original Colosseum build). Confirms `get:false()` is the correct, standard pattern for any future non-pickupable scenery prop - no custom item typeclass required.
- [x] **Caught and fixed a real bug myself before it shipped**: the first build pass gave the Meta Sudans two different `north` exits (one to the Colosseum, one to Via Triumphalis) - the exact class of exit-naming collision the Underworld v2 rebuild's own notes flagged as something to verify. Caught by the same live-connectivity-check habit from that cleanup, fixed immediately.
- [x] **Full Colosseum color pass completed** - all 65 rooms reachable from the holding cells now have color, up from 25 when this started (40 had zero color codes; all colorized in two passes, zone-consistent palettes matching the Underworld's realm-based approach: cold/damp cyan-green for the cells, blood-red/gold for the arena core, gold/marble-white for the Senatorial Podium, muted tones for the poorer Wooden Heights, etc.)
- [ ] **Housekeeping discovered while doing this**: direct live-database scripting (via `evennia shell`, used for all of the above instead of `.ev` batch files - faster and more immediately verifiable, matching the lesson from the Underworld batch-file bugs) occasionally hits a transient `django.db.utils.OperationalError: database is locked` when the live server is mid-write at the same moment. Not a bug - SQLite only allows one writer at a time, and a real (healthy) server process is the one holding it. A short retry resolves it every time observed. Worth keeping in mind for any future live-DB scripting rather than assuming the server is unhealthy.
- [x] **The Forum Romanum is built** - 99 rooms total (98 new + the existing Via Sacra room extended from), matching the requested reference document almost exactly: the Via Sacra entry spine (7), the main square (7, genuinely non-linear - a real central hub plus a loop through Basilica Julia, not a single corridor), Curia Julia (6), Basilica Julia and Basilica Aemilia (9 each), the full temple cluster (39 - Saturn/treasury, Vesta + House of the Vestals, Castor and Pollux, Julius Caesar, Concord, Antoninus and Faustina, the Regia), the Tabularium (5), Clivus Capitolinus (4), and a 13-room commercial district organized by trade the way real Roman commerce actually clustered.
  - Built as validated data first, not live trial-and-error: every room/exit/NPC/object/echo was defined in `world/batch_forum_data.py` (kept in the repo as a permanent reference of the zone's structure) and run through an automated validator - checking for duplicate names, exit-direction collisions, and full BFS reachability from the entry point - *before* a single database write happened. The validator caught 2 real collisions on the first pass (Basilica Julia's entrance, Temple of Saturn's cella) - both fixed for effectively zero cost, instead of needing a live audit to find them after the fact.
  - 17 flavor NPCs (5 genuinely wandering - a Senator's herald, a Vestal Virgin, a beggar, a foreign merchant, a haggling commoner - each bounded to a sensible `wander_rooms` set, 12 static) plus 4 real `NPCMerchant` shopkeepers (bookseller, goldsmith, perfumer, food vendor), each stocked with new item prototypes added to `world/prototypes.py` (scrolls, jewelry, perfume, food).
  - 9 lookable, `get:false()`-locked scenery objects (the Rostra's bronze ship-prows, the Golden Milestone, the statue of Victory in the Curia, cult statues in several temple cellae, a generic painted statue in the main square).
  - 9 rooms with ambient echoes via the existing `ColosseumEcho` script (the central plaza, both basilica halls, the Rostra, the Regia's sacrificial courtyard, Vesta's sacred fire, the Tabularium's gallery, the commercial district's market and fountain plaza).
  - Fully verified live afterward anyway, not just trusted the pre-flight check: 163 total rooms now reachable from the holding cells (up from 65), zero duplicate names game-wide, zero broken exits, zero uncolored Forum rooms, every NPC/merchant/object/echo confirmed present and correctly configured.
- [x] **Forum made "vibrant" per request - all 21 Forum NPCs now actually talk.** New general-purpose `NPCChatter` script (`world/colosseum.py`, sibling to the existing `ColosseumEcho`) attached to every Forum NPC - all 4 merchants (bookseller, goldsmith, perfumer, food vendor - real sales-pitch lines, e.g. "Fresh copies, honest prices - come, have a look!") and all 17 flavor/wander NPCs, each with 1-3 in-character lines matching their role (the beggar actually begs - "Spare a coin, friend, just a coin..."; the Senator complains about Senate procedure; the Vestal Virgin is sparse and solemn; lictors and guards are terse). Fires every ~60s to the NPC's current room, picking a random line from `db.chatter_lines`. Verified live: 21/21 Forum NPCs confirmed to have the script attached and lines set.
- [x] **Reviewed the Colosseum's room sequences/structure per request - fully closed out, zero real bugs.** All 16 originally-flagged rooms (from a heuristic scan for direction words in description text with no matching exit) individually checked by hand this session. Every single one is a false positive - colloquial English ("down here" = "in this place," "two seats down," "sitting up") or a deliberate design stub (Via Triumphalis/Meta Sudans), not a real navigation gap. **One genuine bug was found in the process, but not from the flagged list** - a full game-wide exit-collision scan (prompted by the same diligence, not the scan itself) caught Grove of Champions (#613) having two different exits both named "west" (to Blessed Fields and to Gardens of the Fortunate) - a leftover from the earlier manual Underworld duplicate-cleanup. Fixed (renamed to south/north on both ends) and Gardens of the Fortunate's missing description (the only empty-desc room in the entire game) was filled in. Re-verified game-wide afterward: 221 total rooms, zero collisions, zero duplicate names, zero empty descriptions.
- [x] **Reviewed the Ludus specifically per request - structure is sound, found one real gap, and it's now fixed.** All four training tiers (Weapons Yard → Wrestling Pit → Beast Taming Ring → Champions' Court) are correctly connected, correctly staffed (3 NPCs each), and the NPC difficulty genuinely escalates (recruit trainers are level 2/114 HP, champions are level 10/172 HP). Unlike the Deeper Sands, which has a real level-6 gate (`DeeperSandsGateExit`), the Ludus had no equivalent at all - every training ground connected directly to the entrance, so a level-1 could walk straight into Champions' Court with nothing but flavor text as a warning. **Decision made and implemented**: see the Ludus level gate entry above (`LevelGateExit`, three tiers gated at levels 3/5/7).
- [x] ~~**Next real step**: ...the top of the Clivus Capitolinus (toward the Capitoline Hill's own temples)~~ - **done, see the Capitoline Hill section above.**
- [ ] **Next real step**: Forum Romanum still dead-ends at one deliberate future-expansion stub, matching real Roman geography - the Argiletum (north from the commercial district, toward where the Subura district would go). A natural, already-anchored next piece whenever more of the city is wanted.

---

## 🚨 Do this first

- [ ] **Reload the server.** Several fixes across this file are written but not yet live until a reload picks them up — check each section below for what's still pending.
- [x] ~~**Get this codebase into git.**~~ — resolved. Repo connected to GitHub (`github.com/Hunter-Meares/rome`) via a repo-scoped SSH deploy key, full game history committed to `main` and `dev`, `.gitignore` gaps fixed (db backups/journal, a stray local sqlite build directory), stale README links fixed, a `secret_settings.py.example` template added, and the vestigial unused `evennia` submodule (pinned to an old ~v5.0.1 commit nothing actually used) removed entirely.
- [ ] **Set up a real staging instance before real players arrive.** `main` = production, `dev` = staging is now the intended workflow (branches exist and are in sync) - but there's no second *running* server yet. Recommended: a second Evennia instance on different ports (e.g. 7531/4013-4014) with its own separate database, checked out on `dev`, so future changes can be tested live without touching the production server or its player data. Fine to keep skipping this while there are zero players; worth doing before that's no longer true. Explicitly on hold per your call - ask when ready.

---

## 💡 Feature ideas for player attraction/immersion (not yet scoped, no code started)

Brainstormed on request - picked for being strong thematic fits for Rome specifically rather than generic MUD features. Roughly ordered by impact-for-effort; none of these have any implementation started.

- [ ] **Actual Colosseum "Games."** Right now the arena is a training ground, not a spectacle. See the dedicated entry higher up in this file (Ludus/rumor/auditing section) for the discussed design - a scheduled/admin-triggered themed NPC gauntlet with amplified spectator reactions and a real reward, not a full PvP bracket - and why.
- [ ] **Earned, display-able titles from achievements - a genuine dual-title system, kept deliberately separate from the existing custom `title` command.** Design discussed and settled:
  - `db.custom_title` stays exactly as it is today - free text, fully player-controlled, unrestricted (pure self-expression, e.g. "Senator of Rome").
  - New `db.earned_titles` (a list) + `db.active_earned_title` (which one is currently displayed) - populated automatically off achievement completion (a small addition to the achievement dicts: a `"title"` field, e.g. `"the Undefeated"` on the Arena Master achievement). Can only ever contain titles actually unlocked - no faking it, same "verified, not just claimed" spirit as the existing `greet`/mask-proof identity system.
  - New commands alongside the unchanged `title <text>` / `title clear`: `titles` (list what's unlocked + which is active), `titles set <name>`, `titles clear`.
  - Display split by context rather than trying to cram both in everywhere: `who`'s compact table shows one slot only (earned title takes priority if active, falls back to custom) to keep the table from getting even more cramped than it already is (see the `who` cleanup section below); `stats`/looking directly at a player shows both, labeled separately, since there's room there.
- [ ] **A living-world rumor/news system.** NPCs occasionally mentioning recent player accomplishments ("Have you heard? Marcus defeated the Arena Master!"). Cheap to build, disproportionately high payoff for making the world feel alive rather than static - plugs directly into achievement data already being tracked.
- [ ] **Collegia - player-run guilds.** Historically authentic (collegia were real Roman trade/social guilds), and distinct from the existing static lore factions. Player-created, player-led, real ranks. Gives long-term players a reason to organize beyond a temporary party, and gives Rome-the-city a natural building type (guild halls) once it exists.
- [ ] **A bounty/quest board.** Simple repeatable "kill X" / "fetch Y" objectives for gold/XP. Right now new/returning players default to "grind NPCs" with no clearer structure; a board gives an obvious answer to "what do I do today."
- [ ] **`top`/leaderboard command.** Top players by level, gold, or achievements. Cheap, social, quietly competitive.
- [ ] **Bump `extended_room` (time-of-day descriptions) up the existing contrib priority list.** Already chosen, currently unprioritized. Given the amount of care already put into atmosphere (the Underworld color-palette work, room descriptions throughout), this is disproportionately high-immersion for the effort.
- [ ] **Bump in-character `mail` up the existing contrib priority list too.** Also already chosen, also currently low priority. Given how much social infrastructure already exists (sdesc/mask/recog/greet), letters between characters is a natural next social layer that's currently missing.
- [ ] **Colosseum end-game content for level 100 players - brainstormed this session, nothing scoped/built yet.** Full list given in chat; top picks by impact-for-effort: (1) a real "Games" event system (see the Actual Colosseum Games idea above, but specifically framed as the level-100 answer - a champion's bracket, spectator reactions, a crowd-favor stat); (2) a genuine end-game boss (an undefeated champion/gladiator legend, meaningfully harder than the current Champions' Court roster, with unique drops); (3) a prestige/rebirth-style system once level 100 is hit, so there's a reason to keep engaging rather than the level bar just going flat; (4) cosmetic-only arena titles/regalia earned specifically from Colosseum content, tying into the earned-titles idea above.

---

## 🧪 This session: automated test coverage + bugs found

New: **221 automated tests** across 11 files (`world/tests_chargen.py`, `tests_combat.py`, `tests_party.py`, `tests_achievements.py`, `tests_underworld.py`, `tests_combat_commands.py`, `tests_items.py`, `tests_economy.py`, `tests_colosseum.py`, `tests_npcs.py`, `tests_quit.py`), run via `evennia test`. This closes a large fraction of the open items in the Testing Checklist section further down — see that section for exactly which ones.

Real, previously-undiscovered bugs found and fixed along the way:

- [x] **Critical**: level 6+ death never actually moved the player to the Underworld. `handle_player_defeat` deliberately leaves HP at 0 while dead, but `CombatCharacter.at_pre_move` unconditionally blocks any move at hp≤0 - the move silently failed every time. Fixed with an explicit `force_move` bypass for that one system-authorized relocation.
- [x] **Critical, found while reviewing tonight's Underworld rebuild**: dead players (`is_dead=True`, hp=0) could not move through *any* normal exit at all - not just the initial drop-off. This made the entire new Elysium/Tartarus/Asphodel expansion unwalkable by an actual dead player; only a superuser (full HP) could ever see it, which is exactly why neither of us had noticed. Fixed: `at_pre_move` now also allows movement when `db.is_dead` is true, distinct from someone merely knocked to 0 HP mid-fight (who's still correctly blocked).
- [x] **Major**: every self-targeted spell/skill (target type `"anychar"` - `cure wounds`, `field dressing`, `antidote`, `sanctuary`, `testudo`, `rally`, `ward against death`, and 14 others) failed with "requires a target" when cast with no argument, instead of defaulting to the caster. The self-fallback code existed but was unreachable - an earlier validation check returned before it could ever run. This meant a Medicus typing `cast cure wounds` to heal themselves - probably the single most common support-caster action - never worked.
- [x] **Major**: using *any* item never actually consumed a limited use or spent the combat action. Every `itemfunc_*` returns `False` explicitly on failure but nothing (`None`) on success; `use_item`'s check treated both as failure and bailed before reaching `spend_item_use`/`spend_action`. Net effect: potions were functionally infinite, and using an item in combat cost nothing.
- [x] **Major**: the shop's "infinite stock" design was completely broken. `_buy` checked `ware.db.prototype_key` to decide whether to spawn a fresh copy - but Evennia's spawner never actually sets that as a `.db` attribute (it's tracked as a Tag instead). Every purchase silently handed over the real display item rather than a copy, meaning a shop genuinely could run dry exactly as the design was meant to prevent.
- [x] `schedule_respawn`'s `move_to(None)` call was missing `to_none=True` - a defeated `RespawningNPC` never actually left the room during its respawn wait, just sat there "defeated" until the timer fired and moved it right back to where it already was.
- [x] Party `invite`/`kick` couldn't find a target by their real name unless the searcher had already `greet`-ed them or was a Builder - the same rpsystem sdesc-search root cause already documented and fixed for `attack`/`fight` (`find_combat_target`), just never applied to party. Same fix applied.
- [x] `cast <spell> = <name>` and `skill <skill> = <name>` had the identical named-target search gap as party invite - fixed the same way. `use <item> = <name>` had it too.
- [x] `at_defeat`'s XP/gold-split loops could crash (`AttributeError`) on a stale `damage_log` entry for a since-deleted contributor - the exact gotcha #2 pattern (a deleted reference reloads as literal `None`, not an object with `pk=None`) that was already fixed once in `next_turn()`, but missed here.

---

## 🌒 Underworld expansion — ✅ built, then debugged live, now genuinely confirmed

Original entry undersold what actually happened here - worth a full rewrite.

- [x] Grew from 3 rooms to **30** (matches what both build attempts independently aimed for)
- [x] **v1 (`batch_underworld_expansion.ev`) had two real, separate bugs**, both later documented directly in v2's own header: `@destroy` without `/force` silently no-ops in batch-command mode (the old exit never actually got removed, so everything built after it chained onto the wrong location), and v1's narration used literal `|x` (ANSI black), which renders **invisible on black-background clients** - a real, live text bug, not a style nitpick.
- [x] **v2 (`batch_underworld_expansion_v2.ev`) fixed both** - `/force` throughout, and Evennia's xterm256 greyscale codes (`|=o`/`|=v`) instead of literal black. Also upgraded Asphodel Meadows to a genuine verified-collision-free 3×3 grid instead of a single line, and added two wandering ghost NPCs.
- [x] **Found via a live-database audit this session**: v1 was run, then v2 was run on top of it without cleaning up v1's rooms first - leaving two entire parallel Elysium/Tartarus/Asphodel networks live and reachable at once (54 rooms instead of ~30), both looping back to Threshold of Return. Confirmed v1's copies still had the invisible `|x` text bug live.
- [x] **Cleaned up live** - v1's ~21 orphaned rooms deleted, the duplicate Judgment Hall consolidated to one copy, Minos and the Fury NPCs relocated to the surviving hall, a stray exit rewired. Re-verified after cleanup: 0 duplicate room names, 0 broken exits, 0 remaining `|x` text, single Judgment Hall.
- [x] Two wandering ghost NPCs added (`a wandering shade` - Asphodel Meadows grid, `a lingering hero's shade` - Elysium) with real `WanderingNPC` scripts and `wander_rooms` lists.
- [x] **This session: "only 2 or so NPCs" and "too linear" both addressed.** 6 new spirit NPCs added (10 total Underworld NPCs now, up from 2 non-boss ones): `a weeping shade` and `an old soldier's shade` (wandering, Asphodel), `a laurel-crowned shade` (wandering, Elysium), `a shade at the water's edge` (static, River Lethe - talks), `a chained shade` (wandering, Tartarus), `a shrieking shade` (static, Wailing Cavern - deliberately silent, no chatter, just startling). 4 of the 6 given `NPCChatter` lines (ghostly/mournful, distinct in tone from the Forum's lively chatter); 2 left silent on purpose for variety. 2 new branch rooms added to reduce linearity - **The Endless Slope** (Sisyphus-themed, branches off The Chained Depths in Tartarus) and **The Grove of Remembrance** (memorial grove, branches off The Isles of the Blessed in Elysium) - both real side-paths, not just corridor extensions. Underworld now 32 rooms total. Re-verified game-wide afterward alongside the Grove of Champions fix above: no new collisions or dead ends introduced.
- [x] ~~**Still needs doing**: both wandering NPCs are currently sitting *inside Zeus's own inventory*~~ - **resolved, verified this session**: both are correctly out in the world (`a wandering shade` in The South Fields, `a lingering hero's shade` in The Still Waters), not in anyone's inventory. No action was needed by the time this got checked.
- [ ] Minor, non-urgent, not checked this session: both NPCs' `home` attribute may still point to the character "Jupiter" rather than a room (a side effect of `@create`'s context at creation time) - harmless unless their current room is ever deleted, worth a `@home` reset sometime.
- [x] **"Not yet tested live at all" - now genuinely addressed**: full connectivity confirmed via a live BFS trace (all 30 rooms mutually reachable, no dead ends), no broken exits. The one thing that could NOT have been honestly tested before today - a real dead character actually walking through it - was structurally impossible until the `is_dead` movement fix above; it should be a real, doable walkthrough now.
- [x] `batch_underworld_expansion.ev` (v1) confirmed safe to delete - fully superseded, and its rooms are now cleaned up live so there's no remaining dependency on it.
- [ ] Cerberus, Rhadamanthus, and Aeacus - still not built, same "future smaller follow-up pass" status as before.
- [ ] Ghostly NPCs still intentionally simple (no dialogue/reactive behavior) - unchanged from before.

---

## 🧹 Cleanup (quick, do these first)

- [x] ~~Delete leftover test objects in Zeus' Throne Room~~ - **checked this session, nothing was there**: Jupiter's Throne Room contents are just its four exits and Argus. No daggers, no training dummy - already clean, whether cleaned up in an earlier untracked session or never actually present on this database.
- [x] ~~Confirm the "dummy" account/character search comes back empty~~ - **checked this session**: the only object matching "dummy" is the real, intentional test account's own character (#457, in Arena Sands) - not a stray.
- [x] ~~Delete `world/tb_basic.py` and `world/tb_range.py`~~ - **resolved this session, though not via the planned range merge.** `tb_basic.py` was already gone from disk by the time this got checked (deleted at some earlier, untracked point without following this note's own sequencing warning), leaving `tb_range.py` an orphan with an already-broken `from . import tb_basic` import that nothing happened to trigger. Deleted `tb_range.py` too - both are now gone. The ranged/positional combat project itself is still open, just no longer blocked on this cleanup.
- [x] ~~`batch_podium_ring.ev` - confirmed dead~~ - deleted this session.
- [x] ~~`batch_underworld_expansion.ev` (v1)~~ - deleted this session.
- [x] ~~`batch_cmds.ev`~~ - deleted this session.
- [x] ~~Double check `secret_settings.py` doesn't also define `PROTOTYPE_MODULES`~~ — turned into a much bigger find than this checkbox implied. `world.combat` **was** in `PROTOTYPE_MODULES`, and Evennia treats every module-level dict in a listed module as a prototype — silently injecting a stray `prototype_key` attribute into `SPELLS`/`SKILLS`, which was the root cause of a real combat crash (`AttributeError` in NPC `_gather_actions`). Fixed by removing `world.combat` from `PROTOTYPE_MODULES` entirely — it never had real prototypes in it, those all correctly live in `world/prototypes.py`.
- [ ] **New**: `CLAUDE.md` has drifted in a few small places worth a quick pass: it references `world/tests_chargen.py` as already existing with 11 passing tests, but that file wasn't actually present on disk before this session (now it is, with 24 tests, folded into the larger suite above); it says "8 achievements defined," but there are 5 currently (all correctly wired, just a stale count); and its Underworld section says the expansion is "a real, wanted future project, not started" - which is now very out of date given the section above.

---

## 🧠 NPC AI / autonomous combat behavior — ✅ built

Every combat-capable NPC now genuinely acts on its own turn instead of sitting passive.

- [x] Ludus trainers and Arena Fighters (11 total) now fight back — `HostileNPC` typeclass, hooks into `CombatTurnHandler.start_turn`'s existing `at_turn_start` check
- [x] Augur's Summon Familiar, Haruspex's Summon Lemures, and Venator's beast companion all act automatically via `SummonedAlly` — mirrors their owner's real `combat_side` (not just a last-attacked mirror)
- [x] Decided: summoned allies **do** attack automatically now, not a passive body — resolves the open design question from this section
- [x] Went beyond "minimum viable" — `HostileNPC` doesn't just attack, it randomly picks between basic attack and any spell/skill its class/level allows that it can currently afford, calling the exact same `spellfunc`/`skillfunc` a player's `cast`/`skill` would call
- [x] **Major bug found and fixed**: `AutoStatNPC`'s stat-deriving logic lived in `at_object_creation()`, which fires *before* a prototype's own fields (`race`, `player_class`, `level`) get applied — meaning it silently never actually derived stats for any prototype-spawned NPC. Fixed by moving the logic to `at_object_post_creation()`.
- [x] **New, confirmed this session**: `_gather_actions()` and `at_turn_start()` covered by automated tests - basic attack always available, class/level/cost filtering all verified against real `SPELLS`/`SKILLS` data, and a live NPC-vs-player attack traced end to end.
- [ ] **Still open**: real target *prioritization* across multiple enemies (currently always picks the first valid target found) — low priority unless multi-person fights against these NPCs become common

## 🎭 NPC race/class/level derivation — ✅ built

- [x] `derive_npc_stats(race_key, class_key, level)` built in `world/combat.py` — computes HP/MP/SP and all four core stats using the exact same formulas chargen uses
- [x] `AutoStatNPC` typeclass applies this automatically at creation via `db.race`/`db.player_class`/`db.level`
- [x] All 6 Arena Fighters (Recruit through Arena Master, levels 3–25) built through it from the start
- [x] All 11 Ludus/Arena NPCs retrofitted with real race/class assignments matching their existing flavor
- [x] Spectator/flavor NPCs (Milo, Titus, Herald, commoners, nobles, vendors) deliberately left on plain `DefaultCharacter`
- [x] **New, confirmed this session**: `derive_npc_stats` verified by automated test against the exact same ceiling/leveling invariants `tests_chargen.py` locks in for real players (base 10 + best race/class stacking to 16, per-level growth matching `LEVEL_UP_*` constants).

## 🏛️ Colosseum expansion — ✅ built, vendor blocker now resolved

Genuinely transformed from a one-room newbie tutorial into a grand, multi-purpose landmark.

- [x] Arena Sands expanded via "The Deeper Sands" — 7 new rooms, 6 leveled fighters (levels 3–25)
- [x] Level gate on the deeper section — `DeeperSandsGateExit`, blocks characters below level 6
- [x] Full multi-floor seating spine built and expanded into real multi-room clusters per tier: Senatorial Podium (4 rooms), Equestrian Terraces (4 rooms), Maenianum Secundum Imum/Summum split (5 rooms), Wooden Heights (4 rooms), Colosseum's Crown (3 rooms)
- [x] The Hypogeum — 5 rooms beneath the arena floor
- [x] Wandering spectator NPCs — `WanderingNPC` script, 4 NPCs deployed
- [x] **This item is now resolved, not still blocked**: "Vendors selling anything" was previously blocked on Economy, but Economy shipped this session (see below) - the Colosseum vendor and a new Ludus weaponsmith are both real, stocked `NPCMerchant`s. Worth one live `shop` check now that the shop-stock bug above is fixed, since that bug would have made "does the vendor actually sell things" look broken even after Economy shipped.
- [ ] **Design note for whenever Rome proper gets built and connected**: wandering NPCs are deliberately bounded to a `wander_rooms` list set at spawn time - they will NOT automatically wander into Rome once it exists. Extending any NPC's beat is a small, deliberate edit, not automatic.
- [x] **New, confirmed this session**: full live-database audit of all 62 rooms reachable from the holding cells - 0 duplicate room names, 0 broken exits, 0 thin/empty descriptions, all 18 `RespawningNPC`s confirmed alive and correctly placed (none stuck at 0 HP from the `schedule_respawn` bug above - the fix landed before it had a live victim). Two exits that initially looked accidentally one-way (Maintenance Tunnel→Guard Checkpoint, Hidden Stairwell→Riddle Door Chamber) confirmed intentional - the sneak/riddle escape paths are meant to be one-way.
- [x] **Correction to the line directly above, found by an actual player walking the route**: Maintenance Tunnel→Guard Checkpoint being "one-way" was only half-checked - a real, live bug. `Maintenance Tunnel` had a normal walkable `east` exit into `Guard Checkpoint`, but `Guard Checkpoint` had no `west` back - its only exit (`east`) led sideways to Flooded Cistern, not back the way you came. The only route back to Maintenance Tunnel was `sneak` (a random-chance command, not a direction), so walking `east` in and finding no way to walk back out read exactly like "connected east to east instead of east to west." Fixed by deleting the stray `east` exit entirely - matches the escape path's actual intent (getting past the guard is a one-way stealth commitment, same philosophy as the Underworld ferry) rather than trying to bolt on a real `west` return that would let players bypass the guard for free.
- [x] **Also found and fixed this session, same live-playthrough report**: 201 exits game-wide (mostly the Forum, built via a batch script that never set `aliases=[...]`) were missing their standard single-letter direction alias (`west` had no `w`, etc.) - walkable in the exits list but the shorthand command silently failed with "Command 'w' is not available." Added the correct alias to all 201. Also found: all 98 Forum room descriptions had their source file's literal line-wrap indentation baked into the live text (`\n    `), rendering as broken mid-sentence indentation in the client. Reflowed all 98 live, and fixed `world/batch_forum_data.py` itself so the reference file doesn't reproduce the bug if ever rerun.
- [x] **The Colosseum Herald (#286, Atrium of the Games) was completely silent since the original build** - never given the `NPCChatter` treatment applied to the Forum. Fixed: 4 herald-appropriate announcement lines added.
- [x] **New: reactive spectator crowd system.** Rooms tagged `spectacle` (category `colosseum` - currently Arena Sands and The Master's Sands) now get real crowd reactions tied directly to combat events, not just idle chatter: a ~35% chance of a reaction line on every landed hit (`CombatRules.apply_damage`), and a guaranteed one on every defeat (`CombatRules.at_defeat`), via a new `CombatRules.spectator_react()` helper. Deliberately scoped to actual arena floors, not the Ludus (a training ground, not a spectacle, per the existing design distinction between the two) - extending the `spectacle` tag to new rooms later (e.g. once the Games event idea above is built) is a one-line `tags.add()`, not a code change.

## 🔁 Persistent NPCs / respawning — ✅ built, one real bug found and fixed

- [x] `RespawningNPC` typeclass + `RespawnTimer` script built — persistent Script, not a bare `delay()`
- [x] All 4 Ludus trainer tiers converted, 3 copies per tier, `respawn_delay` scaled 30s–90s
- [x] `challenge` confirmed to fail gracefully in these rooms now ("There's no one here to challenge")
- [x] All 6 Deeper Sands Arena Fighters converted the same way, one copy per room, `respawn_delay` 60s–300s
- [x] `cleanupnpcs` admin command built
- [x] **New, real bug found and fixed this session**: `schedule_respawn`'s `npc.move_to(None, quiet=True)` call was missing `to_none=True` - without it, `move_to(None)` silently does nothing at all (returns `False`, no location change). A defeated `RespawningNPC` never actually left the room during its wait; it just sat there "defeated" until the timer fired and moved it right back to where it already was. Fixed, and confirmed via a live check that none of the 18 currently-deployed `RespawningNPC`s are stuck in this state.
- [x] **New, confirmed this session**: `RespawnTimer.at_repeat()` covered by automated tests - full-HP restoration and correct home-room placement on a normal respawn, and graceful self-cleanup (no crash) if the NPC or its home room was destroyed while waiting. The literal "survives an actual server reload" scenario still can't be simulated in a unit test - what's now verified is that the mechanism responsible for that (a `persistent=True`, `autostart=True` Script) is actually configured correctly by `schedule_respawn`, which is the part that would have silently broken instead.

## ⚔️ Combat system follow-ups

- [x] Party system / combat sides integration — resolved (unchanged from before)
- [x] **`use` command with an actual item** — now explicitly confirmed via automated tests, and a real bug found in the process (see the top section above)
- [x] **`powerattack`** — now explicitly confirmed via automated tests (SP cost enforced, rejected when insufficient, action correctly spent on use)
- [x] Simple NPC "AI" — done, see dedicated section above
- [ ] **Future project: ranged/positional combat.** Still not started - but worth noting explicitly: every system it was previously scoped as depending on (8-class ability rosters, weapon proficiency, the stats system, sides/teams) is now built, so this is the first point where starting it isn't blocked on something else.
- [x] `learnspell`/`learnskill` level-gated — unchanged, gold cost still open, still blocked on Economy... except Economy is now built, so this is worth revisiting as a real decision rather than a blocked item.
- [x] AoE auto-targeting — unchanged, now covered by automated tests for both `cast` and `skill`.
- [x] `disengage` fix — unchanged, now has 2 dedicated automated tests (success removes from fight, failure keeps fighter in and still spends the turn).
- [x] Turn-handler stuck-loop fix — unchanged, now has a direct regression test that constructs a fighters list containing a literal `None` entry and confirms `next_turn()` prunes it without raising.
- [x] Confirmed this fix covers **any** personal-instance NPC defeat, not just `slay` — unchanged.
- [x] `fight` (bare, no target) redesign — unchanged, now covered by automated tests for every branch (own challenge opponent, lone unambiguous fighter, ambiguous asks for a name, `fight all` groups by party).
- [x] NPC targeting fix (`find_combat_target`) — unchanged, but see the top section above: the same underlying rpsystem sdesc-search gap turned out to also affect `party invite`/`kick`, `cast`/`skill`/`use` with a named target - all fixed the same way now, not just plain `attack`/`fight`.
- [x] XP-on-kill missing-`attacker` fix — unchanged, now covered by automated tests including a genuine multi-attacker proportional-split scenario and the "stale/deleted contributor in damage_log" edge case (which itself turned out to need one more fix - see the top section above).

## 😴 Resting & combat balance — ✅ built this session

_(Unchanged from before - all confirmed by automated tests this session: gradual regen math, auto-interrupt on combat entry, movement/combat-command blocking while resting, and the hit-chance calibration target itself.)_

## 🧭 Chargen race/class synergy hints — ✅ built this session

_(Unchanged - the full 48-combo matrix, plus the Human/Centaur tie-breaking bug and the Harpy rebalance, are now locked in by 24 automated tests specifically so a future edit to `_leans_caster` or the race/class data can't silently regress either fix again.)_

## 🎓 Leveling system — ✅ built

_(Unchanged - level-up math, XP proportional splitting, and `award_cast_xp` all now covered by automated tests, including a dedicated multi-level-up-from-one-large-reward case.)_

## 📋 Character sheet / stat visibility — ✅ built

- [x] `stats` command, help topics, `groupcombat` topic — unchanged
- [ ] Django web admin reachability at `/admin/` — still never explicitly checked, genuinely trivial to do (just visit the URL and confirm login works)

## 📊 Session analytics & admin tooling — ✅ built

_(Unchanged.)_

## 🧑‍🎨 Character creation (chargen menu) — ✅ built

_(Unchanged - now backed by 24 automated tests covering every race×class combo, the stat ceiling invariant, starting-gear/spell/skill data integrity against `SPELLS`/`SKILLS`/prototypes, and the actual `_apply_race_and_class` stat math end to end.)_

## 🏛️ World building

_(Unchanged.)_

## 🔧 Server / infrastructure

_(Unchanged.)_

## 🏟️ Starting location & onboarding — ✅ built

_(Unchanged.)_

## 🏛️ Rome the city (500-room recreation — big, multi-phase project)

Not started. Still fully open - but see the note in the "Do this first" framing above: the Underworld expansion needed a human to manually catch three separate real bugs (a silently-no-op'd `@destroy`, invisible text, and a full duplicate network from re-running a batch file without cleanup) across roughly 30 rooms. That failure rate isn't something manual review scales to at 500+ rooms. Worth building a reusable connectivity/duplicate-check tool (the live audit run this session - BFS reachability, duplicate-name detection, broken-exit detection - could become a real admin command) before the next big batch-build push, not just before Rome specifically.

## 💰 Economy system — ✅ built this session, one major bug found and fixed

- [x] `character.db.gold`, gold-on-defeat, `world/economy.py` shop flow, sell-back — unchanged
- [x] **New, real bug found and fixed this session**: the "infinite stock" design was completely broken. `_buy` checked `ware.db.prototype_key` to decide whether to spawn a fresh copy for the buyer - but Evennia's spawner never actually stores that as a `.db` Attribute (it's tracked via a Tag, `category="from_prototype"`, instead). That check was always `None`/false for every real prototype-spawned ware, so every single purchase silently fell through to moving the *actual display item* to the buyer instead of spawning a copy - meaning a shop genuinely could be emptied out, exactly what this design was supposed to prevent. Fixed to read the tag correctly.
- [x] **New, confirmed this session**: full buy/sell flow covered by automated tests, including the specific regression case above (buy the same item 5 times, confirm the display item never leaves the merchant and 5 real copies land in the buyer's inventory).
- [ ] Restocking, custom pricing/haggling, `learnspell`/`learnskill` gold cost — all still open, unchanged.

## 🏟️ Colosseum questline follow-ups

_(Unchanged except: Underworld/Hades zone entries below now point to the fuller Underworld Expansion section above rather than duplicating it.)_

- [x] Real Underworld/Hades zone built — see the dedicated Underworld Expansion section above for the full, current status
- [x] 15-minute wait / riddle / XP penalty — unchanged
- [ ] Escalating consequences for repeated `sneak` failures — unchanged, not addressed
- [x] Old Milo dialogue — unchanged
- [ ] `recall` cooldown — unchanged, not addressed
- [ ] Connect to future Forum Romanum — unchanged, blocked on Forum Romanum existing

## 🎽 Equipment expansion — not addressed, still fully open

## 📊 Core stats/traits system — ✅ built, one item still open

_(Unchanged - website copy update still open.)_

## 🎭 rpsystem contrib — ✅ built

_(Unchanged, except: `find_combat_target`'s fix turned out to be needed in several more places than originally thought - see the top section above.)_

## 🚪 Doors (SimpleDoor contrib) — ✅ built

_(Unchanged.)_

## 🧪 Testing checklist — mostly closed out this session

**Confirmed working live** (unchanged from before - Colosseum tiers, doors, onboarding, exit descriptions, both escape paths, NPC AI mid-fight, disengage, escape defeat message).

**Newly confirmed this session** (via 221 automated tests + a live-database audit, replacing most of the "still not confirmed" list below):
- [x] Party system (invite/accept/decline/leave/leader-transfer/kick) - found and fixed a real named-target search bug in the process
- [x] Self-targeting spell fix (`cast cure wounds` with no target) - found this was actually still broken, not fixed; now genuinely fixed
- [x] Weapon proficiency penalty in combat numbers
- [x] Underworld/death system - found and fixed two real, serious bugs (see top section) that would have made this genuinely broken for a real player even though it looked fine in code review
- [x] Auto-targeting for AoE spells/skills with no explicit target
- [x] A genuine multi-person team fight (2v2), confirming sides/teams ends the fight correctly on whole-side defeat, not raw fighter count
- [x] `RespawningNPC` - confirmed the respawn mechanism itself works correctly; found and fixed the "never actually leaves the room" bug in the process. The literal reload-survival scenario still can't be unit-tested directly - see the note in the Persistent NPCs section above.
- [x] XP splitting in a genuine group kill, including a pure-support (healing-only) character leveling via casting XP alone
- [x] `quit`-during-combat - 5 dedicated tests confirming the block fires correctly, only for the issuing session's own puppeted character, and doesn't disconnect when blocked

**Still genuinely open:**
- [ ] Rank titles showing correctly on `who` at all boundary levels - not covered by this session's tests, worth a dedicated pass
- [ ] `sessionlogs` - one more real connect/disconnect cycle for full confidence, unchanged from before
- [ ] A real, in-person walkthrough of the full Colosseum spine (Atrium → seating spine → Hypogeum → Deeper Sands) and the full Underworld (now that a dead character can actually move through it) - automated tests and a database-level audit both confirm the *structure* is sound, but neither substitutes for actually reading the rooms in order as a player would.

## 🎨 Website / first impressions

_(Unchanged.)_

## 📦 Contribs to implement

- [x] ~~`building_menu` bumped up in priority~~ - **built**, see the Cursus Divinorum section above (`world/building_menu.py`, the `build`/`redit` command).
- [x] ~~`auditing` bumped up in priority~~ - **built this session**, see the Ludus/rumor/auditing section above. Note for anyone reading this later expecting a *world-integrity* checker (duplicate names/broken exits/unreachable rooms): that's not what this contrib is - it's a command/traffic logger (what players actually typed, for QA and incident investigation). The connectivity-checker idea that motivated bumping this up is still a real, separate, not-yet-built tool - worth its own entry rather than conflating the two again.
- [ ] **New idea, not yet scoped: a reusable connectivity/duplicate-check admin tool.** The actual thing that would have turned several of this project's real bugs (the Underworld v1/v2 duplicate-network mystery, the Grove of Champions collision, the Capitoline naming collision) into a lookup instead of manual live-database archaeology. Every big room-building session this project has done has manually re-implemented some version of this (BFS reachability, duplicate-name detection, exit-collision detection) as a throwaway script - worth promoting to a real admin command before the next big batch-build (Argiletum/Subura, or Rome-the-city).
- [ ] `git_integration`, `extended_room`, `mail`, `ingame_reports`, `health_bar`, `crafting` - all unchanged, still not built.

## 🚪 Quit-during-combat — ✅ fixed and now fully confirmed

- [x] Real bug found and fixed — unchanged from before
- [x] Fixed with a minimal `CmdQuit` subclass — unchanged
- [ ] Known, deliberately-unaddressed limitation (multi-session `quit/all`) — unchanged, still not prioritized
- [x] **"Not yet tested live" - now resolved.** 5 dedicated automated tests confirm: blocked while the issuing session's own puppeted character is in combat, allowed when not in combat, allowed when the session has no puppet (OOC), allowed when a *different* character is fighting (not this session's own puppet), and confirmed the block genuinely stops the quit rather than warning and disconnecting anyway.
