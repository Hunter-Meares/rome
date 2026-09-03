"""
Religion & piety for mortal characters - a mortal's personal standing
with a real, worshippable pantheon god, explicitly distinct from two
other systems already in this game that could easily be confused with
it:
  - The Cursus Divinorum (world/combat.py's GOD_TIERS) is about a
    player literally BECOMING a god via level. This is about an
    ordinary mortal's relationship with the gods that already exist -
    a level-106 god has moved past this mechanic entirely, not maxed
    it out.
  - Faction membership (world/factions.py) is a genuinely different,
    ORTHOGONAL kind of commitment - political/social affiliation, not
    personal devotion. A player can hold both at once (a Legionary
    devoted to Mars is the single most natural combination in this
    entire setting) - this module deliberately does NOT merge with or
    reuse FACTIONS, despite the two systems sharing an almost
    identical shape (permanent membership, a leader who can induct/
    expel, no self-leave). Real, brutal feedback surfaced that overlap
    directly before this was built; the decision was to mirror the
    proven SHAPE, not the same mechanism, specifically so the two stay
    independent.

Design, per direct discussion before any of this was built:
  - One religion at a time. Joined via `pray <god>` (warns it's
    permanent) -> `pray <god> confirm` (joins for real) - the exact
    two-step pattern world/factions.py already proved out for "this
    is a real, weighty choice." An ordinary member can never leave on
    their own - only that religion's Pontifex or a god can `expel`
    them.
  - `pontifex <god> = <player>` (god-only) appoints a religion's
    Pontifex, mirroring world/factions.py's `factionleader` command
    exactly - not "invest," which already means something else in
    this game (a faction leader promoting one of their own members -
    a real naming collision caught before this shipped). No religion
    is blocked from functioning just because it has no Pontifex yet -
    a god can always act in a Pontifex's place.
  - `blemish <player> = <reason>` (Pontifex or god) reduces piety as
    an in-character consequence - requires a reason (logged), a fixed
    modest magnitude, and a cooldown per (discipliner, target) pair,
    specifically to survive the abuse risk raised directly during
    design: "it can't be based on something out of character, and it
    can't be abused." A logged reason and a hard cap don't prevent
    someone from acting in bad faith, but they make it visible and
    boring to try.
  - Piety is NOT gained by repeating `pray` - that was explicitly
    called out as too passive during design. All real progress comes
    from doing something in that god's actual domain, tracked as a
    counter toward a periodic tick rather than a per-action reward
    (see RELIGION_TRIGGERS below) - `pray` itself only ever joins.
  - Deliberately launched with only the gods that have a real,
    already-built activity to hook into (Mars/combat, Mercury/
    commerce, Apollo/healing, Pluto/surviving death) rather than
    forcing a weak or invented trigger onto every one of the 14 just
    to claim full coverage - Neptune, Minerva, Venus, Ceres, Vulcan,
    Juno, Diana, and Bacchus are still joinable (the framework applies
    uniformly), just honestly thin until either a real trigger is
    agreed for them or the content that would justify one gets built
    (crafting for Vulcan, sea content for Neptune, etc.).
  - Titles are deliberately NOT part of this - reopened during design
    and deferred again, same call already made for quest rewards:
    build the real shared earned-titles system once, have every
    system (quests, religion) hook into it, rather than a third ad hoc
    title mechanic bolted onto just this one.
"""

from evennia import Command
from evennia.utils import search
from evennia.utils.create import create_channel

from world.factions import GOD_LEVEL_THRESHOLD
from world.god_help import PANTHEON

# Real, already-built temple/altar rooms mapped to the one god each is
# dedicated to. Praying here needs no argument - the implicit local
# target convention already used by CmdChallenge/quest.
PRAYER_SITES = {
    "Main Cella - Jupiter": "jupiter",
    "Temple of Juno Moneta": "juno",
    "Cella of Ceres": "ceres",
    "Temple of Diana Aventina - Main Cella": "diana",
    "Temple of Vesta - the Sacred Fire": "vesta",
}

# The Pantheon's own altar - explicitly "dedicated to all of them at
# once" in its own room description (world/batch_pantheon_data.py) -
# covers every one of the 14, including the 9 with no dedicated
# temple of their own. Requires an explicit `pray <god>` here, unlike
# the single-god temples above, since there's no one sensible implicit
# target.
PANTHEON_ALTAR_ROOM = "The Altar of All Gods"

# Real, already-built activities that grant piety - a counter toward
# a periodic tick, not a per-action reward, so this can't be spammed
# for a fast climb. The other 10 gods in PANTHEON are still joinable;
# they just have no entry here yet (see module docstring).
RELIGION_TRIGGERS = {
    "mars": {"count_required": 7, "label": "combat kills"},
    "mercury": {"count_required": 7, "label": "trades"},
    "apollo": {"count_required": 7, "label": "heals cast"},
}
PIETY_PER_TICK = 10

# Pluto is rare enough (surviving death and actually returning) that
# it grants piety immediately, no counter needed.
PLUTO_PIETY_PER_RESURRECTION = 15

PIETY_TIERS = [
    (0, None),
    (25, "Favored"),
    (75, "Devoted"),
    (150, "Beloved"),
]

# Concrete, per-god passive bonuses at the top two tiers - "a small,
# real, thematically-tied passive bonus" was always part of the design,
# but launched with these exact numbers only once directly asked for a
# specific breakdown rather than left as a vague someday-detail.
# "Favored" (the entry tier) is deliberately bonus-free - a real,
# earned mid-tier goal, not a reward for the very first tick.
RELIGION_BONUSES = {
    "mars": {
        "Devoted": {"melee_damage_bonus": 2},
        "Beloved": {"melee_damage_bonus": 4},
    },
    "mercury": {
        "Devoted": {"shop_discount": 0.10},
        "Beloved": {"shop_discount": 0.20},
    },
    "apollo": {
        "Devoted": {"heal_bonus": 0.15},
        "Beloved": {"heal_bonus": 0.30},
    },
    "pluto": {
        "Devoted": {"death_xp_penalty_reduction": 0.5},
        "Beloved": {"death_xp_penalty_reduction": 1.0},
    },
}


def religion_bonus(character, god_key, bonus_key):
    """
    The character's current bonus value for bonus_key under god_key,
    or 0/None-equivalent if not devoted to that god, not at a tier
    that grants it, or that god has no such bonus defined. Centralizes
    the "are they actually eligible for this" check so every call site
    (combat.py, economy.py) stays a one-line lookup rather than
    re-deriving tier logic in three different places.
    """
    if character.db.religion != god_key:
        return 0
    tier = piety_tier((character.db.piety or {}).get(god_key, 0))
    if not tier:
        return 0
    return RELIGION_BONUSES.get(god_key, {}).get(tier, {}).get(bonus_key, 0)

BLEMISH_AMOUNT = 15
BLEMISH_COOLDOWN_SECONDS = 3600


def god_display_name(god_key):
    return PANTHEON.get(god_key, (god_key.title(),))[0]


def _religion_channel_name(god_key):
    return "%s-religion" % god_key


def get_religion_channel(god_key):
    """Finds the live Channel object for a god's religion, or None if it
    hasn't been created yet (see ensure_religion_channels_exist)."""
    found = search.search_channel(_religion_channel_name(god_key))
    return found[0] if found else None


def _connect_all_gods_to(channel):
    """
    Every character at a god level (over 100) auto-joins a channel the
    moment it exists - same helper world/factions.py already proved
    out for its own channels, duplicated here in full rather than
    imported (it's a 3-line, fully generic function; not worth a
    cross-module import of another module's underscore-prefixed name
    for something this small).
    """
    for obj in search.search_object_attribute(key="level"):
        if not obj.is_typeclass("evennia.objects.objects.DefaultCharacter", exact=False):
            continue
        if (obj.db.level or 0) > GOD_LEVEL_THRESHOLD:
            channel.connect(obj)


def ensure_religion_channels_exist():
    """
    Creates one private channel per god in PANTHEON (all 14, not just
    the 4 with a real trigger today - every god is joinable) if it
    doesn't already exist. Safe to call repeatedly - idempotent, skips
    any channel that's already there. Same lock shape as faction
    channels: visible to everyone, but only a member of that specific
    religion (or a god) can actually listen/send.
    """
    created = []
    god_clause = "attr(level, 100, compare=gt)"
    for god_key, data in PANTHEON.items():
        if get_religion_channel(god_key):
            continue
        channel = create_channel(
            key=_religion_channel_name(god_key),
            desc="%s - private religion channel" % data[0],
            locks=(
                "control:%s;"
                "listen:attr(religion, %s) or %s;"
                "send:attr(religion, %s) or %s"
            )
            % (god_clause, god_key, god_clause, god_key, god_clause),
        )
        _connect_all_gods_to(channel)
        created.append(channel)
    return created


def connect_god_to_all_religion_channels(character):
    """Called from CmdGodLevel whenever someone is promoted above level
    100 - joins every religion channel immediately, mirroring
    connect_god_to_all_faction_channels exactly."""
    for god_key in PANTHEON:
        channel = get_religion_channel(god_key)
        if channel:
            channel.connect(character)


def piety_tier(value):
    tier = None
    for threshold, name in PIETY_TIERS:
        if value >= threshold:
            tier = name
    return tier


def can_manage_religion(caller, god_key):
    """
    True if caller can pontifex/blemish/expel for this god's religion -
    any god (level over 100, or true superuser), or that specific
    religion's own Pontifex. Mirrors world/factions.py's
    can_manage_faction exactly.
    """
    is_superuser = bool(caller.account and caller.account.is_superuser)
    if is_superuser or (caller.db.level or 0) > GOD_LEVEL_THRESHOLD:
        return True
    return caller.db.religion == god_key and caller.db.religion_rank == "pontifex"


def join_religion(character, god_key):
    old_key = character.db.religion
    if old_key and old_key != god_key:
        leave_religion(character)

    character.db.religion = god_key
    character.db.religion_rank = "member"

    channel = get_religion_channel(god_key)
    if channel:
        channel.connect(character)


def leave_religion(character):
    old_key = character.db.religion
    if old_key:
        channel = get_religion_channel(old_key)
        if channel:
            channel.disconnect(character)

    character.db.religion = None
    character.db.religion_rank = None


def add_piety(character, god_key, amount):
    piety = character.db.piety or {}
    old_value = piety.get(god_key, 0)
    new_value = max(0, old_value + amount)
    piety[god_key] = new_value
    character.db.piety = piety

    old_tier = piety_tier(old_value)
    new_tier = piety_tier(new_value)
    if new_tier and new_tier != old_tier:
        character.msg(
            "|Y%s now regards you as %s.|n" % (god_display_name(god_key), new_tier)
        )
        if new_tier == "Beloved":
            from world.titles import RELIGION_BELOVED_TITLES, grant_earned_title
            title = RELIGION_BELOVED_TITLES.get(god_key)
            if title:
                grant_earned_title(character, title)


def _credit_trigger(character, god_key):
    """
    Shared by the three counter-based triggers (Mars/Mercury/Apollo) -
    only fires for a character currently devoted to this exact god,
    increments the raw activity counter, and ticks piety once the
    counter reaches the trigger's own count_required, resetting it.
    """
    if character.db.religion != god_key:
        return
    trigger = RELIGION_TRIGGERS.get(god_key)
    if not trigger:
        return

    progress = character.db.piety_progress or {}
    count = progress.get(god_key, 0) + 1
    if count >= trigger["count_required"]:
        add_piety(character, god_key, PIETY_PER_TICK)
        count = 0
    progress[god_key] = count
    character.db.piety_progress = progress


def credit_mars_kill(defeated):
    """
    Called from CombatRules.at_defeat, same damage_log population as
    the XP/gold split and world/bounties.py's credit_bounty_progress -
    every real contributor currently devoted to Mars gets credit
    toward their next piety tick.
    """
    from world.combat import iter_damage_contributors

    damage_log = defeated.db.damage_log or {}
    for contributor in iter_damage_contributors(damage_log):
        _credit_trigger(contributor, "mars")


def credit_mercury_trade(character):
    """Called from world/economy.py's _buy and _sell - either direction of commerce counts."""
    _credit_trigger(character, "mercury")


def credit_apollo_heal(caster):
    """Called from CombatRules.spell_healing - the healer's own devotion, not the target's."""
    _credit_trigger(caster, "apollo")


def credit_pluto_resurrection(character):
    """
    Called from CombatRules.resurrect() - rare and significant enough
    to grant piety immediately rather than needing a counter.
    """
    if character.db.religion != "pluto":
        return
    add_piety(character, "pluto", PLUTO_PIETY_PER_RESURRECTION)


class CmdPray(Command):
    """
    Pray at a real shrine - the way to join a god's religion.

    Usage:
      pray <god>
      pray <god> confirm

    At one of the gods' own dedicated temples, 'pray' alone (no god
    needed) worships whichever god that temple belongs to. At the
    Pantheon's Altar of All Gods, you must name which of the 14 you
    mean.

    Joining is permanent - there is no walking away from it whenever
    you please, same as a faction. The only way out afterward is your
    religion's own Pontifex, or a god, using 'expel'. You'll be shown
    a warning first; only 'pray <god> confirm' actually joins.

    Piety itself isn't earned by praying repeatedly - it comes from
    actually doing something in your god's own domain. See 'help
    religion' for what that means for each god.
    """

    key = "pray"
    help_category = "general"

    def func(self):
        caller = self.caller
        arg = self.args.strip().lower()

        confirmed = False
        words = arg.split()
        if words and words[-1] == "confirm":
            confirmed = True
            arg = " ".join(words[:-1])

        here_name = caller.location.key if caller.location else None
        implicit_god = PRAYER_SITES.get(here_name)

        if arg:
            god_key = None
            if arg in PANTHEON:
                god_key = arg
            else:
                matches = [k for k in PANTHEON if arg in PANTHEON[k][0].lower()]
                if len(matches) == 1:
                    god_key = matches[0]
            if not god_key:
                caller.msg("No god matches '%s'." % arg)
                return
            if implicit_god and god_key != implicit_god:
                caller.msg(
                    "You can't properly worship %s here - this shrine belongs to "
                    "%s. Try the Pantheon's Altar of All Gods instead."
                    % (god_display_name(god_key), god_display_name(implicit_god))
                )
                return
            if not implicit_god and here_name != PANTHEON_ALTAR_ROOM:
                caller.msg("There's no shrine here to pray at.")
                return
        else:
            if not implicit_god:
                if here_name == PANTHEON_ALTAR_ROOM:
                    caller.msg("Pray to which god? Usage: pray <god>")
                else:
                    caller.msg("There's no shrine here to pray at.")
                return
            god_key = implicit_god

        current = caller.db.religion
        if current and current != god_key:
            if (caller.db.level or 0) <= GOD_LEVEL_THRESHOLD and not (
                caller.account and caller.account.is_superuser
            ):
                caller.msg(
                    "You are already devoted to %s for life - you can't simply "
                    "turn to %s. Petition your religion's Pontifex, or the gods "
                    "themselves, if you truly want out first."
                    % (god_display_name(current), god_display_name(god_key))
                )
                return

        if current == god_key:
            caller.msg("You are already devoted to %s." % god_display_name(god_key))
            return

        if not confirmed:
            caller.msg(
                "You feel the weight of the choice in front of you. Devote "
                "yourself to %s and you belong to that god for the rest of "
                "your life - there is no walking away from this whenever you "
                "please. The only way out, once you're in, is a petition to "
                "your religion's Pontifex, or to the gods themselves. If you "
                "are certain, say so plainly: |wpray %s confirm|n."
                % (god_display_name(god_key), god_key)
            )
            return

        join_religion(caller, god_key)
        caller.msg("|YYou devote yourself to %s.|n" % god_display_name(god_key))


class CmdPontifex(Command):
    """
    Designate a religion's Pontifex - god-only.

    Usage:
      pontifex <god> = <player>

    Promotes player to Pontifex of that god's religion, demoting
    whoever held it before (a religion only ever has one Pontifex at a
    time). Mirrors 'factionleader' exactly. Requires Auspex (level
    over 100) or true superuser.
    """

    key = "pontifex"
    help_category = "admin"

    def func(self):
        caller = self.caller
        is_superuser = bool(caller.account and caller.account.is_superuser)
        if (caller.db.level or 0) <= GOD_LEVEL_THRESHOLD and not is_superuser:
            caller.msg("You lack the standing to designate a Pontifex.")
            return

        if "=" not in self.args:
            caller.msg("Usage: pontifex <god> = <player>")
            return
        lhs, rhs = self.args.split("=", 1)
        god_arg = lhs.strip().lower()
        if god_arg not in PANTHEON:
            caller.msg("No god matches '%s'." % lhs.strip())
            return
        target = caller.search(rhs.strip(), global_search=True)
        if not target:
            return

        old_rank = target.db.religion_rank
        if target.db.religion != god_arg:
            join_religion(target, god_arg)
        target.db.religion_rank = "pontifex"
        caller.msg(
            "%s is now Pontifex of %s's religion." % (target.key, god_display_name(god_arg))
        )
        target.msg(
            "|YYou have been named Pontifex of %s's religion.|n" % god_display_name(god_arg)
        )


class CmdBlemish(Command):
    """
    Reduce a religion member's piety as an in-character consequence -
    Pontifex or god only.

    Usage:
      blemish <player> = <reason>

    Requires a reason - this is logged (see the god-only 'religion
    log <god>') specifically so it can never be a quiet, unaccountable
    action. A fixed, modest amount, and only usable against the same
    target once per hour by the same discipliner - not a tool for
    settling an out-of-character grudge quickly.
    """

    key = "blemish"
    help_category = "general"

    def func(self):
        import time

        caller = self.caller
        if "=" not in self.args:
            caller.msg("Usage: blemish <player> = <reason>")
            return
        lhs, rhs = self.args.split("=", 1)
        reason = rhs.strip()
        if not reason:
            caller.msg("A reason is required - blemishing someone needs a real, in-character cause.")
            return

        target = caller.search(lhs.strip(), global_search=True)
        if not target:
            return

        god_key = target.db.religion
        if not god_key:
            caller.msg("%s is not a member of any religion." % target.key)
            return
        if not can_manage_religion(caller, god_key):
            caller.msg("You don't have the standing to blemish members of that religion.")
            return

        cooldowns = caller.db.blemish_cooldowns or {}
        last = cooldowns.get(target.id, 0)
        if time.time() - last < BLEMISH_COOLDOWN_SECONDS:
            caller.msg("You've already blemished %s too recently - wait before doing so again." % target.key)
            return
        cooldowns[target.id] = time.time()
        caller.db.blemish_cooldowns = cooldowns

        add_piety(target, god_key, -BLEMISH_AMOUNT)

        log = target.db.religion_log or []
        log.append({
            "action": "blemish", "by": caller.key, "reason": reason, "time": time.time(),
        })
        target.db.religion_log = log

        target.msg("|rYou have been blemished in the eyes of %s: %s|n" % (god_display_name(god_key), reason))
        caller.msg("%s has been blemished. Reason logged: %s" % (target.key, reason))


class CmdExpel(Command):
    """
    Permanently remove someone from their religion - Pontifex or god
    only.

    Usage:
      expel <player> = <reason>

    The only way an ordinary member ever leaves a religion, mirroring
    world/factions.py's own 'faction expel'. Their piety total is kept
    (not erased), in case they're ever re-inducted later - only their
    current membership ends.
    """

    key = "expel"
    help_category = "general"

    def func(self):
        import time

        caller = self.caller
        if "=" not in self.args:
            caller.msg("Usage: expel <player> = <reason>")
            return
        lhs, rhs = self.args.split("=", 1)
        reason = rhs.strip()
        if not reason:
            caller.msg("A reason is required.")
            return

        target = caller.search(lhs.strip(), global_search=True)
        if not target:
            return

        god_key = target.db.religion
        if not god_key:
            caller.msg("%s is not a member of any religion." % target.key)
            return
        if not can_manage_religion(caller, god_key):
            caller.msg("You don't have the standing to expel members of that religion.")
            return

        leave_religion(target)

        log = target.db.religion_log or []
        log.append({
            "action": "expel", "by": caller.key, "reason": reason, "time": time.time(),
        })
        target.db.religion_log = log

        target.msg("|rYou have been expelled from %s's religion: %s|n" % (god_display_name(god_key), reason))
        caller.msg("%s has been expelled from %s's religion." % (target.key, god_display_name(god_key)))


class CmdReligion(Command):
    """
    Check your own standing with the gods, or (god-only) review a
    religion's recent activity.

    Usage:
      religion
      religion log <god>

    Bare 'religion' shows every god you have any piety with, your
    current tier, and (if you're a member) whether you're a Pontifex.

    'religion log <god>' (god-only) shows that religion's recent
    induct/blemish/expel activity, for real accountability over the
    Pontifex/blemish system.
    """

    key = "religion"
    help_category = "general"

    def func(self):
        caller = self.caller
        arg = self.args.strip()

        if arg.lower().startswith("log"):
            if (caller.db.level or 0) <= GOD_LEVEL_THRESHOLD and not (
                caller.account and caller.account.is_superuser
            ):
                caller.msg("Only gods can do that.")
                return
            god_arg = arg[3:].strip().lower()
            if god_arg not in PANTHEON:
                caller.msg("No god matches '%s'." % god_arg)
                return
            self._show_log(caller, god_arg)
            return

        self._show_own_standing(caller)

    def _show_own_standing(self, caller):
        piety = caller.db.piety or {}
        if not piety:
            caller.msg("You have no standing with any god yet. Find a shrine and 'pray'.")
            return
        lines = ["|wYour Standing with the Gods|n"]
        for god_key, value in piety.items():
            tier = piety_tier(value) or "Unknown"
            is_member = caller.db.religion == god_key
            rank = ""
            if is_member and caller.db.religion_rank == "pontifex":
                rank = " - Pontifex"
            elif is_member:
                rank = " - devoted"
            lines.append("  %-10s %3d (%s)%s" % (god_display_name(god_key), value, tier, rank))
        caller.msg("\n".join(lines))

    def _show_log(self, caller, god_key):
        from world.combat import all_player_characters

        entries = []
        for character in all_player_characters():
            if character.db.religion != god_key and not character.db.religion_log:
                continue
            for entry in character.db.religion_log or []:
                entries.append((character.key, entry))

        if not entries:
            caller.msg("No recent activity for %s's religion." % god_display_name(god_key))
            return

        entries.sort(key=lambda pair: pair[1]["time"], reverse=True)
        lines = ["|wRecent activity - %s's religion|n" % god_display_name(god_key)]
        for character_name, entry in entries[:20]:
            lines.append(
                "  %s: %s by %s - %s"
                % (character_name, entry["action"], entry["by"], entry["reason"])
            )
        caller.msg("\n".join(lines))
