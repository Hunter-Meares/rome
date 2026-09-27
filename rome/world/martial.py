"""
Martial effects: critical hits, and the D&D-style status effects that damage
skills can inflict - Bleeding, Sundered armor, Disarmed, Grappled, Stunned and
Blinded.

Deliberately NOT built out of the conditions casters already use (poison,
slow, paralysis, fear, defense/accuracy down, ...), so a warrior's tricks are
their own and don't echo a caster spell.

CRITICAL HITS (owner request, Sep 26): a landed melee weapon strike can be a
critical hit and deal extra damage. The chance and multiplier follow the
weapon, D&D 3.5-style "threat range x multiplier" - light blades crit often for
double, axes and polearms rarely for triple - and Agilitas nudges the chance up.
Melee and ranged weapons (bows and javelins crit too - added at the owner's request after the first pass was melee only), REAL PLAYERS only (monsters don't, so no
creature quietly gets deadlier), and a disarmed fighter fights unarmed.
Basic attacks, power attacks and every weapon-based skill can crit.

THE EFFECTS
  - Bleeding: a wound that costs HP every turn - a share of the blow that
    opened it - and stops the moment the target is healed. (Unlike poison, which
    a heal doesn't touch.)
  - Sundered: the strike cleaves through one random piece of worn armor - the
    body armor or the shield - which stops working for the rest of that fight
    (it's a `combat_` attribute, so the engine clears it when the fight ends;
    nothing about the item itself changes). Has no effect on someone wearing
    neither.
  - Disarmed: the target's weapon is knocked from their grip for a couple of
    turns; they fight with bare fists.
  - Grappled: held fast - the target can't disengage or flee.
  - Stunned: knocked senseless - the target loses every turn and can't act, cast,
    speak or move, and unlike Sleep, damage does NOT wake them. Guarded against
    chain-stunning: right after a stun a target is Stun Immune for a few turns.
  - Blinded: dust in the eyes - a big penalty to the target's accuracy.

Bleeding, Disarmed, Grappled, Stunned and Blinded are resisted with Vigor (they
attack the body); a Sundered cleave is a mechanical chance with no resist.
Everything here is real-player-only when it comes from a skill, like the weapon
multiplier - monsters keep their old behaviour.
"""

from random import choice

from django.conf import settings

# --- Critical hits -------------------------------------------------------
# weapon_category -> (base crit chance in percent, damage multiplier)
CRIT_PROFILES = {
    "light_blade": (10, 2.0),   # daggers, gladii: quick and keen
    "ranged": (8, 2.0),         # bows and javelins: a well-placed shot
    "heavy_blade": (8, 2.0),    # swords and greatswords
    "polearm": (5, 3.0),        # spears and tridents: rare but brutal
    "heavy_weapon": (5, 3.0),   # axes and mauls: rare but brutal
    "staff": (5, 2.0),
}
UNARMED_CRIT = (5, 2.0)
KEEN_EDGE_CRIT_BONUS = 15  # extra percentage points while a Gladiator's Weapon Flourish is up
CRIT_PER_AGILITAS = 0.5   # extra percentage points per point of Agilitas over 10
CRIT_MAX_CHANCE = 30

# Effects a skill's `rider` can inflict, and how long the fight-scoped ones
# linger. Stun immunity is deliberate: without it a stun-lock is a real PvP risk.
STUN_IMMUNITY_EXTRA_TURNS = 3
BLINDED_ACCURACY_MOD = -50   # Accuracy Down (the caster debuff) is -25


# Critical hits are random, and hundreds of existing tests assert exact damage
# numbers - so under the test runner (Evennia sets TEST_ENVIRONMENT) crits are
# off unless a test that is about crits switches them on with this flag.
CRITS_IN_TESTS = False


def crits_enabled():
    return not getattr(settings, "TEST_ENVIRONMENT", False) or CRITS_IN_TESTS


def _rules():
    from world.combat import COMBAT_RULES

    return COMBAT_RULES


def _randint(low, high):
    # Resolved through world.combat so a test that fixes the dice fixes these too.
    from world import combat

    return combat.randint(low, high)


def wielded_weapon(character):
    """The weapon a character actually fights with: none if they're Disarmed."""
    if "Disarmed" in (character.db.conditions or {}):
        return None
    return character.db.wielded_weapon


def crit_profile(attacker):
    """(chance percent, multiplier) for this attacker, or None if they can't crit."""
    if not getattr(attacker, "account", None) or not crits_enabled():
        return None
    weapon = wielded_weapon(attacker)
    if weapon is not None:
        profile = CRIT_PROFILES.get(weapon.db.weapon_category)
        if profile is None:
            return None  # ranged, or something that isn't a melee weapon
    else:
        profile = UNARMED_CRIT
    chance, multiplier = profile
    chance += max(0, (attacker.db.agilitas or 10) - 10) * CRIT_PER_AGILITAS
    if "Keen Edge" in (attacker.db.conditions or {}):
        chance += KEEN_EDGE_CRIT_BONUS  # the Gladiator's Weapon Flourish
    return min(CRIT_MAX_CHANCE, chance), multiplier


def roll_crit(attacker, guaranteed=False):
    """
    The damage multiplier for one landed strike: the weapon's crit multiplier if
    it crits (always, if `guaranteed` and the attacker can crit at all), else 1.
    """
    profile = crit_profile(attacker)
    if profile is None:
        return 1.0
    chance, multiplier = profile
    if guaranteed or _randint(1, 100) <= chance:
        return multiplier
    return 1.0


def announce_crit(attacker):
    if attacker.location:
        attacker.location.msg_contents("|r*** CRITICAL HIT! ***|n %s strikes a vital spot!" % attacker)


# --- Status effects ------------------------------------------------------

def stop_bleeding(character, quiet=False):
    """A heal closes a bleeding wound. Called wherever HP is restored."""
    conditions = character.db.conditions or {}
    if "Bleeding" in conditions:
        del conditions["Bleeding"]
        if not quiet and character.location:
            character.location.msg_contents("%s's wounds stop bleeding." % character)
        return True
    return False


def pathfinder_pays_this_step(character):
    """The Venator's Pathfinder: only every second step costs stamina."""
    steps = (character.db.pathfinder_steps or 0) + 1
    if steps >= 2:
        character.db.pathfinder_steps = 0
        return True
    character.db.pathfinder_steps = steps
    return False


def is_incapacitated(character):
    """Asleep (Sleep spell) or Stunned - unable to act at all."""
    conditions = character.db.conditions or {}
    return "Asleep" in conditions or "Stunned" in conditions


def incapacitated_message(character):
    if "Stunned" in (character.db.conditions or {}):
        return "|rYou are stunned - you can do nothing until it passes.|n"
    return (
        "|rYou are fast asleep, held in a magical slumber - you can do nothing until "
        "something wakes you.|n"
    )


def is_sundered(character, slot):
    """True if the piece worn in `slot` has been cleaved through this fight."""
    held = character.db.combat_sundered
    return held == slot or held == "both"


def _sunder(rules, target, both=False):
    """
    Cleave through one random worn piece of armor for the rest of the fight - or,
    with `both` (Shattering Blow), every piece worn: the body armor AND the shield.
    """
    options = [
        slot for slot in ("worn_armor", "worn_shield")
        if getattr(target.db, slot) and not is_sundered(target, slot)
    ]
    if not options:
        return False
    if both:
        chosen = options
        already = [s for s in ("worn_armor", "worn_shield") if is_sundered(target, s)]
        target.db.combat_sundered = "both" if len(chosen) + len(already) == 2 else chosen[0]
    else:
        chosen = [choice(options)]
        already = [s for s in ("worn_armor", "worn_shield") if is_sundered(target, s)]
        target.db.combat_sundered = "both" if already else chosen[0]
    for slot in chosen:
        item = getattr(target.db, slot)
        target.location.msg_contents(
            "|rThe blow cleaves clean through %s's %s - it hangs useless for the rest of the fight!|n"
            % (target, item.key)
        )
    return True


def apply_rider(rules, user, target, rider, damage=0, attacker_stat=None):
    """
    Inflicts a skill's rider effect on `target` after a landed hit. `rider` is a
    SKILLS-entry dict: {"effect", "chance" (percent, default 100), "duration"
    (turns), "share" (Bleeding: fraction of the blow that opened the wound)}.
    Only real players' skills carry riders, and only against living, non-pacifist
    targets.
    """
    if not rider or not getattr(user, "account", None):
        return False
    if target is None or not target.pk or (target.db.hp or 0) <= 0 or target.db.pacifist:
        return False
    if _randint(1, 100) > rider.get("chance", 100):
        return False

    effect = rider["effect"]
    duration = rider.get("duration", 2)

    if effect == "Sundered":
        return _sunder(rules, target, both=rider.get("both", False))

    # Legionary's Unbreakable (Sep 27): outright immunity to the four holds/
    # blinds below, no resist roll needed - checked before the ordinary
    # resist check so it's a hard stop, not just better odds.
    if effect in ("Stunned", "Grappled", "Disarmed", "Blinded") and "Unbreakable" in (
        target.db.conditions or {}
    ):
        if target.location:
            target.location.msg_contents("%s is unbreakable - it can't take hold!" % target)
        return False

    if rules.resists_condition(
        user, target, condition=effect, attacker_stat=attacker_stat,
        resist_stat=rider.get("resist"),
    ):
        target.location.msg_contents("%s shrugs off the %s!" % (target, effect.lower()))
        return False

    conditions = rules.get_conditions(target)
    if effect == "Stunned":
        if "Stun Immunity" in conditions:
            target.location.msg_contents("%s is too dazed already to be stunned again!" % target)
            return False
        rules.add_condition(target, user, "Stunned", duration)
        rules.add_condition(target, user, "Stun Immunity", duration + STUN_IMMUNITY_EXTRA_TURNS)
        target.msg("|rThe blow leaves you senseless - you can't act until it passes.|n")
        return True
    if effect == "Bleeding":
        magnitude = max(1, int(damage * rider.get("share", 0.2)))
        rules.add_condition(target, user, "Bleeding", duration)
        # (re-fetched: the condition dict from before add_condition is stale)
        rules.get_conditions(target)["Bleeding"].append(magnitude)  # [turns, source, HP lost per turn]
        return True
    # Disarmed, Grappled, Blinded: a plain timed condition.
    rules.add_condition(target, user, effect, duration)
    return True
