"""
Regression coverage for the achievement-wiring gotcha documented in
CLAUDE.md: 'defining [an achievement] with no matching
track_achievements() call anywhere is dead data that can never
complete (this happened once already this project with 4 of the
original achievements)'.

This is a static, source-scanning check rather than a DB-backed one -
deliberately so, since the actual bug it guards against is a purely
textual mismatch (an achievement dict's category/tracking pair with
no corresponding call site), not a runtime behavior. Plain unittest,
no EvenniaTest/DB needed, matching tests_chargen.py's precedent for
pure-logic checks.
"""

import re
import unittest
from pathlib import Path

import world.achievements as achievements_module

_WORLD_DIR = Path(achievements_module.__file__).parent

# Every achievement dict defined in world/achievements.py has a
# 'category' and 'tracking' field - this is what track_achievements()
# is called with at each real call site. A call site "counts" for an
# achievement if it passes that same (category, tracking) pair.
_CALL_SITE_PATTERN = re.compile(
    r"track_achievements\([^)]*category=[\"']([^\"']+)[\"'][^)]*tracking=[\"']([^\"']+)[\"']",
    re.DOTALL,
)


def _all_achievement_dicts():
    """Every module-level dict in world/achievements.py with a 'key' field."""
    found = []
    for name, value in vars(achievements_module).items():
        if name.startswith("_"):
            continue
        if isinstance(value, dict) and "key" in value and "category" in value:
            found.append((name, value))
    return found


def _all_call_site_pairs():
    """Scans every .py file under world/ for track_achievements() call sites."""
    pairs = set()
    for path in _WORLD_DIR.glob("*.py"):
        text = path.read_text()
        for match in _CALL_SITE_PATTERN.finditer(text):
            pairs.add((match.group(1), match.group(2)))
    return pairs


class TestAchievementWiring(unittest.TestCase):
    def test_at_least_one_achievement_is_defined(self):
        # Guards against this test suite silently checking nothing if
        # achievements.py's dicts are ever restructured away from
        # plain module-level dicts.
        self.assertGreater(len(_all_achievement_dicts()), 0)

    def test_every_achievement_has_a_matching_track_achievements_call_site(self):
        call_sites = _all_call_site_pairs()
        undead_wired = []
        for name, data in _all_achievement_dicts():
            pair = (data["category"], data["tracking"])
            if pair not in call_sites:
                undead_wired.append((name, pair))

        self.assertEqual(
            undead_wired,
            [],
            "Achievement(s) with no matching track_achievements() call site "
            "found anywhere in world/ - this achievement can never complete: "
            "%r" % (undead_wired,),
        )

    def test_every_achievement_dict_has_required_fields(self):
        for name, data in _all_achievement_dicts():
            for field in ("key", "name", "desc", "category", "tracking"):
                self.assertIn(field, data, "%s is missing required field '%s'" % (name, field))
