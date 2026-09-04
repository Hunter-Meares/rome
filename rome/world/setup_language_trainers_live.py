"""
One-time live setup for the three language trainers Rome already has
a real room for - Germanic has none yet, deliberately, since its
trainer is meant to live at the Germanic settlement once that's
built (see world/languages.py's module docstring).

Placement, not arbitrary:
  - Greek: the already-built "Greek Reading Room" in the Library
    (world/batch_library_data.py) - about as on-the-nose a real match
    as this project has ever had.
  - Egyptian: "The Priest's Chamber" in the Temple of Isis
    (world/batch_campus_martius_data.py) - already an explicitly
    foreign-cult priesthood.
  - Celtic: "The Wing of Foreign Curiosities" in Trajan's Market
    (world/batch_trajan_market_data.py) - a foreign-goods wing, a
    natural home for a Gallic trader who's picked up some Latin but
    still teaches his own tongue on the side.

Run once via `evennia shell < world/setup_language_trainers_live.py`.
Not idempotent - re-running duplicates the NPCs.
"""

from evennia.utils import search, create

from world.languages import LanguageTrainer

PLACEMENTS = [
    (
        "Greek Reading Room", "greek", "a Greek scholar",
        "A wiry, ink-stained man surrounded by scroll cases, "
        "visibly more interested in the texts around him than in "
        "anyone standing in front of him - until asked about the "
        "language itself, at which point he brightens considerably.",
    ),
    (
        "The Priest's Chamber", "egyptian", "a priest of Isis",
        "Shaved-headed and robed in plain white linen, exactly as "
        "this priesthood's own conventions dictate - visibly used to "
        "explaining his goddess's own tongue to curious outsiders, "
        "for a price.",
    ),
    (
        "The Wing of Foreign Curiosities", "celtic", "a Gallic trader",
        "A broad-shouldered trader with a heavy accent even in Latin, "
        "surrounded by goods that clearly didn't come from anywhere "
        "near Rome - willing to teach his own tongue to anyone with "
        "the coin and the patience for it.",
    ),
]

created = 0
for room_name, language, npc_name, desc in PLACEMENTS:
    rooms = search.search_object(room_name, typeclass="typeclasses.rooms.Room")
    if not rooms:
        print("SKIPPED %s trainer - could not find room '%s' live." % (language, room_name))
        continue
    trainer = create.create_object(LanguageTrainer, key=npc_name, location=rooms[0])
    trainer.db.language = language
    trainer.db.desc = desc
    created += 1
    print("Placed %s (%s) in '%s'." % (npc_name, language, room_name))

print("Language trainer setup complete: %d of %d placed." % (created, len(PLACEMENTS)))
