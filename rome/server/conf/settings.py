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
START_LOCATION = "#69"

######################################################################
# Default Account setup and access
######################################################################
AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False
AUTO_PUPPET_ON_LOGIN = False
MAX_NR_CHARACTERS = 3

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
