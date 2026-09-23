"""
Tests for world/pacifism.py - the pacifism flag itself, the eligibility
gates, gear surrender, and every real combat-entry point (CmdFight,
skill_ambush, CmdChallenge, join_fight, the room-sweep 'fight all'
fallback, apply_damage, and both wildernesses' _aggro_on_sight) that
must refuse a pacifist. Also covers the has_ever_killed_player flag
set in world/combat.py's PvP branch, and world/quests.py's kill-step
refusal for a pacifist.
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create

from world.combat import (
    COMBAT_RULES,
    CombatTurnHandler,
    HostileNPC,
    AutoStatNPC,
    CmdFight,
    CmdChallenge,
)
from world.prototypes import ARENA_TRAINER
from world.tests_combat_commands import CombatCommandTestBase
from world.tests_combat import CombatTestBase
from world.pacifism import (
    PACIFISM_COMBAT_COOLDOWN,
    is_pacifist,
    pacifism_blockers,
    become_pacifist,
    restore_combatant,
    CmdPacifism,
    CmdGodPacifism,
)


def _weapon(location):
    return create.create_object(
        "typeclasses.objects.Object",
        key="a plain sword",
        location=location,
        attributes=[("stat_bonuses", {}), ("resource_bonuses", {})],
    )


class TestEligibility(EvenniaTest):
    def test_eligible_by_default(self):
        self.assertEqual(pacifism_blockers(self.char1), [])

    def test_already_pacifist_is_its_own_blocker(self):
        self.char1.db.pacifist = True
        self.assertIn("already", pacifism_blockers(self.char1)[0])

    def test_ever_killed_a_player_is_a_permanent_blocker(self):
        self.char1.db.has_ever_killed_player = True
        blockers = pacifism_blockers(self.char1)
        self.assertIn("killed another player", blockers[0])

    def test_currently_in_combat_blocks(self):
        self.char1.db.combat_turnhandler = create.create_script(CombatTurnHandler, obj=self.room1)
        blockers = pacifism_blockers(self.char1)
        self.assertIn("middle of a fight", blockers[0])

    def test_recent_combat_activity_blocks(self):
        import time
        self.char1.db.last_combat_activity = time.time()
        blockers = pacifism_blockers(self.char1)
        self.assertIn("keyed up", blockers[0])

    def test_old_combat_activity_does_not_block(self):
        import time
        self.char1.db.last_combat_activity = time.time() - PACIFISM_COMBAT_COOLDOWN - 10
        self.assertEqual(pacifism_blockers(self.char1), [])

    def test_is_pacifist_reads_the_flag(self):
        self.assertFalse(is_pacifist(self.char1))
        self.char1.db.pacifist = True
        self.assertTrue(is_pacifist(self.char1))


class TestBecomePacifist(EvenniaTest):
    def test_sets_the_flag(self):
        become_pacifist(self.char1)
        self.assertTrue(self.char1.db.pacifist)

    def test_ordinary_gear_is_unequipped_but_kept(self):
        weapon = _weapon(self.char1)
        self.char1.db.wielded_weapon = weapon
        become_pacifist(self.char1)
        self.assertIsNone(self.char1.db.wielded_weapon)
        self.assertTrue(weapon.pk)
        self.assertEqual(weapon.location, self.char1)

    def test_unique_gear_is_destroyed_not_dropped(self):
        armor = create.create_object(
            "typeclasses.objects.Object",
            key="the One True Cuirass",
            location=self.char1,
            attributes=[
                ("stat_bonuses", {}), ("resource_bonuses", {}), ("unique_item", True),
            ],
        )
        self.char1.db.worn_armor = armor
        become_pacifist(self.char1)
        self.assertIsNone(self.char1.db.worn_armor)
        self.assertFalse(armor.pk)

    def test_removes_stat_bonuses_from_equipped_gear(self):
        # Only accessory armor (never a weapon) carries stat_bonuses
        # in this game's real data model - see world/combat.py's own
        # EQUIPMENT_STAT_KEYS comment.
        bracers = create.create_object(
            "typeclasses.objects.Object",
            key="a pair of bonus bracers",
            location=self.char1,
            attributes=[("stat_bonuses", {"virtus": 3}), ("resource_bonuses", {})],
        )
        self.char1.db.virtus = 13
        self.char1.db.worn_arms = bracers
        become_pacifist(self.char1)
        self.assertEqual(self.char1.db.virtus, 10)

    def test_reports_kept_and_destroyed_gear_separately(self):
        msgs = []
        self.char1.msg = lambda text="", **kw: msgs.append(str(text))
        self.char1.db.wielded_weapon = _weapon(self.char1)
        unique = create.create_object(
            "typeclasses.objects.Object",
            key="the Only One",
            location=self.char1,
            attributes=[("stat_bonuses", {}), ("resource_bonuses", {}), ("unique_item", True)],
        )
        self.char1.db.worn_armor = unique
        become_pacifist(self.char1)
        self.assertTrue(any("a plain sword" in m for m in msgs))
        self.assertTrue(any("the Only One" in m and "Gone for good" in m for m in msgs))


class TestPacifismAchievement(EvenniaTest):
    def test_becoming_a_pacifist_grants_the_peaceable(self):
        from evennia.contrib.game_systems.achievements import get_achievement_progress

        become_pacifist(self.char1)
        progress = get_achievement_progress(self.char1, "the_peaceable")
        self.assertTrue(progress.get("completed"))

    def test_reaching_level_ten_as_a_pacifist_grants_iron_will(self):
        from evennia.contrib.game_systems.achievements import get_achievement_progress

        self.char1.db.pacifist = True
        self.char1.db.level = 9
        self.char1.db.xp = 0
        self.char1.db.max_hp = 100
        self.char1.db.max_mp = 20
        self.char1.db.max_sp = 30

        # has_account (evennia.objects.objects.DefaultObject) means "has
        # an active session right now" - always False for a bare
        # EvenniaTest fixture even though .account is set. See CLAUDE.md
        # gotcha #18.
        with patch("evennia.objects.objects.DefaultObject.has_account", new=True):
            COMBAT_RULES.award_xp(self.char1, COMBAT_RULES.xp_for_level(9))

        self.assertEqual(self.char1.db.level, 10)
        progress = get_achievement_progress(self.char1, "iron_will")
        self.assertTrue(progress.get("completed"))

    def test_reaching_level_ten_as_a_combatant_does_not_grant_iron_will(self):
        from evennia.contrib.game_systems.achievements import get_achievement_progress

        self.char1.db.pacifist = False
        self.char1.db.level = 9
        self.char1.db.xp = 0
        self.char1.db.max_hp = 100
        self.char1.db.max_mp = 20
        self.char1.db.max_sp = 30

        with patch("evennia.objects.objects.DefaultObject.has_account", new=True):
            COMBAT_RULES.award_xp(self.char1, COMBAT_RULES.xp_for_level(9))

        self.assertEqual(self.char1.db.level, 10)
        progress = get_achievement_progress(self.char1, "iron_will")
        self.assertFalse(progress.get("completed"))


class TestRestoreCombatant(EvenniaTest):
    def test_clears_the_flag(self):
        self.char1.db.pacifist = True
        restore_combatant(self.char1)
        self.assertFalse(self.char1.db.pacifist)


class TestCmdPacifism(EvenniaCommandTest):
    def test_bare_command_shows_a_warning_and_does_not_switch(self):
        result = self.call(CmdPacifism(), "", caller=self.char1)
        self.assertIn("permanent", result)
        self.assertIn("confirm", result)
        self.assertFalse(self.char1.db.pacifist)

    def test_warning_names_unique_gear_at_risk(self):
        unique = create.create_object(
            "typeclasses.objects.Object",
            key="the Doomed Blade",
            location=self.char1,
            attributes=[("stat_bonuses", {}), ("resource_bonuses", {}), ("unique_item", True)],
        )
        self.char1.db.wielded_weapon = unique
        result = self.call(CmdPacifism(), "", caller=self.char1)
        self.assertIn("the Doomed Blade", result)
        self.assertIn("lost for good", result)

    def test_confirm_actually_switches(self):
        result = self.call(CmdPacifism(), "confirm", caller=self.char1)
        self.assertTrue(self.char1.db.pacifist)
        self.assertIn("lay down your arms", result)

    def test_a_blocked_character_cannot_confirm_their_way_past_it(self):
        self.char1.db.has_ever_killed_player = True
        result = self.call(CmdPacifism(), "confirm", caller=self.char1)
        self.assertIn("killed another player", result)
        self.assertFalse(self.char1.db.pacifist)

    def test_already_pacifist_is_told_so(self):
        self.char1.db.pacifist = True
        result = self.call(CmdPacifism(), "", caller=self.char1)
        self.assertIn("already", result)


class TestCmdGodPacifism(EvenniaCommandTest):
    def test_a_mortal_cannot_use_it(self):
        self.char1.db.level = 50
        self.char2.db.pacifist = True
        result = self.call(CmdGodPacifism(), self.char2.key, caller=self.char1)
        self.assertIn("Only gods", result)
        self.assertTrue(self.char2.db.pacifist)

    def test_a_god_restores_a_real_pacifist(self):
        self.char1.db.level = 106
        self.char2.db.pacifist = True
        result = self.call(CmdGodPacifism(), self.char2.key, caller=self.char1)
        self.assertIn("can fight again", result)
        self.assertFalse(self.char2.db.pacifist)

    def test_refuses_a_non_pacifist_target(self):
        self.char1.db.level = 106
        result = self.call(CmdGodPacifism(), self.char2.key, caller=self.char1)
        self.assertIn("isn't a pacifist", result)


class TestApplyDamageNoOp(CombatTestBase):
    def test_a_pacifist_takes_no_damage_at_all(self):
        self.char1.db.pacifist = True
        self.char1.db.hp = 50
        COMBAT_RULES.apply_damage(self.char1, 30)
        self.assertEqual(self.char1.db.hp, 50)

    def test_combat_activity_is_stamped_for_a_real_hit_between_accounts(self):
        self.char2.db.hp = 50
        COMBAT_RULES.apply_damage(self.char2, 10, attacker=self.char1)
        self.assertTrue(self.char2.db.last_combat_activity)
        self.assertTrue(self.char1.db.last_combat_activity)

    def test_combat_activity_is_not_stamped_for_a_bare_npc_attacker(self):
        npc = create.create_object(AutoStatNPC, key="a mindless brute", location=self.room1)
        self.char2.db.hp = 50
        COMBAT_RULES.apply_damage(self.char2, 10, attacker=npc)
        self.assertIsNone(npc.db.last_combat_activity)


class TestPvPKillFlag(CombatTestBase):
    def test_defeating_another_player_flags_the_attacker(self):
        self.char2.db.hp = 0
        self.char2.db.damage_log = {self.char1: 10}
        self.assertIsNone(self.char1.db.has_ever_killed_player)
        COMBAT_RULES.at_defeat(self.char2, attacker=self.char1)
        self.assertTrue(self.char1.db.has_ever_killed_player)

    def test_an_ordinary_npc_kill_never_sets_the_flag(self):
        npc = create.create_object(
            HostileNPC, key="a training dummy", location=self.room1,
            attributes=[("xp_reward", 10), ("damage_log", {self.char1: 10})],
        )
        COMBAT_RULES.at_defeat(npc, attacker=self.char1)
        self.assertIsNone(self.char1.db.has_ever_killed_player)


class TestCombatEntryGuards(CombatCommandTestBase):
    def test_a_pacifist_cannot_start_fight(self):
        self.char1.db.pacifist = True
        result = self.call(CmdFight(), "", caller=self.char1)
        self.assertIn("laid down arms", result)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_cannot_start_a_fight_against_a_pacifist_target(self):
        self.char2.db.pacifist = True
        result = self.call(CmdFight(), self.char2.key, caller=self.char1)
        self.assertIn("laid down arms", result)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_fight_all_excludes_a_pacifist_bystander(self):
        self.char2.db.pacifist = True
        self.char2.db.hp = 10
        npc = create.create_object(AutoStatNPC, key="a rowdy brawler", location=self.room1)
        npc.db.hp = 10
        self.call(CmdFight(), "all", caller=self.char1)
        self.assertNotIn(self.char2, self.room1.db.combat_turnhandler.db.fighters)

    def test_join_fight_never_inserts_a_pacifist(self):
        handler = create.create_script(CombatTurnHandler, obj=self.room1)
        before = list(handler.db.fighters)
        self.char2.db.pacifist = True
        handler.join_fight(self.char2)
        self.assertEqual(handler.db.fighters, before)

    def test_challenge_refuses_a_pacifist_caller(self):
        self.room1.db.trainer_prototype = ARENA_TRAINER
        self.char1.db.pacifist = True
        result = self.call(CmdChallenge(), "", caller=self.char1)
        self.assertIn("laid down arms", result)
        self.assertIsNone(self.char1.ndb.active_trainer_npc)


class TestWildernessAggroExemption(EvenniaTest):
    def test_no_encounter_ever_spawns_for_a_pacifist(self):
        from evennia.contrib.grid import wilderness
        from world.wilderness_rome import RomeWildernessMapProvider

        wilderness.create_wilderness(
            name="test_pacifist_road", mapprovider=RomeWildernessMapProvider()
        )
        self.char1.db.level = 25
        self.char1.db.pacifist = True
        wilderness.enter_wilderness(self.char1, coordinates=(0, 0), name="test_pacifist_road")

        for _ in range(60):
            exits = {e.key: e for e in self.char1.location.exits}
            exits["north"].at_traverse(self.char1, exits["north"].destination)
            npcs = [o for o in self.char1.location.contents if o.db.race]
            self.assertEqual(npcs, [])
            south = {e.key: e for e in self.char1.location.exits}
            south["south"].at_traverse(self.char1, south["south"].destination)


class TestQuestKillStepRefusesPacifist(EvenniaCommandTest):
    def test_a_pacifist_cannot_start_a_kill_quest(self):
        from world.quests import CmdQuest

        self.char1.db.pacifist = True
        self.char1.db.level = 10
        giver = create.create_object(
            "typeclasses.characters.Character", key="a grain-dole administrator",
            location=self.room1,
        )
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("laid down arms", result)
        self.assertNotIn("grain_doesnt_add_up", self.char1.db.quest_log or {})

    def test_a_pacifist_can_still_start_a_visit_quest(self):
        from world.quests import CmdQuest

        self.char1.db.pacifist = True
        self.char1.db.level = 10
        giver = create.create_object(
            "typeclasses.characters.Character", key="a priest of Ceres", location=self.room1,
        )
        result = self.call(CmdQuest(), "", caller=self.char1)
        self.assertIn("Objective:", result)
        self.assertIn("ceres_favor", self.char1.db.quest_log or {})

    def test_entry_hint_never_teases_a_kill_quest_to_a_pacifist(self):
        from world.quests import quest_entry_hint

        self.char1.db.pacifist = True
        self.char1.db.level = 10
        create.create_object(
            "typeclasses.characters.Character", key="a grain-dole administrator",
            location=self.room1,
        )
        msgs = []
        self.char1.msg = lambda text="", **kw: msgs.append(str(text))
        self.char1.location = self.room1
        quest_entry_hint(self.char1)
        self.assertEqual(msgs, [])
