"""
One-time live setup for the faction system: creates the 8 faction
channels and places the 8 induction NPCs in their chosen rooms. Run
once via `evennia shell < world/setup_factions_live.py` after deploying
world/factions.py and the combat.py changes. Safe to re-run - channel
creation is idempotent (ensure_faction_channels_exist skips existing
ones) and NPC placement is guarded by a tag check per room.

Room choices and why:
  - Imperial Legion -> Outer Courtyard (Palatine Hill) - military
    assembly ground, already level-10 gated as part of the whole zone.
  - Praetorian Order -> Praetorian Barracks (Palatine Hill) - a real,
    already-named room, no better fit exists.
  - Hellenic Resistance -> The Back Room (Subura tavern) - secretive,
    right behind Bacchus's public common room for a deliberate contrast.
  - Cult of Mithras -> The Palaestra (Baths) - soldiers' exercise
    ground, brotherhood/camaraderie fits Mithras' historical roots.
  - Orphic Mysteries -> Eastern Niche (Pantheon) - NOT the Underworld's
    Threshold of Return (confirmed live: unreachable by the living,
    see rome_mud_todo.md) - this niche's existing flavor text ("a
    minor god's statue... not the building's main devotion, but not
    forgotten either") already reads like a fringe cult's corner.
  - Cult of Hecate -> A Crooked Junction (Subura) - a literal
    crossroads, Hecate's own mythological domain.
  - Cult of Bacchus -> The Leaking Amphora (Subura tavern) - an actual
    tavern.
  - Collegium Umbrae -> Maintenance Tunnel (Colosseum) - already an
    established hidden passage.
"""

from evennia.utils import search, create

from world.factions import ensure_faction_channels_exist, FactionInductorNPC

created_channels = ensure_faction_channels_exist()
print("Channels created: %s" % [c.key for c in created_channels])

NPC_PLACEMENTS = [
    (
        "imperial_legion",
        "Outer Courtyard",
        "Centurion Gaius Metellus",
        (
            "|wA scarred veteran|n who stands like the vine-wood staff he carries "
            "is load-bearing - spine dead straight, chin level, eyes doing a slow "
            "sweep of the courtyard even mid-conversation. |wHis left hand is "
            "missing two fingers|n, lost to something he's never once explained; "
            "his uniform, decades old by the cut of it, is kept so immaculately "
            "that the omission reads as pride, not neglect. When he speaks it is "
            "in short, complete sentences, as if every word had already passed "
            "inspection."
        ),
    ),
    (
        "praetorian_order",
        "Praetorian Barracks",
        "Prefect Lucius Varro",
        (
            "|wA composed, unhurried man|n in a dress uniform pressed to a knife's "
            "edge, who has the unsettling habit of already knowing the answer to "
            "whatever he's about to ask you. |wHe speaks quietly enough that you "
            "have to lean in|n, which you suspect is entirely the point - it turns "
            "every conversation into something confidential whether you wanted it "
            "to be or not. His eyes move over newcomers the way a clerk checks a "
            "ledger for a discrepancy."
        ),
    ),
    (
        "hellenic_resistance",
        "The Back Room",
        "Nikandros",
        (
            "|wA sun-weathered man|n dressed like any other laborer in the Subura, "
            "which is exactly the point. |wHe is missing his left eye|n, the lid "
            "sewn shut long ago, and favors his right side faintly when he moves. "
            "A thin cord at his throat disappears beneath his tunic - anyone who's "
            "seen it up close says it holds a small bronze medallion, worn smooth, "
            "of a bow and a crescent moon. He listens far more than he talks."
        ),
    ),
    (
        "cult_of_mithras",
        "The Palaestra",
        "Marcus Ferrox",
        (
            "|wA broad, quiet man|n well past his fighting prime, watching the "
            "wrestlers and boxers with the calm of someone who has genuinely seen "
            "it all before. |wA cloak of cured bull-hide|n hangs from his shoulders "
            "despite the heat, and a small tattoo of a bull is visible on his "
            "forearm when he crosses his arms, which is often. He never seems to "
            "raise his voice, and somehow never needs to."
        ),
    ),
    (
        "orphic_mysteries",
        "Eastern Niche",
        "Melantho",
        (
            "|wAn unnervingly still woman|n in ash-grey robes, standing close "
            "enough to the niche's shadowed statue that newcomers sometimes "
            "mistake her for a second one. |wHer eyes rarely blink|n, and seem to "
            "focus on something just past whoever she's looking at. A faint smell "
            "of lily and turned earth follows her, though nothing in the room "
            "explains it. She speaks slowly, as if translating from somewhere "
            "further away than the words suggest."
        ),
    ),
    (
        "cult_of_hecate",
        "A Crooked Junction",
        "Old Trivia",
        (
            "|wA hunched old woman|n who is somehow always standing at the exact "
            "center of the junction no matter which way you approach it. |wA ring "
            "of small iron keys hangs from her belt|n, none of which seem to open "
            "anything nearby, and a black dog sits at her feet that has never once "
            "been seen to bark. She addresses everyone as though she already knows "
            "which of their secrets is worth the most."
        ),
    ),
    (
        "cult_of_bacchus",
        "The Leaking Amphora",
        "Silenus",
        (
            "|wA florid, laughing man|n crowned in wilting ivy, his tunic "
            "permanently wine-stained in a way that looks less like an accident "
            "and more like a uniform. |wGrape leaves are tangled into his beard|n "
            "and he sways gently even when standing still, though he has never "
            "once been seen to actually stumble. He toasts every stranger within "
            "arm's reach as though they were already old friends."
        ),
    ),
    (
        "collegium_umbrae",
        "Maintenance Tunnel",
        "Vespillo",
        (
            "|wA figure who keeps to the tunnel's deepest shadow|n, hood up, face "
            "never quite catching what little light reaches this far down. |wHe "
            "makes no sound at all when he moves|n, and more than one visitor has "
            "sworn he wasn't there a moment before they noticed him. His voice, "
            "when it comes, is flat and unhurried, like a man discussing "
            "paperwork rather than murder."
        ),
    ),
]

for faction_key, room_name, npc_name, desc in NPC_PLACEMENTS:
    rooms = search.search_object(room_name, typeclass="typeclasses.rooms.Room")
    if not rooms:
        print("SKIPPED %s - room '%s' not found" % (npc_name, room_name))
        continue
    room = rooms[0]

    existing = [
        obj for obj in room.contents
        if obj.db.faction == faction_key and obj.is_typeclass(FactionInductorNPC, exact=False)
    ]
    if existing:
        print("SKIPPED %s - inductor already present in %s" % (npc_name, room_name))
        continue

    npc = create.create_object(FactionInductorNPC, key=npc_name, location=room)
    npc.db.desc = desc
    npc.db.faction = faction_key
    print("Placed %s (%s) in %s" % (npc_name, faction_key, room_name))

# Tag an existing NPC as Legion-aligned for Requisition to find. The
# Ludus weapons master is the closest existing "military authority
# figure" already in the game - reusing it rather than creating a
# redundant NPC just to hold one tag.
trainers = search.search_object("weapons master", typeclass="world.combat.SpellSkillTrainer")
if trainers:
    trainers[0].tags.add("legion_aligned", category="npc_role")
    print("Tagged %s as legion_aligned" % trainers[0].key)
else:
    print("WARNING: could not find the Ludus weapons master to tag as legion_aligned")
