"""
Rome combat system

Merged turn-based combat system combining weapons/armor (equip),
usable items and status conditions (items), and spellcasting (magic)
into a single, unified system. Adapted from Evennia's 'turnbattle'
contrib (Tim Ashley Jenkins 2017, refactor by Griatch 2022) by hunter.

Three resources are tracked per character:
    HP (Hit Points)    - health. Reaching 0 means defeat.
    MP (Magic Points)  - spent casting spells (see SPELLS below).
    SP (Stamina Points) - spent on physical special moves, currently
                           used by the 'powerattack' command.

To install:
    In typeclasses/characters.py:
        from world.combat import CombatCharacter
        class Character(CombatCharacter):
            ...

    In commands/default_cmdsets.py:
        from world import combat
        ...
        self.add(combat.BattleCmdSet())

    (Only ONE BattleCmdSet should ever be added - this file replaces
    tb_basic, tb_equip, tb_items, and tb_magic's separate cmdsets.)
"""

from random import randint

from evennia import TICKER_HANDLER as tickerhandler
from evennia import DefaultScript, create_object, create_script
from evennia.objects.objects import DefaultCharacter, DefaultObject
from evennia.contrib.rpg.rpsystem import ContribRPCharacter, CmdMask
from commands.command import Command
from commands.command import MuxCommand
from evennia.commands.default.help import CmdHelp
from evennia.commands.default.cmdset_character import CharacterCmdSet
from evennia.commands.default.account import CmdQuit as DefaultCmdQuit
from evennia.prototypes.spawner import spawn
from evennia.utils.logger import log_trace

"""
----------------------------------------------------------------------------
OPTIONS
----------------------------------------------------------------------------
"""

TURN_TIMEOUT = 30  # Time before turns automatically end, in seconds
ACTIONS_PER_TURN = 1  # Number of actions allowed per turn
NONCOMBAT_TURN_TIME = 30  # Time per turn count out of combat (for condition tickdown)

# Condition modifiers
REGEN_RATE = (4, 8)
POISON_RATE = (4, 8)
ACC_UP_MOD = 25
ACC_DOWN_MOD = -25
DMG_UP_MOD = 5
DMG_DOWN_MOD = -5
DEF_UP_MOD = 15
DEF_DOWN_MOD = -15

# ----------------------------------------------------------------------------
# WEAPON PROFICIENCY
# ----------------------------------------------------------------------------
# Which weapon categories each class handles at full effectiveness. Using
# a weapon outside your class's proficiencies still works - nothing is
# ever fully blocked by this - but carries a real accuracy and damage
# penalty, so picking up a stranger's greatsword as an Augur is a
# meaningfully worse idea than fighting with your own ritual staff.
CLASS_WEAPON_PROFICIENCIES = {
    "augur": ["staff", "light_blade"],
    "medicus": ["staff", "light_blade"],
    "haruspex": ["staff", "light_blade"],
    "speculator": ["light_blade", "ranged"],
    "venator": ["ranged", "polearm"],
    "gladiator": ["light_blade", "heavy_blade", "polearm"],
    "legionary": ["light_blade", "heavy_blade", "polearm"],
    "barbarian": ["heavy_weapon", "heavy_blade"],
}

NONPROFICIENT_ACCURACY_PENALTY = -20

# How strongly the relevant stat (Agilitas for physical attacks,
# Ingenium for offensive spells) swings hit chance, applied to the
# raw stat difference from baseline (e.g. Ingenium 16 vs baseline 10
# = a difference of 6, times this multiplier). Calibrated so a
# maximally-invested attacker (race + class both pushing the same
# stat, currently capping at 16) hits a genuinely weak-defense target
# roughly 90%+ of the time, rather than barely nudging past a
# coinflip - a deliberate design choice that race/class investment
# should swing whether an attack connects at all, not just its
# damage. Applied identically in get_attack, spell_attack, and
# skill_attack so all three scale the same way.
ACCURACY_STAT_MULTIPLIER = 7

# Defender-side accuracy penalties (see get_attack) for Augur's
# Veil of Night and Illusory Duplicate spells.
INVISIBLE_ACCURACY_PENALTY = -40
ILLUSION_ACCURACY_PENALTY = -30

# Sanctuary (Medicus mythic-tier spell). A higher-level attacker has
# this percent chance to break through and drag a Sanctuary'd
# character into a fight anyway - but if they succeed, their own
# outgoing damage is halved for the rest of that fight, via the
# "Sanctuary Broken" condition.
SANCTUARY_BREAK_CHANCE = 30
SANCTUARY_DURATION = 3600  # 1 real hour, in seconds

# Personal-instance NPC safety net (see spawn_personal_npc/InstanceCleanupTimer)
INSTANCE_CLEANUP_TIMEOUT = 600  # 10 minutes, in seconds

# Rite of the Entrails (Haruspex). A cursed target takes extra damage
# from all sources for the condition's duration.
CURSED_DAMAGE_MULTIPLIER = 1.3

# Speculator's Ambush (one-time bonus on the next successful
# attack) and Deathmark (guaranteed hit + bonus damage, mythic
# tier). Both consumed the moment they trigger, not normal multi-turn
# conditions.
AMBUSH_DAMAGE_BONUS = 20
MARKED_FOR_DEATH_DAMAGE_BONUS = 35

# Gladiator's Riposte - flat counter-damage dealt back at whoever
# lands a hit while Riposte Ready is active.
RIPOSTE_COUNTER_DAMAGE = 20
NONPROFICIENT_DAMAGE_MULTIPLIER = 0.75  # 25% damage reduction

# Power Attack (SP-based melee special move) options
POWERATTACK_SP_COST = 10
POWERATTACK_DAMAGE_BONUS = 15  # Flat bonus damage added on top of normal weapon/unarmed damage
POWERATTACK_ACCURACY_PENALTY = -15  # Harder to land than a normal attack

# Crowd reactions in rooms tagged 'spectacle' (category 'colosseum' -
# currently Arena Sands and The Master's Sands). Fires from apply_damage
# and at_defeat so every damage path (basic attack, spell, skill, item)
# gets the same lively crowd, without duplicating the check three times.
# Hits use a chance so a multi-round fight doesn't spam a line every
# single swing; a kill is rare and climactic enough to always fire.
SPECTATOR_HIT_CHANCE = 35
SPECTATOR_HIT_LINES = [
    "The crowd roars as the blow connects!",
    "A cheer rises from the stands!",
    "Someone in the tiers lets out a sharp whistle.",
    '"Finish him!" someone shouts from the crowd.',
    "The crowd gasps at the force of the strike.",
    "Spectators lean over the railing for a better look.",
    "A ripple of excitement runs through the watching crowd.",
]
SPECTATOR_KILL_LINES = [
    "The crowd erupts into thunderous applause!",
    "A roar of approval shakes the stands as the bout ends.",
    "Somewhere above, bets are already being placed on the next match.",
    "The crowd stamps its feet in a deafening ovation.",
    "Cheering rolls down from the tiers in waves.",
    '"Another one down!" someone crows from the stands.',
]

# ----------------------------------------------------------------------------
# LEVELING CURVE
# ----------------------------------------------------------------------------
# xp_for_level(level) = LEVEL_XP_BASE * level^LEVEL_XP_EXPONENT gives the XP
# needed to advance FROM that level to the next one. Tuned so levels 1-10
# (the only content that currently exists, via the Ludus training ground)
# come at a fast, satisfying pace. Levels 11-100 use the same formula so
# the system fully works, but that end of the curve is a placeholder -
# there's no content built yet to actually level through up there, so
# don't treat these numbers as final until there's been real playtesting
# against real high-level content.
# How gold rewards derive from xp_reward - dividing by 3 gives a
# range of roughly 5 gold (lowest Ludus tier, xp_reward 15) up to
# ~183 gold (Arena Master, xp_reward 550), a modest early-game amount
# that scales up meaningfully without needing separate hand-tuning
# per NPC.
GOLD_PER_XP_DIVISOR = 3

LEVEL_XP_BASE = 20
LEVEL_XP_EXPONENT = 1.9
MAX_LEVEL = 100  # 101 ("God") is assigned manually, never earned via XP

# Rank titles shown in place of raw level numbers (e.g. on 'who'). Bands
# chosen to line up with the Skills & Spells tier system on the website
# (Novice/Adept/Veteran/Master/Grand Master). Levels 101+ (the "Cursus
# Divinorum" god tiers) are handled separately via GOD_TIERS below.
RANK_TITLES = [
    (90, "Grand Master"),
    (60, "Master"),
    (35, "Veteran"),
    (15, "Adept"),
    (1, "Novice"),
]

# The god tier ladder. Each level maps to (title, permission) - the
# Evennia Permission string automatically granted/revoked alongside
# that level by CmdGodLevel, so a character's displayed rank and their
# actual command access always move together instead of being two
# separately-maintained facts. 101 and 106 have no permission of their
# own: 101 ("Novus Deus") is a genuine probationary rung - immortal
# and RP-significant, but no real admin commands yet, matching what
# level 101 already did before this system existed. 106 ("Rex Divum")
# is never assigned by any command at all - it exists only to label
# whichever character already is a true Django superuser (currently
# Jupiter/#1), since a true superuser bypasses every lock unconditionally
# regardless of anything in this table (see CLAUDE.md gotcha #6).
GOD_TIERS = {
    101: ("Novus Deus", None),
    102: ("Auspex", "Helper"),
    103: ("Aedilis", "Builder"),
    104: ("Praeses", "Admin"),
    105: ("Numen Regnant", "Developer"),
    106: ("Rex Divum", None),
}


def rank_title(level):
    """
    Returns the rank title for a given level. Level 100 exactly gets
    its own unique title ("Legend") rather than sharing "Grand Master"
    with the rest of the 90-99 band - the single highest level a
    mortal can reach deserves to stand apart from mere skill tiers.
    Levels 101+ pull their title from GOD_TIERS; anything past 106
    (shouldn't normally happen) falls back to the top tier's title
    rather than crashing.
    """
    if level is None:
        level = 1
    if level > 100:
        tier = GOD_TIERS.get(level, GOD_TIERS[106])
        return tier[0]
    if level == 100:
        return "Legend"
    for threshold, title in RANK_TITLES:
        if level >= threshold:
            return title
    return "Novice"


def derive_npc_stats(race_key, class_key, level):
    """
    Computes HP/MP/SP and core stats for an NPC using the exact same
    formulas real player characters go through at chargen and on
    level-up - base stats + race stat_mods + class stat_mods +
    per-level growth. Returns a plain dict, ready to merge into a
    prototype or apply directly to a spawned object's attributes.

    This is what makes "a level 15 Minotaur Barbarian" NPC actually
    hit like a real level 15 Minotaur Barbarian player would, instead
    of a hand-picked number with no real connection to the leveling
    system - closes the exact gap flagged when 'consider' was built.

    race_key/class_key can be None for NPCs that aren't meant to be a
    "real" playable-archetype character at all (beasts, spirits,
    generic mooks) - in that case this just returns the flat level-1
    baseline scaled by level, no race/class bonuses layered on.
    """
    from world.chargen_menu import RACES, CLASSES

    virtus = agilitas = ingenium = vigor = 10
    max_hp, max_mp, max_sp = 100, 20, 30

    if race_key and race_key in RACES:
        mods = RACES[race_key]["stat_mods"]
        max_hp += mods["max_hp"]
        max_mp += mods["max_mp"]
        max_sp += mods["max_sp"]
        virtus += mods.get("virtus", 0)
        agilitas += mods.get("agilitas", 0)
        ingenium += mods.get("ingenium", 0)
        vigor += mods.get("vigor", 0)

    if class_key and class_key in CLASSES:
        class_mods = CLASSES[class_key].get("stat_mods", {})
        virtus += class_mods.get("virtus", 0)
        agilitas += class_mods.get("agilitas", 0)
        ingenium += class_mods.get("ingenium", 0)
        vigor += class_mods.get("vigor", 0)

    # Vigor/Ingenium feed a small amount into Max HP/MP, same formula
    # used at chargen - see world/chargen_menu.py _apply_race_and_class.
    max_hp += (vigor - 10) * 2
    max_mp += (ingenium - 10) * 2

    levels_gained = max(0, level - 1)
    max_hp += levels_gained * LEVEL_UP_HP_GAIN
    max_mp += levels_gained * LEVEL_UP_MP_GAIN
    max_sp += levels_gained * LEVEL_UP_SP_GAIN

    return {
        "level": level,
        "hp": max_hp,
        "max_hp": max_hp,
        "mp": max_mp,
        "max_mp": max_mp,
        "sp": max_sp,
        "max_sp": max_sp,
        "virtus": virtus,
        "agilitas": agilitas,
        "ingenium": ingenium,
        "vigor": vigor,
        "player_class": class_key,
        "race": race_key,
    }

# Roughly how much max HP/MP/SP a character gains per level-up.
LEVEL_UP_HP_GAIN = 8
LEVEL_UP_MP_GAIN = 3
LEVEL_UP_SP_GAIN = 4

# Chance (out of 100) that a 'disengage' attempt actually succeeds.
# Failing still costs the full turn - you don't get a free retry.
DISENGAGE_SUCCESS_CHANCE = 55

"""
----------------------------------------------------------------------------
COMBAT RULES - MERGED
----------------------------------------------------------------------------
"""


class CombatRules:
    """
    Stores all combat rules and helper methods. Combines equipment
    (weapons/armor), items/conditions, and magic (spells) into one
    unified ruleset.
    """

    # ------------------------------------------------------------------
    # CORE ROLLS
    # ------------------------------------------------------------------

    def roll_init(self, character):
        """
        Rolls initiative - higher goes first. Agilitas gives a real,
        meaningful edge (each point adds a few points to the roll) but
        doesn't remove the randomness entirely - a high-Agilitas
        character is more likely to go early, not guaranteed to.
        """
        agilitas = character.db.agilitas or 10
        return randint(1, 1000) + (agilitas * 3)

    def get_conditions(self, character):
        """
        Safely returns a character's conditions dict, initializing it
        to an empty dict if missing. This lets simple objects (like a
        training dummy or a monster that isn't a full CombatCharacter)
        join combat without crashing on condition checks.
        """
        if character.db.conditions is None:
            character.db.conditions = {}
        return character.db.conditions

    def is_ally(self, character, other):
        """
        Whether 'other' should be treated as an ally of 'character'
        for targeting purposes - prefers actual combat_side (who
        you're really fighting with/against in THIS fight) when
        character is currently in combat, falling back to party
        membership when they're not.

        This distinction matters: combat_side and party membership
        usually agree, but not always - two party members could end
        up dueling each other for sport, in which case they're
        allies in the party system but genuinely opposed in this
        specific fight. Using combat_side when available means AoE
        spells/skills correctly avoid hitting a real ally without
        also incorrectly protecting a party member you're actually
        fighting right now.
        """
        side = character.db.combat_side
        if side is not None:
            return other.db.combat_side == side
        from world.party import get_party_members

        return other in get_party_members(character)

    def try_break_sanctuary(self, attacker, defender):
        """
        Checks whether attacker can drag a Sanctuary'd defender into a
        fight (Medicus's mythic-tier Sanctuary spell). Equal-or-lower-
        level attackers can never break through - Sanctuary holds
        completely. Higher-level attackers have SANCTUARY_BREAK_CHANCE
        percent odds to break through anyway, but pay for it: their
        own outgoing damage is halved for the rest of that fight (see
        the "Sanctuary Broken" check in get_damage). Returns True if
        the fight can proceed against this defender - either there's
        no active Sanctuary, or the attacker broke through it.
        """
        if not defender.db.sanctuary_active:
            return True

        attacker_level = attacker.db.level or 1
        sanctuary_level = defender.db.sanctuary_level or (defender.db.level or 1)

        if attacker_level <= sanctuary_level:
            attacker.msg(
                "%s is protected by Sanctuary - you can't draw them into a fight."
                % defender.key
            )
            return False

        if randint(1, 100) <= SANCTUARY_BREAK_CHANCE:
            attacker.location.msg_contents(
                "%s tears through %s's Sanctuary by sheer force!" % (attacker, defender)
            )
            # Duration 99 is a practical "lasts the rest of this fight"
            # value - no realistic fight runs 99 rounds, and this
            # reuses the existing per-turn condition system rather
            # than needing a dedicated "until combat ends" duration
            # type just for this one spell.
            self.add_condition(attacker, attacker, "Sanctuary Broken", 99)
            return True

        attacker.msg("You try to break %s's Sanctuary, but it holds." % defender.key)
        return False

    def is_proficient(self, character, weapon):
        """
        Returns True if character's class is proficient with the given
        weapon's category. Characters with no wielded weapon (fighting
        unarmed) or no player_class set (NPCs) are always treated as
        proficient - this check only ever applies to an actual class
        using an actual weapon.
        """
        if not weapon:
            return True
        char_class = character.db.player_class
        if not char_class:
            return True
        proficiencies = CLASS_WEAPON_PROFICIENCIES.get(char_class)
        if not proficiencies:
            return True
        return weapon.db.weapon_category in proficiencies

    def get_attack(self, attacker, defender):
        """
        Attack roll. Factors in:
            - Wielded weapon's accuracy bonus, or unarmed accuracy
            - Accuracy Up / Accuracy Down conditions
            - A penalty if using a weapon outside your class's
              proficiencies
        """
        attack_value = randint(1, 100)
        attack_value += ((attacker.db.agilitas or 10) - 10) * ACCURACY_STAT_MULTIPLIER

        if attacker.db.wielded_weapon:
            attack_value += attacker.db.wielded_weapon.db.accuracy_bonus
            if not self.is_proficient(attacker, attacker.db.wielded_weapon):
                attack_value += NONPROFICIENT_ACCURACY_PENALTY
        else:
            attack_value += attacker.db.unarmed_accuracy or 0

        if "Accuracy Up" in self.get_conditions(attacker):
            attack_value += ACC_UP_MOD
        if "Accuracy Down" in self.get_conditions(attacker):
            attack_value += ACC_DOWN_MOD

        # Defender-side conditions - unlike the two above (which are
        # about the attacker's own state), these belong to the
        # defender but still affect how hard THEY are to hit. Used by
        # Augur's Veil of Night (invisibility) and Illusory Duplicate.
        if "Invisible" in self.get_conditions(defender):
            attack_value += INVISIBLE_ACCURACY_PENALTY
        if "Illusory Duplicate" in self.get_conditions(defender):
            attack_value += ILLUSION_ACCURACY_PENALTY

        return attack_value

    def get_defense(self, attacker, defender):
        """
        Defense value. Factors in:
            - Worn armor's defense modifier
            - Defense Up / Defense Down conditions
        """
        defense_value = 50
        defense_value += (defender.db.agilitas or 10) - 10

        if defender.db.worn_armor:
            defense_value += defender.db.worn_armor.db.defense_modifier

        if "Defense Up" in self.get_conditions(defender):
            defense_value += DEF_UP_MOD
        if "Defense Down" in self.get_conditions(defender):
            defense_value += DEF_DOWN_MOD

        return defense_value

    def get_damage(self, attacker, defender):
        """
        Damage roll. Factors in:
            - Wielded weapon's damage range, or unarmed damage range
            - Worn armor's damage reduction (on the defender)
            - Damage Up / Damage Down conditions
            - A penalty if using a weapon outside your class's
              proficiencies
        """
        if attacker.db.wielded_weapon:
            weapon = attacker.db.wielded_weapon
            damage_value = randint(weapon.db.damage_range[0], weapon.db.damage_range[1])
            if not self.is_proficient(attacker, weapon):
                damage_value = int(damage_value * NONPROFICIENT_DAMAGE_MULTIPLIER)

            # Virtus (raw strength) powers heavy/melee weapons; Agilitas
            # (finesse/precision) powers ranged and light blade weapons
            # instead - keeps a high-Agilitas Speculator or Venator
            # benefiting from their own stat investment, not just
            # heavy-hitting classes.
            category = weapon.db.weapon_category
            if category in ("ranged", "light_blade"):
                damage_value += ((attacker.db.agilitas or 10) - 10) // 2
            else:
                damage_value += ((attacker.db.virtus or 10) - 10) // 2
        else:
            dmg_range = attacker.db.unarmed_damage_range or (5, 15)
            damage_value = randint(dmg_range[0], dmg_range[1])
            damage_value += ((attacker.db.virtus or 10) - 10) // 2

        if defender.db.worn_armor:
            damage_value -= defender.db.worn_armor.db.damage_reduction

        # Vigor (constitution/toughness) - a small flat reduction on
        # top of whatever armor provides, independent of it.
        damage_value -= ((defender.db.vigor or 10) - 10) // 3

        if "Damage Up" in self.get_conditions(attacker):
            damage_value += DMG_UP_MOD
        if "Damage Down" in self.get_conditions(attacker):
            damage_value += DMG_DOWN_MOD
        if "Sanctuary Broken" in self.get_conditions(attacker):
            damage_value = int(damage_value * 0.5)

        # Defender-side amplifier - unlike the two above (about the
        # attacker's own state), this belongs to the defender but
        # still increases how much they suffer. Used by Haruspex's
        # Rite of the Entrails.
        if "Cursed" in self.get_conditions(defender):
            damage_value = int(damage_value * CURSED_DAMAGE_MULTIPLIER)

        if "Ambush" in self.get_conditions(attacker):
            del self.get_conditions(attacker)["Ambush"]
            damage_value += AMBUSH_DAMAGE_BONUS

        if "Marked for Death" in self.get_conditions(defender):
            del self.get_conditions(defender)["Marked for Death"]
            damage_value += MARKED_FOR_DEATH_DAMAGE_BONUS

        if damage_value < 0:
            damage_value = 0

        return damage_value

    def apply_damage(self, defender, damage, attacker=None):
        """
        Applies damage to a target, reducing their HP by the damage
        amount to a minimum of 0. Characters with db.invincible = True
        take no damage at all - useful for gods, admin test characters,
        or story-critical NPCs that should never be defeated in combat.

        Also checks for the "Death Ward" condition (Medicus's Ward
        Against Death spell) - if present and this hit would otherwise
        be fatal, the ward is consumed instead and the defender is left
        at 1 HP rather than falling.

        The attacker parameter is used both by Gladiator's Riposte and
        to track per-attacker damage contribution (db.damage_log) for
        splitting XP fairly when the defender is eventually defeated -
        every real damage source now passes this, not just direct
        physical attacks.
        """
        if defender.db.invincible:
            return

        would_be_lethal = (defender.db.hp - damage) <= 0
        if would_be_lethal and "Death Ward" in self.get_conditions(defender):
            del self.get_conditions(defender)["Death Ward"]
            defender.db.hp = 1
            defender.location.msg_contents(
                "|Y%s should have fallen, but a lingering ward holds them back "
                "from death's door!|n" % defender
            )
            return

        if "Shielded" in self.get_conditions(defender):
            del self.get_conditions(defender)["Shielded"]
            defender.location.msg_contents(
                "|Y%s's protective ward absorbs the blow entirely!|n" % defender
            )
            return

        defender.db.hp -= damage
        if defender.db.hp <= 0:
            defender.db.hp = 0

        if attacker and damage > 0:
            damage_log = defender.db.damage_log or {}
            damage_log[attacker] = damage_log.get(attacker, 0) + damage
            defender.db.damage_log = damage_log
            self.spectator_react(defender.location, SPECTATOR_HIT_LINES, SPECTATOR_HIT_CHANCE)

        # Riposte (Gladiator) - a genuine reactive trigger, unlike
        # every other condition check in this method: it doesn't
        # prevent or reduce the incoming hit at all, it fires AFTER
        # taking it, striking back at whoever dealt it. Only fires if
        # the caller passed a real attacker (see docstring above) and
        # the defender is still standing.
        if (
            attacker
            and defender.db.hp > 0
            and "Riposte Ready" in self.get_conditions(defender)
        ):
            del self.get_conditions(defender)["Riposte Ready"]
            defender.location.msg_contents(
                "%s takes the hit and answers immediately with a riposte!" % defender
            )
            self.apply_damage(attacker, RIPOSTE_COUNTER_DAMAGE)

    def spectator_react(self, location, lines, chance=100):
        """
        Fires a random crowd-reaction line into `location`, but only if
        it's tagged 'spectacle' (category 'colosseum') - so ambient
        crowd noise stays confined to actual arena floors (Arena Sands,
        The Master's Sands) rather than bleeding into the Ludus training
        grounds or anywhere else combat happens to occur.
        """
        if not location or not location.tags.has("spectacle", category="colosseum"):
            return
        if randint(1, 100) > chance:
            return
        location.msg_contents(lines[randint(0, len(lines) - 1)])

    def at_defeat(self, defeated, attacker=None):
        """
        Announces defeat, and handles two special cases:
          - If the defeated object is tagged 'colosseum_trainer' and an
            attacker is known, the attacker earns their freedom (used by
            the Colosseum escape questline in world/colosseum.py).
          - If the defeated object is an actual player character (has a
            connected .account), handles death/respawn based on level.
        """
        display_name = defeated.db.base_name or defeated.key
        if defeated.location:
            defeated.location.msg_contents("%s has been defeated!" % display_name)
            self.spectator_react(defeated.location, SPECTATOR_KILL_LINES)

        # --- Colosseum escape-on-victory ---
        if attacker and defeated.tags.has("colosseum_trainer", category="npc_role"):
            if not attacker.db.colosseum_escaped:
                attacker.db.colosseum_escaped = True
                from evennia.contrib.game_systems.achievements import track_achievements
                from world.achievements import announce_achievements
                completed = track_achievements(attacker, category="colosseum", tracking="escaped")
                announce_achievements(attacker, completed)
                attacker.msg(
                    "|yWith a final blow, you defeat the trainer - the crowd roars! "
                    "You have earned your freedom.|n\n"
                    "|yGo |weast|y through the Gate of Life to reach the Atrium of "
                    "the Games. From there, the Ludus lies |weast|y - head there when "
                    "you're ready to keep training.|n"
                )
                attacker.location.msg_contents(
                    "%s has triumphed over the trainer and earned their freedom!" % attacker,
                    exclude=attacker,
                )

        # --- Generic "any NPC defeated" achievement tracking ---
        # Covers first_blood/battle_hardened - fires for any attacker
        # who defeats any NPC at all, not just the Colosseum trainer.
        # Only tracks real players (has_account) - NPCs occasionally
        # defeat other NPCs (e.g. a summoned ally), and those
        # shouldn't count toward a player's own achievement progress.
        if attacker and attacker.has_account:
            from evennia.contrib.game_systems.achievements import track_achievements
            from world.achievements import announce_achievements
            completed = track_achievements(attacker, category="defeat", tracking="any_npc", count=1)
            announce_achievements(attacker, completed)

        # --- XP reward, for any NPC with an xp_reward attribute set ---
        # Split proportionally by tracked damage contribution (see
        # apply_damage's damage_log), not just awarded whole to
        # whoever landed the killing blow - a group that brings an
        # NPC down together all earn a fair share based on how much
        # they actually contributed, not a winner-take-all race for
        # the last hit. Falls back to the old killing-blow-only
        # behavior only if damage_log is somehow empty (shouldn't
        # normally happen, since apply_damage always logs it now).
        if defeated.db.xp_reward:
            damage_log = defeated.db.damage_log or {}
            total_damage = sum(damage_log.values())
            if total_damage > 0:
                for contributor, dealt in damage_log.items():
                    # See gotcha #2 in CLAUDE.md: a deleted object's
                    # reference, reloaded from a persisted attribute
                    # (damage_log is one), resolves to literal None -
                    # not an object with pk=None. `contributor is
                    # None` must be checked first, same fix already
                    # applied in CombatTurnHandler.next_turn().
                    if contributor is None or not contributor.pk:
                        continue
                    share = int(round(defeated.db.xp_reward * (dealt / total_damage)))
                    if share > 0:
                        self.award_xp(contributor, share)
            elif attacker:
                self.award_xp(attacker, defeated.db.xp_reward)

        # --- Gold reward, derived from xp_reward rather than a
        # separate hand-tuned field per NPC - xp_reward already
        # scales sensibly with an NPC's level/difficulty, so deriving
        # gold from it automatically gives "higher level NPCs award
        # more gold" for free, without duplicating tuning work across
        # every single prototype. Same proportional damage-share
        # split as XP, for the same fairness reasons.
        if defeated.db.xp_reward:
            gold_pool = max(1, defeated.db.xp_reward // GOLD_PER_XP_DIVISOR)
            damage_log = defeated.db.damage_log or {}
            total_damage = sum(damage_log.values())
            if total_damage > 0:
                for contributor, dealt in damage_log.items():
                    if contributor is None or not contributor.pk:
                        continue
                    share = int(round(gold_pool * (dealt / total_damage)))
                    if share > 0:
                        contributor.db.gold = (contributor.db.gold or 0) + share
                        contributor.msg("|Y+%d gold.|n" % share)
            elif attacker:
                attacker.db.gold = (attacker.db.gold or 0) + gold_pool
                attacker.msg("|Y+%d gold.|n" % gold_pool)

        # --- Persistent NPC respawn (see RespawningNPC) - checked
        # BEFORE instance cleanup below, since a respawning NPC is
        # never instance-owned (they're the opposite model: one
        # shared NPC that comes back, not a disposable personal copy)
        if defeated.db.respawns:
            self.schedule_respawn(defeated)
            return

        # --- Personal NPC instance cleanup (see spawn_personal_npc) ---
        if defeated.db.instance_owner:
            defeated.delete()
            return  # nothing left to do - the object no longer exists

        # --- Player death/respawn (skip for NPCs/objects with no account) ---
        if getattr(defeated, "account", None):
            self.handle_player_defeat(defeated, attacker=attacker)

    def schedule_respawn(self, npc):
        """
        Handles a defeated persistent (non-instance) NPC: remembers
        its home room, removes it from play, and starts a real,
        persistent RespawnTimer script that brings it back after a
        delay - not a bare delay() call, since those don't survive a
        server reload, and this needs to reliably happen even if a
        reload occurs while the NPC is waiting to respawn.
        """
        if not npc.db.respawn_home:
            npc.db.respawn_home = npc.location

        npc.location.msg_contents(
            "%s falls, but this is not the end of them." % npc
        )
        # to_none=True is required here - move_to(None) without it
        # doesn't move the object at all (it just messages "The
        # destination doesn't exist." to the NPC itself and returns
        # False, leaving .location completely unchanged). Without this,
        # a defeated respawning NPC never actually left the room at
        # all - it just sat there, visibly still "defeated," for the
        # entire respawn delay, contradicting this method's own
        # "removes it from play" docstring above.
        npc.move_to(None, quiet=True, to_none=True)

        delay = npc.db.respawn_delay or 90
        create_script(
            RespawnTimer,
            key="respawn_%s" % npc.key,
            obj=npc,
            interval=delay,
            start_delay=True,
            persistent=True,
            autostart=True,
        )

    def handle_player_defeat(self, defeated, attacker=None):
        """
        Handles what happens when an actual player character is defeated
        in combat. Level 5 and below: the gods return you to the holding
        cells immediately, no real penalty. Level 6+ actually sends you
        to the Underworld now - is_dead is set, stats are NOT restored,
        and you stay there until you either solve the riddle at the
        Threshold of Return yourself, or a Medicus with the Blessing of
        Asclepius resurrects you. Also costs half your current XP
        progress toward your next level.

        Also cleans up the defeated character's combat state properly -
        removes them from the turn handler's fighter list and clears
        their combat_* attributes - so they don't end up stuck reporting
        as "in combat" (and unable to move) after respawning somewhere
        else entirely.
        """
        from evennia.objects.models import ObjectDB
        from evennia.utils.search import search_tag
        from django.conf import settings

        level = defeated.db.level or 1

        # --- Clean up combat/turn-handler state BEFORE moving anyone ---
        turnhandler = defeated.db.combat_turnhandler
        if turnhandler and turnhandler.pk:
            fighters = turnhandler.db.fighters or []
            if defeated in fighters:
                fighters.remove(defeated)
                turnhandler.db.fighters = fighters

            if not fighters:
                # No one left to fight - just end the encounter cleanly.
                turnhandler.stop()
                turnhandler.delete()
            else:
                # Re-point db.turn at whoever is actually acting right
                # now (the attacker), since removing defeated from the
                # list may have shifted everyone's index down by one.
                if attacker and attacker in fighters:
                    turnhandler.db.turn = fighters.index(attacker)
                elif turnhandler.db.turn >= len(fighters):
                    turnhandler.db.turn = 0

        self.combat_cleanup(defeated)

        if level <= 5:
            # Safe respawn - restore stats and send back to the cells,
            # no penalty at all.
            defeated.db.hp = defeated.db.max_hp
            defeated.db.mp = defeated.db.max_mp
            defeated.db.sp = defeated.db.max_sp

            cells = ObjectDB.objects.get_id(settings.START_LOCATION)
            defeated.msg(
                "|mDarkness takes you... but the gods are not yet done with you.|n"
            )
            if cells:
                defeated.move_to(cells, quiet=False)
                defeated.msg(
                    "You awaken in the holding cells beneath the Colosseum, alive once more."
                )
            return

        # Level 6+: real death. Stats stay at 0 - nothing to restore
        # until they actually make it back.
        defeated.db.is_dead = True
        defeated.db.xp = (defeated.db.xp or 0) // 2

        defeated.msg(
            "|mYou feel your spirit torn from your body, dragged toward a dark river...|n"
        )
        defeated.msg(
            "|mYou are dead. Half your progress toward your next level is gone with you.|n"
        )

        underworld_entrance = search_tag("underworld_entrance", category="underworld")
        if underworld_entrance:
            defeated.db.charon_arrived = False
            # force_move: see CombatCharacter.at_pre_move - this move
            # deliberately happens while hp is still 0, so the normal
            # "can't move while defeated" block must be bypassed here.
            defeated.move_to(underworld_entrance[0], quiet=False, force_move=True)
            defeated.msg(
                "You find yourself on the far shore of a dark river, the world of "
                "the living somewhere behind you now. There is no boat yet - you'll "
                "have to wait for the ferryman."
            )
            # Local import to avoid a circular import - world/underworld.py
            # already imports COMBAT_RULES from this module, so importing
            # it back at module load time here would be a real problem.
            # Deferred to call-time, this is safe.
            from world.underworld import CharonTimer

            defeated.scripts.add(CharonTimer)
        else:
            # Underworld isn't built on this install yet - fail safe
            # rather than leaving a player permanently stuck as dead
            # with nowhere to go.
            defeated.db.is_dead = False
            defeated.db.hp = defeated.db.max_hp
            defeated.db.mp = defeated.db.max_mp
            defeated.db.sp = defeated.db.max_sp
            cells = ObjectDB.objects.get_id(settings.START_LOCATION)
            if cells:
                defeated.move_to(cells, quiet=False)

    def send_to_underworld(self, character):
        """
        Standalone helper for sending an already-dead-in-spirit
        character to the Underworld outside of the normal combat-defeat
        path, if ever needed (e.g. a scripted event). Currently unused
        by anything else, kept for parity with resurrect() below.
        """
        from evennia.utils.search import search_tag

        character.db.is_dead = True
        underworld_entrance = search_tag("underworld_entrance", category="underworld")
        if underworld_entrance:
            character.move_to(underworld_entrance[0], quiet=False)

    def resurrect(self, character):
        """
        Brings a dead character back to the world of the living - fully
        heals them, clears is_dead, and returns them somewhere sensible
        for their experience level. Used by both the Underworld
        riddle-solve return path and Medicus's Blessing of Asclepius
        spell (spell_resurrect below).

        Level 5 and below return to the holding cells beneath the
        Colosseum, same as always - still early enough in the escape
        questline that the cells are the natural "home." Level 6+
        returns to the Temple of Jupiter Optimus Maximus on the
        Capitoline instead (tagged 'capitoline_resurrection_point',
        category 'capitoline') - by that point a character has proven
        themselves enough that being pulled back from death by the
        king of the gods himself, in his own temple, fits better than
        waking up back in a cell.
        """
        from evennia.objects.models import ObjectDB
        from django.conf import settings
        from evennia.utils.search import search_tag

        if not character.db.is_dead:
            return False

        character.db.is_dead = False
        character.db.hp = character.db.max_hp
        character.db.mp = character.db.max_mp
        character.db.sp = character.db.max_sp

        level = character.db.level or 1
        destination = None
        if level >= 6:
            temple = search_tag("capitoline_resurrection_point", category="capitoline")
            if temple:
                destination = temple[0]
                arrival_msg = (
                    "|GLife floods back into you. You awaken within the Temple of "
                    "Jupiter Optimus Maximus, the god's own hall around you, alive "
                    "once more.|n"
                )
        if not destination:
            destination = ObjectDB.objects.get_id(settings.START_LOCATION)
            arrival_msg = (
                "|GLife floods back into you. You awaken in the holding cells "
                "beneath the Colosseum, alive once more.|n"
            )

        if destination:
            character.move_to(destination, quiet=False)
        character.msg(arrival_msg)
        return True

    def resolve_attack(
        self,
        attacker,
        defender,
        attack_value=None,
        defense_value=None,
        damage_value=None,
        inflict_condition=None,
    ):
        """
        Resolves an attack (from the 'attack' command, item use, or a
        spell) and outputs the result. Handles weapon naming and
        condition-on-hit.
        """
        if inflict_condition is None:
            inflict_condition = []

        # Tracks who this attacker most recently went after. Used by
        # summoned allies (Augur's familiar, Haruspex's Lemures,
        # Venator's beast companion) to know who to fight without
        # needing a full team/sides system - they just mirror
        # whoever their owner last attacked. Set centrally here since
        # every attack (player, NPC, or otherwise) flows through this
        # one method.
        attacker.db.combat_last_target = defender

        attackers_weapon = "attack"
        if attacker.db.wielded_weapon:
            attackers_weapon = attacker.db.wielded_weapon.db.weapon_type_name

        # is None (not a plain falsy check) - attack_value/defense_value
        # can legitimately be 0 or negative with enough penalties, and
        # a falsy check would silently recalculate a real 0 as if it
        # had never been provided at all.
        if attack_value is None:
            attack_value = self.get_attack(attacker, defender)
        if defense_value is None:
            defense_value = self.get_defense(attacker, defender)

        # Marked for Death (Speculator's Deathmark) - guarantees
        # this hit lands regardless of the normal accuracy roll, then
        # is consumed. Checked on the DEFENDER, since it's about them
        # having been marked, not about the attacker's own skill.
        if "Marked for Death" in self.get_conditions(defender):
            attacker.location.msg_contents(
                "|Y%s's mark seals %s's fate - the strike cannot be evaded!|n"
                % (attacker, defender)
            )
        elif attack_value < defense_value:
            attacker.location.msg_contents(
                "|w%s's %s misses %s!|n" % (attacker, attackers_weapon, defender)
            )
            return

        if not damage_value:
            damage_value = self.get_damage(attacker, defender)

        if damage_value > 0:
            attacker.location.msg_contents(
                "%s's %s strikes %s for |r%i|n damage - %s %s!"
                % (
                    attacker, attackers_weapon, defender, damage_value,
                    defender, self.hp_status_phrase(defender),
                )
            )
        else:
            attacker.location.msg_contents(
                "|w%s's %s bounces harmlessly off %s!|n" % (attacker, attackers_weapon, defender)
            )

        self.apply_damage(defender, damage_value, attacker=attacker)

        for condition in inflict_condition:
            self.add_condition(defender, attacker, condition[0], condition[1])

        if defender.db.hp <= 0:
            self.at_defeat(defender, attacker=attacker)

    # ------------------------------------------------------------------
    # COMBAT STATE HELPERS
    # ------------------------------------------------------------------

    def hp_status_phrase(self, character, hp_override=None):
        """
        A qualitative description of how hurt a character currently
        looks, based on HP percentage - gives players a real sense of
        whether a fight is going their way, without exposing exact
        numbers (which stay private, visible only via their own
        status line and character sheet).

        hp_override lets a caller show the PROJECTED status after
        damage that hasn't actually been applied yet (spell_attack
        builds its whole message before calling apply_damage in a
        separate pass) - without this, the phrase would describe the
        target's condition before the hit that's being announced,
        which would read as wrong.
        """
        max_hp = character.db.max_hp or 1
        hp = hp_override if hp_override is not None else (character.db.hp or 0)
        hp = max(0, hp)
        pct = hp / max_hp

        if pct >= 1.0:
            return "looks completely unscathed"
        elif pct >= 0.75:
            return "looks lightly wounded"
        elif pct >= 0.5:
            return "looks wounded"
        elif pct >= 0.25:
            return "looks badly wounded"
        else:
            return "looks like they're barely standing"

    def combat_cleanup(self, character):
        """Removes all temporary combat_* attributes from a character."""
        # list() snapshots the attributes before removal starts -
        # iterating character.attributes.all() directly while also
        # removing from it risks skipping entries, a real Python
        # "modify while iterating" bug caught in a code review.
        for attr in list(character.attributes.all()):
            if attr.key[:7] == "combat_":
                character.attributes.remove(key=attr.key)

    def is_in_combat(self, character):
        return bool(character.db.combat_turnhandler)

    def is_turn(self, character):
        turnhandler = character.db.combat_turnhandler
        if not turnhandler or not turnhandler.db.fighters:
            return False
        turn = turnhandler.db.turn
        if turn is None or turn >= len(turnhandler.db.fighters):
            return False
        currentchar = turnhandler.db.fighters[turn]
        return bool(character == currentchar)

    def spend_action(self, character, actions, action_name=None):
        """Spends a character's available combat actions."""
        if action_name:
            character.db.combat_lastaction = action_name
        if actions == "all":
            character.db.combat_actionsleft = 0
        else:
            # (... or 0) guards against combat_actionsleft never
            # having been initialized (or having been cleared by
            # combat_cleanup) - a plain -= would crash with a
            # TypeError against None.
            character.db.combat_actionsleft = (character.db.combat_actionsleft or 0) - actions
            if character.db.combat_actionsleft < 0:
                character.db.combat_actionsleft = 0
        character.db.combat_turnhandler.turn_end_check(character)

    # ------------------------------------------------------------------
    # CONDITIONS
    # ------------------------------------------------------------------

    def condition_tickdown(self, character, turnchar):
        """Ticks down condition durations at the start of turnchar's turn."""
        for key in list(self.get_conditions(character)):
            condition_duration = self.get_conditions(character)[key][0]
            condition_turnchar = self.get_conditions(character)[key][1]
            if condition_duration is not True:
                if condition_turnchar == turnchar:
                    self.get_conditions(character)[key][0] -= 1
                if self.get_conditions(character)[key][0] <= 0:
                    character.location.msg_contents(
                        "%s no longer has the '%s' condition." % (str(character), str(key))
                    )
                    del self.get_conditions(character)[key]

    def add_condition(self, character, turnchar, condition, duration):
        """Adds a condition to a character."""
        self.get_conditions(character).update({condition: [duration, turnchar]})
        character.location.msg_contents("%s gains the '%s' condition." % (character, condition))

    def apply_turn_conditions(self, character):
        """
        Applies conditions that fire at the start of each turn
        (Regeneration, Poisoned, Haste, Paralyzed).
        """
        if "Regeneration" in self.get_conditions(character):
            to_heal = randint(REGEN_RATE[0], REGEN_RATE[1])
            if character.db.hp + to_heal > character.db.max_hp:
                to_heal = character.db.max_hp - character.db.hp
            character.db.hp += to_heal
            character.location.msg_contents(
                "%s regains %i HP from Regeneration." % (character, to_heal)
            )

        if "Poisoned" in self.get_conditions(character):
            to_hurt = randint(POISON_RATE[0], POISON_RATE[1])
            self.apply_damage(character, to_hurt)
            character.location.msg_contents(
                "%s takes %i damage from being Poisoned." % (character, to_hurt)
            )
            if character.db.hp <= 0:
                self.at_defeat(character)

        if self.is_in_combat(character) and "Haste" in self.get_conditions(character):
            character.db.combat_actionsleft += 1
            character.msg("You gain an extra action this turn from Haste!")

        if self.is_in_combat(character) and "Paralyzed" in self.get_conditions(character):
            character.db.combat_actionsleft = 0
            character.location.msg_contents(
                "%s is Paralyzed, and can't act this turn!" % character
            )
            character.db.combat_turnhandler.turn_end_check(character)

    # ------------------------------------------------------------------
    # ITEMS
    # ------------------------------------------------------------------

    def spend_item_use(self, item, user):
        """Spends one use on a limited-use item."""
        item.db.item_uses -= 1

        if item.db.item_uses > 0:
            user.msg("%s has %i uses remaining." % (item.key.capitalize(), item.db.item_uses))
        else:
            if not item.db.item_consumable:
                user.msg("%s has no uses remaining." % item.key.capitalize())
            else:
                if item.db.item_consumable is True:
                    user.msg("%s has been consumed." % item.key.capitalize())
                    item.delete()
                else:
                    residue = spawn({"prototype_parent": item.db.item_consumable})[0]
                    residue.location = item.location
                    user.msg("After using %s, you are left with %s." % (item, residue))
                    item.delete()

    def use_item(self, user, item, target):
        """Performs the action of using an item."""
        if item.db.item_selfonly and target is None:
            target = user

        if item.db.item_selfonly and user != target:
            user.msg("%s can only be used on yourself." % item)
            return

        kwargs = {}
        if item.db.item_kwargs:
            kwargs = item.db.item_kwargs

        try:
            item_func = ITEMFUNCS[item.db.item_func]
        except KeyError:
            user.msg("ERROR: %s not defined in ITEMFUNCS" % item.db.item_func)
            return

        # Every itemfunc_* implementation returns False explicitly on
        # failure, but has no explicit `return True` on success - it
        # just falls off the end, returning None. `if not item_func(...)`
        # treated that None (a successful use!) the same as an actual
        # False failure, so spend_item_use/spend_action below were
        # skipped on EVERY successful item use - items never consumed
        # a use (making limited-use/consumable items effectively
        # infinite) and never spent the user's combat action (a free
        # action every turn). `is False` only stops here on the
        # itemfuncs' real, explicit failure signal.
        if item_func(item, user, target, **kwargs) is False:
            return

        if item.db.item_uses:
            self.spend_item_use(item, user)

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="item")

    def itemfunc_heal(self, item, user, target, **kwargs):
        """Item function that heals HP."""
        if not target:
            target = user

        if not target.attributes.has("max_hp"):
            user.msg("You can't use %s on that." % item)
            return False

        if target.db.hp >= target.db.max_hp:
            user.msg("%s is already at full health." % target)
            return False

        min_healing, max_healing = 20, 40
        if "healing_range" in kwargs:
            min_healing, max_healing = kwargs["healing_range"]

        to_heal = randint(min_healing, max_healing)
        if target.db.hp + to_heal > target.db.max_hp:
            to_heal = target.db.max_hp - target.db.hp
        target.db.hp += to_heal

        user.location.msg_contents("%s uses %s! %s regains %i HP!" % (user, item, target, to_heal))

    def itemfunc_add_condition(self, item, user, target, **kwargs):
        """Item function that gives the target one or more conditions."""
        conditions = kwargs.get("conditions", [("Regeneration", 5)])

        if not target:
            target = user

        if not target.attributes.has("max_hp"):
            user.msg("You can't use %s on that." % item)
            return False

        user.location.msg_contents("%s uses %s!" % (user, item))

        for condition in conditions:
            self.add_condition(target, user, condition[0], condition[1])

    def itemfunc_cure_condition(self, item, user, target, **kwargs):
        """Item function that removes given conditions from a target."""
        to_cure = kwargs.get("to_cure", ["Poisoned"])

        if not target:
            target = user

        if not target.attributes.has("max_hp"):
            user.msg("You can't use %s on that." % item)
            return False

        item_msg = "%s uses %s! " % (user, item)

        for key in list(self.get_conditions(target)):
            if key in to_cure:
                item_msg += "%s no longer has the '%s' condition. " % (str(target), str(key))
                del self.get_conditions(target)[key]

        user.location.msg_contents(item_msg)

    def itemfunc_attack(self, item, user, target, **kwargs):
        """Item function that attacks a target."""
        if not self.is_in_combat(user):
            user.msg("You can only use that in combat.")
            return False

        if not target:
            user.msg("You have to specify a target to use %s! (use <item> = <target>)" % item)
            return False

        if target == user:
            user.msg("You can't attack yourself!")
            return False

        if not target.db.hp:
            user.msg("You can't use %s on that." % item)
            return False

        min_damage = kwargs.get("damage_range", (20, 40))[0]
        max_damage = kwargs.get("damage_range", (20, 40))[1]
        accuracy = kwargs.get("accuracy", 0)
        inflict_condition = kwargs.get("inflict_condition", [])

        attack_value = randint(1, 100) + accuracy
        damage_value = randint(min_damage, max_damage)

        if "Accuracy Up" in self.get_conditions(user):
            attack_value += ACC_UP_MOD
        if "Accuracy Down" in self.get_conditions(user):
            attack_value += ACC_DOWN_MOD

        user.location.msg_contents("%s attacks %s with %s!" % (user, target, item))
        self.resolve_attack(
            user,
            target,
            attack_value=attack_value,
            damage_value=damage_value,
            inflict_condition=inflict_condition,
        )

    # ------------------------------------------------------------------
    # SPELLS
    # ------------------------------------------------------------------

    def spell_healing(self, caster, spell_name, targets, cost, **kwargs):
        """
        Spell that restores HP to a target or targets. Supports either
        a flat healing_range (min, max) or a heal_percent (e.g. 0.5 for
        50% of the target's own max HP) - used by Greater Restoration,
        where a flat number wouldn't scale sensibly across wildly
        different max HP totals at different levels.
        """
        spell_msg = "%s casts %s!" % (caster, spell_name)

        heal_percent = kwargs.get("heal_percent")
        min_healing, max_healing = kwargs.get("healing_range", (20, 40))
        ingenium_bonus = ((caster.db.ingenium or 10) - 10) // 2

        for character in targets:
            if heal_percent:
                to_heal = int(character.db.max_hp * heal_percent)
            else:
                to_heal = randint(min_healing, max_healing) + ingenium_bonus
            if character.db.hp + to_heal > character.db.max_hp:
                to_heal = character.db.max_hp - character.db.hp
            character.db.hp += to_heal
            spell_msg += " %s regains %i HP!" % (character, to_heal)

        caster.db.mp -= cost
        caster.location.msg_contents(spell_msg)

        if self.is_in_combat(caster):
            self.spend_action(caster, 1, action_name="cast")

    def spell_cure_condition(self, caster, spell_name, targets, cost, **kwargs):
        """
        Spell that removes given conditions from its targets - the
        spell equivalent of itemfunc_cure_condition. Used by Medicus's
        Antidote.
        """
        to_cure = kwargs.get("to_cure", ["Poisoned"])
        spell_msg = "%s casts %s!" % (caster, spell_name)

        for target in targets:
            conditions = self.get_conditions(target)
            for key in list(conditions):
                if key in to_cure:
                    spell_msg += " %s no longer has the '%s' condition." % (target, key)
                    del conditions[key]

        caster.db.mp -= cost
        caster.location.msg_contents(spell_msg)

    def spell_resurrect(self, caster, spell_name, targets, cost, **kwargs):
        """
        Spell that brings a dead character back to the world of the
        living. Used by Medicus's Blessing of Asclepius. Unlike every
        other spell, valid targets for this one aren't found in the
        caster's current room - a dead character is in the Underworld,
        nowhere near the caster physically - so this relies on the
        "deadchar" target type resolving via a global search instead of
        a room search (see CmdCast). MP is only spent if something
        actually happened, so a failed/empty cast doesn't cost anything.
        """
        spell_msg = "%s casts %s!" % (caster, spell_name)
        revived_any = False

        for target in targets:
            if not target.db.is_dead:
                caster.msg("%s is not dead - there is nothing to resurrect." % target.key)
                continue
            self.resurrect(target)
            spell_msg += " %s is pulled back from the realm of the dead!" % target.key
            revived_any = True

        if not revived_any:
            return

        caster.db.mp -= cost
        caster.location.msg_contents(spell_msg)

        if self.is_in_combat(caster):
            self.spend_action(caster, 1, action_name="cast")

    def spell_sanctuary(self, caster, spell_name, targets, cost, **kwargs):
        """
        Medicus's mythic-tier Sanctuary. Equal-or-lower-level
        characters cannot drag the target into a fight at all while
        this is active - see try_break_sanctuary, which handles the
        higher-level "break through, but pay for it" case, checked
        whenever anyone tries to start a fight (see CmdFight). Lasts
        1 real hour via SanctuaryTimer, a persistent Script - not a
        regular condition, since an hour is far beyond the scale the
        normal per-turn condition system is built for.
        """
        for target in targets:
            target.db.sanctuary_active = True
            target.db.sanctuary_level = target.db.level or 1
            target.scripts.add(SanctuaryTimer)

        caster.db.mp -= cost
        names = ", ".join(t.key for t in targets)
        caster.location.msg_contents(
            "%s casts %s - a shimmer of protective light surrounds %s."
            % (caster, spell_name, names)
        )

    def spell_restore_mp(self, caster, spell_name, targets, cost, **kwargs):
        """
        Restores MP to a target - Medicus's Vigor. Nothing else in the
        game currently restores MP at all (spent MP normally only
        comes back through resting/regenerating over time), so this
        fills a genuine gap rather than duplicating an existing effect.
        """
        spell_msg = "%s casts %s!" % (caster, spell_name)
        min_restore, max_restore = kwargs.get("restore_range", (15, 25))

        for character in targets:
            to_restore = randint(min_restore, max_restore)
            if character.db.mp + to_restore > character.db.max_mp:
                to_restore = character.db.max_mp - character.db.mp
            character.db.mp += to_restore
            spell_msg += " %s regains %i MP!" % (character, to_restore)

        caster.db.mp -= cost
        caster.location.msg_contents(spell_msg)

    def spell_vampiric(self, caster, spell_name, targets, cost, **kwargs):
        """
        Deals damage to a target and heals the caster for a portion of
        it - Haruspex's Vampiric Touch.
        """
        spell_msg = "%s casts %s!" % (caster, spell_name)
        min_damage, max_damage = kwargs.get("damage_range", (15, 25))
        drain_percent = kwargs.get("drain_percent", 0.5)
        total_drained = 0

        for target in targets:
            damage = randint(min_damage, max_damage)
            self.apply_damage(target, damage, attacker=caster)
            spell_msg += " %s takes %i damage!" % (target, damage)
            total_drained += damage

        heal_amount = int(total_drained * drain_percent)
        if heal_amount > 0:
            caster.db.hp = min(caster.db.hp + heal_amount, caster.db.max_hp)
            spell_msg += " %s drains %i HP!" % (caster, heal_amount)

        caster.db.mp -= cost
        caster.location.msg_contents(spell_msg)

        if self.is_in_combat(caster):
            self.spend_action(caster, 1, action_name="cast")

    def spell_blood_sacrament(self, caster, spell_name, targets, cost, **kwargs):
        """
        Converts a portion of the caster's own health into a
        devastating burst of damage - Haruspex's Blood Sacrament.
        Costs both MP and a chunk of the caster's current HP, so
        casting this recklessly at low HP is genuinely risky, not
        just expensive. Refuses to cast (and doesn't spend anything)
        if the caster doesn't have enough HP to safely pay the cost.
        """
        hp_cost = kwargs.get("hp_cost", 15)
        min_damage, max_damage = kwargs.get("damage_range", (35, 50))

        if caster.db.hp <= hp_cost:
            caster.msg("You don't have enough blood left to spare for this ritual.")
            return

        spell_msg = "%s casts %s, spilling their own blood as payment!" % (caster, spell_name)
        caster.db.hp -= hp_cost

        for target in targets:
            damage = randint(min_damage, max_damage)
            self.apply_damage(target, damage, attacker=caster)
            spell_msg += " %s takes %i damage!" % (target, damage)

        caster.db.mp -= cost
        caster.location.msg_contents(spell_msg)

        if self.is_in_combat(caster):
            self.spend_action(caster, 1, action_name="cast")


    def spell_add_condition(self, caster, spell_name, targets, cost, **kwargs):
        """
        Spell that grants a condition to its targets - the spell
        equivalent of itemfunc_add_condition. Used for buff spells like
        Augur's Auspice (Defense Up) and Favour of the Sky (Accuracy Up).
        """
        conditions = kwargs.get("conditions", [("Defense Up", 3)])
        spell_msg = "%s casts %s!" % (caster, spell_name)

        for target in targets:
            for condition in conditions:
                self.add_condition(target, caster, condition[0], condition[1])

        caster.db.mp -= cost
        caster.location.msg_contents(spell_msg)

        if self.is_in_combat(caster):
            self.spend_action(caster, 1, action_name="cast")

    def spell_attack(self, caster, spell_name, targets, cost, **kwargs):
        """Spell that deals damage in combat."""
        spell_msg = "%s casts %s!" % (caster, spell_name)

        atkname_single, atkname_plural = kwargs.get("attack_name", ("The spell", "spells"))
        min_damage, max_damage = kwargs.get("damage_range", (10, 20))
        accuracy = kwargs.get("accuracy", 0)
        attack_count = kwargs.get("attack_count", 1)
        # Two separate bonuses from the same stat: full-strength for
        # the hit roll (ingenium_accuracy, matching how get_attack
        # uses agilitas at full strength for basic attacks - the two
        # should scale the same way), halved for damage (unchanged -
        # this part was never the issue). Splitting these out fixes a
        # real inconsistency: spells/skills were using the halved
        # value for BOTH hit chance and damage, while basic attack
        # only ever used the full value, making race/class choice
        # barely move the needle on whether a spell or skill actually
        # connects even though it clearly did for a plain attack.
        ingenium_accuracy = ((caster.db.ingenium or 10) - 10) * ACCURACY_STAT_MULTIPLIER
        ingenium_bonus = ((caster.db.ingenium or 10) - 10) // 2

        to_attack = list(targets)
        if len(targets) < attack_count:
            extra_attacks = attack_count - len(targets)
            for n in range(extra_attacks):
                to_attack.insert(0, targets[0])

        total_hits = {fighter: 0 for fighter in targets}
        total_damage = {fighter: 0 for fighter in targets}

        for fighter in to_attack:
            attack_value = randint(1, 100) + accuracy + ingenium_accuracy
            defense_value = self.get_defense(caster, fighter)
            if attack_value >= defense_value:
                spell_dmg = randint(min_damage, max_damage) + ingenium_bonus
                total_hits[fighter] += 1
                total_damage[fighter] += spell_dmg

        for fighter in targets:
            if total_hits[fighter] == 0:
                spell_msg += " The spell misses %s!" % fighter
            else:
                attack_count_str = atkname_single + " hits"
                if total_hits[fighter] > 1:
                    attack_count_str = "%i %s hit" % (total_hits[fighter], atkname_plural)
                projected_hp = (fighter.db.hp or 0) - total_damage[fighter]
                spell_msg += " %s %s for |r%i|n damage - %s %s!" % (
                    attack_count_str,
                    fighter,
                    total_damage[fighter],
                    fighter,
                    self.hp_status_phrase(fighter, hp_override=projected_hp),
                )

        caster.db.mp -= cost
        caster.location.msg_contents(spell_msg)

        for fighter in targets:
            self.apply_damage(fighter, total_damage[fighter], attacker=caster)
            if fighter.db.hp <= 0:
                self.at_defeat(fighter, attacker=caster)

        if self.is_in_combat(caster):
            self.spend_action(caster, 1, action_name="cast")

    def spell_conjure(self, caster, spell_name, targets, cost, **kwargs):
        """Spell that creates an object."""
        obj_key = kwargs.get("obj_key", "a nondescript object")
        obj_desc = kwargs.get("obj_desc", "A perfectly generic object.")
        obj_typeclass = kwargs.get("obj_typeclass", "evennia.objects.objects.DefaultObject")

        conjured_obj = create_object(obj_typeclass, key=obj_key, location=caster.location)
        conjured_obj.db.desc = obj_desc

        caster.db.mp -= cost

        caster.location.msg_contents(
            "%s casts %s, and %s appears!" % (caster, spell_name, conjured_obj)
        )

    def spell_conjure_weapon(self, caster, spell_name, targets, cost, **kwargs):
        """
        Conjures a weapon into the caster's hands, its power scaling
        with the caster's own level. Always conjures from the staff
        category specifically - Augur's actual proficiency - rather
        than switching to heavier weapon types at high level, which
        would trigger the class's own non-proficiency penalty and be
        self-defeating (a light caster fighting worse the "stronger"
        their conjured weapon supposedly got). The weapon fades after
        10 minutes if not already gone, since it's a temporary
        manifestation, not a permanent item. (This cleanup timer uses
        a plain delay() rather than a persistent Script, unlike the
        Underworld's Charon timer - if a reload happens to eat it, the
        worst case is a weapon that just doesn't auto-expire, not a
        player getting permanently stuck.)
        """
        from evennia.prototypes.spawner import spawn
        from evennia.utils.utils import delay

        level = caster.db.level or 1
        if level < 30:
            damage_range = (6, 14)
            display_name = "a conjured staff"
        elif level < 60:
            damage_range = (14, 24)
            display_name = "a conjured staff, wreathed in faint light"
        elif level < 90:
            damage_range = (22, 34)
            display_name = "a conjured staff, crackling with divine power"
        else:
            damage_range = (32, 48)
            display_name = "a conjured staff of pure Olympian light"

        weapon = spawn("RITUAL_STAFF")[0]
        weapon.location = caster
        weapon.key = display_name
        weapon.db.damage_range = damage_range

        caster.db.mp -= cost
        caster.location.msg_contents(
            "%s casts %s, calling %s into being!" % (caster, spell_name, weapon)
        )

        delay(600, callback=weapon.delete)

    def spell_summon_familiar(self, caster, spell_name, targets, cost, **kwargs):
        """
        Summons a divine familiar to the caster's side, its strength
        scaling with the caster's own level - same tier breakpoints as
        Conjure Weapon, and same personal-instance mechanism as the
        Ludus trainers (spawn_personal_npc). Like every other personal/
        summoned NPC in the game right now, it has no AI of its own -
        it appears and joins the fight, but won't act automatically.
        That's a real, honest limitation shared with the Ludus
        trainers, not something unique to this spell - true NPC AI is
        its own future system.
        """
        level = caster.db.level or 1
        if level < 30:
            prototype = "AUGUR_FAMILIAR_TIER1"
        elif level < 60:
            prototype = "AUGUR_FAMILIAR_TIER2"
        elif level < 90:
            prototype = "AUGUR_FAMILIAR_TIER3"
        else:
            prototype = "AUGUR_FAMILIAR_TIER4"

        familiar = self.spawn_personal_npc(kwargs.get("familiar_prototype", prototype), caster)

        caster.db.mp -= cost
        caster.location.msg_contents(
            "%s casts %s, and %s descends to their side!" % (caster, spell_name, familiar)
        )

        if self.is_in_combat(caster):
            turnhandler = caster.db.combat_turnhandler
            if turnhandler and turnhandler.pk:
                turnhandler.join_fight(familiar, side=caster.db.combat_side)
            self.spend_action(caster, 1, action_name="cast")

    def spell_summon_lemures(self, caster, spell_name, targets, cost, **kwargs):
        """
        Summons a restless spirit of the dead to fight at the caster's
        side, its strength scaling with the caster's own level - exact
        same tier breakpoints AND HP curve as Augur's Summon Familiar,
        so both classes' summon spells stay balanced against each
        other at equal level rather than one quietly outscaling the
        other. Same "no AI" limitation as every other personal-instance
        NPC in the game right now.
        """
        level = caster.db.level or 1
        if level < 30:
            prototype = "HARUSPEX_LEMURES_TIER1"
        elif level < 60:
            prototype = "HARUSPEX_LEMURES_TIER2"
        elif level < 90:
            prototype = "HARUSPEX_LEMURES_TIER3"
        else:
            prototype = "HARUSPEX_LEMURES_TIER4"

        lemures = self.spawn_personal_npc(kwargs.get("lemures_prototype", prototype), caster)

        caster.db.mp -= cost
        caster.location.msg_contents(
            "%s casts %s, and %s rises from the shadows!" % (caster, spell_name, lemures)
        )

        if self.is_in_combat(caster):
            turnhandler = caster.db.combat_turnhandler
            if turnhandler and turnhandler.pk:
                turnhandler.join_fight(lemures, side=caster.db.combat_side)
            self.spend_action(caster, 1, action_name="cast")

    # Destinations Gate is allowed to reach - deliberately a small,
    # curated whitelist rather than free-form teleport-by-room-name,
    # which would let players bypass every puzzle/gate in the game
    # (the Colosseum's escape questline, anything sequence-locked).
    # Add more entries here as more hub locations get tagged.
    GATE_DESTINATIONS = {
        "atrium": ("colosseum_recall_point", "colosseum"),
    }

    def spell_gate(self, caster, spell_name, targets, cost, **kwargs):
        """
        Teleports the caster to one of a small set of pre-approved hub
        locations (see GATE_DESTINATIONS above). The typed argument is
        a plain keyword (e.g. "atrium"), not a character to search
        for - see the "keyword" target type in CmdCast, which passes
        the raw text straight through instead of trying to resolve it
        against room contents.
        """
        from evennia.utils.search import search_tag

        if not targets:
            valid = ", ".join(self.GATE_DESTINATIONS.keys())
            caster.msg("Gate to where? Known destinations: %s" % valid)
            return

        destination_key = targets[0].strip().lower()
        if destination_key not in self.GATE_DESTINATIONS:
            valid = ", ".join(self.GATE_DESTINATIONS.keys())
            caster.msg("You can't gate there. Known destinations: %s" % valid)
            return

        tag, category = self.GATE_DESTINATIONS[destination_key]
        rooms = search_tag(tag, category=category)
        if not rooms:
            caster.msg("The gate finds nowhere to open to.")
            return

        caster.location.msg_contents(
            "%s vanishes in a shimmer of divine light!" % caster, exclude=caster
        )
        caster.db.mp -= cost
        caster.move_to(rooms[0], quiet=False)
        caster.msg("You step through a gate of light and arrive elsewhere.")

    def spell_scry(self, caster, spell_name, targets, cost, **kwargs):
        """
        Reveals who's present in a room reachable through one of the
        caster's current exits, without needing to actually go there -
        Augur's Birdsight. The target is an exit name/direction (e.g.
        "north"), passed via the "keyword" target type, same mechanism
        as Gate - not a character to search for.
        """
        if not targets:
            caster.msg("Scry which direction? Usage: cast birdsight = <exit>")
            return

        exit_name = targets[0].strip().lower()
        exit_obj = caster.search(exit_name, candidates=caster.location.exits)
        if not exit_obj or not exit_obj.destination:
            caster.msg("There's no exit called '%s' to scry through." % exit_name)
            return

        destination = exit_obj.destination
        occupants = [o.key for o in destination.contents if o.attributes.has("max_hp")]

        caster.db.mp -= cost
        if occupants:
            caster.msg(
                "Through the eyes of birds, you glimpse %s: %s"
                % (destination.key, ", ".join(occupants))
            )
        else:
            caster.msg(
                "Through the eyes of birds, you glimpse %s: it appears empty."
                % destination.key
            )

    # ------------------------------------------------------------------
    # SKILLS (SP-based, for non-caster classes - same idea as spells,
    # but spending SP instead of MP, and using "skillfunc" entries in
    # SKILLS instead of "spellfunc" entries in SPELLS)
    # ------------------------------------------------------------------

    def skill_add_condition(self, user, skill_name, targets, cost, **kwargs):
        """
        SP-costing equivalent of spell_add_condition - grants one or
        more conditions to the target(s). Used for most of the
        Speculator's buff/debuff skills (Sneak, Poisoned Blade,
        Precision Strike, Crippling Strike, Smoke and Shadow, Vanish).
        """
        conditions = kwargs.get("conditions", [("Defense Up", 3)])
        skill_msg = "%s uses %s!" % (user, skill_name)

        for target in targets:
            for condition in conditions:
                self.add_condition(target, user, condition[0], condition[1])

        user.db.sp -= cost
        user.location.msg_contents(skill_msg)

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    def skill_ambush(self, user, skill_name, targets, cost, **kwargs):
        """
        Speculator's Ambush - a genuine surprise-attack opener, not
        just a pre-fight buff you have to remember to use before
        separately typing 'fight'. Starts a fight with just the
        ambushed target - nobody else in the room gets pulled in,
        which fits an ambush a lot better than the old room-wide
        sweep did - AND guarantees a bonus on the user's first
        successful attack once the fight begins.
        """
        here = user.location
        target = targets[0]

        if user.db.is_dead:
            user.msg("You are dead. The living's quarrels are no longer yours.")
            return
        if not user.db.hp:
            user.msg("You can't ambush anyone - you've been defeated!")
            return
        if self.is_in_combat(user):
            user.msg("You're already in a fight!")
            return
        if not target.db.hp or target.db.is_dead:
            user.msg("There's no one there to ambush.")
            return
        if target == user:
            user.msg("You can't ambush yourself.")
            return
        if not self.try_break_sanctuary(user, target):
            return

        self.add_condition(user, user, "Ambush", 5)
        user.db.sp -= cost
        here.msg_contents("%s bursts from hiding, ambushing %s!" % (user, target))

        if here.db.combat_turnhandler:
            here.db.combat_turnhandler.join_fight(user)
        else:
            here.ndb.pending_fighters = [user, target]
            here.scripts.add(CombatTurnHandler)

    def skill_backstab(self, user, skill_name, targets, cost, **kwargs):
        """
        Deals bonus damage if the target hasn't yet acted at all in
        this fight (checked via combat_lastaction being unset).
        Deliberately does NOT stack with an active Ambush
        bonus - if both would apply, Ambush is simply
        consumed without adding its own bonus on top, so a player
        can't stack two "surprise" bonuses into one absurd hit.
        """
        bonus_damage = kwargs.get("bonus_damage", 20)
        target = targets[0]

        if not self.is_in_combat(user):
            user.msg(
                "There's no fight to exploit an opening in - use 'ambush' if you "
                "want to start one."
            )
            return

        if target.db.combat_lastaction != "null":
            user.msg("%s is already in the fight - there's no opening left to exploit." % target.key)
            return

        # Mutual exclusion with Ambush - consume it silently
        # if present, rather than letting both bonuses apply at once.
        if "Ambush" in self.get_conditions(user):
            del self.get_conditions(user)["Ambush"]

        self.apply_damage(target, bonus_damage, attacker=user)
        user.db.sp -= cost
        user.location.msg_contents(
            "%s finds an opening and strikes %s from the shadows!" % (user, target)
        )

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    def skill_field_report(self, user, skill_name, targets, cost, **kwargs):
        """
        Reveals a target's current HP and active conditions to the
        user's whole party at once - Speculator's Field Report.
        """
        from world.party import get_party_members

        target = targets[0]
        conditions = list(self.get_conditions(target).keys())
        condition_str = ", ".join(conditions) if conditions else "no conditions"

        report = "|c[Field Report]|n %s - HP: %s/%s - %s" % (
            target.key,
            target.db.hp,
            target.db.max_hp,
            condition_str,
        )

        user.db.sp -= cost
        for member in get_party_members(user):
            member.msg(report)

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    def skill_deathmark(self, user, skill_name, targets, cost, **kwargs):
        """
        Mythic-tier Speculator skill. Guarantees the user's next
        attack against the marked target lands and deals heavy bonus
        damage - "Marked for Death" is checked directly in
        resolve_attack, bypassing the normal accuracy roll entirely
        for that one hit, then is consumed.
        """
        target = targets[0]
        self.add_condition(target, user, "Marked for Death", 5)
        user.db.sp -= cost
        user.location.msg_contents(
            "%s marks %s - a blade meant for one throat alone." % (user, target)
        )

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    def skill_attack(self, user, skill_name, targets, cost, **kwargs):
        """
        Generic SP-costing direct damage skill - the skill-system
        equivalent of spell_attack. Deliberately generic and reusable,
        not Venator-specific, since every remaining physical class
        needs at least one direct-damage signature move and there's no
        reason to write four near-identical methods for that.

        Now includes a real hit/miss roll, matching spell_attack -
        this used to always connect regardless of stats, an
        inconsistency with spells (which could always miss) that
        made physical damage skills mechanically more reliable than
        their magical equivalent for no deliberate reason.
        """
        skill_msg = "%s uses %s!" % (user, skill_name)
        min_damage, max_damage = kwargs.get("damage_range", (15, 25))
        accuracy = kwargs.get("accuracy", 0)
        # Same split as spell_attack: full-strength for the hit roll
        # (matching get_attack's pattern), halved for damage (unchanged).
        agilitas_accuracy = ((user.db.agilitas or 10) - 10) * ACCURACY_STAT_MULTIPLIER
        agilitas_bonus = ((user.db.agilitas or 10) - 10) // 2

        total_damage = 0
        for target in targets:
            attack_value = randint(1, 100) + accuracy + agilitas_accuracy
            defense_value = self.get_defense(user, target)
            if attack_value < defense_value:
                skill_msg += " %s misses %s!" % (skill_name, target)
                continue
            damage = randint(min_damage, max_damage) + agilitas_bonus
            self.apply_damage(target, damage, attacker=user)
            total_damage += damage
            skill_msg += " %s takes |r%i|n damage - %s %s!" % (
                target, damage, target, self.hp_status_phrase(target)
            )

        user.db.sp -= cost
        user.location.msg_contents(skill_msg)

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    def skill_piercing_shot(self, user, skill_name, targets, cost, **kwargs):
        """
        An armor-ignoring ranged strike - Venator's Piercing Shot.
        Computes damage independently rather than going through the
        normal weapon/armor pipeline in get_damage(), specifically so
        the target's armor damage_reduction never gets subtracted -
        that's the entire point of the skill.
        """
        target = targets[0]
        min_damage, max_damage = kwargs.get("damage_range", (20, 30))
        agilitas_bonus = ((user.db.agilitas or 10) - 10) // 2
        damage = randint(min_damage, max_damage) + agilitas_bonus

        self.apply_damage(target, damage, attacker=user)
        user.db.sp -= cost
        user.location.msg_contents(
            "%s's shot finds a gap in %s's armor entirely, striking for %i damage!"
            % (user, target, damage)
        )

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    def skill_pack_tactics(self, user, skill_name, targets, cost, **kwargs):
        """
        Grants a damage buff, but only if the user currently has an
        active beast companion out (spawned via Call of the Wild) -
        Venator's Pack Tactics. Refuses (and refunds the SP cost
        attempt entirely) if there's no companion present, so it's a
        genuine synergy pick, not just a Damage Up spell with extra
        steps.
        """
        if not user.db.active_companion or not user.db.active_companion.pk:
            user.msg("You need an active beast companion out to use Pack Tactics.")
            return

        self.add_condition(user, user, "Damage Up", 4)
        user.db.sp -= cost
        user.location.msg_contents(
            "%s and %s move as one, striking with practiced coordination!"
            % (user, user.db.active_companion.key)
        )

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    def skill_call_of_the_wild(self, user, skill_name, targets, cost, **kwargs):
        """
        Summons a beast companion to fight at the user's side, its
        strength scaling with the user's own level - same tier
        breakpoints AND HP curve as Augur's familiar and Haruspex's
        Lemures (40/80/130/190), so all three summon-capable classes
        stay balanced against each other at equal level. Tracks the
        companion on db.active_companion so Pack Tactics can check for
        it.
        """
        level = user.db.level or 1
        if level < 30:
            prototype = "VENATOR_BEAST_TIER1"
        elif level < 60:
            prototype = "VENATOR_BEAST_TIER2"
        elif level < 90:
            prototype = "VENATOR_BEAST_TIER3"
        else:
            prototype = "VENATOR_BEAST_TIER4"

        companion = self.spawn_personal_npc(kwargs.get("beast_prototype", prototype), user)
        user.db.active_companion = companion

        user.db.sp -= cost
        user.location.msg_contents(
            "%s uses %s, and %s bounds to their side!" % (user, skill_name, companion)
        )

        if self.is_in_combat(user):
            turnhandler = user.db.combat_turnhandler
            if turnhandler and turnhandler.pk:
                turnhandler.join_fight(companion, side=user.db.combat_side)
            self.spend_action(user, 1, action_name="skill")

    def skill_track(self, user, skill_name, targets, cost, **kwargs):
        """
        Reveals who's present in a room reachable through one of the
        user's current exits, without needing to actually go there -
        Venator's Track. SP-based mirror of Augur's Birdsight
        (spell_scry) - same mechanic, different resource and flavor.
        """
        if not targets:
            user.msg("Track which direction? Usage: skill track = <exit>")
            return

        exit_name = targets[0].strip().lower()
        exit_obj = user.search(exit_name, candidates=user.location.exits)
        if not exit_obj or not exit_obj.destination:
            user.msg("There's no exit called '%s' to track through." % exit_name)
            return

        destination = exit_obj.destination
        occupants = [o.key for o in destination.contents if o.attributes.has("max_hp")]

        user.db.sp -= cost
        if occupants:
            user.msg("Reading the signs, you sense movement through %s: %s" % (destination.key, ", ".join(occupants)))
        else:
            user.msg("Reading the signs, you sense nothing through %s." % destination.key)

    def skill_riposte(self, user, skill_name, targets, cost, **kwargs):
        """
        Grants a one-time "Riposte Ready" condition - the next hit the
        user takes triggers an immediate counter-attack, checked in
        apply_damage rather than here. A genuinely reactive skill,
        unlike everything else in the game so far, which only ever
        does something on the user's own turn.
        """
        self.add_condition(user, user, "Riposte Ready", 3)
        user.db.sp -= cost
        user.location.msg_contents(
            "%s settles into a ready stance, watching for an opening." % user
        )

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    def skill_gory_finish(self, user, skill_name, targets, cost, **kwargs):
        """
        A real execute - deals heavy bonus damage, but only against a
        target already below the HP threshold. Refuses (refunding
        nothing spent yet) against a healthier target, so it's a
        genuine finishing move, not just a slightly-better attack.
        """
        target = targets[0]
        threshold_percent = kwargs.get("threshold_percent", 0.2)
        min_damage, max_damage = kwargs.get("damage_range", (30, 45))

        if target.db.hp > target.db.max_hp * threshold_percent:
            user.msg(
                "%s is still too strong for a finishing blow - wait until they're "
                "closer to falling." % target.key
            )
            return

        agilitas_bonus = ((user.db.agilitas or 10) - 10) // 2
        damage = randint(min_damage, max_damage) + agilitas_bonus
        self.apply_damage(target, damage, attacker=user)

        user.db.sp -= cost
        user.location.msg_contents(
            "%s delivers a cinematic finishing blow to %s for %i damage!"
            % (user, target, damage)
        )

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    def skill_thundering_maul(self, user, skill_name, targets, cost, **kwargs):
        """
        A heavy two-handed strike - Barbarian's Thundering Maul.
        Requires an actual two-handed weapon in hand; refuses (and
        spends nothing) otherwise. This finally implements the exact
        check flagged as missing back when weapon proficiency was
        first designed - "what happens if the player isn't holding a
        two-handed weapon" now has a real answer: the skill just
        won't fire.
        """
        weapon = user.db.wielded_weapon
        if not weapon or not weapon.db.two_handed:
            user.msg("Thundering Maul needs a two-handed weapon in hand.")
            return

        target = targets[0]
        min_damage, max_damage = kwargs.get("damage_range", (30, 45))
        virtus_bonus = ((user.db.virtus or 10) - 10) // 2
        damage = randint(min_damage, max_damage) + virtus_bonus
        self.apply_damage(target, damage, attacker=user)

        user.db.sp -= cost
        user.location.msg_contents(
            "%s brings their weapon down in a thundering two-handed blow, "
            "striking %s for %i damage!" % (user, target, damage)
        )

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    def skill_reckless_abandon(self, user, skill_name, targets, cost, **kwargs):
        """
        A huge damage strike that leaves the user dangerously exposed -
        Barbarian's Reckless Abandon. Deals heavy damage but applies a
        real Defense Down to the user themselves as the cost - a
        genuine risk/reward tradeoff, not just a bigger number.
        """
        target = targets[0]
        min_damage, max_damage = kwargs.get("damage_range", (35, 55))
        virtus_bonus = ((user.db.virtus or 10) - 10) // 2
        damage = randint(min_damage, max_damage) + virtus_bonus
        self.apply_damage(target, damage, attacker=user)
        self.add_condition(user, user, "Defense Down", 3)

        user.db.sp -= cost
        user.location.msg_contents(
            "%s abandons all defense for a devastating strike against %s, "
            "dealing %i damage!" % (user, target, damage)
        )

        if self.is_in_combat(user):
            self.spend_action(user, 1, action_name="skill")

    # ------------------------------------------------------------------
    # STAMINA / POWER ATTACK
    # ------------------------------------------------------------------

    def power_attack(self, attacker, defender):
        """
        SP-based melee special move: hits harder than a normal attack,
        but costs stamina and is less accurate. Uses the same weapon/
        armor/condition logic as a normal attack, plus flat modifiers.
        """
        attack_value = self.get_attack(attacker, defender) + POWERATTACK_ACCURACY_PENALTY
        defense_value = self.get_defense(attacker, defender)
        damage_value = self.get_damage(attacker, defender) + POWERATTACK_DAMAGE_BONUS

        attacker.db.sp -= POWERATTACK_SP_COST

        self.resolve_attack(
            attacker,
            defender,
            attack_value=attack_value,
            defense_value=defense_value,
            damage_value=damage_value,
        )

    # ------------------------------------------------------------------
    # LEVELING / XP
    # ------------------------------------------------------------------

    def xp_for_level(self, level):
        """XP required to advance FROM this level to the next one."""
        return int(LEVEL_XP_BASE * (level ** LEVEL_XP_EXPONENT))

    def award_xp(self, character, amount):
        """
        Grants XP to a character and handles any resulting level-ups
        (possibly several at once, from one big reward). Does nothing
        for characters at MAX_LEVEL or the manually-assigned God tier
        (101+), since those aren't earned through XP.
        """
        level = character.db.level or 1
        if level >= MAX_LEVEL:
            return

        character.db.xp = (character.db.xp or 0) + amount
        character.msg("|yYou gain %d experience.|n" % amount)

        while character.db.level < MAX_LEVEL and character.db.xp >= self.xp_for_level(
            character.db.level
        ):
            character.db.xp -= self.xp_for_level(character.db.level)
            character.db.level += 1

            character.db.max_hp += LEVEL_UP_HP_GAIN
            character.db.max_mp += LEVEL_UP_MP_GAIN
            character.db.max_sp += LEVEL_UP_SP_GAIN
            character.db.hp = character.db.max_hp
            character.db.mp = character.db.max_mp
            character.db.sp = character.db.max_sp

            character.msg(
                "|G*** You have reached level %d! ***|n" % character.db.level
            )
            if character.db.level == MAX_LEVEL and character.has_account:
                from evennia.contrib.game_systems.achievements import track_achievements
                from world.achievements import announce_achievements
                completed = track_achievements(character, category="level", tracking="hundred")
                announce_achievements(character, completed)

    # Tunable: how much XP a single cast awards per point of MP/SP
    # spent. Applies to EVERY successful spell or skill use, not just
    # damage - a Medicus healing a badly-hurt ally, or a caster
    # landing a debuff, is genuinely contributing to the fight and
    # should walk away with something to show for it, the same as
    # someone swinging a sword. Scales with cost specifically so a
    # cheap early spell and a powerful late-game one aren't treated
    # as equally significant.
    #
    # Calibrated at 1, not 2: worked through the actual numbers for a
    # level-1 caster with ~26 MP casting cure wounds (cost 5) through
    # their whole pool - at 2x that's 50 XP from casting alone,
    # already more than most low-tier NPCs award a SOLO killer
    # outright (15-40 xp_reward). At 1x it stays meaningful without
    # letting a pure support caster out-level melee.
    CAST_XP_PER_COST = 1

    def award_cast_xp(self, caster, cost):
        """
        Awards a small amount of XP for successfully casting a spell
        or using a skill - completely independent of whether it dealt
        any damage. Only while actually in combat, so this rewards
        real participation in a fight rather than becoming a way to
        grind XP by repeatedly casting a cheap spell on yourself with
        nothing around to fight at all.
        """
        if not self.is_in_combat(caster):
            return
        amount = cost * self.CAST_XP_PER_COST
        if amount > 0:
            self.award_xp(caster, amount)

    # ------------------------------------------------------------------
    # PERSONAL NPC INSTANCES
    # ------------------------------------------------------------------
    # Used for any "fight this trainer" encounter (Colosseum escape,
    # Ludus training) where many players might want to fight the "same"
    # NPC at once. Rather than one shared NPC everyone queues behind,
    # each challenger gets their own disposable copy, cleaned up when
    # the fight ends (or after a safety-net timeout if abandoned).

    def spawn_personal_npc(self, prototype_name, challenger):
        """
        Spawns a fresh personal copy of an NPC prototype for a single
        challenger. Returns the spawned NPC.
        """
        obj = spawn(prototype_name)[0]
        obj.move_to(challenger.location, quiet=True)
        obj.db.instance_owner = challenger
        obj.db.base_name = obj.key  # clean name, kept for defeat messages etc.
        obj.key = "%s (%s's opponent)" % (obj.key, challenger.key)

        # Safety net: if the fight is abandoned (challenger disengages,
        # disconnects, whatever) the instance still gets cleaned up
        # after 10 minutes rather than lingering forever. A persistent
        # Script rather than a plain delay() call - delay() doesn't
        # survive a server reload or crash, which was the actual,
        # confirmed root cause of NPCs needing manual cleanupnpcs runs
        # (see InstanceCleanupTimer below, same fix already applied to
        # RespawnTimer/CharonTimer/SanctuaryTimer elsewhere in this file).
        obj.scripts.add(InstanceCleanupTimer)

        return obj


COMBAT_RULES = CombatRules()

ITEMFUNCS = {
    "heal": COMBAT_RULES.itemfunc_heal,
    "attack": COMBAT_RULES.itemfunc_attack,
    "add_condition": COMBAT_RULES.itemfunc_add_condition,
    "cure_condition": COMBAT_RULES.itemfunc_cure_condition,
}

def _usage_line(verb, name, target_type):
    """
    Builds a real, copy-pasteable usage example for a spell or skill,
    computed from its target type rather than hand-written per entry -
    one source of truth (the SPELLS/SKILLS dict itself) instead of 90+
    separate strings that could drift out of sync with the actual
    mechanics.
    """
    if target_type in ("self", "none"):
        return "%s %s" % (verb, name)
    if target_type == "deadchar":
        return "%s %s = <dead character's name>" % (verb, name)
    if target_type == "keyword":
        return "%s %s = <destination or exit name>" % (verb, name)
    return "%s %s = <target>" % (verb, name)


SPELLS = {
    "mark of decay": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 1,
        "desc": "A damage-over-time curse that saps enemy strength.",
        "target": "otherchar",
        "cost": 4,
        "conditions": [("Poisoned", 4)],
        "classes": ["haruspex"],
    },
    "grave chill": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 5,
        "desc": "Lowers a target's accuracy for a short time.",
        "target": "otherchar",
        "cost": 4,
        "conditions": [("Accuracy Down", 4)],
        "classes": ["haruspex"],
    },
    "weaken flesh": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 8,
        "desc": "Lowers a target's defense for a short time.",
        "target": "otherchar",
        "cost": 4,
        "conditions": [("Defense Down", 4)],
        "classes": ["haruspex"],
    },
    "rite of the entrails": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 15,
        "desc": "Curses a target to take extra damage from everything for a short time.",
        "target": "otherchar",
        "cost": 5,
        "conditions": [("Cursed", 4)],
        "classes": ["haruspex"],
    },
    "ritual flame": {
        "spellfunc": COMBAT_RULES.spell_attack,
        "level_required": 20,
        "desc": "A jet of ritual fire - reliable single-target damage.",
        "target": "otherchar",
        "cost": 3,
        "noncombat_spell": False,
        "attack_name": ("A jet of ritual flame", "jets of ritual flame"),
        "damage_range": (25, 35),
        "classes": ["haruspex"],
    },
    "ill fortune": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 25,
        "desc": "Lowers a target's outgoing damage for a short time.",
        "target": "otherchar",
        "cost": 5,
        "conditions": [("Damage Down", 4)],
        "classes": ["haruspex"],
    },
    "vampiric touch": {
        "spellfunc": COMBAT_RULES.spell_vampiric,
        "level_required": 30,
        "desc": "Damages a target and heals the caster for half of it.",
        "target": "otherchar",
        "cost": 8,
        "noncombat_spell": False,
        "damage_range": (15, 25),
        "drain_percent": 0.5,
        "classes": ["haruspex"],
    },
    "curse of silence": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 35,
        "desc": "Prevents a target from casting any spells for a short time.",
        "target": "otherchar",
        "cost": 8,
        "conditions": [("Silenced", 3)],
        "classes": ["haruspex"],
    },
    "blood sacrament": {
        "spellfunc": COMBAT_RULES.spell_blood_sacrament,
        "level_required": 40,
        "desc": "Costs the caster their own HP to unleash a devastating burst of damage.",
        "target": "otherchar",
        "cost": 6,
        "noncombat_spell": False,
        "hp_cost": 15,
        "damage_range": (35, 50),
        "classes": ["haruspex"],
    },
    "doom": {
        "spellfunc": COMBAT_RULES.spell_attack,
        "level_required": 45,
        "desc": "A heavy bolt of black doom - strong single-target damage.",
        "target": "otherchar",
        "cost": 7,
        "noncombat_spell": False,
        "attack_name": ("A bolt of black doom", "bolts of black doom"),
        "damage_range": (30, 42),
        "classes": ["haruspex"],
    },
    "omen of ruin": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 50,
        "desc": "Frightens a target and lowers their accuracy and damage at once.",
        "target": "otherchar",
        "cost": 8,
        "conditions": [("Frightened", 3), ("Accuracy Down", 3), ("Damage Down", 3)],
        "classes": ["haruspex"],
    },
    "soul rot": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 60,
        "desc": "A spreading poison curse that can strike up to three enemies at once.",
        "target": "otherchar",
        "cost": 9,
        "max_targets": 3,
        "conditions": [("Poisoned", 5)],
        "classes": ["haruspex"],
    },
    "summon lemures": {
        "spellfunc": COMBAT_RULES.spell_summon_lemures,
        "level_required": 65,
        "desc": "Calls a restless spirit of the dead to fight at the caster's side. Strength scales with the caster's level.",
        "target": "none",
        "cost": 10,
        "classes": ["haruspex"],
    },
    "necrotic storm": {
        "spellfunc": COMBAT_RULES.spell_attack,
        "level_required": 80,
        "desc": "A wave of necrotic force striking up to three enemies at once.",
        "target": "otherchar",
        "cost": 12,
        "noncombat_spell": False,
        "max_targets": 3,
        "attack_name": ("A wave of necrotic force", "waves of necrotic force"),
        "damage_range": (20, 30),
        "classes": ["haruspex"],
    },
    "wail of the damned": {
        "spellfunc": COMBAT_RULES.spell_attack,
        "level_required": 90,
        "desc": "Mythic tier. A wail from the underworld striking up to five enemies at once.",
        "target": "otherchar",
        "cost": 16,
        "noncombat_spell": False,
        "max_targets": 5,
        "attack_name": ("A wail from the depths of the underworld", "wails from the depths of the underworld"),
        "damage_range": (30, 45),
        "classes": ["haruspex"],
    },
    "divine judgment": {
        "spellfunc": COMBAT_RULES.spell_attack,
        "level_required": 15,
        "desc": "A bolt of heavenly light - Augur's basic offensive spell.",
        "target": "otherchar",
        "cost": 5,
        "noncombat_spell": False,
        "attack_name": ("A bolt of heavenly light", "bolts of heavenly light"),
        "damage_range": (18, 28),
        "classes": ["augur"],
    },
    "auspice": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 5,
        "desc": "Grants the caster a temporary defense boost.",
        "target": "self",
        "cost": 4,
        "conditions": [("Defense Up", 4)],
        "classes": ["augur"],
    },
    "favour of the sky": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 8,
        "desc": "Grants an ally a temporary accuracy boost.",
        "target": "anychar",
        "cost": 4,
        "conditions": [("Accuracy Up", 4)],
        "classes": ["augur"],
    },
    "veil of night": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 40,
        "desc": "Turns the caster nearly invisible, making them much harder to hit for a short time.",
        "target": "self",
        "cost": 6,
        "conditions": [("Invisible", 3)],
        "classes": ["augur"],
    },
    "illusory duplicate": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 35,
        "desc": "Confuses enemies with illusory copies, making the caster harder to hit for a short time.",
        "target": "self",
        "cost": 5,
        "conditions": [("Illusory Duplicate", 2)],
        "classes": ["augur"],
    },
    "omen of doom": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 45,
        "desc": "Curses an enemy with lowered accuracy and damage at once.",
        "target": "otherchar",
        "cost": 7,
        "conditions": [("Accuracy Down", 4), ("Damage Down", 4)],
        "classes": ["augur"],
    },
    "prophetic ward": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 50,
        "desc": "Fully absorbs the next hit against the warded target.",
        "target": "anychar",
        "cost": 8,
        "conditions": [("Shielded", 6)],
        "classes": ["augur"],
    },
    "conjure weapon": {
        "spellfunc": COMBAT_RULES.spell_conjure_weapon,
        "level_required": 60,
        "desc": "Conjures a staff into the caster's hands. Power scales with the caster's level. Fades after 10 minutes.",
        "target": "none",
        "cost": 6,
        "combat_spell": False,
        "classes": ["augur"],
    },
    "summon familiar": {
        "spellfunc": COMBAT_RULES.spell_summon_familiar,
        "level_required": 65,
        "desc": "Calls a divine bird to fight at the caster's side. Strength scales with the caster's level.",
        "target": "none",
        "cost": 10,
        "classes": ["augur"],
    },
    "gate": {
        "spellfunc": COMBAT_RULES.spell_gate,
        "level_required": 80,
        "desc": "Teleports the caster to one of a small set of known safe locations.",
        "target": "keyword",
        "cost": 8,
        "combat_spell": False,
        "classes": ["augur"],
    },
    "wrath of olympus": {
        "spellfunc": COMBAT_RULES.spell_attack,
        "level_required": 90,
        "desc": "Mythic tier. A devastating bolt of Olympian lightning.",
        "target": "otherchar",
        "cost": 15,
        "noncombat_spell": False,
        "attack_name": ("A bolt of Olympian lightning", "bolts of Olympian lightning"),
        "damage_range": (45, 65),
        "classes": ["augur"],
    },
    "birdsight": {
        "spellfunc": COMBAT_RULES.spell_scry,
        "level_required": 30,
        "desc": "Reveals who is present in an adjacent room, through a named exit, without entering it.",
        "target": "keyword",
        "cost": 3,
        "combat_spell": False,
        "classes": ["augur"],
    },
    "blessing of fortune": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 25,
        "desc": "Grants an ally a temporary damage boost.",
        "target": "anychar",
        "cost": 5,
        "conditions": [("Damage Up", 4)],
        "classes": ["augur"],
    },
    "omen of weakness": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 20,
        "desc": "Lowers an enemy's defense for a short time.",
        "target": "otherchar",
        "cost": 5,
        "conditions": [("Defense Down", 4)],
        "classes": ["augur"],
    },
    "cure wounds": {
        "spellfunc": COMBAT_RULES.spell_healing,
        "level_required": 1,
        "desc": "Heals a single ally a moderate amount.",
        "target": "anychar",
        "cost": 5,
        "classes": ["medicus", "augur"],
    },
    "mass cure wounds": {
        "spellfunc": COMBAT_RULES.spell_healing,
        "level_required": 40,
        "desc": "Heals up to five allies at once.",
        "target": "anychar",
        "cost": 10,
        "max_targets": 5,
        "classes": ["medicus"],
    },
    "greater restoration": {
        "spellfunc": COMBAT_RULES.spell_healing,
        "level_required": 60,
        "desc": "Heals a single ally for half their maximum HP.",
        "target": "anychar",
        "cost": 12,
        "heal_percent": 0.5,
        "classes": ["medicus"],
    },
    "sacred chant": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "desc": "Grants up to five allies a heal-over-time effect.",
        "target": "anychar",
        "cost": 8,
        "max_targets": 5,
        "conditions": [("Regeneration", 4)],
        "classes": ["medicus"],
    },
    "ward against death": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 50,
        "desc": "The next fatal blow against the warded target instead leaves them at 1 HP.",
        "target": "anychar",
        "cost": 10,
        "conditions": [("Death Ward", 6)],
        "classes": ["medicus"],
    },
    "blessing of asclepius": {
        "spellfunc": COMBAT_RULES.spell_resurrect,
        "level_required": 80,
        "desc": "Mythic tier. Resurrects a dead ally, wherever they are.",
        "target": "deadchar",
        "cost": 18,
        "classes": ["medicus"],
    },
    "sanctuary": {
        "spellfunc": COMBAT_RULES.spell_sanctuary,
        "level_required": 90,
        "desc": "Mythic tier. Equal-or-lower-level characters cannot drag the target into a fight. Higher-level attackers can try to break through, at a cost to their own damage if they succeed. Lasts 1 hour.",
        "target": "anychar",
        "cost": 20,
        "classes": ["medicus"],
    },
    "smite the unclean": {
        "spellfunc": COMBAT_RULES.spell_attack,
        "level_required": 65,
        "desc": "A lance of holy light - Medicus's one offensive spell.",
        "target": "otherchar",
        "cost": 6,
        "noncombat_spell": False,
        "attack_name": ("A lance of holy light", "lances of holy light"),
        "damage_range": (20, 30),
        "classes": ["medicus"],
    },
    "bless": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 15,
        "desc": "Grants an ally a temporary accuracy boost.",
        "target": "anychar",
        "cost": 5,
        "conditions": [("Accuracy Up", 4)],
        "classes": ["medicus"],
    },
    "guardian spirit": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 20,
        "desc": "Grants an ally a temporary defense boost.",
        "target": "anychar",
        "cost": 6,
        "conditions": [("Defense Up", 4)],
        "classes": ["medicus"],
    },
    "divine favor": {
        "spellfunc": COMBAT_RULES.spell_add_condition,
        "level_required": 35,
        "desc": "Grants an ally both an accuracy and a damage boost at once.",
        "target": "anychar",
        "cost": 7,
        "conditions": [("Accuracy Up", 4), ("Damage Up", 4)],
        "classes": ["medicus"],
    },
    "purify": {
        "spellfunc": COMBAT_RULES.spell_cure_condition,
        "level_required": 30,
        "desc": "Cures poison and several other harmful conditions from a single target.",
        "target": "anychar",
        "cost": 6,
        "to_cure": ["Poisoned", "Frightened", "Accuracy Down", "Damage Down", "Defense Down"],
        "classes": ["medicus"],
    },
    "cleanse": {
        "spellfunc": COMBAT_RULES.spell_cure_condition,
        "level_required": 45,
        "desc": "Cures poison and several other harmful conditions from up to five allies at once.",
        "target": "anychar",
        "cost": 10,
        "max_targets": 5,
        "to_cure": ["Poisoned", "Frightened", "Accuracy Down", "Damage Down", "Defense Down"],
        "classes": ["medicus"],
    },
    "vigor": {
        "spellfunc": COMBAT_RULES.spell_restore_mp,
        "level_required": 25,
        "desc": "Restores MP to a target - one of the only ways to recover spent MP outside of resting.",
        "target": "anychar",
        "cost": 8,
        "restore_range": (15, 25),
        "classes": ["medicus"],
    },
    "field dressing": {
        "spellfunc": COMBAT_RULES.spell_healing,
        "level_required": 5,
        "desc": "A fast, smaller heal usable mid-combat.",
        "target": "anychar",
        "cost": 4,
        "healing_range": (30, 50),
        "classes": ["medicus"],
    },
    "antidote": {
        "spellfunc": COMBAT_RULES.spell_cure_condition,
        "level_required": 8,
        "desc": "Cures poison and a few other harmful conditions from a single target.",
        "target": "anychar",
        "cost": 4,
        "to_cure": ["Poisoned", "Frightened", "Accuracy Down", "Damage Down", "Defense Down"],
        "classes": ["medicus"],
    },
    "conjure torch": {
        "spellfunc": COMBAT_RULES.spell_conjure,
        "level_required": 1,
        "desc": "Conjures a simple torch - a small, practical convenience.",
        "target": "none",
        "cost": 2,
        "combat_spell": False,
        "obj_key": "a conjured torch",
        "obj_desc": (
            "A simple pitch-soaked torch, its flame burning with a faint, "
            "unnatural steadiness - a small convenience, conjured rather than "
            "carried."
        ),
        # No "classes" key - available to any caster who bothers to learn it.
    },
}

SKILLS = {
    "sneak": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 4,
        "level_required": 1,
        "conditions": [("Invisible", 3)],
        "classes": ["speculator"],
        "desc": "Turns the user nearly invisible, making them much harder to hit for a short time. Usable in or out of combat.",
    },
    "ambush": {
        "skillfunc": COMBAT_RULES.skill_ambush,
        "target": "otherchar",
        "cost": 5,
        "level_required": 5,
        "combat_spell": False,
        "classes": ["speculator"],
        "desc": "Starts a fight with a burst from hiding, guaranteeing a bonus on the user's first successful attack. Only the user and the ambushed target are drawn in - nobody else in the room. Does not stack with Backstab - only one opener bonus applies per hit.",
    },
    "poisoned blade": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 4,
        "level_required": 8,
        "conditions": [("Poisoned", 4)],
        "classes": ["speculator"],
        "desc": "Coats the user's weapon, applying a poison curse to the target's next hit.",
    },
    "backstab": {
        "skillfunc": COMBAT_RULES.skill_backstab,
        "target": "otherchar",
        "cost": 6,
        "level_required": 15,
        "bonus_damage": 20,
        "noncombat_spell": False,
        "classes": ["speculator"],
        "desc": "Bonus damage against a target who hasn't yet acted in the fight. Requires being already in combat - does not stack with Ambush.",
    },
    "field report": {
        "skillfunc": COMBAT_RULES.skill_field_report,
        "target": "otherchar",
        "cost": 3,
        "level_required": 20,
        "classes": ["speculator"],
        "desc": "Reveals a target's current HP and active conditions to the user's whole party at once.",
    },
    "precision strike": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 5,
        "level_required": 25,
        "conditions": [("Accuracy Down", 3)],
        "classes": ["speculator"],
        "desc": "Lowers a target's accuracy for a short time.",
    },
    "crippling strike": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 6,
        "level_required": 35,
        "conditions": [("Defense Down", 3)],
        "classes": ["speculator"],
        "desc": "Lowers a target's defense for a short time.",
    },
    "smoke and shadow": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 6,
        "level_required": 45,
        "conditions": [("Illusory Duplicate", 3)],
        "classes": ["speculator"],
        "desc": "A burst of evasion, making the user much harder to hit for a short time.",
    },
    "vanish": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 8,
        "level_required": 60,
        "conditions": [("Invisible", 4)],
        "classes": ["speculator"],
        "desc": "A stronger, longer invisibility - usable mid-fight, not just before one.",
    },
    "deathmark": {
        "skillfunc": COMBAT_RULES.skill_deathmark,
        "target": "otherchar",
        "cost": 10,
        "level_required": 90,
        "classes": ["speculator"],
        "desc": "Mythic tier. A blade meant for one throat alone - the user's next attack against the marked target cannot miss and deals heavy bonus damage.",
    },
    "mark": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 4,
        "level_required": 1,
        "conditions": [("Accuracy Down", 3)],
        "classes": ["venator"],
        "desc": "Marks a target as prey, lowering their accuracy for a short time.",
    },
    "keen eye": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 4,
        "level_required": 5,
        "conditions": [("Accuracy Up", 3)],
        "classes": ["venator"],
        "desc": "A hunter's focus - grants the user a temporary accuracy boost.",
    },
    "entangle": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 5,
        "level_required": 10,
        "conditions": [("Defense Down", 3)],
        "classes": ["venator"],
        "desc": "A thrown cord, a snare line, a well-placed trip - whatever the moment calls for. Lowers a target's defense for a short time.",
    },
    "track": {
        "skillfunc": COMBAT_RULES.skill_track,
        "target": "keyword",
        "cost": 3,
        "level_required": 15,
        "combat_spell": False,
        "classes": ["venator"],
        "desc": "Reads the signs to reveal who's present in an adjacent room, through a named exit, without entering it.",
    },
    "piercing shot": {
        "skillfunc": COMBAT_RULES.skill_piercing_shot,
        "target": "otherchar",
        "cost": 6,
        "level_required": 20,
        "damage_range": (20, 30),
        "classes": ["venator"],
        "desc": "An armor-ignoring ranged strike - the target's armor provides no protection against this hit.",
    },
    "rapid volley": {
        "skillfunc": COMBAT_RULES.skill_attack,
        "target": "otherchar",
        "cost": 8,
        "level_required": 30,
        "max_targets": 3,
        "damage_range": (14, 22),
        "classes": ["venator"],
        "desc": "A quick volley of shots, striking up to three targets at once.",
    },
    "snare": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 6,
        "level_required": 40,
        "conditions": [("Poisoned", 4)],
        "classes": ["venator"],
        "desc": "A hidden trap poisons whatever springs it.",
    },
    "call of the wild": {
        "skillfunc": COMBAT_RULES.skill_call_of_the_wild,
        "target": "none",
        "cost": 10,
        "level_required": 50,
        "classes": ["venator"],
        "desc": "Calls a beast companion to fight at the user's side - wolf, boar, or something greater, depending on level.",
    },
    "pack tactics": {
        "skillfunc": COMBAT_RULES.skill_pack_tactics,
        "target": "none",
        "cost": 6,
        "level_required": 70,
        "classes": ["venator"],
        "desc": "Grants a damage boost, but only while an active beast companion is out fighting alongside the user.",
    },
    "bane of the wild hunt": {
        "skillfunc": COMBAT_RULES.skill_attack,
        "target": "otherchar",
        "cost": 12,
        "level_required": 90,
        "max_targets": 5,
        "damage_range": (28, 40),
        "classes": ["venator"],
        "desc": "Mythic tier. A hunt Artemis herself would envy - a devastating volley striking up to five targets at once.",
    },
    "feint": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 4,
        "level_required": 1,
        "conditions": [("Accuracy Down", 3)],
        "classes": ["gladiator"],
        "desc": "A theatrical feint that draws the crowd's eye and leaves the target's guard down - lowers their accuracy for a short time.",
    },
    "weapon mastery": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 5,
        "level_required": 5,
        "conditions": [("Damage Up", 3)],
        "classes": ["gladiator"],
        "desc": "Channels years of arena training into the next few strikes - grants a temporary damage boost.",
    },
    "weapon flourish": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 4,
        "level_required": 10,
        "conditions": [("Accuracy Up", 3)],
        "classes": ["gladiator"],
        "desc": "A flashy display of weapon control - grants a temporary accuracy boost.",
    },
    "disarming strike": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 6,
        "level_required": 15,
        "conditions": [("Damage Down", 3)],
        "classes": ["gladiator"],
        "desc": "A precise strike aimed at the weapon hand - lowers a target's outgoing damage for a short time.",
    },
    "second wind": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 6,
        "level_required": 20,
        "conditions": [("Regeneration", 3)],
        "classes": ["gladiator"],
        "desc": "The crowd's roar carries you through the pain - grants a short heal-over-time.",
    },
    "gory finish": {
        "skillfunc": COMBAT_RULES.skill_gory_finish,
        "target": "otherchar",
        "cost": 8,
        "level_required": 30,
        "threshold_percent": 0.2,
        "damage_range": (30, 45),
        "classes": ["gladiator"],
        "desc": "A cinematic execute - only works against a target already below 20% HP, but hits hard when it does.",
    },
    "riposte": {
        "skillfunc": COMBAT_RULES.skill_riposte,
        "target": "none",
        "cost": 7,
        "level_required": 40,
        "classes": ["gladiator"],
        "desc": "The next hit the user takes triggers an immediate counter-attack against whoever landed it.",
    },
    "finishing blow": {
        "skillfunc": COMBAT_RULES.skill_attack,
        "target": "otherchar",
        "cost": 8,
        "level_required": 50,
        "damage_range": (25, 38),
        "classes": ["gladiator"],
        "desc": "A heavy, direct strike aimed to end a fight quickly.",
    },
    "favor": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 8,
        "level_required": 70,
        "conditions": [("Damage Up", 4), ("Accuracy Up", 4)],
        "classes": ["gladiator"],
        "desc": "The crowd rises to their feet - grants both an accuracy and a damage boost at once.",
    },
    "glory": {
        "skillfunc": COMBAT_RULES.skill_attack,
        "target": "otherchar",
        "cost": 12,
        "level_required": 90,
        "damage_range": (45, 65),
        "classes": ["gladiator"],
        "desc": "Mythic tier. A strike worthy of a legend retold for generations - a massive damage finisher.",
    },
    "hold the line": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 4,
        "level_required": 1,
        "conditions": [("Defense Up", 3)],
        "classes": ["legionary"],
        "desc": "Plants your feet and draws every eye - grants a temporary defense boost.",
    },
    "shield bash": {
        "skillfunc": COMBAT_RULES.skill_attack,
        "target": "otherchar",
        "cost": 5,
        "level_required": 5,
        "damage_range": (15, 25),
        "classes": ["legionary"],
        "desc": "A heavy shield strike, driving a target back.",
    },
    "provoke": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 4,
        "level_required": 10,
        "conditions": [("Accuracy Down", 3)],
        "classes": ["legionary"],
        "desc": "Draws a target's focus and rattles their guard - lowers their accuracy for a short time.",
    },
    "gladius cleave": {
        "skillfunc": COMBAT_RULES.skill_attack,
        "target": "otherchar",
        "cost": 7,
        "level_required": 15,
        "max_targets": 3,
        "damage_range": (14, 22),
        "classes": ["legionary"],
        "desc": "A close-range cleave, striking up to three enemies in front of you at once.",
    },
    "shield wall": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 6,
        "level_required": 25,
        "conditions": [("Defense Up", 4)],
        "classes": ["legionary"],
        "desc": "A stronger defensive stance than Hold the Line - grants a larger defense boost.",
    },
    "testudo": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "anychar",
        "cost": 8,
        "level_required": 35,
        "max_targets": 5,
        "conditions": [("Defense Up", 3)],
        "classes": ["legionary"],
        "desc": "Forms a shield wall - grants up to five allies (use '= party' to hit your whole group at once) a temporary defense boost.",
    },
    "rally": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "anychar",
        "cost": 8,
        "level_required": 45,
        "max_targets": 5,
        "conditions": [("Regeneration", 3)],
        "classes": ["legionary"],
        "desc": "A legionary's discipline steadies the whole unit - grants up to five allies (use '= party' for your whole group) a heal-over-time.",
    },
    "unbreakable": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 10,
        "level_required": 60,
        "conditions": [("Defense Up", 5)],
        "classes": ["legionary"],
        "desc": "A near-total defensive stance, held for longer than any lesser stance.",
    },
    "shattering blow": {
        "skillfunc": COMBAT_RULES.skill_attack,
        "target": "otherchar",
        "cost": 9,
        "level_required": 75,
        "damage_range": (28, 40),
        "classes": ["legionary"],
        "desc": "A heavy strike aimed to break through even the sturdiest guard.",
    },
    "last stand": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "anychar",
        "cost": 14,
        "level_required": 90,
        "max_targets": 5,
        "conditions": [("Defense Up", 5)],
        "classes": ["legionary"],
        "desc": "Mythic tier. The line that will not break, no matter the cost - grants up to five allies (use '= party') a powerful, long-lasting defense boost.",
    },
    "rage of the north": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 5,
        "level_required": 1,
        "conditions": [("Damage Up", 3), ("Defense Down", 3)],
        "classes": ["barbarian"],
        "desc": "A berserker's rage - grants a damage boost, but at the cost of your own defense for the same duration.",
    },
    "reckless swing": {
        "skillfunc": COMBAT_RULES.skill_attack,
        "target": "otherchar",
        "cost": 5,
        "level_required": 5,
        "damage_range": (18, 28),
        "classes": ["barbarian"],
        "desc": "A wild, heavy swing with little regard for form.",
    },
    "war cry": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 7,
        "level_required": 15,
        "max_targets": 3,
        "conditions": [("Accuracy Down", 3)],
        "classes": ["barbarian"],
        "desc": "A roar that shakes nearby enemies' resolve - lowers the accuracy of up to three enemies at once (use '= enemies' to hit whoever's hostile in the room).",
    },
    "thundering maul": {
        "skillfunc": COMBAT_RULES.skill_thundering_maul,
        "target": "otherchar",
        "cost": 8,
        "level_required": 20,
        "damage_range": (30, 45),
        "classes": ["barbarian"],
        "desc": "A heavy two-handed strike. Requires an actual two-handed weapon in hand - won't work with anything else.",
    },
    "intimidating roar": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "otherchar",
        "cost": 6,
        "level_required": 30,
        "conditions": [("Frightened", 2)],
        "classes": ["barbarian"],
        "desc": "A roar that leaves a single enemy too frightened to act for a short time.",
    },
    "ferocity": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 8,
        "level_required": 40,
        "conditions": [("Damage Up", 4)],
        "classes": ["barbarian"],
        "desc": "A stronger, purer rage than Rage of the North - a bigger damage boost, without the defense cost.",
    },
    "reckless abandon": {
        "skillfunc": COMBAT_RULES.skill_reckless_abandon,
        "target": "otherchar",
        "cost": 9,
        "level_required": 50,
        "damage_range": (35, 55),
        "classes": ["barbarian"],
        "desc": "A huge damage strike that leaves the user's own defense down afterward - real risk for real reward.",
    },
    "unstoppable": {
        "skillfunc": COMBAT_RULES.skill_add_condition,
        "target": "self",
        "cost": 10,
        "level_required": 65,
        "conditions": [("Defense Up", 5)],
        "classes": ["barbarian"],
        "desc": "A powerful, sustained defensive resolve that nothing seems able to shake.",
    },
    "earth-shaking slam": {
        "skillfunc": COMBAT_RULES.skill_attack,
        "target": "otherchar",
        "cost": 11,
        "level_required": 80,
        "max_targets": 3,
        "damage_range": (25, 38),
        "classes": ["barbarian"],
        "desc": "A ground-shaking slam striking up to three enemies at once.",
    },
    "fury of the frontier": {
        "skillfunc": COMBAT_RULES.skill_attack,
        "target": "otherchar",
        "cost": 14,
        "level_required": 90,
        "max_targets": 5,
        "damage_range": (32, 48),
        "classes": ["barbarian"],
        "desc": "Mythic tier. A storm of axe and fury the legions still tell campfire stories about - a massive multi-hit rage attack striking up to five enemies at once.",
    },
}

"""
----------------------------------------------------------------------------
EQUIPMENT TYPECLASSES
----------------------------------------------------------------------------
"""


class CombatWeapon(DefaultObject):
    """A weapon which can be wielded in combat with the 'wield' command."""

    rules = COMBAT_RULES

    def at_object_creation(self):
        self.db.damage_range = (15, 25)
        self.db.accuracy_bonus = 0
        self.db.weapon_type_name = "weapon"

    def at_drop(self, dropper):
        if dropper.db.wielded_weapon == self:
            dropper.db.wielded_weapon = None
            dropper.location.msg_contents("%s stops wielding %s." % (dropper, self))

    def at_give(self, giver, getter):
        if giver.db.wielded_weapon == self:
            giver.db.wielded_weapon = None
            giver.location.msg_contents("%s stops wielding %s." % (giver, self))


class CombatArmor(DefaultObject):
    """A set of armor which can be worn with the 'don' command."""

    rules = COMBAT_RULES

    def at_object_creation(self):
        self.db.damage_reduction = 4
        self.db.defense_modifier = -4

    def at_pre_drop(self, dropper):
        if self.rules.is_in_combat(dropper):
            dropper.msg("You can't doff armor in a fight!")
            return False
        return True

    def at_drop(self, dropper):
        if dropper.db.worn_armor == self:
            dropper.db.worn_armor = None
            dropper.location.msg_contents("%s removes %s." % (dropper, self))

    def at_pre_give(self, giver, getter):
        if self.rules.is_in_combat(giver):
            giver.msg("You can't doff armor in a fight!")
            return False
        return True

    def at_give(self, giver, getter):
        if giver.db.worn_armor == self:
            giver.db.worn_armor = None
            giver.location.msg_contents("%s removes %s." % (giver, self))


"""
----------------------------------------------------------------------------
CHARACTER TYPECLASS - MERGED
----------------------------------------------------------------------------
"""


class AutoStatNPC(DefaultCharacter):
    """
    Base typeclass for combat-capable NPCs whose stats should be
    derived automatically from race/class/level, instead of every
    single prototype needing to hand-compute and hardcode hp/mp/sp
    and core stats individually (the old pattern used for the Arena
    Fighters). Set db.race, db.player_class, and db.level in the
    prototype - at_object_post_creation calls derive_npc_stats() and
    applies the results automatically.

    Deliberately uses at_object_post_creation, NOT at_object_creation
    - a real, documented Evennia gotcha: at_object_creation fires
    BEFORE a prototype's own fields (like db.race, db.player_class)
    get applied to the object, so checking for them there always sees
    None and never actually derives anything. at_object_post_creation
    specifically fires after prototype attributes are set, which is
    what this needs. This was a genuine bug in the original version -
    every prototype-spawned NPC using this typeclass silently never
    had its stats derived at all, until this fix.

    Purely flavor/unattackable NPCs (spectators, vendors, the Herald)
    should NOT use this typeclass - they don't need combat stats at
    all, and should stick with plain evennia.objects.objects.
    DefaultCharacter, same as Milo/Titus/Herald already do.
    """

    def at_object_post_creation(self):
        super().at_object_post_creation()

        race = self.db.race
        player_class = self.db.player_class
        level = self.db.level or 1

        if race or player_class:
            stats = derive_npc_stats(race, player_class, level)
            for key, value in stats.items():
                self.attributes.add(key, value)


class HostileNPC(AutoStatNPC):
    """
    Base typeclass for NPCs meant to genuinely fight back - Ludus
    trainers, Arena Fighters. Inherits AutoStatNPC's automatic
    race/class/level-derived stats (so setting db.player_class on the
    prototype gives it both real stats AND, via at_turn_start below, a
    real kit to actually fight with - the two used to be separate,
    non-overlapping typeclasses).

    On its turn, this NPC randomly picks between its basic attack and
    any spell/skill belonging to its class that it's high enough
    level for and can currently afford - calling the exact same
    spellfunc/skillfunc a player's 'cast'/'skill' command would call,
    not a simplified imitation. If the NPC has no player_class set at
    all, it just falls back to always attacking - the same behavior
    HostileNPC always had before this class-awareness was added.
    """

    def _gather_actions(self):
        """
        Returns a list of (kind, name, target_is_self) tuples for
        every usable offensive or self-buff option this NPC's class
        and level currently allow - excluding anything that can't
        function mid-combat (Gate, Track, Ambush's fight-starting
        variant, etc: combat_spell explicitly False) or costs more
        than the NPC currently has.
        """
        actions = [("attack", None, False)]

        npc_class = self.db.player_class
        if not npc_class:
            return actions
        level = self.db.level or 1

        for source_name, source_dict, resource in (
            ("spell", SPELLS, "mp"),
            ("skill", SKILLS, "sp"),
        ):
            for name, data in source_dict.items():
                if not isinstance(data, dict):
                    # Defensive skip - guards against any unexpected
                    # non-dict entries (confirmed root cause: having
                    # world.combat in settings.PROTOTYPE_MODULES made
                    # Evennia treat every module-level dict here as a
                    # prototype, injecting a stray "prototype_key"
                    # entry into SPELLS/SKILLS. Fixed at the settings
                    # level - this check just stays as cheap insurance.
                    continue
                classes = data.get("classes")
                if classes and npc_class not in classes:
                    continue
                if data.get("level_required", 1) > level:
                    continue
                if data.get("combat_spell") is False:
                    continue
                target_type = data.get("target")
                if target_type not in ("otherchar", "anychar", "self"):
                    continue
                have = self.db.mp if resource == "mp" else self.db.sp
                if data["cost"] > (have or 0):
                    continue
                actions.append((source_name, name, target_type == "self"))

        return actions

    def _use_ability(self, kind, name, target):
        """Invokes a chosen spell/skill exactly as CmdCast/CmdUseSkill would."""
        source_dict = SPELLS if kind == "spell" else SKILLS
        data = dict(source_dict[name])
        reserved = {
            "spellfunc", "skillfunc", "target", "cost", "combat_spell",
            "noncombat_spell", "max_targets", "classes", "desc", "level_required",
        }
        kwargs = {k: v for k, v in data.items() if k not in reserved}
        func = data.get("spellfunc") or data.get("skillfunc")
        func(self, name, [target], data["cost"], **kwargs)

    def at_turn_start(self):
        turnhandler = self.db.combat_turnhandler
        if not turnhandler or not turnhandler.pk:
            return

        fighters = turnhandler.db.fighters or []
        possible_targets = [f for f in fighters if f != self and f.db.hp]
        if not possible_targets:
            return
        opponent = possible_targets[0]

        actions = self._gather_actions()
        kind, name, target_is_self = actions[randint(0, len(actions) - 1)]

        if kind == "attack":
            COMBAT_RULES.resolve_attack(self, opponent)
            COMBAT_RULES.spend_action(self, 1, action_name="attack")
            return

        target = self if target_is_self else opponent
        # Spell/skill functions already manage their own action-spend
        # when the caster is in combat - matching exactly how
        # CmdCast/CmdUseSkill invoke them for players, so no separate
        # spend_action call here (that would double-spend the turn).
        self._use_ability(kind, name, target)


class RespawnTimer(DefaultScript):
    """
    A one-shot, persistent timer that brings a defeated RespawningNPC
    back after a delay. Persistent (survives a server reload) rather
    than a bare delay() call - a respawn that got silently cancelled
    by a reload would mean the NPC just never comes back at all,
    exactly the kind of reload-fragility that caused real problems
    with the personal-instance safety-net timer earlier.
    """

    def at_script_creation(self):
        self.persistent = True

    def at_repeat(self):
        npc = self.obj
        home = npc.db.respawn_home if npc else None

        if not npc or not npc.pk or not home or not home.pk:
            # NPC or its home room got destroyed/deleted while
            # waiting - nothing sensible to respawn into, just clean
            # up the timer itself rather than erroring repeatedly.
            self.stop()
            self.delete()
            return

        npc.db.hp = npc.db.max_hp
        npc.move_to(home, quiet=False)
        home.msg_contents("%s arrives, ready to fight again." % npc)

        self.stop()
        self.delete()


class RespawningNPC(HostileNPC):
    """
    A persistent NPC that respawns after being defeated, instead of
    being deleted (the personal-instance model - see spawn_personal_npc)
    or left stuck at 0 HP forever, unfightable by anyone else (a real
    bug the old static Arena Fighters had - nothing ever reset them
    after their first defeat).

    Set db.respawn_delay (seconds) on the prototype to customize the
    wait - defaults to 90 if unset. Intended for shared, standing
    encounters everyone can fight (Ludus trainers, Arena Fighters),
    not one-off personal/story moments like the initial Colosseum
    challenge, which stays on the instance model deliberately.
    """

    def at_object_post_creation(self):
        super().at_object_post_creation()
        self.db.respawns = True
        self.db.respawn_home = self.location


class SummonedAlly(DefaultCharacter):
    """
    Base typeclass for summoned combat allies (Augur's Summon
    Familiar, Haruspex's Summon Lemures, Venator's Call of the Wild).
    Mirrors whoever its owner (db.instance_owner, already set by
    spawn_personal_npc) most recently attacked - a practical
    stand-in for real team/sides logic, which combat doesn't have
    yet. If the owner hasn't attacked anyone yet this fight, falls
    back to attacking anyone present who isn't itself or its owner.
    """

    def at_turn_start(self):
        turnhandler = self.db.combat_turnhandler
        if not turnhandler or not turnhandler.pk:
            return

        fighters = turnhandler.db.fighters or []
        owner = self.db.instance_owner
        target = owner.db.combat_last_target if owner else None

        if not target or target not in fighters or not target.db.hp:
            possible_targets = [
                f for f in fighters if f != self and f != owner and f.db.hp
            ]
            target = possible_targets[0] if possible_targets else None

        if not target:
            return

        COMBAT_RULES.resolve_attack(self, target)
        COMBAT_RULES.spend_action(self, 1, action_name="attack")


class CombatCharacter(ContribRPCharacter):
    """
    A character able to participate in the merged turn-based combat
    system: equipment, items/conditions, and magic all together, plus
    a stamina (SP) resource for physical special moves.

    Also the roleplay system - sdesc, pose, recog, masking - via
    ContribRPCharacter (replaces DefaultCharacter directly, matching
    Evennia's own documented setup; ContribRPCharacter already
    extends DefaultCharacter internally, so this isn't losing any of
    the base character functionality).
    """

    rules = COMBAT_RULES

    def get_display_name(self, looker, **kwargs):
        """
        Checks, in order: (1) is the looker a god (level over 100)?
        Gods see the truth unconditionally, same spirit as a
        superuser bypassing locks - no mask or sdesc hides anything
        from them. (2) Does the looker have a verified_identities
        entry for this character - set by the greet command when
        someone has genuinely introduced themselves? This is
        intentionally independent of the rpsystem contrib's own
        masking/recog logic, not an override of it - masking can only
        affect what super() below would return, and a verified
        identity never reaches that fallback at all. That's what
        makes a real introduction immune to a later mask, while a
        casual, unverified recog still isn't. (3) Otherwise, defer to
        the contrib's normal sdesc/mask/recog behavior.
        """
        if looker is not None:
            looker_level = looker.db.level or 0
            if looker_level > 100:
                return self.key

            verified = looker.db.verified_identities
            if verified and self.id in verified:
                return verified[self.id]
        return super().get_display_name(looker, **kwargs)

    def access(self, accessing_obj, access_type="read", default=False, **kwargs):
        """
        Wizinvis - a god with db.wizinvis set is hidden from anyone
        whose level is lower than their own (so a mortal, or a lower
        god tier, simply doesn't see them in a room's contents/look),
        but stays fully visible to anyone at or above their own level,
        and to true superusers unconditionally. Only affects the
        'view' access type - doesn't touch locks like get/attack/etc,
        so a wizinvis god can still be found by name if someone
        already knows to look (matches real wizinvis behavior in
        other codebases: hidden from casual notice, not truly gone).
        """
        if access_type == "view" and self.db.wizinvis and accessing_obj is not self:
            looker_account = getattr(accessing_obj, "account", None)
            if not (looker_account and looker_account.is_superuser):
                looker_level = 0
                if hasattr(accessing_obj, "db"):
                    looker_level = accessing_obj.db.level or 0
                self_level = self.db.level or 0
                if looker_level < self_level:
                    return False
        return super().access(accessing_obj, access_type=access_type, default=default, **kwargs)

    def process_language(self, text, speaker, language, **kwargs):
        """
        Listener-side hook from the rpsystem contrib - called on every
        receiver of a say/pose/emote with the raw spoken text. Default
        rpsystem behavior only obfuscates text explicitly tagged with
        a language in an emote (langname"..."); this project instead
        treats every utterance as spoken in a real language, defaulting
        to the speaker's currently-set db.speaking (itself defaulting
        to Latin - see world/languages.py and CombatCharacter's
        at_object_creation), so plain 'say' is meaningfully affected
        too, not just explicitly-tagged emotes.

        Gods (level 101+) understand every language unconditionally,
        same "truth cuts through everything" spirit as get_display_name
        above. Anyone who doesn't know the language it was spoken in
        hears it scrambled via rplanguage's own phonetic engine -
        real, consistent nonsense, not just a blank "you don't
        understand."
        """
        effective_language = language or (speaker.db.speaking or "latin")

        level = self.db.level or 1
        known = self.db.known_languages or ["latin"]
        if level > 100 or effective_language in known:
            return "|w%s|n" % text

        from evennia.contrib.rpg.rpsystem import rplanguage

        try:
            garbled = rplanguage.obfuscate_language(text, level=1.0, language=effective_language)
        except Exception:
            garbled = text
        return "|w(in an unfamiliar tongue) %s|n" % garbled

    def msg(self, text=None, from_obj=None, session=None, **kwargs):
        """
        Relays a copy of everything this character receives to anyone
        currently snooping them (see CmdSnoop) - the actual mechanism
        behind snoop, since Evennia has no built-in session-watching
        of its own. Snoopers get a prefixed copy; the target is never
        told they're being watched. Only relays real text messages,
        not e.g. bare OOB/prompt updates, to keep a snooper's own
        screen readable.
        """
        super().msg(text=text, from_obj=from_obj, session=session, **kwargs)
        snoopers = self.db.snoopers
        if snoopers and text:
            display_text = text[0] if isinstance(text, tuple) else text
            if isinstance(display_text, str):
                prefix = "|x[snoop %s]|n " % self.key
                for snooper in list(snoopers):
                    if snooper and snooper.pk and snooper != self:
                        snooper.msg(prefix + display_text)

    def return_appearance(self, looker, **kwargs):
        """
        Adds a custom-title line ahead of the normal appearance text,
        when one is set. db.custom_title only ever showed up on the
        who tables before this - there was genuinely no way to see a
        title in full anywhere else, and no way at all to see another
        character's title if who's column width had cropped it.
        """
        appearance = super().return_appearance(looker, **kwargs)
        if self.db.custom_title:
            return "|Y%s|n\n%s" % (self.db.custom_title, appearance)
        return appearance

    def at_object_creation(self):
        """Called once, when this object is first created."""
        super().at_object_creation()
        # HP
        self.db.max_hp = 100
        self.db.hp = self.db.max_hp
        # MP
        self.db.max_mp = 20
        self.db.mp = self.db.max_mp
        self.db.spells_known = []
        self.db.skills_known = []
        # SP
        self.db.max_sp = 30
        self.db.sp = self.db.max_sp
        # Equipment
        self.db.wielded_weapon = None
        self.db.worn_armor = None
        self.db.unarmed_damage_range = (5, 15)
        self.db.unarmed_accuracy = 30
        # Conditions
        self.db.conditions = {}
        # Level and experience (see xp_for_level/award_xp on CombatRules)
        self.db.level = 1
        self.db.xp = 0
        # Currency - a simple integer balance, not individual coin
        # objects, matching Evennia's own official recommended pattern
        # for this (simpler, no risk of item-count bloat from carrying
        # hundreds of "coin" objects).
        self.db.gold = 0
        # Underworld state - see CombatRules.send_to_underworld/resurrect
        self.db.is_dead = False

        # Core stats (see CORE_STATS block below for how these feed
        # into combat math). Baseline of 10 each - race and class
        # modifiers get layered on top of this during chargen, in
        # world/chargen_menu.py.
        self.db.virtus = 10
        self.db.agilitas = 10
        self.db.ingenium = 10
        self.db.vigor = 10
        # Languages - see world/languages.py and process_language below.
        # Every character starts knowing (and speaking) only Latin.
        self.db.known_languages = ["latin"]
        self.db.speaking = "latin"
        # Subscribe to ticker handler for out-of-combat condition tickdown
        tickerhandler.add(NONCOMBAT_TURN_TIME, self.at_update, idstring="update")

    def at_pre_move(self, destination, move_type="move", **kwargs):
        """
        Prevent moving while in combat, defeated, or resting.

        The hp<=0 block has two exceptions:

        - db.is_dead: a genuinely dead character (level 6+ death -
          see CombatRules.handle_player_defeat) is SUPPOSED to be
          able to walk around the Underworld while hp stays at 0
          ("stats stay at 0 - nothing to restore until they actually
          make it back", by design). Without this, every normal exit
          a dead player tried to use themselves - not just the one
          system move that first drops them at the entrance - would
          silently fail with "You can't move, you've been defeated!",
          making the entire Underworld unwalkable by an actual dead
          player (only reachable at all by someone with hp>0, e.g. a
          superuser testing it). This is genuinely distinct from
          "just got knocked to 0 hp mid-fight, still standing in the
          battle room" - is_dead is only ever true for the specific,
          intentional dead-and-exploring-the-afterlife state.
        - force_move (bool, in kwargs): bypasses the block outright,
          for a system-authorized relocation happening at the exact
          moment hp hits 0 - before is_dead has necessarily been set
          yet, or for any future case that isn't the "wandering the
          Underworld" scenario above.
        """
        if self.rules.is_in_combat(self):
            self.msg("You can't exit a room while in combat!")
            return False
        if self.db.hp <= 0 and not self.db.is_dead and not kwargs.get("force_move"):
            self.msg("You can't move, you've been defeated!")
            return False
        if self.db.resting:
            self.msg("You're resting. Type 'stand' first if you want to move.")
            return False
        return True

    # Tunables for the resting/regen system - percentage of max
    # HP/MP/SP restored per tick, and how often a tick fires. At the
    # defaults, going from near-0 to full takes ~6.7 minutes at any
    # level (the percentage scales with max, so this stays roughly
    # constant rather than taking longer for a higher-level character
    # with a bigger pool).
    REST_TICK_INTERVAL = 10
    REST_TICK_PERCENT = 0.025  # 2.5% per 10s tick = 15%/minute

    def at_rest_tick(self):
        """
        Called every REST_TICK_INTERVAL seconds via TICKER_HANDLER
        while resting. Restores a percentage of max HP/MP/SP each
        tick; once all three are full, resting ends automatically -
        nothing left to wait for.
        """
        if not self.db.resting:
            # Stale ticker somehow still firing after resting already
            # ended some other way - unsubscribe defensively.
            tickerhandler.remove(self.REST_TICK_INTERVAL, self.at_rest_tick)
            return

        for stat in ("hp", "mp", "sp"):
            current = getattr(self.db, stat) or 0
            maximum = getattr(self.db, "max_" + stat) or 0
            if current < maximum:
                gained = max(1, int(maximum * self.REST_TICK_PERCENT))
                self.attributes.add(stat, min(maximum, current + gained))

        if self.db.hp >= self.db.max_hp and self.db.mp >= self.db.max_mp and self.db.sp >= self.db.max_sp:
            self.msg("|gYou feel fully rested.|n")
            self.stop_resting()

    def stop_resting(self):
        """
        Ends the resting state cleanly, wherever it's called from -
        the player typing 'stand', being pulled into combat, or
        reaching full HP/MP/SP naturally. Always safe to call even if
        not currently resting.
        """
        if self.db.resting:
            tickerhandler.remove(self.REST_TICK_INTERVAL, self.at_rest_tick)
            self.db.resting = False

    def at_post_move(self, source_location, move_type="move", **kwargs):
        """
        Called after a successful move. Calls super() FIRST - this is
        what actually shows the new room after moving; skipping it
        (as an earlier version of this method did) silently breaks
        that for everyone, forcing a manual 'look' after every move.
        Only ADDS analytics room-trail tracking on top (see
        world/analytics.py) - harmless no-op for characters with no
        active session tracked.
        """
        super().at_post_move(source_location, move_type=move_type, **kwargs)
        if self.has_account:
            from world.analytics import log_room_visit
            log_room_visit(self)

    def at_post_puppet(self, **kwargs):
        """
        Called right after an account starts puppeting this
        character - i.e. actually logging in and taking control,
        not just authenticating. Starts session analytics tracking
        here instead of the account's own at_post_login, which
        turned out unreliable for this - self.account is confirmed
        directly accessible from this hook (Evennia issue #992),
        avoiding the account-side puppet-lookup timing problems that
        broke two earlier attempts at this.
        """
        super().at_post_puppet(**kwargs)
        if self.has_account:
            from world.analytics import start_session
            start_session(self, self.account)

    def at_post_unpuppet(self, account=None, session=None, **kwargs):
        """
        Called right after an account stops puppeting this character
        - covers logout, disconnect, and switching characters alike.
        Finalizes the session analytics record here instead of the
        account's own at_disconnect - this character-side hook is
        confirmed to still have the character fully accessible with
        the account passed directly as a parameter, unlike
        at_disconnect, which fires only after the character has
        likely already been unpuppeted, making it too late to
        reliably find via the account.
        """
        super().at_post_unpuppet(account=account, session=session, **kwargs)
        if account:
            from world.analytics import end_session
            end_session(self, account)

    def at_turn_start(self):
        """
        Called at the start of this character's turn in combat (by the
        turn handler). Sends the HP/MP/SP prompt and applies any
        conditions that trigger at turn start.
        """
        self.msg(
            "|wIt's your turn! HP: %i/%i  MP: %i/%i  SP: %i/%i|n"
            % (
                self.db.hp,
                self.db.max_hp,
                self.db.mp,
                self.db.max_mp,
                self.db.sp,
                self.db.max_sp,
            )
        )
        self.rules.apply_turn_conditions(self)

    def at_update(self):
        """Fires every NONCOMBAT_TURN_TIME seconds, out of combat."""
        if not self.rules.is_in_combat(self):
            for key in self.db.conditions:
                self.db.conditions[key][1] = self
            self.rules.apply_turn_conditions(self)
            self.rules.condition_tickdown(self, self)


"""
----------------------------------------------------------------------------
SCRIPTS
----------------------------------------------------------------------------
"""


class SanctuaryTimer(DefaultScript):
    """
    A one-shot timer clearing a character's Sanctuary status after
    SANCTUARY_DURATION seconds (Medicus's mythic-tier Sanctuary
    spell). A real Script rather than a plain delay() call, same
    reasoning as the Underworld's CharonTimer - this needs to
    correctly survive a server reload during that hour rather than
    leaving someone's Sanctuary either stuck on forever or silently
    dropped early.
    """

    def at_script_creation(self):
        self.key = "sanctuary_timer"
        self.interval = SANCTUARY_DURATION
        self.repeats = 1
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        character = self.obj
        if not character or not character.pk:
            self.stop()
            return
        character.db.sanctuary_active = False
        character.msg("|mYour Sanctuary fades.|n")
        self.stop()


class InstanceCleanupTimer(DefaultScript):
    """
    A one-shot timer that deletes a personal-instance NPC (see
    spawn_personal_npc above) if its fight is abandoned rather than
    finished. Was a plain delay() call - the confirmed cause of NPCs
    needing a manual `cleanupnpcs` run, since delay() doesn't survive
    a server reload or crash during that window, leaving the instance
    orphaned. As a persistent Script, this timer itself survives a
    reload, so the safety net is now actually safe.
    """

    def at_script_creation(self):
        self.key = "instance_cleanup_timer"
        self.interval = INSTANCE_CLEANUP_TIMEOUT
        self.repeats = 1
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        npc = self.obj
        if npc and npc.pk:
            npc.delete()


class CombatTurnHandler(DefaultScript):
    """
    Handles the progression of combat through turns. Assigned to a room
    when a fight starts; only one fight can happen per room at a time.
    """

    rules = COMBAT_RULES

    def at_script_creation(self):
        self.key = "Combat Turn Handler"
        self.interval = 5
        self.persistent = True

        # Normally sweeps everyone in the room with HP into the fight -
        # but if the room has a pending_fighters list set (by CmdFight
        # or skill_ambush targeting one specific person), use that
        # instead. This is what makes a real 1-on-1 duel possible,
        # rather than "whoever happens to be standing nearby."
        pending = self.obj.ndb.pending_fighters
        if pending:
            self.db.fighters = list(pending)
            self.obj.ndb.pending_fighters = None
            # A real 1v1 duel - two clear sides.
            sides = {pending[0]: "A", pending[1]: "B"}
        else:
            self.db.fighters = []
            for thing in self.obj.contents:
                if thing.db.hp:
                    self.db.fighters.append(thing)
            # 'fight all' - group fighters by party membership, so a
            # group of allies correctly counts as one side rather
            # than each member being treated as an independent
            # combatant (which would make the fight "end" the moment
            # any single ally on the winning team happened to be the
            # last one standing on their side, or never end at all if
            # several teammates all survive). Solo fighters (no
            # party) each still get their own individual side, same
            # as before.
            group_sides = {}
            sides = {}
            for fighter in self.db.fighters:
                leader = fighter.db.party_leader or fighter
                if leader not in group_sides:
                    group_sides[leader] = "team_%d" % len(group_sides)
                sides[fighter] = group_sides[leader]

        for fighter in self.db.fighters:
            self.initialize_for_combat(fighter, side=sides.get(fighter))

        self.obj.db.combat_turnhandler = self

        ordered_by_roll = sorted(self.db.fighters, key=self.rules.roll_init, reverse=True)
        self.db.fighters = ordered_by_roll

        self.obj.msg_contents("Turn order is: %s " % ", ".join(obj.key for obj in self.db.fighters))

        self.db.turn = 0
        self.db.timer = TURN_TIMEOUT
        self.db.timeout_warning_given = False

        self.start_turn(self.db.fighters[0])

    def at_stop(self):
        for fighter in self.db.fighters:
            if fighter:
                self.rules.combat_cleanup(fighter)
        self.obj.db.combat_turnhandler = None

    def at_repeat(self):
        currentchar = self.db.fighters[self.db.turn]

        # Defensive check: a fighter destroyed mid-combat (via
        # @destroy, not a normal defeat) leaves a dangling reference
        # here - @destroy has no way to know to clean itself out of
        # this list. Without this check, the turn cycle can get stuck
        # trying to act on an object that no longer exists. Remove
        # them and move on immediately rather than getting stuck.
        if currentchar is None or not currentchar.pk:
            fighters = self.db.fighters
            fighters.remove(currentchar)
            self.db.fighters = fighters
            if not fighters:
                self.stop()
                self.delete()
                return
            if self.db.turn >= len(fighters):
                self.db.turn = 0
            self.next_turn()
            return

        self.db.timer -= self.interval

        if self.db.timer <= 0:
            self.obj.msg_contents("%s's turn timed out!" % currentchar)
            self.rules.spend_action(currentchar, "all", action_name="disengage")
            return
        elif self.db.timer <= 10 and not self.db.timeout_warning_given:
            currentchar.msg("WARNING: About to time out!")
            self.db.timeout_warning_given = True

    def initialize_for_combat(self, character, side=None):
        self.rules.combat_cleanup(character)
        character.db.combat_actionsleft = 0
        character.db.combat_turnhandler = self
        character.db.combat_lastaction = "null"
        character.db.combat_side = side
        # Being pulled into a fight always ends resting - NPCs don't
        # have this method at all (plain DefaultCharacter, not
        # CombatCharacter), hence the defensive check.
        if hasattr(character, "stop_resting"):
            character.stop_resting()

    def start_turn(self, character):
        """Readies a character for their turn and sends the prompt."""
        character.db.combat_actionsleft = ACTIONS_PER_TURN
        if hasattr(character, "at_turn_start"):
            character.at_turn_start()
        else:
            # Simple objects (like a training dummy) without the full
            # CombatCharacter hooks just get a generic turn announcement.
            character.location.msg_contents("It's %s's turn!" % character)

    def next_turn(self):
        """Advances to the next character in the turn order."""
        # Prune any fighter destroyed mid-combat (via @destroy, or
        # slay's NPC-instance cleanup) before anything else runs.
        #
        # Real root cause of a persistent stuck-loop bug, found via
        # live diagnostics: once a deleted object's reference is
        # reloaded from a persisted attribute (like this list),
        # Evennia resolves it to literal None - not a "ghost" object
        # that merely has pk=None. The original version of this
        # check, `f.pk` for each f, itself crashed with an
        # AttributeError the moment it hit that None entry - meaning
        # the pruning code never even got a chance to run, which is
        # why the fight stayed stuck forever instead of ending: the
        # fix meant to catch this exact scenario was crashing on the
        # very thing it was trying to detect. `f is not None` first,
        # short-circuiting before ever touching `f.pk`, fixes this.
        valid_fighters = [f for f in self.db.fighters if f is not None and f.pk]
        if len(valid_fighters) != len(self.db.fighters):
            if self.db.turn >= len(valid_fighters):
                self.db.turn = 0
            self.db.fighters = valid_fighters
        if not valid_fighters:
            self.stop()
            self.delete()
            return
        if len(valid_fighters) == 1:
            # Everyone else was pruned (destroyed/deleted mid-combat,
            # e.g. slay or @destroy) - the one fighter left standing
            # wins by default.
            self.obj.msg_contents("Only %s remains! Combat is over!" % valid_fighters[0])
            self.stop()
            self.delete()
            return

        disengage_check = all(
            fighter.db.combat_lastaction == "disengage" for fighter in self.db.fighters
        )
        if disengage_check:
            self.obj.msg_contents("All fighters have disengaged! Combat is over!")
            self.stop()
            self.delete()
            return

        # Side-aware victory check: counts how many distinct SIDES
        # still have at least one living member, not just how many
        # individual fighters remain. A raw fighter-count check
        # (the old version) incorrectly ends a fight the instant
        # allies outnumber a defeated solo enemy, or never ends one
        # at all once several allies remain on the same side - it
        # has no concept of who's actually still fighting whom.
        living_sides = set()
        for fighter in self.db.fighters:
            if fighter.db.hp != 0:
                living_sides.add(fighter.db.combat_side)
        if len(living_sides) <= 1:
            winning_side = next(iter(living_sides), None)
            survivors = [
                f for f in self.db.fighters
                if f.db.hp != 0 and f.db.combat_side == winning_side
            ]
            if len(survivors) == 1:
                self.obj.msg_contents("Only %s remains! Combat is over!" % survivors[0])
            elif survivors:
                self.obj.msg_contents(
                    "%s stand triumphant! Combat is over!"
                    % ", ".join(str(f) for f in survivors)
                )
            else:
                self.obj.msg_contents("Combat is over!")
            self.stop()
            self.delete()
            return

        currentchar = self.db.fighters[self.db.turn]
        self.db.turn += 1
        if self.db.turn > len(self.db.fighters) - 1:
            self.db.turn = 0
        newchar = self.db.fighters[self.db.turn]
        # time_until_next_repeat() returns None if the script's own
        # repeating timer hasn't actually started yet - true the very
        # first time next_turn() runs, since the script is created
        # with autostart=False and this can fire during
        # at_script_creation() itself (e.g. an NPC going first and
        # immediately spending its action). Falls back to 0 - nothing
        # meaningful to sync with yet, so just use TURN_TIMEOUT as-is.
        self.db.timer = TURN_TIMEOUT + (self.time_until_next_repeat() or 0)
        self.db.timeout_warning_given = False
        self.obj.msg_contents("%s's turn ends - %s's turn begins!" % (currentchar, newchar))

        # Tick down conditions for everyone against the new current character
        for fighter in self.db.fighters:
            self.rules.condition_tickdown(fighter, newchar)

        self.start_turn(newchar)

    def turn_end_check(self, character):
        if not character.db.combat_actionsleft:
            self.next_turn()
            return

    def infer_join_side(self, character):
        """
        Works out which side a character joining an ongoing fight
        should be on: if any of their party members are already
        fighting, join that ally's side. Otherwise, they're treated
        as a new, independent combatant with their own side - this
        covers both a genuine bystander jumping in and an aggressive
        join like Ambush, where the "joiner" is actually attacking,
        not allying with anyone.
        """
        from world.party import get_party_members

        allies_already_fighting = [
            f for f in get_party_members(character) if f in self.db.fighters
        ]
        if allies_already_fighting:
            return allies_already_fighting[0].db.combat_side
        return "solo_join_%d" % id(character)

    def join_fight(self, character, side=None):
        self.db.fighters.insert(self.db.turn, character)
        self.db.turn += 1
        if side is None:
            side = self.infer_join_side(character)
        self.initialize_for_combat(character, side=side)


"""
----------------------------------------------------------------------------
COMMANDS
----------------------------------------------------------------------------
"""


class CmdFight(Command):
    """
    Starts a fight.

    Usage:
      fight
      fight <target>
      fight all

    With no argument, fights your own personal opponent if you have
    one waiting (from challenge), or the lone other person here if
    there's exactly one - unambiguous, so no name needed. With a
    target, fights just that one person, even if others are nearby.
    'fight all' starts a full brawl with everyone here able to fight
    - the only way to pull in a whole room, never the accidental
    default.

    'fight all' automatically groups combatants by party - your
    whole party fights together as one side against everyone else,
    rather than every person (including your own allies) being
    treated as a separate, individual combatant. See 'help party'
    and 'help groupcombat' for more.
    """

    key = "fight"
    help_category = "combat"
    rules = COMBAT_RULES
    combat_handler_class = CombatTurnHandler

    def _start_duel(self, target):
        caller = self.caller
        here = caller.location

        if not target.db.hp:
            caller.msg("You can't fight that.")
            return
        if target == caller:
            caller.msg("You can't fight yourself.")
            return
        if not self.rules.try_break_sanctuary(caller, target):
            return

        if here.db.combat_turnhandler:
            here.msg_contents("%s joins the fight!" % caller)
            here.db.combat_turnhandler.join_fight(caller)
            return

        here.msg_contents("%s challenges %s to a fight!" % (caller, target))
        here.ndb.pending_fighters = [caller, target]
        here.scripts.add(self.combat_handler_class)

    def func(self):
        caller = self.caller
        here = caller.location

        if caller.db.is_dead:
            caller.msg("You are dead. The living's quarrels are no longer yours.")
            return
        if not caller.db.hp:
            caller.msg("You can't start a fight if you've been defeated!")
            return
        if self.rules.is_in_combat(caller):
            caller.msg("You're already in a fight!")
            return
        if caller.db.resting:
            caller.msg("You're resting. Type 'stand' first if you want to fight.")
            return

        arg = self.args.strip().lower() if self.args else ""

        if arg == "all":
            fighters = []
            for thing in here.contents:
                if thing.db.hp:
                    if thing != caller and not self.rules.try_break_sanctuary(caller, thing):
                        continue
                    fighters.append(thing)
            if len(fighters) <= 1:
                caller.msg("There's nobody here to fight!")
                return
            if here.db.combat_turnhandler:
                here.msg_contents("%s joins the fight!" % caller)
                here.db.combat_turnhandler.join_fight(caller)
                return
            here.msg_contents("%s starts a fight!" % caller)
            here.scripts.add(self.combat_handler_class)
            return

        if arg:
            target = find_combat_target(caller, self.args, candidates=here.contents)
            if not target:
                return
            self._start_duel(target)
            return

        # No target given. First choice: caller's own personal
        # opponent from challenge, if one's still waiting - a direct
        # reference, no name search needed at all, and correctly
        # scoped to just the two of you rather than sweeping the room.
        own_opponent = caller.ndb.active_trainer_npc
        if own_opponent and own_opponent.pk and own_opponent.location == here and own_opponent.db.hp:
            self._start_duel(own_opponent)
            return

        # No personal opponent waiting - fall back to auto-targeting
        # the lone other fighter here, same unambiguous-only rule as
        # attack/powerattack. Multiple candidates now requires an
        # explicit name, or 'fight all' for a real brawl - no more
        # accidentally sweeping a room full of bystanders by default.
        possible = [thing for thing in here.contents if thing != caller and thing.db.hp]
        if len(possible) == 0:
            caller.msg("There's nobody here to fight!")
            return
        if len(possible) > 1:
            caller.msg(
                "Fight whom? More than one possible target - specify a name, "
                "or use 'fight all' to take on everyone here."
            )
            return
        self._start_duel(possible[0])


def find_combat_target(caller, search_text, candidates=None):
    """
    Robust target search for combat commands. Tries the standard,
    sdesc-aware search first (correctly handles other player
    characters, who may be disguised) - if that finds nothing, falls
    back to a plain, case-insensitive key/alias match.

    The fallback matters specifically for NPCs like Rutilus, which
    have no sdesc set up at all (they're plain HostileNPC, not
    ContribRPCharacter-based) - once CombatCharacter merged with
    ContribRPCharacter, the standard search became sdesc-aware for
    the searching player, and it doesn't reliably fall through to a
    plain name match for a target that has no sdesc of its own.
    Without this fallback, an NPC's own real, visible name can fail
    to find them entirely, even typed exactly.
    """
    if candidates is None:
        candidates = caller.location.contents

    search_text = search_text.strip()

    result = caller.search(search_text, candidates=candidates, quiet=True)
    if result:
        return result[0] if isinstance(result, list) else result

    search_lower = search_text.lower()
    for obj in candidates:
        if obj.key.lower().startswith(search_lower):
            return obj
        if any(alias.lower().startswith(search_lower) for alias in obj.aliases.all()):
            return obj

    caller.msg("Could not find '%s'." % search_text)
    return None


class CmdAttack(Command):
    """
    Attacks another character.

    Usage:
      attack <target>
    """

    key = "attack"
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        if self.caller.db.is_dead:
            self.caller.msg("You are dead. You have no quarrel left to settle here.")
            return
        if not self.rules.is_in_combat(self.caller):
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return
        if not self.rules.is_turn(self.caller):
            self.caller.msg("You can only do that on your turn.")
            return
        if not self.caller.db.hp:
            self.caller.msg("You can't attack, you've been defeated.")
            return
        if "Frightened" in self.caller.db.conditions:
            self.caller.msg("You're too frightened to attack!")
            return

        attacker = self.caller

        if not self.args:
            turnhandler = attacker.db.combat_turnhandler
            fighters = turnhandler.db.fighters if turnhandler and turnhandler.pk else []
            other_fighters = [f for f in fighters if f != attacker and f.db.hp]
            if len(other_fighters) == 1:
                defender = other_fighters[0]
            elif len(other_fighters) == 0:
                self.caller.msg("There's no one left to attack.")
                return
            else:
                self.caller.msg(
                    "Attack whom? More than one possible target - specify a name. "
                    "Usage: attack <target>"
                )
                return
        else:
            defender = find_combat_target(self.caller, self.args, candidates=self.caller.location.contents)

        if not defender:
            return
        if not defender.db.hp:
            self.caller.msg("You can't fight that!")
            return
        if attacker == defender:
            self.caller.msg("You can't attack yourself!")
            return

        self.rules.resolve_attack(attacker, defender)
        self.rules.spend_action(self.caller, 1, action_name="attack")


class CmdPowerAttack(Command):
    """
    A stamina-fueled, harder-hitting attack. Costs SP and is less
    accurate than a normal attack, but deals extra damage on a hit.

    Usage:
      powerattack <target>
    """

    key = "powerattack"
    aliases = ["pattack"]
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        if not self.rules.is_in_combat(self.caller):
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return
        if not self.rules.is_turn(self.caller):
            self.caller.msg("You can only do that on your turn.")
            return
        if not self.caller.db.hp:
            self.caller.msg("You can't attack, you've been defeated.")
            return
        if "Frightened" in self.caller.db.conditions:
            self.caller.msg("You're too frightened to attack!")
            return
        if self.caller.db.sp < POWERATTACK_SP_COST:
            self.caller.msg(
                "You don't have enough SP for a power attack. (%i required)"
                % POWERATTACK_SP_COST
            )
            return

        attacker = self.caller

        if not self.args:
            turnhandler = attacker.db.combat_turnhandler
            fighters = turnhandler.db.fighters if turnhandler and turnhandler.pk else []
            other_fighters = [f for f in fighters if f != attacker and f.db.hp]
            if len(other_fighters) == 1:
                defender = other_fighters[0]
            elif len(other_fighters) == 0:
                self.caller.msg("There's no one left to attack.")
                return
            else:
                self.caller.msg(
                    "Power attack whom? More than one possible target - specify a "
                    "name. Usage: powerattack <target>"
                )
                return
        else:
            defender = find_combat_target(self.caller, self.args, candidates=self.caller.location.contents)

        if not defender:
            return
        if not defender.db.hp:
            self.caller.msg("You can't fight that!")
            return
        if attacker == defender:
            self.caller.msg("You can't attack yourself!")
            return

        self.rules.power_attack(attacker, defender)
        self.rules.spend_action(self.caller, 1, action_name="powerattack")


class CmdPass(Command):
    """
    Passes on your turn.

    Usage:
      pass
    """

    key = "pass"
    aliases = ["wait", "hold"]
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        if not self.rules.is_in_combat(self.caller):
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return
        if not self.rules.is_turn(self.caller):
            self.caller.msg("You can only do that on your turn.")
            return
        self.caller.location.msg_contents(
            "%s takes no further action, passing the turn." % self.caller
        )
        self.rules.spend_action(self.caller, "all", action_name="pass")


class CmdQuit(DefaultCmdQuit):
    """
    Same as Evennia's own quit command in every way, except it
    refuses to work while the character actually playing this
    session is mid-combat.

    Deliberately a hard block, not an auto-disengage - the person
    asked for exactly this behavior rather than having their
    character get pulled out of a fight automatically on their
    behalf. To actually leave, use 'disengage' first (not guaranteed
    to succeed - see help disengage), or win/lose the fight, then
    quit normally.

    Note: quit's real func() runs with account_caller=True, meaning
    self.caller here is the ACCOUNT, not a Character - combat state
    lives on the Character, so this checks the character actually
    puppeted by THIS specific session (self.session.puppet), not
    self.caller directly and not just any character owned by the
    account. Only blocks a plain 'quit'; doesn't attempt to reason
    about the rarer 'quit/all' multi-session case.
    """

    def func(self):
        session = self.session
        character = session.puppet if session else None
        if character and COMBAT_RULES.is_in_combat(character):
            self.caller.msg(
                "|rYou cannot quit now! You are still fighting!|n\n"
                "|rTry to |wdisengage|r first, or finish the fight.|n"
            )
            return
        super().func()


class CmdDisengage(Command):
    """
    Attempt to disengage from combat and flee.

    Usage:
      disengage

    Ends your turn and attempts to break away from the fight. Success
    isn't guaranteed - if you fail, you're still in the fight and will
    need to try again next turn (or fight your way out instead).
    """

    key = "disengage"
    aliases = ["spare"]
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        if not self.rules.is_in_combat(self.caller):
            self.caller.msg("You can only do that in combat. (see: help fight)")
            return
        if not self.rules.is_turn(self.caller):
            self.caller.msg("You can only do that on your turn.")
            return

        roll = randint(1, 100)
        if roll <= DISENGAGE_SUCCESS_CHANCE:
            caller = self.caller
            caller.location.msg_contents(
                "%s breaks away and disengages from the fight!" % caller
            )

            # The original version stopped after this message - the
            # player was told they'd escaped but never actually got
            # removed from the fight, so they kept getting turns
            # indefinitely. Fixed: remove from fighters BEFORE
            # spend_action (which calls turn_end_check based on this
            # same list - next_turn() re-reads it directly each time,
            # so this ordering is safe), then combat_cleanup LAST,
            # since spend_action needs combat_turnhandler to still be
            # set in order to call turn_end_check on it at all.
            turnhandler = caller.db.combat_turnhandler
            if turnhandler and turnhandler.pk:
                fighters = turnhandler.db.fighters or []
                if caller in fighters:
                    fighters.remove(caller)
                    turnhandler.db.fighters = fighters
                if turnhandler.db.turn >= len(fighters):
                    turnhandler.db.turn = 0

            self.rules.spend_action(caller, "all", action_name="disengage")
            self.rules.combat_cleanup(caller)
        else:
            self.caller.msg(
                "|rYou try to break away, but can't shake free - you're still in "
                "the fight!|n"
            )
            self.caller.location.msg_contents(
                "%s tries to flee but fails to break away!" % self.caller,
                exclude=self.caller,
            )
            self.rules.spend_action(self.caller, "all", action_name="failed_disengage")


class CmdRest(Command):
    """
    Begin resting to gradually recover HP, MP, and SP over time.

    Usage:
      rest

    Resting isn't instant - it restores a percentage of your max
    HP/MP/SP every few seconds, reaching full in a few minutes rather
    than all at once. While resting, you can't move or fight - type
    'stand' to get up early, or being pulled into a fight will end it
    for you automatically. You can only start resting if you're not
    already in combat.

    For instant recovery instead, a healing spell or item is still
    the way to go - resting is deliberately the slow option.
    """

    key = "rest"
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        caller = self.caller
        if self.rules.is_in_combat(caller):
            caller.msg("You can't rest while you're in combat.")
            return
        if caller.db.resting:
            caller.msg("You're already resting.")
            return
        if caller.db.hp >= caller.db.max_hp and caller.db.mp >= caller.db.max_mp and caller.db.sp >= caller.db.max_sp:
            caller.msg("You're already at full HP, MP, and SP.")
            return

        caller.db.resting = True
        tickerhandler.add(caller.REST_TICK_INTERVAL, caller.at_rest_tick)
        caller.location.msg_contents(
            "%s settles in to rest, recovering slowly." % caller
        )


class CmdStand(Command):
    """
    Get up from resting.

    Usage:
      stand

    Ends resting early - whatever HP/MP/SP you've recovered so far is
    kept, you just stop gaining more. Only relevant while resting;
    does nothing otherwise.
    """

    key = "stand"
    help_category = "combat"

    def func(self):
        caller = self.caller
        if not caller.db.resting:
            caller.msg("You're not resting.")
            return
        caller.stop_resting()
        caller.location.msg_contents("%s stands up." % caller)


class CmdChallenge(Command):
    """
    Challenge this room's trainer to a private duel.

    Usage:
      challenge

    Spawns a personal opponent just for you, so you never have to wait
    in line behind other players fighting for the same trainer. Once
    the duel ends - win or lose - your opponent disappears. Works in
    any room set up as a training or trial ground.
    """

    key = "challenge"
    help_category = "combat"

    def func(self):
        caller = self.caller
        proto = caller.location.db.trainer_prototype

        if not proto:
            caller.msg("There's no one here to challenge.")
            return

        existing = caller.ndb.active_trainer_npc
        if existing and existing.pk:
            caller.msg(
                "You already have an opponent waiting - deal with %s first."
                % existing.key
            )
            return

        opponent = COMBAT_RULES.spawn_personal_npc(proto, caller)
        caller.ndb.active_trainer_npc = opponent

        caller.location.msg_contents(
            "%s steps forward to challenge an opponent!" % caller, exclude=caller
        )
        caller.msg(
            "%s steps forward to face you. Type |wfight|n to begin." % opponent.key
        )


class CmdCoreStats(Command):
    """
    Shows your full character sheet - identity, progression, current
    resources, and core stats all in one place.

    Usage:
      stats
    """

    key = "stats"
    help_category = "combat"

    def func(self):
        char = self.caller
        if char.db.virtus is None:
            char.msg("You don't seem to have core stats set up.")
            return

        race_display = char.db.race_display or "Unknown"
        class_display = char.db.class_display or "-"
        level = char.db.level or 1
        title = rank_title(level)
        custom_title = char.db.custom_title
        xp = char.db.xp or 0
        xp_needed = COMBAT_RULES.xp_for_level(level) if level < MAX_LEVEL else None

        lines = [
            "|w%s|n" % char.key,
        ]
        if custom_title:
            lines.append("  |Y%s|n" % custom_title)
        lines += [
            "  %s, %s" % (race_display, class_display),
            "  Level %d (%s)" % (level, title),
        ]
        if xp_needed is not None:
            lines.append("  XP: %d / %d to next level" % (xp, xp_needed))
        else:
            lines.append("  XP: max level reached")

        lines.append("")
        lines.append(
            "|wHP:|n %d/%d  |cMP:|n %d/%d  |gSP:|n %d/%d"
            % (
                char.db.hp, char.db.max_hp,
                char.db.mp, char.db.max_mp,
                char.db.sp, char.db.max_sp,
            )
        )
        lines.append("|YGold:|n %d" % (char.db.gold or 0))

        lines.append("")
        lines.append("|wCore Stats|n")
        lines.append("  Virtus (Strength):       %d  - melee/heavy weapon damage" % char.db.virtus)
        lines.append("  Agilitas (Agility):      %d  - accuracy, dodge, initiative, ranged/light weapon damage" % char.db.agilitas)
        lines.append("  Ingenium (Intelligence): %d  - spell damage and healing" % char.db.ingenium)
        lines.append("  Vigor (Constitution):    %d  - extra Max HP/MP, flat damage reduction" % char.db.vigor)

        char.msg("\n".join(lines))


class CmdCleanupNPCs(Command):
    """
    Finds and destroys orphaned personal-instance NPCs - opponents
    spawned by challenge that never got properly cleaned up.

    Usage:
      cleanupnpcs
      cleanupnpcs confirm

    These NPCs are supposed to clean themselves up automatically -
    either the moment they're properly defeated, or via a 10-minute
    safety timer (InstanceCleanupTimer, a persistent Script) if a
    fight is challenged but never actually finished. That timer now
    survives a server reload, so this should rarely find anything -
    it remains as a safety net for the genuinely rare case of combat
    getting stuck before resolving normally, or a crash before the
    timer was even attached.

    With no argument, this only LISTS what it finds - nothing gets
    destroyed. Review the list, then run 'cleanupnpcs confirm' to
    actually destroy everything listed. Anyone still genuinely mid-
    fight is automatically skipped and left alone, never touched.
    """

    key = "cleanupnpcs"
    locks = "cmd:perm(Admin)"
    help_category = "admin"

    def func(self):
        caller = self.caller
        candidates = HostileNPC.objects.filter(db_attributes__db_key="instance_owner")

        orphaned = []
        for npc in candidates:
            if not npc.pk:
                continue
            turnhandler = npc.db.combat_turnhandler
            if turnhandler and turnhandler.pk:
                # Still genuinely in an active fight - leave it alone.
                continue
            orphaned.append(npc)

        if not orphaned:
            caller.msg("No orphaned personal NPCs found.")
            return

        lines = ["|wOrphaned personal NPCs found:|n"]
        for npc in orphaned:
            location = npc.location.key if npc.location else "nowhere"
            lines.append("  %s (in: %s)" % (npc.key, location))

        if self.args and self.args.strip().lower() == "confirm":
            count = len(orphaned)
            for npc in orphaned:
                npc.delete()
            caller.msg("\n".join(lines))
            caller.msg("|gDestroyed %d orphaned NPC(s).|n" % count)
        else:
            caller.msg("\n".join(lines))
            caller.msg("|y(Run 'cleanupnpcs confirm' to destroy these.)|n")


class CmdSlay(Command):
    """
    Instantly slay a target - a god's power over life and death.

    Usage:
      slay <target>

    Sets the target's HP to 0 immediately, triggering the exact same
    real consequences an ordinary combat defeat would - an NPC is
    defeated normally, while a player character is sent to the
    Underworld (or a safe respawn, if below level 6) exactly as if
    they'd lost a genuine fight. Works whether or not the target is
    currently in combat. Only available to gods (level over 100), and
    only against mortals - no god can slay another god, Rex Divum
    included.
    """

    key = "slay"
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        caller = self.caller
        level = caller.db.level or 0
        if level <= 100:
            caller.msg("Only the gods hold this power.")
            return

        if not self.args:
            caller.msg("Slay whom? Usage: slay <target>")
            return

        target = find_combat_target(caller, self.args, candidates=caller.location.contents)
        if not target:
            return
        if not target.attributes.has("max_hp"):
            caller.msg("That cannot be slain.")
            return
        if (target.db.level or 0) > 100:
            caller.msg("%s is a god - beyond your power to slay." % target.key)
            return
        if target.db.hp is not None and target.db.hp <= 0:
            caller.msg("%s is already dead." % target.key)
            return

        target.db.hp = 0
        caller.location.msg_contents(
            "|r%s raises a hand, and %s simply... stops.|n" % (caller, target)
        )

        if target.has_account:
            self.rules.handle_player_defeat(target, attacker=caller)
        else:
            self.rules.at_defeat(target, attacker=caller)


def _permission_rank(permname):
    """
    Index of a permission string within settings.PERMISSION_HIERARCHY
    (higher = more authority), or -1 if it's not a real permission
    (used for the god tiers - 101 and 106 - that don't grant one).
    Local helper for CmdGodLevel's "can't promote above your own
    authority" check below.
    """
    from django.conf import settings

    try:
        return [p.lower() for p in settings.PERMISSION_HIERARCHY].index(permname.lower())
    except (ValueError, AttributeError):
        return -1


class CmdGodLevel(Command):
    """
    Set a character's level directly - the Cursus Divinorum's
    'advance', and also the general-purpose way to set anyone's
    mortal level for testing or events.

    Usage:
      godlevel <character> = <level>

    Works across the whole range, not just the god tiers: 'godlevel
    Marcus = 50' sets a mortal's level exactly as much as 'godlevel
    Marcus = 103' would raise them to Aedilis. For levels 102-105,
    the matching Evennia permission (Helper/Builder/Admin/Developer)
    is granted or revoked automatically, so rank and real command
    access always move together - there's no separate step.

    Level 106 (Rex Divum) can't be granted through this command at
    all - it isn't a rank anyone is promoted into, it only ever
    describes whoever already holds the true superuser account.

    Crossing into godhood (any level over 100) also sets the target's
    displayed race to 'Olympian' and their displayed class to their
    own divine domain (e.g. Jupiter -> 'King of the Sky', looked up
    from db.divine_presence) rather than their tier's rank title -
    that's already shown as the level itself, so repeating it as
    'class' too would just be the same fact twice. Their original
    mortal race/class is kept and restored automatically if they're
    ever demoted back to 100 or below.

    Requires Praeses (104) or true superuser to use at all, and you
    can never raise anyone to a level whose permission outranks your
    own (a Praeses/Admin can promote up to Praeses, but only a Numen
    Regnant/Developer or the superuser can grant Numen Regnant itself).
    """

    key = "godlevel"
    aliases = ["advance"]
    help_category = "admin"

    def func(self):
        caller = self.caller
        is_superuser = bool(caller.account and caller.account.is_superuser)
        caller_level = caller.db.level or 1

        if caller_level < 104 and not is_superuser:
            caller.msg("You lack the authority to change anyone's level.")
            return

        if not self.args or "=" not in self.args:
            caller.msg("Usage: godlevel <character> = <level>")
            return

        lhs, rhs = self.args.split("=", 1)
        target = caller.search(lhs.strip(), global_search=True)
        if not target:
            return

        try:
            new_level = int(rhs.strip())
        except ValueError:
            caller.msg("Level must be a whole number.")
            return

        if new_level < 1 or new_level > 105:
            caller.msg(
                "Level must be between 1 and 105 - 106 (Rex Divum) can't be "
                "granted, it only ever describes a true superuser."
            )
            return

        if not is_superuser:
            new_perm = GOD_TIERS.get(new_level, (None, None))[1]
            caller_perm = GOD_TIERS.get(caller_level, (None, None))[1]
            if new_perm and _permission_rank(new_perm) > _permission_rank(caller_perm or ""):
                caller.msg(
                    "You can't grant a rank with more authority than your own."
                )
                return

        # Clear out whichever god-tier permission this system may have
        # previously granted the target, before applying the new one -
        # otherwise repeated promotions/demotions would just pile up
        # permissions rather than the target's access matching their
        # current level.
        old_perm = target.db.godlevel_permission
        if old_perm:
            target.permissions.remove(old_perm)
            target.db.godlevel_permission = None

        old_level = target.db.level or 1
        target.db.level = new_level
        target.db.invincible = new_level > 100

        new_perm = GOD_TIERS.get(new_level, (None, None))[1]
        if new_perm:
            target.permissions.add(new_perm)
            target.db.godlevel_permission = new_perm

        # Race/class on ascension: every god's race_display becomes
        # "Olympian" - a mortal race stops meaning anything once
        # someone is a literal god, extending the "Olympian" flavor
        # Jupiter already used before this system existed. class_display
        # is deliberately NOT set to the tier title (Auspex, Aedilis,
        # ...) - that's already shown as the level/rank itself (e.g. on
        # 'who'), and repeating it as "class" too is pure redundancy,
        # the same fact shown twice under different labels. Instead
        # class_display becomes the god's own domain (e.g. Jupiter ->
        # "King of the Sky"), looked up from world/god_help.py's
        # PANTHEON data via whatever db.divine_presence is already set
        # to - a second, genuinely different axis of information (WHO
        # this god is) rather than a restatement of HOW senior they
        # are. Falls back to "Divine" (the exact generic value Jupiter
        # himself used before this system existed) if divine_presence
        # isn't set to a recognized deity yet. The character's actual
        # mortal race_display/class_display are preserved so a later
        # demotion back to level 100 or below can restore them.
        if new_level > 100 and old_level <= 100:
            target.db.mortal_race_display = target.db.race_display
            target.db.mortal_class_display = target.db.class_display
        if new_level > 100:
            from world.god_help import god_domain

            target.db.race_display = "Olympian"
            target.db.class_display = god_domain(target.db.divine_presence) or "Divine"
        elif old_level > 100 and new_level <= 100:
            if target.db.mortal_race_display:
                target.db.race_display = target.db.mortal_race_display
            if target.db.mortal_class_display:
                target.db.class_display = target.db.mortal_class_display

        title = rank_title(new_level)
        caller.msg("|gSet %s to level %d (%s).|n" % (target.key, new_level, title))
        target.msg("|yYour level has been set to %d (%s).|n" % (new_level, title))


class CmdWizInvis(Command):
    """
    Turn wizinvis on or off - a god's invisibility to those beneath them.

    Usage:
      wizinvis
      wizinvis off

    While active, you're hidden from anyone whose level is lower than
    your own - they won't see you in a room's contents or in 'look',
    and you won't be announced arriving or departing. Anyone at or
    above your own level, and any true superuser, sees straight
    through it regardless. Requires Auspex (level 102) or higher.
    """

    key = "wizinvis"
    help_category = "admin"

    def func(self):
        caller = self.caller
        level = caller.db.level or 0
        is_superuser = bool(caller.account and caller.account.is_superuser)
        if level < 102 and not is_superuser:
            caller.msg("You lack the standing to go unseen.")
            return

        if self.args and self.args.strip().lower() == "off":
            if not caller.db.wizinvis:
                caller.msg("You're already visible.")
                return
            caller.db.wizinvis = False
            caller.msg("|yYou are visible once more.|n")
            return

        if caller.db.wizinvis:
            caller.msg("You're already unseen.")
            return
        caller.db.wizinvis = True
        caller.msg("|yYou fade from the sight of those beneath you.|n")


class CmdRestore(Command):
    """
    Fully restore a character's HP, MP, and SP.

    Usage:
      restore <character>
      restore me

    Requires Auspex (level 102) or higher.
    """

    key = "restore"
    help_category = "admin"

    def func(self):
        caller = self.caller
        level = caller.db.level or 0
        is_superuser = bool(caller.account and caller.account.is_superuser)
        if level < 102 and not is_superuser:
            caller.msg("You lack the standing to work this restoration.")
            return

        if not self.args:
            caller.msg("Usage: restore <character>")
            return

        target = caller.search(self.args.strip(), global_search=True)
        if not target:
            return
        if not target.attributes.has("max_hp"):
            caller.msg("That can't be restored.")
            return

        target.db.hp = target.db.max_hp
        target.db.mp = target.db.max_mp
        target.db.sp = target.db.max_sp
        caller.msg("|gRestored %s to full HP/MP/SP.|n" % target.key)
        if target != caller:
            target.msg("|gA divine touch restores you fully.|n")


class CmdSnoop(Command):
    """
    Secretly monitor everything a character sees.

    Usage:
      snoop <character>
      snoop off <character>

    Silently relays everything the target receives to you, prefixed
    so you can tell it apart from your own surroundings. The target is
    never notified. Shows their output only, not their raw keystrokes.
    Requires Auspex (level 102) or higher.
    """

    key = "snoop"
    help_category = "admin"

    def func(self):
        caller = self.caller
        level = caller.db.level or 0
        is_superuser = bool(caller.account and caller.account.is_superuser)
        if level < 102 and not is_superuser:
            caller.msg("You lack the standing to snoop.")
            return

        args = self.args.strip()
        if not args:
            caller.msg("Usage: snoop <character> | snoop off <character>")
            return

        turning_off = False
        if args.lower().startswith("off "):
            turning_off = True
            args = args[4:].strip()

        target = caller.search(args, global_search=True)
        if not target:
            return
        if target == caller:
            caller.msg("You can't snoop yourself.")
            return

        snoopers = target.db.snoopers or []
        if turning_off:
            if caller in snoopers:
                snoopers.remove(caller)
                target.db.snoopers = snoopers
                caller.msg("You stop snooping %s." % target.key)
            else:
                caller.msg("You aren't snooping %s." % target.key)
            return

        if caller in snoopers:
            caller.msg("You're already snooping %s." % target.key)
            return
        snoopers.append(caller)
        target.db.snoopers = snoopers
        caller.msg("|yYou begin snooping %s. Their output will appear prefixed.|n" % target.key)


class CmdGreet(Command):
    """
    Formally introduce yourself to someone, revealing your real name.

    Usage:
      greet <target>

    Unlike an ordinary recog, this creates a genuine, verified
    introduction - the person you greet will always know your real
    identity from now on, even if you later put on a disguise. This
    is one-directional: greeting someone tells them who you are, but
    doesn't automatically reveal their identity to you in return -
    if you want to know who they are, they need to greet you back.

    You don't need to type someone's full description exactly - a
    distinguishing word or two is enough, the same way you'd refer
    to anyone else you can see but don't fully recognize.
    """

    key = "greet"
    help_category = "general"

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg("Greet whom? Usage: greet <target>")
            return

        target = caller.search(self.args, candidates=caller.location.contents)
        if not target:
            return
        if target == caller:
            caller.msg("You already know who you are.")
            return
        if not target.has_account:
            caller.msg("There's no point introducing yourself to that.")
            return

        old_display = caller.get_display_name(target)

        verified = target.db.verified_identities or {}
        verified[caller.id] = caller.key
        target.db.verified_identities = verified

        target.msg(
            "%s steps forward and introduces themselves: \"I am %s.\""
            % (old_display, caller.key)
        )
        caller.msg("You introduce yourself to %s." % target.get_display_name(caller))


class FriendlyCmdMask(CmdMask):
    """
    Disguise yourself, hiding your real identity from others.

    Usage:
      mask <new description>
      unmask

    While disguised, everyone sees the description you choose here
    instead of how you normally appear - and anyone who only knew
    you casually (through a passing recog) won't recognize you
    anymore either. The one exception: anyone you've properly
    greeted, or who has greeted you, will still know exactly who you
    are, disguise or not - a real introduction can't be undone by
    just changing your appearance.
    """

    # No func() override - this only replaces the help text above.
    # The actual masking behavior is entirely inherited, unchanged,
    # from the real CmdMask this subclasses.


class CmdConsider(Command):
    """
    Size up how dangerous a fight would be before you commit to one.

    Usage:
      consider <target>

    Gives a plain-language read on how the target compares to you,
    based on level - not exact numbers, just enough to know whether
    a fight is safe, risky, or suicidal before you're already in it.
    Works on NPCs and other players alike.
    """

    key = "consider"
    help_category = "combat"

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg("Consider whom? Usage: consider <target>")
            return

        target = caller.search(self.args, candidates=caller.location.contents)
        if not target:
            return
        if not target.attributes.has("max_hp"):
            caller.msg("That's not something you can fight.")
            return
        if target == caller:
            caller.msg("You already know exactly how dangerous you are.")
            return

        my_level = caller.db.level or 1
        their_level = target.db.level
        if their_level is None:
            caller.msg(
                "You can't get a read on how dangerous %s might be." % target.key
            )
            return

        diff = their_level - my_level

        if diff <= -15:
            verdict = "This opponent looks like no real challenge for you at all."
        elif diff <= -5:
            verdict = "This opponent looks easy for you."
        elif diff <= 4:
            verdict = "This looks like a fair, even fight."
        elif diff <= 14:
            verdict = "This opponent looks tough - be careful."
        elif diff <= 29:
            verdict = "|yThis opponent could seriously hurt you. Think twice.|n"
        else:
            verdict = "|rFighting this would be suicide. Do not engage.|n"

        caller.msg("You size up %s.\n%s" % (target.key, verdict))


class CmdStatus(Command):
    """
    Shows your current and maximum HP, MP, and SP.

    Usage:
      status
    """

    key = "status"
    aliases = ["prompt"]
    help_category = "combat"

    def func(self):
        char = self.caller
        if not char.db.max_hp:
            self.caller.msg("You don't seem to have combat stats set up. Try 'update self'.")
            return
        char.msg(
            "|wHP:|n %i/%i  |cMP:|n %i/%i  |gSP:|n %i/%i"
            % (
                char.db.hp,
                char.db.max_hp,
                char.db.mp,
                char.db.max_mp,
                char.db.sp,
                char.db.max_sp,
            )
        )


class CmdWield(Command):
    """
    Wield a weapon you are carrying.

    Usage:
      wield <weapon>
    """

    key = "wield"
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        if self.rules.is_in_combat(self.caller):
            if not self.rules.is_turn(self.caller):
                self.caller.msg("You can only do that on your turn.")
                return
        if not self.args:
            self.caller.msg("Usage: wield <obj>")
            return
        weapon = self.caller.search(self.args, candidates=self.caller.contents)
        if not weapon:
            return
        if not weapon.is_typeclass("world.combat.CombatWeapon", exact=True):
            self.caller.msg("That's not a weapon!")
            return

        if not self.caller.db.wielded_weapon:
            self.caller.db.wielded_weapon = weapon
            self.caller.location.msg_contents("%s wields %s." % (self.caller, weapon))
        else:
            old_weapon = self.caller.db.wielded_weapon
            self.caller.db.wielded_weapon = weapon
            self.caller.location.msg_contents(
                "%s lowers %s and wields %s." % (self.caller, old_weapon, weapon)
            )

        if not self.rules.is_proficient(self.caller, weapon):
            self.caller.msg(
                "|y(You aren't trained in this kind of weapon - you'll fight "
                "noticeably worse with it than with something you know.)|n"
            )

        if self.rules.is_in_combat(self.caller):
            self.rules.spend_action(self.caller, 1, action_name="wield")


class CmdUnwield(Command):
    """
    Stop wielding a weapon.

    Usage:
      unwield
    """

    key = "unwield"
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        if self.rules.is_in_combat(self.caller):
            if not self.rules.is_turn(self.caller):
                self.caller.msg("You can only do that on your turn.")
                return
        if not self.caller.db.wielded_weapon:
            self.caller.msg("You aren't wielding a weapon!")
        else:
            old_weapon = self.caller.db.wielded_weapon
            self.caller.db.wielded_weapon = None
            self.caller.location.msg_contents("%s lowers %s." % (self.caller, old_weapon))


class CmdDon(Command):
    """
    Don armor that you are carrying.

    Usage:
      don <armor>
    """

    key = "don"
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        if self.rules.is_in_combat(self.caller):
            self.caller.msg("You can't don armor in a fight!")
            return
        if not self.args:
            self.caller.msg("Usage: don <obj>")
            return
        armor = self.caller.search(self.args, candidates=self.caller.contents)
        if not armor:
            return
        if not armor.is_typeclass("world.combat.CombatArmor", exact=True):
            self.caller.msg("That's not armor!")
            return

        if not self.caller.db.worn_armor:
            self.caller.db.worn_armor = armor
            self.caller.location.msg_contents("%s dons %s." % (self.caller, armor))
        else:
            old_armor = self.caller.db.worn_armor
            self.caller.db.worn_armor = armor
            self.caller.location.msg_contents(
                "%s removes %s and dons %s." % (self.caller, old_armor, armor)
            )


class CmdDoff(Command):
    """
    Stop wearing armor.

    Usage:
      doff
    """

    key = "doff"
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        if self.rules.is_in_combat(self.caller):
            self.caller.msg("You can't doff armor in a fight!")
            return
        if not self.caller.db.worn_armor:
            self.caller.msg("You aren't wearing any armor!")
        else:
            old_armor = self.caller.db.worn_armor
            self.caller.db.worn_armor = None
            self.caller.location.msg_contents("%s removes %s." % (self.caller, old_armor))


class CmdUse(MuxCommand):
    """
    Use an item.

    Usage:
      use <item> [= target]
    """

    key = "use"
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        item = self.caller.search(self.lhs, candidates=self.caller.contents)
        if not item:
            return

        target = None
        if self.rhs:
            # Same rpsystem sdesc-search fix as attack/cast/skill -
            # see find_combat_target's docstring.
            target = find_combat_target(self.caller, self.rhs, candidates=self.caller.location.contents)
            if not target:
                return

        if self.rules.is_in_combat(self.caller):
            if not self.rules.is_turn(self.caller):
                self.caller.msg("You can only use items on your turn.")
                return

        if not item.db.item_func:
            self.caller.msg("'%s' is not a usable item." % item.key.capitalize())
            return

        if item.attributes.has("item_uses"):
            if item.db.item_uses <= 0:
                self.caller.msg("'%s' has no uses remaining." % item.key.capitalize())
                return

        self.rules.use_item(self.caller, item, target)


class CmdLearnSpell(Command):
    """
    Learn a magic spell.

    Usage:
        learnspell <spell name>
    """

    key = "learnspell"
    help_category = "magic"

    def func(self):
        spell_list = sorted(SPELLS.keys())
        args = self.args.lower().strip(" ")
        caller = self.caller
        spell_to_learn = []

        if not args or len(args) < 3:
            caller.msg(
                "Usage: learnspell <spell name>\n"
                "Not sure what's available? Try 'spellinfo' to see your full spellbook."
            )
            return

        # Prefer an exact match first, to avoid ambiguity between spells
        # whose names are substrings of one another (e.g. "cure wounds"
        # vs. "mass cure wounds").
        if args in spell_list:
            spell_to_learn = [args]
        else:
            for spell in spell_list:
                if args in spell.lower():
                    spell_to_learn.append(spell)

        if not spell_to_learn:
            caller.msg("There is no spell with that name.")
            return
        if len(spell_to_learn) > 1:
            matched_spells = ", ".join(spell_to_learn)
            caller.msg("Which spell do you mean: %s?" % matched_spells)
            return

        spell_to_learn = spell_to_learn[0]

        # Class-gating: a spell with a "classes" list can only be
        # learned by characters whose player_class is in that list.
        # Spells with no "classes" key (like cactus conjuration) are
        # open to everyone.
        allowed_classes = SPELLS[spell_to_learn].get("classes")
        if allowed_classes and caller.db.player_class not in allowed_classes:
            caller.msg(
                "Your training doesn't include the spell '%s'. That knowledge "
                "belongs to another path." % spell_to_learn
            )
            return

        level_required = SPELLS[spell_to_learn].get("level_required", 1)
        caller_level = caller.db.level or 1
        if caller_level < level_required:
            caller.msg(
                "You aren't experienced enough for '%s' yet - it requires level %d "
                "(you are level %d)." % (spell_to_learn, level_required, caller_level)
            )
            return

        if spell_to_learn not in caller.db.spells_known:
            caller.db.spells_known.append(spell_to_learn)
            caller.msg("You learn the spell '%s'!" % spell_to_learn)
        else:
            caller.msg("You already know the spell '%s'!" % spell_to_learn)


class CmdCast(MuxCommand):
    """
    Cast a magic spell that you know.

    Usage:
        cast <spellname> [= <target1>, <target2>, etc...]
        cast <spellname> = party
        cast <spellname> = allies
        cast <spellname> = enemies

    You don't need to type a spell's full name - a unique partial
    match works too (e.g. "cast fortune" for "blessing of fortune"),
    as long as it's not ambiguous among what you know.

    For a spell that can affect more than one target, "party" and
    "allies" (same thing, either word works) target your whole party
    roster at once instead of naming each ally individually.
    "enemies" does the same for every hostile-capable target in the
    room, up to the spell's limit.
    """

    key = "cast"
    help_category = "magic"
    rules = COMBAT_RULES

    def func(self):
        caller = self.caller

        if caller.db.is_dead:
            caller.msg("The dead have no power to cast spells - only to be released from where they wait.")
            return

        if "Silenced" in (caller.db.conditions or {}):
            caller.msg("A curse chokes off your words - you cannot cast spells right now.")
            return

        if "Frightened" in (caller.db.conditions or {}):
            caller.msg("You're too frightened to focus enough to cast anything!")
            return

        if caller.db.resting:
            caller.msg("You're resting. Type 'stand' first if you want to cast anything.")
            return

        if self.rules.is_in_combat(caller):
            if not self.rules.is_turn(caller):
                caller.msg("You can only cast a spell on your turn.")
                return
            if caller.db.combat_actionsleft is not None and caller.db.combat_actionsleft <= 0:
                caller.msg("You've already used your action this turn.")
                return

        if not self.lhs or len(self.lhs) < 3:
            caller.msg("Usage: cast <spell name> = <target>, <target2>, ...")
            if not caller.db.spells_known:
                caller.msg("You don't know any spells.")
                return
            caller.db.spells_known = sorted(caller.db.spells_known)
            spells_known_msg = "You know the following spells:|/" + "|/".join(
                caller.db.spells_known
            )
            caller.msg(spells_known_msg)
            return

        spellname = self.lhs.lower()
        spell_to_cast = []

        if not self.rhs:
            spell_targets = []
        elif self.rhs.lower() in ["me", "self", "myself"]:
            spell_targets = [caller]
        else:
            spell_targets = self.rhslist

        # Prefer an exact match first, to avoid ambiguity between spells
        # whose names are substrings of one another.
        if spellname in caller.db.spells_known:
            spell_to_cast = [spellname]
        else:
            for spell in caller.db.spells_known:
                if spellname in spell.lower():
                    spell_to_cast.append(spell)

        if not spell_to_cast:
            caller.msg("You don't know a spell of that name.")
            return
        if len(spell_to_cast) > 1:
            matched_spells = ", ".join(spell_to_cast)
            caller.msg("Which spell do you mean: %s?" % matched_spells)
            return

        spell_to_cast = spell_to_cast[0]

        if spell_to_cast not in SPELLS:
            caller.msg("ERROR: Spell %s is undefined" % spell_to_cast)
            return

        spelldata = dict(SPELLS[spell_to_cast])  # copy to avoid mutating the shared dict
        spelldata.setdefault("combat_spell", True)
        spelldata.setdefault("noncombat_spell", True)
        spelldata.setdefault("max_targets", 1)

        kwargs = {}
        spelldata_opts = [
            "spellfunc",
            "target",
            "cost",
            "combat_spell",
            "noncombat_spell",
            "max_targets",
            "classes",
            "desc",
            "level_required",
        ]
        for key in spelldata:
            if key not in spelldata_opts:
                kwargs[key] = spelldata[key]

        if spelldata["cost"] > caller.db.mp:
            caller.msg("You don't have enough MP to cast '%s'." % spell_to_cast)
            return

        if spelldata["combat_spell"] is False and self.rules.is_in_combat(caller):
            caller.msg("You can't use the spell '%s' in combat." % spell_to_cast)
            return

        if spelldata["noncombat_spell"] is False and not self.rules.is_in_combat(caller):
            caller.msg("You can't use the spell '%s' outside of combat." % spell_to_cast)
            return

        if len(spell_targets) > 0 and spelldata["target"] == "none":
            caller.msg("The spell '%s' isn't cast on a target." % spell_to_cast)
            return

        target_candidates = []
        if spelldata["target"] in ["any", "other"]:
            target_candidates = caller.location.contents + caller.contents
        if spelldata["target"] == "anyobj":
            prefilter = caller.location.contents + caller.contents
            target_candidates = [t for t in prefilter if not t.attributes.has("max_hp")]
        if spelldata["target"] in ["anychar", "otherchar"]:
            prefilter = caller.location.contents
            target_candidates = [t for t in prefilter if t.attributes.has("max_hp")]
        # "deadchar" (Blessing of Asclepius) has no room to search - a
        # dead ally is in the Underworld, nowhere near the caster. Use
        # global_search below instead of a candidate list.

        # No explicit target given for an offensive spell - rather than
        # always demanding a name, default sensibly: for a single-target
        # spell, auto-target the lone enemy if there's exactly one (same
        # unambiguous-only rule as 'attack'/'powerattack'); for an
        # AoE-capable spell, just fill up to its max_targets cap the
        # same way '= enemies' already does, since "hit as many as I'm
        # allowed" isn't ambiguous the way "hit one specific person" is.
        if spelldata["target"] == "otherchar" and len(spell_targets) == 0:
            possible_enemies = [
                t for t in target_candidates if not self.rules.is_ally(caller, t)
            ]

            if spelldata["max_targets"] == 1:
                if len(possible_enemies) == 1:
                    spell_targets = [possible_enemies[0].key]
                elif len(possible_enemies) == 0:
                    caller.msg("There's nobody here to target.")
                    return
                else:
                    caller.msg(
                        "Cast '%s' on whom? More than one possible target - "
                        "specify a name." % spell_to_cast
                    )
                    return
            else:
                if not possible_enemies:
                    caller.msg("There's nobody here to target.")
                    return
                spell_targets = [t.key for t in possible_enemies[: spelldata["max_targets"]]]

        # "anychar" excluded here alongside "self"/"none": it's meant
        # to default to the caster themselves when no target is given
        # (see the 'spell_targets = [caller]' fallback below) - cure
        # wounds, sanctuary, testudo, and every other self-or-ally
        # support spell/skill uses this target type specifically so
        # 'cast cure wounds' with no argument heals the caster. This
        # check used to run BEFORE that fallback ever got a chance to
        # apply, so it unconditionally rejected every no-target
        # "anychar" cast with "requires a target" - the fallback
        # existed in code but could never actually be reached.
        if spelldata["target"] not in ["self", "none", "anychar"] and len(spell_targets) == 0:
            caller.msg("The spell '%s' requires a target." % spell_to_cast)
            return

        if len(spell_targets) > spelldata["max_targets"]:
            targplural = "target" if spelldata["max_targets"] == 1 else "targets"
            caller.msg(
                "The spell '%s' can only be cast on %i %s."
                % (spell_to_cast, spelldata["max_targets"], targplural)
            )
            return

        # "party" shortcut: `cast <spell> = party` targets your whole
        # roster at once, skipping name-by-name searching entirely.
        # "enemies" is the mirror image - every hostile-capable target
        # in the room (i.e. everyone with HP except your own party),
        # up to the spell's max_targets cap.
        if (
            len(spell_targets) == 1
            and spell_targets[0].strip().lower() in ["party", "allies", "ally"]
            and spelldata["target"] in ["anychar", "otherchar"]
        ):
            from world.party import get_party_members

            matched_targets = get_party_members(caller)
        elif (
            len(spell_targets) == 1
            and spell_targets[0].strip().lower() in ["enemies", "enemy", "all"]
            and spelldata["target"] in ["anychar", "otherchar"]
        ):
            matched_targets = [
                t for t in target_candidates if not self.rules.is_ally(caller, t)
            ][: spelldata["max_targets"]]
            if not matched_targets:
                caller.msg("There's nobody here to target.")
                return
        elif spelldata["target"] == "keyword":
            # Not a character/object search at all - the raw typed text
            # (e.g. "atrium") is passed straight through as-is. Used by
            # Gate, where the argument is a destination name from a
            # fixed whitelist, not something to search the room for.
            matched_targets = spell_targets
        else:
            matched_targets = []
            for target in spell_targets:
                if spelldata["target"] == "deadchar":
                    match = caller.search(target, global_search=True)
                    if match and not match.db.is_dead:
                        caller.msg("%s is not dead." % match.key)
                        match = None
                else:
                    # Plain caller.search() alone isn't reliable here:
                    # rpsystem's sdesc-aware search override means a
                    # non-Builder caller can fail to find another real
                    # Character by their exact name (only NPCs, which
                    # lack an sdesc handler, are unaffected) - the same
                    # root cause find_combat_target already exists to
                    # fix for attack/fight/powerattack. 'cast heal =
                    # <ally name>' needs the identical fallback, or a
                    # support caster can't reliably target a party
                    # member they haven't formally met/recog'd.
                    match = find_combat_target(caller, target, candidates=target_candidates)
                matched_targets.append(match)
        spell_targets = matched_targets

        if len(spell_targets) == 0 and spelldata["target"] in ["self", "anychar"]:
            spell_targets = [caller]

        if spelldata["target"] in ["other", "otherchar"] and caller in spell_targets:
            caller.msg("You can't cast '%s' on yourself." % spell_to_cast)
            return

        if None in spell_targets:
            return

        if len(spell_targets) != len(set(spell_targets)):
            caller.msg("You can't specify the same target more than once!")
            return

        try:
            spelldata["spellfunc"](
                caller, spell_to_cast, spell_targets, spelldata["cost"], **kwargs
            )
            self.rules.award_cast_xp(caller, spelldata["cost"])
        except Exception:
            log_trace("Error in callback for spell: %s." % spell_to_cast)


class CmdUseSkill(MuxCommand):
    """
    Use a trained combat skill.

    Usage:
      skill <skill name> = <target>, <target2>, ...
      skill <skill name> = party
      skill <skill name> = allies
      skill <skill name> = enemies

    The SP-costing equivalent of 'cast' for non-caster classes. Same
    partial-name matching as 'cast' - you don't need to type the full
    skill name if what you've typed is unambiguous among what you
    know. Same turn/action rules as casting a spell: only on your own
    turn, once per turn, while in combat.

    "party" and "allies" are the same thing, either word works - both
    target your whole party roster at once for skills that can affect
    more than one person.
    """

    key = "skill"
    help_category = "combat"
    rules = COMBAT_RULES

    def func(self):
        user = self.caller

        if user.db.is_dead:
            user.msg("The dead have no use for combat skills.")
            return

        if "Silenced" in (user.db.conditions or {}):
            user.msg("A curse chokes off your focus - you cannot use skills right now.")
            return

        if "Frightened" in (user.db.conditions or {}):
            user.msg("You're too frightened to use any of your training right now!")
            return

        if user.db.resting:
            user.msg("You're resting. Type 'stand' first if you want to use a skill.")
            return

        if self.rules.is_in_combat(user):
            if not self.rules.is_turn(user):
                user.msg("You can only use a skill on your turn.")
                return
            if user.db.combat_actionsleft is not None and user.db.combat_actionsleft <= 0:
                user.msg("You've already used your action this turn.")
                return

        if not self.lhs or len(self.lhs) < 3:
            user.msg("Usage: skill <skill name> = <target>, <target2>, ...")
            if not user.db.skills_known:
                user.msg("You don't know any skills.")
                return
            user.db.skills_known = sorted(user.db.skills_known)
            user.msg("You know the following skills:|/" + "|/".join(user.db.skills_known))
            return

        skillname = self.lhs.lower()
        skill_to_use = []

        if not self.rhs:
            skill_targets = []
        elif self.rhs.lower() in ["me", "self", "myself"]:
            skill_targets = [user]
        else:
            skill_targets = self.rhslist

        if skillname in user.db.skills_known:
            skill_to_use = [skillname]
        else:
            for skill in user.db.skills_known:
                if skillname in skill.lower():
                    skill_to_use.append(skill)

        if not skill_to_use:
            user.msg("You don't know a skill of that name.")
            return
        if len(skill_to_use) > 1:
            user.msg("Which skill do you mean: %s?" % ", ".join(skill_to_use))
            return

        skill_to_use = skill_to_use[0]

        if skill_to_use not in SKILLS:
            user.msg("ERROR: Skill %s is undefined" % skill_to_use)
            return

        skilldata = dict(SKILLS[skill_to_use])
        skilldata.setdefault("combat_spell", True)
        skilldata.setdefault("noncombat_spell", True)
        skilldata.setdefault("max_targets", 1)

        kwargs = {}
        skilldata_opts = [
            "skillfunc",
            "target",
            "cost",
            "combat_spell",
            "noncombat_spell",
            "max_targets",
            "classes",
            "desc",
            "level_required",
        ]
        for key in skilldata:
            if key not in skilldata_opts:
                kwargs[key] = skilldata[key]

        if skilldata["cost"] > user.db.sp:
            user.msg("You don't have enough SP to use '%s'." % skill_to_use)
            return

        if skilldata["combat_spell"] is False and self.rules.is_in_combat(user):
            user.msg("You can't use the skill '%s' in combat." % skill_to_use)
            return

        if skilldata["noncombat_spell"] is False and not self.rules.is_in_combat(user):
            user.msg("You can't use the skill '%s' outside of combat." % skill_to_use)
            return

        if len(skill_targets) > 0 and skilldata["target"] == "none":
            user.msg("The skill '%s' isn't used on a target." % skill_to_use)
            return

        target_candidates = []
        if skilldata["target"] in ["anychar", "otherchar"]:
            target_candidates = [t for t in user.location.contents if t.attributes.has("max_hp")]

        # No explicit target given for an offensive skill - same
        # sensible default as CmdCast: auto-target the lone enemy for
        # a single-target skill (only if unambiguous), or fill up to
        # max_targets the same way '= enemies' already does for an
        # AoE-capable one.
        if skilldata["target"] == "otherchar" and len(skill_targets) == 0:
            possible_enemies = [
                t for t in target_candidates if not self.rules.is_ally(user, t)
            ]

            if skilldata["max_targets"] == 1:
                if len(possible_enemies) == 1:
                    skill_targets = [possible_enemies[0].key]
                elif len(possible_enemies) == 0:
                    user.msg("There's nobody here to target.")
                    return
                else:
                    user.msg(
                        "Use '%s' on whom? More than one possible target - "
                        "specify a name." % skill_to_use
                    )
                    return
            else:
                if not possible_enemies:
                    user.msg("There's nobody here to target.")
                    return
                skill_targets = [t.key for t in possible_enemies[: skilldata["max_targets"]]]

        # See the identical fix/comment in CmdCast above - "anychar"
        # must default to the user themselves when no target is given.
        if skilldata["target"] not in ["self", "none", "anychar"] and len(skill_targets) == 0:
            user.msg("The skill '%s' requires a target." % skill_to_use)
            return

        if len(skill_targets) > skilldata["max_targets"]:
            targplural = "target" if skilldata["max_targets"] == 1 else "targets"
            user.msg(
                "The skill '%s' can only be used on %i %s."
                % (skill_to_use, skilldata["max_targets"], targplural)
            )
            return

        if (
            len(skill_targets) == 1
            and skill_targets[0].strip().lower() in ["party", "allies", "ally"]
            and skilldata["target"] in ["anychar", "otherchar"]
        ):
            from world.party import get_party_members

            matched_targets = get_party_members(user)
        elif (
            len(skill_targets) == 1
            and skill_targets[0].strip().lower() in ["enemies", "enemy", "all"]
            and skilldata["target"] in ["anychar", "otherchar"]
        ):
            matched_targets = [
                t for t in target_candidates if not self.rules.is_ally(user, t)
            ][: skilldata["max_targets"]]
            if not matched_targets:
                user.msg("There's nobody here to target.")
                return
        else:
            matched_targets = []
            for target in skill_targets:
                # See the identical fix/comment in CmdCast above - same
                # rpsystem sdesc-search issue, same fallback.
                match = find_combat_target(user, target, candidates=target_candidates)
                matched_targets.append(match)
        skill_targets = matched_targets

        if len(skill_targets) == 0 and skilldata["target"] in ["self", "anychar"]:
            skill_targets = [user]

        if skilldata["target"] in ["other", "otherchar"] and user in skill_targets:
            user.msg("You can't use '%s' on yourself." % skill_to_use)
            return

        if None in skill_targets:
            return

        if len(skill_targets) != len(set(skill_targets)):
            user.msg("You can't specify the same target more than once!")
            return

        try:
            skilldata["skillfunc"](
                user, skill_to_use, skill_targets, skilldata["cost"], **kwargs
            )
            self.rules.award_cast_xp(user, skilldata["cost"])
        except Exception:
            log_trace("Error in callback for skill: %s." % skill_to_use)


class CmdLearnSkill(Command):
    """
    Learn a combat skill.

    Usage:
        learnskill <skill name>
    """

    key = "learnskill"
    help_category = "combat"

    def func(self):
        skill_list = sorted(SKILLS.keys())
        args = self.args.lower().strip(" ")
        caller = self.caller
        skill_to_learn = []

        if not args or len(args) < 3:
            caller.msg(
                "Usage: learnskill <skill name>\n"
                "Not sure what's available? Try 'skillinfo' to see your full skill list."
            )
            return

        if args in skill_list:
            skill_to_learn = [args]
        else:
            for skill in skill_list:
                if args in skill.lower():
                    skill_to_learn.append(skill)

        if not skill_to_learn:
            caller.msg("There is no skill with that name.")
            return
        if len(skill_to_learn) > 1:
            caller.msg("Which skill do you mean: %s?" % ", ".join(skill_to_learn))
            return

        skill_to_learn = skill_to_learn[0]

        allowed_classes = SKILLS[skill_to_learn].get("classes")
        if allowed_classes and caller.db.player_class not in allowed_classes:
            caller.msg(
                "Your training doesn't include the skill '%s'. That knowledge "
                "belongs to another path." % skill_to_learn
            )
            return

        level_required = SKILLS[skill_to_learn].get("level_required", 1)
        caller_level = caller.db.level or 1
        if caller_level < level_required:
            caller.msg(
                "You aren't experienced enough for '%s' yet - it requires level %d "
                "(you are level %d)." % (skill_to_learn, level_required, caller_level)
            )
            return

        if skill_to_learn not in caller.db.skills_known:
            caller.db.skills_known.append(skill_to_learn)
            caller.msg("You learn the skill '%s'!" % skill_to_learn)
        else:
            caller.msg("You already know the skill '%s'!" % skill_to_learn)


class CmdSkillInfo(Command):
    """
    Show detailed information about a skill, or your full skill list.

    Usage:
      skillinfo
      skillinfo <skill name>

    With no argument, shows every skill your class can ever learn -
    both what you already know and what's still ahead of you, with
    the level each one requires. With a skill name, shows its SP
    cost, which classes can learn it, its level requirement, and what
    it actually does.
    """

    key = "skillinfo"
    aliases = ["skilldesc", "skillbook"]
    help_category = "combat"

    def func(self):
        caller = self.caller

        if not self.args:
            player_class = caller.db.player_class
            known = set(caller.db.skills_known or [])

            available_by_class = {
                name
                for name, data in SKILLS.items()
                if not data.get("classes") or player_class in data.get("classes", [])
            }
            available = sorted(
                known | available_by_class, key=lambda n: SKILLS[n].get("level_required", 1)
            )

            if not available:
                caller.msg("Your class has no skills associated with it.")
                return

            caller_level = caller.db.level or 1
            known_lines = []
            locked_lines = []
            unlearned_lines = []

            for name in available:
                level_req = SKILLS[name].get("level_required", 1)
                if name in known:
                    known_lines.append("  %s (Lv %d)" % (name.title(), level_req))
                elif caller_level < level_req:
                    locked_lines.append(
                        "  %s (Lv %d - you are Lv %d)" % (name.title(), level_req, caller_level)
                    )
                else:
                    unlearned_lines.append(
                        "  %s (Lv %d - ready to learn now!)" % (name.title(), level_req)
                    )

            msg = "|wYour skill list:|n\n"
            msg += "\n|gKnown:|n\n" + ("\n".join(known_lines) if known_lines else "  (none yet)")
            if unlearned_lines:
                msg += "\n\n|yReady to learn (use 'learnskill'):|n\n" + "\n".join(unlearned_lines)
            if locked_lines:
                msg += "\n\n|xNot yet available:|n\n" + "\n".join(locked_lines)

            caller.msg(msg)
            return

        skillname = self.args.strip().lower()

        if skillname in SKILLS:
            matches = [skillname]
        else:
            matches = [s for s in SKILLS if skillname in s.lower()]

        if not matches:
            caller.msg("No skill found matching '%s'." % skillname)
            return
        if len(matches) > 1:
            caller.msg("Which skill do you mean: %s?" % ", ".join(sorted(matches)))
            return

        skill = matches[0]
        data = SKILLS[skill]
        classes = data.get("classes")
        class_str = ", ".join(c.capitalize() for c in classes) if classes else "Any class"
        desc = data.get("desc", "No description available.")
        level_required = data.get("level_required", 1)
        usage = _usage_line("skill", skill, data["target"])

        caller.msg(
            "|w%s|n\n"
            "  Cost: %s SP\n"
            "  Classes: %s\n"
            "  Requires level: %d\n"
            "  Usage: %s\n"
            "  %s" % (skill.title(), data["cost"], class_str, level_required, usage, desc)
        )


class CmdSpellInfo(Command):
    """
    Show detailed information about a spell, or your full spellbook.

    Usage:
      spellinfo
      spellinfo <spell name>

    With no argument, shows every spell your class can ever learn -
    both what you already know and what's still ahead of you, with
    the level each one requires - not just the spells you've already
    picked up. With a spell name (or a unique partial match, same as
    'cast'), shows its MP cost, which classes can learn it, its level
    requirement, and what it actually does.
    """

    key = "spellinfo"
    aliases = ["spelldesc", "spellbook"]
    help_category = "magic"

    def func(self):
        caller = self.caller

        if not self.args:
            player_class = caller.db.player_class
            known = set(caller.db.spells_known or [])

            # Every spell open to this character's class, or universal
            # (no "classes" key at all, like Conjure Torch) - PLUS
            # anything already known, regardless of class match. That
            # last part matters for edge cases like classless
            # characters (gods, admin test characters) who learned a
            # spell before class-gating existed, or outside the normal
            # rules entirely - a known spell should never just vanish
            # from view because it no longer matches their class.
            available_by_class = {
                name
                for name, data in SPELLS.items()
                if not data.get("classes") or player_class in data.get("classes", [])
            }
            available = sorted(
                known | available_by_class, key=lambda n: SPELLS[n].get("level_required", 1)
            )

            if not available:
                caller.msg("Your class has no spells associated with it.")
                return

            caller_level = caller.db.level or 1
            known_lines = []
            locked_lines = []
            unlearned_lines = []

            for name in available:
                level_req = SPELLS[name].get("level_required", 1)
                if name in known:
                    known_lines.append("  %s (Lv %d)" % (name.title(), level_req))
                elif caller_level < level_req:
                    locked_lines.append(
                        "  %s (Lv %d - you are Lv %d)" % (name.title(), level_req, caller_level)
                    )
                else:
                    unlearned_lines.append(
                        "  %s (Lv %d - ready to learn now!)" % (name.title(), level_req)
                    )

            msg = "|wYour spellbook:|n\n"
            msg += "\n|gKnown:|n\n" + ("\n".join(known_lines) if known_lines else "  (none yet)")
            if unlearned_lines:
                msg += "\n\n|yReady to learn (use 'learnspell'):|n\n" + "\n".join(unlearned_lines)
            if locked_lines:
                msg += "\n\n|xNot yet available:|n\n" + "\n".join(locked_lines)

            caller.msg(msg)
            return

        spellname = self.args.strip().lower()

        if spellname in SPELLS:
            matches = [spellname]
        else:
            matches = [s for s in SPELLS if spellname in s.lower()]

        if not matches:
            caller.msg("No spell found matching '%s'." % spellname)
            return
        if len(matches) > 1:
            caller.msg("Which spell do you mean: %s?" % ", ".join(sorted(matches)))
            return

        spell = matches[0]
        data = SPELLS[spell]
        classes = data.get("classes")
        class_str = ", ".join(c.capitalize() for c in classes) if classes else "Any class"
        desc = data.get("desc", "No description available.")
        level_required = data.get("level_required", 1)
        usage = _usage_line("cast", spell, data["target"])

        caller.msg(
            "|w%s|n\n"
            "  Cost: %s MP\n"
            "  Classes: %s\n"
            "  Requires level: %d\n"
            "  Usage: %s\n"
            "  %s" % (spell.title(), data["cost"], class_str, level_required, usage, desc)
        )


class CmdCombatHelp(CmdHelp):
    """
    View help or a list of topics.

    Usage:
      help <topic or command>
      help list
      help all
    """

    rules = COMBAT_RULES
    combat_help_text = (
        "Available combat commands:|/"
        "|wAttack:|n Attack a target, attempting to deal damage.|/"
        "|wPower Attack:|n A harder-hitting attack that costs SP.|/"
        "|wUse:|n Use an item you're carrying.|/"
        "|wCast:|n Cast a spell you know.|/"
        "|wWield/Unwield:|n Equip or unequip a weapon.|/"
        "|wDon/Doff:|n Equip or unequip armor (out of combat only).|/"
        "|wPass:|n Pass your turn without further action.|/"
        "|wDisengage:|n End your turn and attempt to end combat.|/"
        "|wStatus:|n Check your HP/MP/SP.|/"
    )

    def func(self):
        if self.rules.is_in_combat(self.caller) and not self.args:
            self.caller.msg(self.combat_help_text)
        else:
            super().func()


class BattleCmdSet(CharacterCmdSet):
    """
    The single, unified combat command set - replaces the separate
    cmdsets from tb_basic, tb_equip, tb_items, and tb_magic.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdFight())
        self.add(CmdAttack())
        self.add(CmdPowerAttack())
        self.add(CmdRest())
        self.add(CmdStand())
        self.add(CmdPass())
        self.add(CmdDisengage())
        self.add(CmdCombatHelp())
        self.add(CmdWield())
        self.add(CmdUnwield())
        self.add(CmdDon())
        self.add(CmdDoff())
        self.add(CmdUse())
        self.add(CmdLearnSpell())
        self.add(CmdCast())
        self.add(CmdStatus())
        self.add(CmdCoreStats())
        self.add(CmdConsider())
        self.add(CmdChallenge())
        self.add(CmdSpellInfo())
        self.add(CmdUseSkill())
        self.add(CmdLearnSkill())
        self.add(CmdSkillInfo())
