"""

Lockfuncs

Lock functions are functions available when defining lock strings,
which in turn limits access to various game systems.

All functions defined globally in this module are assumed to be
available for use in lockstrings to determine access. See the
Evennia documentation for more info on locks.

A lock function is always called with two arguments, accessing_obj and
accessed_obj, followed by any number of arguments. All possible
arguments should be handled with *args, **kwargs. The lock function
should handle all eventual tracebacks by logging the error and
returning False.

Lock functions in this module extend (and will overload same-named)
lock functions from evennia.locks.lockfuncs.

"""

# def myfalse(accessing_obj, accessed_obj, *args, **kwargs):
#    """
#    called in lockstring with myfalse().
#    A simple logger that always returns false. Prints to stdout
#    for simplicity, should use utils.logger for real operation.
#    """
#    print "%s tried to access %s. Access denied." % (accessing_obj, accessed_obj)
#    return False


def is_god(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Usage: is_god()

    True if accessing_obj's own db.level is over 100 - a real god, per
    this project's own Cursus Divinorum tier system (see CmdGodLevel,
    world/combat.py). Exists specifically because the stock attr()
    lockfunc can't do this correctly for an ACCOUNT: world/factions.py
    and world/religion.py's faction/religion channels used
    "attr(level, 100, compare=gt)" directly, which reads db.level off
    whatever object is actually being checked - correct for a
    Character (every other god-check in this game already compares
    caller.db.level the same way), but Evennia's own channel
    subscribe path (CmdChannel's /sub switch, comms.py's
    sub_to_channel) checks the ACCOUNT, not the puppeted character,
    and db.level is only ever set on the character. The result: a
    real, confirmed live bug reported directly by a player - Jupiter
    (level 106) could not 'channel/sub' any faction/religion channel
    at all, since account.db.level is always None. It was invisible
    for a long time specifically because Jupiter's account also
    happens to be a true superuser, which bypasses every lock
    unconditionally at the engine level (see CLAUDE.md gotcha #6) -
    masking this for the one account most likely to be used for
    testing, while leaving it silently broken for any FUTURE
    non-superuser god (the normal, intended way anyone becomes a god
    here) trying to manually (re)subscribe themselves.

    Checks accessing_obj's own db.level first (already correct for a
    Character, and for any future direct Character-based lock check),
    falling back to its puppeted character's level if accessing_obj is
    an Account with no db.level of its own - covering exactly the gap
    above without changing how this already-correct check behaves for
    a Character.
    """
    level = accessing_obj.attributes.get("level", default=None)
    if level is None:
        puppet = getattr(accessing_obj, "puppet", None)
        if puppet:
            level = puppet.attributes.get("level", default=0)
    return bool(level) and level > 100
