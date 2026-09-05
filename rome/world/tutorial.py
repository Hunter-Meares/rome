"""
New-player orientation - two pieces, doing different jobs:

  - 'help newbie' (world/help_setup.py) is the full walkthrough, read
    once, covering the whole arc (cells -> Ludus -> sewers -> the
    rest of Rome -> Germania) with pointers to the real 'help X'
    topics for depth on each step, rather than re-explaining them.

  - CmdJourney ('journey', this module) is the thing that actually
    answers "ok, right now, what do I do" - a single, state-aware
    line rather than the whole topic again, since a lost player
    shouldn't have to re-read a full page and work out which part
    currently applies to them. Named 'journey' rather than something
    plainer like 'whatnow' per direct request - too OOC/casual for
    an otherwise in-character game - but 'whatnow' and 'next' stay on
    as real aliases: this command exists specifically for players who
    don't know what to do yet, so it needs to be guessable by
    instinct too, not just discoverable once you already know its
    name. Deliberately reads only state that already exists
    (db.level, db.colosseum_escaped, db.is_dead, is_in_combat) rather
    than adding new "have you visited X" tracking across every other
    system - a small, contained addition, not a sprawling one.

Deliberately does NOT mention faction or religion recruiter
locations - CLAUDE.md already documents that as a deliberate,
spoiler-flagged design choice (players are meant to stumble into
those, not be told where to look), and this shouldn't quietly walk
that back. It does mention, generically, that more exists to find -
a newcomer who's never heard the word "faction" in this game might
never think to check 'help factions' at all otherwise.
"""

from commands.command import Command

LUDUS_LEVEL_CEILING = 8
SEWERS_LEVEL_CEILING = 25
GERMANIA_LEVEL_CEILING = 45


class CmdJourney(Command):
    """
    Get a quick, personal suggestion for what to do next.

    Usage:
      journey

    Reads your own actual progress - level, whether you've escaped
    the cells yet, whether you're dead or mid-fight - and gives you
    one concrete next step, instead of a whole page you have to
    figure out yourself. See 'help newbie' for the full walkthrough
    this is shorthand for.
    """

    key = "journey"
    aliases = ["whatnow", "next"]
    help_category = "general"

    def func(self):
        caller = self.caller

        if caller.db.is_dead:
            caller.msg(
                "|wYou're dead.|n Solve the Underworld's riddle to find your own "
                "way back, or wait for a Medicus who can pull you back directly. "
                "See 'help fight' for what happens on death."
            )
            return

        from world.combat import COMBAT_RULES

        if COMBAT_RULES.is_in_combat(caller):
            caller.msg(
                "|wYou're in a fight right now.|n Focus on that - 'attack', use a "
                "spell or skill, or 'disengage' if it's going badly. See 'help fight'."
            )
            return

        from world.factions import GOD_LEVEL_THRESHOLD

        if (caller.db.level or 1) > GOD_LEVEL_THRESHOLD:
            # A real bug found live: the level check below only had an
            # upper bound (< GERMANIA_LEVEL_CEILING), so anyone past it
            # - including a level 101+ god, whose progression this
            # command was never meant to track at all - fell into the
            # "cleared everything" mortal end-game message. Gods don't
            # have a "journey" this command has any business
            # commenting on.
            caller.msg(
                "|wYou're a god now.|n Whatever 'next' means at your level isn't "
                "something this command has any business guessing at."
            )
            return

        if not caller.db.colosseum_escaped:
            caller.msg(
                "|wFirst things first - you need to actually get out of these "
                "cells.|n Fight your way out ('fight'), or take the quieter way "
                "('sneak', then 'solve' the riddle you find). See 'help newbie' "
                "for the full walkthrough."
            )
            return

        level = caller.db.level or 1

        if level < LUDUS_LEVEL_CEILING:
            caller.msg(
                "|wTrain at the Ludus.|n Start at the Weapons Yard - the Wrestling "
                "Pit, Beast Taming Ring, and Champions' Court open up as you "
                "level. Use 'trainer' once you're there to see what you can learn."
            )
            return

        if level < SEWERS_LEVEL_CEILING:
            caller.msg(
                "|wThe Ludus has taken you about as far as it can.|n Head into "
                "the Cloaca Maxima sewers next - grates from the Ludus, the "
                "Subura, or the Forum all lead down. Real depth, real danger, "
                "real levels."
            )
            return

        if level < GERMANIA_LEVEL_CEILING:
            caller.msg(
                "|wYou've got real options now.|n Check 'achievements', "
                "'bounty', and 'quest' if you haven't - and when you're ready "
                "for something bigger, the road north past Rome's new gate, "
                "the Porta Flaminia, leads to a real Germanic stronghold. "
                "Rome has more going on than fighting, too, if you go looking "
                "for it.\n"
                "'recall' gets you home from anywhere once you've had enough."
            )
            return

        caller.msg(
            "|wYou've cleared every zone built so far.|n Well done - that puts "
            "you among the strongest characters in Rome. Check 'achievements', "
            "'bounty', and 'quest' if any are still open, or just enjoy it."
        )
