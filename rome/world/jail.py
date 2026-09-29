"""
Rome's jail - crime-and-punishment phase 2, part 2. A wanted or homo
sacer player captured by a city guard (world/guards.py's capture(), the
moment their apply_damage clamp fires) ends up here: an ordinary
offender serves a sentence and is released, a convicted murderer (homo
sacer) is executed instead. Confiscation happens at the moment of
capture either way.

Deliberately built on ONE placeholder holding-cell room (see
world/tag_carcer_live.py) rather than a full Carcer complex - the real
building, with its own real geography, is explicitly deferred
(rome_mud_todo.md) until this mechanical core is proven out live.

Movement, combat, spells and skills are all blocked for an imprisoned
character - see the db.imprisoned checks in world/combat.py's
CombatCharacter.at_pre_move, CmdAttack, CmdCast, CmdUseSkill, CmdFight,
CmdChallenge, CmdDuel, and apply_damage's own no-op - mirroring (not
reusing) world/pacifism.py's model, since db.pacifist itself is a
permanent, self-service, gear-destroying choice that has nothing to do
with a temporary, state-imposed one.
"""

import time

from evennia.scripts.scripts import DefaultScript
from evennia.utils.search import search_tag

from commands.command import Command
from world.crime import CAPITAL_CRIMES, ROME_PROPER_ZONE_TAG, WANTED_CRIMINAL_TAG

CARCER_TAG = ("carcer_cell", "jail")

BASE_SENTENCE_MINUTES = 10
SENTENCE_CAP_MINUTES = 720  # the agreed hard cap: no more than 12 hours

EXECUTION_COUNTDOWN_SECONDS = 5 * 60

CONFISCATION_GOLD_PERCENT = 0.25

# (seconds remaining, private message to the prisoner) - checked in
# descending order by ExecutionScript.at_repeat; each fires once, the
# first tick that crosses its threshold.
EXECUTION_STAGES = [
    (180, "|mYou hear the executioner's footsteps approaching.|n"),
    (
        60,
        "|mYou are moved from your cell to the executioner's block. The "
        "gathered crowd begins to cheer.|n",
    ),
]


def _carcer_room():
    key, category = CARCER_TAG
    rooms = search_tag(key, category=category)
    return rooms[0] if rooms else None


def compute_sentence_minutes(perpetrator):
    """
    Escalates with both severity (world.crime.CRIME_WEIGHTS) and repeat-
    offense count on the perpetrator's own permanent crime_record - a
    single theft (10 * 2 = 20min) or a single assault (10 * 3 = 30min)
    both start modest, but every prior non-capital conviction doubles the
    total on top of that, reaching the 12-hour cap by the third or fourth
    offense. Capital crimes never reach this function at all - a homo
    sacer prisoner goes straight to execution instead (see imprison()).
    """
    record = perpetrator.db.crime_record or []
    non_capital = [c for c in record if c["type"] not in CAPITAL_CRIMES]
    if not non_capital:
        return BASE_SENTENCE_MINUTES

    weight_sum = sum(c.get("weight", 1) for c in non_capital)
    minutes = BASE_SENTENCE_MINUTES * weight_sum * (2 ** max(0, len(non_capital) - 1))
    return min(minutes, SENTENCE_CAP_MINUTES)


def confiscate(defender):
    """
    A flat share of current gold, on every capture, plus - for a
    condemned murderer specifically - every equipped weapon and piece of
    armor, seized outright rather than merely dropped (matching world/
    pacifism.py's own reasoning for destroying gear on that transition:
    leaving it in the world at all just means it gets picked back up or
    minded by someone else). An ordinary (non-capital) prisoner keeps
    their gear - they're getting it back when their sentence ends.
    """
    gold = defender.db.gold or 0
    taken = int(gold * CONFISCATION_GOLD_PERCENT)
    if taken > 0:
        defender.db.gold = gold - taken
        defender.msg("|rThe state confiscates %d gold from you.|n" % taken)

    if defender.db.homo_sacer:
        from world.combat import COMBAT_RULES, _equipped_items, _unequip_item

        seized = []
        for item, attr_name in list(_equipped_items(defender).items()):
            _unequip_item(defender, item, attr_name, COMBAT_RULES)
            seized.append(item.key)
            item.delete()
        if seized:
            defender.msg(
                "|rYour arms and armor are stripped from you and seized "
                "by the state: %s.|n" % ", ".join(seized)
            )


def imprison(defender):
    """
    The one entry point into jail - called by world.guards.capture() the
    instant a guard's blow drops a wanted/homo-sacer target to 1 HP.
    Confiscates, moves the prisoner to the holding cell, sets
    db.imprisoned, and starts whichever timer applies: ExecutionScript
    for a convicted murderer, or an ordinary JailScript (sentence length
    from compute_sentence_minutes) for anyone else.
    """
    confiscate(defender)

    defender.db.imprisoned = True
    cell = _carcer_room()
    if cell:
        defender.move_to(cell, quiet=False, move_type="teleport", force_move=True)
    defender.msg("|rYou are dragged in chains to a cell beneath the city.|n")

    if defender.db.homo_sacer:
        defender.msg(
            "|rYou have been condemned to death for murder. There will be "
            "no reprieve.|n"
        )
        defender.db.execution_at = time.time() + EXECUTION_COUNTDOWN_SECONDS
        defender.db.execution_stages_done = []
        defender.scripts.add(ExecutionScript)
    else:
        minutes = compute_sentence_minutes(defender)
        defender.db.imprisoned_until = time.time() + minutes * 60
        defender.msg(
            "|yYou are sentenced to %d minute(s) in the Carcer for your "
            "crimes. Bread and water will be brought to you.|n" % minutes
        )
        defender.scripts.add(JailScript)


def release(defender):
    """
    An ordinary sentence, served in full - the only non-execution way
    out. Clears db.wanted and the wanted-board tag, but deliberately NOT
    the permanent crime_record - see compute_sentence_minutes' own
    docstring for why that stays (a repeat offender should still read as
    one on their next arrest).
    """
    defender.db.imprisoned = False
    defender.db.imprisoned_until = None
    defender.db.wanted = False

    key, category = WANTED_CRIMINAL_TAG
    defender.tags.remove(key, category=category)

    defender.msg("|gYour sentence is served. The cell door opens.|n")

    proper_key, proper_category = ROME_PROPER_ZONE_TAG
    rooms = search_tag(proper_key, category=proper_category)
    if rooms:
        defender.move_to(rooms[0], quiet=False, move_type="teleport", force_move=True)


class JailScript(DefaultScript):
    """Ticks toward db.imprisoned_until, then calls release()."""

    def at_script_creation(self):
        self.key = "jail_sentence"
        self.interval = 30
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        prisoner = self.obj
        if not prisoner or not prisoner.pk or not prisoner.db.imprisoned:
            self.stop()
            self.delete()
            return
        if time.time() >= (prisoner.db.imprisoned_until or 0):
            release(prisoner)
            self.stop()
            self.delete()


class ExecutionScript(DefaultScript):
    """
    Ticks toward db.execution_at, firing each staged flavor echo
    (EXECUTION_STAGES, private to the prisoner) as its threshold is
    crossed, then - at zero - a real, Rome-proper-wide broadcast
    (world.crime's own _announce_rome_proper) followed by
    COMBAT_RULES.handle_player_defeat(prisoner, attacker=None), the exact
    same death path a PvP or PvE kill already uses. This is the ONLY
    place db.homo_sacer is ever cleared - see world/crime.py's own
    module docstring.
    """

    def at_script_creation(self):
        self.key = "execution_countdown"
        self.interval = 15
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        prisoner = self.obj
        if not prisoner or not prisoner.pk or not prisoner.db.imprisoned:
            self.stop()
            self.delete()
            return

        remaining = (prisoner.db.execution_at or 0) - time.time()
        done = prisoner.db.execution_stages_done or []
        for threshold, message in EXECUTION_STAGES:
            if remaining <= threshold and threshold not in done:
                prisoner.msg(message)
                done.append(threshold)
        prisoner.db.execution_stages_done = done

        if remaining > 0:
            return

        from world.combat import COMBAT_RULES
        from world.crime import _announce_rome_proper

        _announce_rome_proper(
            "|R%s is put to death before the crowd for murder against the "
            "Republic.|n" % prisoner.key
        )

        # Cleared BEFORE handle_player_defeat, not after - that call's
        # own resurrection/respawn relocation needs to actually move the
        # prisoner, and CombatCharacter.at_pre_move's db.imprisoned check
        # would otherwise silently block it.
        prisoner.db.imprisoned = False
        prisoner.db.homo_sacer = False
        key, category = WANTED_CRIMINAL_TAG
        prisoner.tags.remove(key, category=category)

        COMBAT_RULES.handle_player_defeat(prisoner, attacker=None)
        self.stop()
        self.delete()


class CmdWanted(Command):
    """
    See who Rome has marked for justice.

    Usage:
      wanted

    Lists everyone currently wanted or condemned (homo sacer) anywhere
    in the game right now - standing and status only, no location
    tracking. A city guard will move against any of these on sight,
    anywhere in Rome proper.
    """

    key = "wanted"
    help_category = "general"

    def func(self):
        caller = self.caller
        key, category = WANTED_CRIMINAL_TAG
        wanted = search_tag(key, category=category)
        if not wanted:
            caller.msg("The wanted board is empty - Rome is, for now, at peace.")
            return

        lines = ["|wTHE WANTED BOARD|n"]
        for person in wanted:
            if person.db.homo_sacer:
                status = "|rMURDERER - condemned, to be executed|n"
            else:
                status = "wanted"
            if person.db.imprisoned:
                status += " (currently held in the Carcer)"
            lines.append("  %s - %s" % (person.key, status))
        caller.msg("\n".join(lines))
