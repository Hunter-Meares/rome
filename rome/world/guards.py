"""
Rome's city guards - crime-and-punishment phase 2, part 1. Real, gear-up
NPCs (CityGuard) that patrol Rome proper on a WanderingNPC-style beat
(GuardPatrolScript) and, on sight, gang up on any wanted/homo sacer
player they cross paths with (check_guard_capture). Never dispatched,
never chase beyond a beat, and confined to Rome proper only (they never
enter the Colosseum/Ludus complex or the sewers, even though
world.crime.is_crime_jurisdiction makes crimes committed there illegal
too - a wanted player who stays out there simply never runs into one
until they come back to the city).

A guard's blow against an eligible target never actually kills them -
world.combat.CombatRules.apply_damage clamps it to 1 HP and hands off to
capture() here instead, which pulls the target out of the fight and
imprisons them (world/jail.py). Everything else about the fight (guards
taking real damage, being genuinely killable and respawning like any
other RespawningNPC) is unchanged - only the ONE direction (guard -> a
wanted target) is ever clamped.
"""

from random import randint

from evennia.prototypes.spawner import spawn

from world.colosseum import SelfHealingRepeatScript
from world.combat import (
    COMBAT_RULES,
    CombatTurnHandler,
    RespawningNPC,
    spawn_leveled_armor,
    spawn_leveled_weapon,
)

# Keyed by level tier, not by name (unlike ARENA_FIGHTER_GEAR/
# AMBER_COAST_GEAR) - several differently-named guard prototypes share
# each tier for flavor variety, per direct request ("make a variety of
# guards"), rather than one gear table entry per unique name.
GUARD_GEAR = {
    25: ("GLADIUS", "SCALEMAIL", "PARMA"),
    50: ("SPEAR", "PLATEMAIL", "CLIPEUS"),
    75: ("BROADSWORD", "PLATEMAIL", "SCUTUM"),
}


def equip_city_guard(npc):
    """Gives a guard real, level-scaled gear for its tier - identical
    mechanism to equip_arena_fighter/equip_amber_coast_npc, just keyed by
    db.level instead of npc.key."""
    gear = GUARD_GEAR.get(npc.db.level)
    if not gear:
        return

    weapon_proto, armor_proto, shield_proto = gear
    level = npc.db.level

    npc.db.wielded_weapon = spawn_leveled_weapon(weapon_proto, level, location=npc)
    npc.db.worn_armor = spawn_leveled_armor(armor_proto, level, location=npc)
    if shield_proto:
        shield = spawn(shield_proto)[0]
        shield.move_to(npc, quiet=True)
        npc.db.worn_shield = shield


class CityGuard(RespawningNPC):
    """
    A Rome city guard. Built on RespawningNPC (not plain HostileNPC)
    because a wanted player fighting back CAN genuinely kill one - this
    is real combat, not a scripted arrest - so a guard needs to come
    back like any other standing encounter, not sit dead forever.
    db.is_city_guard is the marker check_guard_capture and apply_damage's
    capture clamp both key off - set here rather than as a prototype tag
    since RespawningNPC's own super() call already runs derive_npc_stats
    off db.level first, which equip_city_guard below needs.
    """

    def at_object_post_creation(self):
        super().at_object_post_creation()
        self.db.is_city_guard = True
        equip_city_guard(self)


class GuardPatrolScript(SelfHealingRepeatScript):
    """
    Same shape as world.colosseum.WanderingNPC (patrols within
    db.wander_rooms, set to every Rome-proper room at setup time) - plus
    a capture check the moment the guard arrives somewhere new. The
    other direction (a wanted player walking into a room a guard is
    already standing in) is covered separately, from
    world.combat.CombatCharacter.at_post_move.
    """

    def at_script_creation(self):
        self.key = "guard_patrol"
        self.interval = 90
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        guard = self.obj
        if not guard or not guard.pk:
            self.stop()
            return
        if COMBAT_RULES.is_in_combat(guard):
            return  # mid-fight - the turn handler owns this guard's turn, not this script

        wander_rooms = guard.db.wander_rooms
        current = guard.location
        if not wander_rooms or not current:
            return
        held = guard.db.conditions or {}
        if "Asleep" in held or "Stunned" in held or "Confused" in held:
            return

        valid_exits = [ex for ex in current.exits if ex.destination in wander_rooms]
        if valid_exits:
            chosen_exit = valid_exits[randint(0, len(valid_exits) - 1)]
            guard.move_to(chosen_exit.destination, quiet=False, move_type="wander")

        check_guard_capture(guard.location)


def check_guard_capture(room):
    """
    Checks `room` for a live, unengaged guard AND an eligible wanted/
    homo-sacer target, and starts a fight if both are present and no
    fight is already running here. Called from both directions: a guard
    wandering into a room (GuardPatrolScript.at_repeat, above) and a
    wanted player walking into one (world.combat.CombatCharacter.
    at_post_move). Guards never chase - this only ever fires on actually
    crossing paths, matching the "always on patrol, encountering them is
    a coincidence" design.

    Every guard present joins as ONE shared side against the target,
    reusing 'fight all's own mob-grouping (CombatTurnHandler.
    at_script_creation) - the first guard opens the fight via the normal
    pending_fighters path, and any others present join it explicitly on
    that same side, rather than each getting their own independent side
    the way an ordinary partyless-NPC join would.
    """
    if not room or room.db.combat_turnhandler:
        return

    guard_list = [
        obj for obj in room.contents
        if obj.db.is_city_guard and obj.db.hp and not COMBAT_RULES.is_in_combat(obj)
    ]
    if not guard_list:
        return

    targets = [
        obj for obj in room.contents
        if getattr(obj, "account", None)
        and (obj.db.wanted or obj.db.homo_sacer)
        and not obj.db.imprisoned
        and obj.db.hp
        and not COMBAT_RULES.is_in_combat(obj)
    ]
    if not targets:
        return
    target = targets[0]

    room.msg_contents(
        "|rThe city watch spots %s - \"Seize the criminal!\"|n" % target.key
    )
    room.ndb.pending_fighters = [guard_list[0], target]
    room.scripts.add(CombatTurnHandler)

    turnhandler = room.db.combat_turnhandler
    if turnhandler:
        guard_side = guard_list[0].db.combat_side
        for extra_guard in guard_list[1:]:
            turnhandler.join_fight(extra_guard, side=guard_side)


def capture(defender):
    """
    Pulls `defender` out of combat (force_disengage - unconditional, no
    roll, matching CmdGodTeleport's own use of it) and hands off to
    world.jail.imprison(). Called from world.combat.CombatRules.
    apply_damage the moment a guard's blow against a wanted/homo-sacer
    target would otherwise be lethal - that clamp guards against calling
    this more than once (checks db.imprisoned first), so this itself
    doesn't need to be idempotent on its own.
    """
    room = defender.location
    COMBAT_RULES.force_disengage(defender)
    if room:
        room.msg_contents(
            "|rThe guards seize %s, beaten down and helpless!|n" % defender.key
        )

    from world import jail
    jail.imprison(defender)
