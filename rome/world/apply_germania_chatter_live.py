"""
One-time live data-fix script: gives every already-spawned Germanic
Stronghold NPC (world/batch_germania_data.py / setup_germania_live.py,
already deployed) real flavor chatter, per direct request ("add the
germanic npcs speaking random flavor phrases"). Mirrors the exact
pattern setup_wall_gate_live.py already used for its own gate guard -
db.chatter_lines + world.colosseum.NPCChatter, spoken in "germanic" via
db.chatter_language so it's routed through process_language and
displayed in that language's own color (see world/languages.py's new
LANGUAGE_COLORS), scrambled for anyone who hasn't learned Germanic.

Applied directly to every live object tagged "germania_npc" rather than
re-running the batch setup script - these NPCs already exist and are
being actively fought/respawned; re-spawning them would be destructive
and pointless. Idempotent: skips any NPC that already has an
NPCChatter script attached, safe to re-run.

Run once, live, as Developer/superuser:

    evennia shell < world/apply_germania_chatter_live.py

Vidrik Storm-Marked (the zone's unique capstone champion) gets his own
distinct, more commanding lines rather than the shared pool - matching
how the Arena Fighters' own gear/loot are already treated as named
individuals rather than interchangeable trash mobs elsewhere in this
game.
"""

from evennia.utils.search import search_object_by_tag

RANK_AND_FILE_LINES = [
    "The wolves taught us to hunt. We taught them to fear us.",
    "Boar-marked or not, this ground is ours.",
    "Ravens don't circle over empty ground.",
    "The storm doesn't ask who's ready.",
    "Rome's walls won't reach this far. Not yet.",
    "Watch the tree line. It watches back.",
    "A warrior who hasn't bled hasn't really fought.",
    "Cross into contested ground and find out who's stronger.",
    "The chieftain sees everything from that hill.",
    "Every season the raiding parties come back with fewer strangers standing.",
]

VIDRIK_LINES = [
    "Every warband here answers to me, in the end.",
    "I've stood this ground longer than most of you have been alive.",
    "Few who reach me turn back. Fewer still walk away after.",
    "Strength that needs shouting isn't strength at all.",
]

applied = 0
skipped = 0

for npc in search_object_by_tag("germania_npc", category="npc_role"):
    if npc.scripts.get("npc_chatter"):
        skipped += 1
        continue

    npc.db.chatter_lines = VIDRIK_LINES if npc.key == "Vidrik Storm-Marked" else RANK_AND_FILE_LINES
    npc.db.chatter_language = "germanic"
    npc.scripts.add("world.colosseum.NPCChatter")
    applied += 1

print("Attached Germanic chatter to %d NPC(s), skipped %d already-chattering." % (applied, skipped))
