"""
The Triumphal Procession - a recurring, ambient "world event."

Every ~3 hours (with jitter so the exact timing can't be learned and
timed around), a captured enemy leader is paraded through Rome along
a route tracing the real historical triumphus: past the Colosseum
(the closest already-built room to where the real triumphal approach
began), through the actual Arch of Titus, the length of the Forum
Romanum, and up the Clivus Capitolinus to the Temple of Jupiter
Optimus Maximus - the genuine historical endpoint. Every room on
PROCESSION_ROUTE below is a real, already-built room in this game,
traced live against the actual room graph, not invented or guessed.

This is pure ambient texture, not a quest or an encounter - closer to
a weather system than a game mechanic. Nothing is lost if a player
misses it, nothing requires them to participate, and there is no
killable captive or lootable object. A genuine "a Legion earns a real
Triumph" system tied to an actual in-game achievement is a real,
much bigger follow-on idea, deliberately out of scope here - see the
TODO at the bottom of this file.

Two real, confirmed bugs from this design's first draft are fixed
here, both hit directly and independently earlier the same day this
was designed:

1. A Script's `db_interval` attribute can be reassigned freely, but
   an already-running Script's ticking task does NOT reschedule
   itself just because that attribute changed - Evennia only ever
   applies `db_interval` when a task is (re)started
   (evennia/scripts/scripts.py's _start_task/_unpause_task). A naive
   `self.interval = new_value` inside at_repeat() silently does
   nothing to the live timer; the jitter would only ever apply once,
   at creation, and every cycle after that would fire at a fully
   fixed, learnable interval - the exact thing jitter exists to
   prevent. Fixed by calling `self.start(interval=new_value)`
   instead, which actually tears down and re-arms the ticking task.

2. Chaining a whole procession as a batch of plain, non-persistent
   `evennia.utils.delay()` calls means a server reload landing
   anywhere in the 8-12 minute window silently and permanently loses
   every remaining step - no closing message, no cleanup, the parade
   just stops. Confirmed the exact same failure mode the same day in
   CombatCharacter._start_turn_with_pacing/_delayed_start_turn
   (world/combat.py) - a real, not hypothetical, risk given Rome
   reloads multiple times a day during active development. Fixed
   with delay(..., persistent=True) - see the note on room IDs below
   for why this passes plain ints, not room objects, through it.
"""

import random

from evennia import Command, DefaultScript
from evennia.objects.models import ObjectDB
from evennia.utils import utils as evennia_utils

INTERVAL_SECONDS = 3 * 3600  # every 3 hours, real-time
JITTER_SECONDS = 600  # +/- 10 minutes, so the exact time isn't learnable
ROOM_HOLD_TIME = 75  # seconds each stop is held before advancing (8 stops = 10 minutes total)
PRE_ANNOUNCE_LEAD_SECONDS = 180  # 3-minute heads-up before the route itself starts moving

# The real, historical triumphal route, mapped onto Rome's actual
# built rooms - traced live against the real room graph (see this
# module's own docstring). Listed as plain integer room IDs rather
# than object references: evennia.utils.delay(persistent=True)'s own
# docs warn that persistent task arguments shouldn't be live memory
# references, so each room is re-resolved fresh, by primary key
# (cheap and unambiguous - not a string-name search), the moment its
# own callback actually fires, rather than being resolved once and
# carried across the persistent-delay boundary.
#
# The Wall & Gate (Porta Flaminia) was considered as a starting point
# and rejected: it's deliberately anachronistic AND faces the wrong
# direction entirely (the road to Germania/Cisalpine Gaul) - a real
# triumph entered from the opposite side of the city, past the Circus
# Maximus. The Meta Sudans is the closest already-built room to that
# real approach, right by the Colosseum.
PROCESSION_ROUTE = [
    658,   # The Meta Sudans - first sighting, by the Colosseum
    671,   # The Arch of Titus - a real, actual triumphal arch
    675,   # The Forum's Threshold - entering the Forum proper
    677,   # The Forum Romanum - Central Plaza - the spectacle's peak
    681,   # Forum Square - Western Edge - turning toward the Capitoline
    751,   # Clivus Capitolinus - the Base of the Climb
    753,   # Clivus Capitolinus - Near the Summit
    1033,  # Main Cella - Jupiter - the historical endpoint
]

# (name, title, flavor_line) - rotates randomly each cycle so the
# event doesn't always land the same emotional beat (defiant /
# dignified / doomed-young / undignified). Deliberately invented
# composites "in the style of" real conquered peoples rather than
# reusing exact historical names (Vercingetorix, Jugurtha, etc.) on
# an endless loop, which would read strangely the tenth time the same
# already-executed historical figure got paraded again.
CAPTIVE_POOL = [
    (
        "Aldric of the Iron Tide", "war-chief of the coastal Germanic tribes",
        "still defiant, spitting toward the crowd whenever a guard gets close",
    ),
    (
        "Vercassus, druid-lord of the Aedui", "a Gallic chieftain",
        "silent, watching the temples on the Capitoline with something unreadable in his face",
    ),
    (
        "Tanit-Baal, prince of Numidia", "a North African royal captive",
        "walking with deliberate dignity, refusing to stumble despite his chains",
    ),
    (
        "Ashur-nadin, satrap of the eastern marches", "an eastern lord",
        "richly dressed despite his captivity, a detail the crowd finds almost more infuriating than his crimes",
    ),
    (
        "Prasutagus the Younger", "a British chieftain's kinsman",
        "young, and clearly aware of exactly what kind of ending this procession is building toward",
    ),
    (
        "Diegis", "a Dacian lieutenant",
        "marked with old sword-scars the crowd shouts about recognizing",
    ),
    (
        "an unnamed grandson of a Pontic king", "a boy, barely of age",
        "and even some of the crowd seem uncertain whether to cheer",
    ),
    (
        "a nameless pirate-king of Cilicia", "a sea-raider",
        "in salt-stained rags, the least dignified of any triumph in memory - and the crowd loves it for exactly that reason",
    ),
]


class TriumphEventScript(DefaultScript):
    """
    Global singleton - registered in server/conf/settings.py's
    GLOBAL_SCRIPTS as "triumph_event", the same pattern already used
    for the wilderness scripts and NPCHomeResetScript. Drives the
    whole procession centrally and pushes messages out to real rooms,
    rather than each room polling independently.
    """

    def at_script_creation(self):
        self.key = "triumph_event"
        self.desc = "A recurring triumphal procession through Rome"
        self.interval = INTERVAL_SECONDS + random.randint(-JITTER_SECONDS, JITTER_SECONDS)
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        # See this module's own docstring, point 1 - a bare attribute
        # assignment here would silently fail to reschedule the
        # already-running task. self.start() is what actually applies
        # a new interval.
        self.start(interval=INTERVAL_SECONDS + random.randint(-JITTER_SECONDS, JITTER_SECONDS))
        self.run_procession()

    def run_procession(self):
        """
        Kicks off one full procession cycle. Public (no leading
        underscore) specifically so a god-only test command
        (CmdTriumphNow below) can trigger it on demand without
        waiting hours - every other systemic feature in this game
        gets some kind of live-test hook, and this needed one too.

        A real, direct request this addresses: the echo ring only
        ever trailed whichever route room was already active, so
        there was no advance warning before the very first stop -
        anyone not already standing there got no heads-up at all.
        Fixed with a short lead-in, sent immediately (not delayed):
        the first route room and its own neighbors get a "word is
        spreading" message PRE_ANNOUNCE_LEAD_SECONDS before the
        procession actually starts moving, giving anyone nearby a
        real chance to get there before it passes. The rest of the
        route is then scheduled starting after that lead time, not
        from zero.
        """
        captive = random.choice(CAPTIVE_POOL)

        first_room = ObjectDB.objects.filter(id=PROCESSION_ROUTE[0]).first()
        if first_room:
            first_room.msg_contents(
                "|xWord spreads that a triumph is approaching the city - "
                "somewhere beyond, trumpets are beginning to sound.|n"
            )
            for exi in first_room.exits:
                neighbor = exi.destination
                if neighbor and neighbor.pk and neighbor.id not in PROCESSION_ROUTE:
                    neighbor.msg_contents(
                        "|xWord spreads that a triumph is approaching the "
                        "city, somewhere nearby.|n"
                    )

        for i, room_id in enumerate(PROCESSION_ROUTE):
            previous_id = PROCESSION_ROUTE[i - 1] if i > 0 else None
            # persistent=True: see this module's own docstring, point
            # 2. Only plain, trivially-serializable data (ints, the
            # captive tuple of strings) crosses this boundary - never
            # a live room/object reference.
            evennia_utils.delay(
                PRE_ANNOUNCE_LEAD_SECONDS + i * ROOM_HOLD_TIME,
                self._advance_to_room,
                room_id, captive,
                previous_id=previous_id,
                persistent=True,
            )

    def _advance_to_room(self, room_id, captive, previous_id=None):
        room = ObjectDB.objects.filter(id=room_id).first()
        if not room:
            return
        name, title, flavor = captive

        room.msg_contents(
            "|Y*** The crowd surges forward as trumpets blare, and the procession "
            "comes into view - legionary standards raised high, the golden "
            "eagle catching the sun. Behind the lictors and the triumphing "
            "general's chariot walks|n %s|Y, %s, in chains, %s. "
            "The crowd roars, some hurling insults, others fruit and stones. "
            "Guards keep a loose ring around the captive, more for show than "
            "necessity - there is nowhere for a chained man to run. ***|n"
            % (name, title, flavor)
        )

        # Echo ring: every room one exit away from the active room,
        # except another room already on the route. Fixed from the
        # first draft, which compared a room's display key against a
        # list of dbref strings (never actually equal, even for a
        # room genuinely on the route, since .key is a display name
        # not a dbref). Comparing real ids against PROCESSION_ROUTE
        # is what actually works.
        for exi in room.exits:
            neighbor = exi.destination
            if neighbor and neighbor.pk and neighbor.id not in PROCESSION_ROUTE:
                neighbor.msg_contents(
                    "|xA roar goes up somewhere nearby - trumpets, and the "
                    "sound of a crowd several streets over. Someone shouts "
                    "that they can see the standards from here. A triumph "
                    "is passing through the city.|n"
                )

        if previous_id is not None:
            previous_room = ObjectDB.objects.filter(id=previous_id).first()
            if previous_room:
                previous_room.msg_contents(
                    "|xThe sound of trumpets and a cheering crowd fades away, "
                    "moving on through the city.|n"
                )


class CmdTriumphNow(Command):
    """
    God-only: force the triumphal procession to start right now.

    Usage:
      triumphnow

    Bypasses the normal ~3-hour timer entirely - for testing the
    route/messages live without waiting. Does not affect or reset the
    script's own regular schedule; the next automatic cycle still
    fires whenever it was already going to.
    """

    key = "triumphnow"
    help_category = "admin"

    def func(self):
        caller = self.caller
        if (caller.db.level or 0) <= 100:
            caller.msg("Only a god may use this.")
            return

        import evennia

        script = getattr(evennia.GLOBAL_SCRIPTS, "triumph_event", None)
        if not script:
            caller.msg("The triumph_event script isn't registered - check GLOBAL_SCRIPTS.")
            return

        script.run_procession()
        caller.msg("Triggered a triumphal procession - watch the route over the next ~10 minutes.")


"""
----------------------------------------------------------------------------
DEPLOYMENT
----------------------------------------------------------------------------
1. Register the script in server/conf/settings.py's GLOBAL_SCRIPTS dict:

    "triumph_event": {
        "typeclass": "world.triumph_event.TriumphEventScript",
        "desc": "A recurring triumphal procession through Rome",
    },

2. Add CmdTriumphNow to a god-reachable cmdset - the same place
   CmdGodLevel/CmdGodSet are added (commands/default_cmdsets.py):

    from world.triumph_event import CmdTriumphNow
    self.add(CmdTriumphNow())

3. evennia reload. GLOBAL_SCRIPTS entries are created automatically
   the first time Evennia boots with a new entry present.
----------------------------------------------------------------------------
TODO / DELIBERATELY OUT OF SCOPE
----------------------------------------------------------------------------
- A genuine "a Legion earns a real Triumph" system, tied to an actual
  in-game campaign or faction achievement rather than a clock, reusing
  most of the message/route machinery above but triggered by a real
  accomplishment. A strong follow-on, but a separate, much bigger
  design effort - keep it that way rather than conflating the two.
- Faction-specific alternate reaction lines (e.g. the Hellenic
  Resistance reacting differently to a Roman military triumph) - cheap
  to add once the base event is confirmed working live, not before.
- The echo ring only reaches rooms one exit away from an active
  PROCESSION_ROUTE stop - by design (matching the original doc's own
  "you don't need every room in the city scripted" reasoning), not
  every room between two consecutive stops gets any message at all.
  Worth a live worldcheck-style sanity pass on the actual exits
  leading off each route room before this ships, in case one of them
  leads somewhere geographically distant enough that "trumpets nearby"
  would read as nonsensical rather than atmospheric.
"""
