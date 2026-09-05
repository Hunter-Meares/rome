"""
The Germanic Stronghold - the settlement at the far end of the road
north from Rome, and the post-sewers leveling zone (25-45). A
validated, in-memory description of every room, exit, flavor NPC, and
object before anything touches the live database. Same pattern as
every prior build this session.

Deliberately built to feel like a sprawling collection of distinct
warband camps around a central hall, not a downtown - real Germanic
settlements of this era were dispersed tribal strongholds, not dense
stone cities. Size comes from spread, not density. Wood construction
throughout, not stone - a deliberate, constant visual contrast with
every Roman location built anywhere else in this project.

Combat NPCs (the four warband camps' actual population, and the
Contested Borderlands') are NOT in this file - they're real,
persistent RespawningNPC prototypes (world/prototypes.py's
GERMANIA_* entries) placed by world/setup_germania_live.py directly,
matching the sewer zone's own established pattern exactly. This file
only covers rooms, exits, flavor/named NPCs (the chieftain, the seer,
herders, the smith), and lookable objects.

Run this file directly (`python3 world/batch_germania_data.py`) to
validate before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ======================================================================
# ZONE A - Outer Palisade & Approach (10 rooms)
# ======================================================================

room(
    "palisade_gate",
    "The Palisade Gate",
    """|wA real gate|n, but nothing like Rome's - split logs lashed and pegged rather than dressed stone, standing where the road from the south finally ends. |YTwo guards watch the approach with open, unhidden suspicion|n; nothing here pretends outsiders are welcome by default.""",
    "germania_palisade",
)

room(
    "watchtower_north",
    "Palisade Watchtower - North",
    """|wA log platform|n lashed high into a squared timber frame, reached by a notched log serving as a ladder. |YThe northern reaches of the settlement's own territory|n spread out below - smoke from a dozen cookfires, the dark line of the Sacred Grove further off.""",
    "germania_palisade",
)

room(
    "watchtower_south",
    "Palisade Watchtower - South",
    """|wA matching platform|n on the palisade's other flank, its lookout watching the road south with real, practiced attention. |YFrom up here the wilderness itself looks smaller|n - a reminder of how far this settlement actually sits from anything Roman.""",
    "germania_palisade",
)

room(
    "palisade_walkway",
    "The Palisade Walkway",
    """|wA log walkway|n runs along the palisade's inner face, wide enough for a single warrior to pace it fully armed. |YSpear racks are lashed to the timber at intervals|n - ready, not ceremonial.""",
    "germania_palisade",
)

room(
    "inner_gate_approach",
    "Inner Gate Approach",
    """|wA cleared yard|n just inside the palisade, packed dirt worn smooth by real, constant foot traffic. |YThe settlement itself opens out ahead|n - the first real sense of how much ground this place actually covers.""",
    "germania_palisade",
)

room(
    "settlement_hub",
    "The Settlement Hub",
    """|wA wide, worn crossing point|n, cookfire smoke drifting in from every direction at once. |YPaths branch out toward each of the settlement's own warbands|n, and toward the Great Hall and the Sacred Grove beyond - the closest thing this sprawling place has to a single center.""",
    "germania_palisade",
)

room(
    "path_to_wolfkin",
    "Path Toward the Wolf-kin Camp",
    """|gA worn dirt track|n leads north, wolf pelts and crude wolf-head carvings marking territory well before the camp itself comes into view. |YYounger voices carry on the wind|n - training yells, not yet the seasoned quiet of an older warband.""",
    "germania_palisade",
)

room(
    "path_to_boarmarked",
    "Path Toward the Boar-marked Camp",
    """|gA rougher track|n, boar tusks and hide trophies nailed to trees along its length. |wThe ground here is more heavily trampled|n than the Wolf-kin's own approach - an established camp, not a young one.""",
    "germania_palisade",
)

room(
    "path_to_ravenswatch",
    "Path Toward Raven's Watch",
    """|gA narrower, faster path|n, clearly favoring speed over ease of travel - fitting, for a camp built around scouts and raiders. |YReal raven feathers|n hang from low branches at intervals, unmistakably deliberate.""",
    "germania_palisade",
)

room(
    "path_to_stormcallers",
    "Path Toward the Storm-callers' Camp",
    """|gThe most heavily maintained path|n of the four, wide enough for real numbers to move at once. |wCarved storm-motifs|n mark the way - the chieftain's own elite guard doesn't need subtlety to be taken seriously.""",
    "germania_palisade",
)

ZONE_A_COUNT = 10

# ======================================================================
# ZONE B - The Great Hall / Chieftain's Compound (10 rooms)
# ======================================================================

room(
    "greathall_approach",
    "Great Hall Approach",
    """|wA cleared processional yard|n leads toward the largest timber structure in the entire settlement, its roofline visible over every other building. |YThis is where the settlement's real authority actually lives|n, and the architecture makes sure nobody mistakes that.""",
    "germania_greathall",
)

room(
    "greathall_outer_yard",
    "Outer Compound Yard",
    """|wA working yard|n ringed by smaller outbuildings, warriors and household alike moving through on real business rather than ceremony. |gThe Great Hall's own entrance|n dominates the far side.""",
    "germania_greathall",
)

room(
    "greathall_entrance",
    "The Great Hall Entrance",
    """|wMassive timber doors|n, carved with real, weathered designs - wolves, ravens, storm-spirals, every warband's own mark represented at once. |YThis is a threshold that means something|n, not a formality.""",
    "germania_greathall",
)

room(
    "greathall_feasting_hall",
    "The Feasting Hall",
    """|YThe centerpiece room|n of the entire settlement - long tables, a central hearth-fire that never goes fully cold, smoke-blackened rafters high overhead. |wThis is where the settlement's real social life actually happens|n, feast or no feast.""",
    "germania_greathall",
)

room(
    "greathall_chieftains_chamber",
    "The Chieftain's Chamber",
    """|wA restricted, high-status space|n set apart from the feasting hall's noise. |YThe chieftain himself|n can usually be found here when not presiding over the hall proper - a real, significant figure, not a background NPC.""",
    "germania_greathall",
)

room(
    "greathall_war_council",
    "The War-Council Chamber",
    """|wA map of the wider region|n, carved directly into a broad wooden table, dominates this room. |YThis is where raids and alliances actually get planned|n - a real seat of decision-making, not flavor dressing.""",
    "germania_greathall",
)

room(
    "greathall_weapons_hall",
    "The Weapons Rack Hall",
    """|wRacked spears, axes, and shields|n line every wall, warband gear stored here between real fights. |gThe iron and worked wood smell of a warrior culture that takes its equipment seriously|n.""",
    "germania_greathall",
)

room(
    "greathall_guest_chamber",
    "Chamber for Honored Guests",
    """|wA side chamber|n, better appointed than most of the settlement, clearly meant for anyone the chieftain has decided to actually welcome. |YA rare, real acknowledgment|n that not every outsider here is automatically an intruder.""",
    "germania_greathall",
)

room(
    "greathall_family_quarters",
    "The Chieftain's Family Quarters",
    """|wA private living space|n, warmer and more lived-in than the hall's public rooms. |gReal domestic life|n continues here regardless of whatever politics occupy the war-council chamber.""",
    "germania_greathall",
)

room(
    "greathall_storage_cellar",
    "The Storage Cellar",
    """|wA cool, below-ground room|n, mead casks and grain sacks and tribute goods stacked with real care. |YThe settlement's own wealth|n, kept plain and unglamorous rather than displayed.""",
    "germania_greathall",
)

ZONE_B_COUNT = 10

# ======================================================================
# ZONE H - Livestock & Farmstead (8 rooms) - branches off Great Hall
# ======================================================================

room(
    "farmstead_rear_exit",
    "The Compound's Rear Exit",
    """|wA plain timber door|n at the Great Hall compound's back, opening onto ordinary, working ground rather than anything ceremonial. |gThe settlement's quieter, domestic side|n starts here.""",
    "germania_farmstead",
)

room(
    "farmstead_pasture_a",
    "Pasture - East",
    """|gOpen grazing ground|n, real livestock moving unhurried across it. |wNothing about this stretch of the settlement is martial in the slightest|n - a deliberate, grounding contrast.""",
    "germania_farmstead",
)

room(
    "farmstead_pasture_b",
    "Pasture - West",
    """|gA second pasture|n, quieter still, bordered by a low fence of stacked timber. |YOrdinary life|n, continuing regardless of whatever the warbands are doing elsewhere.""",
    "germania_farmstead",
)

room(
    "farmstead_livestock_pen",
    "The Livestock Pen",
    """|wA fenced pen|n holding the settlement's real working animals, penned close for the night rather than left to range. |gThe smell is honest and unglamorous|n - a farm, not a battlefield.""",
    "germania_farmstead",
)

room(
    "farmstead_house",
    "A Modest Farmstead",
    """|wA real, lived-in timber house|n, smaller and plainer than anything in the Great Hall compound. |YA farming family|n calls this home, entirely unconcerned with warband politics.""",
    "germania_farmstead",
)

room(
    "farmstead_grain_store",
    "The Grain Store",
    """|wA raised timber structure|n, built up off the ground to keep the grain inside dry and safe from vermin. |gA real, practical piece of engineering|n, unglamorous but essential.""",
    "germania_farmstead",
)

room(
    "farmstead_well",
    "The Settlement Well",
    """|wA deep, stone-lined well|n - the one piece of real stonework anywhere in the entire settlement, imported knowledge rather than local practice. |YWater here is serious business|n, this far from any real river.""",
    "germania_farmstead",
)

room(
    "farmstead_path",
    "Farmstead Path",
    """|gA quiet dirt path|n connecting the farmstead's scattered buildings, worn by years of ordinary foot traffic rather than warband marching. |wNothing here is in any particular hurry|n.""",
    "germania_farmstead",
)

ZONE_H_COUNT = 8

# ======================================================================
# ZONE I - Craft & Smithy Area (6 rooms) - branches off Great Hall
# ======================================================================

room(
    "smithy_approach",
    "Approach to the Smithy",
    """|rThe smell of hot iron|n reaches this stretch of path well before the smithy itself comes into view. |wReal, constant hammering|n carries from somewhere ahead.""",
    "germania_smithy",
)

room(
    "smithy_forge",
    "The Smithy Forge",
    """|rA real working forge|n, coals banked and glowing, tools hung within easy reach of a smith who clearly knows exactly where everything is without looking. |YThis is where the warbands' actual weapons get made|n.""",
    "germania_smithy",
)

room(
    "smithy_stall",
    "The Weaponsmith's Stall",
    """|wFinished weapons and armor|n laid out for trade rather than war - axes, seaxes, spears, shields, mail and leather, all genuinely Germanic in make. |gReal goods, real prices|n, not Roman imitations.""",
    "germania_smithy",
)

room(
    "smithy_tannery",
    "The Tannery",
    """|rA sharp, unpleasant smell|n hangs over this stretch - hides stretched and worked into real leather, an unglamorous but necessary trade. |wNobody lingers here longer than they have to|n.""",
    "germania_smithy",
)

room(
    "smithy_woodworkers_yard",
    "The Woodworker's Yard",
    """|wSpear shafts and shield frames|n in every stage of completion litter this open yard. |gReal, patient craft work|n - the kind that rarely gets noticed until it fails in a fight.""",
    "germania_smithy",
)

room(
    "smithy_path",
    "Smithy Path",
    """|gA short connecting path|n, wood shavings and metal filings ground into the dirt underfoot from years of use. |wThe craft quarter's own quiet, practical rhythm|n continues regardless of anything else happening in the settlement.""",
    "germania_smithy",
)

ZONE_I_COUNT = 6

# ======================================================================
# ZONE G - Sacred Grove (8 rooms) - branches off the settlement hub
# ======================================================================

room(
    "grove_edge",
    "The Grove's Edge",
    """|GThe tone shifts here|n, quieter and older-feeling than anything else in the settlement. |wNo warband marks this ground|n - a different kind of authority holds it instead.""",
    "germania_grove",
)

room(
    "grove_ancient_trees",
    "A Ring of Ancient Trees",
    """|GTrees far older than the settlement itself|n stand in a rough, deliberate ring. |wSomething about their arrangement is clearly not accidental|n, even to an outsider who couldn't say exactly why.""",
    "germania_grove",
)

room(
    "grove_sacrificial_site",
    "A Sacrificial Site",
    """|wA plain stone altar|n, weathered and old, set at the grove's own quiet center. |gHandled here with the same restraint the subject deserves|n - evocative, not graphic; a real, somber place rather than a spectacle.""",
    "germania_grove",
)

room(
    "grove_rune_stone",
    "A Rune-Marked Stone",
    """|wA standing stone|n, real runes cut deep enough to have survived real weather for real generations. |YWhat they actually say|n is known to vanishingly few people still living.""",
    "germania_grove",
)

room(
    "grove_seers_dwelling",
    "The Seer's Dwelling",
    """|wA modest hut|n, set apart even from the rest of the grove. |YThe settlement's seer|n lives here - genuinely different in role from any Roman priest, closer to prophecy and nature-reading than formal state ritual.""",
    "germania_grove",
)

room(
    "grove_spring",
    "A Quiet Spring",
    """|cClear water|n rises from the ground here, genuinely cold even in warm weather. |wA real, trusted source|n, treated with real quiet respect by anyone who actually lives here.""",
    "germania_grove",
)

room(
    "grove_gathering_clearing",
    "A Gathering Clearing",
    """|GAn open clearing|n, clearly used for real tribal rites - the ground shows real, repeated wear in a rough circle. |wNothing is happening here right now|n, but the space still carries real weight.""",
    "germania_grove",
)

room(
    "grove_deepest_point",
    "The Grove's Deepest Point",
    """|GThe most sacred, most restricted ground|n in the entire settlement. |wEven the seer approaches this place with real, visible care|n - whatever's actually here, it isn't treated lightly by anyone who understands it.""",
    "germania_grove",
)

ZONE_G_COUNT = 8

ROOM_COUNT_A_THROUGH_I_AND_G = (
    ZONE_A_COUNT + ZONE_B_COUNT + ZONE_H_COUNT + ZONE_I_COUNT + ZONE_G_COUNT
)

# ======================================================================
# ZONE C - Warband Camp: The Wolf-kin (15 rooms, levels 27-31)
# Younger, less experienced fighters - a natural, lower-stakes first
# camp. Real combat NPCs (world/prototypes.py's GERMANIA_WOLFKIN_*)
# are placed by setup_germania_live.py, not listed in this file.
# ======================================================================

room(
    "wk_entrance",
    "Wolf-kin Camp - Entrance",
    """|wA loose ring of huts|n comes into view, wolf pelts and crude totem-carvings marking every entrance. |YYounger warriors move through openly|n, none of them bothering to hide how new most of this still is to them.""",
    "germania_wolfkin",
)

room(
    "wk_perimeter",
    "Wolf-kin Perimeter",
    """|gA loosely-marked boundary|n, staked wolf skulls standing in for a real wall this young a warband hasn't gotten around to building yet. |wEnthusiasm substitutes for real fortification here|n, for now.""",
    "germania_wolfkin",
)

room(
    "wk_sleeping_a",
    "Wolf-kin Sleeping Quarters - East",
    """|wA cluster of small huts|n, sleeping furs visible through open doorways. |gNothing here is especially comfortable|n - a young warband's own priorities are visibly elsewhere.""",
    "germania_wolfkin",
)

room(
    "wk_sleeping_b",
    "Wolf-kin Sleeping Quarters - West",
    """|wA second cluster of huts|n, functionally identical to the first. |YReal wolf-tooth necklaces|n hang from several doorposts - earned, not decorative.""",
    "germania_wolfkin",
)

room(
    "wk_training_yard",
    "Wolf-kin Training Yard",
    """|wAn open, well-trampled yard|n, real drilling happening in real time - footwork, formation, the unglamorous basics every warrior actually needs. |gLoud, energetic, and genuinely earnest|n.""",
    "germania_wolfkin",
)

room(
    "wk_practice_ground",
    "Wolf-kin Weapon-Practice Ground",
    """|wWooden practice weapons|n lean against a rack near a row of battered training posts. |YThe posts show real, heavy wear|n - whatever else is true of this camp, nobody's slacking on the fundamentals.""",
    "germania_wolfkin",
)

room(
    "wk_cookfire",
    "Wolf-kin Cookfire Circle",
    """|rA real cookfire|n burns at the camp's own social center, warriors trading loud stories that are probably at least half true. |wThe mood here is genuinely lighter|n than anywhere else in the settlement's warband territory.""",
    "germania_wolfkin",
)

room(
    "wk_leader_hut",
    "Hut of the Wolf-kin's War-Leader",
    """|wA slightly larger hut|n, marking whoever actually leads this young warband. |YReal responsibility|n sits on shoulders that, honestly, still look a little young for it.""",
    "germania_wolfkin",
)

room(
    "wk_supply_hut",
    "Wolf-kin Supply Hut",
    """|wSpare gear and rations|n stored with more enthusiasm than real organization. |gA young warband's own logistics|n, still genuinely finding its footing.""",
    "germania_wolfkin",
)

room(
    "wk_sparring_ring",
    "Wolf-kin Sparring Ring",
    """|wA circle marked in the dirt|n, real bruises handed out freely and without much real grudge afterward. |YThis is where reputations inside the camp actually get made|n.""",
    "germania_wolfkin",
)

room(
    "wk_totem",
    "The Wolf-kin's Totem Post",
    """|wA tall post|n, a real, carved wolf's head crowning it, younger trophies tied on below. |YThe camp's whole identity|n is staked, quite literally, right here.""",
    "germania_wolfkin",
)

room(
    "wk_path_a",
    "Wolf-kin Camp Path - North",
    """|gA worn path|n connecting the camp's scattered huts. |wReal, constant foot traffic|n has worn it down further than the surrounding ground.""",
    "germania_wolfkin",
)

room(
    "wk_path_b",
    "Wolf-kin Camp Path - South",
    """|gA second connecting path|n, running the camp's other length. |wYoung voices|n carry from every direction at once.""",
    "germania_wolfkin",
)

room(
    "wk_lookout",
    "Wolf-kin Lookout Point",
    """|wA raised platform|n, more improvised than the palisade's own real watchtowers. |YStill, someone's always actually posted here|n - enthusiasm again standing in for real polish.""",
    "germania_wolfkin",
)

room(
    "wk_edge",
    "The Wolf-kin Camp's Far Edge",
    """|gThe camp thins out here|n, huts giving way to open ground before the Boar-marked's own territory begins. |wA real, if informal, boundary|n between the settlement's two youngest and most established warbands.""",
    "germania_wolfkin",
)

ZONE_C_COUNT = 15

# ======================================================================
# ZONE D - Warband Camp: The Boar-marked (15 rooms, levels 31-35)
# A rougher, more established band - real fights, not training gear.
# ======================================================================

room(
    "bm_entrance",
    "Boar-marked Camp - Entrance",
    """|wReal boar tusks|n, dozens of them, mark this camp's own entrance - trophies from real fights, not training exercises. |YEverything here reads more battle-worn|n than the Wolf-kin's own territory.""",
    "germania_boarmarked",
)

room(
    "bm_perimeter",
    "Boar-marked Perimeter",
    """|wA real, if simple, log barrier|n rings this camp - more fortification than the Wolf-kin bothered with. |gAn established warband protects what it's actually built|n.""",
    "germania_boarmarked",
)

room(
    "bm_sleeping_a",
    "Boar-marked Sleeping Quarters - East",
    """|wSturdier huts|n than the Wolf-kin's own, real scars and real trophies visible on more than a few of their occupants' gear stacked outside. |YThis is a warband that's actually been tested|n.""",
    "germania_boarmarked",
)

room(
    "bm_sleeping_b",
    "Boar-marked Sleeping Quarters - West",
    """|wA second row of huts|n, boar hides stretched and drying over several of them. |gReal, hard-won comfort|n, not luxury.""",
    "germania_boarmarked",
)

room(
    "bm_training_yard",
    "Boar-marked Training Yard",
    """|wA yard that's seen real use|n, the ground churned deep by real weight behind real blows. |YTraining here looks less like drilling and more like actual sparring|n.""",
    "germania_boarmarked",
)

room(
    "bm_practice_ground",
    "Boar-marked Weapon-Practice Ground",
    """|wReal weapons|n, not wooden substitutes, get used here more often than is strictly safe. |gAn established warband's own confidence|n, worn openly.""",
    "germania_boarmarked",
)

room(
    "bm_cookfire",
    "Boar-marked Cookfire Circle",
    """|rA real cookfire|n, boar meat roasting more often than not. |YStories traded here|n carry more real weight than the Wolf-kin's - these warriors have actually earned most of them.""",
    "germania_boarmarked",
)

room(
    "bm_leader_hut",
    "Hut of the Boar-marked's War-Leader",
    """|wA well-built hut|n, real trophies from real victories displayed without much modesty. |YWhoever leads this camp|n has clearly earned the position the hard way.""",
    "germania_boarmarked",
)

room(
    "bm_supply_hut",
    "Boar-marked Supply Hut",
    """|wReal, well-organized stores|n - an established warband that's learned logistics matters as much as raw strength. |gA genuine contrast|n to the Wolf-kin's own looser arrangement.""",
    "germania_boarmarked",
)

room(
    "bm_trophy_display",
    "Boar-marked Trophy Display",
    """|wReal trophies|n from real fights line this open space - tusks, weapons, the odd piece of foreign gear taken from somewhere else entirely. |YA genuine record|n of this warband's own history.""",
    "germania_boarmarked",
)

room(
    "bm_totem",
    "The Boar-marked's Totem Post",
    """|wA tall post|n crowned with a real boar's skull, older trophies layered thick beneath it. |YThis camp's own identity|n, worn with real, earned confidence.""",
    "germania_boarmarked",
)

room(
    "bm_path_a",
    "Boar-marked Camp Path - North",
    """|gA well-worn path|n, packed hard by years of real use. |wThe ground itself remembers this warband's own weight|n.""",
    "germania_boarmarked",
)

room(
    "bm_path_b",
    "Boar-marked Camp Path - South",
    """|gA second path|n, running the camp's other length. |wReal, heavier footsteps|n than the Wolf-kin's own territory.""",
    "germania_boarmarked",
)

room(
    "bm_sparring_ring",
    "Boar-marked Sparring Ring",
    """|wA real sparring circle|n, the bruises handed out here carry genuine weight behind them. |YReputation matters more openly here|n than in the Wolf-kin's own younger camp.""",
    "germania_boarmarked",
)

room(
    "bm_edge",
    "The Boar-marked Camp's Far Edge",
    """|gThe camp thins toward Raven's Watch's own territory|n from here, huts giving way to open, contested ground. |wA real, informal boundary|n between two very differently-built warbands.""",
    "germania_boarmarked",
)

ZONE_D_COUNT = 15

# ======================================================================
# ZONE E - Warband Camp: Raven's Watch (15 rooms, levels 35-39)
# Scouts and raiders - leaner, faster warriors, a distinct camp
# identity from the two brawler-heavy bands before it.
# ======================================================================

room(
    "rw_entrance",
    "Raven's Watch - Entrance",
    """|wReal raven feathers|n hang everywhere, a genuinely different aesthetic from either warband before it. |YThe warriors here move differently too|n - leaner, quicker, built for covering ground rather than holding it.""",
    "germania_ravenswatch",
)

room(
    "rw_perimeter",
    "Raven's Watch Perimeter",
    """|wNo real wall here at all|n - this camp trusts its own mobility over fixed defenses. |gReal scouts|n watch the approaches instead, which suits this warband's whole identity.""",
    "germania_ravenswatch",
)

room(
    "rw_sleeping_a",
    "Raven's Watch Sleeping Quarters - East",
    """|wSpare, practical shelters|n, built for warriors who spend real time away from camp entirely. |YLittle here is permanent|n - deliberately.""",
    "germania_ravenswatch",
)

room(
    "rw_sleeping_b",
    "Raven's Watch Sleeping Quarters - West",
    """|wA second row of the same lean shelters|n. |gComfort clearly isn't this warband's own priority|n - readiness is.""",
    "germania_ravenswatch",
)

room(
    "rw_training_yard",
    "Raven's Watch Training Yard",
    """|wAn open space|n, but the drilling here looks nothing like the Boar-marked's own brawling - real footwork, real feints, genuine speed over raw power. |YA different kind of warrior entirely|n.""",
    "germania_ravenswatch",
)

room(
    "rw_practice_ground",
    "Raven's Watch Weapon-Practice Ground",
    """|wLight blades and real thrown weapons|n dominate here, rather than the heavier gear favored elsewhere in the settlement. |gSpeed over weight|n, consistently.""",
    "germania_ravenswatch",
)

room(
    "rw_cookfire",
    "Raven's Watch Cookfire Circle",
    """|rA smaller, quieter fire|n than either brawler-camp's own - fewer warriors present at any given moment, most of them genuinely out working. |wThe mood here is watchful|n, not relaxed.""",
    "germania_ravenswatch",
)

room(
    "rw_leader_hut",
    "Hut of Raven's Watch's War-Leader",
    """|wA lean, practical shelter|n, real maps and route-markings visible inside rather than trophies. |YThis leader's own authority|n rests on knowledge of the land, not raw strength.""",
    "germania_ravenswatch",
)

room(
    "rw_supply_hut",
    "Raven's Watch Supply Hut",
    """|wLight, portable gear|n stored for fast deployment - little here is meant to sit still for long. |gA scout warband's own real logistics|n.""",
    "germania_ravenswatch",
)

room(
    "rw_sparring_ring",
    "Raven's Watch Sparring Ring",
    """|wA real sparring space|n, but the bouts here favor speed and real precision over brute force. |YWatching one|n is genuinely different from watching the Boar-marked's own matches.""",
    "germania_ravenswatch",
)

room(
    "rw_totem",
    "Raven's Watch Totem Post",
    """|wA tall post|n, real raven feathers and route-markers tied on rather than trophies of raw strength. |YThis camp's own identity|n is built on knowing the ground better than anyone else.""",
    "germania_ravenswatch",
)

room(
    "rw_path_a",
    "Raven's Watch Camp Path - North",
    """|gA narrow, fast path|n, worn thin rather than wide - warriors here move quickly and don't linger. |wReal purpose|n in every set of footprints.""",
    "germania_ravenswatch",
)

room(
    "rw_path_b",
    "Raven's Watch Camp Path - South",
    """|gA second narrow path|n, running the camp's other length. |wThe same quick, purposeful traffic|n as everywhere else in this warband's territory.""",
    "germania_ravenswatch",
)

room(
    "rw_lookout",
    "Raven's Watch Lookout Point",
    """|wA genuinely excellent vantage point|n - this camp's own specialty on full display. |YReal visibility|n over a wide stretch of the settlement's surrounding territory.""",
    "germania_ravenswatch",
)

room(
    "rw_edge",
    "Raven's Watch Camp's Far Edge",
    """|gThe camp thins toward the Storm-callers' own territory|n from here. |wA real, informal boundary|n between the settlement's scouts and its chieftain's own elite guard.""",
    "germania_ravenswatch",
)

ZONE_E_COUNT = 15

# ======================================================================
# ZONE F - Warband Camp: The Storm-callers (15 rooms, levels 39-43)
# The chieftain's own elite guard - the smallest, most heavily
# defended and decorated of the four camps, deliberately fewer
# warriors than the others but individually far more dangerous.
# Culminates at the unique named champion (level 45-46).
# ======================================================================

room(
    "sc_entrance",
    "The Storm-callers - Entrance",
    """|wReal, deliberate craftsmanship|n marks this camp's own entrance - carved storm-spirals, weapons and armor visibly better-made than anywhere else in the settlement. |YThis is where the chieftain's own trust actually lives|n.""",
    "germania_stormcallers",
)

room(
    "sc_perimeter",
    "Storm-callers' Perimeter",
    """|wA real, well-built barrier|n, the most heavily defended boundary of any warband camp in the settlement. |gFewer warriors guard it|n than at the Wolf-kin's own perimeter - they don't need more.""",
    "germania_stormcallers",
)

room(
    "sc_sleeping_a",
    "Storm-callers' Quarters - East",
    """|wReal, well-built shelters|n, genuinely comfortable by this settlement's standards. |YEarned privilege|n, not softness.""",
    "germania_stormcallers",
)

room(
    "sc_sleeping_b",
    "Storm-callers' Quarters - West",
    """|wA second row of the same well-built shelters|n. |gReal, fine craftsmanship|n on display in every visible detail.""",
    "germania_stormcallers",
)

room(
    "sc_training_yard",
    "Storm-callers' Training Yard",
    """|wA smaller yard|n than either brawler-camp's own, but the intensity here is genuinely different - real, controlled, dangerous precision. |YNothing here looks like practice for its own sake|n.""",
    "germania_stormcallers",
)

room(
    "sc_practice_ground",
    "Storm-callers' Weapon-Practice Ground",
    """|wThe finest weapons|n in the entire settlement rest here between real use. |gReal mastery|n, not raw enthusiasm or raw strength alone.""",
    "germania_stormcallers",
)

room(
    "sc_cookfire",
    "Storm-callers' Cookfire",
    """|rA small, quiet fire|n - the smallest warband in the settlement, and it shows. |YFewer voices|n, but real, unmistakable confidence in every one of them.""",
    "germania_stormcallers",
)

room(
    "sc_leader_hut",
    "Hut of the Storm-callers' Champion",
    """|wThe finest shelter|n of any warband leader in the settlement - real, earned status made visible. |YThis is where the chieftain's own champion actually rests|n between real fights.""",
    "germania_stormcallers",
)

room(
    "sc_supply_hut",
    "Storm-callers' Supply Hut",
    """|wReal, meticulously kept stores|n - nothing here is left to chance the way a younger warband might risk. |gElite discipline|n, extended to logistics too.""",
    "germania_stormcallers",
)

room(
    "sc_trophy_hall",
    "Storm-callers' Trophy Hall",
    """|wThe finest trophies|n in the entire settlement, real gear and real weapons taken from real, significant fights. |YA genuine record|n of exactly why this warband is trusted the way it is.""",
    "germania_stormcallers",
)

room(
    "sc_totem",
    "The Storm-callers' Totem Post",
    """|wA tall, real storm-spiral carved deep into old wood|n, weathered by real seasons. |YThe chieftain's own authority|n is reflected directly in this warband's identity.""",
    "germania_stormcallers",
)

room(
    "sc_path_a",
    "Storm-callers' Camp Path - North",
    """|gA well-maintained path|n, real care evident even in something this small. |wElite discipline extends to everything|n, apparently, even the footpaths.""",
    "germania_stormcallers",
)

room(
    "sc_path_b",
    "Storm-callers' Camp Path - South",
    """|gA second well-maintained path|n, running the camp's other length. |wThe same real, quiet discipline|n throughout.""",
    "germania_stormcallers",
)

room(
    "sc_sparring_ring",
    "Storm-callers' Sparring Ring",
    """|wA real sparring ground|n, but bouts here are dangerous in a way the other camps' own matches aren't. |YThis is where the settlement's actual best warriors test each other|n.""",
    "germania_stormcallers",
)

room(
    "sc_champions_ground",
    "The Champion's Ground",
    """|YThe Storm-callers' own capstone|n - a cleared, deliberate space where the chieftain's champion is genuinely, dangerously strongest. |wFew who come this far turn back|n, and fewer still walk away from what actually waits here.""",
    "germania_stormcallers",
)

ZONE_F_COUNT = 15

# ======================================================================
# ZONE K - Contested Borderlands (13 rooms, levels 41-45)
# The roughest, most dangerous standard content in the settlement,
# territory actively fought over - setting up the Storm-callers' own
# unique champion as the settlement's genuine capstone encounter.
# ======================================================================

room(
    "borderlands_entrance",
    "Contested Borderlands - Entrance",
    """|rThe ground here has changed hands more than once|n, real scorch marks and broken weapons half-buried in the dirt as proof. |YNothing about this stretch of territory is settled|n.""",
    "germania_borderlands",
)

room(
    "borderlands_burned_camp",
    "A Burned-Out Camp",
    """|rReal fire damage|n, old but unmistakable, marks what was once somebody's real camp. |wNobody's rebuilt here since|n - telling, in territory this actively contested.""",
    "germania_borderlands",
)

room(
    "borderlands_ambush_ground",
    "Ambush Ground",
    """|gDense cover|n on every side makes this exact stretch a genuinely dangerous place to walk carelessly. |YReal raiding parties|n favor exactly this kind of ground.""",
    "germania_borderlands",
)

room(
    "borderlands_ridge",
    "The Contested Ridge",
    """|wA real vantage point|n, fought over specifically because of what it overlooks. |YWhoever holds this ridge|n controls real, meaningful ground.""",
    "germania_borderlands",
)

room(
    "borderlands_old_battlefield",
    "An Old Battlefield",
    """|rWeapons, real and broken, still surface here|n after every real rain. |wThis ground has seen genuine, repeated violence|n, and it shows in every direction.""",
    "germania_borderlands",
)

room(
    "borderlands_raiders_camp",
    "A Raiders' Camp",
    """|wA rough, temporary camp|n, built for speed rather than any real permanence. |YWhoever's using it now|n won't be here for long, one way or another.""",
    "germania_borderlands",
)

room(
    "borderlands_scout_post",
    "An Abandoned Scout Post",
    """|wA collapsed lookout platform|n, whoever built it long since moved on or worse. |gReal, contested territory|n doesn't keep fixed positions standing for long.""",
    "germania_borderlands",
)

room(
    "borderlands_river_crossing",
    "A Rough River Crossing",
    """|cA real, cold stream|n cuts through the borderlands here, fordable but genuinely unpleasant. |wA natural chokepoint|n, exactly the kind fought over in territory this contested.""",
    "germania_borderlands",
)

room(
    "borderlands_deep_thicket",
    "A Deep Thicket",
    """|gDense, tangled growth|n makes for slow, dangerous going. |wEasy to lose your bearings here|n, and worse to be caught doing it.""",
    "germania_borderlands",
)

room(
    "borderlands_watch_fire",
    "A Cold Watch-Fire",
    """|rA fire pit|n, long since gone cold, real signs of a hasty departure scattered around it. |wWhatever happened here|n wasn't planned.""",
    "germania_borderlands",
)

room(
    "borderlands_broken_ground",
    "Broken Ground",
    """|wUneven, churned earth|n makes for genuinely treacherous footing. |gReal, repeated fighting|n has left this ground permanently scarred.""",
    "germania_borderlands",
)

room(
    "borderlands_last_stand",
    "The Site of a Last Stand",
    """|rReal, grim evidence|n marks where some real fight ended badly for somebody. |wHandled with the same restraint this subject deserves|n - evocative, not graphic.""",
    "germania_borderlands",
)

room(
    "borderlands_approach_to_stormcallers",
    "Approach to the Storm-callers' Ground",
    """|wThe borderlands' own violence thins out here|n, giving way to the Storm-callers' own, far more disciplined territory ahead. |YThe settlement's real, genuine capstone|n waits just beyond.""",
    "germania_borderlands",
)

ZONE_K_COUNT = 13

TOTAL_ROOM_COUNT_EXPECTED = (
    ROOM_COUNT_A_THROUGH_I_AND_G
    + ZONE_C_COUNT + ZONE_D_COUNT + ZONE_E_COUNT + ZONE_F_COUNT + ZONE_K_COUNT
)


LINKS = [
    # --- Zone A: Outer Palisade & Approach ---
    # "existing_wilderness_edge" is the wilderness's own (0, ROAD_LENGTH)
    # tile (world/wilderness_rome.py) - wired separately in
    # setup_germania_live.py, since it's a WildernessExit, not a plain
    # bidirectional exit like everything else here.
    ("palisade_gate", "south", "inner_gate_approach", "north"),
    ("palisade_gate", "up", "palisade_walkway", "down"),
    ("palisade_walkway", "east", "watchtower_north", "west"),
    ("palisade_walkway", "west", "watchtower_south", "east"),
    ("inner_gate_approach", "south", "settlement_hub", "north"),
    ("settlement_hub", "northwest", "path_to_wolfkin", "southeast"),
    ("settlement_hub", "east", "path_to_boarmarked", "west"),
    ("settlement_hub", "south", "path_to_ravenswatch", "north"),
    ("settlement_hub", "west", "path_to_stormcallers", "east"),
    ("settlement_hub", "southeast", "greathall_approach", "northwest"),
    ("settlement_hub", "southwest", "grove_edge", "northeast"),
    ("settlement_hub", "northeast", "borderlands_entrance", "southwest"),

    # --- Zone B: Great Hall ---
    ("greathall_approach", "south", "greathall_outer_yard", "north"),
    ("greathall_outer_yard", "south", "greathall_entrance", "north"),
    ("greathall_outer_yard", "west", "farmstead_rear_exit", "east"),
    ("greathall_outer_yard", "east", "smithy_approach", "west"),
    # Retrofitted live to a real world.doors.DescriptiveDoor pair - the
    # room's own desc already promised "massive timber doors" here
    # that didn't mechanically exist. This LINKS entry is historical
    # (setup_germania_live.py already ran and isn't meant to be re-run
    # against a populated DB) - kept as plain-exit data for the record.
    ("greathall_entrance", "south", "greathall_feasting_hall", "north"),
    ("greathall_feasting_hall", "east", "greathall_war_council", "west"),
    ("greathall_feasting_hall", "west", "greathall_weapons_hall", "east"),
    ("greathall_feasting_hall", "south", "greathall_chieftains_chamber", "north"),
    ("greathall_feasting_hall", "up", "greathall_guest_chamber", "down"),
    ("greathall_chieftains_chamber", "south", "greathall_family_quarters", "north"),
    ("greathall_chieftains_chamber", "down", "greathall_storage_cellar", "up"),

    # --- Zone H: Livestock & Farmstead ---
    ("farmstead_rear_exit", "west", "farmstead_path", "east"),
    ("farmstead_path", "north", "farmstead_pasture_a", "south"),
    ("farmstead_path", "south", "farmstead_pasture_b", "north"),
    ("farmstead_path", "west", "farmstead_house", "east"),
    ("farmstead_path", "up", "farmstead_well", "down"),
    ("farmstead_house", "north", "farmstead_livestock_pen", "south"),
    ("farmstead_house", "south", "farmstead_grain_store", "north"),

    # --- Zone I: Craft & Smithy ---
    ("smithy_approach", "east", "smithy_path", "west"),
    ("smithy_path", "north", "smithy_forge", "south"),
    ("smithy_path", "south", "smithy_tannery", "north"),
    ("smithy_path", "east", "smithy_woodworkers_yard", "west"),
    ("smithy_forge", "east", "smithy_stall", "west"),

    # --- Zone G: Sacred Grove ---
    ("grove_edge", "south", "grove_ancient_trees", "north"),
    ("grove_ancient_trees", "east", "grove_rune_stone", "west"),
    ("grove_ancient_trees", "west", "grove_seers_dwelling", "east"),
    ("grove_ancient_trees", "south", "grove_gathering_clearing", "north"),
    ("grove_gathering_clearing", "south", "grove_sacrificial_site", "north"),
    ("grove_gathering_clearing", "east", "grove_spring", "west"),
    ("grove_sacrificial_site", "south", "grove_deepest_point", "north"),

    # --- Zone C: Wolf-kin (levels 27-31) ---
    ("path_to_wolfkin", "north", "wk_entrance", "south"),
    ("wk_entrance", "north", "wk_perimeter", "south"),
    ("wk_entrance", "east", "wk_path_a", "west"),
    ("wk_entrance", "west", "wk_path_b", "east"),
    ("wk_path_a", "north", "wk_sleeping_a", "south"),
    ("wk_path_a", "east", "wk_training_yard", "west"),
    ("wk_path_b", "south", "wk_sleeping_b", "north"),
    ("wk_path_b", "west", "wk_cookfire", "east"),
    ("wk_training_yard", "east", "wk_practice_ground", "west"),
    ("wk_training_yard", "south", "wk_sparring_ring", "north"),
    ("wk_cookfire", "north", "wk_leader_hut", "south"),
    ("wk_cookfire", "south", "wk_supply_hut", "north"),
    ("wk_perimeter", "up", "wk_lookout", "down"),
    ("wk_perimeter", "north", "wk_totem", "south"),
    ("wk_totem", "north", "wk_edge", "south"),

    # --- Zone D: Boar-marked (levels 31-35) ---
    ("path_to_boarmarked", "east", "bm_entrance", "west"),
    ("bm_entrance", "north", "bm_perimeter", "south"),
    ("bm_entrance", "east", "bm_path_a", "west"),
    ("bm_entrance", "south", "bm_path_b", "north"),
    ("bm_path_a", "north", "bm_sleeping_a", "south"),
    ("bm_path_a", "east", "bm_training_yard", "west"),
    ("bm_path_b", "south", "bm_sleeping_b", "north"),
    ("bm_path_b", "west", "bm_cookfire", "east"),
    ("bm_training_yard", "east", "bm_practice_ground", "west"),
    ("bm_training_yard", "south", "bm_sparring_ring", "north"),
    ("bm_cookfire", "north", "bm_leader_hut", "south"),
    ("bm_cookfire", "south", "bm_supply_hut", "north"),
    ("bm_perimeter", "north", "bm_totem", "south"),
    ("bm_perimeter", "up", "bm_trophy_display", "down"),
    ("bm_totem", "north", "bm_edge", "south"),

    # --- Zone E: Raven's Watch (levels 35-39) ---
    ("path_to_ravenswatch", "south", "rw_entrance", "north"),
    ("rw_entrance", "south", "rw_perimeter", "north"),
    ("rw_entrance", "east", "rw_path_a", "west"),
    ("rw_entrance", "west", "rw_path_b", "east"),
    ("rw_path_a", "south", "rw_sleeping_a", "north"),
    ("rw_path_a", "east", "rw_training_yard", "west"),
    ("rw_path_b", "north", "rw_sleeping_b", "south"),
    ("rw_path_b", "west", "rw_cookfire", "east"),
    ("rw_training_yard", "east", "rw_practice_ground", "west"),
    ("rw_training_yard", "south", "rw_sparring_ring", "north"),
    ("rw_cookfire", "north", "rw_leader_hut", "south"),
    ("rw_cookfire", "south", "rw_supply_hut", "north"),
    ("rw_perimeter", "south", "rw_totem", "north"),
    ("rw_perimeter", "up", "rw_lookout", "down"),
    ("rw_totem", "south", "rw_edge", "north"),

    # --- Zone F: Storm-callers (levels 39-43, capstone 45-46) ---
    ("path_to_stormcallers", "west", "sc_entrance", "east"),
    ("sc_entrance", "west", "sc_perimeter", "east"),
    ("sc_entrance", "north", "sc_path_a", "south"),
    ("sc_entrance", "south", "sc_path_b", "north"),
    ("sc_path_a", "west", "sc_sleeping_a", "east"),
    ("sc_path_a", "north", "sc_training_yard", "south"),
    ("sc_path_b", "west", "sc_sleeping_b", "east"),
    ("sc_path_b", "south", "sc_cookfire", "north"),
    ("sc_training_yard", "west", "sc_practice_ground", "east"),
    ("sc_training_yard", "north", "sc_sparring_ring", "south"),
    ("sc_cookfire", "south", "sc_leader_hut", "north"),
    ("sc_cookfire", "west", "sc_supply_hut", "east"),
    ("sc_perimeter", "west", "sc_totem", "east"),
    ("sc_perimeter", "up", "sc_trophy_hall", "down"),
    ("sc_totem", "west", "sc_champions_ground", "east"),

    # --- Zone K: Contested Borderlands (levels 41-45) ---
    ("borderlands_entrance", "north", "borderlands_burned_camp", "south"),
    ("borderlands_entrance", "east", "borderlands_ambush_ground", "west"),
    ("borderlands_burned_camp", "north", "borderlands_ridge", "south"),
    ("borderlands_ambush_ground", "east", "borderlands_old_battlefield", "west"),
    ("borderlands_ridge", "east", "borderlands_raiders_camp", "west"),
    ("borderlands_old_battlefield", "north", "borderlands_scout_post", "south"),
    ("borderlands_raiders_camp", "south", "borderlands_river_crossing", "north"),
    ("borderlands_scout_post", "east", "borderlands_deep_thicket", "west"),
    ("borderlands_river_crossing", "east", "borderlands_watch_fire", "west"),
    ("borderlands_deep_thicket", "south", "borderlands_broken_ground", "north"),
    ("borderlands_watch_fire", "south", "borderlands_last_stand", "north"),
    ("borderlands_broken_ground", "east", "borderlands_last_stand", "west"),
    ("borderlands_last_stand", "east", "borderlands_approach_to_stormcallers", "west"),
]


# Named/unique flavor NPCs - civilians and named figures, distinct
# from the real, persistent combat population (world/prototypes.py's
# GERMANIA_* prototypes, placed by setup_germania_live.py). Format
# matches every prior zone this session: (room_key, name, kind, desc,
# extra).
NPCS = [
    (
        "palisade_gate", "a palisade guard", "static",
        "Watching the approach with open, unhidden suspicion - "
        "outsiders don't get the benefit of the doubt here.",
        None,
    ),
    (
        "watchtower_north", "a settlement lookout", "static",
        "Watching the northern territory with real, practiced "
        "attention - smoke, movement, anything worth reporting.",
        None,
    ),
    (
        "watchtower_south", "a settlement lookout", "static",
        "Watching the road south, the one direction real trouble "
        "has historically come from.",
        None,
    ),
    (
        "greathall_chieftains_chamber", "the chieftain", "static",
        "A real, significant figure - broad-shouldered, "
        "grey-bearded, carrying real authority without needing to "
        "raise his voice to prove it. Every warband in this "
        "settlement ultimately answers to him.",
        None,
    ),
    (
        "greathall_war_council", "a war-council advisor", "static",
        "Standing over the carved map table, clearly mid-thought "
        "about something that hasn't been decided yet.",
        None,
    ),
    (
        "greathall_feasting_hall", "a hall attendant", "static",
        "Keeping the hearth-fire fed and the mead flowing - the "
        "settlement's real social life doesn't run itself.",
        None,
    ),
    (
        "grove_seers_dwelling", "the seer", "static",
        "Genuinely unlike any priest built anywhere else in this "
        "world - closer to prophecy and nature-reading than formal "
        "ritual, and visibly aware of things she hasn't said aloud.",
        None,
    ),
    (
        "farmstead_house", "a farmer", "static",
        "Entirely unconcerned with warband politics - real, "
        "ordinary work doesn't stop for any of that.",
        None,
    ),
    (
        "farmstead_pasture_a", "a herder", "static",
        "Watching the livestock with the same unhurried attention "
        "a scout might give the horizon.",
        None,
    ),
    (
        "farmstead_pasture_b", "a herder", "static",
        "Working alone, entirely at ease with the quiet.",
        None,
    ),
    (
        "smithy_forge", "the smith", "static",
        "Genuinely skilled, and it shows in every finished piece "
        "laid out nearby - real Germanic craft, not a Roman "
        "imitation.",
        None,
    ),
    (
        "wk_leader_hut", "the Wolf-kin's war-leader", "static",
        "Young for the responsibility, and visibly aware of it - "
        "leading regardless.",
        None,
    ),
    (
        "bm_leader_hut", "the Boar-marked's war-leader", "static",
        "Scarred, confident, and clearly used to being obeyed "
        "without having to repeat himself.",
        None,
    ),
    (
        "rw_leader_hut", "Raven's Watch's war-leader", "static",
        "Surrounded by real maps and route-markings - this "
        "leader's authority rests on knowing the ground, not raw "
        "strength.",
        None,
    ),
]


OBJECTS = [
    (
        "wk_totem", "the Wolf-kin's totem",
        "A tall post, a real, carved wolf's head crowning it, "
        "younger trophies tied on below - this camp's whole "
        "identity, staked quite literally into the ground."
    ),
    (
        "bm_totem", "the Boar-marked's totem",
        "A tall post crowned with a real boar's skull, older "
        "trophies layered thick beneath it."
    ),
    (
        "rw_totem", "Raven's Watch's totem",
        "A tall post, real raven feathers and route-markers tied "
        "on rather than trophies of raw strength."
    ),
    (
        "sc_totem", "the Storm-callers' totem",
        "A tall, real storm-spiral carved deep into old wood, "
        "weathered by real seasons - the chieftain's own authority, "
        "reflected directly in this warband's identity."
    ),
    (
        "grove_rune_stone", "the rune-marked stone",
        "A standing stone, real runes cut deep enough to have "
        "survived real weather for real generations. What they "
        "actually say is known to vanishingly few people still "
        "living."
    ),
    (
        "grove_sacrificial_site", "the stone altar",
        "Weathered and old, set at the grove's own quiet center - "
        "handled here with real restraint, evocative rather than "
        "graphic."
    ),
    (
        "farmstead_well", "the settlement well",
        "Deep and stone-lined - the one piece of real stonework "
        "anywhere in the entire settlement, imported knowledge "
        "rather than local practice."
    ),
    (
        "greathall_war_council", "the carved map table",
        "A real, detailed map of the wider region, carved directly "
        "into the wood rather than drawn on anything that could be "
        "lost or stolen."
    ),
]


ECHOES = {
    "wk_cookfire": [
        "|rThe fire crackles as someone tosses another log on.|n",
        "|wLaughter carries from somewhere nearby.|n",
    ],
    "sc_champions_ground": [
        "|wThe wind moves differently here, somehow.|n",
    ],
    "grove_deepest_point": [
        "|GThe air feels genuinely older here.|n",
    ],
    "borderlands_old_battlefield": [
        "|rSomething metal glints briefly in the churned earth.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_wilderness_edge"}

    if len(ROOMS) != TOTAL_ROOM_COUNT_EXPECTED:
        errors.append("Expected %d rooms, got %d" % (TOTAL_ROOM_COUNT_EXPECTED, len(ROOMS)))

    names = [r["name"] for r in ROOMS.values()]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        errors.append("Duplicate room names: %s" % dupes)

    for a, da, b, db in LINKS:
        if a not in all_keys:
            errors.append("Link references unknown room: %s" % a)
        if b not in all_keys:
            errors.append("Link references unknown room: %s" % b)
        if _reverse_dir(da) is None or _reverse_dir(db) is None:
            errors.append("Unrecognized direction in link %s" % ((a, da, b, db),))

    used_directions = {}
    for a, da, b, db in LINKS:
        used_directions.setdefault(a, []).append(da)
        used_directions.setdefault(b, []).append(db)
    for room_key, dirs in used_directions.items():
        seen = set()
        for d in dirs:
            if d in seen:
                errors.append("Room '%s' has a duplicate '%s' exit" % (room_key, d))
            seen.add(d)

    adjacency = {}
    for a, da, b, db in LINKS:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    visited = set()
    queue = ["palisade_gate"]
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
        errors.append("Unreachable rooms: %s" % sorted(unreachable))

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
    print("Loaded %d rooms (attaches to the wilderness's (0, ROAD_LENGTH) tile)." % len(ROOMS))
    print("Loaded %d links, %d NPCs, %d objects, %d rooms with echoes." % (
        len(LINKS), len(NPCS), len(OBJECTS), len(ECHOES)
    ))
    errs = validate()
    if errs:
        print("\nVALIDATION FAILED (%d errors):" % len(errs))
        for e in errs:
            print(" -", e)
    else:
        print("\nValidation passed: no duplicate names, no exit collisions, "
              "full connectivity, all references resolve.")
