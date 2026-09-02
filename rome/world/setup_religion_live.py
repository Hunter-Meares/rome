"""
One-time live setup for religion: creates all 14 religion channels (one
per god in PANTHEON, not just the 4 with a real trigger today - every
god is joinable). Run once via `evennia shell < world/setup_religion_live.py`
after deploying world/religion.py and the combat.py/economy.py hooks.
Safe to re-run - channel creation is idempotent (ensure_religion_channels_exist
skips any that already exist).

No NPC placement needed, unlike factions - prayer happens at a real
room (world/religion.py's PRAYER_SITES / PANTHEON_ALTAR_ROOM), not
through an inductor NPC.
"""

from world.religion import ensure_religion_channels_exist

created_channels = ensure_religion_channels_exist()
print("Channels created: %s" % [c.key for c in created_channels])
