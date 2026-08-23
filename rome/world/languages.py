"""
Languages

Wires Evennia's rplanguage contrib (shipped alongside rpsystem, which
this project already uses for sdesc/mask/recog, but never previously
connected) into actual gameplay: every character has a "currently
speaking" tongue and a list of tongues they actually know. Anyone
hearing speech in a language they don't know gets it back scrambled
via rplanguage's own phonetic-obfuscation engine - real, consistent
nonsense, not just a flat "you don't understand" message.

Five languages are defined below, each with its own phoneme/grammar/
vowel palette so they read as genuinely different languages when
scrambled, not the same noise with a different label. Every character
starts knowing (and speaking) Latin, matching the setting - Greek,
Celtic, Germanic, and Egyptian all have to be learned.

Gods (level 101+) understand everything unconditionally - see
CombatCharacter.process_language in world/combat.py, the actual
listener-side hook. This module only defines the languages and the
player-facing commands for choosing/learning one.

Setup is one-time and idempotent (add_language raises
LanguageExistsError on a language that already exists, which
setup_languages() catches and skips) - run it once, in-game, as
Developer/superuser:

    py from world.languages import setup_languages; setup_languages()

Safe to re-run any time this file changes to add a new language -
existing languages are left untouched unless force-recreated by hand.
"""

from evennia.contrib.rpg.rpsystem import rplanguage
from commands.command import Command

KNOWN_LANGUAGES = ["latin", "greek", "celtic", "germanic", "egyptian"]

DEFAULT_LANGUAGE = "latin"

# Distinct phoneme/grammar/vowel palettes per language, so scrambled
# text actually sounds different language to language rather than
# being the same noise under five different labels. Not aiming for
# linguistic authenticity - just enough flavor to tell them apart at
# a glance, matching what the contrib itself is built for.
_LANGUAGE_DEFS = {
    "latin": dict(
        phonemes="a e i o u an en in on um us t p k b d g m n r s l v qu",
        grammar="cv cvc vcv cvcv cvccv vccv cvcvc",
        vowels="aeiou",
        word_length_variance=1,
    ),
    "greek": dict(
        phonemes="a e i o y th ph ch ps x k t p s n m l r on os es ai oi eu",
        grammar="cv cvc vc cvcc cvcv vcvc cvccv",
        vowels="aeioy",
        word_length_variance=1,
    ),
    "celtic": dict(
        phonemes="a e i o u ll dd bh mh ch sh gh f l n r m b d g th",
        grammar="cv cvc cvcc vcc cvccv vcvc",
        vowels="aeiou",
        word_length_variance=2,
    ),
    "germanic": dict(
        phonemes="a e i o u kt scht zw pf tz ch k t p f r l n m b d g w",
        grammar="cvc cvcc cvccc vcc cvcvc ccvc",
        vowels="aeiou",
        word_length_variance=1,
    ),
    "egyptian": dict(
        phonemes="a i u kh sh th nb sekh ka ba en em het t p k n m r s h",
        grammar="cvc cv vc cvcc ccvc vccv",
        vowels="aiu",
        word_length_variance=2,
    ),
}


def setup_languages():
    """
    Registers all five languages with rplanguage's LanguageHandler.
    Idempotent - already-registered languages are left alone.
    """
    created = []
    skipped = []
    for key, kwargs in _LANGUAGE_DEFS.items():
        try:
            rplanguage.add_language(key=key, **kwargs)
            created.append(key)
        except rplanguage.LanguageExistsError:
            skipped.append(key)
    return created, skipped


class CmdSpeak(Command):
    """
    View or change which language you're currently speaking.

    Usage:
      speak
      speak <language>

    Everything you say, pose, or emote goes out in whichever language
    you're currently speaking. Anyone nearby who doesn't know that
    language hears it scrambled into nonsense (though they can still
    tell roughly which language it was, same as overhearing a real
    unfamiliar tongue). Use 'learnlanguage' to pick up more than the
    Latin every character starts with.
    """

    key = "speak"
    help_category = "social"

    def func(self):
        caller = self.caller
        known = caller.db.known_languages or [DEFAULT_LANGUAGE]

        if not self.args:
            current = caller.db.speaking or DEFAULT_LANGUAGE
            caller.msg(
                "You are currently speaking |w%s|n.\nLanguages you know: %s"
                % (current, ", ".join(known))
            )
            return

        language = self.args.strip().lower()
        if language not in known:
            caller.msg(
                "You don't know how to speak %s. Languages you know: %s"
                % (language, ", ".join(known))
            )
            return

        caller.db.speaking = language
        caller.msg("You are now speaking |w%s|n." % language)


class CmdLearnLanguage(Command):
    """
    Learn a new language.

    Usage:
      learnlanguage <language>

    Available languages: latin, greek, celtic, germanic, egyptian.
    Latin is known from the start - this teaches you one of the rest,
    letting you both speak it (see 'speak') and understand others who
    speak it to you, instead of hearing it scrambled.
    """

    key = "learnlanguage"
    help_category = "social"

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg(
                "Usage: learnlanguage <language>\nAvailable: %s"
                % ", ".join(KNOWN_LANGUAGES)
            )
            return

        language = self.args.strip().lower()
        if language not in KNOWN_LANGUAGES:
            caller.msg(
                "There is no such language to learn. Available: %s"
                % ", ".join(KNOWN_LANGUAGES)
            )
            return

        known = caller.db.known_languages or [DEFAULT_LANGUAGE]
        if language in known:
            caller.msg("You already know %s." % language)
            return

        known.append(language)
        caller.db.known_languages = known
        caller.msg("|gYou have learned %s.|n" % language)


from evennia import CmdSet


class LanguageCmdSet(CmdSet):
    """Language selection/learning commands."""

    key = "Language CmdSet"

    def at_cmdset_creation(self):
        self.add(CmdSpeak())
        self.add(CmdLearnLanguage())
