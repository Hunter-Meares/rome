"""
Tests for the faction membership system (world/factions.py): joining
grants/strips the right skills, one-faction-at-a-time switching, the
single-leader-at-a-time rule, invest/expel permission checks, and the
Oath Sworn mutual-buff/betrayal-penalty combat hook in world/combat.py.
"""

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest

from world.factions import (
    FACTIONS,
    join_faction,
    leave_faction,
    set_faction_leader,
    can_manage_faction,
    CmdFaction,
    FactionInductorNPC,
)
from world.combat import COMBAT_RULES, CombatTurnHandler


class FactionTestBase(EvenniaTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.db.skills_known = []
            char.db.faction = None
            char.db.faction_rank = None
            char.db.level = 10
            char.db.conditions = {}
            char.db.virtus = 10
            char.db.agilitas = 10
            char.db.ingenium = 10
            char.db.vigor = 10
            char.db.hp = 50
            char.db.max_hp = 50
            char.db.oath_partner = None
            char.account = None


class TestJoinFaction(FactionTestBase):
    def test_join_grants_the_factions_skills(self):
        join_faction(self.char1, "cult_of_bacchus")

        for skill in FACTIONS["cult_of_bacchus"]["skills"]:
            self.assertIn(skill, self.char1.db.skills_known)

    def test_join_sets_faction_and_member_rank(self):
        join_faction(self.char1, "cult_of_hecate")

        self.assertEqual(self.char1.db.faction, "cult_of_hecate")
        self.assertEqual(self.char1.db.faction_rank, "member")

    def test_joining_a_new_faction_leaves_the_old_one(self):
        join_faction(self.char1, "imperial_legion")
        join_faction(self.char1, "collegium_umbrae")

        self.assertEqual(self.char1.db.faction, "collegium_umbrae")
        for skill in FACTIONS["imperial_legion"]["skills"]:
            self.assertNotIn(skill, self.char1.db.skills_known)
        for skill in FACTIONS["collegium_umbrae"]["skills"]:
            self.assertIn(skill, self.char1.db.skills_known)

    def test_no_two_factions_share_an_ability_name(self):
        seen = {}
        for key, data in FACTIONS.items():
            for skill in data["skills"]:
                self.assertNotIn(
                    skill, seen, "%s is claimed by both %s and %s" % (skill, seen.get(skill), key)
                )
                seen[skill] = key


class TestLeaveFaction(FactionTestBase):
    def test_leave_strips_skills_and_clears_faction(self):
        join_faction(self.char1, "praetorian_order")

        result = leave_faction(self.char1)

        self.assertTrue(result)
        self.assertIsNone(self.char1.db.faction)
        self.assertIsNone(self.char1.db.faction_rank)
        for skill in FACTIONS["praetorian_order"]["skills"]:
            self.assertNotIn(skill, self.char1.db.skills_known)

    def test_leave_with_no_faction_returns_false(self):
        self.assertFalse(leave_faction(self.char1))


class TestSetFactionLeader(FactionTestBase):
    def test_only_one_leader_at_a_time(self):
        join_faction(self.char1, "orphic_mysteries")
        join_faction(self.char2, "orphic_mysteries")

        set_faction_leader("orphic_mysteries", self.char1)
        set_faction_leader("orphic_mysteries", self.char2)

        self.assertEqual(self.char1.db.faction_rank, "member")
        self.assertEqual(self.char2.db.faction_rank, "leader")

    def test_designating_a_non_member_joins_them_first(self):
        set_faction_leader("cult_of_mithras", self.char1)

        self.assertEqual(self.char1.db.faction, "cult_of_mithras")
        self.assertEqual(self.char1.db.faction_rank, "leader")


class TestCanManageFaction(FactionTestBase):
    def test_god_can_manage_any_faction(self):
        self.char1.db.level = 101
        self.assertTrue(can_manage_faction(self.char1, "hellenic_resistance"))

    def test_leader_can_manage_their_own_faction(self):
        join_faction(self.char1, "hellenic_resistance")
        self.char1.db.faction_rank = "leader"

        self.assertTrue(can_manage_faction(self.char1, "hellenic_resistance"))

    def test_leader_cannot_manage_a_different_faction(self):
        join_faction(self.char1, "hellenic_resistance")
        self.char1.db.faction_rank = "leader"

        self.assertFalse(can_manage_faction(self.char1, "cult_of_hecate"))

    def test_plain_member_cannot_manage_their_own_faction(self):
        join_faction(self.char1, "hellenic_resistance")

        self.assertFalse(can_manage_faction(self.char1, "hellenic_resistance"))


class TestOathSworn(FactionTestBase):
    """
    Covers the combat.py hooks added for Oath Sworn: mutual Accuracy Up
    when both partners share a fight, and Defense Down + broken bond if
    one attacks the other.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.oath_partner = self.char2
        self.char2.db.oath_partner = self.char1

    def test_joining_the_same_fight_grants_both_accuracy_up(self):
        # Same mechanism a real duel uses (see skill_ambush): seed
        # pending_fighters on the room, then attach the script - this
        # exercises the real at_script_creation -> initialize_for_combat
        # path rather than hand-constructing a handler.
        self.room1.ndb.pending_fighters = [self.char1, self.char2]
        self.room1.scripts.add(CombatTurnHandler)

        self.assertIn("Accuracy Up", COMBAT_RULES.get_conditions(self.char1))
        self.assertIn("Accuracy Up", COMBAT_RULES.get_conditions(self.char2))

    def test_attacking_your_oath_partner_breaks_it_and_penalizes_both(self):
        self.char1.db.wielded_weapon = None
        self.char2.db.wielded_weapon = None
        self.char1.location.msg_contents = lambda *a, **k: None

        COMBAT_RULES.resolve_attack(
            self.char1, self.char2, attack_value=100, defense_value=0, damage_value=0
        )

        self.assertIsNone(self.char1.db.oath_partner)
        self.assertIsNone(self.char2.db.oath_partner)
        self.assertIn("Defense Down", COMBAT_RULES.get_conditions(self.char1))
        self.assertIn("Defense Down", COMBAT_RULES.get_conditions(self.char2))

    def test_attacking_someone_else_does_not_break_the_oath(self):
        from evennia.utils import create

        stranger = create.create_object(
            "evennia.objects.objects.DefaultObject", key="a stranger"
        )
        stranger.db.wielded_weapon = None
        stranger.db.hp = 10
        self.char1.db.wielded_weapon = None
        self.char1.location.msg_contents = lambda *a, **k: None

        COMBAT_RULES.resolve_attack(
            self.char1, stranger, attack_value=100, defense_value=0, damage_value=0
        )

        self.assertEqual(self.char1.db.oath_partner, self.char2)
        self.assertEqual(self.char2.db.oath_partner, self.char1)


class CmdFactionTestBase(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.db.skills_known = []
            char.db.faction = None
            char.db.faction_rank = None
            char.db.level = 10
        from evennia.utils import create

        self.inductor = create.create_object(
            FactionInductorNPC, key="Test Inductor", location=self.room1
        )
        self.inductor.db.faction = "cult_of_bacchus"


class TestFactionJoinConfirmation(CmdFactionTestBase):
    """
    Joining is a deliberate, two-step commitment now, per direct
    request: the first 'faction join <name>' only shows the
    recruiter's in-character warning that this is permanent - it must
    NOT actually grant membership. Only 'faction join <name> confirm'
    does.
    """

    def test_join_without_confirm_does_not_grant_membership(self):
        result = self.call(CmdFaction(), "join Test Inductor", caller=self.char1)

        self.assertIsNone(self.char1.db.faction)
        self.assertIn("confirm", result.lower())

    def test_join_without_confirm_warns_about_permanence(self):
        result = self.call(CmdFaction(), "join Test Inductor", caller=self.char1)

        self.assertIn("life", result.lower())

    def test_join_with_confirm_grants_membership(self):
        self.call(CmdFaction(), "join Test Inductor", caller=self.char1)
        self.call(CmdFaction(), "join Test Inductor confirm", caller=self.char1)

        self.assertEqual(self.char1.db.faction, "cult_of_bacchus")

    def test_join_by_faction_name_with_confirm_works(self):
        self.call(CmdFaction(), "join bacchus confirm", caller=self.char1)

        self.assertEqual(self.char1.db.faction, "cult_of_bacchus")

    def test_existing_member_cannot_switch_to_a_different_faction(self):
        """
        Real gap found and closed: without this, an ordinary member
        could route around the entire "no self-leave" rule by just
        walking up to a different faction's recruiter and joining -
        join_faction's own auto-leave-old-first behavior would silently
        let that count as "leaving." Switching must be blocked exactly
        like leaving is, for the same reason.
        """
        join_faction(self.char1, "imperial_legion")

        result = self.call(CmdFaction(), "join bacchus confirm", caller=self.char1)

        self.assertEqual(self.char1.db.faction, "imperial_legion")
        self.assertIn("petition", result.lower())

    def test_a_god_can_still_switch_factions_directly(self):
        join_faction(self.char1, "imperial_legion")
        self.char1.db.level = 101

        self.call(CmdFaction(), "join bacchus confirm", caller=self.char1)

        self.assertEqual(self.char1.db.faction, "cult_of_bacchus")


class TestFactionLeaveRestriction(CmdFactionTestBase):
    """
    Factions are meant to be a lifelong commitment - an ordinary
    member should never be able to just walk away with 'faction
    leave'. Only that faction's own leader (stepping down) or a god
    can use it; getting an ordinary member out requires someone else
    to 'faction expel' them.
    """

    def test_plain_member_cannot_leave(self):
        join_faction(self.char1, "cult_of_bacchus")

        result = self.call(CmdFaction(), "leave", caller=self.char1)

        self.assertEqual(self.char1.db.faction, "cult_of_bacchus")
        self.assertIn("petition", result.lower())

    def test_leader_leave_only_steps_down_not_a_full_exit(self):
        """
        Real design refinement, direct request: a leader shouldn't be
        trapped running a faction forever, but stepping down from
        leadership is not the same vow as membership itself - only the
        rank should change, not full departure.
        """
        join_faction(self.char1, "cult_of_bacchus")
        self.char1.db.faction_rank = "leader"

        self.call(CmdFaction(), "leave", caller=self.char1)

        self.assertEqual(self.char1.db.faction, "cult_of_bacchus")
        self.assertEqual(self.char1.db.faction_rank, "member")

    def test_a_former_leader_is_bound_by_the_same_rule_as_any_member(self):
        join_faction(self.char1, "cult_of_bacchus")
        self.char1.db.faction_rank = "leader"
        self.call(CmdFaction(), "leave", caller=self.char1)  # steps down to member

        result = self.call(CmdFaction(), "leave", caller=self.char1)

        self.assertEqual(self.char1.db.faction, "cult_of_bacchus")
        self.assertIn("petition", result.lower())

    def test_a_god_can_leave_even_as_a_plain_member(self):
        join_faction(self.char1, "cult_of_bacchus")
        self.char1.db.level = 101

        self.call(CmdFaction(), "leave", caller=self.char1)

        self.assertIsNone(self.char1.db.faction)


class TestFactionExpelRequiresReasonAndLogs(CmdFactionTestBase):
    """
    Retrofitted, direct request: faction expel should require a reason
    and log it, the same accountability standard world/religion.py's
    own expel was built with from the start.
    """

    def setUp(self):
        super().setUp()
        join_faction(self.char2, "cult_of_bacchus")
        self.char1.db.level = 101

    def test_missing_reason_refused(self):
        result = self.call(CmdFaction(), "expel Char2 =", caller=self.char1)
        self.assertIn("A reason is required", result)
        self.assertEqual(self.char2.db.faction, "cult_of_bacchus")

    def test_no_equals_sign_shows_usage(self):
        result = self.call(CmdFaction(), "expel Char2", caller=self.char1)
        self.assertIn("Usage: faction expel", result)
        self.assertEqual(self.char2.db.faction, "cult_of_bacchus")

    def test_expel_with_reason_removes_membership_and_logs_it(self):
        result = self.call(CmdFaction(), "expel Char2 = betrayed the cult", caller=self.char1)
        self.assertIn("expelled", result)
        self.assertIsNone(self.char2.db.faction)
        self.assertEqual(len(self.char2.db.faction_log), 1)
        self.assertEqual(self.char2.db.faction_log[0]["reason"], "betrayed the cult")
