"""
End-to-end tests for the actual combat Commands (CmdFight, CmdAttack,
CmdPowerAttack, CmdPass, CmdDisengage, CmdChallenge, CmdCast,
CmdUseSkill) - the priority gap flagged after the first review pass:
world/tests_combat.py exercised CombatRules' methods directly, but
never the Command layer itself (argument parsing, turn/action gating,
target resolution) where a player would actually notice a bug.

Also carries the regression tests for a real bug found while writing
this file: CmdCast and CmdUseSkill's named-target resolution used
plain caller.search(), which - like the already-documented
find_combat_target fix for attack/fight/powerattack - fails to find
another real Character by their exact name for a non-Builder caller
(rpsystem's sdesc-aware search override; NPCs are unaffected since
they don't have an sdesc handler). Both commands now use
find_combat_target, matching existing precedent in this file.
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaCommandTest
from evennia.utils import create

from world.combat import (
    COMBAT_RULES,
    CombatTurnHandler,
    CmdFight,
    CmdAttack,
    CmdAutoAttack,
    CmdCombatRow,
    CmdBuyPet,
    PetVendor,
    CmdPowerAttack,
    CmdPass,
    CmdDisengage,
    CmdChallenge,
    CmdCast,
    CmdUseSkill,
    CmdCoreStats,
    CmdLearn,
    CmdTrainer,
    CmdRest,
    CmdSkillInfo,
    CmdSpellInfo,
    CmdWield,
    CmdUnwield,
    CmdDon,
    CmdDoff,
    CmdCompare,
    CmdInspect,
    CmdDismissPet,
    CmdRestore,
    CmdGodLevel,
    CmdGodSet,
    CmdGodTeleport,
    CmdLook,
    CmdForce,
    SKILLS,
    SPELLS,
    POWERATTACK_SP_COST,
    DISENGAGE_SUCCESS_CHANCE,
    DISENGAGE_XP_PENALTY_PERCENT,
    AUTO_ATTACK_DELAY,
    MOVEMENT_SP_COST,
    MOVEMENT_SP_WARN_THRESHOLD,
    MAX_LEVEL,
    LEVEL_UP_HP_GAIN,
    LEVEL_UP_MP_GAIN,
    LEVEL_UP_SP_GAIN,
)
from evennia.contrib.game_systems.mail import CmdMailCharacter


class CombatCommandTestBase(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.db.wielded_weapon = None
            char.db.worn_armor = None
            char.db.conditions = {}
            char.db.virtus = 10
            char.db.agilitas = 10
            char.db.ingenium = 10
            char.db.vigor = 10
            char.db.player_class = None
            char.db.damage_log = {}
            char.db.max_hp = 100
            char.db.hp = 100
            char.db.max_mp = 20
            char.db.mp = 20
            char.db.max_sp = 30
            char.db.sp = 30
            char.db.is_dead = False
            char.db.resting = False
            char.db.combat_turnhandler = None
            char.db.combat_side = None
            char.location = self.room1

    def _start_duel(self):
        """Puts char1 and char2 into a real 1v1 fight via CmdFight, char1 going first."""
        with patch("world.combat.COMBAT_RULES.roll_init") as mock_roll:
            # char1 always wins initiative -> goes first.
            mock_roll.side_effect = lambda char: 1000 if char == self.char1 else 1
            self.call(CmdFight(), "Char2", caller=self.char1)
        return self.char1.db.combat_turnhandler


class TestCmdFight(CombatCommandTestBase):
    def test_starts_a_duel_with_a_named_target(self):
        self.call(CmdFight(), "Char2", caller=self.char1)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char2))

    def test_no_combat_zone_blocks_a_named_duel(self):
        self.room1.tags.add("no_combat_zone", category="zone")
        result = self.call(CmdFight(), "Char2", caller=self.char1)
        self.assertIn("forbids violence", result)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_no_combat_zone_blocks_fight_all(self):
        self.room1.tags.add("no_combat_zone", category="zone")
        result = self.call(CmdFight(), "all", caller=self.char1)
        self.assertIn("forbids violence", result)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_no_target_auto_picks_lone_other_fighter(self):
        self.call(CmdFight(), "", caller=self.char1)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))

    def test_cannot_fight_self(self):
        self.call(CmdFight(), "Char1", caller=self.char1)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_cannot_fight_while_already_in_combat(self):
        self._start_duel()
        result = self.call(CmdFight(), "Char2", caller=self.char1)
        self.assertIn("already in a fight", result)

    def test_cannot_fight_while_resting(self):
        self.char1.db.resting = True
        result = self.call(CmdFight(), "Char2", caller=self.char1)
        self.assertIn("resting", result)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_cannot_fight_if_dead(self):
        self.char1.db.is_dead = True
        result = self.call(CmdFight(), "Char2", caller=self.char1)
        self.assertIn("dead", result)

    def test_starting_a_fight_regens_a_wounded_respawning_npc(self):
        # Integration coverage for the disengage/rest/re-engage grind
        # loop fix: char2 stands in for a persistent NPC (db.respawns)
        # left wounded from an earlier encounter - starting a fresh
        # fight against it should trigger regen_out_of_combat_hp via
        # initialize_for_combat before any new damage is dealt.
        import time
        self.char2.db.respawns = True
        self.char2.db.max_hp = 200
        self.char2.db.hp = 100
        self.char2.db.last_damaged_at = time.time() - 60  # 1 minute ago

        self.call(CmdFight(), "Char2", caller=self.char1)

        self.assertEqual(self.char2.db.hp, 130)  # 15%/minute of 200 = 30

    def test_fight_all_groups_by_party(self):
        ally = create.create_object(
            "typeclasses.characters.Character", key="Ally", location=self.room1
        )
        ally.db.hp = 100
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, ally]
        ally.db.party_leader = self.char1

        self.call(CmdFight(), "all", caller=self.char1)

        handler = self.char1.db.combat_turnhandler
        self.assertTrue(handler)
        self.assertEqual(self.char1.db.combat_side, ally.db.combat_side)
        self.assertNotEqual(self.char1.db.combat_side, self.char2.db.combat_side)


class TestPetsJoinFights(CombatCommandTestBase):
    """
    Regression coverage for a real player report predating this
    session's row/pet work: a pet neither followed into a fight nor
    was protected from its own owner's attacks. Root cause: a normal
    1-on-1 duel (CmdFight's pending_fighters path) never swept anyone
    but the two named combatants into db.fighters at all, so a pet
    standing right there never got a turn and had no combat_side of
    its own - see CombatTurnHandler._sync_companion_pets.
    """

    def _make_pet(self, owner):
        from world.combat import SummonedAlly

        pet = create.create_object(SummonedAlly, key="a loyal pet", location=self.room1)
        pet.db.hp = 20
        pet.db.max_hp = 20
        owner.db.active_companion = pet
        pet.db.instance_owner = owner
        return pet

    def test_pet_joins_a_normal_duel(self):
        pet = self._make_pet(self.char1)
        handler = self._start_duel()
        self.assertIn(pet, handler.db.fighters)

    def test_pet_shares_its_owners_combat_side_in_a_duel(self):
        pet = self._make_pet(self.char1)
        self._start_duel()
        self.assertEqual(pet.db.combat_side, self.char1.db.combat_side)
        self.assertNotEqual(pet.db.combat_side, self.char2.db.combat_side)

    def test_fight_all_puts_the_pet_on_its_owners_side_not_the_mob(self):
        # 'fight all' already sweeps a pet into db.fighters (it's
        # sitting in the room with real hp) - but before this fix, the
        # side-assignment loop had no concept of pet ownership, so a
        # partyless, account-less pet fell into the same catch-all
        # "mob" side as the actual hostile.
        pet = self._make_pet(self.char1)
        self.call(CmdFight(), "all", caller=self.char1)
        self.assertEqual(pet.db.combat_side, self.char1.db.combat_side)
        self.assertNotEqual(pet.db.combat_side, self.char2.db.combat_side)

    def test_personal_challenge_opponent_is_not_pulled_onto_challengers_side(self):
        # A personal-instance duel opponent (Rutilus, a Deeper Sands
        # Arena challenge) ALSO gets db.instance_owner set, via the
        # exact same spawn_personal_npc() a pet uses - that's an
        # adversary, not a pet, and must stay opposed. Only
        # active_companion (never pointed at an opponent) may pull a
        # fighter onto its owner's side.
        opponent = create.create_object(
            "typeclasses.characters.Character", key="a personal foe", location=self.room1
        )
        opponent.db.hp = 30
        opponent.db.instance_owner = self.char1
        self.char1.db.active_companion = None

        self.room1.ndb.pending_fighters = [self.char1, opponent]
        handler = self.room1.scripts.add(CombatTurnHandler)

        self.assertNotEqual(self.char1.db.combat_side, opponent.db.combat_side)

    def test_join_fight_pulls_in_the_joiners_own_pet_too(self):
        self._start_duel()
        ally = create.create_object(
            "typeclasses.characters.Character", key="Ally", location=self.room1
        )
        ally.db.hp = 50
        pet = self._make_pet(ally)

        handler = self.char1.db.combat_turnhandler
        handler.join_fight(ally)

        self.assertIn(pet, handler.db.fighters)
        self.assertEqual(pet.db.combat_side, ally.db.combat_side)


class TestCmdAttack(CombatCommandTestBase):
    def test_attack_out_of_combat_is_rejected(self):
        result = self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertIn("only do that in combat", result)

    def test_attack_on_your_turn_deals_damage(self):
        self._start_duel()
        self.char2.db.hp = 100
        # A non-lethal roll (100 would one-shot a 100-hp char2, which
        # triggers the real player-defeat/respawn flow and restores
        # hp to full again - not what this test is checking).
        with patch("world.combat.randint", return_value=30):
            self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertLess(self.char2.db.hp, 100)

    def test_attack_out_of_turn_is_rejected(self):
        self._start_duel()
        result = self.call(CmdAttack(), "Char1", caller=self.char2)
        self.assertIn("only do that on your turn", result)

    def test_cannot_attack_self(self):
        self._start_duel()
        result = self.call(CmdAttack(), self.char1.key, caller=self.char1)
        self.assertIn("can't attack yourself", result)

    def test_dead_cannot_attack(self):
        self._start_duel()
        self.char1.db.is_dead = True
        result = self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertIn("dead", result)

    def _equip_weapon(self, char, weapon_type_name, weapon_category, accuracy_bonus=100):
        weapon = create.create_object("world.combat.CombatWeapon", key="a %s" % weapon_type_name)
        weapon.db.weapon_type_name = weapon_type_name
        weapon.db.weapon_category = weapon_category
        weapon.db.accuracy_bonus = accuracy_bonus
        char.db.wielded_weapon = weapon
        return weapon

    def test_ranged_weapon_hit_uses_ranged_specific_message(self):
        self._start_duel()
        self._equip_weapon(self.char1, "shortbow", "ranged")
        with patch("world.combat.randint", return_value=50):
            result = self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertIn("finds its mark", result)

    def test_thunderbolt_hit_uses_its_own_override_message_not_polearms(self):
        self._start_duel()
        # Mechanically a polearm, but should never read as one.
        self._equip_weapon(self.char1, "thunderbolt", "polearm")
        with patch("world.combat.randint", return_value=50):
            result = self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertIn("divine lightning", result)
        self.assertNotIn("skewers", result)

    def test_unarmed_attack_still_uses_the_original_generic_message(self):
        self._start_duel()
        with patch("world.combat.randint", return_value=50):
            result = self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertIn("strikes", result)

    def _make_pet(self, owner):
        from world.combat import SummonedAlly

        pet = create.create_object(SummonedAlly, key="a loyal pet", location=self.room1)
        pet.db.hp = 20
        pet.db.max_hp = 20
        owner.db.active_companion = pet
        pet.db.instance_owner = owner
        return pet

    def test_cannot_attack_own_pet_by_name(self):
        # Real player report: "you could attack them" (referring to
        # your own pet). Confirmed live before this fix: resolve_attack
        # has no ally check at all, and attack <name> searches the
        # whole room, not just who's actually in the fight.
        pet = self._make_pet(self.char1)
        self._start_duel()
        result = self.call(CmdAttack(), pet.key, caller=self.char1)
        self.assertIn("own companion", result.lower())
        self.assertEqual(pet.db.hp, 20)

    def test_bare_attack_never_auto_targets_your_own_pet(self):
        # Once a pet actually joins a fight (CombatTurnHandler.
        # _sync_companion_pets), it sits in db.fighters right next to
        # the real enemy - the no-argument fallback must still pick
        # the enemy, not treat "more than one other fighter" as
        # ambiguous or, worse, silently prefer the pet.
        pet = self._make_pet(self.char1)
        handler = self._start_duel()
        self.assertIn(pet, handler.db.fighters)
        with patch("world.combat.randint", return_value=30):
            result = self.call(CmdAttack(), "", caller=self.char1)
        self.assertLess(self.char2.db.hp, 100)
        self.assertEqual(pet.db.hp, 20)

    def test_killing_the_last_enemy_ends_the_fight_immediately(self):
        # Regression for the real root cause behind "in a party, when
        # the enemy died, I started attacking my party mate": at_defeat
        # used to never proactively re-check victory, so a kill that
        # didn't happen to land on the currently-acting character's own
        # turn could leave the fight technically still running for one
        # more turn. Confirmed here the direct way - a normal kill via
        # CmdAttack must clear combat_turnhandler immediately.
        self._start_duel()
        self.char2.db.hp = 1
        with patch("world.combat.randint", return_value=100):
            self.call(CmdAttack(), "Char2", caller=self.char1)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char2))


class TestCmdAutoAttack(CombatCommandTestBase):
    def test_on_by_default_for_a_fresh_character(self):
        self.assertTrue(self.char1.db.auto_attack)

    def test_no_argument_shows_current_state_without_changing_it(self):
        self.char1.db.auto_attack = True
        result = self.call(CmdAutoAttack(), "", caller=self.char1)
        self.assertIn("ON", result)
        self.assertTrue(self.char1.db.auto_attack)  # unchanged, just shown

    def test_off_turns_it_off(self):
        result = self.call(CmdAutoAttack(), "off", caller=self.char1)
        self.assertFalse(self.char1.db.auto_attack)
        self.assertIn("OFF", result)

    def test_on_turns_it_on(self):
        self.char1.db.auto_attack = False
        result = self.call(CmdAutoAttack(), "on", caller=self.char1)
        self.assertTrue(self.char1.db.auto_attack)
        self.assertIn("ON", result)

    def test_garbage_argument_shows_usage_and_does_not_change_state(self):
        self.char1.db.auto_attack = True
        result = self.call(CmdAutoAttack(), "banana", caller=self.char1)
        self.assertIn("Usage:", result)
        self.assertTrue(self.char1.db.auto_attack)

    def test_at_turn_start_schedules_the_delayed_auto_attack(self):
        # Confirms the wiring (at_turn_start -> evennia_utils.delay) is
        # actually in place, without needing a real elapsed delay -
        # the delay mechanism itself only ever fires correctly on a
        # live running server, not from a test/shell process (same
        # class of limitation already documented for RespawnTimer).
        self._start_duel()
        self.char1.db.auto_attack = True
        with patch("world.combat.evennia_utils.delay") as mock_delay:
            self.char1.at_turn_start()
        mock_delay.assert_called_once_with(
            AUTO_ATTACK_DELAY, COMBAT_RULES.try_auto_attack, self.char1
        )

    def test_at_turn_start_does_not_schedule_when_toggled_off(self):
        self._start_duel()
        self.char1.db.auto_attack = False
        with patch("world.combat.evennia_utils.delay") as mock_delay:
            self.char1.at_turn_start()
        mock_delay.assert_not_called()

    def test_never_targets_a_party_mate_after_the_only_enemy_dies(self):
        # Root-cause regression for a real player report: "in a party,
        # when the enemy died, I started attacking my party mate."
        # Confirmed live before this fix: try_auto_attack's own
        # fallback ("if there's exactly one other living fighter left,
        # attack them") had no concept of sides at all - the moment the
        # party's only enemy died, the only other living fighter left
        # in the fight was the player's own ally.
        ally = create.create_object(
            "typeclasses.characters.Character", key="Ally", location=self.room1
        )
        ally.db.hp = 50
        ally.db.max_hp = 50
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, ally]
        ally.db.party_leader = self.char1

        with patch("world.combat.COMBAT_RULES.roll_init") as mock_roll:
            mock_roll.side_effect = lambda char: 1000 if char == self.char1 else 1
            self.call(CmdFight(), "all", caller=self.char1)

        handler = self.char1.db.combat_turnhandler
        self.char1.db.combat_last_target = self.char2
        self.char2.db.hp = 0  # the enemy just died (e.g. mid-turn, via
        # a pet's bonus damage or a condition tick - see at_defeat's
        # own proactive check_for_victory fix for why the fight isn't
        # necessarily already over at this exact moment)

        # Force deterministic turn state, matching a real fresh turn.
        handler.db.turn = handler.db.fighters.index(self.char1)
        self.char1.db.combat_actionsleft = 1

        COMBAT_RULES.try_auto_attack(self.char1)

        self.assertEqual(ally.db.hp, 50)


class TestCmdCombatRow(CombatCommandTestBase):
    def test_no_argument_shows_current_row_without_changing_it(self):
        self.char1.db.combat_row = None
        result = self.call(CmdCombatRow(), "", caller=self.char1)
        self.assertIn("front", result.lower())
        self.assertIsNone(self.char1.db.combat_row)  # unchanged, just shown

    def test_back_sets_the_back_row(self):
        result = self.call(CmdCombatRow(), "back", caller=self.char1)
        self.assertEqual(self.char1.db.combat_row, "back")
        self.assertIn("back", result.lower())

    def test_front_sets_the_front_row(self):
        self.char1.db.combat_row = "back"
        result = self.call(CmdCombatRow(), "front", caller=self.char1)
        self.assertEqual(self.char1.db.combat_row, "front")
        self.assertIn("front", result.lower())

    def test_garbage_argument_shows_usage_and_does_not_change_state(self):
        self.char1.db.combat_row = "front"
        result = self.call(CmdCombatRow(), "sideways", caller=self.char1)
        self.assertIn("Usage:", result)
        self.assertEqual(self.char1.db.combat_row, "front")

    def test_can_be_set_outside_combat(self):
        self.char1.db.combat_turnhandler = None
        result = self.call(CmdCombatRow(), "back", caller=self.char1)
        self.assertEqual(self.char1.db.combat_row, "back")


class TestCmdBuyPet(CombatCommandTestBase):
    def setUp(self):
        super().setUp()
        from evennia.utils import create

        self.vendor = create.create_object(PetVendor, key="a pet vendor", location=self.room1)
        self.char1.db.level = 10
        self.char1.db.gold = 500
        self.char1.db.active_companion = None

    def test_no_vendor_in_room_refuses(self):
        self.vendor.location = self.room2
        result = self.call(CmdBuyPet(), "hound", caller=self.char1)
        self.assertIn("no pet vendor", result.lower())

    def test_no_argument_lists_stock(self):
        result = self.call(CmdBuyPet(), "", caller=self.char1)
        self.assertIn("hound", result.lower())
        self.assertIn("hawk", result.lower())

    def test_unknown_pet_name_refuses(self):
        result = self.call(CmdBuyPet(), "dragon", caller=self.char1)
        self.assertIn("doesn't sell", result.lower())

    def test_below_level_requirement_refuses(self):
        self.char1.db.level = 9
        result = self.call(CmdBuyPet(), "hound", caller=self.char1)
        self.assertIn("level", result.lower())
        self.assertIsNone(self.char1.db.active_companion)

    def test_not_enough_gold_refuses(self):
        self.char1.db.gold = 10
        result = self.call(CmdBuyPet(), "hound", caller=self.char1)
        self.assertIn("enough gold", result.lower())
        self.assertIsNone(self.char1.db.active_companion)

    def test_already_having_a_pet_refuses(self):
        from evennia.utils import create
        from world.combat import SummonedAlly

        self.char1.db.active_companion = create.create_object(SummonedAlly, key="existing pet")
        result = self.call(CmdBuyPet(), "hound", caller=self.char1)
        self.assertIn("already have", result.lower())

    def test_successful_purchase_spawns_a_real_pet_and_charges_gold(self):
        result = self.call(CmdBuyPet(), "hound", caller=self.char1)
        self.assertIsNotNone(self.char1.db.active_companion)
        self.assertTrue(self.char1.db.active_companion.pk)
        self.assertEqual(self.char1.db.gold, 350)
        self.assertEqual(self.char1.db.active_companion.location, self.room1)
        self.assertIn("buys", result.lower())

    def test_successful_purchase_sets_instance_owner(self):
        # Real, confirmed live gap found while fixing pets not joining
        # a fight: SummonedAlly.at_turn_start() (which PurchasedPet
        # inherits) finds who to fight by reading db.instance_owner -
        # every spell/skill-summoned pet gets this via
        # spawn_personal_npc, but CmdBuyPet spawned its pet directly
        # and never set it. Harmless while pets never got a turn at
        # all; the moment that's fixed, a pet with no instance_owner
        # would treat its own owner as just another valid target.
        self.call(CmdBuyPet(), "hound", caller=self.char1)
        self.assertEqual(self.char1.db.active_companion.db.instance_owner, self.char1)


class TestCmdPowerAttack(CombatCommandTestBase):
    def test_requires_enough_sp(self):
        self._start_duel()
        self.char1.db.sp = POWERATTACK_SP_COST - 1
        result = self.call(CmdPowerAttack(), "Char2", caller=self.char1)
        self.assertIn("enough SP", result)

    def test_succeeds_with_enough_sp(self):
        self._start_duel()
        self.char1.db.sp = 30
        with patch("world.combat.randint", return_value=100):
            self.call(CmdPowerAttack(), "Char2", caller=self.char1)
        self.assertFalse(self.char1.db.combat_actionsleft)


class TestCmdPass(CombatCommandTestBase):
    def test_pass_ends_turn(self):
        handler = self._start_duel()
        self.assertEqual(handler.db.fighters[handler.db.turn], self.char1)
        self.call(CmdPass(), "", caller=self.char1)
        self.assertEqual(handler.db.fighters[handler.db.turn], self.char2)

    def test_pass_out_of_combat_rejected(self):
        result = self.call(CmdPass(), "", caller=self.char1)
        self.assertIn("only do that in combat", result)


class TestCmdDisengage(CombatCommandTestBase):
    @patch("world.combat.randint")
    def test_successful_disengage_removes_from_fight(self, mock_randint):
        mock_randint.return_value = 1  # <= DISENGAGE_SUCCESS_CHANCE -> success
        self._start_duel()
        self.call(CmdDisengage(), "", caller=self.char1)
        # Only char2 is left standing - this ends the fight entirely
        # (the turn handler script stops and deletes itself), so check
        # char1's own state rather than the now-deleted handler.
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))
        self.assertIsNone(self.char1.db.combat_turnhandler)

    @patch("world.combat.randint")
    def test_failed_disengage_keeps_fighter_in_fight(self, mock_randint):
        mock_randint.return_value = 100  # > DISENGAGE_SUCCESS_CHANCE -> failure
        handler = self._start_duel()
        self.call(CmdDisengage(), "", caller=self.char1)
        self.assertIn(self.char1, handler.db.fighters)
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))

    def test_flee_is_a_real_alias(self):
        """'flee' should resolve to the exact same command as 'disengage'."""
        self.assertIn("flee", CmdDisengage.aliases)

    @patch("world.combat.randint")
    def test_successful_disengage_costs_xp(self, mock_randint):
        mock_randint.return_value = 1  # <= DISENGAGE_SUCCESS_CHANCE -> success
        self.char1.db.xp = 1000
        self._start_duel()
        self.call(CmdDisengage(), "", caller=self.char1)
        self.assertEqual(self.char1.db.xp, 1000 - int(1000 * DISENGAGE_XP_PENALTY_PERCENT))

    @patch("world.combat.randint")
    def test_failed_disengage_costs_no_xp(self, mock_randint):
        mock_randint.return_value = 100  # > DISENGAGE_SUCCESS_CHANCE -> failure
        self.char1.db.xp = 1000
        self._start_duel()
        self.call(CmdDisengage(), "", caller=self.char1)
        self.assertEqual(self.char1.db.xp, 1000)

    @patch("world.combat.randint")
    def test_disengage_xp_penalty_applies_even_against_a_lower_level_enemy(self, mock_randint):
        # Direct design call: the penalty is deliberately NOT gated on
        # the enemy's level - a flat cost on every successful escape,
        # not just against something you're outmatched by.
        mock_randint.return_value = 1
        self.char1.db.xp = 1000
        self.char1.db.level = 50
        self.char2.db.level = 1
        self._start_duel()
        self.call(CmdDisengage(), "", caller=self.char1)
        self.assertLess(self.char1.db.xp, 1000)

    @patch("world.combat.randint")
    def test_disengage_with_zero_xp_does_not_crash_or_go_negative(self, mock_randint):
        mock_randint.return_value = 1
        self.char1.db.xp = 0
        self._start_duel()
        self.call(CmdDisengage(), "", caller=self.char1)
        self.assertEqual(self.char1.db.xp, 0)

    @patch("world.combat.randint")
    def test_successful_disengage_releases_the_active_pet(self, mock_randint):
        """
        Regression coverage for a real, confirmed gap: fleeing combat
        used to leave an active summoned pet behind to keep fighting
        entirely on its own. A successful disengage should now dismiss
        it via CombatRules.release_pet.
        """
        mock_randint.return_value = 1  # <= DISENGAGE_SUCCESS_CHANCE -> success
        pet = create.create_object(
            "world.combat.SummonedAlly", key="a familiar", location=self.room1
        )
        self.char1.db.active_companion = pet
        self._start_duel()

        self.call(CmdDisengage(), "", caller=self.char1)

        self.assertIsNone(self.char1.db.active_companion)
        self.assertFalse(pet.pk)

    @patch("world.combat.randint")
    def test_failed_disengage_does_not_touch_the_pet(self, mock_randint):
        mock_randint.return_value = 100  # > DISENGAGE_SUCCESS_CHANCE -> failure
        pet = create.create_object(
            "world.combat.SummonedAlly", key="a familiar", location=self.room1
        )
        self.char1.db.active_companion = pet
        self._start_duel()

        self.call(CmdDisengage(), "", caller=self.char1)

        self.assertEqual(self.char1.db.active_companion, pet)
        self.assertTrue(pet.pk)


class TestCmdGodTeleport(CombatCommandTestBase):
    """
    godteleport - the god-only alternative to '@tel' that actually
    works on someone mid-fight. The stock teleport command gets
    refused outright by CombatCharacter.at_pre_move's in-combat block
    (a plain hook check, not a permission lock - true superuser status
    doesn't bypass it). This ends the target's combat participation
    cleanly first (CombatRules.force_disengage), then teleports them.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.level = 106  # the acting god

    def test_refuses_below_god_level(self):
        self.char1.db.level = 100
        result = self.call(CmdGodTeleport(), "Char2 = Room2", caller=self.char1)
        self.assertIn("Only a god", result)

    def test_teleports_a_target_not_in_combat(self):
        self.call(CmdGodTeleport(), "Char2 = Room2", caller=self.char1)
        self.assertEqual(self.char2.location, self.room2)

    def test_ends_combat_cleanly_before_teleporting_a_fighting_target(self):
        self._start_duel()
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char2))

        self.call(CmdGodTeleport(), "Char2 = Room2", caller=self.char1)

        self.assertEqual(self.char2.location, self.room2)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char2))

    def test_does_not_cost_the_target_any_xp(self):
        self._start_duel()
        self.char2.db.xp = 1000
        self.call(CmdGodTeleport(), "Char2 = Room2", caller=self.char1)
        self.assertEqual(self.char2.db.xp, 1000)

    def test_pulling_out_the_non_current_turn_fighter_does_not_skip_the_real_turn(self):
        # char1 goes first (per _start_duel's own initiative rigging).
        # Teleporting char2 (NOT the current-turn fighter) away should
        # remove them cleanly without disturbing whose turn it
        # actually is - char1 should still be up.
        handler = self._start_duel()
        self.assertEqual(handler.db.fighters[handler.db.turn], self.char1)

        self.call(CmdGodTeleport(), "Char2 = Room2", caller=self.char1)

        self.assertEqual(self.char2.location, self.room2)
        # Only one fighter left (char1) - the fight ends entirely.
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

    def test_removing_a_fighter_before_the_current_turn_index_does_not_shift_whose_turn_it_is(self):
        # Three fighters, so removing one doesn't just end the fight
        # outright - this is the real test of the index-shift fix:
        # char2 sits BEFORE char1 in turn order, so pulling char2 out
        # mid-fight must shift turnhandler.db.turn back by one to keep
        # pointing at char1, not silently skip to char3 instead.
        third = create.create_object(
            "typeclasses.characters.Character", key="Char3", location=self.room1
        )
        third.db.hp = 100
        third.db.max_hp = 100

        with patch("world.combat.COMBAT_RULES.roll_init") as mock_roll:
            # Turn order: char2, char1, third.
            order = {self.char2: 1000, self.char1: 500, third: 1}
            mock_roll.side_effect = lambda ch: order[ch]
            self.call(CmdFight(), "all", caller=self.char1)

        handler = self.char1.db.combat_turnhandler
        self.assertEqual(handler.db.fighters, [self.char2, self.char1, third])
        # Advance past char2's turn so it's now char1's turn (index 1).
        handler.db.turn = 1
        self.assertEqual(handler.db.fighters[handler.db.turn], self.char1)

        self.call(CmdGodTeleport(), "Char2 = Room2", caller=self.char1)

        self.assertEqual(self.char2.location, self.room2)
        self.assertEqual(handler.db.fighters, [self.char1, third])
        # Index shifted back by one - still correctly points at char1,
        # not accidentally advanced to third.
        self.assertEqual(handler.db.fighters[handler.db.turn], self.char1)

        third.delete()

    def test_refuses_to_teleport_into_a_character(self):
        # Real, confirmed live incident: a god's destination search had
        # no typeclass restriction, so a name matching another
        # CHARACTER resolved to that character instead of a room -
        # move_to() then dropped the target INSIDE them. Reproduced
        # here the direct way: "Char3" matches a real character, not a
        # room, and must be refused rather than silently succeeding.
        third = create.create_object(
            "typeclasses.characters.Character", key="Char3", location=self.room2
        )
        original_location = self.char2.location

        result = self.call(CmdGodTeleport(), "Char2 = Char3", caller=self.char1)

        self.assertIn("only teleports to rooms", result.lower())
        self.assertEqual(self.char2.location, original_location)

        third.delete()


class TestCmdDismissPet(CombatCommandTestBase):
    """
    Regression coverage for the new 'dismiss'/'banish' command - lets
    a player get rid of their active pet outside of the flee/defeat
    cleanup paths, e.g. simply not wanting it around anymore.
    """

    def test_dismiss_releases_an_active_pet(self):
        pet = create.create_object(
            "world.combat.SummonedAlly", key="a familiar", location=self.room1
        )
        self.char1.db.active_companion = pet

        self.call(CmdDismissPet(), "", caller=self.char1)

        self.assertIsNone(self.char1.db.active_companion)
        self.assertFalse(pet.pk)

    def test_dismiss_with_no_active_pet_gives_a_clear_message(self):
        self.char1.db.active_companion = None
        result = self.call(CmdDismissPet(), "", caller=self.char1)
        self.assertIn("don't have an active pet", result)

    def test_banish_is_a_real_alias(self):
        self.assertIn("banish", CmdDismissPet.aliases)

    def test_dismiss_works_even_when_not_in_the_same_room(self):
        """Pets don't auto-follow their owner, so dismiss must work
        purely off db.active_companion, not a room search."""
        other_room = create.create_object("typeclasses.rooms.Room", key="elsewhere")
        pet = create.create_object(
            "world.combat.SummonedAlly", key="a familiar", location=other_room
        )
        self.char1.db.active_companion = pet

        self.call(CmdDismissPet(), "", caller=self.char1)

        self.assertFalse(pet.pk)


class TestCmdChallenge(CombatCommandTestBase):
    def test_no_trainer_here_rejects(self):
        self.room1.db.trainer_prototype = None
        result = self.call(CmdChallenge(), "", caller=self.char1)
        self.assertIn("no one here to challenge", result)

    def test_spawns_personal_opponent_from_prototype(self):
        self.room1.db.trainer_prototype = "RESPAWNING_ARENA_FIGHTER"
        try:
            self.call(CmdChallenge(), "", caller=self.char1)
        except Exception:
            self.skipTest("RESPAWNING_ARENA_FIGHTER prototype not available in this test DB")
        opponent = self.char1.ndb.active_trainer_npc
        self.assertIsNotNone(opponent)
        self.assertEqual(opponent.db.instance_owner, self.char1)

    def test_cannot_challenge_twice_with_pending_opponent(self):
        fake_opponent = create.create_object(
            "typeclasses.characters.Character", key="pending foe", location=self.room1
        )
        fake_opponent.db.hp = 50
        self.char1.ndb.active_trainer_npc = fake_opponent
        self.room1.db.trainer_prototype = "anything"

        result = self.call(CmdChallenge(), "", caller=self.char1)
        self.assertIn("already have an opponent waiting", result)


class TestCmdCastNamedTargeting(CombatCommandTestBase):
    """
    Regression coverage for the real bug found and fixed while writing
    this file - see module docstring. 'cast <heal> = <ally name>' must
    work for an ordinary (non-Builder) caster targeting another real
    Character by their exact, correct name.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.spells_known = ["cure wounds"]
        # EvenniaTest's char1 fixture carries the "Developer" permission
        # by default, which would mask this exact bug (Builders/Devs
        # get a plain-key fallback rpsystem's override doesn't give
        # everyone else) - strip it so this test reflects an ordinary
        # player.
        self.char1.permissions.remove("Developer")

    def test_cast_heal_on_named_ally_by_real_name_succeeds(self):
        self.char2.db.hp = 50
        self.char2.db.max_hp = 100

        with patch("world.combat.randint", return_value=20):
            self.call(CmdCast(), "cure wounds = Char2", caller=self.char1)

        self.assertGreater(self.char2.db.hp, 50)

    def test_cast_heal_with_no_target_heals_self(self):
        self.char1.db.hp = 50
        self.char1.db.max_hp = 100

        with patch("world.combat.randint", return_value=20):
            self.call(CmdCast(), "cure wounds", caller=self.char1)

        self.assertGreater(self.char1.db.hp, 50)

    def test_cast_unknown_spell_rejected(self):
        result = self.call(CmdCast(), "fireball of doom = Char2", caller=self.char1)
        self.assertIn("don't know a spell", result)

    def test_cast_with_target_but_no_equals_sign_hints_at_the_syntax(self):
        # Real player report: "cast mark trainer" (forgetting the "=")
        # fails the spell-name lookup with no clue why, since the whole
        # "mark trainer" string is treated as one spell name.
        result = self.call(CmdCast(), "cure wounds Char2", caller=self.char1)
        self.assertIn("don't know a spell", result)
        self.assertIn("interpose an =", result)

    def test_cast_without_enough_mp_rejected(self):
        self.char1.db.mp = 0
        result = self.call(CmdCast(), "cure wounds = Char2", caller=self.char1)
        self.assertIn("enough MP", result)

    def test_cast_on_nonexistent_target_reports_not_found(self):
        result = self.call(CmdCast(), "cure wounds = Nobody", caller=self.char1)
        self.assertIn("Could not find", result)


class TestCmdUseSkillNamedTargeting(CombatCommandTestBase):
    """Same regression, for CmdUseSkill ('mark' - target: otherchar)."""

    def setUp(self):
        super().setUp()
        self.char1.db.skills_known = ["mark"]
        self.char1.permissions.remove("Developer")

    def test_skill_on_named_enemy_by_real_name_succeeds(self):
        self._start_duel()
        self.char2.db.conditions = {}

        # A hostile target now gets a real (usually small) chance to
        # resist the debuff entirely (see CONDITION_RESIST_BASE) -
        # pinned to a guaranteed-landing roll since resistance isn't
        # what this test is checking.
        with patch("world.combat.randint", return_value=100):
            self.call(CmdUseSkill(), "mark = Char2", caller=self.char1)

        self.assertIn("Accuracy Down", self.char2.db.conditions)

    def test_skill_without_enough_sp_rejected(self):
        self.char1.db.sp = 0
        result = self.call(CmdUseSkill(), "mark = Char2", caller=self.char1)
        self.assertIn("enough SP", result)

    def test_skill_unknown_rejected(self):
        result = self.call(CmdUseSkill(), "made up skill = Char2", caller=self.char1)
        self.assertIn("don't know a skill", result)


class TestCmdCastAndCmdUseSkillStartARealFightOutOfCombat(CombatCommandTestBase):
    """
    Real, confirmed live bug: a player reported "when I used a combat
    action out of combat, it hits an enemy but does not start a
    fight." CmdCast/CmdUseSkill only ever gated their turn/action
    checks behind 'if is_in_combat', skipped entirely when out of
    combat rather than blocking the action - an offensive spell/skill
    landed real, undefended damage with no CombatTurnHandler ever
    created. Fixed via CombatRules.start_combat_from_offensive_action,
    called right before the spellfunc/skillfunc actually runs. See
    world/tests_combat.py's TestStartCombatFromOffensiveAction for
    direct coverage of that helper; this is the end-to-end command
    regression.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.skills_known = ["mark"]
        self.char1.permissions.remove("Developer")

    def test_using_an_offensive_skill_out_of_combat_starts_a_real_fight(self):
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char2))

        self.call(CmdUseSkill(), "mark = Char2", caller=self.char1)

        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char2))
        self.assertNotEqual(self.char1.db.combat_side, self.char2.db.combat_side)

    def test_using_an_offensive_spell_out_of_combat_starts_a_real_fight(self):
        self.char1.db.spells_known = ["ember bolt"] if "ember bolt" in SPELLS else None
        # Fall back to any real offensive (otherchar-target) spell in
        # SPELLS if 'ember bolt' isn't the name actually used - this
        # only needs *a* genuinely offensive spell to exist, not that
        # specific one.
        if not self.char1.db.spells_known:
            offensive_spell = next(
                name for name, data in SPELLS.items()
                if isinstance(data, dict) and data.get("target") == "otherchar"
            )
            self.char1.db.spells_known = [offensive_spell]
        spell_name = self.char1.db.spells_known[0]
        self.char1.db.mp = 999

        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))

        self.call(CmdCast(), "%s = Char2" % spell_name, caller=self.char1)

        self.assertTrue(COMBAT_RULES.is_in_combat(self.char1))
        self.assertTrue(COMBAT_RULES.is_in_combat(self.char2))

    def test_a_non_combat_self_buff_skill_does_not_start_a_fight(self):
        """A no-op for anything that isn't actually offensive - this
        must not turn every skill/spell use into a fight-starter."""
        self.char1.db.skills_known = ["keen eye"] if "keen eye" in SKILLS else self.char1.db.skills_known
        if "keen eye" not in SKILLS:
            self.skipTest("'keen eye' skill not present in this codebase revision")
        self.call(CmdUseSkill(), "keen eye", caller=self.char1)
        self.assertFalse(COMBAT_RULES.is_in_combat(self.char1))


class TestCmdCastAndCmdUseSkillDefaultToTheCurrentOpponent(CombatCommandTestBase):
    """
    Direct player suggestion, implemented as asked: "when we fire an
    offensive skill/spell, it should auto target the enemy we are
    fighting." Previously, with no explicit target, CmdCast/CmdUseSkill
    only auto-targeted when exactly one possible enemy was in the room
    - useless mid-fight against more than one opponent, forcing a name
    every single time even though there's an obvious current target
    (combat_last_target - the same tracker attack/auto-attack/summoned
    pets already use).
    """

    def setUp(self):
        super().setUp()
        self.char1.db.skills_known = ["mark"]
        self.char1.permissions.remove("Developer")

    def test_defaults_to_combat_last_target_when_more_than_one_enemy_present(self):
        third = create.create_object(
            "typeclasses.characters.Character", key="a third fighter", location=self.room1
        )
        third.db.hp = 50
        third.db.max_hp = 50
        third.db.conditions = {}

        self._start_duel()
        self.char1.db.combat_turnhandler.db.fighters.append(third)
        third.db.combat_turnhandler = self.char1.db.combat_turnhandler
        third.db.combat_side = "solo_join_%d" % id(third)
        self.char1.db.combat_last_target = self.char2

        with patch("world.combat.randint", return_value=100):
            self.call(CmdUseSkill(), "mark", caller=self.char1)

        self.assertIn("Accuracy Down", self.char2.db.conditions)
        self.assertNotIn("Accuracy Down", third.db.conditions)

    def test_still_asks_for_a_name_with_no_current_target_and_multiple_enemies(self):
        third = create.create_object(
            "typeclasses.characters.Character", key="a third fighter", location=self.room1
        )
        third.db.hp = 50
        third.db.max_hp = 50
        third.db.conditions = {}

        self._start_duel()
        self.char1.db.combat_turnhandler.db.fighters.append(third)
        third.db.combat_turnhandler = self.char1.db.combat_turnhandler
        third.db.combat_side = "solo_join_%d" % id(third)
        self.char1.db.combat_last_target = None

        result = self.call(CmdUseSkill(), "mark", caller=self.char1)

        self.assertIn("More than one possible target", result)


class TestSkillInfoAndSpellInfoListing(CombatCommandTestBase):
    """
    A real complaint from live playtesting: the old no-argument
    'skillinfo'/'spellinfo' listing repeated "you are Lv Y" on every
    single locked entry - wordy, and the same fact restated over and
    over. Now built through the shared _format_ability_list helper
    (world/combat.py), which shows the caller's level once in the
    header instead. Also covers the new aliases ('skills' for
    skillinfo; 'spell'/'spells' for spellinfo - not 'skill', since
    that key is already CmdUseSkill, a genuinely different command).
    """

    def setUp(self):
        super().setUp()
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 1
        self.char1.db.skills_known = ["hold the line"]
        self.char1.db.spells_known = []

    def test_level_shown_once_in_header_not_per_locked_line(self):
        result = self.call(CmdSkillInfo(), "", caller=self.char1)
        self.assertIn("you are level 1", result)
        # Only the header should mention the caller's own level - not
        # repeated again for every locked entry below it.
        self.assertEqual(result.count("you are level"), 1)

    def test_known_skill_listed_under_known(self):
        result = self.call(CmdSkillInfo(), "", caller=self.char1)
        self.assertIn("Known", result)
        self.assertIn("Hold The Line", result)

    def test_skillinfo_has_skills_alias(self):
        self.assertIn("skills", CmdSkillInfo.aliases)

    def test_spellinfo_has_spell_and_spells_aliases(self):
        self.assertIn("spell", CmdSpellInfo.aliases)
        self.assertIn("spells", CmdSpellInfo.aliases)

    def test_skillinfo_alias_does_not_collide_with_the_real_skill_command(self):
        # 'skill' (singular) must stay CmdUseSkill's own key - skillinfo
        # only ever gets 'skills' (plural) as an alias, never 'skill'.
        self.assertNotIn("skill", CmdSkillInfo.aliases)
        self.assertEqual(CmdUseSkill.key, "skill")

    def test_class_universal_spell_shows_for_a_non_caster_class(self):
        # Conjure Torch deliberately has no "classes" key - available
        # to any class, including a physical class like Legionary.
        # Not a bug: a small non-combat utility spell, by design.
        result = self.call(CmdSpellInfo(), "", caller=self.char1)
        self.assertIn("Conjure Torch", result)

    def test_a_known_but_since_removed_spell_does_not_crash_the_listing(self):
        # Real, confirmed live bug: a character who'd learned "bone
        # ward" before it was cut from the game entirely got a
        # KeyError every time they ran 'spell'/'spellinfo' afterward -
        # the old version looked up every name in spells_known
        # directly in SPELLS with no existence check first. The stale
        # name should just quietly stop being listed, not break the
        # command for everyone who ever learned something later
        # removed from the game.
        self.char1.db.spells_known = ["bone ward"]
        result = self.call(CmdSpellInfo(), "", caller=self.char1)
        self.assertNotIn("Bone Ward", result)

    def test_a_known_but_since_removed_skill_does_not_crash_the_listing(self):
        self.char1.db.skills_known = ["hold the line", "some removed skill"]
        result = self.call(CmdSkillInfo(), "", caller=self.char1)
        self.assertIn("Hold The Line", result)
        self.assertNotIn("Some Removed Skill", result)


class TestStatsHealthBar(CombatCommandTestBase):
    """
    'stats' now shows HP/MP/SP as visual meters (health_bar contrib)
    rather than bare 'HP: X/Y' text - covers the real edge case that
    made this worth double-checking: a pure-melee character with
    max_mp=0 (display_meter guards divide-by-zero internally, but
    worth confirming that actually holds here rather than trusting it).
    """

    def test_stats_shows_hp_mp_sp_meters(self):
        self.char1.db.hp, self.char1.db.max_hp = 50, 100
        self.char1.db.mp, self.char1.db.max_mp = 10, 20
        self.char1.db.sp, self.char1.db.max_sp = 15, 30
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("HP ", result)
        self.assertIn("MP ", result)
        self.assertIn("SP ", result)
        self.assertIn("50 / 100", result)
        self.assertIn("10 / 20", result)
        self.assertIn("15 / 30", result)

    def test_stats_does_not_crash_with_zero_max_mp(self):
        self.char1.db.max_mp = 0
        self.char1.db.mp = 0
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("0 / 0", result)


class TestStatsBoxDisplay(CombatCommandTestBase):
    """
    'stats' rewritten into a bordered box (world.box_display, shared
    with the MOTD's own box) - a direct request to make the output
    "neat and organized... in a box with vivid colors" instead of
    plain indented text. Also covers the other half of that same
    request: Faction and Religion now always show a real line ("None")
    instead of being omitted whenever unset, so a player never has to
    infer "not in one" from an absent line.
    """

    def test_output_is_bordered_top_and_bottom(self):
        # self.call()'s returned text includes RomePromptMixin's own
        # trailing HP/MP/SP prompt line, sent by at_post_cmd() after
        # this command's own output - so the box's closing border
        # isn't necessarily the literal last line of the full result.
        # Checked by counting border lines instead of indexing by
        # position.
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        border_lines = [line for line in result.split("\n") if "+" in line and "=" in line]
        self.assertGreaterEqual(len(border_lines), 2)

    def test_faction_shows_none_when_not_in_one(self):
        self.char1.db.faction = None
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("Faction: None", result)

    def test_religion_shows_none_when_not_in_one(self):
        self.char1.db.religion = None
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("Religion: None", result)

    def test_faction_shows_real_name_when_set(self):
        from world.factions import FACTIONS

        real_faction_key = next(iter(FACTIONS))
        self.char1.db.faction = real_faction_key
        self.char1.db.faction_rank = "member"
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("Faction: %s" % FACTIONS[real_faction_key]["name"], result)
        self.assertNotIn("Faction: None", result)

    def test_core_stats_all_present(self):
        self.char1.db.virtus = 12
        self.char1.db.agilitas = 13
        self.char1.db.ingenium = 14
        self.char1.db.vigor = 15
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("Virtus:    12", result)
        self.assertIn("Agilitas:  13", result)
        self.assertIn("Ingenium:  14", result)
        self.assertIn("Vigor:     15", result)

    def test_ingenium_label_documents_its_max_mp_effect_too(self):
        """
        Ingenium's label used to say only "(spell power)", silently
        omitting that it also raises max MP (max_mp += (ingenium-10)*2
        in derive_npc_stats/chargen) - an inconsistency against Vigor's
        own label, which already spells out both of ITS effects
        ("Max HP, damage reduction"). Fixed to match that convention.
        """
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("spell power, Max MP", result)

    def test_level_line_has_a_colon_like_every_other_label(self):
        """
        Race:/Class:/Faction:/Religion:/XP:/Gold: all use "Label: value"
        - Level was the one holdout written as "Level %d (%s)" with no
        colon, a real inconsistency flagged directly by the user.
        """
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("Level: 1", result)

    def test_race_and_class_shown_as_labeled_lines(self):
        """
        Race/class were already shown before this, just combined into
        one unlabeled "Human, Gladiator" line - relabeled into explicit
        'Race:'/'Class:' lines to match the existing Faction:/Religion:
        convention, per direct request.
        """
        self.char1.db.race_display = "Human"
        self.char1.db.class_display = "Gladiator"
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("Race: Human", result)
        self.assertIn("Class: Gladiator", result)


class TestStatsConditionsDisplay(CombatCommandTestBase):
    """
    Regression coverage for a real, previously-missing feature: there
    was no command anywhere that let a player check what conditions
    currently affect them - the only feedback was a one-time room
    broadcast at the moment a condition was applied or wore off.
    'stats' now shows a color-coded (green=beneficial, red=harmful)
    list, with the section itself only appearing when at least one
    condition is actually active. Deliberately no turn-count shown -
    see CmdCoreStats' own comment for why a displayed number here
    could easily read as a frozen/misleading ETA.
    """

    def test_no_conditions_section_when_nothing_active(self):
        self.char1.db.conditions = {}
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertNotIn("Conditions", result)

    def test_harmful_condition_is_listed(self):
        self.char1.db.conditions = {"Poisoned": [4, self.char2]}
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("Conditions", result)
        self.assertIn("Poisoned", result)

    def test_beneficial_condition_is_listed(self):
        self.char1.db.conditions = {"Regeneration": [3, self.char1]}
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("Regeneration", result)

    def test_no_turn_count_shown_for_a_condition(self):
        self.char1.db.conditions = {"Poisoned": [4, self.char2]}
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertNotIn("4", result.split("Conditions")[1].split("\n")[1])

    def test_harmful_condition_is_colored_red(self):
        from evennia.utils.ansi import parse_ansi

        self.char1.db.conditions = {"Poisoned": [4, self.char2]}
        result = self.call(CmdCoreStats(), "", caller=self.char1, noansi=False)
        # noansi=False returns real escape codes, not raw |r markup -
        # compute the exact same conversion Evennia's own parser would
        # produce, rather than hardcoding a specific escape sequence
        # that could drift with an ANSI-parser version change.
        self.assertIn(parse_ansi("|rPoisoned", strip_ansi=False), result)

    def test_beneficial_condition_is_colored_green(self):
        from evennia.utils.ansi import parse_ansi

        self.char1.db.conditions = {"Regeneration": [3, self.char1]}
        result = self.call(CmdCoreStats(), "", caller=self.char1, noansi=False)
        self.assertIn(parse_ansi("|gRegeneration", strip_ansi=False), result)

    def test_multiple_conditions_all_shown(self):
        self.char1.db.conditions = {
            "Poisoned": [4, self.char2],
            "Regeneration": [3, self.char1],
            "Frightened": [2, self.char2],
        }
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("Poisoned", result)
        self.assertIn("Regeneration", result)
        self.assertIn("Frightened", result)


class TestSpellSkillTrainers(CombatCommandTestBase):
    """
    'learn' (formerly separate learnspell/learnskill commands, now
    merged into one - see 'learnspell'/'learnskill' kept as aliases
    for backward compatibility) requires both gold and being in the
    same room as the right trainer (world.combat.SpellSkillTrainer,
    CmdTrainer). Uses real spells/skills from the actual SPELLS/SKILLS
    dicts rather than fakes, so a formula or gating change elsewhere
    would actually be caught here.
    """

    def test_old_learnspell_and_learnskill_names_still_work_as_aliases(self):
        self.assertIn("learnspell", CmdLearn.aliases)
        self.assertIn("learnskill", CmdLearn.aliases)

    def _make_trainer(self, teaches, location=None):
        from evennia.utils import create
        from world.combat import SpellSkillTrainer

        trainer = create.create_object(
            SpellSkillTrainer, key="Test Trainer (%s)" % teaches, location=location or self.room1
        )
        trainer.db.teaches = teaches
        return trainer

    def test_compute_learn_cost_scales_with_level(self):
        from world.combat import compute_learn_cost

        self.assertEqual(compute_learn_cost(1), 23)
        self.assertEqual(compute_learn_cost(90), 290)
        self.assertLess(compute_learn_cost(1), compute_learn_cost(90))

    def test_learnskill_blocked_without_a_trainer_present(self):
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 50
        self.char1.db.gold = 9999
        result = self.call(CmdLearn(), "hold the line", caller=self.char1)
        self.assertIn("need to find a trainer", result)
        self.assertNotIn("hold the line", self.char1.db.skills_known)

    def test_learnskill_blocked_without_enough_gold(self):
        self._make_trainer("skills")
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 50
        self.char1.db.gold = 0
        result = self.call(CmdLearn(), "hold the line", caller=self.char1)
        self.assertIn("costs", result)
        self.assertNotIn("hold the line", self.char1.db.skills_known)

    def test_learnskill_succeeds_and_deducts_gold(self):
        self._make_trainer("skills")
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 50
        self.char1.db.gold = 100
        self.call(CmdLearn(), "hold the line", caller=self.char1)
        self.assertIn("hold the line", self.char1.db.skills_known)
        # level_required=1 for "hold the line" -> cost 23
        self.assertEqual(self.char1.db.gold, 77)

    def test_learnspell_succeeds_at_the_spell_trainer_not_the_skill_one(self):
        self._make_trainer("skills")  # wrong type present
        self.char1.db.player_class = "medicus"
        self.char1.db.level = 50
        self.char1.db.gold = 100
        result = self.call(CmdLearn(), "cure wounds", caller=self.char1)
        self.assertIn("need to find a trainer", result)

        self._make_trainer("spells")  # now the right type is also here
        self.call(CmdLearn(), "cure wounds", caller=self.char1)
        self.assertIn("cure wounds", self.char1.db.spells_known)

    def test_already_known_short_circuits_before_gold_or_trainer_checks(self):
        # No trainer, no gold - but already known, so neither should matter.
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 50
        self.char1.db.gold = 0
        self.char1.db.skills_known = ["hold the line"]
        result = self.call(CmdLearn(), "hold the line", caller=self.char1)
        self.assertIn("already know", result)

    def test_trainer_command_with_no_trainer_present(self):
        result = self.call(CmdTrainer(), "", caller=self.char1)
        self.assertIn("no trainer here", result)

    def test_train_is_a_working_alias_for_trainer(self):
        self.assertIn("train", CmdTrainer.aliases)

    def test_trainer_command_shows_known_ready_and_locked(self):
        self._make_trainer("skills")
        self.char1.db.player_class = "legionary"
        self.char1.db.level = 5
        self.char1.db.gold = 1000
        self.char1.db.skills_known = ["hold the line"]  # level_required=1

        result = self.call(CmdTrainer(), "", caller=self.char1)

        self.assertIn("Hold The Line", result)
        self.assertIn("Known:", result)
        self.assertIn("Ready to learn", result)
        # A level-90 skill should show up locked for a level-5 character.
        self.assertIn("Not yet available", result)

    def test_wrong_trainer_type_points_to_the_right_one(self):
        """
        Real, confirmed live confusion: a player found A trainer (the
        skill trainer, standing right at Ludus Entrance) but plays a
        caster class, got a bare "has nothing to teach your class",
        and had no idea a second, spell-teaching trainer even existed
        elsewhere - despite a 'help trainers' topic already covering
        this, which they clearly weren't finding either. Fixed to name
        exactly where the right trainer for their class actually is,
        right in this same message.
        """
        self._make_trainer("skills")
        self.char1.db.player_class = "medicus"  # a spell-using class

        result = self.call(CmdTrainer(), "", caller=self.char1)

        self.assertIn("learns spells instead", result)
        self.assertIn("Flamen of the Cella", result)
        self.assertIn("Capitoline Hill", result)

    def test_wrong_trainer_type_the_other_direction(self):
        self._make_trainer("spells")
        self.char1.db.player_class = "legionary"  # a skill-using class

        result = self.call(CmdTrainer(), "", caller=self.char1)

        self.assertIn("learns skills instead", result)
        self.assertIn("Ludus weapons master", result)
        self.assertIn("Ludus Entrance", result)


class TestInCharacterMail(CombatCommandTestBase):
    """
    Light integration coverage for the mail contrib (CmdMailCharacter,
    installed on CharacterCmdSet) - not re-testing the contrib's own
    internals (it ships its own test suite), just confirming it's
    actually wired up correctly and a real send/receive round-trip
    works between two of this game's real Character objects.
    """

    def test_send_and_receive_between_characters(self):
        self.call(
            CmdMailCharacter(),
            "Char2=A test letter/Hail from across the Forum.",
            caller=self.char1,
        )
        result = self.call(CmdMailCharacter(), "", caller=self.char2)
        self.assertIn("A test letter", result)


class TestCustomTitleDisplay(CombatCommandTestBase):
    """
    Regression coverage for a real gap found live: db.custom_title was
    only ever shown on the who tables - there was no way to see your
    own title in full anywhere else, and no way at all to see another
    character's title if who's column width had cropped it. Both
    'stats' and looking at a character now show it.
    """

    def test_stats_shows_the_callers_own_title(self):
        self.char1.db.custom_title = "the Undefeated"
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertIn("the Undefeated", result)

    def test_stats_omits_the_title_line_when_none_is_set(self):
        self.char1.db.custom_title = None
        result = self.call(CmdCoreStats(), "", caller=self.char1)
        self.assertNotIn("None", result.split("\n")[1] if "\n" in result else "")

    def test_looking_at_a_character_shows_their_title(self):
        self.char1.db.custom_title = "the Undefeated"
        self.char1.db.desc = "A tall, scarred fighter."
        appearance = self.char1.return_appearance(self.char2)
        self.assertIn("the Undefeated", appearance)

    def test_looking_at_a_character_with_no_title_is_unaffected(self):
        self.char1.db.custom_title = None
        self.char1.db.desc = "A tall, scarred fighter."
        appearance = self.char1.return_appearance(self.char2)
        self.assertIn("A tall, scarred fighter.", appearance)


class TestEquippedItemsShowSlotLabelsOnLook(CombatCommandTestBase):
    """
    Regression coverage for a real display bug: 'look'/'look self' used
    to dump every worn/wielded item into the same flat, alphabetically
    sorted "You see: a, b, and c" line as ordinary carried items - no
    indication of where anything was actually equipped. get_display_things
    now special-cases equipped items into the same slot-labeled format
    'inventory' already used (see EQUIPPED_SLOTS/format_equipped_lines).
    """

    def setUp(self):
        super().setUp()
        self.weapon = create.create_object(
            "typeclasses.objects.Object", key="a test sword", location=self.char1
        )
        self.weapon.db.two_handed = False
        self.armor = create.create_object(
            "typeclasses.objects.Object", key="a test breastplate", location=self.char1
        )
        self.trinket = create.create_object(
            "typeclasses.objects.Object", key="a plain trinket", location=self.char1
        )
        self.char1.db.wielded_weapon = self.weapon
        self.char1.db.worn_armor = self.armor

    def test_equipped_items_show_with_slot_labels(self):
        appearance = self.char1.return_appearance(self.char1)
        self.assertIn("Wielded (in hand):", appearance)
        self.assertIn("a test sword", appearance)
        self.assertIn("Worn (as armor):", appearance)
        self.assertIn("a test breastplate", appearance)

    def test_two_handed_weapon_says_so(self):
        self.weapon.db.two_handed = True
        appearance = self.char1.return_appearance(self.char1)
        self.assertIn("Wielded (in both hands):", appearance)

    def test_equipped_items_excluded_from_plain_carrying_line(self):
        appearance = self.char1.return_appearance(self.char1)
        self.assertIn("You see:", appearance)
        self.assertIn("a plain trinket", appearance)
        # The sword/breastplate must appear ONLY via their slot-labeled
        # lines above, not also swept into the generic "You see:" line.
        you_see_line = next(line for line in appearance.split("\n") if line.startswith("|wYou see:|n") or "You see:" in line)
        self.assertNotIn("test sword", you_see_line)
        self.assertNotIn("test breastplate", you_see_line)

    def test_no_equipment_falls_back_to_plain_carrying_line_only(self):
        self.char1.db.wielded_weapon = None
        self.char1.db.worn_armor = None
        appearance = self.char1.return_appearance(self.char1)
        self.assertNotIn("Wielded", appearance)
        self.assertNotIn("Worn", appearance)
        self.assertIn("a plain trinket", appearance)


class TestEquippedItemsHaveABlankLineFromDescription(CombatCommandTestBase):
    """
    Regression coverage for a direct complaint from live playtesting:
    a character's own description ran straight into their Wielded/Worn
    listing with no visual separation - "it all just clutters
    together." The fix needed a real, non-obvious workaround: the base
    DefaultObject.format_appearance() always calls
    compress_whitespace(appearance) with its default max_linebreaks=1,
    which unconditionally collapses ANY run of blank lines back down
    to a single line break - so a bare blank line inserted in
    get_display_things() would have been silently erased right back
    out. CombatCharacter.format_appearance() now raises that to 2,
    scoped to Characters only (rooms/objects keep the default), and
    get_display_things() emits a leading blank line to actually use
    the extra room this allows.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.desc = "A tall, scarred fighter stands here."
        self.weapon = create.create_object(
            "typeclasses.objects.Object", key="a test sword", location=self.char1
        )
        self.char1.db.wielded_weapon = self.weapon

    def test_real_blank_line_separates_desc_from_equipment(self):
        appearance = self.char1.return_appearance(self.char1)
        self.assertIn(
            "A tall, scarred fighter stands here.\n\n|wWielded (in hand):|n",
            appearance,
        )

    def test_no_equipment_or_carried_items_has_no_trailing_blank_line(self):
        self.char1.db.wielded_weapon = None
        self.weapon.delete()  # nothing left to show at all, equipped or loose
        appearance = self.char1.return_appearance(self.char1)
        self.assertFalse(appearance.endswith("\n"))
        self.assertNotIn("\n\n", appearance)

    def test_room_descriptions_are_unaffected(self):
        # The relaxed max_linebreaks is scoped to CombatCharacter only -
        # a plain Room must keep the normal single-blank-line collapse.
        self.room1.db.desc = "A room.\n\n\n\nWith extra blank lines."
        appearance = self.room1.return_appearance(self.char1)
        self.assertNotIn("\n\n\n", appearance)


class TestCooldowns(CombatCommandTestBase):
    """
    First-pass fix for the long-flagged gap in rome_mud_todo.md: "zero
    cooldowns exist anywhere in world/combat.py" - a level-tiered
    default (cooldown_for_level) applied automatically via CmdCast and
    CmdUseSkill, so a powerful ability can't be spammed every turn the
    instant its MP/SP cost is affordable again.
    """

    def setUp(self):
        super().setUp()
        self.char1.permissions.remove("Developer")
        self.char1.db.mp = 20
        self.char1.db.max_mp = 20
        self.char1.db.sp = 20
        self.char1.db.max_sp = 20

    def test_low_level_spell_gets_no_cooldown(self):
        self.char1.db.spells_known = ["cure wounds"]  # level_required 1
        with patch("world.combat.randint", return_value=20):
            self.call(CmdCast(), "cure wounds", caller=self.char1)
        self.assertNotIn("cure wounds", self.char1.db.cooldowns)

    def test_casting_a_tier_20_spell_sets_a_cooldown(self):
        self.char1.db.spells_known = ["vigor"]  # level_required 25 -> cooldown 2
        self.call(CmdCast(), "vigor", caller=self.char1)
        self.assertEqual(self.char1.db.cooldowns.get("vigor"), 2)

    def test_recasting_before_cooldown_expires_is_refused(self):
        self.char1.db.spells_known = ["vigor"]
        self.call(CmdCast(), "vigor", caller=self.char1)
        self.char1.db.mp = 20  # refill so MP itself isn't the blocker
        result = self.call(CmdCast(), "vigor", caller=self.char1)
        self.assertIn("recovering", result)

    def test_cooldown_ticks_down_and_clears(self):
        self.char1.db.spells_known = ["vigor"]
        self.call(CmdCast(), "vigor", caller=self.char1)
        self.assertEqual(self.char1.db.cooldowns.get("vigor"), 2)
        COMBAT_RULES.tick_cooldowns(self.char1)
        self.assertEqual(self.char1.db.cooldowns.get("vigor"), 1)
        COMBAT_RULES.tick_cooldowns(self.char1)
        self.assertNotIn("vigor", self.char1.db.cooldowns)

    def test_skill_cooldown_enforced_the_same_way(self):
        self.char1.db.skills_known = ["shield wall"]  # level_required 25
        self.call(CmdUseSkill(), "shield wall", caller=self.char1)
        self.assertEqual(self.char1.db.cooldowns.get("shield wall"), 2)

        self.char1.db.sp = 20
        result = self.call(CmdUseSkill(), "shield wall", caller=self.char1)
        self.assertIn("recovering", result)


class TestCmdRestBlockedWhileDead(CombatCommandTestBase):
    """
    A dead character's HP/MP/SP are deliberately pinned at 0 the whole
    time they're dead (see handle_player_defeat) - resting must not be
    able to creep them back up before an actual resurrection, or "stats
    stay at 0 until you make it back" stops being true.
    """

    def test_rest_refused_while_dead(self):
        self.char1.db.is_dead = True
        self.char1.db.hp = 0
        self.char1.db.mp = 0
        self.char1.db.sp = 0

        result = self.call(CmdRest(), "", caller=self.char1)

        self.assertIn("only returning to life", result)
        self.assertFalse(self.char1.db.resting)

    def test_rest_works_normally_once_alive(self):
        self.char1.db.is_dead = False
        self.char1.db.hp = 50
        result = self.call(CmdRest(), "", caller=self.char1)
        self.assertIn("settles in to rest", result)
        self.assertTrue(self.char1.db.resting)


class TestCmdRestoreClearsConditionsAndRevivesTheDead(CombatCommandTestBase):
    """
    CmdRestore extended in direct response to two real, confirmed live
    bugs found this same session (conditions surviving death, and a
    hostile condition that could never expire) - a real "something's
    gone wrong with this character's state" escape hatch for staff,
    on top of the HP/MP/SP-only restore it already did.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.level = 102  # the acting god

    def test_restore_on_a_living_target_clears_conditions(self):
        self.char2.db.hp = 10
        self.char2.db.max_hp = 100
        self.char2.db.conditions = {"Poisoned": [4, self.char1]}

        self.call(CmdRestore(), "Char2", caller=self.char1)

        self.assertEqual(self.char2.db.hp, self.char2.db.max_hp)
        self.assertEqual(self.char2.db.conditions, {})

    def test_restore_on_a_dead_target_resurrects_them(self):
        from evennia.objects.models import ObjectDB
        from django.conf import settings

        cells = ObjectDB.objects.get_id(settings.START_LOCATION)
        if not cells:
            self.skipTest("START_LOCATION not resolvable in this test DB")

        self.char2.db.is_dead = True
        self.char2.db.level = 3
        self.char2.db.hp = 0
        self.char2.db.conditions = {"Poisoned": [4, self.char1]}

        self.call(CmdRestore(), "Char2", caller=self.char1)

        self.assertFalse(self.char2.db.is_dead)
        self.assertEqual(self.char2.db.hp, self.char2.db.max_hp)
        self.assertEqual(self.char2.db.conditions, {})
        self.assertEqual(self.char2.location, cells)

    def test_below_level_102_is_refused(self):
        self.char1.db.level = 101
        result = self.call(CmdRestore(), "Char2", caller=self.char1)
        self.assertIn("lack the standing", result)


class TestGodLevelGrantsResourceGrowth(CombatCommandTestBase):
    """
    CmdGodLevel ('godlevel'/'advance') - real, confirmed live bug
    reported directly by a player after being leveled up this way:
    "I think when you advanced my levels that way, it doesn't give hp,
    mp or sp." Setting db.level directly used to completely bypass
    award_xp's level-up loop, so a target advanced 10 levels this way
    kept their old max_hp/mp/sp and never got the stat point every 3rd
    level normally grants. Fixed to apply the exact same per-level
    growth award_xp uses, for every level actually crossed.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.level = 104  # the acting god
        self.char2.db.level = 1
        self.char2.db.max_hp, self.char2.db.hp = 100, 100
        self.char2.db.max_mp, self.char2.db.mp = 20, 20
        self.char2.db.max_sp, self.char2.db.sp = 30, 30
        self.char2.db.unspent_stat_points = 0

    def test_advancing_ten_levels_grants_the_full_resource_gain(self):
        self.call(CmdGodLevel(), "Char2 = 10", caller=self.char1)

        self.assertEqual(self.char2.db.max_hp, 100 + LEVEL_UP_HP_GAIN * 9)
        self.assertEqual(self.char2.db.max_mp, 20 + LEVEL_UP_MP_GAIN * 9)
        self.assertEqual(self.char2.db.max_sp, 30 + LEVEL_UP_SP_GAIN * 9)
        # Topped up to the new max, same as a real level-up would.
        self.assertEqual(self.char2.db.hp, self.char2.db.max_hp)
        self.assertEqual(self.char2.db.mp, self.char2.db.max_mp)
        self.assertEqual(self.char2.db.sp, self.char2.db.max_sp)

    def test_advancing_grants_one_stat_point_per_third_level_crossed(self):
        # 1 -> 10 crosses levels 3, 6, 9 - three stat points.
        self.call(CmdGodLevel(), "Char2 = 10", caller=self.char1)
        self.assertEqual(self.char2.db.unspent_stat_points, 3)

    def test_demoting_reduces_max_resources_without_going_negative(self):
        self.char2.db.level = 10
        self.char2.db.max_hp = 100 + LEVEL_UP_HP_GAIN * 9
        self.char2.db.hp = self.char2.db.max_hp

        self.call(CmdGodLevel(), "Char2 = 1", caller=self.char1)

        self.assertEqual(self.char2.db.max_hp, 100)
        self.assertLessEqual(self.char2.db.hp, self.char2.db.max_hp)

    def test_growth_stacks_on_top_of_stat_points_already_spent_on_resources(self):
        """A previous 'statup hp' boost must survive a later godlevel
        change untouched - this is delta-based, not a reset."""
        self.char2.db.max_hp = 110  # 100 base + a 'statup hp' +10 already spent
        self.char2.db.hp = 110

        self.call(CmdGodLevel(), "Char2 = 2", caller=self.char1)

        self.assertEqual(self.char2.db.max_hp, 110 + LEVEL_UP_HP_GAIN)

    def test_god_tier_levels_beyond_max_level_grant_no_extra_growth(self):
        self.char2.db.level = MAX_LEVEL
        self.char2.db.max_hp = 100 + LEVEL_UP_HP_GAIN * (MAX_LEVEL - 1)
        self.char2.db.hp = self.char2.db.max_hp

        self.call(CmdGodLevel(), "Char2 = 102", caller=self.char1)

        # No further hp growth from 100 -> 102 - only the 1-100 mortal
        # range gets XP-style growth; a god's level isn't earned.
        self.assertEqual(self.char2.db.max_hp, 100 + LEVEL_UP_HP_GAIN * (MAX_LEVEL - 1))


class TestGodLevelConnectsToDivineChannel(CombatCommandTestBase):
    """
    CmdGodLevel's crossing-into-godhood branch already auto-joins every
    faction/religion channel (connect_god_to_all_faction_channels/
    connect_god_to_all_religion_channels) - the new 'divine' channel
    (world/religion.py) gets the exact same treatment, added alongside
    those two calls, so a freshly-promoted god doesn't have to wait for
    a server restart to hear a prayer.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.level = 106  # the acting god
        self.char2.db.level = 1

    def test_promotion_past_100_joins_the_divine_channel(self):
        from world.religion import ensure_divine_channel_exists, get_divine_channel

        ensure_divine_channel_exists()
        self.call(CmdGodLevel(), "Char2 = 101", caller=self.char1)
        channel = get_divine_channel()
        self.assertIn(self.char2, channel.subscriptions.all())


class TestGodLevelGrantsEveryAbilityOnPromotion(CombatCommandTestBase):
    """
    Direct request: a god (current or future) should be able to test
    anything without the same trainer/gold/level grind a mortal player
    goes through - crossing into godhood now grants every spell,
    skill, and language in the game, same choke point as the existing
    faction/religion/divine-channel auto-join just above.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.level = 106  # the acting god
        self.char2.db.level = 1
        self.char2.db.spells_known = []
        self.char2.db.skills_known = []
        self.char2.db.known_languages = ["latin"]

    def test_promotion_grants_every_spell(self):
        self.call(CmdGodLevel(), "Char2 = 101", caller=self.char1)
        real_spells = [name for name, data in SPELLS.items() if isinstance(data, dict)]
        for name in real_spells:
            self.assertIn(name, self.char2.db.spells_known)

    def test_promotion_grants_every_skill(self):
        self.call(CmdGodLevel(), "Char2 = 101", caller=self.char1)
        real_skills = [name for name, data in SKILLS.items() if isinstance(data, dict)]
        for name in real_skills:
            self.assertIn(name, self.char2.db.skills_known)

    def test_promotion_grants_every_language(self):
        self.call(CmdGodLevel(), "Char2 = 101", caller=self.char1)
        for language in ("latin", "greek", "celtic", "egyptian", "germanic"):
            self.assertIn(language, self.char2.db.known_languages)

    def test_a_mortal_promotion_grants_nothing_extra(self):
        """The grant only fires on the actual 1-100 -> 101+ crossing,
        not on an ordinary mortal-range level change."""
        self.call(CmdGodLevel(), "Char2 = 50", caller=self.char1)
        self.assertEqual(self.char2.db.spells_known, [])
        self.assertEqual(self.char2.db.skills_known, [])

    def test_demotion_back_to_mortal_does_not_strip_anything(self):
        """Deliberately one-way - a demoted former god keeping spells
        they 'shouldn't' have is a far safer failure than silently
        deleting a real mortal's own legitimately-learned kit."""
        self.call(CmdGodLevel(), "Char2 = 101", caller=self.char1)
        known_count = len(self.char2.db.spells_known)
        self.assertGreater(known_count, 0)

        self.call(CmdGodLevel(), "Char2 = 50", caller=self.char1)

        self.assertEqual(len(self.char2.db.spells_known), known_count)


class TestCmdGodSet(CombatCommandTestBase):
    """
    'godset' - a direct testing-tool request: set a character's HP/MP/
    SP or core stats directly, without going through combat/statup.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.level = 102  # the acting god
        self.char2.db.hp, self.char2.db.max_hp = 50, 100
        self.char2.db.mp, self.char2.db.max_mp = 10, 20
        self.char2.db.virtus = 10

    def test_refuses_below_god_level(self):
        self.char1.db.level = 100
        result = self.call(CmdGodSet(), "Char2 = hp 500", caller=self.char1)
        self.assertIn("lack the standing", result)

    def test_sets_hp_within_the_current_max(self):
        self.call(CmdGodSet(), "Char2 = hp 75", caller=self.char1)
        self.assertEqual(self.char2.db.hp, 75)
        self.assertEqual(self.char2.db.max_hp, 100)

    def test_setting_hp_above_max_raises_the_max_to_match(self):
        self.call(CmdGodSet(), "Char2 = hp 9999", caller=self.char1)
        self.assertEqual(self.char2.db.hp, 9999)
        self.assertEqual(self.char2.db.max_hp, 9999)

    def test_sets_a_core_stat(self):
        self.call(CmdGodSet(), "Char2 = virtus 30", caller=self.char1)
        self.assertEqual(self.char2.db.virtus, 30)

    def test_rejects_an_unknown_stat(self):
        result = self.call(CmdGodSet(), "Char2 = wisdom 10", caller=self.char1)
        self.assertIn("Unknown stat", result)

    def test_rejects_a_non_numeric_value(self):
        result = self.call(CmdGodSet(), "Char2 = hp banana", caller=self.char1)
        self.assertIn("whole number", result)

    def test_rejects_a_negative_value(self):
        result = self.call(CmdGodSet(), "Char2 = hp -5", caller=self.char1)
        self.assertIn("negative", result)


class TestCmdCompare(CombatCommandTestBase):
    """
    'compare' - a direct player request for a way to tell which of two
    weapons or armor pieces is actually better without doing the math
    by hand. By explicit request: never shows raw numbers in the
    verdict, only qualitative language ("much better", "more
    accurate"), but does flag when an item sits outside the caller's
    class proficiency, since that makes its real performance worse
    than its own numbers alone would suggest.
    """

    def _weapon(self, key, min_dmg, max_dmg, accuracy_bonus, category="light_blade"):
        weapon = create.create_object(
            "world.combat.CombatWeapon", key=key, location=self.char1
        )
        weapon.db.damage_range = (min_dmg, max_dmg)
        weapon.db.accuracy_bonus = accuracy_bonus
        weapon.db.weapon_category = category
        return weapon

    def _armor(self, key, damage_reduction, defense_modifier, armor_slot="body"):
        armor = create.create_object(
            "world.combat.CombatArmor", key=key, location=self.char1
        )
        armor.db.damage_reduction = damage_reduction
        armor.db.defense_modifier = defense_modifier
        armor.db.armor_slot = armor_slot
        return armor

    def test_strictly_better_weapon_gets_a_clean_verdict_with_no_numbers(self):
        self._weapon("a rusty dagger", 5, 10, 5)
        self._weapon("a fine gladius", 61, 71, 15)

        result = self.call(CmdCompare(), "rusty dagger = fine gladius", caller=self.char1)
        verdict = result.split("\n")[0]  # the prompt line appended after includes HP/MP/SP numbers

        self.assertIn("much better", verdict)
        self.assertIn("hits harder", verdict)
        self.assertIn("more accurate", verdict)
        # Never raw numbers in the verdict - only qualitative language,
        # by explicit request.
        self.assertFalse(any(char.isdigit() for char in verdict))

    def test_weapon_tradeoff_names_both_sides_honestly(self):
        self._weapon("a swift dagger", 10, 15, 20)
        self._weapon("a heavy waraxe", 30, 40, 5)

        result = self.call(CmdCompare(), "swift dagger = heavy waraxe", caller=self.char1)

        self.assertIn("hits harder", result)
        self.assertIn("more accurate", result)
        self.assertIn("Depends what you're looking for", result)

    def test_two_identical_weapons_are_about_the_same(self):
        self._weapon("a plain gladius", 20, 30, 10)
        self._weapon("a spare gladius", 20, 30, 10)

        result = self.call(CmdCompare(), "plain gladius = spare gladius", caller=self.char1)
        self.assertIn("about the same", result)

    def test_body_armor_compares_on_damage_reduction_alone(self):
        """
        Real design correction caught while testing this: an earlier
        draft compared armor the same two-axis way as weapons
        (damage_reduction AND defense_modifier), but
        compute_armor_stats always derives defense_modifier as the
        exact negative of damage_reduction for body armor - so every
        single body-armor comparison came back as a "tradeoff" even
        though it's a fixed relationship every piece already has, not
        a real choice. Comparing on damage_reduction alone is what
        actually answers "which one protects me better".
        """
        self._armor("a leather vest", 2, -2)
        self._armor("a plate cuirass", 8, -8)

        result = self.call(CmdCompare(), "leather vest = plate cuirass", caller=self.char1)
        self.assertIn("much better", result)
        self.assertIn("reduces more incoming damage", result)
        self.assertNotIn("Depends", result)

    def test_shields_compare_on_defense_modifier_not_damage_reduction(self):
        self._armor("a small parma", 0, 4, armor_slot="shield")
        self._armor("a large scutum", 0, 12, armor_slot="shield")

        result = self.call(CmdCompare(), "small parma = large scutum", caller=self.char1)
        self.assertIn("better", result)
        self.assertIn("makes you harder to hit", result)

    def test_cannot_compare_weapon_to_armor(self):
        self._weapon("a gladius", 20, 30, 10)
        self._armor("a leather vest", 2, -2)

        result = self.call(CmdCompare(), "gladius = leather vest", caller=self.char1)
        self.assertIn("can't compare a weapon to a piece of armor", result)

    def test_cannot_compare_different_armor_slots(self):
        self._armor("a leather vest", 2, -2, armor_slot="body")
        self._armor("a bronze shield", 0, 10, armor_slot="shield")

        result = self.call(CmdCompare(), "leather vest = bronze shield", caller=self.char1)
        self.assertIn("different slots", result)

    def test_comparing_an_item_to_itself_is_rejected(self):
        self._weapon("a gladius", 20, 30, 10)
        result = self.call(CmdCompare(), "gladius = gladius", caller=self.char1)
        self.assertIn("same item", result)

    def test_flags_a_weapon_outside_class_proficiency(self):
        self.char1.db.player_class = "legionary"  # not proficient with heavy_weapon
        self._weapon("a gladius", 20, 30, 10, category="light_blade")
        self._weapon("a waraxe", 25, 35, 5, category="heavy_weapon")

        result = self.call(CmdCompare(), "gladius = waraxe", caller=self.char1)
        self.assertIn("waraxe is outside your class's usual weapons", result)

    def test_no_proficiency_note_when_both_are_proficient(self):
        self.char1.db.player_class = "legionary"
        self._weapon("a gladius", 20, 30, 10, category="light_blade")
        self._weapon("a spear", 22, 32, 8, category="polearm")

        result = self.call(CmdCompare(), "gladius = spear", caller=self.char1)
        self.assertNotIn("Note:", result)


class TestCmdInspect(CombatCommandTestBase):
    """
    'inspect' - direct player request for a way to tell what category
    or weight tier an item actually is, and whether it's safe to use
    without a penalty. Reuses compare's own CombatWeapon/CombatArmor
    helper pattern.
    """

    def _weapon(self, key, category="light_blade", two_handed=False):
        weapon = create.create_object(
            "world.combat.CombatWeapon", key=key, location=self.char1
        )
        weapon.db.weapon_category = category
        weapon.db.two_handed = two_handed
        return weapon

    def _armor(self, key, category="light", armor_slot="body"):
        armor = create.create_object(
            "world.combat.CombatArmor", key=key, location=self.char1
        )
        armor.db.armor_category = category
        armor.db.armor_slot = armor_slot
        return armor

    def test_shows_weapon_category(self):
        self._weapon("a waraxe", category="heavy_weapon")
        result = self.call(CmdInspect(), "waraxe", caller=self.char1)
        self.assertIn("a Heavy Weapon-type weapon", result)

    def test_shows_two_handed_note(self):
        self._weapon("a waraxe", category="heavy_weapon", two_handed=True)
        result = self.call(CmdInspect(), "waraxe", caller=self.char1)
        self.assertIn("requires both hands", result)

    def test_shows_armor_weight_tier(self):
        self._armor("a scutum", category="medium", armor_slot="shield")
        result = self.call(CmdInspect(), "scutum", caller=self.char1)
        self.assertIn("Medium-weight shield", result)

    def test_proficient_class_gets_a_yes(self):
        self.char1.db.player_class = "barbarian"
        self._weapon("a waraxe", category="heavy_weapon")
        result = self.call(CmdInspect(), "waraxe", caller=self.char1)
        self.assertIn("proficient with this", result)
        self.assertNotIn("NOT proficient", result)

    def test_non_proficient_class_gets_a_no_and_a_pointer(self):
        self.char1.db.player_class = "augur"
        self._weapon("a waraxe", category="heavy_weapon")
        result = self.call(CmdInspect(), "waraxe", caller=self.char1)
        self.assertIn("NOT proficient", result)
        self.assertIn("help armor", result)

    def test_classless_caller_gets_no_verdict_line_at_all(self):
        self.char1.db.player_class = None
        self._weapon("a waraxe", category="heavy_weapon")
        result = self.call(CmdInspect(), "waraxe", caller=self.char1)
        self.assertNotIn("proficient", result)

    def test_refuses_a_non_equipment_item(self):
        from evennia.utils import create as ev_create

        prop = ev_create.create_object(
            "typeclasses.objects.Object", key="a wooden bucket", location=self.char1
        )
        result = self.call(CmdInspect(), "bucket", caller=self.char1)
        self.assertIn("isn't a weapon or a piece of armor", result)

    def test_no_argument_shows_usage(self):
        result = self.call(CmdInspect(), "", caller=self.char1)
        self.assertIn("Usage:", result)


class TestMovementSPCost(CombatCommandTestBase):
    """
    at_pre_move's movement-SP gate (world/combat.py) - MOVEMENT_SP_COST
    per ordinary player move, blocked outright if there isn't enough
    SP left, with gods/dead characters/non-"move" move_types (NPC
    wander, teleports) exempt. Called directly against at_pre_move
    rather than through a real Exit object - the hook only needs a
    destination and a move_type, so no exit wiring is needed to
    exercise it.

    IMPORTANT caveat this file's own isolated approach missed for a
    long time: passing move_type="move" by hand here does NOT prove a
    real Exit traversal ever actually reaches this gate with that same
    value. It didn't - Evennia's own DefaultExit.at_traverse calls
    move_to(..., move_type="traverse"), so this whole gate was
    silently exempting every real player move in the live game the
    entire time, undetected by every test below. Fixed in
    typeclasses/exits.py's Exit.at_traverse (now passes the correct
    move_type="move"); see world/tests_exits.py's
    TestRealExitTraversalChargesMovementSP for the real, end-to-end
    regression coverage this file's own isolated tests can't provide.
    """

    def test_ordinary_move_deducts_the_cost(self):
        self.char1.db.sp = 10
        allowed = self.char1.at_pre_move(self.room2, move_type="move")
        self.assertTrue(allowed)
        self.assertEqual(self.char1.db.sp, 10 - MOVEMENT_SP_COST)

    def test_move_blocked_when_sp_below_cost(self):
        self.char1.db.sp = 0
        allowed = self.char1.at_pre_move(self.room2, move_type="move")
        self.assertFalse(allowed)
        self.assertEqual(self.char1.db.sp, 0)

    def test_god_tier_exempt_from_cost(self):
        self.char1.db.level = 101
        self.char1.db.sp = 0
        allowed = self.char1.at_pre_move(self.room2, move_type="move")
        self.assertTrue(allowed)
        self.assertEqual(self.char1.db.sp, 0)

    def test_dead_character_exempt_from_cost(self):
        self.char1.db.is_dead = True
        self.char1.db.sp = 0
        allowed = self.char1.at_pre_move(self.room2, move_type="move")
        self.assertTrue(allowed)
        self.assertEqual(self.char1.db.sp, 0)

    def test_non_move_move_types_are_exempt(self):
        """NPC wandering ("wander") and teleports ("teleport") never pay this cost."""
        self.char1.db.sp = 0
        self.assertTrue(self.char1.at_pre_move(self.room2, move_type="wander"))
        self.assertTrue(self.char1.at_pre_move(self.room2, move_type="teleport"))
        self.assertEqual(self.char1.db.sp, 0)

    def test_accountless_object_exempt_as_npc_safety_net(self):
        npc = create.create_object(
            "typeclasses.characters.Character", key="a test npc", location=self.room1
        )
        npc.db.sp = 0
        npc.db.is_dead = False
        npc.db.level = 1
        self.assertIsNone(npc.account)
        allowed = npc.at_pre_move(self.room2, move_type="move")
        self.assertTrue(allowed)

    def test_low_sp_warning_fires_once_then_resets_above_threshold(self):
        self.char1.db.max_sp = 10
        self.char1.db.sp = MOVEMENT_SP_COST + int(10 * MOVEMENT_SP_WARN_THRESHOLD)
        self.char1.db.sp_low_warned = False

        # This move should land exactly at/below the warn threshold.
        self.char1.at_pre_move(self.room2, move_type="move")
        self.assertTrue(self.char1.db.sp_low_warned)

        # Restoring SP well above the threshold should clear the flag
        # so a future dip can warn again.
        self.char1.db.sp = 10
        self.char1.at_pre_move(self.room2, move_type="move")
        self.assertFalse(self.char1.db.sp_low_warned)


class TestCmdWieldFailureMessage(CombatCommandTestBase):
    """
    Regression coverage for a real, confirmed player-confusion bug:
    a real player spent 13+ minutes across two sessions trying to
    'wield greatsword' (a weapon belonging to a DIFFERENT class than
    the one they'd picked - Barbarian's starting gear, not their own
    Gladiator's) before giving up and deleting their character. The
    search itself was never broken - Evennia's default partial
    matching already resolves 'greatsword' against a real object
    named 'a rune-etched greatsword' correctly (confirmed directly
    against a live object) - the actual problem was the failure
    message: a bare "Could not find 'X'." gives no way to tell "you
    misspelled it" apart from "you never had this at all," leaving a
    confused player to guess blindly. wield now reports what the
    caller is actually carrying instead.
    """

    def test_failed_search_lists_carried_weapons(self):
        create.create_object(
            "world.combat.CombatWeapon", key="an iron broadsword", location=self.char1
        )
        result = self.call(CmdWield(), "greatsword", caller=self.char1)
        self.assertIn("You aren't carrying anything called 'greatsword'", result)
        self.assertIn("an iron broadsword", result)

    def test_failed_search_with_nothing_carried_says_so(self):
        result = self.call(CmdWield(), "greatsword", caller=self.char1)
        self.assertIn("You aren't carrying anything you could wield or wear", result)

    def test_failed_search_lists_multiple_carried_weapons(self):
        create.create_object(
            "world.combat.CombatWeapon", key="an iron broadsword", location=self.char1
        )
        create.create_object(
            "world.combat.CombatWeapon", key="a bronze dagger", location=self.char1
        )
        result = self.call(CmdWield(), "greatsword", caller=self.char1)
        self.assertIn("an iron broadsword", result)
        self.assertIn("a bronze dagger", result)

    def test_successful_partial_match_still_wields(self):
        # The search itself was never the problem - confirm a real
        # partial match (a substring of a multi-word key) still works
        # exactly as before this change.
        create.create_object(
            "world.combat.CombatWeapon", key="a rune-etched greatsword", location=self.char1
        )
        self.call(CmdWield(), "greatsword", caller=self.char1)
        self.assertIsNotNone(self.char1.db.wielded_weapon)
        self.assertEqual(self.char1.db.wielded_weapon.key, "a rune-etched greatsword")

    def test_truly_non_equippable_match_reports_correctly(self):
        create.create_object(
            "evennia.objects.objects.DefaultObject", key="a rock", location=self.char1
        )
        result = self.call(CmdWield(), "rock", caller=self.char1)
        self.assertIn("That's not something you can wield or wear!", result)


class TestWieldAndUnwieldWorkForAnOrdinaryNonBuilderPlayer(CombatCommandTestBase):
    """
    Real, confirmed live bug reported directly by a player: "Unable to
    target a weapon to wield or unwield." Root cause - the exact same
    rpsystem sdesc-search gap already documented for find_combat_target
    elsewhere in this file, but for equipment instead of characters:
    ContribRPCharacter.get_search_result() tries to match every
    candidate by SDESC first when an explicit candidates list is
    passed, and a plain CombatWeapon/CombatArmor object has no sdesc
    at all - so caller.search(args, candidates=...) found nothing for
    an ordinary player, every single time. Only ever masked during
    development because EvenniaTest's char1 fixture carries the
    Developer permission by default, and rpsystem's own override
    specifically grants BUILDERS a plain-key fallback it never gives
    real players - every test above this one in the file (all still
    using the default Developer-permission caller) would have kept
    passing even with the bug very much still live.
    """

    def setUp(self):
        super().setUp()
        self.char1.permissions.remove("Developer")

    def test_ordinary_player_can_wield_a_weapon_by_exact_name(self):
        create.create_object(
            "world.combat.CombatWeapon", key="a bronze dagger", location=self.char1
        )
        self.call(CmdWield(), "a bronze dagger", caller=self.char1)
        self.assertIsNotNone(self.char1.db.wielded_weapon)
        self.assertEqual(self.char1.db.wielded_weapon.key, "a bronze dagger")

    def test_ordinary_player_can_wield_a_weapon_by_partial_name(self):
        create.create_object(
            "world.combat.CombatWeapon", key="a rune-etched greatsword", location=self.char1
        )
        self.call(CmdWield(), "greatsword", caller=self.char1)
        self.assertIsNotNone(self.char1.db.wielded_weapon)

    def test_ordinary_player_can_wield_by_the_trailing_word_of_a_possessive_name(self):
        """
        Real, confirmed live follow-up bug: "a duelist's stiletto"
        could be found by 'wield a duelist' (a real prefix of the
        whole key) but NOT by 'wield stiletto' - the one word a player
        would most naturally reach for, since it's the actual item
        type. The fallback used to only check whether the search text
        prefixed the KEY AS A WHOLE, never an individual word within
        it. Reported directly: "'wield a duelist' works" right below
        "You aren't carrying anything called 'stiletto'."
        """
        create.create_object(
            "world.combat.CombatWeapon", key="a duelist's stiletto", location=self.char1
        )
        self.call(CmdWield(), "stiletto", caller=self.char1)
        self.assertIsNotNone(self.char1.db.wielded_weapon)
        self.assertEqual(self.char1.db.wielded_weapon.key, "a duelist's stiletto")

    def test_ordinary_player_can_unwield_by_exact_name(self):
        weapon = create.create_object(
            "world.combat.CombatWeapon", key="a bronze dagger", location=self.char1
        )
        self.char1.db.wielded_weapon = weapon
        self.call(CmdUnwield(), "a bronze dagger", caller=self.char1)
        self.assertIsNone(self.char1.db.wielded_weapon)

    def test_ordinary_player_can_don_armor_by_exact_name(self):
        armor = create.create_object(
            "world.combat.CombatArmor", key="a leather vest", location=self.char1
        )
        armor.db.armor_slot = "body"
        self.call(CmdDon(), "a leather vest", caller=self.char1)
        self.assertEqual(self.char1.db.worn_armor, armor)


class TestWieldAndDonAreCrossCompatible(CombatCommandTestBase):
    """
    Direct follow-up request: since wield/don/unwield/doff were kept
    as four separate commands (for genre-appropriate flavor and to
    avoid two commands claiming the same alias), rather than merged
    into one, the underlying mechanics needed to actually be unified
    instead - otherwise 'wield <armor>' and 'don <weapon>' would still
    hit the exact "wrong verb for what you're holding" trap a real
    player already fell into once.
    """

    def _add_weapon(self, key="an iron broadsword"):
        return create.create_object("world.combat.CombatWeapon", key=key, location=self.char1)

    def _add_armor(self, key="a bronze-faced clipeus", slot="shield"):
        armor = create.create_object(
            "world.combat.CombatArmor", key=key, location=self.char1
        )
        armor.db.armor_slot = slot
        return armor

    def test_wield_can_don_armor(self):
        armor = self._add_armor(slot="head")
        self.call(CmdWield(), armor.key, caller=self.char1)
        self.assertEqual(self.char1.db.worn_head, armor)

    def test_don_can_wield_a_weapon(self):
        weapon = self._add_weapon()
        self.call(CmdDon(), weapon.key, caller=self.char1)
        self.assertEqual(self.char1.db.wielded_weapon, weapon)

    def test_unwield_can_remove_armor(self):
        armor = self._add_armor(slot="head")
        self.char1.db.worn_head = armor
        self.call(CmdUnwield(), armor.key, caller=self.char1)
        self.assertIsNone(self.char1.db.worn_head)

    def test_doff_can_remove_a_weapon(self):
        weapon = self._add_weapon()
        self.char1.db.wielded_weapon = weapon
        self.call(CmdDoff(), weapon.key, caller=self.char1)
        self.assertIsNone(self.char1.db.wielded_weapon)

    def test_bare_unwield_still_drops_the_weapon_specifically(self):
        # No argument still defaults to the one well-known convention
        # (drop the weapon), unchanged from before this fix.
        weapon = self._add_weapon()
        self.char1.db.wielded_weapon = weapon
        self.call(CmdUnwield(), "", caller=self.char1)
        self.assertIsNone(self.char1.db.wielded_weapon)

    def test_bare_doff_with_no_weapon_lists_what_is_worn(self):
        armor = self._add_armor(slot="head")
        self.char1.db.worn_head = armor
        result = self.call(CmdDoff(), "", caller=self.char1)
        self.assertIn(armor.key, result)
        self.assertIsNotNone(self.char1.db.worn_head)  # nothing removed, just listed

    def test_registered_aliases(self):
        # self.call() invokes a command instance directly, bypassing
        # Evennia's real cmdset/alias lookup entirely - so the
        # meaningful check for "does this alias actually work" is
        # simply that it's declared, not a call() round-trip through
        # a command object that would respond identically regardless
        # of what string was used to reach it.
        self.assertIn("equip", CmdWield.aliases)
        self.assertIn("wear", CmdDon.aliases)
        self.assertIn("remove", CmdDoff.aliases)
        self.assertIn("unequip", CmdDoff.aliases)
        # wield/don and unwield/doff must not share an alias/key with
        # each other, or Evennia's cmdset would have two commands
        # claiming the same input string.
        wield_names = {CmdWield.key, *CmdWield.aliases}
        don_names = {CmdDon.key, *CmdDon.aliases}
        self.assertEqual(wield_names & don_names, set())
        unwield_names = {CmdUnwield.key, *CmdUnwield.aliases}
        doff_names = {CmdDoff.key, *CmdDoff.aliases}
        self.assertEqual(unwield_names & doff_names, set())


class TestEvidenceBasedAliases(CombatCommandTestBase):
    """
    Regression coverage for aliases added from real player command
    logs (two separate new-player sessions) rather than guesswork -
    each one only added after confirming it doesn't collide with an
    existing, differently-behaving command. 'skill' (bare) was
    considered and deliberately rejected: it's already the real key
    for CmdUseSkill (the skill-casting equivalent of 'cast'), so a
    player typing it got a correct "Usage: skill <skill name>"
    response, not a bug - adding it as an alias for skillinfo/skills
    would have silently broken that real command instead of fixing
    anything.
    """

    def test_score_is_an_alias_for_stats(self):
        self.assertIn("score", CmdCoreStats.aliases)

    def test_sheath_is_an_alias_for_unwield(self):
        self.assertIn("sheath", CmdUnwield.aliases)

    def test_score_alias_does_not_collide_with_a_real_command(self):
        # CmdUseSkill's real key ('skill') was deliberately NOT
        # aliased onto CmdSkillInfo for exactly this reason - confirm
        # 'score' has no such collision before trusting it.
        from world.combat import CmdUseSkill

        used_names = {CmdUseSkill.key, *CmdUseSkill.aliases}
        self.assertNotIn("score", used_names)
        self.assertNotIn("sheath", used_names)


class TestCmdLookPrioritizesExitsOverSameLetterItems(CombatCommandTestBase):
    """
    Real, confirmed live bug reported directly by a player: "using
    look s doesnt look south but to your steel dagger". Genuine
    Evennia/rpsystem search-priority behavior, not specific to this
    one item - a single-letter direction alias could lose to a same-
    letter prefix match on anything in the caller's own inventory.
    Exits are now checked first, by exact key/alias match, before
    falling through to the stock generic search.
    """

    def test_single_letter_alias_resolves_to_the_exit_not_a_same_letter_item(self):
        exit_obj = create.create_object(
            "typeclasses.exits.Exit",
            key="south",
            aliases=["s"],
            location=self.room1,
            destination=self.room2,
        )
        exit_obj.db.desc = "A quiet path leads south."
        create.create_object(
            "typeclasses.objects.Object", key="a steel dagger", location=self.char1
        )

        result = self.call(CmdLook(), "s", caller=self.char1)

        self.assertIn("south", result.lower())
        self.assertNotIn("steel dagger", result)

    def test_full_exit_name_still_resolves_to_the_exit(self):
        create.create_object(
            "typeclasses.exits.Exit",
            key="south",
            aliases=["s"],
            location=self.room1,
            destination=self.room2,
        )

        result = self.call(CmdLook(), "south", caller=self.char1)
        self.assertIn("south", result.lower())

    def test_ordinary_item_lookup_still_works_when_no_exit_matches(self):
        create.create_object(
            "typeclasses.objects.Object", key="a wooden shield", location=self.char1
        )

        result = self.call(CmdLook(), "wooden", caller=self.char1)
        self.assertIn("wooden shield", result.lower())

    def test_bare_look_still_shows_the_room(self):
        result = self.call(CmdLook(), "", caller=self.char1)
        self.assertIn(self.room1.key, result)


class TestCmdForceSearchesGlobally(CombatCommandTestBase):
    """
    Real, confirmed live bug reported directly: 'force' only ever
    worked on someone in the same room as the caller - the stock
    Evennia command calls self.caller.search(self.lhs) with no
    global_search flag, defaulting to the caller's own room/inventory
    only. Fixed to search globally, matching how every other admin
    targeting command in this game already works (godteleport, snoop,
    restore, wizinvis).
    """

    def test_forces_a_command_on_someone_in_a_different_room(self):
        self.char2.location = self.room2

        result = self.call(CmdForce(), "Char2=say hello", caller=self.char1)

        self.assertIn("forced", result.lower())

    def test_still_refuses_with_no_target_or_command(self):
        result = self.call(CmdForce(), "", caller=self.char1)
        self.assertIn("must provide a target", result.lower())
