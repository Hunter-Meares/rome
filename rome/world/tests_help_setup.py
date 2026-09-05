"""
Regression test for a real bug found live: Evennia's help index always
splits into two separate top-level sections - "Commands" (grouped by
each Command class's own help_category) and "Game & World" (grouped by
each HelpEntry's own db_help_category) - with no dedup between the two
sections at all. Giving a help TOPIC the same category name as a group
of real commands doesn't merge them into one listing; it just prints
that category header a second time, in the other section, which read
to a live player as a broken/duplicated menu ("Combat appears twice
and admin appears twice").

world/help_setup.py used to give the "groupcombat" topic category
"Combat" (28 real commands already use help_category="combat") and the
"godbounty"/"godquest"/"godreligion" topics category "Admin" (11 real
commands already use help_category="admin"). Fixed by moving
groupcombat into the existing "General" bucket (where every other
standalone mechanics topic - gold, trade, achievements - already
lives) and giving the three god-oversight topics their own distinct
"God Commands" category instead.

This test locks in the fix generally: no help TOPIC this project
creates should share a category name (case-insensitively) with any
REAL command's help_category, except "General" - the one bucket both
sides deliberately and extensively share on purpose (18 commands, 15+
topics), which is a broad enough catch-all that sharing it doesn't
read as a mistake the way a narrow category like "Combat" or "Admin"
does.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.help.models import HelpEntry

from world.help_setup import create_all_help_entries
from commands.default_cmdsets import CharacterCmdSet, AccountCmdSet


ALLOWED_SHARED_CATEGORIES = {"general"}


class TestHelpTopicCategoriesDontCollideWithCommandCategories(EvenniaTest):
    def test_no_topic_category_collides_with_a_real_command_category(self):
        cmdset = CharacterCmdSet()
        cmdset.at_cmdset_creation()
        account_cmdset = AccountCmdSet()
        account_cmdset.at_cmdset_creation()

        command_categories = {
            (cmd.help_category or "").strip().lower()
            for cmd in list(cmdset.commands) + list(account_cmdset.commands)
            if getattr(cmd, "help_category", None)
        }

        create_all_help_entries()
        topic_categories = {
            (entry.db_help_category or "").strip().lower()
            for entry in HelpEntry.objects.all()
            if entry.db_help_category
        }

        collisions = (command_categories & topic_categories) - ALLOWED_SHARED_CATEGORIES
        self.assertEqual(
            collisions,
            set(),
            "Help topic categor(y/ies) %s collide with real command "
            "categories - Evennia's help index will show that header "
            "twice (once under Commands, once under Game & World)." % collisions,
        )
