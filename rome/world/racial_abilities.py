"""
Racial abilities

Every race in world/chargen_menu.py's RACES dict lists 1-3 "signature
abilities" in its own flavor text (e.g. Nymph's "Boon of the Wilds -
heal allies") - but until now those were pure flavor, stored on the
character (db.race_abilities) with no actual command, mechanic, or
even a way to check them. A real player asked directly in-character
how to use their own race's listed abilities and there was genuinely
no answer - this module is that answer.

Deliberately built as its OWN small system rather than folded into
SPELLS/SKILLS: a racial ability is innate (granted at chargen, not
learned from a trainer for gold) and shouldn't be gated by a
spellcasting resource a given race/class combo might have very little
of (Cyclops's own stat_mods give it -10 max_mp, for instance) - so
these cost no MP or SP at all, just a flat cooldown, reusing the exact
same get_cooldowns/tick_cooldowns machinery SPELLS/SKILLS already use
(confirmed already wired for both in-combat and out-of-combat ticking
on a real player - see CombatCharacter.at_turn_start/at_update in
world/combat.py).

Scope, by direct design decision: only the abilities that map onto a
mechanic this game already has (a heal, a buff/debuff condition, a
bonus-damage attack) are built here. Human's Command Presence/Civic
Access (no politics/reputation system), Minotaur's Labyrinth Sense,
Centaur's Forest Tracker, Harpy's Skyward Scout (no lost/hidden-foe
mechanic), and Cyclops's Forge Mastery (crafting isn't built yet
either) are deliberately left undone rather than forced into a weak
mapping - see rome_mud_todo.md, and the precedent world/religion.py
already set doing the same thing for 10 of the pantheon's 14 gods.
"""

from random import randint

from evennia import CmdSet

from commands.command import Command
from world.combat import COMBAT_RULES, ACCURACY_STAT_MULTIPLIER, find_combat_target


def racial_heal(user, ability_name, targets, **kwargs):
    """Heals target(s) - the racial equivalent of spell_healing, minus
    any MP cost (an innate ability, not a cast spell). Still scales
    with Ingenium, same as a real healing spell would."""
    min_healing, max_healing = kwargs.get("healing_range", (15, 25))
    ingenium_bonus = ((user.db.ingenium or 10) - 10) // 2

    msg = "%s calls on %s!" % (user, ability_name.title())
    old_hp_by_target = {}
    for character in targets:
        old_hp_by_target[character] = character.db.hp or 0
        to_heal = randint(min_healing, max_healing) + ingenium_bonus
        if character.db.hp + to_heal > character.db.max_hp:
            to_heal = character.db.max_hp - character.db.hp
        character.db.hp += to_heal
        msg += " %s regains %i HP!" % (character, to_heal)

    user.location.msg_contents(msg)
    for character in targets:
        COMBAT_RULES.announce_hp_threshold_change(character, old_hp_by_target[character])
    if COMBAT_RULES.is_in_combat(user):
        COMBAT_RULES.spend_action(user, 1, action_name="racial")


def racial_add_condition(user, ability_name, targets, **kwargs):
    """Grants condition(s) to target(s) - the racial equivalent of
    spell_add_condition/skill_add_condition, minus any resource cost."""
    conditions = kwargs.get("conditions", [])
    msg = "%s calls on %s!" % (user, ability_name.title())
    user.location.msg_contents(msg)
    for target in targets:
        for condition in conditions:
            COMBAT_RULES.add_condition(target, user, condition[0], condition[1])
    if COMBAT_RULES.is_in_combat(user):
        COMBAT_RULES.spend_action(user, 1, action_name="racial")


def racial_attack(user, ability_name, targets, **kwargs):
    """
    Deals damage - the racial equivalent of skill_attack, minus any SP
    cost. Uses Agilitas, not Ingenium - every offensive racial ability
    built so far (Galloping Charge, Aerial Assault, Crushing Blow) is a
    physical trait, not a magical one, matching the same stat basic
    attack/skill_attack already use.
    """
    min_damage, max_damage = kwargs.get("damage_range", (15, 25))
    accuracy = kwargs.get("accuracy", 0)
    agilitas_accuracy = ((user.db.agilitas or 10) - 10) * ACCURACY_STAT_MULTIPLIER
    agilitas_bonus = ((user.db.agilitas or 10) - 10) // 2

    msg = "%s calls on %s!" % (user, ability_name.title())
    for target in targets:
        attack_value = randint(1, 100) + accuracy + agilitas_accuracy
        defense_value = COMBAT_RULES.get_defense(user, target)
        if attack_value < defense_value:
            msg += " It misses %s!" % target
            continue
        damage = randint(min_damage, max_damage) + agilitas_bonus
        COMBAT_RULES.apply_damage(target, damage, attacker=user, announce_threshold=False)
        msg += " %s takes |r%i|n damage - %s %s!" % (
            target, damage, target, COMBAT_RULES.hp_status_phrase(target)
        )

    user.location.msg_contents(msg)
    if COMBAT_RULES.is_in_combat(user):
        COMBAT_RULES.spend_action(user, 1, action_name="racial")


# Cooldowns are deliberately higher than a same-tier spell/skill would
# get from cooldown_for_level (world/combat.py) - a low-level spell
# relies on its MP/SP cost alone as the real gate (cooldown_for_level
# returns 0 below level_required 20), but a racial ability has no
# resource cost at all, so its cooldown has to do that whole job by
# itself or it's just a free, spammable extra action every turn.
RACIAL_ABILITIES = {
    "boon of the wilds": {
        "race": "nymph",
        "target": "anychar",
        "cooldown": 8,
        "abilityfunc": racial_heal,
        "healing_range": (15, 25),
        "desc": "Heals a single ally a modest amount - the healing "
        "touch of Nymph's fading wild blood.",
    },
    "elemental ward": {
        "race": "nymph",
        "target": "self",
        "cooldown": 8,
        "abilityfunc": racial_add_condition,
        "conditions": [("Defense Up", 4)],
        "desc": "Wards yourself against harm for a short time.",
    },
    "galloping charge": {
        "race": "centaur",
        "target": "otherchar",
        "cooldown": 6,
        "abilityfunc": racial_attack,
        "damage_range": (20, 30),
        "desc": "A powerful charging strike, Centaur's equine speed "
        "behind every hoof-fall.",
    },
    "aerial assault": {
        "race": "harpy",
        "target": "otherchar",
        "cooldown": 6,
        "abilityfunc": racial_attack,
        "damage_range": (15, 25),
        "accuracy": 20,
        "desc": "A diving strike from above - Harpy's aerial edge "
        "makes it hard to see coming.",
    },
    "crushing blow": {
        "race": "cyclops",
        "target": "otherchar",
        "cooldown": 8,
        "abilityfunc": racial_attack,
        "damage_range": (30, 45),
        "desc": "A single, titanic strike - the full weight of "
        "Cyclops's strength behind it.",
    },
    "intimidating presence": {
        "race": "cyclops",
        "target": "otherchar",
        "cooldown": 8,
        "abilityfunc": racial_add_condition,
        "conditions": [("Accuracy Down", 3), ("Defense Down", 3)],
        "desc": "A fearsome glare that rattles a target's composure, "
        "throwing off their aim and their guard alike.",
    },
    "bull rush": {
        "race": "minotaur",
        "target": "otherchar",
        "cooldown": 8,
        "abilityfunc": racial_add_condition,
        "conditions": [("Paralyzed", 1)],
        "desc": "A bone-jarring charge that leaves the target reeling "
        "for a moment - Minotaur's raw, labyrinth-born strength.",
    },
}


def racial_abilities_known(character):
    """Every RACIAL_ABILITIES key this character's own race actually
    grants - built this way (checked against RACIAL_ABILITIES itself)
    rather than by parsing character.db.race_abilities' flavor-text
    strings, so it can never drift out of sync with what's actually
    implemented here."""
    race = character.db.race
    return sorted(name for name, data in RACIAL_ABILITIES.items() if data["race"] == race)


class CmdRacial(Command):
    """
    Use an innate ability granted by your race.

    Usage:
      racial <ability> [= target]

    Every race has one or two of these from birth - see 'racialinfo'
    for exactly which ones yours grants, their cooldown, and what they
    do. Unlike spells and skills, these cost no MP or SP and never
    need to be learned from a trainer - only a cooldown limits how
    often you can call on one.
    """

    key = "racial"
    aliases = ["race"]
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        caller = self.caller

        if caller.db.is_dead:
            caller.msg("The dead have no call on their old blood.")
            return
        if "Silenced" in (caller.db.conditions or {}):
            caller.msg("A curse chokes off your voice - you can't call on it right now.")
            return
        if caller.db.resting:
            caller.msg("You're resting. Type 'stand' first if you want to use this.")
            return

        if self.rules.is_in_combat(caller):
            if not self.rules.is_turn(caller):
                caller.msg("You can only do that on your turn.")
                return
            if caller.db.combat_actionsleft is not None and caller.db.combat_actionsleft <= 0:
                caller.msg("You've already used your action this turn.")
                return

        lhs, _, rhs = self.args.partition("=")
        lhs = lhs.strip().lower()

        known = racial_abilities_known(caller)
        if not lhs:
            if not known:
                caller.msg("Your race grants you no innate abilities.")
                return
            caller.msg(
                "Usage: racial <ability> [= target]\nYour race grants: %s"
                % ", ".join(name.title() for name in known)
            )
            return

        matches = [name for name in known if lhs == name or lhs in name]
        if not matches:
            caller.msg("Your race doesn't grant you an ability called that.")
            return
        if len(matches) > 1:
            caller.msg("Which one do you mean: %s?" % ", ".join(matches))
            return
        ability_name = matches[0]
        data = RACIAL_ABILITIES[ability_name]

        turns_left = self.rules.get_cooldowns(caller).get(ability_name, 0)
        if turns_left > 0:
            caller.msg(
                "%s is still recovering - %i more turn%s."
                % (ability_name.title(), turns_left, "" if turns_left == 1 else "s")
            )
            return

        target_text = rhs.strip()
        target_type = data["target"]

        if target_type == "self":
            targets = [caller]
        elif not target_text and target_type == "anychar":
            # See CmdCast's identical fallback, world/combat.py - an
            # ally-or-self ability (a heal, here) with no target given
            # defaults to the caller themselves, same as 'cast cure
            # wounds' with no argument heals the caster.
            targets = [caller]
        elif not target_text:
            possible_enemies = [
                t for t in caller.location.contents
                if t.attributes.has("max_hp") and not self.rules.is_ally(caller, t)
            ]
            current_target = caller.db.combat_last_target
            if current_target in possible_enemies:
                targets = [current_target]
            elif len(possible_enemies) == 1:
                targets = [possible_enemies[0]]
            elif len(possible_enemies) == 0:
                caller.msg("There's nobody here to target.")
                return
            else:
                caller.msg(
                    "Use '%s' on whom? More than one possible target - "
                    "specify a name." % ability_name
                )
                return
        else:
            candidates = caller.location.contents
            match = find_combat_target(caller, target_text, candidates=candidates)
            if not match:
                return
            targets = [match]

        if target_type in ("otherchar", "other") and caller in targets:
            caller.msg("You can't use '%s' on yourself." % ability_name)
            return

        # See the identical fix (and its own docstring) in CmdCast/
        # CmdUseSkill, world/combat.py - an offensive racial ability
        # used outside combat is what starts the fight now, the same
        # real, tracked way 'fight'/an offensive spell or skill would,
        # rather than landing as a free, no-consequence hit.
        self.rules.start_combat_from_offensive_action(caller, targets)

        data["abilityfunc"](caller, ability_name, targets, **data)
        if data["cooldown"] > 0:
            self.rules.get_cooldowns(caller)[ability_name] = data["cooldown"]


class CmdRacialInfo(Command):
    """
    List your race's innate abilities, their cooldowns, and what they do.

    Usage:
      racialinfo
    """

    key = "racialinfo"
    aliases = ["raceinfo"]
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        caller = self.caller
        known = racial_abilities_known(caller)
        if not known:
            caller.msg("Your race grants you no innate abilities.")
            return

        cooldowns = self.rules.get_cooldowns(caller)
        lines = ["|wYour racial abilities:|n"]
        for name in known:
            data = RACIAL_ABILITIES[name]
            turns_left = cooldowns.get(name, 0)
            status = (
                "|rrecovering - %i more turn%s|n"
                % (turns_left, "" if turns_left == 1 else "s")
                if turns_left > 0
                else "|gready|n"
            )
            lines.append(
                "  |Y%s|n (%s) - %s" % (name.title(), status, data["desc"])
            )
        lines.append("")
        lines.append("Use 'racial <ability> [= target]' to call on one.")
        caller.msg("\n".join(lines))


class RacialAbilitiesCmdSet(CmdSet):
    """'racial' and 'racialinfo'."""

    key = "Racial Abilities CmdSet"

    def at_cmdset_creation(self):
        self.add(CmdRacial())
        self.add(CmdRacialInfo())
