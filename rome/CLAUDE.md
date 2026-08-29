# Rome MUD — Project Context for Claude Code

Roman-themed text MUD built on **Evennia 6.1.0** (Python 3.12.13). Server root: `~/muddev/rome/`.

This file is a working reference, not a finished spec — the game is under active, ongoing development. When picking up work here, prefer reading the actual current code over trusting descriptions below if they ever conflict; this file can drift out of date faster than the codebase does.

---

## Project shape

- **Theme**: Roman Empire, starting with a Colosseum gladiator-escape questline, expanding toward Rome proper and eventually other cities.
- **Current playable content**: Colosseum (holding cells → escape → Atrium → Ludus training area → Deeper Sands arena), a real Underworld (post-death, 32 rooms), a basic economy with several merchants, a substantial Forum Romanum/Capitoline Hill complex (Tabularium, Temple of Vesta, the Senatorial Podium), and the Subura (16 rooms, off the Forum's Argiletum exit - dense, working-class, a deliberate tonal contrast to the Forum) - 264 rooms total as of this writing. **This directly supersedes the "not yet built" note this line used to carry** - that was true early in the project but is stale now; verify against a live room count before trusting either version.
- **Not yet built**: a second city, wilderness travel between cities. Further Rome-city expansion beyond the Forum/Capitoline is an active, ongoing direction, not a deferred one - see rome_mud_todo.md for current build-project status.
- **Players so far**: small, real player base already hitting real bugs — this is not purely a solo dev sandbox anymore.

---

## Architecture — where things live

- `world/combat.py` — the single largest file. Combat engine, `CombatCharacter` typeclass, all NPC typeclasses, spell/skill functions, XP system, resting, most combat commands. Read this first for almost anything player-stats-or-combat related.
- `world/chargen_menu.py` — character creation EvMenu flow. `RACES` and `CLASSES` dicts here are the single source of truth for race/class stat data — the website (`races.html`/`classes.html`) and in-game help topics are both derived from this, not the other way around.
- `world/character_creator.py` — the `charcreate` command itself (argument parsing). Note: the base Evennia contrib's own `charcreate` never parsed its own arguments at all; this was a real bug fixed this project, not a customization for its own sake.
- `world/economy.py` — gold, `NPCMerchant` typeclass, shop EvMenu (buy/sell).
- `world/achievements.py` — achievement definitions (dicts) plus `announce_achievements()`, the shared helper every `track_achievements()` call site uses to show a vivid completion banner.
- `world/analytics.py` — session login/logout/room-trail logging (`sessionlogs` admin command).
- `world/colosseum.py` — `WanderingNPC` script, Colosseum-specific room/NPC logic.
- `world/underworld.py` — `CharonTimer`, `CharonFerryExit`, the return-riddle mechanic.
- `world/party.py` — party system (`CmdParty`, invite/accept/leave/kick).
- `world/doors.py` — custom door typeclass on top of the `simpledoor` contrib.
- `world/help_setup.py` — generates in-game help topics from `RACES`/`CLASSES`/`STAT_HELP` data, plus a handful of standalone topics (`groupcombat`, `gold`, `trade`, `achievements`). Run `create_all_help_entries()` after any change here.
- `world/prototypes.py` — every spawnable object/NPC prototype. `PROTOTYPE_MODULES` in settings includes this file — **never add another module to that setting without checking it doesn't contain unrelated module-level dicts** (see Gotchas below).
- `commands/default_cmdsets.py` — where every command and contrib gets actually registered. If a command doesn't exist in-game, check here first.
- `typeclasses/characters.py`, `typeclasses/accounts.py` — base hooks (divine-presence announcements, MOTD, some session/account-level logic). Not in current working context as of this file's writing — verify current contents directly rather than trusting old descriptions.

---

## Core stat system

Four core stats: **Virtus** (melee power), **Agilitas** (accuracy/dodge/ranged power), **Ingenium** (spell power), **Vigor** (HP/damage reduction). Base 10 each.

- **Completely static after chargen.** Race + class `stat_mods` apply once, permanently. Leveling only grows `max_hp`/`max_mp`/`max_sp` — verified directly, this is the *only* place any of the four core stats ever get touched in the whole codebase.
- **Real ceiling**: base 10 + best race bonus (+3) + best class bonus (+3) = **16** max on any single stat. No stat mod anywhere exceeds +3 individually.
- **`_leans_caster()`** in `chargen_menu.py` determines whether a race/class is caster-leaning (Ingenium is its single highest stat) or not, with a `None` return for genuinely tied/balanced stats. Used for the chargen synergy hint (see below). This went through two real bug-fix rounds: first for balanced entries (Human) incorrectly resolving to "physical" via tuple tiebreak order, then for a *partial* tie (Centaur's Virtus/Agilitas) hitting the same bug in a narrower form. If touching this function again, test it against all 48 race×class combos before trusting a "looks right" result.
- **Harpy's stat_mods were deliberately changed** mid-project from `agilitas:3, ingenium:0` to `agilitas:2, ingenium:2` after a real design discussion — the original was purely physical-locked despite Harpy's "Windborne Seeker" sky/bird-omen flavor echoing Augur's own bird-augury theme. This was a deliberate rebalance, not a bug fix.
- **Chargen synergy hint**: soft, informational-only note shown after class selection if race and class lean in genuinely different directions (physical vs. magical specifically — not just "different primary stat," that was tried first and was too noisy). Never blocks the choice.

---

## Combat system

- **Hit/miss on every damage path** — basic `attack`, `spell_attack`, and (after a fix) `skill_attack` all use a real `randint(1,100) + accuracy + stat_bonus` vs. `defense_value` roll. `skill_attack` originally always connected regardless of stats — an inconsistency with spells, fixed this project.
- **`ACCURACY_STAT_MULTIPLIER = 7`** — shared constant controlling how strongly the attacker's relevant stat swings hit chance. Calibrated backward from a specific target: a maximally-invested attacker should hit a weak-defense target ~90%+ of the time. Applied identically in `get_attack`, `spell_attack`, and `skill_attack` for consistency. Deliberately asymmetric — only the attacker's bonus is multiplied, the defender's baseline is not.
- **Damage** uses a *separate*, halved stat bonus (`(stat-10)//2`) from the accuracy roll — this split was a deliberate fix, not always the case. Don't conflate the two when touching either.
- **Sides/teams**: every fighter gets a `combat_side` on entering combat. `fight all` groups by party leader. Victory checked by counting distinct *living sides*, not raw fighter count. `is_ally()` prefers real `combat_side` over party membership when actively in combat (handles dueling your own party member for sport).
- **XP and gold** both split proportionally by `damage_log` (per-attacker damage tracked on the defender) rather than winner-take-all on the killing blow. Gold is *derived* from `xp_reward` via `GOLD_PER_XP_DIVISOR`, not a separately hand-tuned field — this means "higher level NPCs pay more gold" falls out automatically from the existing XP scaling.
- **Resting**: `rest` is a gradual regen state (2.5%/10s = 15%/minute of max HP/MP/SP), not instant. Can't move or use combat commands while resting; `stand` ends it early; being pulled into combat auto-interrupts it via `initialize_for_combat`. Uses `TICKER_HANDLER`, not a bare timer (survives reload).
- **Persistent NPCs**: `RespawningNPC` (Ludus trainers, Deeper Sands Arena Fighters) uses a persistent `RespawnTimer` Script, not `delay()`, specifically so a respawn-in-progress survives a server reload.
- **The stuck-loop bug** (multiple rounds, see Gotchas) is fully fixed as of this file's writing — `next_turn()`'s fighter-pruning correctly handles a fighter reference resolving to literal `None`, not just an object with `pk=None`.

---

## Economy

- **Gold**: plain integer (`character.db.gold`), not individual coin objects — matches Evennia's own official recommended pattern for exactly this reason.
- **Shops are effectively infinite-stock**: buying spawns a fresh copy from the ware's `prototype_key` rather than moving/depleting the actual display item. Selling back deletes the item outright (not moved into the merchant's inventory) — both deliberate, to avoid a shop ever running dry and to avoid sold goods piling up as confusing duplicate listings.
- **Sell-back rate**: 50% of an item's price (`SELL_BACK_RATE` in `economy.py`).
- **Five real merchants deployed**: four flavor-goods vendors (Colosseum vendor, Forum bookseller/goldsmith/perfumer/food vendor) plus the Ludus weaponsmith (`world.economy.LudusWeaponsmith`, standing in Ludus Entrance, room #320) — the first shop actually selling real combat gear. She stocks herself automatically from `LUDUS_WEAPONSMITH_STOCK` — three tiers (Novice/Veteran/Champion, levels 2/6/10), each a distinctly-named/flavored item rather than a numeric reskin, using `compute_weapon_stats`/`compute_armor_stats` (`world/combat.py`) for pricing/stats.
- **`learnspell`/`learnskill` now cost gold and require an in-person trainer.** Two trainers (`world.combat.SpellSkillTrainer`): the Ludus weapons master (Ludus Entrance) teaches skills, the Flamen of the Cella (Main Cella - Jupiter, Capitoline Hill) teaches spells. Cost scales with level via `compute_learn_cost()`. `trainer` lists what a specific trainer offers your class, with cost and level shown.

---

## Achievements

5 defined in `world/achievements.py` (First Blood, Battle-Hardened, Free at Last, Legend, A Fine Purchase). Every completion fires a vivid banner via `announce_achievements()` — this required manually capturing and using `track_achievements()`'s return value (the list of newly-completed keys) at every call site; the contrib does **not** auto-announce anything on its own. If adding a new achievement, remember the tracking call is a separate, manual step from the achievement definition — defining one with no matching `track_achievements()` call anywhere is dead data that can never complete (this happened once already this project, with 4 achievements that were later trimmed down to the current 5). `announce_achievements()` also feeds the rumor system (`world/rumors.py`) — every completion is remembered so opted-in NPCs (currently the two heralds) can mention it later.

Requires `ACHIEVEMENT_CONTRIB_MODULES = ["world.achievements"]` in `server/conf/settings.py` — a manual settings edit, not deployable via file upload alone.

---

## Contribs integrated so far

| Contrib | What it adds | Notes |
|---|---|---|
| `rpsystem` | sdesc/mask/recog, `greet` (custom, mask-proof) | Combat stays real-name-based by design; only social layer uses sdesc |
| `simpledoor` | Door typeclass | Custom `DescriptiveOpenCloseDoor` layered on top |
| `character_creator` | Chargen framework | Had a real upstream bug (didn't parse its own name argument) |
| `barter` | Player-to-player safe trading (`trade`/`offer`/`accept`/`decline`) | Registered exactly per docs, unmodified |
| `achievements` | Achievement tracking, `CmdAchieve` | See Achievements section above |
| `ingame_map_display` | `map` command | Friendlier docstring layered on via subclass, real logic untouched |
| `debugpy` | Live VS Code breakpoint debugging | Locked to Developer permission via subclass (contrib's own default lock wasn't verified safe). **Client-side VS Code `launch.json` setup was deferred/skipped** — server-side code is deployed and harmless sitting unused |
| `ingame_reports` | `bug`, `report <player> = <message>`, `idea`/`ideas`, admin `manage reports` | Pure `AccountCmdSet` addition (`ReportsCmdSet`), no migration — each report type auto-creates its own hub Script on first use |

**Chosen but not yet built** (see to-do list): `crafting`, `extended_room`. `mail` (in-character half), `health_bar`, and `ingame_reports` are now built; `auditing` and `building_menu` are now built; `git_integration` was explained and deliberately skipped (this project's external dev workflow already covers what it'd add, with better safety - no in-game code-pull path exists on purpose).

**Explicitly discussed for the future, not started**: `wilderness` + `slow_exit` together, for eventual travel between Rome and other cities — deliberately scoped as "once a second city actually exists to travel to," not before.

---

## Hard-won gotchas — read before touching these areas again

1. **`PROTOTYPE_MODULES` scans every module-level dict, not just intended prototypes.** `world.combat` was once listed there and Evennia silently injected a `prototype_key` attribute into `SPELLS`/`SKILLS`, corrupting NPC action-gathering. Only `world.prototypes` should be listed.

2. **A deleted object's reference, reloaded from a persisted attribute, resolves to literal `None` in Evennia — not a "ghost" object with `pk=None`.** Any code checking `if fighter.pk` on a list of persisted references needs `if fighter is not None and fighter.pk` instead, or it will crash on the exact object it's trying to detect. This caused a real, multi-session stuck-loop bug in `CombatTurnHandler.next_turn()`.

3. **Always call `super()` in overridden hooks, even ones assumed to do nothing by default.** Two separate real bugs this project: `at_post_move` without `super()` silently broke auto-showing the new room after movement; `at_object_creation` without `super()` broke similarly elsewhere.

4. **Contribs don't always re-export everything at their top package `__init__.py` level.** `MapDisplayCmdSet` is re-exported from `ingame_map_display`'s top level; `CmdMap` is not — it's one level deeper, in the inner module sharing the package's name. A wrong assumption here once broke the *entire* `default_cmdsets.py` file (ImportError crashed the whole module, silently falling back to Evennia's bare default cmdset for everyone). **Verify contrib import paths directly against source/docs before writing them, every time** — don't pattern-match from a different contrib's import style.

5. **`time_until_next_repeat()` returns `None`, not a number, if a Script's repeat timer hasn't actually started yet** (e.g., during the Script's own `at_script_creation()`, since it's created with `autostart=False`). Guard with `(x or 0)`.

6. **A superuser account bypasses every lock unconditionally, at the engine level.** No lockstring can restrict a true superuser — this isn't a bug to fix, it's a permanent boundary. Also: checking `obj.access(obj, "edit")` with the *object* as accessor doesn't reliably reflect the same bypass a real logged-in account session gets — don't trust that kind of diagnostic as equivalent to how a live command actually resolves permissions.

7. **`track_achievements()` returns the newly-completed keys specifically so you can announce them — using the return value is a separate step from calling the function.** Don't assume completion is auto-announced by any contrib unless you've wired it yourself.

8. **When debugging something that "looks correct in code review," get real evidence before continuing to reason abstractly.** The stuck-loop bug took three separate rounds of adding/removing temporary diagnostic `msg()` calls before the real root cause (see gotcha #2) was found — careful reading of correct-looking code missed it repeatedly. `debugpy` is now integrated specifically to make this faster next time (server-side only currently; VS Code client setup still pending).

9. **`evennia reload` has twice now shut the server down without the portal actually bringing it back up**, leaving only the portal process alive and the game fully unreachable until `evennia start` is run manually to relaunch just the server component (`Portal is already running... Not restarted. Server starting ... Server started.`). Both incidents happened directly after a code deploy, both times with a real account connected. Always check `server/logs/server.log` for a "Server successfully reloaded" line (or its absence) right after any `reload`, rather than assuming it worked - don't rely on the command's own exit output, since it always times out from this tool's side regardless of outcome.

---

## Design decisions worth knowing, not just bugs

- **God tiers (levels 101–106, the "Cursus Divinorum" ladder)** are a deliberate, separate **game-logic** attribute (`db.level`), each mapped to a real Evennia permission via `GOD_TIERS` in `world/combat.py` and kept in sync by the `godlevel` command - not the same thing as true Evennia superuser status. Jupiter's account (formerly Zeus, renamed mid-project) does separately happen to be a true superuser, but that's incidental to being level 106 (Rex Divum), not the same mechanism - a true superuser bypasses every lock unconditionally regardless of `db.level` (see gotcha #6 below). `rank_title()` shows the specific tier name (Novus Deus through Rex Divum); `class_display` is deliberately just a flat "Divine" for every god instead, so the two don't repeat the same fact under different labels.
- **Personal-instance NPCs vs. persistent/respawning NPCs**: a deliberate split, not accidental inconsistency. Low-stakes/personal moments (the initial Colosseum challenge, Rutilus) stay instance-spawned per-player; standing training/farming content (Ludus, Deeper Sands) is persistent and respawns on a timer.
- **Wandering Colosseum NPCs are deliberately bounded** to a specific `wander_rooms` list set at spawn time, not "wander anywhere reachable." They will **not** automatically wander into Rome once it's built and connected — extending any NPC's beat into new territory is a deliberate, small edit, not automatic.
- **The Underworld ferry is now one-way** (the `back` exit from River Styx Crossing was deliberately removed) — matches the mythology and closes a real "death has no weight" exploit. This raises the stakes for any future Underworld expansion: players are now fully committed once they cross, so dead-ends/connectivity bugs in expanded content would leave someone genuinely stuck.
- **Underworld expansion is built and confirmed**: 32 rooms (Asphodel Meadows, Elysium, Tartarus, the River Lethe, the Judgment Hall), 10 ghostly NPCs (6 with `NPCChatter` dialogue, 2 deliberately silent), fully BFS-verified reachable with no dead ends. The open design tension that motivated waiting to build it - making death feel interesting without undermining death having real stakes - was resolved in practice: the Underworld ferry is one-way (see above) and level 6+ resurrection now returns to the Temple of Jupiter on the Capitoline rather than the starting cells, keeping a real sense of consequence around dying.

---

## Current known-untested items (built, not yet confirmed working live)

Pulled from the project to-do list — check there for the full, current list, but these are the standout ones:
- `RespawningNPC` surviving a server reload mid-respawn-wait (the entire reason it's a persistent Script)
- XP/gold splitting in a real group kill against an NPC; a pure-support Medicus leveling from casting XP alone (the real 2v2 party fight test confirmed sides/turn order/damage all work under a real group, but PvP kills correctly award no XP/gold by design - `xp_reward` is an NPC-only concept - so this specific split still needs a real group-vs-NPC kill to confirm)
- `party decline`/`leave`/`kick` — `invite`/`accept` are now confirmed live (see rome_mud_todo.md's 2v2 party fight test), the rest of the command isn't yet
- `slay` used on an actual player character (only ever tested on NPCs)

---

## Working conventions this project has followed

- **Verify contrib behavior against live docs/source before writing integration code** — don't pattern-match from memory or from a different contrib's conventions (see gotcha #4).
- **Test edge cases with real computed numbers, not just "looks right"** — several fixes this project (the caster-lean tie bug, the hit-chance multiplier calibration) were caught specifically by running the actual logic against real data before shipping, not by reading the code and judging it correct.
- **When something breaks repeatedly in the same area, add temporary diagnostics rather than keep guessing** — used successfully (if reactively) for the stuck-loop bug; `debugpy` is now available to do this more directly going forward.
- **Deploy instructions are given explicitly with every code change** — which file(s) to upload, whether a reload is needed, whether a manual settings.py edit or one-time live command is required on top of the file itself.
- **A to-do list (`rome_mud_todo.md`) is maintained alongside actual work** — check it for current status before assuming something is or isn't built; it's been kept current throughout this project and corrected multiple times when it was found to be stale or inaccurate.
- **`world/motd.py`'s `RECENT_UPDATES_DATE`/`RECENT_UPDATES_TEXT` get updated after any major player-facing change** — a new area, a new player-usable command, a bugfix players would actually notice. Shown at login and via the `motd`/`news` command, both reading from the same `get_motd()`. Keep it to 2-3 lines, written for a player, not a changelog entry — admin-only/internal changes don't belong here.

---

## Testing

Evennia ships its own testing framework built for exactly this kind of project — `EvenniaTest`/`EvenniaCommandTest` (`evennia.utils.test_resources`), which spin up an in-memory test database with pre-built fixtures (`self.char1`, `self.char2`, `self.room1`, etc.) so command/typeclass behavior can be tested without a live running server. Run with `evennia test .` (or a specific path) from the game root.

The first real test file was `world/tests_chargen.py`, covering `_leans_caster` and the chargen synergy-hint mismatch logic - chosen first because it's pure logic with zero database dependency, and because it had already had two real, separate bugs found by hand (not by any automated test), making it the highest-value place to lock in regression coverage first. It's since grown into a full suite: 15 test files (`tests_chargen.py`, `tests_combat.py`, `tests_combat_commands.py`, `tests_party.py`, `tests_achievements.py`, `tests_underworld.py`, `tests_items.py`, `tests_economy.py`, `tests_colosseum.py`, `tests_npcs.py`, `tests_quit.py`, `tests_social.py`, `tests_equipment.py`, `tests_worldcheck.py`, `tests_ingame_reports.py`), **352 tests total, all passing** (one intentional skip). Read `tests_chargen.py` as the pattern for plain-`unittest`-style tests (no `EvenniaTest` needed) when testing pure calculation/logic functions elsewhere in the codebase.

**Note on that file's approach**: it duplicates `_leans_caster`'s logic inline rather than importing the real function, specifically to avoid any Evennia app-loading/import-path fragility in a first test file. This is a real tradeoff, not a best practice to copy blindly — if `_leans_caster` itself changes, the duplicated copy must be updated to match or the tests will silently stop testing the real code. Prefer a direct `from world.chargen_menu import _leans_caster` import in future test files where import-path risk is lower, and consider migrating this file to do the same.

### Where the real testing priority is — regression coverage for the documented gotchas

Every numbered gotcha above represents something that already broke once, silently, and took real debugging effort to find. Each is a strong candidate for a permanent regression test, roughly in priority order:

1. **`next_turn()`'s fighter-pruning** (gotcha #2) — the highest-value target. A test should construct a `fighters` list containing a literal `None` entry (not just a deleted-but-referenced object) and confirm pruning handles it without raising, and that the fight correctly ends when only one side remains. This is exactly the scenario that took three rounds of live debugging to actually diagnose.
2. **Achievement tracking wiring** — a test confirming every achievement `key` defined in `world/achievements.py` has at least one corresponding `track_achievements()` call site somewhere in the codebase would have caught the original "4 of 8 achievements were dead data" bug automatically, rather than requiring a manual code read to notice.
3. **Hit-chance math** (`get_attack`/`get_defense`/`ACCURACY_STAT_MULTIPLIER`) — needs `EvenniaTest` (real character objects with real stats), but is otherwise straightforward: given known stats, assert the computed hit-chance percentage falls in the expected range, especially the calibration target (max-invested attacker vs. weak-defense target should land near 90%+).
4. **Resting state transitions** — `rest` → interrupted by combat should correctly clear `db.resting` and stop the `TICKER_HANDLER` callback; this one's more of an integration test than a pure unit test, given the `TICKER_HANDLER` dependency.

### A real limitation worth knowing before assuming everything is equally testable

Several of this project's hardest bugs were about **live runtime state** — a stuck turn-handler Script, `TICKER_HANDLER`-based resting, a persistent Script surviving a server reload. These are inherently harder to unit test in isolation than pure logic like the stat/hit-chance math, and may need Evennia's time-mocking utilities or be better suited to integration-style tests run against a real (test) server than pure `EvenniaTest` unit tests. Don't assume a clean test suite covering the pure-logic pieces also means the trickiest runtime-state bugs are protected against — those need a different, heavier kind of test, or deliberate manual testing, to catch a regression.
