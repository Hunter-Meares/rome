"""
Housing district - a validated, in-memory description of every room,
exit, NPC, and object before anything touches the live database. Same
pattern as every prior build this session.

Deliberately scoped small per the design discussion: 6 real, distinct
noble domus (not 15 generic ones), each with an actual family and a
real hook, plus a small extension to the Subura's *existing* insula
system for the slum side rather than a whole separate poor district.
No player-ownable housing in this pass - that's a distinct, bigger
future project (see rome_mud_todo.md).

Two attachment points:
- Street of the Patricians attaches to "The Luxury Alley" (#763) via
  its unused "south" exit - a quiet, expensive shopping street is a
  natural approach to a quiet, expensive residential one.
- The second insula building attaches to the Subura's existing
  "Insula Ground Floor" (#2642) via its unused "south" exit.

The 6 domus entrances use the real door system (world/doors.py,
DescriptiveDoor) rather than plain exits - genuine, openable/closable
doors, per the original request. Built by hand in the apply script
(not the generic exit-creation loop) since a working door needs both
sides cross-linked via db.return_exit, which a plain Exit doesn't use.

Run this file directly (`python3 batch_housing_data.py`) to validate
before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


room(
    "patrician_street",
    "Street of the Patricians",
    """|wA quiet, well-swept street|n, a world away from the Subura's crowded noise despite being barely a district over. Blank walls face the road on both sides - Roman domus turn inward, toward their own private courtyards, showing the street nothing but a single formal doorway each. |YA client or two loiters near one entrance|n, waiting for the morning greeting a patron owes them.""",
    "patrician_street",
)

room(
    "domus_aurelia_atrium",
    "Domus Aurelia - Atrium",
    """|YA formal atrium|n, its open roof letting light fall on a shallow catch-basin below. Wax masks of ancestors line one wall in a careful row - a senator's household, and one that wants every visitor to know exactly how long it's been a senator's household. |wCorrespondence sits stacked on a side table|n, several letters conspicuously left half-visible.""",
    "patrician_street",
)

room(
    "domus_aurelia_chamber",
    "Domus Aurelia - Private Study",
    """|wA private study|n, more letters here than in the whole atrium - drafts, discarded ones balled up and not quite thrown away, and at least one addressed to a rival senator in terms too pointed to be entirely diplomatic. |YSenator Aurelius clearly has more enemies than friends in the Curia|n, and seems to be composing a reply to one of them right now.""",
    "patrician_street",
)

room(
    "domus_popillia_atrium",
    "Domus Popillia - Atrium",
    """|YAn atrium decorated with more money than restraint|n - imported marble, gilt fixtures, a fountain doing considerably more than the room strictly needs. Everything here is new, expensive, and slightly too much of it, in the specific way that says the family buying it still remembers not being able to.""",
    "patrician_street",
)

room(
    "domus_popillia_chamber",
    "Domus Popillia - Private Chamber",
    """|wA private sitting room|n, one wall dominated by a large, expensively-commissioned family portrait. |YEvery old aristocratic name in the city has, at some point, declined this family's dinner invitations|n - a fact the portrait's studied confidence doesn't quite manage to hide.""",
    "patrician_street",
)

room(
    "domus_cassia_atrium",
    "Domus Cassia - Atrium",
    """|wAn elegant atrium|n, tastefully appointed, its mistress's reputation considerably less tasteful than the decor. A servant dusting a side table goes very quiet and very focused on the dusting the moment anyone asks about last night.""",
    "patrician_street",
)

room(
    "domus_cassia_chamber",
    "Domus Cassia - Private Chamber",
    """|YA private chamber|n, its furnishings just slightly disordered in a way the household staff have clearly been told, repeatedly, not to remark on. |wCassia's affairs are, technically, a secret|n - which is to say that everyone knows and nobody says so.""",
    "patrician_street",
)

room(
    "domus_fabricia_atrium",
    "Domus Fabricia - Atrium",
    """|wA once-grand atrium|n, kept scrupulously clean but strangely still, as though the household is waiting for something rather than living an ordinary day. A single set of small sandals, long outgrown by whoever wore them, sits by the door exactly where they were left.""",
    "patrician_street",
)

room(
    "domus_fabricia_chamber",
    "Domus Fabricia - The Kept Room",
    """|YA boy's room|n, preserved exactly as it must have looked years ago - toys arranged, bedding made, nothing moved or given away. |wFabricia's son vanished without a trace years past|n, and his mother has never once allowed this room to become anything else.""",
    "patrician_street",
)

room(
    "domus_sempronia_atrium",
    "Domus Sempronia - Atrium",
    """|wA genuinely ancient atrium|n, its family's name older than half the Senate's, its furnishings visibly older than that - patched, mended, and maintained rather than replaced, because replacement isn't really an option anymore. |YThe ancestor masks here outnumber every other family's on the street|n, prestige being the one thing this household still has in real abundance.""",
    "patrician_street",
)

room(
    "domus_sempronia_chamber",
    "Domus Sempronia - Private Chamber",
    """|wA threadbare but immaculately kept private room|n, every surface polished despite there being visibly less to polish than there once was. |YAn old man's pride survives here|n on rather less money than it used to.""",
    "patrician_street",
)

room(
    "domus_licinia_atrium",
    "Domus Licinia - Atrium",
    """|YA warm, well-kept atrium|n, one wall given over entirely to a single framed honor - a household proud enough of it to make sure no visitor could possibly miss it. The rest of the house feels a little quieter than it probably used to.""",
    "patrician_street",
)

room(
    "domus_licinia_chamber",
    "Domus Licinia - Private Chamber",
    """|wA private sitting room|n, kept exactly as tidy as if its usual occupant might walk back in any day - though everyone in the household knows perfectly well she won't, not for years yet, not while her vows hold.""",
    "patrician_street",
)

room(
    "insula2_ground_floor",
    "A Second Insula - Ground Floor",
    """|wAnother cramped entry hall|n, in a building crowded close enough against its neighbor that the Subura's other insula is barely visible past the washing lines strung between them. |YThe stairwell here|n is in marginally better repair than most.""",
    "subura",
)

room(
    "insula2_family_room",
    "A Second Insula - The Herennia Household",
    """|wA single crowded room|n, home to considerably more people than its size suggests it should hold. |YA mother works at mending in the one patch of good light|n, two children underfoot, a third old enough to be out working already. Her husband died on campaign years back; everything since has been managed, somehow, without him.""",
    "subura",
)

ROOM_COUNT_EXPECTED = 15


LINKS = [
    ("existing_luxury_alley", "south", "patrician_street", "north"),
    ("existing_insula_lower_hall", "south", "insula2_ground_floor", "north"),
    ("insula2_ground_floor", "up", "insula2_family_room", "down"),
]

# Domus doors are NOT plain exits - built by hand in the apply script
# using world.doors.DescriptiveDoor (a real, openable/closable door,
# cross-linked via db.return_exit). Listed here as data only, in the
# same (room_a, dir_a, room_b, dir_b) shape as LINKS so the apply
# script and validator can both iterate them uniformly.
DOOR_LINKS = [
    ("patrician_street", "east", "domus_aurelia_atrium", "west"),
    ("domus_aurelia_atrium", "up", "domus_aurelia_chamber", "down"),

    ("patrician_street", "northeast", "domus_popillia_atrium", "southwest"),
    ("domus_popillia_atrium", "up", "domus_popillia_chamber", "down"),

    ("patrician_street", "west", "domus_cassia_atrium", "east"),
    ("domus_cassia_atrium", "up", "domus_cassia_chamber", "down"),

    ("patrician_street", "south", "domus_fabricia_atrium", "north"),
    ("domus_fabricia_atrium", "up", "domus_fabricia_chamber", "down"),

    ("patrician_street", "up", "domus_sempronia_atrium", "down"),
    ("domus_sempronia_atrium", "up", "domus_sempronia_chamber", "down"),

    ("patrician_street", "down", "domus_licinia_atrium", "up"),
    ("domus_licinia_atrium", "north", "domus_licinia_chamber", "south"),
]


NPCS = [
    (
        "domus_aurelia_chamber", "Senator Aurelius", "static",
        "A sharp, unsmiling man drafting correspondence with the "
        "controlled fury of someone composing an insult formal enough "
        "to be technically unimpeachable. He has rivals. He intends to "
        "keep having the last word with all of them.",
        None,
    ),
    (
        "domus_popillia_atrium", "Popillia the Elder", "static",
        "A materfamilias dressed in exactly as much gold as etiquette "
        "will permit, greeting visitors with practiced warmth that "
        "never quite stops watching how they react to the furnishings.",
        None,
    ),
    (
        "domus_cassia_atrium", "Cassia", "static",
        "A striking, self-possessed woman entirely untroubled by "
        "whatever her household staff might be quietly discussing. Her "
        "reputation precedes her into every room; she seems to enjoy "
        "that more than mind it.",
        None,
    ),
    (
        "domus_fabricia_chamber", "Fabricia", "static",
        "A woman who has aged considerably more than the years alone "
        "would explain, sitting quietly in her son's untouched room the "
        "way she apparently does most days. She'll talk about him for "
        "as long as anyone's willing to listen.",
        None,
    ),
    (
        "domus_sempronia_atrium", "an aging patrician", "static",
        "An old man who introduces his family name before his own, "
        "as though the name is doing most of the actual work these "
        "days. Proud, threadbare, and entirely unwilling to acknowledge "
        "either.",
        None,
    ),
    (
        "domus_licinia_atrium", "Licinia's father", "static",
        "A father who mentions his daughter's position at the Temple "
        "of Vesta within the first few sentences of any conversation, "
        "pride and quiet loneliness sitting side by side in exactly "
        "equal measure.",
        None,
    ),
    (
        "patrician_street", "a waiting client", "static",
        "A man in a carefully modest toga, lingering by a patron's door "
        "at an hour that makes clear he's here for the morning "
        "greeting - the old, unbroken custom of a client paying respects "
        "to whoever's wealth and influence he depends on.",
        None,
    ),
    (
        "insula2_family_room", "Herennia", "static",
        "A mother mending clothes in the room's one good patch of "
        "light, two young children playing underfoot and a third old "
        "enough to already be out earning. She lost her husband to a "
        "campaign years ago and has been holding the rest together "
        "since, without much fuss made about it.",
        None,
    ),
]


OBJECTS = [
    (
        "domus_aurelia_atrium", "the ancestor masks",
        "Wax death-masks of the family's forebears, the imagines "
        "maiorum, displayed the way a proud household always displays "
        "them - proof, worn on the wall, of exactly how long this "
        "family has mattered."
    ),
    (
        "domus_sempronia_atrium", "the family's ancestor masks",
        "Rows of wax ancestor masks, more of them than any other house "
        "on the street can claim - the one thing money never had to buy "
        "for this family, and the one thing it can't buy back for "
        "whoever might otherwise have forgotten the name."
    ),
    (
        "domus_licinia_atrium", "the framed honor",
        "A formal document, carefully framed, recording a daughter's "
        "selection as a Vestal Virgin - among the highest honors a "
        "Roman family can receive, and clearly treated as exactly that "
        "in this house."
    ),
]


ECHOES = {
    "patrician_street": [
        "|wA door opens and closes quietly somewhere along the street.|n",
        "|YA client shifts his weight, still waiting to be received.|n",
    ],
}


def _reverse_dir(d):
    pairs = {
        "north": "south", "south": "north",
        "east": "west", "west": "east",
        "up": "down", "down": "up",
        "northeast": "southwest", "southwest": "northeast",
        "northwest": "southeast", "southeast": "northwest",
    }
    return pairs.get(d)


def validate():
    errors = []

    all_keys = set(ROOMS.keys()) | {"existing_luxury_alley", "existing_insula_lower_hall"}

    if len(ROOMS) != ROOM_COUNT_EXPECTED:
        errors.append("Expected %d rooms, got %d" % (ROOM_COUNT_EXPECTED, len(ROOMS)))

    names = [r["name"] for r in ROOMS.values()]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        errors.append("Duplicate room names: %s" % dupes)

    all_links = LINKS + DOOR_LINKS
    for a, da, b, db in all_links:
        if a not in all_keys:
            errors.append("Link references unknown room: %s" % a)
        if b not in all_keys:
            errors.append("Link references unknown room: %s" % b)
        if _reverse_dir(da) is None or _reverse_dir(db) is None:
            errors.append("Unrecognized direction in link %s" % ((a, da, b, db),))

    used_directions = {}
    for a, da, b, db in all_links:
        used_directions.setdefault(a, []).append(da)
        used_directions.setdefault(b, []).append(db)
    for room_key, dirs in used_directions.items():
        seen = set()
        for d in dirs:
            if d in seen:
                errors.append("Room '%s' has a duplicate '%s' exit" % (room_key, d))
            seen.add(d)

    adjacency = {}
    for a, da, b, db in all_links:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    visited = set()
    queue = ["existing_luxury_alley", "existing_insula_lower_hall"]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                queue.append(neighbor)

    unreachable = set(ROOMS.keys()) - visited
    if unreachable:
        errors.append("Unreachable rooms: %s" % unreachable)

    for entry in NPCS:
        room_key = entry[0]
        if room_key not in all_keys:
            errors.append("NPC references unknown room: %s" % room_key)
    for room_key, _, _ in OBJECTS:
        if room_key not in all_keys:
            errors.append("Object references unknown room: %s" % room_key)
    for room_key in ECHOES:
        if room_key not in all_keys:
            errors.append("Echo references unknown room: %s" % room_key)

    return errors


if __name__ == "__main__":
    print("Loaded %d new rooms (attaches to #763 'The Luxury Alley' and #2642 'Insula Ground Floor')." % len(ROOMS))
    print("Loaded %d plain links, %d door links, %d NPCs, %d objects, %d rooms with echoes." % (
        len(LINKS), len(DOOR_LINKS), len(NPCS), len(OBJECTS), len(ECHOES)
    ))
    errs = validate()
    if errs:
        print("\nVALIDATION FAILED (%d errors):" % len(errs))
        for e in errs:
            print(" -", e)
    else:
        print("\nValidation passed: no duplicate names, no exit collisions, "
              "full connectivity, all references resolve.")
