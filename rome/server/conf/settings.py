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
