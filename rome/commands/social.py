"""
Social commands

A player-facing replacement for 'who' - shows name, custom title,
race, class, and level instead of the technical admin table (account
name, room, protocol, host IP). Admins/Developers still see the full
technical table, unchanged - see evennia.commands.default.account.CmdWho
for that logic, which this subclasses and falls back to.

Also includes 'title', letting players set a short custom title shown
on the who list (e.g. "the Undefeated", "Senator of Rome").
"""

import time
from world.combat import rank_title, wizinvis_hides_from

import evennia
from evennia.commands.default.account import CmdWho as DefaultCmdWho
from evennia.commands.default.comms import CmdPage as DefaultCmdPage
from evennia.utils import create, utils

from commands.command import Command

# Column-width caps for the who tables. Every OTHER column already had a
# sensible crop() applied (Account/Char/Race/Class) - Title and Room were
# the two left fully uncropped, and since both can genuinely run long
# (a room name, or up to a 40-character custom title), they were the
# actual cause of the table wrapping into the broken multi-line mess a
# too-wide EvTable produces on a normal client width. Named constants
# so the /full and lean tables (and the plain player table) all stay
# in sync rather than drifting to different, inconsistent widths.
_WHO_TITLE_WIDTH = 16
_WHO_ROOM_WIDTH = 18
_WHO_TITLE_WIDTH_WIDE = 42  # plain player table has no idle column, more room for titles
_WHO_RACE_WIDTH = 14
_WHO_CLASS_WIDTH = 14

# Rank-tier color, applied to rank_title()'s output on the who tables -
# a plain white "GOD" sitting next to a plain white "Novice" gave no
# visual sense of progression at a glance. Ascends from a dim, unassuming
# grey up through increasingly vivid colors, with GOD deliberately the
# only warm/red tone so it reads as unmistakably different from every
# earned mortal rank below it.
_RANK_COLORS = [
    (101, "|R"),  # GOD
    (100, "|Y"),  # Legend
    (90, "|y"),  # Grand Master
    (60, "|C"),  # Master
    (35, "|c"),  # Veteran
    (15, "|g"),  # Adept
    (1, "|x"),  # Novice
]


def _rank_color_code(level):
    """The color code for a given level's tier, per _RANK_COLORS above."""
    lvl = level if isinstance(level, int) else 1
    for threshold, code in _RANK_COLORS:
        if lvl >= threshold:
            return code
    return "|w"


def _colored_rank(level):
    """rank_title()'s text (e.g. 'Veteran', 'Rex Divum'), colored by tier."""
    return "%s%s|n" % (_rank_color_code(level), rank_title(level))


def _colored_level(level):
    """The raw numeric level (not the rank title), colored by tier -
    for the /full technical table, which shows the exact number rather
    than the rank label the other two tables use."""
    return "%s%s|n" % (_rank_color_code(level), level)


def _short_flavor_name(display_text):
    """
    The short 'core name' from a race/class display string like
    'Human (Roman Citizen)' or 'Augur (Light - Mage/Support)' - just
    the part before the parenthetical subtitle. A value with no
    parenthesis at all (e.g. a manually-set flavor value like "Olympian"
    or "Divine") passes through unchanged.

    This is the actual fix for a real bug reported live: cropping the
    FULL display string (as this code used to do) could truncate right
    at the open-paren, and utils.crop()'s default suffix is the
    literal string "[...]", not a single ellipsis character - so
    "Human (Roman Citizen)" cropped to width 12 rendered as the
    genuinely confusing "Human ([...]". Splitting off the subtitle
    first means there's essentially nothing left long enough to need
    truncating in normal use.
    """
    if not display_text:
        return "-"
    return display_text.split(" (", 1)[0]


class CmdWho(DefaultCmdWho):
    """
    list who is currently online

    Usage:
      who
      who/full

    Shows who is currently online - character, title, race, class,
    level, and location. Admins and Developers see this by default;
    add the /full switch for the complete technical table (account
    name, connect time, command count, protocol, host IP).
    """

    def func(self):
        account = self.account
        show_admin_data = account.check_permstring("Developer") or account.check_permstring(
            "Admins"
        )
        # Whoever is actually running this who command - wizinvis
        # (world/combat.py's wizinvis_hides_from) hides a wizinvis'd
        # god from anyone whose own level is lower, in every table
        # below including the admin ones - "Admins" the Evennia
        # permission and "gods" the in-game level system are two
        # separate things (see CLAUDE.md), so an Admin-permissioned
        # low-level character shouldn't see a high-tier wizinvis'd god
        # just because they can see the technical /full columns.
        viewer = self.session.get_puppet() if self.session else None

        session_list = evennia.SESSION_HANDLER.get_sessions()
        session_list = sorted(session_list, key=lambda o: o.account.key)

        if show_admin_data and "full" in self.switches:
            # Complete technical table. Account Name/Puppeting/Protocol/
            # Host stay fully uncropped - those are the genuinely
            # diagnostic fields this view exists for (tracing abuse by
            # host/IP). Title/Race/Class/Room are flavor, not diagnostic,
            # and were the actual cause of this table wrapping into an
            # unreadable mess - cropped the same as the lean table below.
            table = self.styled_table(
                "|YAccount Name",
                "|YOn for",
                "|YIdle",
                "|YPuppeting",
                "|YTitle",
                "|YRace",
                "|YClass",
                "|YLevel",
                "|YRoom",
                "|YCmds",
                "|YProtocol",
                "|YHost",
            )
            for session in session_list:
                if not session.logged_in:
                    continue

                delta_cmd = time.time() - session.cmd_last_visible
                delta_conn = time.time() - session.conn_time
                sess_account = session.get_account()
                puppet = session.get_puppet()
                if wizinvis_hides_from(puppet, viewer):
                    continue
                location = puppet.location.key if puppet and puppet.location else "None"

                title = puppet.db.custom_title if puppet else ""
                race = _short_flavor_name(puppet.db.race_display if puppet else None)
                pclass = _short_flavor_name(puppet.db.class_display if puppet else None)
                level = (puppet.db.level if puppet else None) or 1

                table.add_row(
                    sess_account.get_display_name(sess_account),
                    utils.time_format(delta_conn, 0),
                    utils.time_format(delta_cmd, 1),
                    puppet.key if puppet else "None",
                    "|Y%s|n" % utils.crop(title, width=_WHO_TITLE_WIDTH) if title else "-",
                    utils.crop(race, width=_WHO_RACE_WIDTH),
                    utils.crop(pclass, width=_WHO_CLASS_WIDTH),
                    _colored_level(level),
                    "|c%s|n" % utils.crop(location, width=_WHO_ROOM_WIDTH),
                    session.cmd_total,
                    session.protocol_key,
                    isinstance(session.address, tuple) and session.address[0] or session.address,
                )
            self.msg(str(table))
            naccounts = evennia.SESSION_HANDLER.account_count()
            self.msg("%d account%s logged in." % (naccounts, "" if naccounts == 1 else "s"))
            return

        if show_admin_data:
            # Lean default for admins - readable at normal client
            # widths. Every text column is cropped so long titles/room
            # names can't blow up the table into wrapping. Use
            # 'who/full' for every technical field.
            table = self.styled_table(
                "|YAccount",
                "|YChar",
                "|YTitle",
                "|YRace",
                "|YClass",
                "|YLvl",
                "|YRoom",
                "|YIdle",
            )
            for session in session_list:
                if not session.logged_in:
                    continue

                delta_cmd = time.time() - session.cmd_last_visible
                sess_account = session.get_account()
                puppet = session.get_puppet()
                if wizinvis_hides_from(puppet, viewer):
                    continue
                location = puppet.location.key if puppet and puppet.location else "None"

                title = puppet.db.custom_title if puppet else ""
                race = _short_flavor_name(puppet.db.race_display if puppet else None)
                pclass = _short_flavor_name(puppet.db.class_display if puppet else None)
                level = (puppet.db.level if puppet else None) or 1

                table.add_row(
                    utils.crop(sess_account.get_display_name(sess_account), width=10),
                    utils.crop(puppet.key if puppet else "None", width=10),
                    "|Y%s|n" % utils.crop(title, width=_WHO_TITLE_WIDTH) if title else "-",
                    utils.crop(race, width=_WHO_RACE_WIDTH),
                    utils.crop(pclass, width=_WHO_CLASS_WIDTH),
                    _colored_rank(level),
                    "|c%s|n" % utils.crop(location, width=_WHO_ROOM_WIDTH),
                    utils.time_format(delta_cmd, 1),
                )
            self.msg(str(table))
            naccounts = evennia.SESSION_HANDLER.account_count()
            self.msg("%d account%s logged in." % (naccounts, "" if naccounts == 1 else "s"))
            return

        # No idle column here - regular players don't need to see it
        # (that's an admin-oversight detail, not something a plain
        # who-list needs). The freed width goes to the title column
        # instead, since that's the field actually worth the room -
        # see _WHO_TITLE_WIDTH_WIDE above.
        table = self.styled_table(
            "|YName", "|YTitle", "|YRace", "|YClass", "|YLevel"
        )
        for session in session_list:
            if not session.logged_in:
                continue

            char = session.get_puppet()
            if wizinvis_hides_from(char, viewer):
                continue

            if char:
                name = char.key
                title = char.db.custom_title or ""
                race = _short_flavor_name(char.db.race_display)
                pclass = _short_flavor_name(char.db.class_display)
                level = char.db.level or 1
            else:
                # Account is online but not currently puppeting a character
                name = session.account.key
                title = ""
                race = "-"
                pclass = "-"
                level = "-"

            table.add_row(
                name,
                "|Y%s|n" % utils.crop(title, width=_WHO_TITLE_WIDTH_WIDE) if title else "-",
                utils.crop(race, width=_WHO_RACE_WIDTH),
                utils.crop(pclass, width=_WHO_CLASS_WIDTH),
                _colored_rank(level) if level != "-" else "-",
            )

        self.msg(str(table))
        naccounts = evennia.SESSION_HANDLER.account_count()
        self.msg("%d account%s logged in." % (naccounts, "" if naccounts == 1 else "s"))


class FriendlyCmdPage(DefaultCmdPage):
    """
    Send a private message to another connected player, by character name.

    Usage:
      page <character> <message>
      page <character>,<character>,... = <message>
      tell        ''
      page <number>   - show your last <number> pages
      page/last       - show who you last paged
      page/list       - show your message history

    Real bug fixed here: the contrib's own target search looks
    someone up by their ACCOUNT name (the one you log in with), not
    their CHARACTER name (the one shown everywhere else in the game -
    'who', combat, room descriptions). Since those two are almost
    never the same thing, paging someone by the name you actually see
    them by always failed the lookup - and silently fell back to
    re-sending your own last page to yourself instead of giving any
    error, which is exactly the "paged a name that doesn't exist and
    it went through anyway" bug this replaces. This version looks
    people up by character name among who's actually online instead,
    and says plainly when nobody by that name is connected.
    """

    def func(self):
        caller = self.caller  # an Account - account_caller=True, inherited

        args = self.args.strip() if self.args else ""

        # Nothing being sent right now - viewing history, /last, /list,
        # or a bare number - none of that needs character-name lookup
        # at all, so just defer to the contrib's own working logic.
        if not args or args.isnumeric() or "last" in self.switches or "list" in self.switches:
            super().func()
            return

        if self.rhs:
            names = self.lhslist
            message = self.rhs.strip()
        else:
            parts = args.split(" ", 1)
            if len(parts) < 2:
                caller.msg("Usage: page <character> <message>")
                return
            names, message = [parts[0]], parts[1].strip()

        if not message:
            caller.msg("Usage: page <character> <message>")
            return

        targets = []
        missing = []
        seen_ids = set()
        for name in names:
            name = name.strip()
            match = None
            for session in evennia.SESSION_HANDLER.get_sessions():
                puppet = session.get_puppet()
                if puppet and puppet.key.lower() == name.lower():
                    match = session.get_account()
                    break
            if match and match.id not in seen_ids:
                seen_ids.add(match.id)
                targets.append(match)
            elif not match:
                missing.append(name)

        if missing:
            caller.msg(
                "No one online is playing a character named '%s'." % "' or '".join(missing)
            )
        if not targets:
            return

        header = "|wAccount|n |c%s|n |wpages:|n" % caller.key
        if message.startswith(":"):
            message = "%s %s" % (caller.key, message.strip(":").strip())

        target_perms = " or ".join("id(%d)" % t.id for t in targets + [caller])
        create.create_message(
            caller,
            message,
            receivers=targets,
            locks=(
                "read:%s or perm(Admin);"
                "delete:id(%d) or perm(Admin);"
                "edit:id(%d) or perm(Admin)" % (target_perms, caller.id, caller.id)
            ),
            tags=[("page", "comms")],
        )

        received = []
        rstrings = []
        for target in targets:
            if not target.access(caller, "msg"):
                rstrings.append("You are not allowed to page %s." % target)
                continue
            target.msg("%s %s" % (header, message))
            if hasattr(target, "sessions") and not target.sessions.count():
                received.append("|C%s|n" % target.name)
                rstrings.append(
                    "%s is offline. They will see your message if they list "
                    "their pages later." % received[-1]
                )
            else:
                received.append("|c%s|n" % target.name)
        if rstrings:
            caller.msg("\n".join(rstrings))
        caller.msg("You paged %s with: '%s'." % (", ".join(received), message))


class CmdTitle(Command):
    """
    Set a custom title shown on the who list, your character sheet,
    and when someone looks at you.

    Usage:
      title            - show your current title
      title <text>     - set a new title
      title clear      - remove your title

    Your title appears next to your name on the who list, e.g.
    "Marcus - the Undefeated". Keep it short (40 characters or less).
    """

    key = "title"
    help_category = "general"

    def func(self):
        caller = self.caller
        args = self.args.strip() if self.args else ""

        if not args:
            # Bare 'title' shows the current one - this used to clear
            # it instead, which meant the single most natural thing to
            # type when you just wanted to check your title wiped it.
            current = caller.db.custom_title
            if current:
                caller.msg("Your title is: %s" % current)
            else:
                caller.msg("You don't have a title set. Use 'title <text>' to set one.")
            return

        if args.lower() == "clear":
            caller.db.custom_title = None
            caller.msg("Your title has been cleared.")
            return

        title = args
        if len(title) > 40:
            caller.msg("Titles must be 40 characters or less.")
            return

        caller.db.custom_title = title
        caller.msg("Your title is now: %s" % title)