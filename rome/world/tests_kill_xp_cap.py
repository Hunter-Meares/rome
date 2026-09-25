"""
Tests for the per-kill XP cap (world/combat.py's KILL_XP_CAP_FRACTION,
CombatRules.kill_xp_cap / award_kill_xp).

The damage-proportional XP split stops pure idling (no damage, no XP)
but not "tagging": nothing accounted for level, so a level 1 landing a
few hits beside a level 100 collected a real share of a reward sized for
the high-level NPC. A contributor's share of one kill is now capped
relative to THEIR OWN level - see the constants' comment for why there
is a floor and why the fraction is what it is.
"""

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

import world.prototypes as prototypes
from world.combat import (
    AutoStatNPC,
    COMBAT_RULES,
    GOLD_PER_XP_DIVISOR,
    KILL_XP_CAP_FLOOR,
)


def _npc(location, xp_reward):
    npc = create.create_object(AutoStatNPC, key="a test brute", location=location)
    npc.db.hp = 0
    npc.db.xp_reward = xp_reward
    return npc


class TestKillXpCapValues(EvenniaTest):
    def test_low_levels_sit_on_the_floor(self):
        self.char1.db.level = 1
        self.assertEqual(COMBAT_RULES.kill_xp_cap(self.char1), KILL_XP_CAP_FLOOR)

    def test_cap_grows_with_the_characters_own_level(self):
        self.char1.db.level = 30
        low = COMBAT_RULES.kill_xp_cap(self.char1)
        self.char1.db.level = 60
        self.assertGreater(COMBAT_RULES.kill_xp_cap(self.char1), low)

    def test_award_kill_xp_pays_a_small_share_in_full(self):
        self.char1.db.level = 1
        self.char1.db.xp = 0
        self.assertEqual(COMBAT_RULES.award_kill_xp(self.char1, 10), 1.0)
        self.assertEqual(self.char1.db.xp, 10)

    def test_award_kill_xp_caps_a_huge_share_and_reports_the_factor(self):
        self.char1.db.level = 1
        self.char1.db.xp = 0
        factor = COMBAT_RULES.award_kill_xp(self.char1, 600)
        self.assertAlmostEqual(factor, KILL_XP_CAP_FLOOR / 600)


class TestLowLevelCannotLeechAHighLevelKill(EvenniaTest):
    """The exact scenario from the design question: a level 1 grouped
    with a level 90 must not collect the level 90's reward."""

    def setUp(self):
        super().setUp()
        self.high, self.low = self.char1, self.char2
        self.high.db.level, self.low.db.level = 90, 1
        for c in (self.high, self.low):
            c.db.xp = 0
            c.db.gold = 0

    def _kill(self, low_dmg, high_dmg, reward=6197):
        npc = _npc(self.room1, reward)
        npc.db.damage_log = {self.high: high_dmg, self.low: low_dmg}
        COMBAT_RULES.at_defeat(npc, attacker=self.high)

    def test_the_low_level_tagger_is_capped_to_a_couple_of_levels_at_most(self):
        self._kill(low_dmg=5, high_dmg=95)  # a 5% share = ~310 XP uncapped
        self.assertLessEqual(self.low.db.level, 3)  # uncapped this was level 4+

    def test_the_high_level_partner_is_untouched(self):
        self._kill(low_dmg=5, high_dmg=95)
        self.assertEqual(self.high.db.xp, int(round(6197 * 0.95)))
        self.assertEqual(self.high.db.level, 90)

    def test_the_taggers_gold_is_reduced_by_the_same_factor(self):
        self._kill(low_dmg=5, high_dmg=95)
        gold_pool = max(1, 6197 // GOLD_PER_XP_DIVISOR)
        self.assertLess(self.low.db.gold, int(round(gold_pool * 0.05)))
        self.assertEqual(self.high.db.gold, int(round(gold_pool * 0.95)))

    def test_pure_idling_still_earns_nothing(self):
        # Unchanged from before the cap: no damage, no share at all.
        npc = _npc(self.room1, 6197)
        npc.db.damage_log = {self.high: 100}
        COMBAT_RULES.at_defeat(npc, attacker=self.high)
        self.assertEqual(self.low.db.xp, 0)
        self.assertEqual(self.low.db.level, 1)


class TestNormalPlayIsUntouched(EvenniaTest):
    def test_an_on_level_solo_kill_is_paid_in_full(self):
        self.char1.db.level = 20
        self.char1.db.xp = 0
        reward = int(COMBAT_RULES.xp_for_level(20) * 0.06)
        npc = _npc(self.room1, reward)
        npc.db.damage_log = {self.char1: 50}
        COMBAT_RULES.at_defeat(npc, attacker=self.char1)
        self.assertEqual(self.char1.db.xp, reward)

    def test_no_xp_paying_npc_in_the_game_is_capped_for_an_on_level_player(self):
        # The data check that justifies the floor and the fraction: if
        # someone adds content that pays more than the cap allows a
        # player of its own level, this names it.
        over = []
        checked = 0
        for name, proto in vars(prototypes).items():
            if not (isinstance(proto, dict) and proto.get("xp_reward") and proto.get("level")):
                continue
            checked += 1
            self.char1.db.level = proto["level"]
            if proto["xp_reward"] > COMBAT_RULES.kill_xp_cap(self.char1):
                over.append((name, proto["level"], proto["xp_reward"]))
        self.assertGreater(checked, 50, "expected to find the game's XP-paying NPC prototypes")
        self.assertEqual(over, [], "these NPCs pay more than an on-level player can receive")
