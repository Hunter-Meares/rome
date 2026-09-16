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


class TestRulesHelpTopic(EvenniaTest):
    """
    A direct request to mirror the website's rules.html page in-game:
    roleplay required, no multiplaying, no cheating, gods (and staff)
    enforce it. Kept as its own topic rather than folded into
    'roleplay', since it also covers ground roleplay quality never
    did - multiplaying, self-dealing, code of conduct, cheating.
    """

    def test_rules_topic_exists(self):
        create_all_help_entries()
        self.assertIsNotNone(HelpEntry.objects.filter(db_key="rules").first())

    def test_rules_topic_covers_multiplaying_and_cheating(self):
        create_all_help_entries()
        text = HelpEntry.objects.get(db_key="rules").db_entrytext.lower()
        self.assertIn("no multiplaying", text)
        self.assertIn("no cheating", text)
        self.assertIn("no self-dealing", text)
        self.assertIn("no metagaming", text)
        self.assertIn("no powergaming", text)

    def test_rules_topic_mentions_divine_and_staff_enforcement(self):
        create_all_help_entries()
        text = HelpEntry.objects.get(db_key="rules").db_entrytext.lower()
        self.assertIn("gods", text)
        self.assertIn("staff", text)

    def test_rules_topic_points_to_roleplay_and_description_topics(self):
        create_all_help_entries()
        text = HelpEntry.objects.get(db_key="rules").db_entrytext.lower()
        self.assertIn("help roleplay", text)
        self.assertIn("help description", text)


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

    def test_description_topic_notes_the_article_is_never_automatic(self):
        """
        Direct follow-up question: does the game insert 'a'/'an' for
        you on sdesc/mask? It doesn't - SdescHandler.add() and
        CmdMask.func() both store the typed text verbatim, no article
        handling at all. Worth stating explicitly rather than leaving
        players to infer it from the examples alone.
        """
        create_all_help_entries()
        entry = HelpEntry.objects.get(db_key="description")
        text = entry.db_entrytext.lower()
        self.assertIn("never adds", text)

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


class TestShortcutsHelpTopic(EvenniaTest):
    """
    Direct follow-up request: point new players at Evennia's own
    built-in 'nick' command for shortening repetitive spell/skill
    commands, since it's easy to not know it exists at all.
    """

    def test_shortcuts_topic_exists_and_mentions_nick(self):
        create_all_help_entries()
        entry = HelpEntry.objects.filter(db_key="shortcuts").first()
        self.assertIsNotNone(entry)
        self.assertIn("nick", entry.db_entrytext.lower())

    def test_newbie_topic_points_to_shortcuts(self):
        create_all_help_entries()
        entry = HelpEntry.objects.get(db_key="newbie")
        self.assertIn("help shortcuts", entry.db_entrytext.lower())


class TestArmorHelpTopic(EvenniaTest):
    """
    Direct player-support request: a single help topic explaining
    class weapon/armor proficiency (CLASS_WEAPON_PROFICIENCIES/
    CLASS_ARMOR_PROFICIENCIES in world/combat.py) and the real
    penalties for going outside it - previously undocumented anywhere,
    despite the mechanic already existing.
    """

    def test_armor_topic_exists_and_mentions_the_penalty_numbers(self):
        create_all_help_entries()
        entry = HelpEntry.objects.filter(db_key="armor").first()
        self.assertIsNotNone(entry)
        self.assertIn("-20 accuracy", entry.db_entrytext)
        self.assertIn("25%", entry.db_entrytext)

    def test_armor_topic_points_to_inspect(self):
        create_all_help_entries()
        entry = HelpEntry.objects.get(db_key="armor")
        self.assertIn("inspect", entry.db_entrytext.lower())

    def test_weapons_and_proficiency_are_aliases_for_armor(self):
        create_all_help_entries()
        entry = HelpEntry.objects.get(db_key="armor")
        alias_list = [a.lower() for a in entry.aliases.all()]
        self.assertIn("weapons", alias_list)
        self.assertIn("proficiency", alias_list)

    def test_rerunning_setup_does_not_create_duplicate_armor_entries(self):
        create_all_help_entries()
        create_all_help_entries()
        self.assertEqual(HelpEntry.objects.filter(db_key="armor").count(), 1)


class TestIndividualRacialAbilityHelpEntries(EvenniaTest):
    """
    Real, confirmed live gap: a player asked in-character how to use
    Boon of the Wilds, and 'help boon of the wilds' matched "Wild Rite
    of Bacchus" (an unrelated cult topic sharing the word "wild")
    instead of anything relevant, since no entry for the ability
    itself existed. Mirrors the existing individual-faction-ability
    help entries exactly, pulled from RACIAL_ABILITIES directly so
    these can't drift from the real mechanics.
    """

    def test_every_racial_ability_gets_its_own_findable_entry(self):
        from world.racial_abilities import RACIAL_ABILITIES

        create_all_help_entries()
        for ability_name in RACIAL_ABILITIES:
            entry = HelpEntry.objects.filter(db_key=ability_name).first()
            self.assertIsNotNone(entry, "no help entry for racial ability %r" % ability_name)

    def test_boon_of_the_wilds_entry_is_the_real_one_not_a_fuzzy_match(self):
        create_all_help_entries()
        entry = HelpEntry.objects.get(db_key="boon of the wilds")
        text = entry.db_entrytext.lower()
        self.assertIn("nymph", text)
        self.assertIn("racial boon of the wilds", text)

    def test_rerunning_setup_does_not_create_duplicate_racial_entries(self):
        """
        Regression guard for the actual bug found while adding this:
        the racial ability keys (and 'racial'/'shortcuts' themselves)
        were missing from managed_keys, the list create_all_help_entries
        clears before regenerating - re-running it would have silently
        piled up duplicate HelpEntry rows for the same key instead of
        replacing them.
        """
        from world.racial_abilities import RACIAL_ABILITIES

        create_all_help_entries()
        create_all_help_entries()
        for ability_name in RACIAL_ABILITIES:
            self.assertEqual(HelpEntry.objects.filter(db_key=ability_name).count(), 1)
        self.assertEqual(HelpEntry.objects.filter(db_key="racial").count(), 1)
        self.assertEqual(HelpEntry.objects.filter(db_key="shortcuts").count(), 1)
