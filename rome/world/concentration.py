"""
Concentration spells and the states that ride on them: flight, true
invisibility, sleep, confusion and the Flame of Vesta aura - plus the
`fly`/`land`, `release` and `effects` commands that go with them.

CONCENTRATION
A concentration spell keeps working only while its caster keeps paying for it.
Casting costs MP once, up front, like any spell; holding it costs MP again every
CONCENTRATION_TICK seconds until it's released, runs the caster dry, or the
caster logs out. Several can be held at once - flight and invisibility together
is the point - each with its own drain, so the more you hold, the sooner they
all give out together. What's held lives in db.concentrations
({key: {spell, drain_percent, target, started}}), and one persistent
ConcentrationScript per caster does the draining.

Concentration is deliberately NOT broken by combat: you can cast one in or out
of a fight and it keeps running through it. Only three things end it - the
caster releasing it, running out of MP, or leaving the game (logout / death).
It also can't be rested off: `rest` refuses while anything is held, since a
free MP refill would make "holds while the MP drains" meaningless.

Each drain is a share of the caster's own max MP rather than a flat number, so
a concentration costs the same fraction of a caster's pool at level 30 as at
level 90 (minimum 1 MP a tick). Lighter magic - flight - is about 1% a tick;
invisibility and sleep about 2%; the Flame of Vesta 3%.

THE STATES
  - Flight: movement costs a quarter of the usual SP (every 4th step, see
    CombatCharacter._check_and_pay_movement_sp). Harpies fly for free (`fly`,
    no MP, no drain); an Augur casts the spell.
  - Invisibility: hidden from every player and NPC that can't see through it
    (room lists, targeting, speech shows "Someone"), and skips wilderness
    encounters. It ends the instant its holder attacks or casts anything
    hostile - no lingering bonus. Cast mid-fight it ends the fight for the
    caster (nobody can see them to keep fighting). The counter is See
    Invisibility (gods always see through it).
  - Sleep: the target can't speak, cast, use skills or move until the caster
    releases it; ANY damage wakes them. It ends the target's fight.
  - Confusion: timed (3-5 real minutes), not held. The confused wander into
    random rooms and lash out at whoever's nearby until it fades; cast mid-
    fight it ends the fight for the target.
  - Flame of Vesta: while held, an aura that damages every enemy in the
    caster's fight each tick.

Whatever is built on `db.conditions` uses the standard condition dict, so
Asleep and Confused show in `stats` and `effects` like any other; both use a
held (True) duration - the timer lives here, not in the per-turn tickdown.
"""

import time
from random import choice, randint

from evennia import DefaultScript
from evennia.utils import delay

from commands.command import Command, build_hpmp_prompt

CONCENTRATION_TICK = 10  # seconds between drains
SLEEP_MAX_SECONDS = 600  # a held sleep can't outlast this, whatever the MP
CONFUSION_MIN_SECONDS = 180
CONFUSION_MAX_SECONDS = 300
CONFUSION_TICK = 8
FLIGHT_SP_EVERY = 4  # flying pays 1 SP on every 4th step: a 75% discount

# Which exit classes a confused creature will stumble through. An allowlist:
# special exits (the Underworld ferry, wilderness entrances, level gates,
# one-way story gates) are never part of a random walk.
_WALKABLE_EXIT_CLASSES = {"Exit", "WildernessExit", "DescriptiveDoor"}


def _rules():
    from world.combat import COMBAT_RULES

    return COMBAT_RULES


# ----------------------------------------------------------------------------
# CONCENTRATION CORE
# ----------------------------------------------------------------------------


def get_concentrations(character):
    if character.db.concentrations is None:
        character.db.concentrations = {}
    return character.db.concentrations


def is_concentrating(character, key):
    return key in (character.db.concentrations or {})


def drain_for(character, drain_percent):
    """MP one tick of a concentration costs this caster."""
    if not drain_percent:
        return 0
    return max(1, round((character.db.max_mp or 0) * drain_percent))


def total_drain(character):
    return sum(
        drain_for(character, entry.get("drain_percent", 0))
        for entry in get_concentrations(character).values()
    )


def drain_word(drain_percent):
    if not drain_percent:
        return "no"
    if drain_percent <= 0.011:
        return "light"
    if drain_percent <= 0.021:
        return "moderate"
    return "heavy"


def _ensure_script(character):
    if not character.scripts.has("concentration"):
        character.scripts.add(ConcentrationScript)


def _stop_script_if_idle(character):
    if not (character.db.concentrations or {}):
        character.scripts.remove("concentration")


def begin_concentration(caster, key, spell, drain_percent, target=None):
    conc = get_concentrations(caster)
    conc[key] = {
        "spell": spell,
        "drain_percent": drain_percent,
        "target": target,
        "started": time.time(),
    }
    _ensure_script(caster)


def _drop_entry(caster, key):
    """Removes an entry without any of the end-of-effect side effects."""
    conc = caster.db.concentrations or {}
    entry = conc.get(key)
    if entry is None:
        return None
    del conc[key]
    _stop_script_if_idle(caster)
    return entry


def end_concentration(caster, key, reason="released"):
    """
    Ends one held concentration and undoes whatever it was holding up.
    `reason`: "released" (the caster let go), "exhausted" (MP ran out),
    "logout", "death", "attack" (invisibility broken by an attack) or
    "faded" (nothing left to hold). Returns True if something was ended.
    """
    entry = _drop_entry(caster, key)
    if entry is None:
        return False

    quiet = reason in ("logout", "death")
    where = caster.location

    if key == "fly":
        if not quiet:
            caster.msg("You settle back to the ground.")
            if where:
                where.msg_contents("%s drifts back down to the ground." % caster, exclude=caster)
    elif key == "invisibility":
        if reason == "attack":
            caster.msg("|yYour spell shatters as you strike - you shimmer back into view!|n")
            if where:
                where.msg_contents("%s shimmers into view, mid-strike!" % caster, exclude=caster)
        elif not quiet:
            caster.msg("You let the spell go and become visible again.")
            if where:
                where.msg_contents("%s shimmers into view." % caster, exclude=caster)
    elif key.startswith("sleep:"):
        target = entry.get("target")
        if target is not None and target.pk:
            wake_sleeper(target, reason="released" if reason == "released" else "spell_ended")
    elif key == "vesta":
        if not quiet:
            caster.msg("The sacred flame gutters out.")
            if where:
                where.msg_contents("The flame about %s gutters out." % caster, exclude=caster)

    return True


def end_all_concentrations(caster, reason="released"):
    ended = []
    for key in list((caster.db.concentrations or {}).keys()):
        if end_concentration(caster, key, reason=reason):
            ended.append(key)
    return ended


class ConcentrationScript(DefaultScript):
    """One per caster holding anything. Drains MP and runs per-tick effects."""

    def at_script_creation(self):
        self.key = "concentration"
        self.interval = CONCENTRATION_TICK
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        caster = self.obj
        if not caster or not caster.pk:
            self.stop()
            return
        conc = caster.db.concentrations
        if not conc:
            self.stop()
            return

        # Safety net for a caster who vanished without logging out cleanly.
        # Requires a few consecutive misses so a reload (sessions not yet
        # re-synced when the first tick fires) can never drop a real player's
        # spells.
        if not caster.sessions.count():
            self.ndb.offline_ticks = (self.ndb.offline_ticks or 0) + 1
            if self.ndb.offline_ticks >= 3:
                end_all_concentrations(caster, reason="logout")
            return
        self.ndb.offline_ticks = 0

        if caster.db.is_dead:
            end_all_concentrations(caster, reason="death")
            return

        drain = total_drain(caster)
        if drain and (caster.db.mp or 0) < drain:
            if caster.location:
                caster.msg(
                    "|rYour strength gives out and your concentration collapses - "
                    "everything you were holding lets go.|n"
                )
            end_all_concentrations(caster, reason="exhausted")
            return
        caster.db.mp = (caster.db.mp or 0) - drain

        if drain and (caster.db.mp or 0) < drain * 3 and not self.ndb.warned:
            caster.msg("|yYour concentration wavers - you can't keep this up much longer.|n")
            self.ndb.warned = True
        elif (caster.db.mp or 0) >= drain * 3:
            self.ndb.warned = False

        for key in list(conc.keys()):
            entry = conc.get(key)
            if entry is None:
                continue
            if key.startswith("sleep:"):
                target = entry.get("target")
                if target is None or not target.pk or "Asleep" not in (target.db.conditions or {}):
                    _drop_entry(caster, key)
                    caster.msg("Your hold on the sleeper fades - nothing is left to hold.")
            elif key == "vesta":
                _tick_flame_of_vesta(caster, entry)

        if caster.pk and caster.attributes.has("max_hp"):
            caster.msg(prompt=build_hpmp_prompt(caster))


def _finish_cast(caster):
    rules = _rules()
    if rules.is_in_combat(caster):
        rules.spend_action(caster, 1, action_name="cast")


# ----------------------------------------------------------------------------
# FLIGHT
# ----------------------------------------------------------------------------


def is_flying(character):
    return is_concentrating(character, "fly")


def flight_pays_this_step(character):
    """
    True if this step of a flier's journey should cost SP. Flight makes
    movement cost 1 SP in every FLIGHT_SP_EVERY steps instead of every one -
    a counter, since SP is a whole number and a quarter of 1 can't be paid.
    """
    steps = (character.db.flight_steps or 0) + 1
    if steps >= FLIGHT_SP_EVERY:
        character.db.flight_steps = 0
        return True
    character.db.flight_steps = steps
    return False


def spell_fly(caster, spell_name, targets, cost, **kwargs):
    if (caster.db.race or "").lower() == "harpy":
        caster.msg("A Harpy needs no spell to fly - just type 'fly'.")
        return False
    if is_flying(caster):
        caster.msg("You're already in the air. ('land' brings you down.)")
        return False
    caster.db.mp -= cost
    caster.location.msg_contents(
        "%s casts %s and rises into the air, feet leaving the ground." % (caster, spell_name)
    )
    begin_concentration(caster, "fly", spell_name, kwargs.get("drain_percent", 0.01))
    caster.msg(
        "|cYou are flying. Journeys cost a quarter of the stamina now, but holding "
        "the spell drains your MP - 'land' or 'release fly' lets it go.|n"
    )
    _finish_cast(caster)


class CmdFly(Command):
    """
    Take to the air.

    Usage:
      fly          - Harpies: take to the air, free
      cast fly     - Augurs: the Fly spell (level 30)
      land         - come back down

    A Harpy is born to it: flying costs no MP, no spell and no
    concentration you can run dry on - just type 'fly'. An Augur learns the
    spell 'fly' at level 30 (cast it with 'cast fly'); that one is a
    concentration spell, so holding it drains a little MP every few seconds
    until you 'land'.

    Either way, while you're airborne, travelling from room to room costs a
    quarter of the usual stamina, which makes exploring far easier. It works
    in and out of a fight, and ends when you 'land' or log out. See 'help
    concentration' for how held spells work.
    """

    key = "fly"
    aliases = []
    help_category = "general"

    def func(self):
        caller = self.caller
        if (caller.db.race or "").lower() != "harpy":
            if "fly" in (caller.db.spells_known or []):
                caller.msg("You have no wings of your own - cast the spell: cast fly")
            else:
                caller.msg(
                    "You have no wings. Only Harpies can fly at will; a few casters "
                    "learn a spell that lets them (see 'help concentration')."
                )
            return
        if caller.db.is_dead:
            caller.msg("The dead have no wings to spread.")
            return
        if is_flying(caller):
            caller.msg("You're already in the air. ('land' brings you down.)")
            return
        begin_concentration(caller, "fly", "harpy flight", 0)
        caller.msg("|cYou spread your wings and rise. Journeys cost far less stamina while you fly.|n")
        caller.location.msg_contents(
            "%s spreads their wings and lifts off the ground." % caller, exclude=caller
        )


# ----------------------------------------------------------------------------
# INVISIBILITY
# ----------------------------------------------------------------------------


def is_invisible(character):
    return character is not None and is_concentrating(character, "invisibility")


def invisible_hides_from(character, looker):
    """
    True if `character` is invisible and `looker` is someone it hides from.
    Only three kinds of looker see through it: the character themself, gods,
    and anyone under the See Invisibility spell - not even the character's own
    party can see them without it. A looker of None is never hidden from (it
    means "no viewpoint", not "a stranger").
    """
    if character is None or looker is None or looker is character:
        return False
    if not hasattr(character, "db") or not is_invisible(character):
        return False
    if not hasattr(looker, "db"):
        return False
    if (looker.db.level or 0) > 100:
        return False
    account = getattr(looker, "account", None)
    if account and account.is_superuser:
        return False
    return "Sees Invisible" not in (looker.db.conditions or {})


def reveal_on_offense(character):
    """Invisibility ends the moment its holder attacks - no lingering bonus."""
    if is_invisible(character):
        end_concentration(character, "invisibility", reason="attack")


def spell_invisibility(caster, spell_name, targets, cost, **kwargs):
    rules = _rules()
    if is_invisible(caster):
        caster.msg("You're already unseen. ('visible' lets the spell go.)")
        return False
    caster.db.mp -= cost
    caster.location.msg_contents(
        "%s casts %s and vanishes from sight!" % (caster, spell_name), exclude=caster
    )
    was_in_combat = rules.is_in_combat(caster)
    begin_concentration(caster, "invisibility", spell_name, kwargs.get("drain_percent", 0.02))
    caster.msg(
        "|cYou can no longer be seen. Attack or cast anything hostile and the spell "
        "breaks; 'visible' or 'release invisibility' lets it go.|n"
    )
    if was_in_combat:
        caster.location.msg_contents(
            "Nobody can strike what they can't see - the fight around %s falls apart." % caster,
            exclude=caster,
        )
        rules.force_disengage(caster)
    else:
        _finish_cast(caster)


# ----------------------------------------------------------------------------
# HOSTILE-SPELL GUARDS
# ----------------------------------------------------------------------------


def _hostile_blocked(caster, target):
    """A reason this crowd-control spell can't be used on `target`, or None."""
    from world.combat import is_no_combat_zone

    rules = _rules()
    if target is None or target is caster:
        return "You can't do that to yourself."
    if target.db.pacifist:
        return "%s has laid down arms for good - such magic cannot touch them." % target.key
    if target.db.invincible or (target.db.level or 0) > 100:
        return "%s is beyond such magic." % target.key
    if target.db.is_dead:
        return "%s is beyond your reach." % target.key
    if rules.is_ally(caster, target):
        return "You won't turn your magic on an ally."
    if is_no_combat_zone(caster.location):
        return "Something about this place forbids violence - the spell will not take."
    return None


# ----------------------------------------------------------------------------
# SLEEP
# ----------------------------------------------------------------------------


def sleep_key(target):
    return "sleep:%s" % target.id


def _expire_sleep(target, token):
    """Hard cap on a held sleep. Module-level so it survives a reload."""
    if not target or not target.pk:
        return
    cond = (target.db.conditions or {}).get("Asleep")
    if cond is not None and target.db.sleep_token == token:
        wake_sleeper(target, reason="spell_ended")


def wake_sleeper(target, reason="damage"):
    """
    Wakes `target` and lets its caster's hold go. `reason`: "damage" (struck
    awake), "released", or "spell_ended" (the concentration ran out).
    Safe to call on anyone; a no-op if they're not asleep.
    """
    rules = _rules()
    conditions = rules.get_conditions(target)
    cond = conditions.pop("Asleep", None)
    if cond is None:
        return False
    target.db.sleep_token = None
    caster = cond[1]
    if caster is not None and getattr(caster, "pk", None):
        entry = _drop_entry(caster, sleep_key(target))
        if entry is not None and reason == "damage":
            caster.msg("Your spell on %s breaks as they're jolted awake." % target.key)
    where = target.location
    if where:
        if reason == "damage":
            where.msg_contents("|y%s jolts awake with a start!|n" % target)
        else:
            where.msg_contents("%s stirs and wakes." % target)
    target.msg("|yYou wake!|n")
    return True


def spell_sleep(caster, spell_name, targets, cost, **kwargs):
    rules = _rules()
    target = targets[0]
    if "Asleep" in rules.get_conditions(target):
        caster.msg("%s is already asleep." % target.key)
        return False
    problem = _hostile_blocked(caster, target)
    if problem:
        caster.msg(problem)
        return False

    caster.db.mp -= cost
    reveal_on_offense(caster)
    caster.location.msg_contents("%s casts %s at %s!" % (caster, spell_name, target))
    if rules.resists_condition(caster, target):
        caster.location.msg_contents("%s shakes off the drowsiness and resists the effect!" % target)
        _finish_cast(caster)
        return

    rules.add_condition(target, caster, "Asleep", True)
    caster.location.msg_contents("%s slumps, fast asleep." % target)
    target.msg("|rA crushing drowsiness overwhelms you - you can't move, speak or act until something wakes you.|n")
    if rules.is_in_combat(target):
        rules.force_disengage(target)
    token = time.time()
    target.db.sleep_token = token
    begin_concentration(
        caster, sleep_key(target), spell_name, kwargs.get("drain_percent", 0.02), target=target
    )
    delay(SLEEP_MAX_SECONDS, _expire_sleep, target, token, persistent=True)
    caster.msg(
        "|cYou hold %s in slumber. Any blow wakes them; 'release sleep' lets them go, "
        "and holding it drains your MP.|n" % target.key
    )
    _finish_cast(caster)


def asleep_blocks(character):
    return "Asleep" in (character.db.conditions or {})


ASLEEP_MESSAGE = (
    "|rYou are fast asleep, held in a magical slumber - you can do nothing until "
    "something wakes you.|n"
)

# Commands a sleeper may still use: looking, and purely out-of-game housekeeping.
SLEEP_ALLOWED_COMMANDS = frozenset({
    "look", "l", "ls", "effects", "affects", "help", "h", "?", "who", "quit", "ooc", "ic",
    "inventory", "inv", "i", "stats", "score", "corestats", "status", "time", "motd", "news",
    "bug", "idea", "ideas", "report", "achievements", "achieve", "titles", "journey",
})


def sleeper_may_run(command):
    names = {(command.key or "").lower(), (getattr(command, "cmdstring", "") or "").lower()}
    names.update((alias or "").lower() for alias in (command.aliases or []))
    if any(name.startswith("__") for name in names):
        return True  # engine system commands (no-input, unknown-command, ...)
    return bool(names & SLEEP_ALLOWED_COMMANDS)


# ----------------------------------------------------------------------------
# CONFUSION
# ----------------------------------------------------------------------------


def is_confused(character):
    return "Confused" in (character.db.conditions or {})


def end_confusion(target, reason="faded"):
    conditions = (target.db.conditions or {})
    conditions.pop("Confused", None)
    target.db.confused_until = None
    home = target.db.confused_from
    target.db.confused_from = None
    target.scripts.remove("confusion")
    if not target.pk:
        return
    target.msg("|gThe fog lifts from your mind.|n")
    if target.location:
        target.location.msg_contents("%s blinks and seems to come back to themself." % target, exclude=target)
    # An NPC that stumbled off goes back to its post (players are left where
    # they ended up - that's their own two feet's business).
    if home is not None and getattr(home, "pk", None) and not getattr(target, "account", None):
        if target.location != home and not home.is_typeclass(
            "evennia.contrib.grid.wilderness.wilderness.WildernessRoom", exact=False
        ):
            target.move_to(home, quiet=False, move_type="wander")


def _walkable_exits(character):
    location = character.location
    if not location:
        return []
    exits = []
    for ex in location.exits:
        if not ex.destination:
            continue
        if not ({cls.__name__ for cls in type(ex).__mro__} & _WALKABLE_EXIT_CLASSES):
            continue
        if not ex.access(character, "traverse"):
            continue
        exits.append(ex)
    return exits


def _combat_capable(character):
    return bool(getattr(character, "account", None)) or hasattr(character, "_gather_actions")


def _random_victim(character):
    from world.combat import is_no_combat_zone

    if is_no_combat_zone(character.location) or not _combat_capable(character):
        return None
    rules = _rules()
    candidates = []
    for thing in character.location.contents:
        if thing is character or not thing.db.hp or thing.db.pacifist or thing.db.is_dead:
            continue
        if thing.db.invincible or (thing.db.level or 0) > 100:
            continue
        if rules.is_ally(character, thing):
            continue
        candidates.append(thing)
    return choice(candidates) if candidates else None


class ConfusionScript(DefaultScript):
    """Runs a confused creature's random behaviour until the spell fades."""

    def at_script_creation(self):
        self.key = "confusion"
        self.interval = CONFUSION_TICK
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        target = self.obj
        if not target or not target.pk:
            self.stop()
            return
        if not is_confused(target):
            self.stop()
            return
        if time.time() >= (target.db.confused_until or 0):
            end_confusion(target)
            return
        # Nothing to act on for someone logged out, dead, asleep or already
        # in a fight (the fight itself is what's happening to them).
        if not target.location or target.db.is_dead or not target.db.hp:
            return
        rules = _rules()
        if asleep_blocks(target) or rules.is_in_combat(target):
            return
        if hasattr(target, "stop_resting"):
            target.stop_resting()

        roll = randint(1, 100)
        if roll <= 55:
            exits = _walkable_exits(target)
            if exits:
                ex = choice(exits)
                target.msg("|yYou stumble away %s, dazed and unsure why.|n" % ex.key)
                target.location.msg_contents(
                    "%s stumbles off %s, dazed." % (target, ex.key), exclude=target
                )
                target.move_to(ex.destination, move_type="wander")
                return
        elif roll <= 85:
            victim = _random_victim(target)
            if victim is not None:
                target.msg("|yYou lash out wildly at %s!|n" % victim)
                target.location.msg_contents(
                    "%s rounds on %s in a daze and lashes out!" % (target, victim), exclude=target
                )
                rules.start_combat_from_offensive_action(target, [victim])
                return
        target.msg("|yThe world swims - you stagger and mutter, unable to think straight.|n")
        target.location.msg_contents("%s staggers, muttering nonsense." % target, exclude=target)


def spell_confusion(caster, spell_name, targets, cost, **kwargs):
    rules = _rules()
    target = targets[0]
    if is_confused(target):
        caster.msg("%s is already confused." % target.key)
        return False
    problem = _hostile_blocked(caster, target)
    if problem:
        caster.msg(problem)
        return False

    caster.db.mp -= cost
    reveal_on_offense(caster)
    caster.location.msg_contents("%s casts %s at %s!" % (caster, spell_name, target))
    if rules.resists_condition(caster, target):
        caster.location.msg_contents("%s clears their head and resists the effect!" % target)
        _finish_cast(caster)
        return

    duration = randint(CONFUSION_MIN_SECONDS, CONFUSION_MAX_SECONDS)
    rules.add_condition(target, caster, "Confused", True)
    target.db.confused_until = time.time() + duration
    target.db.confused_from = target.location
    target.msg(
        "|rYour thoughts scatter. For the next few minutes you'll wander and lash out "
        "at random until it passes.|n"
    )
    if rules.is_in_combat(target):
        rules.force_disengage(target)
        caster.location.msg_contents(
            "%s loses all interest in the fight, and wanders off in a daze." % target
        )
    if not target.scripts.has("confusion"):
        target.scripts.add(ConfusionScript)
    _finish_cast(caster)


# ----------------------------------------------------------------------------
# FLAME OF VESTA
# ----------------------------------------------------------------------------


def _tick_flame_of_vesta(caster, entry):
    """Each tick, scorches every enemy in the caster's own fight."""
    from world.combat import scale_spell_damage_range, SPELLS

    rules = _rules()
    if not rules.is_in_combat(caster):
        return
    handler = caster.db.combat_turnhandler
    fighters = (handler.db.fighters if handler and handler.pk else None) or []
    spell = SPELLS.get("flame of vesta", {})
    low, high = scale_spell_damage_range(
        caster, spell.get("aura_damage_range", (4, 7)), spell_name="flame of vesta"
    )
    bonus = ((caster.db.ingenium or 10) - 10) // 2
    foes = [
        f for f in fighters
        if f is not None and f.pk and f is not caster and f.db.hp and not rules.is_ally(caster, f)
    ]
    for foe in foes:
        damage = randint(low, high) + bonus
        caster.location.msg_contents(
            "|rHallowed fire from %s's aura scorches %s for %i damage!|n" % (caster, foe, damage)
        )
        rules.apply_damage(foe, damage, attacker=caster, announce_threshold=False)
        if foe.db.hp <= 0:
            rules.at_defeat(foe, attacker=caster)


def spell_flame_of_vesta(caster, spell_name, targets, cost, **kwargs):
    if is_concentrating(caster, "vesta"):
        caster.msg("The sacred flame already burns about you.")
        return False
    caster.db.mp -= cost
    caster.location.msg_contents(
        "%s casts %s, and a ring of pale hearth-fire kindles about them." % (caster, spell_name)
    )
    begin_concentration(caster, "vesta", spell_name, kwargs.get("drain_percent", 0.03))
    caster.msg(
        "|cThe flame scorches every enemy in your fight as long as you hold it - and "
        "drains your MP heavily. 'release vesta' lets it go.|n"
    )
    _finish_cast(caster)


# ----------------------------------------------------------------------------
# COMMANDS
# ----------------------------------------------------------------------------


def _describe_concentration(caster, key, entry):
    """A player-facing name for one held concentration."""
    spell = entry.get("spell") or key
    target = entry.get("target")
    if key.startswith("sleep:") and target is not None and getattr(target, "pk", None):
        return "%s (holding %s asleep)" % (spell, target.key)
    return spell


def _release_hint(key):
    if key == "fly":
        return "land"
    if key == "invisibility":
        return "visible"
    return "release %s" % key.split(":")[0]


class CmdRelease(Command):
    """
    Let go of a spell you're concentrating on.

    Usage:
      release                 - let go of what you're holding (asks if several)
      release <spell>         - e.g. release fly, release sleep
      release all
      land                    - stop flying
      visible                 - drop invisibility

    Concentration spells keep working only while you pay for them with MP
    every few seconds. Letting one go stops the drain at once - a sleeper
    you release wakes, a flier drifts down, an invisible caster shimmers
    back into view. 'effects' shows everything you're holding and how heavy
    each drain is.
    """

    key = "release"
    aliases = []
    help_category = "magic"

    def func(self):
        caller = self.caller
        held = get_concentrations(caller)
        used = (self.cmdstring or self.key).lower()
        arg = self.args.strip().lower()

        if used == "land":
            arg = "fly"
        elif used == "visible":
            arg = "invisibility"
        elif used == "unfly":
            arg = "fly"

        if not held:
            if used == "land":
                caller.msg("You're not flying.")
            elif used == "visible":
                caller.msg("You're not invisible.")
            else:
                caller.msg("You aren't holding any spell.")
            return

        if arg == "all":
            names = [
                _describe_concentration(caller, k, e) for k, e in list(held.items())
            ]
            end_all_concentrations(caller, reason="released")
            caller.msg("You let go of everything you were holding: %s." % ", ".join(names))
            return

        if not arg:
            if len(held) == 1:
                key = next(iter(held))
                end_concentration(caller, key, reason="released")
                return
            lines = ["You're holding several spells - say which to release, or 'release all':"]
            for key, entry in held.items():
                lines.append("  %s (release %s)" % (_describe_concentration(caller, key, entry), _release_hint(key)))
            caller.msg("\n".join(lines))
            return

        matches = []
        for key, entry in held.items():
            target = entry.get("target")
            haystack = " ".join([
                key.lower(), (entry.get("spell") or "").lower(),
                (target.key.lower() if target is not None and getattr(target, "pk", None) else ""),
            ])
            if arg in haystack:
                matches.append(key)
        if not matches:
            caller.msg("You aren't holding anything like '%s'. ('effects' shows what you are.)" % arg)
            return
        if arg in ("sleep",) or len(matches) == 1:
            for key in matches:
                end_concentration(caller, key, reason="released")
            return
        caller.msg(
            "That could mean several things you're holding: %s. Be more specific."
            % ", ".join(_describe_concentration(caller, k, held[k]) for k in matches)
        )


class CmdLand(CmdRelease):
    """
    Come down from the air.

    Usage:
      land

    Ends flight - a Harpy's own, or an Augur's Fly spell - and drops you
    gently back to the ground. For the spell, that also stops the MP drain
    at once. Works in or out of combat and costs no action. If you aren't
    flying it does nothing. To let go of other held spells see 'help
    release'; to fly see 'help fly'.
    """

    key = "land"
    aliases = []


class CmdVisible(CmdRelease):
    """
    Drop your invisibility and step back into view.

    Usage:
      visible

    Ends the Invisibility spell early - it stops the MP drain at once, and
    everyone in the room sees you shimmer back into view. (Invisibility
    also ends by itself the instant you attack or cast anything hostile.)
    If you aren't invisible it does nothing. To let go of other held spells
    see 'help release'; for the spell itself see 'help invisibility'.
    """

    key = "visible"
    aliases = []


class CmdEffects(Command):
    """
    See everything currently affecting you.

    Usage:
      effects

    Lists your active buffs and afflictions, the concentration spells you're
    holding (with how heavy each drain on your MP is, and how to release it),
    and any protective ward you carry. If you're holding concentration
    spells, it also tells you roughly how long your MP will last at the
    current drain.
    """

    key = "effects"
    aliases = ["affects", "buffs", "conditions"]
    help_category = "magic"

    def func(self):
        from world.combat import BENEFICIAL_CONDITIONS, HARMFUL_CONDITIONS
        from world.wards import get_temp_hp, temp_hp_seconds_left

        caller = self.caller
        rules = _rules()
        lines = []

        conditions = rules.get_conditions(caller)
        if conditions:
            lines.append("|wConditions:|n")
            for name, data in conditions.items():
                duration = data[0]
                if name in BENEFICIAL_CONDITIONS:
                    color = "|g"
                elif name in HARMFUL_CONDITIONS:
                    color = "|r"
                else:
                    color = "|w"
                if duration is True:
                    when = "until it's broken"
                elif name == "Confused":
                    when = "until it fades"
                else:
                    when = "about %i more turn%s" % (duration, "" if duration == 1 else "s")
                lines.append("  %s%s|n - %s" % (color, name, when))

        held = get_concentrations(caller)
        if held:
            lines.append("|wHeld by concentration:|n")
            per_tick = 0
            for key, entry in held.items():
                pct = entry.get("drain_percent", 0)
                drain = drain_for(caller, pct)
                per_tick += drain
                per_minute = drain * (60 // CONCENTRATION_TICK)
                word = drain_word(pct)
                cost = (
                    "no drain" if not drain
                    else "%s drain - about %i MP a minute" % (word, per_minute)
                )
                lines.append(
                    "  |c%s|n - %s  (%s)"
                    % (_describe_concentration(caller, key, entry), cost, _release_hint(key))
                )
            if per_tick:
                mp = caller.db.mp or 0
                seconds = int(mp / per_tick) * CONCENTRATION_TICK
                if seconds < 90:
                    lasts = "under a minute and a half"
                else:
                    lasts = "about %i minutes" % max(1, round(seconds / 60))
                lines.append(
                    "  Together they drain about %i MP a minute - your MP will last %s at this rate."
                    % (per_tick * (60 // CONCENTRATION_TICK), lasts)
                )

        temp = get_temp_hp(caller)
        if temp:
            lines.append("|wWard:|n")
            extra = " - and it lashes melee attackers with cold" if caller.db.thorns_range else ""
            lines.append(
                "  |c%i temporary hit points|n, fading in about %i minute%s%s"
                % (temp, max(1, round(temp_hp_seconds_left(caller) / 60)),
                   "" if round(temp_hp_seconds_left(caller) / 60) <= 1 else "s", extra)
            )

        if not lines:
            caller.msg("Nothing is affecting you.")
            return
        caller.msg("|wYou are affected by:|n\n" + "\n".join(lines))


# ----------------------------------------------------------------------------
# REMOVED-SPELL MIGRATION
# ----------------------------------------------------------------------------

# Spells removed in the caster rework, with the level each was learned at.
# Bane (Augur's level-1 spell) is replaced outright by Magic Arrow - it may
# have been a free starting spell, so it's swapped rather than refunded. The
# rest were bought from a trainer and are refunded at what they cost.
REMOVED_SPELLS = {
    "bane": 1,
    "omen of weakness": 20,
    "omen of doom": 45,
    "bless": 15,
    "divine favor": 35,
}
FREE_REPLACEMENTS = {"bane": "magic arrow"}


def prune_removed_spells(character):
    """
    Idempotent. Drops any removed spell from a character's spellbook,
    swapping Bane for Magic Arrow and refunding the gold for the rest.
    Run at login and whenever magic is used, so online and offline players
    are both covered without touching a live object from another process.
    Returns the gold refunded (0 if nothing changed).
    """
    from world.combat import SPELLS, compute_learn_cost

    known = character.db.spells_known
    if not known:
        return 0
    gone = [name for name in known if name in REMOVED_SPELLS]
    if not gone:
        return 0

    kept = [name for name in known if name not in REMOVED_SPELLS]
    refund = 0
    swapped = []
    for name in gone:
        replacement = FREE_REPLACEMENTS.get(name)
        if replacement:
            classes = SPELLS.get(replacement, {}).get("classes")
            if replacement not in kept and (not classes or character.db.player_class in classes):
                kept.append(replacement)
                swapped.append((name, replacement))
                continue
        refund += compute_learn_cost(REMOVED_SPELLS[name])

    character.db.spells_known = sorted(kept)
    if refund:
        character.db.gold = (character.db.gold or 0) + refund

    lines = ["|yThe priests have reworked the old rites - some spells you knew are no more:|n"]
    for old, new in swapped:
        lines.append("  %s is replaced by %s." % (old.title(), new.title()))
    refunded_names = [n for n in gone if n not in dict(swapped)]
    if refunded_names:
        lines.append(
            "  %s - %i gold refunded, to spend on the new spells."
            % (", ".join(n.title() for n in refunded_names), refund)
        )
    character.msg("\n".join(lines))
    return refund
