"""
Session analytics

Lightweight, deliberately minimal tracking of real player sessions -
when someone logs in, how long they actually play, and which rooms
they visit along the way. No command logging, no chat/message
capture - just movement and timing. The goal is answering real
questions ("how long do people actually play before leaving? where
are they when they go?") with real data instead of guessing from a
single anecdote.

All session records are stored on one global Script, queried via the
CmdSessionLogs admin command (see bottom of this file).
"""

import time

from evennia import DefaultScript, create_script
from evennia.utils import search
from commands.command import Command


def _get_logger_script():
    """Finds the single global analytics script, creating it on first use."""
    existing = search.search_script("session_analytics")
    if existing:
        return existing[0]
    script = create_script(
        "evennia.DefaultScript",
        key="session_analytics",
        persistent=True,
    )
    script.db.sessions = []
    return script


def start_session(character, account):
    """
    Called on login (see typeclasses/accounts.py at_post_login) -
    begins tracking a new session for this character. Stored directly
    on the character (not the global log yet) until the session ends,
    so an in-progress session doesn't clutter the log with incomplete
    records if the server reloads mid-session.
    """
    character.db.session_start = time.time()
    character.db.session_rooms = [character.location.key] if character.location else []


def log_room_visit(character):
    """
    Called whenever a character finishes moving (see world/combat.py
    CombatCharacter.at_post_move) - appends the new room to this
    session's room trail. Uses full reassignment rather than in-place
    .append() - the safe, reliable pattern for Evennia persistent
    attributes holding nested structures.
    """
    if character.db.session_start is None:
        return
    if not character.location:
        return
    rooms = character.db.session_rooms or []
    rooms.append(character.location.key)
    character.db.session_rooms = rooms


def end_session(character, account):
    """
    Called on disconnect (see typeclasses/accounts.py at_disconnect) -
    finalizes this session's record and saves it to the global log.
    """
    if character is None or character.db.session_start is None:
        return

    logger = _get_logger_script()
    record = {
        "account": account.key,
        "character": character.key,
        "start": character.db.session_start,
        "end": time.time(),
        "rooms": character.db.session_rooms or [],
    }
    sessions = logger.db.sessions or []
    sessions.append(record)
    logger.db.sessions = sessions

    character.db.session_start = None
    character.db.session_rooms = None


class CmdSessionLogs(Command):
    """
    Shows recent player session records - how long people actually
    played and which rooms they visited, most recent first.

    Usage:
      sessionlogs
      sessionlogs <number>

    With no argument, shows the last 15 sessions. Give a number to
    see more or fewer.
    """

    key = "sessionlogs"
    locks = "cmd:perm(Admin)"
    help_category = "admin"

    def func(self):
        logger = _get_logger_script()
        sessions = logger.db.sessions or []

        if not sessions:
            self.caller.msg("No session records yet.")
            return

        count = 15
        if self.args and self.args.strip().isdigit():
            count = int(self.args.strip())

        recent = sessions[-count:]
        recent.reverse()

        lines = ["|wRecent Sessions|n (most recent first)"]
        for rec in recent:
            duration_secs = (rec["end"] or time.time()) - rec["start"]
            minutes = int(duration_secs // 60)
            seconds = int(duration_secs % 60)
            started = time.strftime("%Y-%m-%d %H:%M", time.localtime(rec["start"]))
            room_count = len(rec["rooms"])
            last_room = rec["rooms"][-1] if rec["rooms"] else "unknown"

            lines.append(
                "  %s | %s (%s) | %dm %ds | %d rooms | last seen: %s"
                % (started, rec["character"], rec["account"], minutes, seconds, room_count, last_room)
            )

        self.caller.msg("\n".join(lines))
