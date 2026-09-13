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


class TestRoleplayHelpTopic(EvenniaTest):
    """
    A real, previously-missing help topic for a roleplay-enforced MUD:
    direct request to state plainly that this isn't just a combat
    sandbox, and that the gods (a literal, staff-controlled mechanic
    here, not an abstraction) may reward good roleplay or punish poor/
    absent roleplay.
    """

    def test_roleplay_topic_exists_with_rp_alias(self):
        create_all_help_entries()
        entry = HelpEntry.objects.filter(db_key="roleplay").first()
        self.assertIsNotNone(entry)
        self.assertIn("rp", [a.strip().lower() for a in entry.aliases.all()])

    def test_roleplay_topic_mentions_reward_and_punishment(self):
        create_all_help_entries()
        entry = HelpEntry.objects.get(db_key="roleplay")
        text = entry.db_entrytext.lower()
        self.assertIn("favor", text)
        self.assertIn("displeasure", text)

    def test_roleplay_topic_points_to_the_description_topic(self):
        create_all_help_entries()
        entry = HelpEntry.objects.get(db_key="roleplay")
        self.assertIn("help description", entry.db_entrytext.lower())


class TestDescriptionHelpTopic(EvenniaTest):
    """
    A dedicated help topic (separate from 'roleplay') explaining the
    real difference between a character's description, sdesc, and
    mask - direct follow-up request once it came up that these three
    are easy to confuse, since 'you can change your sdesc any time too'
    makes mask sound redundant at a glance. The real difference is
    recog persistence: a plain sdesc change never defeats an existing
    recog someone has on you, but mask explicitly does - see
    world/help_setup.py's own content for the full explanation.
    """

    def test_description_topic_exists_with_desc_alias(self):
        create_all_help_entries()
        entry = HelpEntry.objects.filter(db_key="description").first()
        self.assertIsNotNone(entry)
        self.assertIn("desc", [a.strip().lower() for a in entry.aliases.all()])

    def test_description_topic_covers_all_three_concepts_with_examples(self):
        create_all_help_entries()
        entry = HelpEntry.objects.get(db_key="description")
        text = entry.db_entrytext.lower()
        # All three concepts named...
        self.assertIn("setdesc", text)
        self.assertIn("sdesc", text)
        self.assertIn("mask", text)
        # ...each with a real usage example, not just a definition.
        self.assertIn("setdesc a tall, sun-weathered gladiator", text)
        self.assertIn("sdesc a tall, sun-weathered gladiator", text)
        self.assertIn("mask a hooded merchant", text)

    def test_description_topic_documents_the_real_setdesc_command(self):
        """
        Regression guard for a real inaccuracy caught live: an earlier
        draft of this topic claimed there was no self-service way to
        change your description after character creation, missing that
        Evennia's own default 'setdesc' command (locks = cmd:all()) has
        always been open to every player - a real, working command,
        just easy to overlook next to the separate, Builder-locked
        '@desc'. The topic must document the real one, not claim it
        doesn't exist.
        """
        create_all_help_entries()
        entry = HelpEntry.objects.get(db_key="description")
        text = entry.db_entrytext.lower()
        self.assertNotIn("no self-service", text)
        self.assertNotIn("ask a god", text)

    def test_description_topic_explains_why_mask_isnt_just_another_sdesc(self):
        create_all_help_entries()
        entry = HelpEntry.objects.get(db_key="description")
        self.assertIn("recog", entry.db_entrytext.lower())
