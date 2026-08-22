"""
Colosseum mechanics

Supports the new-player onboarding questline: captives begin in the
holding cells beneath the Colosseum and must either fight their way
free (defeating the Arena Trainer in Arena Sands - see world/combat.py's
at_defeat for the escape-on-victory logic) or sneak out through the
cisterns and tunnels (this module's CmdSneak and CmdSolve).

Also includes CmdRecall, a general-purpose "return to the city hub"
command usable from anywhere once a player is free.
"""

from random import randint

from evennia.scripts.scripts import DefaultScript
from evennia.utils.search import search_tag

from commands.command import Command
from evennia.objects.objects import DefaultExit

#########################################################
#           Gated exit - combat escape path
#########################################################


class GateOfLifeExit(DefaultExit):
    """
    Blocks passage until the traverser has actually earned their
    freedom (by defeating the Arena Trainer). Without this, the combat
    escape path is just a normal walkable corridor with nothing
    actually gating it - the fight would be entirely optional.
    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        if not traversing_object.db.colosseum_escaped:
            traversing_object.msg(
                "|rYou haven't earned your freedom yet - you'll need to defeat "
                "the trainer first.|n"
            )
            return
        super().at_traverse(traversing_object, target_location, **kwargs)


class DeeperSandsGateExit(DefaultExit):
    """
    Blocks characters below level 6 from the deeper Arena Sands - real
    leveled opponents up to 25, not the newbie-safe escape questline.
    Forces brand-new players through the Ludus/beginner section first
    rather than letting a level 1 character wander straight into
    something that could kill them in two rounds.
    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        level = traversing_object.db.level or 1
        if level < 6:
            traversing_object.msg(
                "|rYou aren't experienced enough to enter this part of the "
                "arena yet. Prove yourself in the Ludus first - come back "
                "once you've reached level 6.|n"
            )
            return
        super().at_traverse(traversing_object, target_location, **kwargs)

#########################################################
#              Ambient room-echo script
#########################################################


class ColosseumEcho(DefaultScript):
    """
    Attach to a room to have it periodically announce an ambient sound
    to everyone inside - crowd noise, clanging metal, distant screams,
    etc. Configure by setting `obj.db.echo_messages` to a list of
    strings before/after adding this script to the room.
    """

    def at_script_creation(self):
        self.key = "colosseum_echo"
        self.interval = 45
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        messages = self.obj.db.echo_messages
        if not messages:
            return
        self.obj.msg_contents(messages[randint(0, len(messages) - 1)])


class WanderingNPC(DefaultScript):
    """
    Attach to an NPC to have it periodically wander between a defined
    set of rooms - its "beat" - rather than roaming the whole game or
    leaving the Colosseum entirely. Configure by setting
    obj.db.wander_rooms to a list of room objects before adding this
    script.

    Each tick, picks a random exit from the NPC's current room that
    actually leads to one of the allowed wander_rooms, and moves
    there. If no such exit exists from the current room (a dead end
    relative to the beat), it just stays put until the next tick -
    deliberately doesn't teleport, so the NPC's movement always
    follows real, walkable paths a player could also see it take.
    """

    def at_script_creation(self):
        self.key = "wandering_npc"
        self.interval = 90
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        npc = self.obj
        if not npc or not npc.pk:
            self.stop()
            return

        wander_rooms = npc.db.wander_rooms
        current = npc.location
        if not wander_rooms or not current:
            return

        valid_exits = [
            ex for ex in current.exits if ex.destination in wander_rooms
        ]
        if not valid_exits:
            return

        chosen_exit = valid_exits[randint(0, len(valid_exits) - 1)]
        npc.move_to(chosen_exit.destination, quiet=False, move_type="wander")


#########################################################
#                  Stealth escape path
#########################################################


class CmdSneak(Command):
    """
    Attempt to sneak past the guard.

    Usage:
      sneak

    Only usable in the Guard Checkpoint, beneath the Colosseum. Success
    is random - if you're spotted, you can simply try again.
    """

    key = "sneak"
    help_category = "colosseum"

    def func(self):
        caller = self.caller

        if not caller.location or caller.location.key != "Guard Checkpoint":
            caller.msg("There's nothing to sneak past here.")
            return

        roll = randint(1, 100)
        if roll > 40:  # 60% chance of success
            caller.msg(
                "|cYou hold your breath and slip past the dozing guard, unseen.|n"
            )
            dest = search_tag("colosseum_maintenance_tunnel", category="colosseum")
            if dest:
                caller.move_to(dest[0], quiet=True)
        else:
            caller.msg(
                "|rThe guard stirs - you freeze, heart pounding, but he settles "
                "back down. You can try again.|n"
            )


class CmdSolve(Command):
    """
    Answer the riddle inscribed on the door.

    Usage:
      solve <answer>

    Only usable in the Riddle Door Chamber, beneath the Colosseum.
    """

    key = "solve"
    help_category = "colosseum"

    # Accepted answers, all lowercase.
    _ACCEPTED_ANSWERS = {"shadow", "a shadow", "your shadow", "my shadow"}

    def func(self):
        caller = self.caller

        if not caller.location or caller.location.key != "Riddle Door Chamber":
            caller.msg("There's nothing to solve here.")
            return

        if not self.args:
            caller.msg("Usage: solve <answer>")
            return

        answer = self.args.strip().lower()

        if answer in self._ACCEPTED_ANSWERS:
            caller.msg(
                "|yThe inscription flares with pale light and the door grinds open "
                "before you.|n"
            )
            caller.db.colosseum_escaped = True
            dest = search_tag("colosseum_hidden_stairwell", category="colosseum")
            if dest:
                caller.move_to(dest[0], quiet=True)
        else:
            caller.msg("|rThe inscription remains dark and silent. That is not the answer.|n")


#########################################################
#                       Recall
#########################################################


class CmdRecall(Command):
    """
    Return to the Colosseum Atrium - the heart of the city.

    Usage:
      recall

    Can't be used while in combat.
    """

    key = "recall"
    help_category = "general"

    def func(self):
        caller = self.caller

        from world.combat import COMBAT_RULES

        if COMBAT_RULES.is_in_combat(caller):
            caller.msg("You can't recall while in combat!")
            return

        dest = search_tag("colosseum_recall_point", category="colosseum")
        if not dest:
            caller.msg("Recall isn't available right now.")
            return

        caller.msg(
            "|cYou close your eyes. The roar of a distant crowd rises around you, "
            "and the world shifts.|n"
        )
        caller.move_to(dest[0], quiet=True)


#########################################################
#                       Cmdset
#########################################################

from evennia import CmdSet


class ColosseumCmdSet(CmdSet):
    """Commands supporting the Colosseum questline and city recall."""

    key = "Colosseum CmdSet"

    def at_cmdset_creation(self):
        self.add(CmdSneak())
        self.add(CmdSolve())
        self.add(CmdRecall())