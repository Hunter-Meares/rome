"""
Earned titles - a title a character receives automatically for a real
in-game accomplishment, as distinct from commands/social.py's `title`
command (db.custom_title): free-text, player-chosen, purely cosmetic.

Two other systems each considered bolting on their own one-off title
mechanic while being designed and both explicitly punted on it -
world/quests.py's reward and world/religion.py's Beloved tier both
flagged "build the real shared system once, hook everything into it"
rather than a third ad hoc mechanism. This is that system.

Design:
  - `db.earned_titles` is every title a character has ever earned -
    it never shrinks, even if the active one is cleared, so an old
    title can always be re-selected later.
  - `db.active_earned_title` is at most one of those, chosen for
    display. `grant_earned_title` auto-activates a newly-granted
    title ONLY if nothing is currently active, so a character's very
    first earned title shows up immediately without silently
    overriding a title they already chose to display.
  - An earned title and a custom title are not in competition -
    wherever there's room (stats, look) both show, clearly separate.
    `who`'s columns only have room for one: earned title wins there
    when active, custom title otherwise (see commands/social.py).
  - No retroactive granting - only an accomplishment reached AFTER
    this shipped grants a title. A deliberate, separate decision if
    ever wanted.
  - Only one active earned title at a time; no stacking multiple
    earned titles into a single display.

Source mapping - which specific accomplishment grants which title.
Kept here, not scattered into achievements/quests/religion, so this
one file is the whole answer to "what earns what":
"""

from evennia import Command

ACHIEVEMENT_TITLES = {
    "legend": "the Undefeated",
}

QUEST_TITLES = {
    "corrupt_official": "the Incorruptible",
}

# Only the top ("Beloved") tier grants a title - meant to be rare and
# earned, not handed out at the entry tier. Only the 4 gods with a
# real trigger (world/religion.py's RELIGION_TRIGGERS) have one; the
# other 10 are honestly thin until a trigger exists for them too.
RELIGION_BELOVED_TITLES = {
    "mars": "the War-Blessed",
    "mercury": "Mercury's Favored",
    "apollo": "the Radiant",
    "pluto": "the Deathless",
}


def grant_earned_title(character, title):
    """
    The one shared place every source (achievements, quests,
    religion) grants a title through. Adds it to the character's
    earned list if new, auto-activates it only if nothing is
    currently active, and announces the moment. A no-op if the
    character already has this exact title (so re-crossing a tier
    boundary, e.g. losing and regaining Beloved, doesn't re-announce
    it).
    """
    earned = character.db.earned_titles or []
    if title in earned:
        return

    earned.append(title)
    character.db.earned_titles = earned

    character.msg('|Y*** New title earned: "%s" ***|n' % title)

    if not character.db.active_earned_title:
        character.db.active_earned_title = title
        character.msg(
            "|xIt's now your active title. Type 'titles' to see everything "
            "you've earned, or 'titles clear' to go back to no earned "
            "title.|n"
        )


class CmdTitles(Command):
    """
    Manage your earned titles - accomplishments from achievements,
    quests, and religion that grant an automatic title, as distinct
    from the ordinary 'title' command's free-text custom title.

    Usage:
      titles
      titles set <title>
      titles clear

    Bare 'titles' lists everything you've earned and which one, if
    any, is currently active. 'titles set' switches your active
    title to any other one you've already earned. 'titles clear'
    goes back to showing no earned title - your custom title, if
    you have one, still shows.
    """

    key = "titles"
    help_category = "general"

    def func(self):
        caller = self.caller
        arg = self.args.strip()
        earned = caller.db.earned_titles or []

        if not arg:
            if not earned:
                caller.msg("You haven't earned any titles yet.")
                return
            active = caller.db.active_earned_title
            lines = ["|wYour Earned Titles|n"]
            for title in earned:
                marker = " |Y(active)|n" if title == active else ""
                lines.append("  %s%s" % (title, marker))
            caller.msg("\n".join(lines))
            return

        if arg.lower() == "clear":
            if not caller.db.active_earned_title:
                caller.msg("You have no active earned title.")
                return
            caller.db.active_earned_title = None
            caller.msg("Your earned title is no longer shown.")
            return

        if arg.lower().startswith("set"):
            name = arg[3:].strip()
            if not name:
                caller.msg("Usage: titles set <title>")
                return
            matches = [t for t in earned if t.lower() == name.lower()]
            if not matches:
                caller.msg("You haven't earned a title called '%s'." % name)
                return
            caller.db.active_earned_title = matches[0]
            caller.msg('Your active title is now "%s".' % matches[0])
            return

        caller.msg("Usage: titles [set <title>|clear]")
