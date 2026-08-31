"""
The Cloaca Maxima - a validated, in-memory description of every room
and exit before anything touches the live database. Follows the exact
pattern batch_subura_data.py established: data + a standalone
validator, no Django needed, so a duplicate key or a broken exit gets
caught before a single database write happens.

85 rooms: three 5-room entrance approaches (Ludus, Subura, Forum - each
genuinely distinct before converging), meeting at an 8-room Confluence,
then six real depth tiers (Main Cloaca -> Flooded Depths -> Sunken
Quarter -> Forgotten Works -> Abyssal Cistern), plus two deliberate
inter-tier shortcuts that skip a tier entirely (a real risk, not a
convenience - see world/setup_sewers_live.py for NPC placement and the
shortcut connections specifically).

Anchors into the existing world (verified live before use, wired in
world/setup_sewers_live.py, not here - this file only covers the 85
new rooms and the links between them):
  - Ludus Approach  <- Ludus Entrance (room 320), via exit "grate"
  - Subura Approach <- The Subura Fountain (room 2640), via exit "grate"
  - Forum Approach  <- Basilica Julia - Rear Exit, via exit "grate"
Each anchor's "grate" exit leads to that approach's first room; the
matching return exit out of the sewers is "up". Using "grate" rather
than a compass direction for the anchor connection specifically, so it
reads as climbing down through a literal sewer grate rather than just
another exit - matches the user's own framing ("several sewer grates
spread around the city"). Everything below that first room uses plain
compass directions/up/down like the rest of the game.

Run this file directly (`python3 world/batch_sewers_data.py`) to
validate before executing anything against the live game.
"""

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ============================================================
# LUDUS APPROACH (5 rooms, levels 5-6)
# Cleaner construction, echoes of the arena still faintly audible.
# ============================================================

room(
    "sewer_ludus_grate", "Beneath the Ludus Grate",
    """|wA shaft of daylight|n falls through the iron grate directly overhead, and with it, faintly, the clash and roar of the Ludus above - training bouts continuing without any idea what's moving in the dark beneath them. The brickwork here is clean, recently maintained; whoever built this stretch built it to last.""",
    "sewers",
)

room(
    "sewer_ludus_runoff", "The Runoff Channel",
    """A shallow channel of water runs the length of this tunnel, carrying off whatever the Ludus above sluices down to it - mostly water, sometimes worse. The stonework is still good Roman construction, arched and even, built by people who expected it to be inspected.""",
    "sewers",
)

room(
    "sewer_ludus_bend", "A Clean Bend",
    """The tunnel bends here around what must be a support pillar for something above - the stonework thickens noticeably on one side. The Ludus's noise has faded to almost nothing, just a memory of sound rather than anything you could still make out.""",
    "sewers",
)

room(
    "sewer_ludus_barracks_wall", "Along the Barracks Wall",
    """A long, straight stretch running beneath what was probably a training barracks once, judging by the old iron fittings rusted into the ceiling - hooks for lamps, maybe, or something else entirely. A few scattered bones, animal by the look of them, litter one corner.""",
    "sewers",
)

room(
    "sewer_ludus_last_light", "Where the Light Gives Out",
    """The last hint of grate-light from above finally fails here - past this point, only what you carry with you cuts the dark. The clean construction is starting to look a little less deliberate, a little more patched, like the builders were rushing to finish this section.""",
    "sewers",
)

# ============================================================
# SUBURA APPROACH (5 rooms, levels 5-6)
# Rougher, improvised, already squatter-adjacent.
# ============================================================

room(
    "sewer_subura_grate", "Beneath the Fountain Grate",
    """The fountain's overflow drips down through the grate above in a constant, irregular patter, and the sound of the Subura's crowd - haggling, arguing, living loudly - carries down with it. The brickwork here has clearly been patched more than once, by hands with no official standing to be doing it at all.""",
    "sewers",
)

room(
    "sewer_subura_patchwork", "The Patchwork Tunnel",
    """Whole sections of wall here are a visible mismatch of old and new brick, mortar of at least three different ages holding the whole thing together. Someone has been expanding this stretch unofficially for a long time.""",
    "sewers",
)

room(
    "sewer_subura_lean_to", "A Squatter's Lean-To",
    """Someone has made a real, if miserable, home of this dry pocket - a rolled mat, a few clay jars, a cold fire-pit ringed in stone. Whoever lives here isn't home right now, or is being very quiet about the fact that they are.""",
    "sewers",
)

room(
    "sewer_subura_low_crawl", "The Low Crawl",
    """The ceiling drops sharply here, forcing anyone taller than a child to stoop or crawl through several feet of genuinely unpleasant passage. Whoever built this section clearly didn't care whether it was comfortable, only whether it worked.""",
    "sewers",
)

room(
    "sewer_subura_gathering", "A Gathering Point",
    """A wider pocket where several patched tunnels meet, clearly used as a real meeting spot - a few crates arranged like seats, the ash of more than one old fire. Whatever business gets done down here, this is plainly where it happens.""",
    "sewers",
)

# ============================================================
# FORUM APPROACH (5 rooms, levels 5-6)
# The most official of the three - real Roman engineering throughout.
# ============================================================

room(
    "sewer_forum_grate", "Beneath the Basilica Grate",
    """Even down here, the construction announces exactly whose sewer this is meant to be - dressed stone, a genuine barrel vault, brickwork stamped here and there with a maker's mark. The Basilica Julia's own foot-traffic murmurs faintly through the grate above.""",
    "sewers",
)

room(
    "sewer_forum_vault", "The Vaulted Passage",
    """A genuinely impressive stretch of vaulted stonework, wide enough for two to walk abreast comfortably - this is the real Cloaca Maxima the histories describe, not a rumor of it. It's easy to forget, standing here, that you're beneath a sewer at all.""",
    "sewers",
)

room(
    "sewer_forum_records_drop", "The Records Drop",
    """A strange little alcove, dry and oddly clean, holding the unmistakable ash of burned documents - papers destroyed in a hurry, by someone who badly needed them gone and couldn't risk burning them anywhere more visible.""",
    "sewers",
)

room(
    "sewer_forum_hidden_alcove", "A Hidden Alcove",
    """A niche carved into the wall, half-concealed behind a support pillar, holding a bedroll, a locked strongbox, and nothing else - someone official has been using this space for something they very much don't want found.""",
    "sewers",
)

room(
    "sewer_forum_last_stones", "The Last Dressed Stones",
    """The dressed, official stonework finally gives way here to rougher, older construction - the boundary, it seems, of whatever the Forum's own engineers actually maintain versus whatever came before them.""",
    "sewers",
)

# ============================================================
# THE CONFLUENCE (8 rooms, levels 6-8)
# Where all three approaches genuinely meet for the first time.
# ============================================================

room(
    "sewer_confluence_hub", "The Confluence",
    """Three separate tunnel networks converge here into one real, unmistakable junction - the true beginning of the Cloaca Maxima proper, where whoever built each approach clearly never expected the others to actually meet.""",
    "sewers",
)

room(
    "sewer_confluence_ledge", "The Watching Ledge",
    """A raised stone ledge runs along one wall here, just high enough above the channel to stay dry - a good vantage point, and evidently a popular one, judging by how worn smooth the stone has become.""",
    "sewers",
)

room(
    "sewer_confluence_market", "The Underground Exchange",
    """An improvised, entirely unofficial market has taken root here - a few plank tables, goods that ask no questions about where they came from, and an unspoken rule that whatever happens in daylight stays there.""",
    "sewers",
)

room(
    "sewer_confluence_contested", "Contested Ground",
    """Chalk marks and scratched sigils cover the walls here, each one crossed out and redrawn by someone else - territory markers from at least two different groups who both think this junction belongs to them.""",
    "sewers",
)

room(
    "sewer_confluence_drip_hall", "The Drip Hall",
    """Water falls in a steady, echoing rhythm from a crack far overhead, filling this whole chamber with sound. Impossible to hear anyone approach over it - which cuts both ways.""",
    "sewers",
)

room(
    "sewer_confluence_side_channel", "A Side Channel",
    """A narrower secondary channel breaks off from the main confluence, clearly less-traveled than the rest - the kind of space people use specifically because fewer people use it.""",
    "sewers",
)

room(
    "sewer_confluence_collapsed_arch", "The Collapsed Arch",
    """Part of the original vaulting has come down here at some point, long enough ago that the rubble's been worn smooth by traffic climbing over it since. Nobody's bothered to clear it; nobody's had to.""",
    "sewers",
)

room(
    "sewer_confluence_threshold", "The Deeper Threshold",
    """The Confluence's far wall opens into a passage noticeably wider and older than anything behind you - the real Main Cloaca, by the look and feel of the air alone, cooler and heavier than anything above it.""",
    "sewers",
)

# ============================================================
# THE MAIN CLOACA (15 rooms, levels 9-12)
# Genuine cart-scale tunnels - the historical showpiece tier.
# ============================================================

room(
    "sewer_cloaca_cart_tunnel_1", "The Cart-Scale Tunnel",
    """A tunnel genuinely wide and tall enough to drive a hay-cart through, exactly as the old accounts claim - one of the real, remarkable engineering feats this whole system is famous for. The scale of it is almost hard to believe from inside.""",
    "sewers",
)

room(
    "sewer_cloaca_cart_tunnel_2", "The Long Straightaway",
    """The tunnel runs dead straight for a considerable distance here, torchlight from some unseen source ahead barely reaching this far. Sound carries a long way down a passage this size.""",
    "sewers",
)

room(
    "sewer_cloaca_bandit_camp", "The Bandit Camp",
    """A real, semi-permanent camp has been built into a dry side recess here - bedrolls, a cookfire, crates of plainly stolen goods stacked with more organization than you'd expect. This is somebody's actual home base.""",
    "sewers",
)

room(
    "sewer_cloaca_watch_post", "The Bandits' Watch Post",
    """A raised platform, lashed together from scavenged timber, gives a clear line of sight down both directions of the tunnel - a deliberate watch post, and a good one.""",
    "sewers",
)

room(
    "sewer_cloaca_storeroom", "The Stolen Goods Store",
    """Crates and amphorae are stacked floor to ceiling here, none of it acquired honestly - the bandit camp's real treasury, guarded more carefully than the camp itself.""",
    "sewers",
)

room(
    "sewer_cloaca_cult_antechamber", "The Cult's Antechamber",
    """Someone has arranged this space with real, deliberate care - candle-stubs in careful rows, chalk sigils at the threshold meant to ward off the uninitiated. This is clearly the outer edge of something more private beyond it.""",
    "sewers",
)

room(
    "sewer_cloaca_cult_rite_chamber", "The Rite Chamber",
    """A circle of worn stones marks the center of this chamber, ash and old wax pooled at its heart - a place of real, regular ritual, the walls scratched with the same three-faced sigil over and over. Whoever performs the Crossroads Queen's rites down here does it far from anyone who might object.""",
    "sewers",
)

room(
    "sewer_cloaca_fugitive_den", "The Fugitive's Den",
    """A tight, defensible dead-end that someone's clearly chosen specifically because it's easy to guard and hard to be surprised in - the mark of someone with real reason to expect they might be hunted.""",
    "sewers",
)

room(
    "sewer_cloaca_side_grate", "A Second Grate",
    """A smaller grate overhead here, long since rusted shut, admits a thin gray light and nothing else - not a real way in or out anymore, just a reminder that the city continues on, unaware, directly above.""",
    "sewers",
)

room(
    "sewer_cloaca_junction", "The Cloaca Junction",
    """Several of the Main Cloaca's tunnels meet in a broad, open space here - not quite as grand as the Confluence above, but clearly an important crossing point in its own right.""",
    "sewers",
)

room(
    "sewer_cloaca_flooded_step", "The Flooded Step",
    """The floor drops in a wide, shallow step here, standing water pooling ankle-deep across it - the first real hint that what lies ahead won't stay this dry.""",
    "sewers",
)

room(
    "sewer_cloaca_old_repair", "An Old Repair",
    """A section of the vault that clearly failed once, patched back together with cruder stonework than the rest - functional, but visibly the weakest point in an otherwise impressive structure.""",
    "sewers",
)

room(
    "sewer_cloaca_echo_chamber", "The Echo Chamber",
    """A near-perfect dome swallows and returns every sound made here, your own footsteps coming back to you a half-second late. Disorienting, and more than a little unsettling.""",
    "sewers",
)

room(
    "sewer_cloaca_hidden_shortcut", "The Hidden Passage",
    """A narrow, deliberately concealed gap behind a false section of wall - someone dug this through by hand, and recently, judging by the tool marks. It plunges down at a steep, dangerous angle, air rushing up from somewhere far below that feels much older, and much worse, than anything nearby.""",
    "sewers",
)

room(
    "sewer_cloaca_threshold", "The Waterline Threshold",
    """The dry stone underfoot finally gives way to standing water that shows no sign of receding - the true edge of the Flooded Depths, and a genuinely different kind of danger from here on.""",
    "sewers",
)

# ============================================================
# THE FLOODED DEPTHS (15 rooms, levels 13-16)
# Partially waterlogged, genuinely hazardous to move through.
# ============================================================

room(
    "sewer_flood_entry", "The Flooded Entry",
    """Water stands knee-deep here and only gets worse ahead, dark enough that you genuinely can't see what's moving beneath the surface. Every step forward is a small, real risk.""",
    "sewers",
)

room(
    "sewer_flood_causeway", "The Broken Causeway",
    """A raised stone walkway, clearly meant to keep foot traffic dry, has crumbled away in several places - each gap means wading through water you'd much rather avoid.""",
    "sewers",
)

room(
    "sewer_flood_smuggler_dock", "The Smugglers' Dock",
    """A crude wooden dock has been built out over the water here, small flat-bottomed boats tied off against it - a real, working smuggling operation that's made the flooding an asset instead of an obstacle.""",
    "sewers",
)

room(
    "sewer_flood_cargo_hold", "The Waterlogged Cargo Hold",
    """Crates lashed to floating platforms bob gently here, the smugglers' actual inventory kept just above the waterline - goods moved through the city's sewers instead of its streets, past every checkpoint that matters.""",
    "sewers",
)

room(
    "sewer_flood_escape_channel", "The Escape Channel",
    """A narrow, fast-flowing channel branches off here, clearly kept clear on purpose - a real, deliberate escape route for anyone who needs to vanish from the main network quickly.""",
    "sewers",
)

room(
    "sewer_flood_deep_pool", "The Deep Pool",
    """The floor drops away entirely here into black, still water of genuinely unknown depth. Something large enough to disturb the surface moves beneath it every so often, unhurried.""",
    "sewers",
)

room(
    "sewer_flood_mutant_nest", "The Feral Nest",
    """A tangle of gnawed bones, shed matter, and something that might once have been fur fills this alcove - whatever's made a home here has been shaped by the flooding into something no longer quite natural.""",
    "sewers",
)

room(
    "sewer_flood_bloated_hollow", "The Bloated Hollow",
    """The stonework itself looks wrong here, swollen and discolored by decades of standing water - and something about the air makes your skin crawl before you can say exactly why.""",
    "sewers",
)

room(
    "sewer_flood_gladiator_arena", "The Sunken Arena",
    """A wide, waterlogged chamber that's clearly been used, again and again, for exactly one purpose - the scarred stone and the confident, waiting presence here make that obvious immediately.""",
    "sewers",
)

room(
    "sewer_flood_narrow_wade", "The Narrow Wade",
    """The tunnel pinches down to barely shoulder-width here, water rising to the chest of anyone passing through - a genuinely vulnerable stretch with nowhere to maneuver if something goes wrong.""",
    "sewers",
)

room(
    "sewer_flood_current", "The Strong Current",
    """The water actually moves here, a real current pulling steadily toward some drain or outflow further on - strong enough to be a genuine hazard if you're not braced for it.""",
    "sewers",
)

room(
    "sewer_flood_air_pocket", "The Air Pocket Chamber",
    """The ceiling rises unexpectedly high here, a rare dry ledge sitting just above the waterline - obviously used as a rest stop by whoever regularly makes this crossing.""",
    "sewers",
)

room(
    "sewer_flood_drowned_stair", "The Drowned Stair",
    """A stone stairway descends directly into the black water here and simply doesn't resurface - wherever it actually leads is entirely submerged now, lost to however many years of flooding.""",
    "sewers",
)

room(
    "sewer_flood_final_channel", "The Final Channel",
    """The water begins, finally, to recede here, the flooding giving way ahead to dry stone once more - the far edge of the Flooded Depths, and a real relief to reach.""",
    "sewers",
)

room(
    "sewer_flood_threshold", "The Rising Threshold",
    """The passage climbs here, water falling away behind you as the tunnel rises toward something clearly older and stranger than the flooded network you're leaving - the edge of the Sunken Quarter.""",
    "sewers",
)

# ============================================================
# THE SUNKEN QUARTER (12 rooms, levels 17-19)
# An old residential/commercial sublevel, buried and absorbed by the
# sewer network over time - real ordinary architecture half-swallowed.
# ============================================================

room(
    "sewer_sunken_entry", "The Buried Threshold",
    """The tunnel opens abruptly into something that clearly wasn't built as a sewer at all - a genuine doorframe, worn smooth, standing half-buried in silt and rubble. Whatever this place used to be, the city simply grew over it.""",
    "sewers",
)

room(
    "sewer_sunken_street", "The Buried Street",
    """An entire stretch of what was once an ordinary street runs here, cobblestones still visible beneath decades of grime - a ghost of ordinary life, swallowed whole and forgotten.""",
    "sewers",
)

room(
    "sewer_sunken_shopfront", "The Collapsed Shopfront",
    """A shop counter, unmistakable even after all this time, still stands behind a half-collapsed frontage - whatever it once sold is long gone, but the shape of ordinary commerce is still achingly recognizable.""",
    "sewers",
)

room(
    "sewer_sunken_courtyard", "The Sunken Courtyard",
    """A small domestic courtyard, its fountain long dry, sits improbably intact beneath the weight of everything built above it - someone's home, once, now just another room in the dark.""",
    "sewers",
)

room(
    "sewer_sunken_settlement", "The Squatters' Settlement",
    """A real, organized community has taken root in these buried ruins - proper shelters built from salvaged material, a genuine social order visible in how the space is arranged. These people aren't just surviving down here; they've settled.""",
    "sewers",
)

room(
    "sewer_sunken_watch_tower", "The Settlement's Watch Point",
    """A section of upper floor, somehow still structurally sound, gives the settlement's watchers a real vantage over the approaches - organized, deliberate, and clearly taken seriously.""",
    "sewers",
)

room(
    "sewer_sunken_market", "The Buried Market",
    """The settlement's own improvised market fills this wider chamber - goods scavenged, traded, and sold entirely outside the city's knowledge, a whole second economy nobody above knows exists.""",
    "sewers",
)

room(
    "sewer_sunken_shrine", "The Forgotten Household Shrine",
    """A small household shrine still stands here, its god's identity worn illegible by time - someone in the settlement has clearly kept it tended anyway, fresh offerings sitting at its base.""",
    "sewers",
)

room(
    "sewer_sunken_collapsed_insula", "The Collapsed Insula",
    """The upper floors of what was once a real insula building have come down entirely, choking this space with rubble - passable, but only carefully, and only slowly.""",
    "sewers",
)

room(
    "sewer_sunken_deep_cellar", "The Deep Cellar",
    """A private cellar, remarkably well preserved, still holds the shattered remains of amphorae that once stored someone's wine - a small, sad monument to an entirely ordinary life.""",
    "sewers",
)

room(
    "sewer_sunken_boundary_wall", "The Boundary Wall",
    """A genuine defensive wall has been built here, deliberately, by the settlement - the clearest sign yet that whatever's further in is something they actively want to keep out, not just avoid.""",
    "sewers",
)

room(
    "sewer_sunken_threshold", "The Old Foundations",
    """The buried streets and shopfronts finally give way to something older still - foundations from before even this sunken quarter, stonework that predates everything you've passed through so far.""",
    "sewers",
)

# ============================================================
# THE FORGOTTEN WORKS (12 rooms, levels 20-23)
# The oldest section - possibly predating the formal Cloaca Maxima.
# ============================================================

room(
    "sewer_forgotten_entry", "The Threshold of the Old Works",
    """The stonework here is unlike anything built anywhere else in this whole network - rougher, heavier, unmistakably older. Whoever raised this section did it long before Rome had a formal sewer at all.""",
    "sewers",
)

room(
    "sewer_forgotten_gallery", "The Ancient Gallery",
    """A long gallery of crude, massive stonework stretches ahead, clearly built by hands with far less engineering knowledge than whatever came after - functional, brutal, and still standing after everything.""",
    "sewers",
)

room(
    "sewer_forgotten_cyclops_den", "The Feral Cyclops's Den",
    """Bones, broken stone, and the wreckage of anything unlucky enough to wander this deep are scattered everywhere here - whatever's made this its territory has clearly stopped distinguishing between prey and intruder.""",
    "sewers",
)

room(
    "sewer_forgotten_bone_pile", "The Bone Pile",
    """An enormous, deliberate pile of bones - animal and otherwise - has been stacked here with something uncomfortably close to care. Not a den. A trophy collection.""",
    "sewers",
)

room(
    "sewer_forgotten_cult_hall", "The Cult's Under-Hall",
    """A wide chamber, carefully cleared of rubble by hands that clearly meant to use it - ritual markings here are more elaborate and more disturbing than anything seen higher up in the network.""",
    "sewers",
)

room(
    "sewer_forgotten_augur_sanctum", "The Augur's Sanctum",
    """Bird bones and feathers, arranged with real ceremonial precision, cover every surface of this private inner chamber - someone is reading omens down here, far from any sky, and finding something worth staying for.""",
    "sewers",
)

room(
    "sewer_forgotten_collapsed_well", "The Collapsed Well",
    """An ancient well shaft, long dry, drops away into darkness here - whatever water source this once fed has been gone for centuries, but the shaft itself is still very much a hazard.""",
    "sewers",
)

room(
    "sewer_forgotten_crushed_passage", "The Crushed Passage",
    """The ceiling has partially given way here under the sheer weight of everything built above it over the centuries - passable only by stooping low beneath stone that groans audibly with every step.""",
    "sewers",
)

room(
    "sewer_forgotten_old_altar", "The Old Altar",
    """A crude stone altar, far older than the cult using the chambers nearby, sits half-buried in silt - whoever raised it worshipped something with no name anyone down here still remembers.""",
    "sewers",
)

room(
    "sewer_forgotten_deep_cistern_approach", "The Approach to the Deep",
    """The passage narrows and steepens here, descending sharply toward something that feels, unmistakably, like the true bottom of the entire network - older, colder, and heavier than everything above it.""",
    "sewers",
)

room(
    "sewer_forgotten_shortcut", "The Deep Cutting",
    """A rough, steep cutting drops away here, hand-dug and clearly very old, plunging straight down toward something far below - a genuinely dangerous route past the Sunken Quarter's own worth of danger, if you're willing to risk it.""",
    "sewers",
)

room(
    "sewer_forgotten_threshold", "The Final Descent",
    """The Forgotten Works' oldest stonework finally opens onto a final stair, descending toward a darkness that feels genuinely, physically different from everything above it.""",
    "sewers",
)

# ============================================================
# THE ABYSSAL CISTERN (8 rooms, levels 24-25)
# Deliberately the smallest zone - a real "final approach" feel.
# ============================================================

room(
    "sewer_abyssal_entry", "The Cistern's Edge",
    """The passage ends here at the lip of something vast and entirely man-made - an ancient cistern, far larger than anything a simple sewer should need. The air itself feels older.""",
    "sewers",
)

room(
    "sewer_abyssal_stair", "The Descending Stair",
    """A wide stone stair spirals down along the cistern's inner wall, built for something that once needed to move through here in numbers. Every step down feels like a real, deliberate commitment.""",
    "sewers",
)

room(
    "sewer_abyssal_flooded_floor", "The Cistern Floor",
    """Still, black water covers the entire floor of this cavernous space, its true depth impossible to judge. Nothing about this place feels like it was ever meant to be found.""",
    "sewers",
)

room(
    "sewer_abyssal_pillar_hall", "The Pillar Hall",
    """Massive stone pillars rise from the water at regular intervals here, holding up a ceiling lost entirely to darkness overhead - the true scale of this place only fully sinks in standing among them.""",
    "sewers",
)

room(
    "sewer_abyssal_dry_ledge", "The Last Dry Ledge",
    """A single wide ledge of dry stone runs along one side of the cistern - the last solid, dependable ground before whatever waits at the heart of this place.""",
    "sewers",
)

room(
    "sewer_abyssal_offering_shelf", "The Offering Shelf",
    """A shelf carved directly into the cistern wall holds the remains of offerings left by hands long gone - coins, bones, small carved idols, all sunk beneath a fine layer of undisturbed silt.""",
    "sewers",
)

room(
    "sewer_abyssal_threshold", "The Threshold of the Deep Heart",
    """The water narrows here into a single dark channel leading toward the cistern's absolute center - whatever's down there, this is the only way left to reach it.""",
    "sewers",
)

room(
    "sewer_abyssal_heart", "The Heart of the Cistern",
    """The oldest, deepest chamber in the entire network - a vast, still space that feels less like the bottom of a sewer and more like the bottom of something the city itself was built to bury.""",
    "sewers",
)


# ============================================================
# EXITS - bidirectional (from_room, from_dir, to_room, to_dir)
# ============================================================

LINKS = [
    # Ludus Approach spine
    ("sewer_ludus_grate", "down", "sewer_ludus_runoff", "up"),
    ("sewer_ludus_runoff", "down", "sewer_ludus_bend", "up"),
    ("sewer_ludus_bend", "down", "sewer_ludus_barracks_wall", "up"),
    ("sewer_ludus_barracks_wall", "down", "sewer_ludus_last_light", "up"),
    ("sewer_ludus_last_light", "down", "sewer_confluence_hub", "north"),

    # Subura Approach spine
    ("sewer_subura_grate", "down", "sewer_subura_patchwork", "up"),
    ("sewer_subura_patchwork", "down", "sewer_subura_lean_to", "up"),
    ("sewer_subura_lean_to", "down", "sewer_subura_low_crawl", "up"),
    ("sewer_subura_low_crawl", "down", "sewer_subura_gathering", "up"),
    ("sewer_subura_gathering", "down", "sewer_confluence_hub", "east"),

    # Forum Approach spine
    ("sewer_forum_grate", "down", "sewer_forum_vault", "up"),
    ("sewer_forum_vault", "down", "sewer_forum_records_drop", "up"),
    ("sewer_forum_records_drop", "down", "sewer_forum_hidden_alcove", "up"),
    ("sewer_forum_hidden_alcove", "down", "sewer_forum_last_stones", "up"),
    ("sewer_forum_last_stones", "down", "sewer_confluence_hub", "west"),

    # The Confluence (8 rooms, hub-and-branch with a real loop)
    ("sewer_confluence_hub", "up", "sewer_confluence_ledge", "down"),
    ("sewer_confluence_hub", "south", "sewer_confluence_market", "north"),
    ("sewer_confluence_market", "east", "sewer_confluence_contested", "west"),
    ("sewer_confluence_contested", "south", "sewer_confluence_drip_hall", "north"),
    ("sewer_confluence_drip_hall", "west", "sewer_confluence_side_channel", "east"),
    ("sewer_confluence_side_channel", "north", "sewer_confluence_market", "south"),
    ("sewer_confluence_drip_hall", "east", "sewer_confluence_collapsed_arch", "west"),
    ("sewer_confluence_collapsed_arch", "south", "sewer_confluence_threshold", "north"),

    # The Main Cloaca (15 rooms)
    ("sewer_confluence_threshold", "south", "sewer_cloaca_cart_tunnel_1", "north"),
    ("sewer_cloaca_cart_tunnel_1", "south", "sewer_cloaca_cart_tunnel_2", "north"),
    ("sewer_cloaca_cart_tunnel_2", "east", "sewer_cloaca_bandit_camp", "west"),
    ("sewer_cloaca_bandit_camp", "up", "sewer_cloaca_watch_post", "down"),
    ("sewer_cloaca_bandit_camp", "south", "sewer_cloaca_storeroom", "north"),
    ("sewer_cloaca_cart_tunnel_2", "west", "sewer_cloaca_cult_antechamber", "east"),
    ("sewer_cloaca_cult_antechamber", "west", "sewer_cloaca_cult_rite_chamber", "east"),
    ("sewer_cloaca_cult_antechamber", "south", "sewer_cloaca_fugitive_den", "north"),
    ("sewer_cloaca_cart_tunnel_2", "south", "sewer_cloaca_junction", "north"),
    ("sewer_cloaca_junction", "up", "sewer_cloaca_side_grate", "down"),
    ("sewer_cloaca_junction", "east", "sewer_cloaca_old_repair", "west"),
    ("sewer_cloaca_old_repair", "south", "sewer_cloaca_echo_chamber", "north"),
    ("sewer_cloaca_echo_chamber", "west", "sewer_cloaca_hidden_shortcut", "east"),
    ("sewer_cloaca_junction", "south", "sewer_cloaca_flooded_step", "north"),
    ("sewer_cloaca_flooded_step", "south", "sewer_cloaca_threshold", "north"),

    # The Flooded Depths (15 rooms)
    ("sewer_cloaca_threshold", "south", "sewer_flood_entry", "north"),
    ("sewer_flood_entry", "south", "sewer_flood_causeway", "north"),
    ("sewer_flood_causeway", "east", "sewer_flood_smuggler_dock", "west"),
    ("sewer_flood_smuggler_dock", "south", "sewer_flood_cargo_hold", "north"),
    ("sewer_flood_smuggler_dock", "east", "sewer_flood_escape_channel", "west"),
    ("sewer_flood_causeway", "south", "sewer_flood_deep_pool", "north"),
    ("sewer_flood_deep_pool", "west", "sewer_flood_mutant_nest", "east"),
    ("sewer_flood_mutant_nest", "south", "sewer_flood_bloated_hollow", "north"),
    ("sewer_flood_deep_pool", "east", "sewer_flood_gladiator_arena", "west"),
    ("sewer_flood_deep_pool", "south", "sewer_flood_narrow_wade", "north"),
    ("sewer_flood_narrow_wade", "south", "sewer_flood_current", "north"),
    ("sewer_flood_current", "east", "sewer_flood_air_pocket", "west"),
    ("sewer_flood_current", "south", "sewer_flood_drowned_stair", "north"),
    ("sewer_flood_current", "west", "sewer_flood_final_channel", "east"),
    ("sewer_flood_final_channel", "south", "sewer_flood_threshold", "north"),

    # The Sunken Quarter (12 rooms)
    ("sewer_flood_threshold", "south", "sewer_sunken_entry", "north"),
    ("sewer_sunken_entry", "south", "sewer_sunken_street", "north"),
    ("sewer_sunken_street", "east", "sewer_sunken_shopfront", "west"),
    ("sewer_sunken_street", "west", "sewer_sunken_courtyard", "east"),
    ("sewer_sunken_street", "south", "sewer_sunken_settlement", "north"),
    ("sewer_sunken_settlement", "up", "sewer_sunken_watch_tower", "down"),
    ("sewer_sunken_settlement", "east", "sewer_sunken_market", "west"),
    ("sewer_sunken_settlement", "west", "sewer_sunken_shrine", "east"),
    ("sewer_sunken_shopfront", "south", "sewer_sunken_collapsed_insula", "north"),
    ("sewer_sunken_courtyard", "south", "sewer_sunken_deep_cellar", "north"),
    ("sewer_sunken_settlement", "south", "sewer_sunken_boundary_wall", "north"),
    ("sewer_sunken_boundary_wall", "south", "sewer_sunken_threshold", "north"),

    # The Forgotten Works (12 rooms)
    ("sewer_sunken_threshold", "south", "sewer_forgotten_entry", "north"),
    ("sewer_forgotten_entry", "south", "sewer_forgotten_gallery", "north"),
    ("sewer_forgotten_gallery", "east", "sewer_forgotten_cyclops_den", "west"),
    ("sewer_forgotten_cyclops_den", "south", "sewer_forgotten_bone_pile", "north"),
    ("sewer_forgotten_gallery", "west", "sewer_forgotten_cult_hall", "east"),
    ("sewer_forgotten_cult_hall", "west", "sewer_forgotten_augur_sanctum", "east"),
    ("sewer_forgotten_gallery", "south", "sewer_forgotten_collapsed_well", "north"),
    ("sewer_forgotten_collapsed_well", "south", "sewer_forgotten_crushed_passage", "north"),
    ("sewer_forgotten_cult_hall", "south", "sewer_forgotten_old_altar", "north"),
    ("sewer_forgotten_gallery", "down", "sewer_forgotten_deep_cistern_approach", "up"),
    ("sewer_forgotten_deep_cistern_approach", "down", "sewer_forgotten_shortcut", "up"),
    ("sewer_forgotten_deep_cistern_approach", "south", "sewer_forgotten_threshold", "north"),

    # The Abyssal Cistern (8 rooms)
    ("sewer_forgotten_threshold", "south", "sewer_abyssal_entry", "north"),
    ("sewer_abyssal_entry", "down", "sewer_abyssal_stair", "up"),
    ("sewer_abyssal_stair", "down", "sewer_abyssal_flooded_floor", "up"),
    ("sewer_abyssal_flooded_floor", "east", "sewer_abyssal_pillar_hall", "west"),
    ("sewer_abyssal_flooded_floor", "west", "sewer_abyssal_dry_ledge", "east"),
    ("sewer_abyssal_dry_ledge", "south", "sewer_abyssal_offering_shelf", "north"),
    ("sewer_abyssal_pillar_hall", "south", "sewer_abyssal_threshold", "north"),
    ("sewer_abyssal_threshold", "south", "sewer_abyssal_heart", "north"),

    # --- The two deliberate inter-tier shortcuts ---
    # Main Cloaca (tier 2) -> Sunken Quarter (tier 4), skipping the
    # Flooded Depths entirely. A real risk, not a convenience - see
    # world/setup_sewers_live.py's docstring for the difficulty math.
    ("sewer_cloaca_hidden_shortcut", "down", "sewer_sunken_boundary_wall", "up"),
    # Flooded Depths (tier 3) -> Forgotten Works (tier 5), skipping the
    # Sunken Quarter entirely.
    ("sewer_flood_drowned_stair", "down", "sewer_forgotten_old_altar", "up"),
]


def validate():
    """Standalone structural check - no Django needed. Confirms every
 exit target actually exists as a defined room, every room key is
 unique (enforced live by room() itself), and every room the LINKS
 list touches is actually reachable from at least one of the three
 grate entrances via a plain BFS."""
    errors = []

    from collections import defaultdict
    directions_per_room = defaultdict(list)

    for from_key, from_dir, to_key, to_dir in LINKS:
        if from_key not in ROOMS:
            errors.append("LINKS references undefined room: %s" % from_key)
        if to_key not in ROOMS:
            errors.append("LINKS references undefined room: %s" % to_key)
        directions_per_room[from_key].append(from_dir)
        directions_per_room[to_key].append(to_dir)

    for room_key, directions in directions_per_room.items():
        seen_dirs = set()
        for d in directions:
            if d in seen_dirs:
                errors.append("Duplicate exit direction '%s' in room: %s" % (d, room_key))
            seen_dirs.add(d)

    # Build an adjacency map and BFS from all three grates.
    adjacency = {}
    for from_key, _, to_key, _ in LINKS:
        adjacency.setdefault(from_key, set()).add(to_key)
        adjacency.setdefault(to_key, set()).add(from_key)

    entrances = ["sewer_ludus_grate", "sewer_subura_grate", "sewer_forum_grate"]
    seen = set()
    frontier = list(entrances)
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        for neighbor in adjacency.get(current, ()):
            if neighbor not in seen:
                frontier.append(neighbor)

    unreachable = set(ROOMS.keys()) - seen
    if unreachable:
        errors.append("Unreachable rooms from any grate: %s" % sorted(unreachable))

    if errors:
        raise ValueError("\n".join(errors))

    print("Validated: %d rooms, %d exits, all reachable from all 3 grates." % (
        len(ROOMS), len(LINKS) * 2,
    ))


if __name__ == "__main__":
    validate()
