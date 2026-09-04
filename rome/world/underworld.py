"""
The Underworld

Where level 6+ characters go when they're defeated in combat. Getting
here is handled entirely by CombatRules.handle_player_defeat() in
world/combat.py - this module only covers what happens once you're
actually there: the riddle-based way back.

A Medicus with the (not-yet-built) Blessing of Asclepius spell will be
the other way back, once that's implemented - it'll just call
COMBAT_RULES.resurrect() directly, same as the riddle-solve below does.
"""

from evennia import default_cmds, DefaultExit
from evennia.scripts.scripts import DefaultScript
from evennia.utils.search import search_tag

from commands.command import Command
from world.combat import COMBAT_RULES, NO_COMBAT_ZONE_TAG, UNDERWORLD_ZONE_TAG


def tag_underworld_as_no_combat_zone():
    """
    Tags every room reachable from the Underworld entrance (a plain
    exit-following BFS, same technique world/worldcheck.py uses for
    reachability) as a no-combat zone - see NO_COMBAT_ZONE_TAG in
    world/combat.py. The afterlife shouldn't be a place fights can be
    started, PvP or otherwise; this reaches every room in the zone
    without needing to hand-list them, so re-running it after any
    future Underworld expansion picks up the new rooms automatically.

    Also applies UNDERWORLD_ZONE_TAG in the same pass - a separate,
    narrower tag ("this room is part of the Underworld," not just
    "no fights here") that CmdRecall uses to refuse recalling out of
    the afterlife. Same walk, no extra traversal cost.

    Idempotent - tags.add() on an already-tagged room is a no-op, so
    safe to run again any time. Run once, in-game, as Developer/
    superuser:

        py from world.underworld import tag_underworld_as_no_combat_zone as t; t()
    """
    entrances = search_tag("underworld_entrance", category="underworld")
    if not entrances:
        return 0

    key, category = NO_COMBAT_ZONE_TAG
    underworld_key, underworld_category = UNDERWORLD_ZONE_TAG
    visited = set()
    queue = [entrances[0]]
    while queue:
        room = queue.pop()
        if not room or not room.pk or room.pk in visited:
            continue
        visited.add(room.pk)
        room.tags.add(key, category=category)
        room.tags.add(underworld_key, category=underworld_category)
        for ex in room.exits:
            dest = ex.destination
            if dest and dest.pk and dest.pk not in visited:
                queue.append(dest)

    return len(visited)


class CharonTimer(DefaultScript):
    """
    A one-shot timer attached directly to a dead character, firing once
    ~15 minutes after death to bring Charon's arrival. This is a real
    Script rather than a plain utils.delay() call specifically because
    Scripts are properly database-backed and survive server reloads by
    default - no special handling needed. A delay() tied to a lambda
    closure over a bound method on a plain (non-database) object like
    COMBAT_RULES would likely fail to survive a reload at all, since
    there'd be nothing straightforward for Evennia to serialize.
    """

    def at_script_creation(self):
        self.key = "charon_timer"
        self.interval = 900  # 15 minutes
        self.repeats = 1
        self.persistent = True
        self.start_delay = True  # don't fire the instant it's created

    def at_repeat(self):
        character = self.obj
        if not character or not character.pk or not character.db.is_dead:
            self.stop()
            return

        character.db.charon_arrived = True
        carried_across = False
        if character.location:
            character.location.msg_contents(
                "|mOut of the mist, a black boat emerges, poled in silence by a "
                "hooded figure. Charon has come.|n"
            )

            # Automatically carries the character across, rather than
            # requiring them to separately type the exit's name
            # afterward - the crossing message below narrates them
            # already boarding and sailing, so a manual second step
            # would directly contradict what's being described. Finds
            # the real CharonFerryExit object in the room instead of
            # searching by room name/tag, so this stays correct even
            # if the exit or destination room is ever renamed.
            ferry_exit = next(
                (e for e in character.location.exits if isinstance(e, CharonFerryExit)),
                None,
            )
            if ferry_exit and ferry_exit.destination:
                character.msg(
                    "|mThe boat is waiting when you step to the water's edge - low, "
                    "black, and utterly silent. Charon does not speak, does not "
                    "gesture, only tilts his head a fraction toward the deck. You "
                    "step aboard. The pole finds the riverbed without a sound, and "
                    "the black water begins to slide past, current and boat moving "
                    "as one, carrying you toward a shore you cannot yet see and "
                    "will not be able to leave once you reach it.|n"
                )
                # force_move: a dead character's hp deliberately stays
                # at 0 the whole time they're dead (see
                # CombatRules.handle_player_defeat - "stats stay at 0
                # ... until they actually make it back"), and
                # CombatCharacter.at_pre_move unconditionally blocks
                # ANY move while hp<=0 unless this is passed. Without
                # it, this move silently fails right after the
                # narration above claims it already happened.
                carried_across = character.move_to(
                    ferry_exit.destination, quiet=False, force_move=True, move_type="teleport"
                )

        # Only shown as a fallback (no ferry exit found in the room,
        # or the forced move somehow failed) - saying this AFTER a
        # successful auto-carry would contradict the narration above,
        # which already describes the crossing as done.
        if not carried_across:
            character.msg("|yYou may now continue |wonward|y to cross the river.|n")
        self.stop()


class CharonFerryExit(DefaultExit):
    """
    The crossing onward from Shores of the Styx - blocked until Charon
    actually arrives with his boat, roughly 15 minutes after death (see
    CharonTimer above, which handles the wait and flips
    db.charon_arrived when it fires). Without this, the wait would be
    purely cosmetic - a dead character could just walk onward instantly
    regardless of whether the ferryman had shown up at all.

    In the common case, CharonTimer's own at_repeat already carries a
    present character across automatically the moment Charon arrives -
    this exit's own traverse path is the fallback for anyone who
    wasn't there for that (logged off, arrived at this room late,
    etc.) and manually crosses afterward.
    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        if not traversing_object.db.charon_arrived:
            traversing_object.msg(
                "|mThere is no boat yet - only the black water, and the patient "
                "shapes of others who arrived before you. You'll have to wait for "
                "the ferryman.|n"
            )
            return
        traversing_object.msg(
            "|mThe boat is waiting when you step to the water's edge - low, black, "
            "and utterly silent. Charon does not speak, does not gesture, only "
            "tilts his head a fraction toward the deck. You step aboard. The pole "
            "finds the riverbed without a sound, and the black water begins to "
            "slide past, current and boat moving as one, carrying you toward a "
            "shore you cannot yet see and will not be able to leave once you "
            "reach it.|n"
        )
        super().at_traverse(traversing_object, target_location, **kwargs)


class CmdAnswerRiddle(Command):
    """
    Answer the riddle at the Threshold of Return.

    Usage:
      answer <your answer>

    Only works in the Threshold of Return, and only if you're actually
    dead. Answer correctly and you're returned to the world of the
    living - answer wrong and nothing happens except a little more
    time spent among the dead.
    """

    key = "answer"
    help_category = "underworld"

    def func(self):
        caller = self.caller

        if caller.location.key != "Threshold of Return":
            caller.msg("There's no riddle to answer here.")
            return

        if not caller.db.is_dead:
            caller.msg("You have nothing to answer for - you're already among the living.")
            return

        if not self.args:
            caller.msg("Answer what? Usage: answer <your answer>")
            return

        answer = self.args.strip().lower()
        if answer in ("man", "a man", "human", "a human", "mankind", "humankind", "people"):
            caller.location.msg_contents(
                "%s speaks the answer, and the shade at the threshold steps aside." % caller
            )
            COMBAT_RULES.resurrect(caller)
        else:
            caller.msg(
                "The shade at the threshold says nothing. Your answer was wrong - "
                "the riddle remains."
            )


class UnderworldCmdSet(default_cmds.CharacterCmdSet):
    key = "UnderworldCmdSet"

    def at_cmdset_creation(self):
        self.add(CmdAnswerRiddle())
