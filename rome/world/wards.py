"""
Temporary hit points and the retaliation ward - the mechanic behind False
Life, Aid and Armor of Agathys.

Temporary HP is a buffer that sits in front of a character's real HP: every
hit is soaked by it first, and only what's left gets through
(CombatRules.apply_damage calls absorb_with_temp_hp). It is not healing - it
doesn't raise max HP, isn't restored by resting, and doesn't stack: a new ward
only replaces the old one if it's stronger. It also fades on its own after
TEMP_HP_SECONDS of real time, checked lazily on read (get_temp_hp) so there's
no timer to lose across a reload.

Armor of Agathys adds a retaliation: while the ward still stands, a melee
attacker who strikes the wearer takes cold damage back. The retaliation range
is fixed at cast time (scaled by the caster's level like any damaging spell)
and lives on the wearer as db.thorns_range until the ward is gone.

Both the ward's size (a share of the target's own max HP) and the retaliation
damage scale with level, so a ward is worth roughly the same fraction of a
fight at level 12 as at level 90.
"""

import time
from random import randint

TEMP_HP_SECONDS = 600  # a ward fades after 10 real minutes


def _rules():
    from world.combat import COMBAT_RULES

    return COMBAT_RULES


def get_temp_hp(character):
    """Current temporary HP (0 if none, or if it has faded)."""
    amount = character.db.temp_hp or 0
    if amount <= 0:
        return 0
    until = character.db.temp_hp_until or 0
    if until and time.time() > until:
        clear_temp_hp(character)
        return 0
    return amount


def clear_temp_hp(character):
    character.db.temp_hp = 0
    character.db.temp_hp_until = None
    character.db.thorns_range = None


def temp_hp_seconds_left(character):
    if not get_temp_hp(character):
        return 0
    return max(0, int((character.db.temp_hp_until or 0) - time.time()))


def grant_temp_hp(character, amount, thorns_range=None):
    """Sets a fresh ward. Callers check strength first (spell_temp_hp)."""
    character.db.temp_hp = int(amount)
    character.db.temp_hp_until = time.time() + TEMP_HP_SECONDS
    character.db.thorns_range = tuple(thorns_range) if thorns_range else None


def absorb_with_temp_hp(rules, defender, damage, attacker=None, melee=False):
    """
    Soaks `damage` with the defender's temporary HP and returns what's left
    over. Called from CombatRules.apply_damage once the hit is known to be
    landing. If the ward carries a retaliation and this was a melee hit, the
    attacker pays for it - even on the hit that breaks the ward.
    """
    temp = get_temp_hp(defender)
    if temp <= 0 or damage <= 0:
        return damage

    thorns = defender.db.thorns_range
    absorbed = min(temp, damage)
    defender.db.temp_hp = temp - absorbed
    remaining = damage - absorbed
    if defender.location:
        defender.location.msg_contents(
            "|c%s's ward soaks up %i damage.|n" % (defender, absorbed)
        )
    if defender.db.temp_hp <= 0:
        clear_temp_hp(defender)
        if defender.location:
            defender.location.msg_contents("|c%s's ward gives way.|n" % defender)

    if melee and thorns and attacker is not None and attacker is not defender and attacker.pk:
        dealt = randint(int(thorns[0]), int(thorns[1]))
        if defender.location:
            defender.location.msg_contents(
                "|cA lash of killing cold answers the blow, striking %s for |r%i|c damage!|n"
                % (attacker, dealt)
            )
        rules.apply_damage(attacker, dealt, attacker=defender, announce_threshold=False)
        if attacker.db.hp is not None and attacker.db.hp <= 0:
            rules.at_defeat(attacker, attacker=defender)
    return remaining


def spell_temp_hp(caster, spell_name, targets, cost, **kwargs):
    """
    Grants temporary HP - False Life (self), Armor of Agathys (self, with a
    retaliation) and Aid (up to three allies). `hp_percent` is the ward's size
    as a share of each target's own max HP; `thorns_range` (Armor of Agathys)
    is the retaliation, scaled by the caster's level and Ingenium.
    """
    from world.combat import scale_spell_damage_range

    rules = _rules()
    pct = kwargs.get("hp_percent", 0.2)
    thorns = kwargs.get("thorns_range")
    scaled_thorns = None
    if thorns:
        lo, hi = scale_spell_damage_range(caster, thorns, spell_name=spell_name)
        bonus = ((caster.db.ingenium or 10) - 10) // 2
        scaled_thorns = (lo + bonus, hi + bonus)

    grants = []
    for target in targets:
        amount = max(1, round((target.db.max_hp or 1) * pct))
        if get_temp_hp(target) >= amount:
            caster.msg("%s is already warded at least this well." % target.key)
            continue
        grants.append((target, amount))
    if not grants:
        return False

    caster.db.mp -= cost
    names = ", ".join(str(t) for t, _ in grants)
    if len(grants) == 1 and grants[0][0] is caster:
        caster.location.msg_contents(
            "%s casts %s, and a shroud of borrowed vitality settles around them." % (caster, spell_name)
        )
    else:
        caster.location.msg_contents(
            "%s casts %s, and borrowed vitality settles around %s." % (caster, spell_name, names)
        )
    for target, amount in grants:
        grant_temp_hp(target, amount, thorns_range=scaled_thorns)
        target.msg("|cYou are warded with %i temporary hit points.|n" % amount)
        if scaled_thorns:
            target.msg("|cAnyone who strikes you in melee while it holds will be lashed by cold.|n")

    if rules.is_in_combat(caster):
        rules.spend_action(caster, 1, action_name="cast")
