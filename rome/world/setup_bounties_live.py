"""
One-time live setup for the bounty board: places a single BountyBoard
object at the real, already-built "The Rostra" room in the Forum -
the actual historical spot Romans posted public notices, a strong,
already-established anchor for exactly this purpose.

Run once via `evennia shell < world/setup_bounties_live.py`. Not
idempotent - re-running creates a second board.
"""

from evennia.utils import search, create

from world.bounties import BountyBoard

anchors = search.search_object("The Rostra", typeclass="typeclasses.rooms.Room")
if not anchors:
    raise SystemExit("ABORTED: could not find the real 'The Rostra' room live.")
rostra = anchors[0]

board = create.create_object(
    BountyBoard, key="a bounty board", location=rostra
)
board.db.desc = (
    "A weathered wooden board, thick with layers of posted notices - "
    "most of them offering real coin for real, specific problems. "
    "Unlike the Forum's official proclamations elsewhere, nothing "
    "here is signed by any senator. Whoever's willing to actually do "
    "the work gets paid, no questions asked about how."
)

print("Bounty board created at:", rostra.key)
