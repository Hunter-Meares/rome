"""
Tests for religion & piety (world/religion.py): tier math, the
Pontifex/blemish/expel management gate, the four real action triggers
(Mars/Mercury/Apollo/Pluto), and the CmdPray/CmdPontifex/CmdBlemish/
CmdExpel/CmdReligion command flows.
"""

from unittest.mock import patch

from evennia.utils.test_resources import EvenniaTest, EvenniaCommandTest
from evennia.utils import create

from world.combat import AutoStatNPC, COMBAT_RULES
from world.religion import (
    PANTHEON_ALTAR_ROOM,
    RELIGION_TRIGGERS,
    RELIGION_BONUSES,
    PIETY_PER_TICK,
    BLEMISH_AMOUNT,
    CmdPray,
    CmdPontifex,
    CmdBlemish,
    CmdExpel,
    CmdReligion,
    piety_tier,
    can_manage_religion,
    join_religion,
    leave_religion,
    add_piety,
    religion_bonus,
    credit_mars_kill,
    credit_mercury_trade,
    credit_apollo_heal,
    credit_pluto_resurrection,
    ensure_religion_channels_exist,
    get_religion_channel,
    JupiterSanctumGateExit,
    CmdBeseech,
    ensure_divine_channel_exists,
    get_divine_channel,
    connect_god_to_divine_channel,
)
from server.conf.lockfuncs import is_god


class TestPietyTier(EvenniaTest):
    def test_boundaries(self):
        self.assertIsNone(piety_tier(0))
        self.assertIsNone(piety_tier(24))
        self.assertEqual(piety_tier(25), "Favored")
        self.assertEqual(piety_tier(74), "Favored")
        self.assertEqual(piety_tier(75), "Devoted")
        self.assertEqual(piety_tier(149), "Devoted")
        self.assertEqual(piety_tier(150), "Beloved")


class TestCanManageReligion(EvenniaTest):
    def test_god_can_manage_any_religion(self):
        self.char1.db.level = 101
        self.char1.db.religion = None
        self.assertTrue(can_manage_religion(self.char1, "mars"))

    def test_pontifex_of_own_religion(self):
        self.char1.db.level = 10
        self.char1.db.religion = "mars"
        self.char1.db.religion_rank = "pontifex"
        self.assertTrue(can_manage_religion(self.char1, "mars"))

    def test_pontifex_of_a_different_religion_cannot_manage_this_one(self):
        self.char1.db.level = 10
        self.char1.db.religion = "mercury"
        self.char1.db.religion_rank = "pontifex"
        self.assertFalse(can_manage_religion(self.char1, "mars"))

    def test_ordinary_member_cannot_manage(self):
        self.char1.db.level = 10
        self.char1.db.religion = "mars"
        self.char1.db.religion_rank = "member"
        self.assertFalse(can_manage_religion(self.char1, "mars"))


class TestJoinLeaveAndAddPiety(EvenniaTest):
    def test_join_sets_religion_and_member_rank(self):
        join_religion(self.char1, "mars")
        self.assertEqual(self.char1.db.religion, "mars")
        self.assertEqual(self.char1.db.religion_rank, "member")

    def test_leave_clears_both(self):
        join_religion(self.char1, "mars")
        leave_religion(self.char1)
        self.assertIsNone(self.char1.db.religion)
        self.assertIsNone(self.char1.db.religion_rank)

    def test_add_piety_floors_at_zero(self):
        self.char1.db.piety = {"mars": 5}
        add_piety(self.char1, "mars", -100)
        self.assertEqual(self.char1.db.piety["mars"], 0)

    def test_add_piety_announces_a_new_tier(self):
        self.char1.db.piety = {"mars": 20}
        add_piety(self.char1, "mars", 10)  # crosses into Favored (25)
        self.assertEqual(self.char1.db.piety["mars"], 30)


class TestActionTriggers(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.religion = None
        self.char1.db.piety = {}
        self.char1.db.piety_progress = {}

    def _tick_to_threshold(self, credit_fn, god_key, arg):
        required = RELIGION_TRIGGERS[god_key]["count_required"]
        for _ in range(required):
            credit_fn(arg)

    def test_mars_kill_ignored_for_non_mars_devotee(self):
        self.char1.db.religion = "mercury"
        npc = create.create_object(AutoStatNPC, key="dummy", location=self.room1)
        npc.db.damage_log = {self.char1: 10}
        credit_mars_kill(npc)
        self.assertEqual(self.char1.db.piety.get("mars", 0), 0)

    def test_mars_kill_ticks_piety_at_threshold_and_resets_counter(self):
        self.char1.db.religion = "mars"
        required = RELIGION_TRIGGERS["mars"]["count_required"]

        for i in range(required - 1):
            npc = create.create_object(AutoStatNPC, key="dummy", location=self.room1)
            npc.db.damage_log = {self.char1: 10}
            credit_mars_kill(npc)
        self.assertEqual(self.char1.db.piety.get("mars", 0), 0)

        npc = create.create_object(AutoStatNPC, key="dummy", location=self.room1)
        npc.db.damage_log = {self.char1: 10}
        credit_mars_kill(npc)
        self.assertEqual(self.char1.db.piety["mars"], PIETY_PER_TICK)
        self.assertEqual(self.char1.db.piety_progress["mars"], 0)

    def test_mercury_trade_ticks_piety(self):
        self.char1.db.religion = "mercury"
        required = RELIGION_TRIGGERS["mercury"]["count_required"]
        for _ in range(required):
            credit_mercury_trade(self.char1)
        self.assertEqual(self.char1.db.piety["mercury"], PIETY_PER_TICK)

    def test_apollo_heal_ticks_piety(self):
        self.char1.db.religion = "apollo"
        required = RELIGION_TRIGGERS["apollo"]["count_required"]
        for _ in range(required):
            credit_apollo_heal(self.char1)
        self.assertEqual(self.char1.db.piety["apollo"], PIETY_PER_TICK)

    def test_pluto_resurrection_grants_piety_immediately_no_counter(self):
        self.char1.db.religion = "pluto"
        credit_pluto_resurrection(self.char1)
        self.assertGreater(self.char1.db.piety["pluto"], 0)

    def test_pluto_ignored_for_non_pluto_devotee(self):
        self.char1.db.religion = "mars"
        credit_pluto_resurrection(self.char1)
        self.assertEqual(self.char1.db.piety.get("pluto", 0), 0)


class TestCmdPray(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char1.db.religion = None
        self.char1.db.religion_rank = None
        self.jupiter_cella = create.create_object(
            "typeclasses.rooms.Room", key="Main Cella - Jupiter"
        )
        self.altar = create.create_object(
            "typeclasses.rooms.Room", key=PANTHEON_ALTAR_ROOM
        )

    def test_implicit_join_at_dedicated_temple_requires_confirm(self):
        self.char1.location = self.jupiter_cella
        result = self.call(CmdPray(), "", caller=self.char1)
        self.assertIn("pray jupiter confirm", result)
        self.assertIsNone(self.char1.db.religion)

    def test_implicit_join_confirmed_actually_joins(self):
        self.char1.location = self.jupiter_cella
        result = self.call(CmdPray(), "confirm", caller=self.char1)
        self.assertIn("devote yourself to Jupiter", result)
        self.assertEqual(self.char1.db.religion, "jupiter")

    def test_mismatched_explicit_god_at_a_specific_temple_is_refused(self):
        self.char1.location = self.jupiter_cella
        result = self.call(CmdPray(), "mars confirm", caller=self.char1)
        self.assertIn("belongs to Jupiter", result)
        self.assertIsNone(self.char1.db.religion)

    def test_pantheon_altar_requires_explicit_god(self):
        self.char1.location = self.altar
        result = self.call(CmdPray(), "", caller=self.char1)
        self.assertIn("Pray to which god", result)

    def test_pantheon_altar_works_for_a_god_with_no_dedicated_temple(self):
        self.char1.location = self.altar
        result = self.call(CmdPray(), "neptune confirm", caller=self.char1)
        self.assertEqual(self.char1.db.religion, "neptune")

    def test_no_shrine_elsewhere(self):
        self.char1.location = self.room1
        result = self.call(CmdPray(), "", caller=self.char1)
        self.assertIn("no shrine here", result)

    def test_ordinary_member_cannot_switch_religions(self):
        self.char1.db.religion = "mars"
        self.char1.db.level = 10
        self.char1.location = self.jupiter_cella
        result = self.call(CmdPray(), "confirm", caller=self.char1)
        self.assertIn("already devoted to Mars", result)
        self.assertEqual(self.char1.db.religion, "mars")

    def test_god_can_switch_freely(self):
        self.char1.db.religion = "mars"
        self.char1.db.level = 101
        self.char1.location = self.jupiter_cella
        result = self.call(CmdPray(), "confirm", caller=self.char1)
        self.assertEqual(self.char1.db.religion, "jupiter")


class TestCmdPontifex(EvenniaCommandTest):
    def test_non_god_refused(self):
        self.char1.db.level = 50
        result = self.call(CmdPontifex(), "mars = Char2", caller=self.char1)
        self.assertIn("lack the standing", result)

    def test_god_appoints_and_auto_joins_if_needed(self):
        self.char1.db.level = 101
        self.char2.db.religion = None
        result = self.call(CmdPontifex(), "mars = Char2", caller=self.char1)
        self.assertIn("Pontifex", result)
        self.assertEqual(self.char2.db.religion, "mars")
        self.assertEqual(self.char2.db.religion_rank, "pontifex")


class TestCmdBlemish(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char2.db.religion = "mars"
        self.char2.db.religion_rank = "member"
        self.char2.db.piety = {"mars": 50}
        self.char1.db.blemish_cooldowns = {}

    def test_requires_a_reason(self):
        self.char1.db.level = 101
        result = self.call(CmdBlemish(), "Char2 = ", caller=self.char1)
        self.assertIn("reason is required", result)

    def test_non_manager_refused(self):
        self.char1.db.level = 10
        self.char1.db.religion = None
        result = self.call(CmdBlemish(), "Char2 = betraying Mars", caller=self.char1)
        self.assertIn("don't have the standing", result)
        self.assertEqual(self.char2.db.piety["mars"], 50)

    def test_god_can_blemish_and_it_is_logged(self):
        self.char1.db.level = 101
        result = self.call(CmdBlemish(), "Char2 = fled from battle", caller=self.char1)
        self.assertIn("blemished", result)
        self.assertEqual(self.char2.db.piety["mars"], 50 - BLEMISH_AMOUNT)
        self.assertEqual(len(self.char2.db.religion_log), 1)
        self.assertEqual(self.char2.db.religion_log[0]["reason"], "fled from battle")

    def test_cooldown_blocks_a_second_blemish_from_the_same_discipliner(self):
        self.char1.db.level = 101
        self.call(CmdBlemish(), "Char2 = first offense", caller=self.char1)
        result = self.call(CmdBlemish(), "Char2 = second offense", caller=self.char1)
        self.assertIn("too recently", result)
        self.assertEqual(self.char2.db.piety["mars"], 50 - BLEMISH_AMOUNT)


class TestCmdExpel(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.char2.db.religion = "mars"
        self.char2.db.religion_rank = "member"
        self.char2.db.piety = {"mars": 50}

    def test_requires_a_reason(self):
        self.char1.db.level = 101
        result = self.call(CmdExpel(), "Char2 = ", caller=self.char1)
        self.assertIn("reason is required", result)

    def test_god_can_expel_preserving_piety(self):
        self.char1.db.level = 101
        result = self.call(CmdExpel(), "Char2 = renounced the faith", caller=self.char1)
        self.assertIn("expelled", result)
        self.assertIsNone(self.char2.db.religion)
        self.assertEqual(self.char2.db.piety["mars"], 50)  # preserved, not erased
        self.assertEqual(len(self.char2.db.religion_log), 1)


class TestCmdReligion(EvenniaCommandTest):
    def test_no_piety_shows_empty_state(self):
        self.char1.db.piety = {}
        result = self.call(CmdReligion(), "", caller=self.char1)
        self.assertIn("no standing with any god", result)

    def test_shows_own_standing(self):
        self.char1.db.piety = {"mars": 30}
        self.char1.db.religion = "mars"
        self.char1.db.religion_rank = "member"
        result = self.call(CmdReligion(), "", caller=self.char1)
        self.assertIn("Mars", result)
        self.assertIn("Favored", result)

    def test_log_refused_for_non_god(self):
        self.char1.db.level = 50
        result = self.call(CmdReligion(), "log mars", caller=self.char1)
        self.assertIn("Only gods", result)

    def test_log_shows_logged_entries(self):
        self.char1.db.level = 101
        self.char2.db.religion = "mars"
        self.char2.db.religion_log = [
            {"action": "blemish", "by": "Someone", "reason": "test reason", "time": 1.0}
        ]
        result = self.call(CmdReligion(), "log mars", caller=self.char1)
        self.assertIn("test reason", result)


class TestReligionBonus(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.char1.db.religion = None
        self.char1.db.piety = {}

    def test_no_bonus_below_devoted(self):
        self.char1.db.religion = "mars"
        self.char1.db.piety = {"mars": 30}  # Favored, not Devoted
        self.assertEqual(religion_bonus(self.char1, "mars", "melee_damage_bonus"), 0)

    def test_devoted_grants_the_defined_bonus(self):
        self.char1.db.religion = "mars"
        self.char1.db.piety = {"mars": 80}  # Devoted
        self.assertEqual(
            religion_bonus(self.char1, "mars", "melee_damage_bonus"),
            RELIGION_BONUSES["mars"]["Devoted"]["melee_damage_bonus"],
        )

    def test_wrong_religion_gets_nothing(self):
        self.char1.db.religion = "mercury"
        self.char1.db.piety = {"mars": 200}  # high Mars piety, but not currently devoted to Mars
        self.assertEqual(religion_bonus(self.char1, "mars", "melee_damage_bonus"), 0)

    def test_god_with_no_bonus_defined_returns_zero(self):
        self.char1.db.religion = "neptune"
        self.char1.db.piety = {"neptune": 200}
        self.assertEqual(religion_bonus(self.char1, "neptune", "melee_damage_bonus"), 0)


class TestReligionChannels(EvenniaTest):
    def test_ensure_creates_one_channel_per_god(self):
        from world.god_help import PANTHEON

        created = ensure_religion_channels_exist()
        self.assertEqual(len(created), len(PANTHEON))
        for god_key in PANTHEON:
            self.assertIsNotNone(get_religion_channel(god_key))

    def test_ensure_is_idempotent(self):
        ensure_religion_channels_exist()
        second_pass = ensure_religion_channels_exist()
        self.assertEqual(len(second_pass), 0)

    def test_every_religion_channel_name_starts_with_a_capital(self):
        # A direct request: all channel names read like "Public".
        from world.god_help import PANTHEON

        ensure_religion_channels_exist()
        for god_key in PANTHEON:
            key = get_religion_channel(god_key).key
            self.assertTrue(key[0].isupper(), key)
            self.assertEqual(key, "%s-religion" % god_key.capitalize())

    def test_joining_connects_to_the_channel(self):
        ensure_religion_channels_exist()
        join_religion(self.char1, "mars")
        channel = get_religion_channel("mars")
        self.assertTrue(channel.has_connection(self.char1))

    def test_leaving_disconnects_from_the_channel(self):
        ensure_religion_channels_exist()
        join_religion(self.char1, "mars")
        leave_religion(self.char1)
        channel = get_religion_channel("mars")
        self.assertFalse(channel.has_connection(self.char1))

    def test_switching_religions_disconnects_the_old_channel(self):
        ensure_religion_channels_exist()
        join_religion(self.char1, "mars")
        join_religion(self.char1, "mercury")
        mars_channel = get_religion_channel("mars")
        mercury_channel = get_religion_channel("mercury")
        self.assertFalse(mars_channel.has_connection(self.char1))
        self.assertTrue(mercury_channel.has_connection(self.char1))


class TestIsGodLockfunc(EvenniaTest):
    """
    Real, confirmed live bug reported directly by a player: a real god
    (Jupiter, level 106) could not 'channel/sub' any faction/religion
    channel at all. Root cause - these channels' listen/send/control
    locks used to read "attr(level, 100, compare=gt)" directly, which
    is correct when checked against a CHARACTER (every other god-check
    in this game compares caller.db.level the same way) but wrong for
    an ACCOUNT: Evennia's own channel /sub path (comms.py's
    sub_to_channel -> Channel.connect) checks self.caller, which for
    an account-level command IS the account, not the puppeted
    character - and db.level only ever lives on the character. It was
    invisible for a long time specifically because Jupiter's account
    also happens to be a true superuser, which bypasses every lock
    unconditionally regardless of what the lock string even says (see
    CLAUDE.md gotcha #6) - masking this for the one account most
    likely to be used for testing, while leaving it silently broken
    for any future non-superuser god. Fixed with a dedicated is_god()
    lockfunc (server/conf/lockfuncs.py) that checks the puppeted
    character's level when given an Account.

    Tests is_god() directly against plain Mock stand-ins for the
    account case, rather than a real Account - Account.puppet depends
    on an actual live SESSION currently puppeting (get_all_puppets()
    reads self.sessions.all()), not any stored attribute a test could
    just set directly, so a real end-to-end simulation would mean
    standing up a whole fake session just to prove this one function's
    own logic. The channel-integration tests below it don't have that
    problem - a plain Character needs no session at all.
    """

    def test_true_for_a_characters_own_high_level(self):
        self.char1.db.level = 106
        self.assertTrue(is_god(self.char1, None))

    def test_false_for_a_characters_own_low_level(self):
        self.char1.db.level = 10
        self.assertFalse(is_god(self.char1, None))

    def test_false_when_level_was_never_set_at_all(self):
        self.assertFalse(is_god(self.char1, None))

    def test_true_for_an_account_via_its_puppeted_characters_level(self):
        """The actual bug this fixes: an Account has no db.level of
        its own at all - only a Character does."""
        from unittest.mock import Mock

        self.char1.db.level = 106
        fake_account = Mock()
        fake_account.attributes.get.return_value = None
        fake_account.puppet = self.char1
        self.assertTrue(is_god(fake_account, None))

    def test_false_for_an_account_with_no_puppet_at_all(self):
        from unittest.mock import Mock

        fake_account = Mock()
        fake_account.attributes.get.return_value = None
        fake_account.puppet = None
        self.assertFalse(is_god(fake_account, None))

    def test_false_for_an_account_whose_puppet_is_not_a_god(self):
        from unittest.mock import Mock

        self.char1.db.level = 10
        fake_account = Mock()
        fake_account.attributes.get.return_value = None
        fake_account.puppet = self.char1
        self.assertFalse(is_god(fake_account, None))


class TestGodChannelAccess(EvenniaTest):
    """Integration coverage: the real faction/religion channel lock
    strings actually use is_god() and grant a god's CHARACTER access
    regardless of faction/religion membership - the part that doesn't
    require simulating a real session to test."""

    def test_a_gods_character_can_listen_without_being_a_member(self):
        ensure_religion_channels_exist()
        self.char1.db.level = 106
        self.char1.db.religion = None
        channel = get_religion_channel("mars")
        self.assertTrue(channel.access(self.char1, "listen"))

    def test_a_non_god_non_member_is_denied(self):
        ensure_religion_channels_exist()
        self.char1.db.level = 10
        self.char1.db.religion = None
        channel = get_religion_channel("mars")
        self.assertFalse(channel.access(self.char1, "listen"))

    def test_faction_channels_get_the_same_fix(self):
        from world.factions import ensure_faction_channels_exist, get_faction_channel

        ensure_faction_channels_exist()
        self.char1.db.level = 101
        self.char1.db.faction = None
        channel = get_faction_channel("imperial_legion")
        self.assertTrue(channel.access(self.char1, "listen"))


class TestJupiterSanctumGateExit(EvenniaTest):
    """
    Two real bugs found live, fixed together: this exit used to be
    locked to traverse:perm(Builder) - an engine permission utterly
    disconnected from religion, meaning no real player could ever pass
    it regardless of devotion, despite the room's own desc implying
    real standing could earn entry - and a blocked attempt gave no
    message at all (Evennia's own silent default when a lock rejects
    you with no db.err_traverse set).
    """

    def setUp(self):
        super().setUp()
        self.gate = create.create_object(
            JupiterSanctumGateExit, key="north", location=self.room1, destination=self.room2
        )
        self.char1.db.level = 1
        self.char1.db.religion = None
        self.char1.db.piety = {}

    def test_blocked_and_explained_with_no_religion(self):
        captured = []
        self.char1.msg = lambda text="", **kwargs: captured.append(text)

        self.gate.at_traverse(self.char1, self.room2)

        self.assertEqual(self.char1.location, self.room1)
        full_text = "".join(str(m) for m in captured)
        self.assertIn("mystic force", full_text)

    def test_blocked_when_devoted_but_not_yet_beloved(self):
        self.char1.db.religion = "jupiter"
        self.char1.db.piety = {"jupiter": 100}  # Devoted, not Beloved

        self.gate.at_traverse(self.char1, self.room2)

        self.assertEqual(self.char1.location, self.room1)

    def test_blocked_when_beloved_of_a_different_god(self):
        self.char1.db.religion = "mars"
        self.char1.db.piety = {"mars": 200}

        self.gate.at_traverse(self.char1, self.room2)

        self.assertEqual(self.char1.location, self.room1)

    def test_allowed_when_beloved_of_jupiter(self):
        self.char1.db.religion = "jupiter"
        self.char1.db.piety = {"jupiter": 150}

        self.gate.at_traverse(self.char1, self.room2)

        self.assertEqual(self.char1.location, self.room2)

    def test_gods_always_pass_regardless_of_religion(self):
        self.char1.db.level = 101
        self.char1.db.religion = None

        self.gate.at_traverse(self.char1, self.room2)

        self.assertEqual(self.char1.location, self.room2)


class TestDivineChannel(EvenniaTest):
    """
    The 'divine' channel (world/religion.py) - a direct request for an
    IC way for players to reach the gods, distinct from the per-god
    religion channels: one shared channel every god hears regardless of
    which god a prayer was addressed to, not 14 separate ones.
    """

    def test_its_name_starts_with_a_capital(self):
        ensure_divine_channel_exists()
        self.assertEqual(get_divine_channel().key, "Divine")

    def test_ensure_creates_it_exactly_once(self):
        first = ensure_divine_channel_exists()
        self.assertIsNotNone(first)
        second = ensure_divine_channel_exists()
        self.assertIsNone(second)  # idempotent - already exists

    def test_a_gods_character_can_listen_with_no_membership_needed(self):
        ensure_divine_channel_exists()
        self.char1.db.level = 106
        channel = get_divine_channel()
        self.assertTrue(channel.access(self.char1, "listen"))

    def test_an_ordinary_mortal_cannot_listen_or_send(self):
        ensure_divine_channel_exists()
        self.char1.db.level = 10
        channel = get_divine_channel()
        self.assertFalse(channel.access(self.char1, "listen"))
        self.assertFalse(channel.access(self.char1, "send"))

    def test_connect_god_to_divine_channel_subscribes_them(self):
        ensure_divine_channel_exists()
        self.char1.db.level = 106
        connect_god_to_divine_channel(self.char1)
        channel = get_divine_channel()
        self.assertIn(self.char1, channel.subscriptions.all())


class TestCmdBeseech(EvenniaCommandTest):
    """
    CmdBeseech - the actual 'cry out to a god' command. Deliberately a
    separate verb from CmdPray (which is shrine-gated and joins a
    religion) - this works from anywhere, to any of the 14, regardless
    of the caller's own devotion, and has no mechanical effect at all
    beyond the room announcement and the divine-channel post.
    """

    def setUp(self):
        super().setUp()
        self.char1.db.last_beseech_time = None
        ensure_divine_channel_exists()

    def test_requires_an_equals_sign(self):
        result = self.call(CmdBeseech(), "mars help me", caller=self.char1)
        self.assertIn("Usage:", result)

    def test_unknown_god_is_refused(self):
        result = self.call(CmdBeseech(), "nosuchgod = help", caller=self.char1)
        self.assertIn("No god matches", result)

    def test_valid_prayer_announces_in_the_room(self):
        result = self.call(CmdBeseech(), "mars = give me strength", caller=self.char1)
        self.assertIn("cries out to Mars", result)

    def test_valid_prayer_posts_to_the_divine_channel(self):
        with patch("world.religion.get_divine_channel") as mock_get_channel:
            mock_channel = mock_get_channel.return_value
            self.call(CmdBeseech(), "mars = give me strength", caller=self.char1)
        mock_channel.msg.assert_called_once()

    def test_cooldown_blocks_a_second_prayer_too_soon(self):
        self.call(CmdBeseech(), "mars = first plea", caller=self.char1)
        result = self.call(CmdBeseech(), "mars = second plea", caller=self.char1)
        self.assertIn("give them a moment", result)
