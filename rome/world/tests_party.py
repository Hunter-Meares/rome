"""
Tests for the party system (world/party.py) - the "never explicitly
confirmed this project" item flagged in CLAUDE.md's known-untested
list. Covers the plain helper functions directly, plus the CmdParty
subcommands via EvenniaTest's call() helper against real Character
objects.
"""

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest

from world.party import get_party_members, is_party_leader, CmdParty


class TestGetPartyMembers(EvenniaTest):
    def test_solo_character_returns_just_themselves(self):
        self.char1.db.party_leader = None
        self.char1.db.party_members = None
        self.assertEqual(get_party_members(self.char1), [self.char1])

    def test_returns_full_roster_including_self(self):
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2]
        self.char2.db.party_leader = self.char1

        self.assertEqual(get_party_members(self.char1), [self.char1, self.char2])
        # A non-leader member looks up the SAME list via the leader.
        self.assertEqual(get_party_members(self.char2), [self.char1, self.char2])

    def test_filters_stale_deleted_references(self):
        from evennia.utils import create

        ghost = create.create_object("typeclasses.characters.Character", key="ghost")
        self.char1.db.party_leader = self.char1
        self.char1.db.party_members = [self.char1, self.char2, ghost]
        ghost.delete()

        result = get_party_members(self.char1)
        self.assertEqual(result, [self.char1, self.char2])


class TestIsPartyLeader(EvenniaTest):
    def test_solo_character_is_own_leader(self):
        self.char1.db.party_leader = None
        self.assertTrue(is_party_leader(self.char1))

    def test_leader_is_leader(self):
        self.char1.db.party_leader = self.char1
        self.assertTrue(is_party_leader(self.char1))

    def test_regular_member_is_not_leader(self):
        self.char1.db.party_leader = self.char2
        self.assertFalse(is_party_leader(self.char1))


class TestPartyCommandFlow(EvenniaCommandTest):
    """
    Exercises the actual CmdParty subcommands end to end, the way a
    player would type them - invite/accept/leave/kick, per the
    CLAUDE.md checklist item.
    """

    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.db.party_leader = None
            char.db.party_members = None
            char.db.party_invite = None
        self.char1.location = self.room1
        self.char2.location = self.room1

    def test_invite_and_accept_forms_a_party(self):
        self.call(CmdParty(), "invite Char2", caller=self.char1)
        self.assertEqual(self.char2.db.party_invite, self.char1)

        self.call(CmdParty(), "accept", caller=self.char2)

        self.assertEqual(self.char1.db.party_leader, self.char1)
        self.assertIn(self.char2, self.char1.db.party_members)
        self.assertEqual(self.char2.db.party_leader, self.char1)
        self.assertIsNone(self.char2.db.party_invite)

    def test_decline_leaves_no_party_formed(self):
        self.call(CmdParty(), "invite Char2", caller=self.char1)
        self.call(CmdParty(), "decline", caller=self.char2)

        self.assertIsNone(self.char2.db.party_invite)
        self.assertEqual(get_party_members(self.char1), [self.char1])
        self.assertEqual(get_party_members(self.char2), [self.char2])

    def test_cannot_invite_self(self):
        self.call(CmdParty(), "invite %s" % self.char1.key, caller=self.char1)
        self.assertEqual(get_party_members(self.char1), [self.char1])

    def test_non_leader_cannot_invite(self):
        # Form a party with char1 as leader, char2 as member.
        self.call(CmdParty(), "invite Char2", caller=self.char1)
        self.call(CmdParty(), "accept", caller=self.char2)

        from evennia.utils import create

        char3 = create.create_object(
            "typeclasses.characters.Character", key="Char3", location=self.room1
        )
        result = self.call(CmdParty(), "invite Char3", caller=self.char2)
        self.assertIn("Only your party's leader", result)
        self.assertNotIn(char3, get_party_members(self.char1))

    def test_cannot_invite_someone_already_in_a_party(self):
        from evennia.utils import create

        char3 = create.create_object(
            "typeclasses.characters.Character", key="Char3", location=self.room1
        )
        char3.db.party_leader = None
        char3.db.party_members = None
        char3.db.party_invite = None

        # char1+char2 form a party first.
        self.call(CmdParty(), "invite Char2", caller=self.char1)
        self.call(CmdParty(), "accept", caller=self.char2)

        # char3 tries to invite char2, who's already partied elsewhere.
        result = self.call(CmdParty(), "invite Char2", caller=char3)
        self.assertIn("already in another party", result)

    def test_leader_leaving_promotes_next_member(self):
        self.call(CmdParty(), "invite Char2", caller=self.char1)
        self.call(CmdParty(), "accept", caller=self.char2)

        self.call(CmdParty(), "leave", caller=self.char1)

        self.assertEqual(self.char2.db.party_leader, self.char2)
        self.assertEqual(self.char2.db.party_members, [self.char2])
        self.assertIsNone(self.char1.db.party_leader)
        self.assertIsNone(self.char1.db.party_members)

    def test_last_member_leaving_disbands_party(self):
        self.call(CmdParty(), "invite Char2", caller=self.char1)
        self.call(CmdParty(), "accept", caller=self.char2)

        self.call(CmdParty(), "leave", caller=self.char2)

        self.assertEqual(get_party_members(self.char1), [self.char1])

    def test_leaving_solo_reports_not_in_a_party(self):
        result = self.call(CmdParty(), "leave", caller=self.char1)
        self.assertIn("not in a party", result)

    def test_leader_kick_removes_member(self):
        self.call(CmdParty(), "invite Char2", caller=self.char1)
        self.call(CmdParty(), "accept", caller=self.char2)

        self.call(CmdParty(), "kick Char2", caller=self.char1)

        self.assertIsNone(self.char2.db.party_leader)
        self.assertIsNone(self.char2.db.party_members)
        self.assertEqual(get_party_members(self.char1), [self.char1])

    def test_non_leader_cannot_kick(self):
        self.call(CmdParty(), "invite Char2", caller=self.char1)
        self.call(CmdParty(), "accept", caller=self.char2)

        result = self.call(CmdParty(), "kick %s" % self.char1.key, caller=self.char2)
        self.assertIn("Only your party's leader", result)
        self.assertIn(self.char1, get_party_members(self.char2))

    def test_cannot_kick_self(self):
        self.call(CmdParty(), "invite Char2", caller=self.char1)
        self.call(CmdParty(), "accept", caller=self.char2)

        result = self.call(CmdParty(), "kick %s" % self.char1.key, caller=self.char1)
        self.assertIn("use 'party leave' instead", result)

    def test_roster_display_for_solo_character(self):
        result = self.call(CmdParty(), "", caller=self.char1)
        self.assertIn("not currently in a party", result)

    def test_roster_display_shows_all_members_and_leader_tag(self):
        self.call(CmdParty(), "invite Char2", caller=self.char1)
        self.call(CmdParty(), "accept", caller=self.char2)

        result = self.call(CmdParty(), "", caller=self.char1)
        self.assertIn(self.char1.key, result)
        self.assertIn("Char2", result)
        self.assertIn("leader", result)
