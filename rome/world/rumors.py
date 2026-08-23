"""
Rumor system

Lets opted-in NPCs (see NPCChatter's tells_rumors flag in
world/colosseum.py) occasionally mention a real, recent player
achievement instead of their own scripted chatter line - "Have you
heard? Marcus just earned First Blood!" This module doesn't track
anything new; it just remembers the last few achievement completions
somewhere NPC chatter can read from. world/achievements.py's
announce_achievements() - the single shared choke point every
track_achievements() call site already routes through - is the one
place that records a rumor, so nothing else has to change to plug in.

Rumors live on a single persistent, unattached global Script rather
than on any one character or room - they aren't about any specific
place, and any NPC anywhere should be able to draw from the same
shared pool.
"""

from random import choice

from evennia.scripts.scripts import DefaultScript
from evennia.utils.search import search_script

MAX_RUMORS = 20
RUMOR_STORE_KEY = "rumor_store"

RUMOR_TEMPLATES = [
    'Have you heard? %s just earned "%s"!',
    'They say %s pulled off "%s" - word travels fast.',
    'Word around the city is %s earned "%s".',
    'Someone was telling me %s managed "%s" - can you believe it?',
]


class RumorStore(DefaultScript):
    """
    Pure storage - no timer, no at_repeat. Just a durable, global
    place to keep the last MAX_RUMORS achievement completions.
    """

    def at_script_creation(self):
        self.key = RUMOR_STORE_KEY
        self.persistent = True
        self.db.rumors = []


def _get_store():
    existing = search_script(RUMOR_STORE_KEY)
    if existing:
        return existing[0]
    from evennia.utils import create

    return create.create_script(RumorStore)


def record_rumor(character_name, achievement_name):
    """
    Called by announce_achievements() whenever something new
    completes. Keeps only the most recent MAX_RUMORS entries - old
    news stops being news.
    """
    store = _get_store()
    rumors = store.db.rumors or []
    rumors.append({"character": character_name, "achievement": achievement_name})
    store.db.rumors = rumors[-MAX_RUMORS:]


def get_random_rumor_line():
    """
    A ready-to-say line about a random recent achievement, or None if
    nothing's been recorded yet. Picking both a random rumor and a
    random template keeps repeat tellings from sounding identical.
    """
    store = _get_store()
    rumors = store.db.rumors or []
    if not rumors:
        return None
    entry = choice(rumors)
    template = choice(RUMOR_TEMPLATES)
    return template % (entry["character"], entry["achievement"])
