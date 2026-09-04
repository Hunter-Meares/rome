"""
Tests for the NPC typeclasses (world/combat.py) - AutoStatNPC's stat
derivation, HostileNPC's action-gathering/turn AI, SummonedAlly's
targeting, and RespawningNPC/RespawnTimer/schedule_respawn - the
"RespawningNPC surviving a server reload mid-respawn-wait" item
CLAUDE.md flags as still unconfirmed.

A real server reload can't be simulated in a unit test, but the
mechanism that's SUPPOSED to guarantee survival can be verified
directly: RespawnTimer must actually be created with persistent=True
(this is what makes Evennia's Script save/reload it automatically,
not a bare delay() call - see the class's own docstring), and its
at_repeat logic must correctly bring the NPC back regardless of how
much real time passed while "waiting" (a reload doesn't reset a
persistent Script's timer, so no special reload-simulation is needed
to test the actual respawn logic itself).
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create

from world.combat import (
    COMBAT_RULES,
    derive_npc_stats,
    AutoStatNPC,
    HostileNPC,
    RespawnTimer,
    RespawningNPC,
    SummonedAlly,
    LEVEL_UP_HP_GAIN,
    LEVEL_UP_MP_GAIN,
    LEVEL_UP_SP_GAIN,
)


def _randint_side_effect(a, b):
    """
    A realistic stand-in for random.randint used across this file:
    behaves exactly like the real thing for a degenerate range (a==b,
    e.g. a fixed damage_range or the action-index roll when there's
    only one possible action), and otherwise forces the maximum -
    guaranteeing a hit on any accuracy roll. A single fixed
    return_value would instead clobber a degenerate range's only
    valid value (causing an IndexError picking an action) or a
    same-mocked damage roll turning a controlled test hit into an
    accidental kill (which triggers the real defeat/respawn flow and
    quietly resets hp back to full, masking what the test meant to
    check).
    """
    if a == b:
        return a
    return b


class TestDeriveNpcStats(EvenniaTest):
    def test_no_race_or_class_is_flat_baseline(self):
        stats = derive_npc_stats(None, None, level=1)
        self.assertEqual(stats["virtus"], 10)
        self.assertEqual(stats["agilitas"], 10)
        self.assertEqual(stats["ingenium"], 10)
        self.assertEqual(stats["vigor"], 10)
        self.assertEqual(stats["max_hp"], 100)

    def test_race_and_class_mods_stack_same_as_chargen(self):
        stats = derive_npc_stats("minotaur", "barbarian", level=1)
        # Minotaur +3 virtus, Barbarian +3 virtus -> ceiling of 16,
        # same invariant tests_chargen.py locks in for player chargen.
        self.assertEqual(stats["virtus"], 16)

    def test_level_scaling_matches_award_xp_growth_rates(self):
        level1 = derive_npc_stats(None, None, level=1)
        level5 = derive_npc_stats(None, None, level=5)
        self.assertEqual(level5["max_hp"] - level1["max_hp"], 4 * LEVEL_UP_HP_GAIN)
        self.assertEqual(level5["max_mp"] - level1["max_mp"], 4 * LEVEL_UP_MP_GAIN)
        self.assertEqual(level5["max_sp"] - level1["max_sp"], 4 * LEVEL_UP_SP_GAIN)

    def test_unknown_race_or_class_key_is_ignored_not_crashed(self):
        # Should not raise, and should behave like no race/class given.
        stats = derive_npc_stats("not_a_real_race", "not_a_real_class", level=1)
        self.assertEqual(stats["virtus"], 10)

    # --- Level-up stat points, added after a live question exposed a
    # real gap: HP/MP/SP scaled with level, but virtus/agilitas/
    # ingenium/vigor - the stats that actually drive damage/accuracy -
    # didn't, for every NPC in the game. Fixed by granting NPCs the
    # same stat points a player would have earned by that level (one
    # every 3 levels) and distributing them toward whatever the
    # NPC's own race/class already leans into, capped exactly like a
    # player's own lifetime caps.

    def test_no_stat_points_below_level_3(self):
        level1 = derive_npc_stats("minotaur", "barbarian", level=1)
        level2 = derive_npc_stats("minotaur", "barbarian", level=2)
        self.assertEqual(level1["virtus"], level2["virtus"])

    def test_exactly_one_point_granted_at_level_3(self):
        level2 = derive_npc_stats("minotaur", "barbarian", level=2)
        level3 = derive_npc_stats("minotaur", "barbarian", level=3)
        total2 = sum(level2[s] for s in ("virtus", "agilitas", "ingenium", "vigor"))
        total3 = sum(level3[s] for s in ("virtus", "agilitas", "ingenium", "vigor"))
        self.assertEqual(total3 - total2, 1)

    def test_points_granted_matches_the_real_level_up_cadence(self):
        # Level 9 = 3 grants (levels 3, 6, 9) - human/haruspex has
        # plenty of headroom below any cap at this level, so none of
        # the 3 points get wasted skipping an already-capped stat.
        level1 = derive_npc_stats("human", "haruspex", level=1)
        level9 = derive_npc_stats("human", "haruspex", level=9)
        total1 = sum(level1[s] for s in ("virtus", "agilitas", "ingenium", "vigor"))
        total9 = sum(level9[s] for s in ("virtus", "agilitas", "ingenium", "vigor"))
        self.assertEqual(total9 - total1, 3)

    def test_higher_level_means_more_total_stats_for_the_same_build(self):
        low = derive_npc_stats("minotaur", "barbarian", level=3)
        high = derive_npc_stats("minotaur", "barbarian", level=30)
        total_low = sum(low[s] for s in ("virtus", "agilitas", "ingenium", "vigor"))
        total_high = sum(high[s] for s in ("virtus", "agilitas", "ingenium", "vigor"))
        self.assertGreater(total_high, total_low)

    def test_agilitas_never_exceeds_its_own_tighter_cap(self):
        from world.leveling import AGILITAS_CAP

        stats = derive_npc_stats("centaur", "venator", level=100)
        self.assertLessEqual(stats["agilitas"], AGILITAS_CAP)

    def test_a_leaning_stat_caps_at_the_bonus_ceiling_not_beyond(self):
        from world.leveling import STAT_CAP_BONUS

        # Minotaur leans virtus at chargen - same bonus cap a player
        # of that race gets, not an unbounded climb with level.
        stats = derive_npc_stats("minotaur", "barbarian", level=100)
        self.assertLessEqual(stats["virtus"], STAT_CAP_BONUS)

    def test_no_race_or_class_gets_no_stat_points_even_at_high_level(self):
        # No class/race identity to spend points toward - stays flat
        # baseline regardless of level, exactly like level 1.
        stats = derive_npc_stats(None, None, level=100)
        self.assertEqual(stats["virtus"], 10)
        self.assertEqual(stats["agilitas"], 10)
        self.assertEqual(stats["ingenium"], 10)
        self.assertEqual(stats["vigor"], 10)


class TestAutoStatNPC(EvenniaTest):
    def test_stats_derived_from_prototype_race_and_class(self):
        npc = create.create_object(AutoStatNPC, key="test npc", location=self.room1)
        npc.db.race = "cyclops"
        npc.db.player_class = "legionary"
        npc.db.level = 1
        npc.at_object_post_creation()

        self.assertEqual(npc.db.vigor, 15)  # cyclops +2, legionary +3
        self.assertEqual(npc.db.max_hp, npc.db.hp)

    def test_no_race_or_class_leaves_stats_untouched(self):
        npc = create.create_object(AutoStatNPC, key="test npc 2", location=self.room1)
        npc.at_object_post_creation()
        # Plain DefaultCharacter has no db.virtus at all - just confirm
        # this doesn't crash and doesn't fabricate one.
        self.assertIsNone(npc.db.virtus)


class TestHostileNPCGatherActions(EvenniaTest):
    def test_always_includes_basic_attack(self):
        npc = create.create_object(HostileNPC, key="grunt", location=self.room1)
        npc.db.player_class = None
        actions = npc._gather_actions()
        self.assertIn(("attack", None, False), actions)

    def test_no_class_only_has_attack(self):
        npc = create.create_object(HostileNPC, key="grunt2", location=self.room1)
        npc.db.player_class = None
        actions = npc._gather_actions()
        self.assertEqual(actions, [("attack", None, False)])

    def test_class_adds_affordable_in_level_spells(self):
        npc = create.create_object(HostileNPC, key="haruspex npc", location=self.room1)
        npc.db.player_class = "haruspex"
        npc.db.level = 1
        npc.db.mp = 10
        npc.db.sp = 0

        actions = npc._gather_actions()

        # "mark of decay" is haruspex, level_required 1, cost 4 - should
        # be included at level 1 with 10 mp.
        self.assertIn(("spell", "mark of decay", False), actions)

    def test_excludes_spells_above_current_level(self):
        npc = create.create_object(HostileNPC, key="haruspex npc 2", location=self.room1)
        npc.db.player_class = "haruspex"
        npc.db.level = 1
        npc.db.mp = 999
        npc.db.sp = 0

        actions = npc._gather_actions()

        # "rite of the entrails" is haruspex, level_required 15.
        names = [a[1] for a in actions if a[0] == "spell"]
        self.assertNotIn("rite of the entrails", names)

    def test_excludes_unaffordable_spells(self):
        npc = create.create_object(HostileNPC, key="haruspex npc 3", location=self.room1)
        npc.db.player_class = "haruspex"
        npc.db.level = 1
        npc.db.mp = 0  # can't afford anything
        npc.db.sp = 0

        actions = npc._gather_actions()
        self.assertEqual(actions, [("attack", None, False)])

    def test_excludes_wrong_class_spells(self):
        npc = create.create_object(HostileNPC, key="haruspex npc 4", location=self.room1)
        npc.db.player_class = "haruspex"
        npc.db.level = 100
        npc.db.mp = 999
        npc.db.sp = 999

        actions = npc._gather_actions()
        names = [a[1] for a in actions if a[0] == "spell"]
        # "cure wounds" belongs to medicus/augur, not haruspex.
        self.assertNotIn("cure wounds", names)


class TestHostileNPCTurnAI(EvenniaTest):
    def test_no_opponent_does_nothing(self):
        from world.combat import CombatTurnHandler

        npc = create.create_object(HostileNPC, key="lone npc", location=self.room1)
        npc.db.player_class = None
        npc.db.hp = 100
        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        handler.db.fighters = [npc]
        npc.db.combat_turnhandler = handler

        npc.at_turn_start()  # should not raise with no valid opponent

    def test_attacks_opponent_when_no_class(self):
        from world.combat import CombatTurnHandler

        npc = create.create_object(HostileNPC, key="attacker npc", location=self.room1)
        npc.db.player_class = None
        npc.db.hp = 100
        npc.db.virtus = 10
        npc.db.agilitas = 10
        npc.db.unarmed_damage_range = (10, 10)
        npc.db.unarmed_accuracy = 100
        npc.db.wielded_weapon = None
        npc.db.worn_armor = None
        npc.db.conditions = {}

        self.char1.db.hp = 100
        self.char1.db.agilitas = 10
        self.char1.db.worn_armor = None
        self.char1.db.conditions = {}

        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        handler.db.fighters = [npc, self.char1]
        npc.db.combat_turnhandler = handler

        with patch("world.combat.randint", side_effect=_randint_side_effect):
            npc.at_turn_start()

        self.assertLess(self.char1.db.hp, 100)


class TestSummonedAlly(EvenniaTest):
    def test_mirrors_owners_last_target(self):
        from world.combat import CombatTurnHandler

        ally = create.create_object(SummonedAlly, key="familiar", location=self.room1)
        ally.db.hp = 20
        ally.db.virtus = 10
        ally.db.unarmed_damage_range = (5, 5)
        ally.db.unarmed_accuracy = 100
        ally.db.wielded_weapon = None
        ally.db.worn_armor = None
        ally.db.conditions = {}
        ally.db.instance_owner = self.char1

        self.char1.db.combat_last_target = self.char2
        self.char1.db.hp = 100
        self.char2.db.hp = 100
        self.char2.db.agilitas = 10
        self.char2.db.worn_armor = None
        self.char2.db.conditions = {}

        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        handler.db.fighters = [ally, self.char1, self.char2]
        ally.db.combat_turnhandler = handler

        with patch("world.combat.randint", side_effect=_randint_side_effect):
            ally.at_turn_start()

        self.assertLess(self.char2.db.hp, 100)
        self.assertEqual(self.char1.db.hp, 100)  # owner untouched

    def test_falls_back_to_any_other_fighter_if_no_last_target(self):
        from world.combat import CombatTurnHandler

        ally = create.create_object(SummonedAlly, key="familiar2", location=self.room1)
        ally.db.hp = 20
        ally.db.virtus = 10
        ally.db.unarmed_damage_range = (5, 5)
        ally.db.unarmed_accuracy = 100
        ally.db.wielded_weapon = None
        ally.db.worn_armor = None
        ally.db.conditions = {}
        ally.db.instance_owner = self.char1

        self.char1.db.combat_last_target = None
        self.char1.db.hp = 100
        self.char2.db.hp = 100
        self.char2.db.agilitas = 10
        self.char2.db.worn_armor = None
        self.char2.db.conditions = {}

        handler = create.create_script(CombatTurnHandler, obj=self.room1, autostart=False)
        handler.db.fighters = [ally, self.char1, self.char2]
        ally.db.combat_turnhandler = handler

        with patch("world.combat.randint", side_effect=_randint_side_effect):
            ally.at_turn_start()

        self.assertLess(self.char2.db.hp, 100)


class TestRespawningNPCAndTimer(EvenniaTest):
    def test_at_object_post_creation_marks_respawns_and_home(self):
        npc = create.create_object(RespawningNPC, key="trainer", location=self.room1)
        self.assertTrue(npc.db.respawns)
        self.assertEqual(npc.db.respawn_home, self.room1)

    def test_schedule_respawn_creates_a_persistent_autostart_timer(self):
        npc = create.create_object(RespawningNPC, key="trainer2", location=self.room1)
        npc.db.respawn_delay = 45

        COMBAT_RULES.schedule_respawn(npc)

        timers = [s for s in npc.scripts.all() if isinstance(s, RespawnTimer)]
        self.assertEqual(len(timers), 1)
        timer = timers[0]
        # This is the actual mechanism that's supposed to make a
        # respawn-in-progress survive a server reload - a persistent
        # Script, not a bare delay() call.
        self.assertTrue(timer.persistent)
        self.assertEqual(timer.interval, 45)
        self.assertIsNone(npc.location)  # removed from play while waiting

    def test_schedule_respawn_defaults_delay_to_90(self):
        npc = create.create_object(RespawningNPC, key="trainer3", location=self.room1)
        COMBAT_RULES.schedule_respawn(npc)
        timer = [s for s in npc.scripts.all() if isinstance(s, RespawnTimer)][0]
        self.assertEqual(timer.interval, 90)

    def test_respawn_timer_restores_npc_at_full_hp_in_home_room(self):
        npc = create.create_object(RespawningNPC, key="trainer4", location=self.room1)
        npc.db.max_hp = 100
        npc.db.hp = 0
        npc.db.respawn_home = self.room1
        npc.move_to(None, quiet=True)

        timer = create.create_script(RespawnTimer, obj=npc, autostart=False)
        timer.at_repeat()

        self.assertEqual(npc.db.hp, npc.db.max_hp)
        self.assertEqual(npc.location, self.room1)
        self.assertFalse(timer.pk)  # one-shot: stops and deletes itself

    def test_respawn_timer_cleans_up_if_home_room_was_destroyed(self):
        home = create.create_object("typeclasses.rooms.Room", key="doomed home")
        npc = create.create_object(RespawningNPC, key="trainer5", location=home)
        npc.db.respawn_home = home
        npc.move_to(None, quiet=True)
        home.delete()

        timer = create.create_script(RespawnTimer, obj=npc, autostart=False)
        timer.at_repeat()  # must not raise

        self.assertFalse(timer.pk)
