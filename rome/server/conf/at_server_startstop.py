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

    # Same restoration gap, same fix, for the second wilderness stretch
    # (world/wilderness_amber_coast.py) - see that hook's own docstring
    # above for why this has to be called by hand.
    amber_script = getattr(evennia.GLOBAL_SCRIPTS, "amber_coast_road", None)
    if amber_script:
        amber_script.at_server_start()

    # Real, confirmed live incident: a CombatTurnHandler's own ticking
    # (interval=5, persistent=True - the mechanism behind both the
    # 20-second turn timeout and the NPC turn-pacing delay) can survive
    # a restart as PERSISTED DATA (db.fighters, db.turn all correct)
    # while its actual repeating task never resumes - confirmed live by
    # checking two real, currently-active fights after an earlier
    # restart: both showed is_active=True but
    # time_until_next_repeat()=None. Root cause, traced into Evennia
    # core itself (evennia/scripts/manager.py's
    # update_scripts_after_server_start()): a script's task is only
    # ever re-armed via _unpause_task(), which is a no-op unless the
    # OLD process had already, gracefully PAUSED it first (writing
    # db._paused_time) as part of a clean shutdown sequence. Any
    # restart that skips that graceful pause step - a crash, an OOM
    # kill, or anything else that doesn't go through Evennia's normal
    # shutdown path, plausibly explaining a real player report
    # ("the server restart broke this [NPC], I can't do anything until
    # he ends his turn") - leaves _paused_time unset, so unpause never
    # fires and the script silently never ticks again. A plain
    # `evennia reload` issued from an already-healthy running process
    # pauses correctly and doesn't hit this; this is specifically for
    # whatever restart DIDN'T get that chance. Rather than trying to
    # fix Evennia's own pause/unpause machinery, this just
    # unconditionally re-arms every currently-active CombatTurnHandler
    # on every boot - script.start() isn't gated on prior pause state
    # at all, and is a safe, idempotent no-op for a fight whose ticking
    # was already fine.
    from evennia.scripts.models import ScriptDB
    from world.combat import CombatTurnHandler

    for script in ScriptDB.objects.filter(
        db_typeclass_path__endswith=".CombatTurnHandler", db_is_active=True
    ):
        script.start()


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
