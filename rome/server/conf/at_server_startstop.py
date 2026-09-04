"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence. It
allows for customizing the server operation as desired.

This module must contain at least these global functions:

at_server_init()
at_server_start()
at_server_stop()
at_server_reload_start()
at_server_reload_stop()
at_server_cold_start()
at_server_cold_stop()

"""


def at_server_init():
    """
    This is called first as the server is starting up, regardless of how.
    """
    pass


def at_server_start():
    """
    This is called every time the server starts up, regardless of
    how it was shut down.

    Restores the Germania wilderness's rooms' ndb.wildernessscript
    (world/wilderness_rome.py) by hand - a real bug found live and
    confirmed from inside a real reload: WildernessScript's own
    at_server_start() (the contrib's own restoration logic) is never
    actually invoked by Evennia's generic script-restart machinery,
    because that machinery only resumes scripts with a real ticking
    interval, and the wilderness script has none (it's a pure data
    container, nothing to tick) - verified directly by logging every
    room's ndb.wildernessscript immediately on boot and seeing None,
    before this hook's own restoration call fixed it in the same
    breath. Registering the script via GLOBAL_SCRIPTS
    (server/conf/settings.py) fixed script CREATION surviving a
    reload, but not this - a second, separate gap. This hook is the
    one Evennia guarantees fires on every single boot regardless of
    script intervals, so it's the actual right place to force that
    restoration - just calls the script's own already-correct
    at_server_start() method directly rather than duplicating its
    logic here.
    """
    import evennia

    script = getattr(evennia.GLOBAL_SCRIPTS, "germania_road", None)
    if script:
        script.at_server_start()


def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    pass


def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    pass


def at_server_reload_stop():
    """
    This is called only time the server stops before a reload.
    """
    pass


def at_server_cold_start():
    """
    This is called only when the server starts "cold", i.e. after a
    shutdown or a reset.
    """
    pass


def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or
    reset.
    """
    pass
