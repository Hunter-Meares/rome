"""
Sends a one-time, automatic welcome letter - in-character, from
Jupiter himself - the moment a brand-new character finishes chargen
and is about to actually start playing. Not sent for an abandoned,
never-finished WIP character - see the call site in
world/character_creator.py's finish_char_callback, which only calls
this from the "chargen genuinely completed" branch.

Deliberately short and mostly a pointer rather than a manual: repeats
none of 'help newbie'/'whatnow''s own content, just tells a new player
those exist. A letter that re-explains every command in detail would
go stale the moment a command is renamed - the same lesson this
project already learned the hard way with help_setup.py's own stale
help-entry count.

Uses the mail contrib's own underlying create_message() call directly
(see evennia.contrib.game_systems.mail.mail.CmdMail.send_mail, which
this mirrors exactly - same create_message() call, same "new"/"mail"
tag) rather than faking a Command instance just to reuse its
self.caller-bound method.
"""

from evennia.utils import create, search

WELCOME_MAIL_SUBJECT = "Welcome to Rome"

WELCOME_MAIL_BODY = (
    "A new soul has entered my city, and so I write to you myself.\n\n"
    "You stand in Rome at the height of its power - or so any citizen "
    "here would tell you; whether or not that's true is a question for "
    "the philosophers. This is a roleplaying game first: speak, act, "
    "and think as your character would, and you will find this city "
    "far richer for it.\n\n"
    "A few things worth knowing right away:\n"
    "  help newbie   - a full walkthrough of what to do first\n"
    "  whatnow       - unsure what to do next? just ask\n"
    "  help          - the complete list of everything you can do\n"
    "  bug / idea / report - we read every one of these, always\n\n"
    "This city is still being built around you. If something feels "
    "broken or unfinished, it very well might be - tell us, and that "
    "is how Rome grows.\n\n"
    "May the gods favor you.\n\n"
    "- Jupiter"
)


def send_welcome_mail(new_character):
    """
    Sends the one-time welcome letter to a brand-new character, from
    Jupiter's own real, live character object - not a flavor-only
    stand-in, so a reply actually reaches a real, monitored inbox
    (matching the MOTD's own zeus@rome.vineyard.haus admin-contact
    convention).

    Deliberately silent and non-fatal if Jupiter can't be found for
    any reason (a future rename, Jupiter's character somehow missing)
    - a missing welcome letter is a real but minor gap; crashing
    chargen completion over it would not be worth it. Never raises.
    """
    matches = search.search_object("Jupiter", typeclass="typeclasses.characters.Character")
    if not matches:
        return
    jupiter = matches[0]

    new_message = create.create_message(
        jupiter, WELCOME_MAIL_BODY, receivers=new_character, header=WELCOME_MAIL_SUBJECT,
    )
    new_message.tags.add("new", category="mail")
