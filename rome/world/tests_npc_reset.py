"""
Tests for world/npc_reset.py - the periodic sweep that returns a
displaced NPC to its own db.respawn_home (or, for a WanderingNPC,
back inside its own wander_rooms beat), covering the real gap that
only a death/respawn cycle ever restored an NPC's position before
this, and generalized to cover every NPC hierarchy in the game (not
just the combat/RespawningNPC population), by direct request.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create

from world.npc_reset import sweep_and_reset_displaced_npcs, NPCHomeResetScript, RESET_INTERVAL_HOURS
from world.combat import RespawningNPC


class TestSweepAndResetDisplacedNpcs(EvenniaTest):
    def _make_combat_npc(self, key="a test respawning npc", location=None):
        return create.create_object(
            RespawningNPC,
            key=key,
            location=location or self.room1,
            attributes=[("race", "human"), ("player_class", "gladiator"), ("level", 10)],
        )

    def _make_flavor_npc(self, key="a test flavor npc", location=None):
        npc = create.create_object(
            "typeclasses.characters.Character", key=key, location=location or self.room1,
        )
        npc.locks.add("puppet:false()")
        return npc

    # --- Combat NPCs (already stamp db.respawn_home at creation) ---

    def test_combat_npc_already_at_home_is_left_alone(self):
        npc = self._make_combat_npc()
        self.assertEqual(npc.db.respawn_home, self.room1)

        result = sweep_and_reset_displaced_npcs()

        self.assertEqual(result["reset"], 0)
        self.assertEqual(npc.location, self.room1)

    def test_displaced_combat_npc_gets_moved_back_home(self):
        npc = self._make_combat_npc()
        npc.location = self.room2

        result = sweep_and_reset_displaced_npcs()

        self.assertEqual(result["reset"], 1)
        self.assertEqual(npc.location, self.room1)

    def test_npc_currently_in_combat_is_not_reset(self):
        npc = self._make_combat_npc()
        npc.location = self.room2
        npc.db.combat_turnhandler = True  # is_in_combat only checks truthiness

        result = sweep_and_reset_displaced_npcs()

        self.assertEqual(result["reset"], 0)
        self.assertEqual(result["skipped_in_combat"], 1)
        self.assertEqual(npc.location, self.room2)

    def test_npc_mid_respawn_wait_with_no_location_is_skipped(self):
        npc = self._make_combat_npc()
        npc.location = None

        result = sweep_and_reset_displaced_npcs()  # must not raise

        self.assertEqual(result["reset"], 0)

    def test_deleted_npc_reference_does_not_crash_the_sweep(self):
        npc = self._make_combat_npc()
        other = self._make_combat_npc(key="a second test npc")
        other.location = self.room2
        npc.delete()

        result = sweep_and_reset_displaced_npcs()  # must not raise

        self.assertEqual(result["reset"], 1)
        self.assertEqual(other.location, self.room1)

    # --- Flavor NPCs (no db.respawn_home until this sweep bootstraps it) ---

    def test_flavor_npc_with_no_respawn_home_gets_bootstrapped_not_moved(self):
        npc = self._make_flavor_npc()
        self.assertIsNone(npc.db.respawn_home)

        result = sweep_and_reset_displaced_npcs()

        self.assertEqual(result["bootstrapped"], 1)
        self.assertEqual(result["reset"], 0)
        self.assertEqual(npc.db.respawn_home, self.room1)
        self.assertEqual(npc.location, self.room1)

    def test_flavor_npc_is_reset_on_a_later_sweep_after_bootstrapping(self):
        npc = self._make_flavor_npc()
        sweep_and_reset_displaced_npcs()  # bootstraps respawn_home = room1

        npc.location = self.room2
        result = sweep_and_reset_displaced_npcs()

        self.assertEqual(result["reset"], 1)
        self.assertEqual(npc.location, self.room1)

    def test_real_player_character_is_never_touched(self):
        # char1/char2 (EvenniaTest fixtures) are plain Characters with
        # no linked account either, in the test harness - simulate a
        # real player by giving one a real account link instead.
        from evennia.accounts.models import AccountDB

        account = AccountDB.objects.create(username="test_player_account")
        self.char1.account = account
        self.char1.location = self.room2

        result = sweep_and_reset_displaced_npcs()

        # Never even considered - no bootstrap, no reset.
        self.assertIsNone(self.char1.db.respawn_home)
        self.assertEqual(self.char1.location, self.room2)

    # --- Wandering NPCs ---

    def test_wandering_npc_inside_its_own_beat_is_left_alone(self):
        from world.colosseum import WanderingNPC

        npc = self._make_flavor_npc()
        npc.scripts.add(WanderingNPC)
        npc.db.wander_rooms = [self.room1, self.room2]
        npc.location = self.room2

        result = sweep_and_reset_displaced_npcs()

        self.assertEqual(result["wandering_reset"], 0)
        self.assertEqual(npc.location, self.room2)

    def test_wandering_npc_pushed_outside_its_beat_is_reset_to_the_first_room(self):
        from world.colosseum import WanderingNPC

        npc = self._make_flavor_npc()
        npc.scripts.add(WanderingNPC)
        npc.db.wander_rooms = [self.room1, self.room2]
        npc.location = self.room1
        # sweep once so nothing bootstraps oddly before the real test move
        sweep_and_reset_displaced_npcs()

        far_room = create.create_object("typeclasses.rooms.Room", key="somewhere else entirely")
        npc.location = far_room

        result = sweep_and_reset_displaced_npcs()

        self.assertEqual(result["wandering_reset"], 1)
        self.assertEqual(npc.location, self.room1)


class TestNPCHomeResetScript(EvenniaTest):
    def test_script_creation_sets_a_real_persistent_interval(self):
        script = create.create_script(NPCHomeResetScript)
        self.assertTrue(script.persistent)
        self.assertEqual(script.interval, RESET_INTERVAL_HOURS * 3600)
        script.stop()
