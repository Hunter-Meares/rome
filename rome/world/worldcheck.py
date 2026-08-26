"""
A reusable connectivity/duplicate-check tool.

Every check in this module is a promoted version of a throwaway script
this project has manually rewritten, once, during a real live-database
incident - see each function's docstring for exactly which one. All
checks are read-only; nothing here ever modifies the database. See
CmdWorldCheck below for the admin-facing command that runs these and
reports findings - it never auto-fixes anything either, matching the
same "list, then a human decides" pattern cleanupnpcs/cleanupitems use.
"""

from collections import defaultdict

from evennia.utils.ansi import strip_ansi

from commands.command import Command
from typeclasses.rooms import Room
from typeclasses.exits import Exit

# Standard compass/vertical directions and the single-letter alias
# Evennia's own convention expects each one to also carry.
STANDARD_DIRECTION_ALIASES = {
    "north": "n",
    "south": "s",
    "east": "e",
    "west": "w",
    "northeast": "ne",
    "northwest": "nw",
    "southeast": "se",
    "southwest": "sw",
    "up": "u",
    "down": "d",
}


def check_duplicate_room_names():
    """
    Groups every room by its plain-text (ANSI-stripped, case-
    insensitive) name. Returns a list of (name, [rooms]) for every
    name shared by more than one room.

    Real incident this catches: the Capitoline Hill build's first
    draft duplicated an existing Forum room's exact name
    ("Clivus Capitolinus - a Quiet Switchback") - only found by a
    live post-build audit, not caught in advance.
    """
    by_name = defaultdict(list)
    for room in Room.objects.all():
        plain = strip_ansi(room.key).strip().lower()
        by_name[plain].append(room)
    return [(name, rooms) for name, rooms in by_name.items() if len(rooms) > 1]


def check_exit_collisions():
    """
    For every room, groups its own outgoing exits by their plain-text
    key. Returns a list of (room, key, [exits]) for every room where
    two or more exits claim the same direction word - only one of them
    is ever actually reachable by typing that word, the rest are
    silently unreachable.

    Real incident this catches: Grove of Champions (#613) had two
    different exits both named "west" (to Blessed Fields and to
    Gardens of the Fortunate) - found by a game-wide exit-collision
    scan prompted by unrelated diligence, not by design.
    """
    findings = []
    for room in Room.objects.all():
        by_key = defaultdict(list)
        for ex in room.exits:
            plain = strip_ansi(ex.key).strip().lower()
            by_key[plain].append(ex)
        for key, exits in by_key.items():
            if len(exits) > 1:
                findings.append((room, key, exits))
    return findings


def check_broken_exits():
    """
    Returns every Exit whose destination doesn't resolve to a real,
    still-existing room - either None outright, or a deleted object's
    reference (which Evennia resolves to literal None, not a "ghost"
    object with pk=None - see CLAUDE.md gotcha #2).
    """
    findings = []
    for ex in Exit.objects.all():
        dest = ex.destination
        if dest is None or not dest.pk:
            findings.append(ex)
    return findings


def check_reachability(start=None):
    """
    Breadth-first traversal from `start` (defaults to
    settings.START_LOCATION) following every exit's destination.
    Returns (reachable, unreachable) - two lists of Room objects.

    Real incident this catches: the Underworld v2 rebuild was run on
    top of v1 without cleaning it up first, leaving two entire
    parallel networks live and reachable at once (54 rooms instead of
    the ~30 either build actually intended) - found by a live
    reachability count coming back wildly higher than expected, not by
    reading the room list.
    """
    if start is None:
        from django.conf import settings
        from evennia.objects.models import ObjectDB

        start_id = int(str(settings.START_LOCATION).lstrip("#"))
        start = ObjectDB.objects.get_id(start_id)

    visited_pks = set()
    queue = [start]
    while queue:
        room = queue.pop()
        if not room or not room.pk or room.pk in visited_pks:
            continue
        visited_pks.add(room.pk)
        for ex in room.exits:
            dest = ex.destination
            if dest and dest.pk and dest.pk not in visited_pks:
                queue.append(dest)

    all_rooms = list(Room.objects.all())
    reachable = [r for r in all_rooms if r.pk in visited_pks]
    unreachable = [r for r in all_rooms if r.pk not in visited_pks]
    return reachable, unreachable


def check_one_way_exits():
    """
    For every exit A->B, checks whether B has any exit leading back to
    A. Returns every exit with no such return path. Not everything
    flagged here is a bug - some one-way exits are entirely deliberate
    (the Underworld ferry, a stealth-escape corridor) - this is a list
    to review, not something to auto-fix.

    Real incident this catches: Maintenance Tunnel's `east` exit into
    Guard Checkpoint had no way back at all (Guard Checkpoint's only
    exit led sideways to Flooded Cistern) - only discovered when an
    actual player walked the route and got stuck, since it read
    exactly like a normal two-way exit from the description alone.
    """
    findings = []
    for ex in Exit.objects.all():
        dest = ex.destination
        origin = ex.location
        if not dest or not dest.pk or not origin or not origin.pk:
            continue  # already covered by check_broken_exits
        has_return = any(
            other.destination and other.destination.pk == origin.pk for other in dest.exits
        )
        if not has_return:
            findings.append(ex)
    return findings


def check_missing_direction_aliases():
    """
    For every exit whose key is a standard compass/vertical direction,
    checks it also has the matching single-letter alias registered.

    Real incident this catches: 201 exits game-wide (mostly the Forum,
    built via a batch script that never set aliases=[...]) were
    walkable in full ("west") but the shorthand ("w") silently failed
    with "Command 'w' is not available."
    """
    findings = []
    for ex in Exit.objects.all():
        plain_key = strip_ansi(ex.key).strip().lower()
        expected_alias = STANDARD_DIRECTION_ALIASES.get(plain_key)
        if not expected_alias:
            continue
        aliases = [strip_ansi(a).strip().lower() for a in ex.aliases.all()]
        if expected_alias not in aliases:
            findings.append((ex, expected_alias))
    return findings


def check_thin_descriptions(min_words=5):
    """
    Flags any room whose description is missing or suspiciously short.

    Real incident this catches: Gardens of the Fortunate was the one
    completely empty-description room in the entire game, found only
    during an unrelated manual review pass.
    """
    findings = []
    for room in Room.objects.all():
        desc = strip_ansi(room.db.desc or "").strip()
        word_count = len(desc.split())
        if word_count < min_words:
            findings.append((room, word_count))
    return findings


class CmdWorldCheck(Command):
    """
    Scan the whole game for structural problems, read-only.

    Usage:
      worldcheck
      worldcheck <check>

    Available checks: duplicates, collisions, broken, reachability,
    oneway, aliases, descriptions. Run with no argument for all of
    them. Never changes anything - every finding is something to look
    at, not something this command fixes for you.
    """

    key = "worldcheck"
    locks = "cmd:perm(Builder)"
    help_category = "admin"

    def func(self):
        caller = self.caller
        which = self.args.strip().lower() if self.args else None

        checks = {
            "duplicates": self._report_duplicates,
            "collisions": self._report_collisions,
            "broken": self._report_broken,
            "reachability": self._report_reachability,
            "oneway": self._report_oneway,
            "aliases": self._report_aliases,
            "descriptions": self._report_descriptions,
        }

        if which and which not in checks:
            caller.msg("Unknown check '%s'. Available: %s" % (which, ", ".join(checks)))
            return

        to_run = [checks[which]] if which else list(checks.values())
        for report_func in to_run:
            report_func(caller)

    def _report_duplicates(self, caller):
        findings = check_duplicate_room_names()
        caller.msg("|w=== Duplicate room names (%d) ===|n" % len(findings))
        if not findings:
            caller.msg("  None found.")
        for name, rooms in findings:
            locs = ", ".join("%s (#%d)" % (r.key, r.pk) for r in rooms)
            caller.msg("  %s" % locs)

    def _report_collisions(self, caller):
        findings = check_exit_collisions()
        caller.msg("\n|w=== Exit-direction collisions (%d) ===|n" % len(findings))
        if not findings:
            caller.msg("  None found.")
        for room, key, exits in findings:
            caller.msg(
                "  %s (#%d): %d exits named '%s' (%s)"
                % (room.key, room.pk, len(exits), key, ", ".join("#%d" % e.pk for e in exits))
            )

    def _report_broken(self, caller):
        findings = check_broken_exits()
        caller.msg("\n|w=== Broken exits (%d) ===|n" % len(findings))
        if not findings:
            caller.msg("  None found.")
        for ex in findings:
            loc = ex.location.key if ex.location else "nowhere"
            caller.msg("  %s (#%d) in %s -> broken destination" % (ex.key, ex.pk, loc))

    def _report_reachability(self, caller):
        reachable, unreachable = check_reachability()
        total = Room.objects.count()
        caller.msg(
            "\n|w=== Reachability ===|n\n  %d/%d rooms reachable from the start location."
            % (len(reachable), total)
        )
        if unreachable:
            caller.msg("  Unreachable rooms (%d):" % len(unreachable))
            for r in unreachable:
                caller.msg("    %s (#%d)" % (r.key, r.pk))

    def _report_oneway(self, caller):
        findings = check_one_way_exits()
        caller.msg("\n|w=== One-way exits, worth a look (%d) ===|n" % len(findings))
        if findings:
            caller.msg(
                "  (some of these are deliberate - the Underworld ferry, stealth "
                "escapes - review, don't assume broken)"
            )
        else:
            caller.msg("  None found.")
        for ex in findings:
            origin_key = ex.location.key if ex.location else "?"
            dest_key = ex.destination.key if ex.destination else "?"
            caller.msg("  %s (#%d): %s -> %s, no return path" % (ex.key, ex.pk, origin_key, dest_key))

    def _report_aliases(self, caller):
        findings = check_missing_direction_aliases()
        caller.msg("\n|w=== Exits missing their direction alias (%d) ===|n" % len(findings))
        if not findings:
            caller.msg("  None found.")
        for ex, expected in findings:
            loc = ex.location.key if ex.location else "nowhere"
            caller.msg("  %s (#%d) in %s - missing alias '%s'" % (ex.key, ex.pk, loc, expected))

    def _report_descriptions(self, caller):
        findings = check_thin_descriptions()
        caller.msg("\n|w=== Thin/empty room descriptions (%d) ===|n" % len(findings))
        if not findings:
            caller.msg("  None found.")
        for room, word_count in findings:
            caller.msg("  %s (#%d): %d word(s)" % (room.key, room.pk, word_count))
