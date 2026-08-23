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


class LevelGateExit(DefaultExit):
    """
    Generic level-gated exit - blocks traversal below a minimum level,
    set per-exit via `db.min_level` (and an optional `db.gate_flavor`
    naming what's beyond, used in the refusal message so the same
    class reads correctly at every gate instead of a generic one).

    A sibling to DeeperSandsGateExit above, deliberately left as its
    own separate class rather than refactored onto this one - it's
    already live and deployed, and there's no value in the risk of
    touching working, deployed content just to deduplicate ~10 lines.
    This class is for new gates instead - currently the Ludus's own
    internal tiers (Wrestling Pit, Beast Taming Ring, Champions'
    Court), which needed three different thresholds and didn't
    justify three new one-off classes.
    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        min_level = self.db.min_level or 1
        level = traversing_object.db.level or 1
        if level < min_level:
            flavor = self.db.gate_flavor or "this part of the Ludus"
            traversing_object.msg(
                "|rYou aren't experienced enough for %s yet. Come back "
                "once you've reached level %d.|n" % (flavor, min_level)
            )
            return
        super().at_traverse(traversing_object, target_location, **kwargs)

#########################################################
#         Self-healing repeating-script mixin
#########################################################


class SelfHealingRepeatScript(DefaultScript):
    """
    Shared base for every periodic-tick script below (ambient echoes,
    NPC chatter, wandering NPCs) - fixes a real, confirmed bug in how
    these get created.

    All of this project's world-building NPCs/rooms are set up via
    piped `evennia shell` scripts, not live in-game commands. That
    matters here specifically: `scripts.add()` does start the script's
    repeat timer immediately, but `evennia shell` is a separate,
    short-lived process from the actual running game server - it exits
    within moments of finishing, taking that in-memory timer with it,
    before the script has ever gone through one real pause/resume
    cycle inside the live server.

    Evennia normally restarts a persistent script's timer after every
    server reload via an *unpause* (`_unpause_task`, internally) - but
    unpausing only resumes a task that recorded a genuine pause state
    (`db._paused_time` etc.) at the moment it was interrupted. A script
    whose timer only ever existed in a throwaway shell process never
    got the chance to record that pause state, so Evennia's own
    reload-time unpause silently does nothing for it, forever - the
    script sits at `db_is_active=True` in the database, looking
    perfectly healthy, while never actually ticking again.

    Confirmed live via a temporary diagnostic: every single NPCChatter
    script in the game (34/34, all built via `evennia shell`) had
    literally never fired since creation, and roughly half of
    WanderingNPC/ColosseumEcho's instances were in the same state -
    the other half had, at some point, been touched by a real live
    server interaction that gave them a genuine pause cycle to resume
    from, which is why some worked and others silently didn't.

    `at_server_start()` is the fix: unlike the unpause step, Evennia
    calls this hook, inside the real live process, for every active
    script on every single reload - regardless of whether the unpause
    above actually did anything. Checking here whether a real task is
    running and force-starting one if not is exactly the self-healing
    check needed, and it's cheap and idempotent for scripts that are
    already ticking correctly.
    """

    def at_server_start(self):
        super().at_server_start()
        if self.db_is_active and not self.ndb._task:
            self.start(force_restart=True)


#########################################################
#              Ambient room-echo script
#########################################################


class ColosseumEcho(SelfHealingRepeatScript):
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


class NPCChatter(SelfHealingRepeatScript):
    """
    Attach directly to an NPC (not a room) to have it periodically say
    one of a set of lines out loud to whoever's in the room with it -
    a merchant's sales pitch, a beggar's plea, a senator's complaint.
    Configure by setting `obj.db.chatter_lines` (a list of plain
    strings, no quote marks or "X says" wrapper needed - both are
    added automatically) before/after adding this script to the NPC.

    Deliberately a general-purpose sibling to ColosseumEcho above,
    not Colosseum-specific despite the module - matches the existing
    precedent of WanderingNPC also living here despite being reused
    well beyond the Colosseum itself (the Forum's wandering NPCs use
    it too).

    Routed through each listener's own process_language hook (same
    listener-side mechanism player speech uses - see
    CombatCharacter.process_language in world/combat.py), rather than
    a blind msg_contents - Rome's NPCs speak Latin, the city's own
    lingua franca (`obj.db.chatter_language` overrides this per-NPC if
    a specific NPC should ever speak something else), so a listener
    who genuinely doesn't know Latin hears it scrambled exactly like
    they would from a player.

    Set `obj.db.tells_rumors = True` to also let this NPC occasionally
    report a real, recent player achievement instead of its own
    scripted lines (see world/rumors.py) - opt-in per NPC rather than
    universal, since not every NPC's flavor fits gossiping (a herald
    announcing news makes sense; the Flamen Dialis, bound by ritual
    silence around most things, doesn't). `obj.db.rumor_chance`
    (default 30) controls how often, out of 100, a tick prefers a
    rumor over the NPC's own lines when one is available.
    """

    def at_script_creation(self):
        self.key = "npc_chatter"
        self.interval = 60
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        npc = self.obj
        if not npc or not npc.pk or not npc.location:
            return

        line = None
        if npc.db.tells_rumors and randint(1, 100) <= (npc.db.rumor_chance or 30):
            from world.rumors import get_random_rumor_line

            line = get_random_rumor_line()

        if not line:
            lines = npc.db.chatter_lines
            if not lines:
                return
            line = lines[randint(0, len(lines) - 1)]

        quoted = '"%s"' % line
        language = npc.db.chatter_language or "latin"

        for receiver in npc.location.contents:
            if receiver is npc:
                continue
            if hasattr(receiver, "process_language") and callable(receiver.process_language):
                heard = receiver.process_language(quoted, npc, language)
            else:
                heard = quoted
            receiver.msg("%s says, %s" % (npc, heard))


class WanderingNPC(SelfHealingRepeatScript):
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