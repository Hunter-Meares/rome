r"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "Rome"
# A list of ports the Evennia telnet server listens on Can be one or many.
TELNET_PORTS = [7530]
WEBSERVER_PORTS = [(4011, 4012)] # Default port was in use by another user UGH

######################################################################
# Typeclasses and other paths
######################################################################

# The start position for new characters. Default is Limbo (#2).
START_LOCATION = "#223"

######################################################################
# Default Account setup and access
######################################################################
AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False
AUTO_PUPPET_ON_LOGIN = False
MAX_NR_CHARACTERS = 3

# Points character creation at our custom Rome-themed menu instead of
# the contrib's example_menu.py.
CHARGEN_MENU = "world.chargen_menu"

######################################################################
# SQLite locking fix - root cause diagnosed across many sessions of
# "database is locked" on nearly every evennia reload/shell/stop.
#
# Evennia's default SQLITE3_PRAGMAS (imported above via `from
# evennia.settings_default import *`) never sets journal_mode, so
# SQLite falls back to its default rollback-journal locking: any
# writer's brief exclusive-lock window (the live server commits
# constantly - TICKER_HANDLER ticks, NPCChatter, idmapper flushes)
# blocks even a plain read from a second connection outright. Every
# `evennia reload`/`shell`/`stop` opens a brand-new connection whose
# very first action (Django's own register_functions probe, then
# Evennia's sqlite3_prep() applying SQLITE3_PRAGMAS) is exactly that
# kind of read - if it lands during one of the live server's frequent
# internal writes, it fails immediately. Combined with Python
# sqlite3's default 5-second busy-timeout (Django never overrides
# it), a single unlucky moment was often enough to fail outright
# rather than just wait it out.
#
# Two independent, additive fixes:
#   1. journal_mode=WAL lets readers and a writer operate
#      concurrently (a WAL-mode reader sees a consistent snapshot
#      instead of being blocked by an in-progress write at all) -
#      this is the fix that actually addresses the root cause, not
#      just papering over the symptom with a longer wait. Applied via
#      SQLITE3_PRAGMAS (Evennia's sqlite3_prep() runs every pragma in
#      this tuple on each new connection), the same supported
#      mechanism the default pragmas already use - not a one-off
#      manual migration step.
#   2. A longer connection timeout (Python sqlite3's own busy-handler
#      retry window, 5s by default, never overridden anywhere before
#      this) as a second line of defense for the rarer case that's
#      still a real momentary collision even under WAL (e.g. two
#      writers at once - WAL still serializes writers against each
#      other, just not against readers).
SQLITE3_PRAGMAS = SQLITE3_PRAGMAS + ("PRAGMA journal_mode=WAL",)
DATABASES["default"]["OPTIONS"] = {"timeout": 20}

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")


try:
    # Created by the `evennia connections` wizard
    from .connection_settings import *
except ImportError:
    pass

# List of Python modules Evennia scans for prototype dictionaries (like
# ARGUS_NPC in world/prototypes.py, or DAGGER/BROADSWORD/HEALTH_POTION in
# world/combat.py), making them spawnable by name via spawn("NAME") or the
# in-game @spawn command. This list is exhaustive, not additive - only
# modules listed here are scanned, so any new file with prototypes must be
# added here too.
PROTOTYPE_MODULES = ["world.prototypes"]

# Achievements contrib (evennia.contrib.game_systems.achievements) - points 
# to the module(s) containing achievement definitions. Actual achievement 
# data (name/desc/category/tracking/count/prereqs for each one) lives in 
# world/achievements.py, not here - this setting just tells the contrib 
# where to find it. The actual progress-tracking calls (track_achievements()) 
# are wired into the relevant game logic separately: world/combat.py (combat 
# victories, reaching level 100) and world/economy.py (merchant purchases). 
# Players check their own progress in-game with the 'achievements' command.
ACHIEVEMENT_CONTRIB_MODULES = ["world.achievements"]

# world/help_entries.py originally held only Evennia's own stock
# scaffolding "evennia" help topic (never customized for Rome, deleted
# per request), leaving the file genuinely empty. An empty
# HELP_ENTRY_DICTS list still gets scanned by default (Evennia's
# default FILE_HELP_ENTRY_MODULES = ["world.help_entries"]) and logs a
# spurious [EE] "Could not find file-help module" on every reload -
# technically true but not an actual error. All of Rome's real help
# content (god/pantheon lore, races/classes/stats) is added directly
# to the database instead (world/god_help.py, world/help_setup.py),
# so there's nothing left for this file-based mechanism to load.
FILE_HELP_ENTRY_MODULES = []

# Makes all of Evennia's default commands (look, get, movement, etc.)
# use our custom MuxCommand base, so the HP/MP/SP prompt refreshes
# after every command, not just combat ones.
COMMAND_DEFAULT_CLASS = "commands.command.MuxCommand"

# Custom multimatch disambiguation display - see server/conf/at_search.py
# for the real bug this fixes: every player search here actually routes
# through rpsystem's sdesc-aware override, which only recognizes a
# LEADING number ("1-name") to pick between matches, not Evennia's own
# default trailing-number display ("name-1") - a real, silent mismatch
# a live player hit directly.
SEARCH_AT_RESULT = "server.conf.at_search.at_search_result"

# Auditing (evennia.contrib.utils.auditing) - logs every command a
# player sends to server/logs/audit_YYYY-MM-DD.log (JSON, one file
# per day), for QA and post-incident investigation (e.g. "what did
# this player actually do before X happened"). The contrib ships with
# default AUDIT_MASKS that already scrub passwords out of login/
# character-creation commands before anything is written, so this is
# safe to enable without extra config - but it does log everything
# else in cleartext, including public/private in-character speech, so
# treat these logs with the same care as any other record containing
# player communications.
#
# AUDIT_OUT (server output back to clients) is deliberately left off -
# the contrib's own docs warn a single broadcast to everyone online
# becomes one log line *per connected player*, which is a lot of
# volume for not much investigative value compared to AUDIT_IN.
SERVER_SESSION_CLASS = "evennia.contrib.utils.auditing.server.AuditedServerSession"
AUDIT_IN = True
AUDIT_OUT = False

# The wilderness surrounding Rome / the road to Germania
# (world/wilderness_rome.py). A real bug found live: a WildernessScript
# created ad hoc via the contrib's own create_wilderness() is never
# marked active, so Evennia's server-boot script-restart machinery
# never calls its at_server_start() hook - meaning every wilderness
# room's in-memory wilderness reference silently went None after a
# real reload, breaking movement and descriptions outright for anyone
# still out there. Registering it here instead makes Evennia create,
# start, and reliably restart it on every boot, which is what actually
# fires at_server_start() when it's supposed to - the contrib's own
# docs name this as the fix for exactly this problem.
GLOBAL_SCRIPTS = {
    "germania_road": {
        "typeclass": "world.wilderness_rome.GermaniaWildernessScript",
        "desc": "The wilderness surrounding Rome, on the road to Germania",
    },
}
