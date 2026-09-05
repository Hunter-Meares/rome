"""
Forum Romanum world data - a validated, in-memory description of every
room, exit, NPC, object, and echo before anything touches the live
database. Built as data + a validator (run standalone, no Django
needed) specifically because of two real lessons from this session:

1. The Underworld expansion's v1 attempt shipped a real exit-naming
   collision (two "north" exits from the same room) that only a live
   audit caught after the fact.
2. A hand-built ~30-room batch already needed that live audit to catch
   duplicate content from a re-run. At 99 rooms, catching mistakes
   AFTER they're live is much more expensive than catching them here,
   in plain Python, before a single database write happens.

LINKS are defined as single bidirectional connections (room_a, dir_a,
room_b, dir_b) rather than two independent per-room exit lists - this
makes an accidental duplicate exit direction on one room structurally
impossible to introduce silently, since each link always creates
exactly one matched pair.

Run this file directly (`python3 batch_forum_data.py`) to validate
before executing anything against the live game.
"""

# ============================================================
# ROOMS
# ============================================================
# key -> dict(name, desc, zone)

ROOMS = {}


def room(key, name, desc, zone):
    if key in ROOMS:
        raise ValueError("duplicate room key: %s" % key)
    ROOMS[key] = {"name": name, "desc": desc.strip(), "zone": zone}


# ------------------------------------------------------------------
# ZONE 1 - Via Sacra entry spine (6 new rooms; connects to the
# existing "Via Sacra" room #661 built the previous session, which
# serves as the 7th stretch the reference doc calls for).
# ------------------------------------------------------------------

room(
    "via_sacra_arch_approach",
    "Approach to the Arch of Titus",
    """|YThe road narrows here|n, funneled between the backs of buildings not yet finished, as it bends toward a shape rising ahead - a single monumental arch, pale stone catching the light. |wPilgrims and petitioners alike slow their pace|n without quite meaning to, the way people do before something built to be looked at.""",
    "via_sacra",
)

room(
    "arch_of_titus",
    "The Arch of Titus",
    """|YA single triumphal arch spans the road entirely|n, forcing everyone - senator and slave alike - to pass beneath the same carved stone. The relief work is unmistakable even at a glance: |wa procession of soldiers carrying off the spoils of a conquered temple|n, a great branched lampstand hoisted on straining shoulders. |cAn inscription runs along the arch's crown|n, Latin cut deep enough to still catch shadow after a century of weather. Rome remembers its victories in stone, so that no one passing beneath one can forget them either.""",
    "via_sacra",
)

room(
    "via_sacra_shrines",
    "The Sacred Way - Shrine Row",
    """|YSmall shrines crowd both sides of the road here|n, no two alike - a niche to a household god, a blackened altar still faintly warm from someone's morning offering, a chipped statue worn smooth at the feet from generations of hands touching it in passing. |gGarlands of dried flowers|n hang from more than one doorpost. None of these shrines are grand. All of them are used.""",
    "via_sacra",
)

room(
    "via_sacra_colonnade",
    "The Shaded Colonnade",
    """|wA covered colonnade|n runs along the road's northern edge, stone columns holding up a roof that turns the worst of the midday sun into dappled shade. |gMerchants have claimed the shadow for their own|n, trays of small goods balanced on knees, and a handful of idlers lean against the columns doing nothing in particular except watching everyone else go by.""",
    "via_sacra",
)

room(
    "forum_square_approach",
    "Approach to the Forum Square",
    """|YThe road widens noticeably here|n, buildings pulling back on either side as though making room for what's coming. |cThe noise changes too|n - less the close murmur of a street, more the layered roar of a crowd that hasn't come into view yet. Whatever lies ahead, it isn't small.""",
    "via_sacra",
)

room(
    "forum_threshold",
    "The Forum's Threshold",
    """|YThe road opens all at once|n, and the Forum Romanum stands revealed - a great paved valley ringed by temples, courts, and monuments, |wmarble and gilt catching the sun from every direction|n at once. This is not a single building. This is the heart of an empire, built to be walked through, argued in, worshipped in, and never quite finished admiring. |cThe crowd noise here is constant and enormous|n - a thousand conversations, a hundred transactions, somewhere a voice raised over all of it.""",
    "via_sacra",
)

# ------------------------------------------------------------------
# ZONE 2 - the main Forum square (7 rooms)
# ------------------------------------------------------------------

room(
    "forum_square_east",
    "Forum Square - Eastern Edge",
    """|YThe eastern edge of the great square|n, where the temple cluster first comes fully into view - columns and pediments rising in close succession, |wpainted statues|n catching the light in colors no ruin ever preserves. The paving underfoot is fitted stone, worn into a faint, permanent polish by centuries of sandaled feet.""",
    "forum_square",
)

room(
    "forum_square_central",
    "The Forum Romanum - Central Plaza",
    """|YThe Forum's true center|n, a broad open plaza ringed by the most important buildings in the Roman world. |cThe noise is constant and layered|n - vendors, arguments, distant oratory, the general hum of a downtown at its busiest - and the air carries incense from the temples mixed unapologetically with the smell of the crowd itself. Every direction leads somewhere that matters.""",
    "forum_square",
)

room(
    "forum_comitium",
    "The Comitium",
    """|wAn open, sunken assembly ground|n, older than almost everything around it - this is where the Republic's citizens once gathered to vote and to watch trials decided in the open air. |YIt sees far less use now|n than it once did, imperial business having moved indoors and upward, but it hasn't been abandoned. Old stone worn into steps still holds the shape of a crowd that used to stand here.""",
    "forum_square",
)

room(
    "forum_rostra",
    "The Rostra",
    """|YA raised speaker's platform|n, its face studded with the actual bronze prows - the rostra - of enemy warships captured generations ago, each one a permanent, physical boast. |wAnyone who wants Rome's attention climbs these steps|n and speaks from here; there is no other way to be heard by a crowd this size. The stone at the platform's edge is worn smooth exactly where a hundred years of orators have planted their feet.""",
    "forum_square",
)

room(
    "forum_golden_milestone",
    "The Golden Milestone",
    """|YA gilded bronze column|n stands here, unassuming next to the great buildings around it, and yet every road in the empire is measured from this exact point. |wDistances carved into the bronze|n name cities most Romans will never see - Londinium, Antiochia, Alexandria - each one, in principle, only a matter of miles from where you're standing. Beside it, a low stone marker - the Umbilicus - claims to sit at the literal center of the city itself.""",
    "forum_square",
)

room(
    "forum_square_west",
    "Forum Square - Western Edge",
    """|YThe square's western edge|n, where the ground begins to rise toward the Capitoline Hill. The Tabularium's long facade looms overhead, |wbuilt directly into the hillside|n, and the base of the Temple of Saturn's steps starts just to the south. The crowd thins slightly here, replaced by the more purposeful traffic of people with somewhere specific to be.""",
    "forum_square",
)

room(
    "forum_square_south",
    "Forum Square - Southern Edge",
    """|YThe southern edge of the square|n, dominated by the long, columned facade of a basilica rising on one side and the temple cluster continuing along the other. |cLawyers argue cases in loud, practiced voices|n even out here on the steps, unwilling to wait until they're actually inside to start making their point.""",
    "forum_square",
)

# ------------------------------------------------------------------
# ZONE 3 - Curia Julia, the Senate House (6 rooms)
# ------------------------------------------------------------------

room(
    "curia_portico",
    "Curia Julia - Entrance Portico",
    """|YA plain, severe facade|n compared to the temples nearby - the Senate House was built to impress with authority, not ornament. |wArmed lictors|n stand near the entrance, less a threat than a formality, a visible reminder of whose business happens inside.""",
    "curia",
)

room(
    "curia_antechamber",
    "Curia Julia - Antechamber",
    """A modest waiting room just inside the entrance, where petitioners and junior senators alike wait to be received. |wBenches line the walls|n, and the murmur of the chamber beyond is audible even through the heavy bronze doors.""",
    "curia",
)

room(
    "curia_chamber",
    "Curia Julia - the Senate Chamber",
    """|YThe Senate of Rome meets here|n, tiered rows of benches running the length of the hall on either side, facing a central floor where business is actually conducted. At the far end stands the |Yaltar and gilded statue of Victory|n, to whom every session formally opens. |wThe air smells faintly of bronze and old incense|n, and even empty, the room carries real weight.""",
    "curia",
)

room(
    "curia_side_chamber",
    "Curia Julia - Side Chamber",
    """A smaller room off the main chamber, used for the sort of conversation senators prefer not to have where everyone can hear it. |wThe furnishings are plain|n but comfortable - this is a room for business, not display.""",
    "curia",
)

room(
    "curia_records_room",
    "Curia Julia - Records Room",
    """Shelves of tightly-rolled scrolls line every wall, each one a record of some session's proceedings, going back further than most of the senators currently arguing upstairs would guess. |wA pair of clerks|n work in near-silence, cataloguing the day's business before it has the chance to be misremembered.""",
    "curia",
)

room(
    "curia_rear_chamber",
    "Curia Julia - Restricted Chamber",
    """A private rear chamber, its access narrowed by custom rather than any visible lock. |YNothing here suggests you're unwelcome exactly|n - only that this is a room for people whose business here is already understood, not explained. Few linger who don't belong.""",
    "curia",
)

# ------------------------------------------------------------------
# ZONE 4 - Basilica Julia (9 rooms)
# ------------------------------------------------------------------

room(
    "basilica_julia_entrance",
    "Basilica Julia - Main Entrance",
    """|YA vast columned hall|n opens up beyond the entrance, the ceiling lost somewhere in shadow far overhead. Basilica Julia is Rome's civil court and then some - part courthouse, part public gathering hall, |wthe noise inside almost a match for the square outside|n.""",
    "basilica_julia",
)

room(
    "basilica_julia_gallery",
    "Basilica Julia - Central Gallery",
    """A wide gallery connecting the basilica's separate court chambers, |wfoot traffic constant in every direction|n - litigants, witnesses, the merely curious drawn in by whatever case sounds most interesting today. Stairs climb toward a gallery overlooking the floor below.""",
    "basilica_julia",
)

room(
    "basilica_julia_court1",
    "Basilica Julia - Court Chamber I",
    """|YA civil case is underway|n, an advocate mid-argument, voice pitched to carry to a small knot of onlookers who've stopped simply to watch. |wThe dispute concerns a contested inheritance|n, from what little makes sense out of context - the kind of case that could run for days.""",
    "basilica_julia",
)

room(
    "basilica_julia_court2",
    "Basilica Julia - Court Chamber II",
    """A second case occupies this chamber, quieter and more procedural than the theater next door - |wa dispute over a property boundary|n, argued in the flat, technical tone of lawyers who've done this a hundred times before and expect to do it a hundred more.""",
    "basilica_julia",
)

room(
    "basilica_julia_upper_gallery",
    "Basilica Julia - Upper Gallery",
    """|YA balcony overlooking the basilica's ground floor|n, the noise below softened just enough by height and distance to become almost pleasant. From here you can watch three separate legal dramas unfold at once without being part of any of them.""",
    "basilica_julia",
)

room(
    "basilica_julia_tabernae_a",
    "Basilica Julia - Tabernae Row",
    """|gA row of small shops built directly into the basilica's ground floor|n - the building itself doubling as a shopping arcade between court sessions. Whatever you need while you wait for a verdict, one of these stalls probably sells it.""",
    "basilica_julia",
)

room(
    "basilica_julia_tabernae_b",
    "Basilica Julia - Second Tabernae Row",
    """The row continues, |gstalls packed close on both sides|n, the smell of fresh bread from one competing directly with a leatherworker's stall from the next. Business here runs entirely on the basilica's own foot traffic.""",
    "basilica_julia",
)

room(
    "basilica_julia_consult_hall",
    "Basilica Julia - Consultation Hall",
    """A quieter side hall, away from the main galleries, where lawyers meet clients for the conversations that happen before a case ever reaches a courtroom. |wLow voices|n and careful, unhurried negotiation replace the basilica's usual noise.""",
    "basilica_julia",
)

room(
    "basilica_julia_rear_exit",
    "Basilica Julia - Rear Exit",
    """A quieter exit at the building's rear, |wless grand than the main entrance|n but considerably less crowded. It opens back onto the square from a different angle entirely - useful for anyone trying to avoid a particular conversation happening near the front doors.""",
    "basilica_julia",
)

# ------------------------------------------------------------------
# ZONE 5 - Basilica Aemilia (9 rooms)
# ------------------------------------------------------------------

room(
    "basilica_aemilia_entrance",
    "Basilica Aemilia - Main Entrance",
    """|YA long, dignified facade|n, older in feel than the Julia across the square - Basilica Aemilia has stood, rebuilt and expanded, for generations. The entrance hall inside is busy with the same mix of law and commerce as its sister building.""",
    "basilica_aemilia",
)

room(
    "basilica_aemilia_hall",
    "Basilica Aemilia - the Great Hall",
    """|YThe basilica's central hall|n, vast enough that voices from either end blur into a single wash of sound. Look closely at the floor near the northern wall and you'll find |wdark, permanent stains in the stone|n - the mark, so the story goes, of bronze coins that melted outright in a fire here generations ago and were simply paved over rather than removed.""",
    "basilica_aemilia",
)

room(
    "basilica_aemilia_court1",
    "Basilica Aemilia - Court Chamber I",
    """A case is in session here, the advocate's voice pitched loud enough to be heard clearly from the hall outside. |wThe details concern a disputed shipment|n and whose fault its loss really was - the kind of maritime dispute that keeps half the city's lawyers employed.""",
    "basilica_aemilia",
)

room(
    "basilica_aemilia_court2",
    "Basilica Aemilia - Court Chamber II",
    """A second chamber, presently between sessions - benches empty, a single clerk tidying scrolls left behind by the morning's business. |wThe quiet here is temporary|n; another case is due within the hour.""",
    "basilica_aemilia",
)

room(
    "basilica_aemilia_tabernae_a",
    "Basilica Aemilia - Tabernae Row",
    """|gShops line the ground floor here|n, much like the Julia's own arcade, though the goods lean more toward everyday necessities than curiosities - cloth, tools, plain pottery.""",
    "basilica_aemilia",
)

room(
    "basilica_aemilia_tabernae_b",
    "Basilica Aemilia - Second Tabernae Row",
    """The row continues past a support colonnade, |gsmaller stalls packed even closer together|n here, run by merchants who couldn't afford the more visible spots nearer the entrance.""",
    "basilica_aemilia",
)

room(
    "basilica_aemilia_moneylenders",
    "Basilica Aemilia - Moneylenders' Corner",
    """|YA distinct corner of the basilica|n, set slightly apart from the general shops - a cluster of moneylenders' booths, ledgers open, conversations pitched low and careful in the particular way that only ever means money.""",
    "basilica_aemilia",
)

room(
    "basilica_aemilia_upper_gallery",
    "Basilica Aemilia - Upper Gallery",
    """A balcony running the length of the great hall, |wa clear view down onto the coin-stained floor below|n. Fewer people bother climbing up here than in the Julia's equivalent gallery - the view is similar, but the Aemilia has never quite had the same reputation for drama.""",
    "basilica_aemilia",
)

room(
    "basilica_aemilia_rear_exit",
    "Basilica Aemilia - Rear Exit",
    """A plain rear doorway leading back out toward the square, |wworn smooth by shopkeepers|n hauling goods in and out at all hours, far more than by the basilica's actual visitors.""",
    "basilica_aemilia",
)

# ------------------------------------------------------------------
# ZONE 6 - Temple cluster (39 rooms)
# ------------------------------------------------------------------

# --- Temple of Saturn (6) ---
room(
    "temple_saturn_steps",
    "Temple of Saturn - Outer Steps",
    """|YA long flight of stone steps|n climbs toward one of the oldest temples in the Forum, eight surviving columns holding up a pediment weathered nearly featureless by age. |gArgentarii - moneychangers|n have set up business right at the base of the steps, close enough to the state treasury within to make the association obvious.""",
    "temple_saturn",
)

room(
    "temple_saturn_cella",
    "Temple of Saturn - Main Cella",
    """|YThe cult statue of Saturn|n dominates the inner chamber, old enough that its paint has faded to a shadow of what it once was. |cIncense smoke curls near the ceiling|n, never quite clearing. This is one of the oldest continuously-worshipped sites in the entire city.""",
    "temple_saturn",
)

room(
    "temple_saturn_side",
    "Temple of Saturn - Side Chamber",
    """A smaller chamber off the main cella, used for storing ritual implements and offerings not yet consecrated. |wA priest moves quietly among shelves|n of bronze vessels, checking each one against some private inventory of his own.""",
    "temple_saturn",
)

room(
    "temple_saturn_aerarium_ante",
    "Temple of Saturn - Aerarium Antechamber",
    """|YA heavy, iron-bound door|n marks the entrance to Rome's actual state treasury, the Aerarium - the temple above serving as much to guard this room as to honor the god. |wA pair of clerks|n sit at a table nearby, checking names against a list before anyone is permitted further in.""",
    "temple_saturn",
)

room(
    "temple_saturn_vault",
    "Temple of Saturn - the Treasury Vault",
    """|YRome's actual gold reserves|n, stacked in ingots and sealed strongboxes under heavy guard. The air is cool and still, the kind of silence that money seems to generate around itself. |wArmed guards watch every corner|n, unblinking, entirely unimpressed by anyone who wanders in without a very good reason.""",
    "temple_saturn",
)

room(
    "temple_saturn_records",
    "Temple of Saturn - Treasury Records",
    """Ledgers line every wall of this narrow room, each one tracking exactly what's stored where in the vault beyond - |wa small army of scribes|n maintains the count, cross-checking totals that, by all accounts, are never allowed to be wrong for long.""",
    "temple_saturn",
)

# --- Temple of Vesta + House of the Vestal Virgins (7) ---
room(
    "temple_vesta_approach",
    "Approach to the Temple of Vesta",
    """|YThe crowd thins noticeably|n as the road curves toward a small, circular temple - Vesta's, distinct from every rectangular building around it. |wEven casual conversation seems to quiet|n as people pass, an old habit of respect nobody quite has to be taught.""",
    "temple_vesta",
)

room(
    "temple_vesta_exterior",
    "Temple of Vesta - the Circular Shrine",
    """|YA ring of slender columns|n surrounds the temple's core, unlike any other building in the Forum - this design is said to echo the earliest Roman huts, deliberately unchanged for centuries. |cA thin trace of smoke|n rises from somewhere within.""",
    "temple_vesta",
)

room(
    "temple_vesta_sacred_fire",
    "Temple of Vesta - the Sacred Fire",
    """|YRome's eternal flame burns here|n, tended without interruption for longer than anyone living can verify by memory alone. Only a Vestal or the Pontifex Maximus himself may properly stand this close. |wYou feel distinctly like a guest who has wandered somewhere he wasn't quite invited|n - the custom here is understood, not enforced, and every Roman who's ever set foot in this city knows it.""",
    "temple_vesta",
)

room(
    "vestal_house_courtyard",
    "House of the Vestal Virgins - Entrance Courtyard",
    """|YA large, elegant courtyard|n opens beyond the temple, considerably grander than the modest shrine out front might suggest - this is a real residence, home to six of the most privileged women in Rome. |wA fountain murmurs quietly|n at the courtyard's center.""",
    "temple_vesta",
)

room(
    "vestal_house_statue_garden",
    "House of the Vestal Virgins - Statue Garden",
    """|wRows of statues|n line this quiet garden, each one a former Vestal of particular distinction, name and years of service carved into the base beneath. |gIvy has been allowed to climb some of the older ones|n, softening faces worn smooth by weather rather than disrespect.""",
    "temple_vesta",
)

room(
    "vestal_house_chamber",
    "House of the Vestal Virgins - a Private Chamber",
    """A small, plainly furnished private room - one of six identical chambers housing the Vestals themselves. |wEverything here is neat to the point of austerity|n, a life defined as much by discipline as by privilege.""",
    "temple_vesta",
)

room(
    "vestal_house_hall",
    "House of the Vestal Virgins - Dining Hall",
    """A communal hall where the six Vestals take their meals together, |wlong marble table|n set with a formality that seems to persist even when the room is empty. The atmosphere is quietly, deliberately calm.""",
    "temple_vesta",
)

# --- Temple of Castor and Pollux (5) ---
room(
    "temple_castor_facade",
    "Temple of Castor and Pollux - the Three Columns",
    """|YThree towering columns|n rise from a high podium, all that most passersby ever really look at - though the temple behind them is very much intact and in active use. Dedicated to the twin gods, protectors said to have personally appeared on Rome's behalf in battle more than once.""",
    "temple_castor",
)

room(
    "temple_castor_cella",
    "Temple of Castor and Pollux - Main Cella",
    """|YTwin cult statues|n stand side by side within, the resemblance between the two gods rendered deliberately identical. |wThe chamber smells faintly of horse and leather|n - the twins are patrons of cavalry and horsemen both, and offerings here often reflect it.""",
    "temple_castor",
)

room(
    "temple_castor_senate_chamber",
    "Temple of Castor and Pollux - Senate Chamber",
    """A side hall occasionally pressed into service for Senate meetings when the Curia itself is unavailable or unsuitable for the business at hand. |wRows of plain benches|n sit unused today, ready regardless.""",
    "temple_castor",
)

room(
    "temple_castor_measures",
    "Temple of Castor and Pollux - the Measures Room",
    """|YRome's official standard weights and measures|n are kept here, bronze and stone reference pieces against which every merchant's scale in the city can, in theory, be checked. |wA clerk sits bored behind a small table|n, present far more often than he's actually needed.""",
    "temple_castor",
)

room(
    "temple_castor_rear",
    "Temple of Castor and Pollux - Rear Precinct",
    """A quieter space behind the main temple, used for smaller private rites and the odd storage of processional equipment between festivals. |wThe noise of the square barely reaches here|n at all.""",
    "temple_castor",
)

# --- Temple of Julius Caesar (4) ---
room(
    "temple_caesar_altar",
    "Temple of Julius Caesar - the Outer Altar",
    """|YA modest altar|n marks the exact spot where Caesar's body was cremated, and it shows - fresh flowers, small coins, scraps of written prayer wedged into every crack in the stone. |wOrdinary citizens|n come here far more often than senators do; whatever Caesar was in life, in death he belongs to the people specifically.""",
    "temple_caesar",
)

room(
    "temple_caesar_steps",
    "Temple of Julius Caesar - Steps and Portico",
    """A modest set of steps leads up to the temple portico, |wsmaller and plainer|n than most of its neighbors, a deliberate choice - this temple was never meant to compete with the grand religious architecture around it, only to mark the spot.""",
    "temple_caesar",
)

room(
    "temple_caesar_cella",
    "Temple of Julius Caesar - Main Cella",
    """|YA statue of the deified Caesar|n stands within, a star carved above his head - the comet that appeared in the sky after his death, taken by many as proof of his ascension to godhood. |wThe cella is small but rarely empty|n.""",
    "temple_caesar",
)

room(
    "temple_caesar_offerings",
    "Temple of Julius Caesar - Offerings Room",
    """A side room where visitors leave what they can afford - |wcoins, small carved figures, scraps of food|n left in genuine tribute rather than any formal ritual. A priest quietly clears the older offerings each morning to make room for the day's new ones.""",
    "temple_caesar",
)

# --- Temple of Concord (5) ---
room(
    "temple_concord_steps",
    "Temple of Concord - Outer Steps",
    """|YA broad, dignified stairway|n climbs toward a temple dedicated to an idea rather than a single god - Concordia, social harmony, reconciliation between orders that don't always agree. |wThe symbolism is not lost on anyone who remembers why it was built|n.""",
    "temple_concord",
)

room(
    "temple_concord_cella",
    "Temple of Concord - Main Cella",
    """|YA serene, dignified cult statue|n of Concordia herself watches over a chamber deliberately calmer in mood than most of the temples nearby. |cThe light here is soft|n, filtered through high windows.""",
    "temple_concord",
)

room(
    "temple_concord_hall",
    "Temple of Concord - Meeting Hall",
    """A large hall occasionally used for Senate sessions, chosen specifically when the business at hand calls for exactly the symbolism this building provides. |wEmpty today|n, the hall still carries an air of careful formality.""",
    "temple_concord",
)

room(
    "temple_concord_side",
    "Temple of Concord - Gallery of Spoils",
    """|YA side chamber displaying captured artwork and spoils|n, gathered here over generations from conquests across the empire - Greek bronzes, foreign treasures, all of it repurposed as proof of Roman reach rather than left where it was made.""",
    "temple_concord",
)

room(
    "temple_concord_rear",
    "Temple of Concord - Rear Precinct",
    """A quiet space behind the temple proper, used for minor rites and the storage of ritual equipment. |wThe crowd's noise fades almost entirely back here|n.""",
    "temple_concord",
)

# --- Temple of Antoninus and Faustina (5) ---
room(
    "temple_antoninus_steps",
    "Temple of Antoninus and Faustina - the Great Steps",
    """|YA famously tall, steep flight of steps|n climbs toward one of the newer temples in the Forum, built to honor a deified emperor and his wife together. |wThe climb alone discourages casual visitors|n - which, some say, is rather the point.""",
    "temple_antoninus",
)

room(
    "temple_antoninus_portico",
    "Temple of Antoninus and Faustina - Portico",
    """|YMassive columns|n, each cut from a single block of stone, hold up a portico grand enough to rival any temple in the Forum. |wThe scale of it is meant to be felt|n, not just seen.""",
    "temple_antoninus",
)

room(
    "temple_antoninus_cella",
    "Temple of Antoninus and Faustina - Cella",
    """|YStatues of the deified emperor and empress|n stand together within, rendered with the same divine dignity given to any god of the old pantheon. The imperial cult made plain, in marble and gilt.""",
    "temple_antoninus",
)

room(
    "temple_antoninus_side",
    "Temple of Antoninus and Faustina - Side Chamber",
    """A smaller chamber to one side, used for the practical business of maintaining a temple this size - |wpriests' robes, ritual vessels, and the accumulated small necessities|n of daily worship.""",
    "temple_antoninus",
)

room(
    "temple_antoninus_rear",
    "Temple of Antoninus and Faustina - Rear Precinct",
    """A quiet precinct behind the temple, overlooking a narrow service lane. |wThe grandeur out front doesn't extend back here|n - just practical stonework and the occasional delivery cart.""",
    "temple_antoninus",
)

# --- The Regia (7) ---
room(
    "regia_courtyard",
    "The Regia - Outer Courtyard",
    """|YA modest, oddly-shaped courtyard|n, its irregular walls a genuine relic of an age before Rome had emperors at all - tradition holds this was once the residence of Rome's early kings. |wIt has never been rebuilt into something grander|n, on principle.""",
    "regia",
)

room(
    "regia_hall",
    "The Regia - Entrance Hall",
    """A small entrance hall, plain by Forum standards, serving as the official headquarters of the Pontifex Maximus - Rome's chief priest, an office the Emperor himself now holds personally. |wA single attendant|n manages an improbable amount of official business from behind a small desk.""",
    "regia",
)

room(
    "regia_chamber",
    "The Regia - the Pontifex's Chamber",
    """|YThe Pontifex Maximus's official chamber|n, where the highest religious authority in Rome conducts the business of the state religion. |wThe room is smaller than the title suggests|n - real power in Rome rarely needs to shout about itself.""",
    "regia",
)

room(
    "regia_archive",
    "The Regia - Calendar Archive",
    """|YRome's official religious calendar is kept here|n, meticulously maintained - which days are auspicious, which are not, when every festival falls. |wA small staff of priests|n cross-references entries against each other with real care; getting this wrong has real consequences for the whole city.""",
    "regia",
)

room(
    "regia_shrine",
    "The Regia - Side Shrine",
    """A small shrine tucked into a side room, dedicated to Mars and housing several of the sacred spears and shields associated with his cult. |wNo one touches these without real ceremony|n.""",
    "regia",
)

room(
    "regia_sacrificial_court",
    "The Regia - Sacrificial Courtyard",
    """An open-air courtyard used for the state sacrifices that fall under the Pontifex's direct authority. |rThe stone altar at its center bears the marks of long, continuous use|n. The air carries a faint trace of old smoke no amount of weather quite clears.""",
    "regia",
)

room(
    "regia_inner_chamber",
    "The Regia - Private Inner Chamber",
    """A restricted inner room, access understood rather than announced. |wWhatever business happens here|n stays deliberately out of the public record kept just rooms away.""",
    "regia",
)

# ------------------------------------------------------------------
# ZONE 7 - Tabularium (5 rooms)
# ------------------------------------------------------------------

room(
    "tabularium_entrance",
    "The Tabularium - Entrance Hall",
    """|YBuilt directly into the Capitoline Hill itself|n, the Tabularium's entrance hall is cool, stone-vaulted, and considerably quieter than the square outside. This is Rome's official records office - |wlaws, treaties, and state archives|n, all kept here.""",
    "tabularium",
)

room(
    "tabularium_legal_archive",
    "The Tabularium - Legal Archive",
    """|wRow upon row of shelved scrolls|n, each one a law passed, a judgment rendered, a decree issued - the actual, physical record of how Rome has governed itself for centuries. |YClerks move between the shelves|n with the quiet efficiency of people who take this seriously.""",
    "tabularium",
)

room(
    "tabularium_military_archive",
    "The Tabularium - Military Archive",
    """Records of legions raised, campaigns fought, and veterans discharged fill this section - |wmaps, muster rolls, and dispatches|n going back generations, some clearly consulted far more recently than others.""",
    "tabularium",
)

room(
    "tabularium_treaties_archive",
    "The Tabularium - Treaties and Foreign Affairs",
    """|YEvery formal treaty Rome has ever signed|n is kept here, in some cases with the original foreign seals still attached. Client kingdoms, conquered provinces, uneasy alliances - all of it documented, filed, and quietly consulted whenever a dispute resurfaces.""",
    "tabularium",
)

room(
    "tabularium_gallery",
    "The Tabularium - Upper Gallery",
    """|YA gallery cut into the hillside itself|n, offering a genuinely dramatic view out over the entire Forum below - temples, basilicas, the crowded square, all of it laid out at once. |cFew visitors leave this spot quickly|n; it's simply too good a view to rush past.""",
    "tabularium",
)

# ------------------------------------------------------------------
# ZONE 8 - Clivus Capitolinus (4 rooms)
# ------------------------------------------------------------------

room(
    "clivus_base",
    "Clivus Capitolinus - the Base of the Climb",
    """|YThe road forks upward here|n, breaking off from the Forum square to begin its climb toward the Capitoline Hill. |wThe grade is gentle at first|n, paved in the same fitted stone as the square below, though it won't stay gentle for long.""",
    "clivus",
)

room(
    "clivus_midway",
    "Clivus Capitolinus - Midway Up the Slope",
    """The road steepens noticeably here, |wswitching back once|n against the hillside. Looking back down offers a first real sense of how far the climb has already carried you above the Forum floor.""",
    "clivus",
)

room(
    "clivus_near_top",
    "Clivus Capitolinus - Near the Summit",
    """|YThe temples of the Capitoline come into view ahead|n, rooflines gilded and unmistakable even from a distance - though what stands beyond this point remains, for now, a road that simply continues further than this city has built.""",
    "clivus",
)

room(
    "clivus_switchback",
    "Clivus Capitolinus - a Quiet Switchback",
    """|YA quiet bend in the road|n, used mostly by people catching their breath rather than continuing on. |cThe view back down over the Forum from here is genuinely striking|n - the whole square, the basilicas, the temple roofs, laid out like a single enormous argument for what Rome believes about itself.""",
    "clivus",
)

# ------------------------------------------------------------------
# ZONE 9 - Commercial district (13 rooms)
# ------------------------------------------------------------------

room(
    "commerce_bankers_row",
    "Bankers' Row",
    """|YA row of stone counters and open-fronted booths|n, clustered here specifically for the treasury's proximity - argentarii doing steady business in loans, deposits, and currency exchange. |gThe click of coins being counted|n is nearly constant.""",
    "commerce",
)

room(
    "commerce_moneychanger",
    "A Moneychanger's Stall",
    """A single, well-established stall, its owner known by name to half the regulars who pass through. |YScales and a small fortune in assorted coinage|n sit openly on the counter, guarded by nothing more than the moneychanger's own reputation and a very large hired man standing nearby.""",
    "commerce",
)

room(
    "commerce_booksellers",
    "Booksellers' Corner",
    """|YRacks of tightly-rolled scrolls|n fill this small corner, copied texts ranging from philosophy to poetry to the latest gossip pamphlets from the provinces. |wA bookseller argues cheerfully|n with a customer over the accuracy of a particular copyist's hand.""",
    "commerce",
)

room(
    "commerce_goldsmiths",
    "Goldsmiths and Jewelers",
    """|YSmall, well-guarded stalls|n display rings, bracelets, and delicate gold chains, the craftsmen working in full view of passersby - partly for advertisement, partly because there's simply no room to work anywhere else.""",
    "commerce",
)

room(
    "commerce_perfumers",
    "The Perfumers' Stalls",
    """|cA thick, layered wall of scent|n hits you before you even see the stalls themselves - floral oils, exotic imported resins, and something faintly medicinal all competing at once. |gSmall glass vials|n catch the light along every counter.""",
    "commerce",
)

room(
    "commerce_market",
    "The Market Stretch",
    """|YFood vendors line both sides|n of this open stretch - roasted meat, fresh bread, fruit brought in from estates outside the city. |gThe noise and smell together are almost overwhelming|n, in the specific way that means business is good.""",
    "commerce",
)

room(
    "commerce_cloth",
    "Cloth Merchants and Tailors",
    """|YBolts of fabric|n in every color a Roman dye-house can produce hang from racks and drape over counters - wool, linen, the occasional genuine silk imported at real expense. |wA tailor measures a customer|n with practiced, rapid efficiency.""",
    "commerce",
)

room(
    "commerce_scribes",
    "Scribes and Notaries for Hire",
    """A row of small writing desks, each manned by a scribe available for hire - |wletters, contracts, legal documents|n, drafted on the spot for anyone who can't or won't write their own. Business runs entirely on Rome's appetite for putting things in writing.""",
    "commerce",
)

room(
    "commerce_luxury_alley",
    "The Luxury Alley",
    """A quieter, narrower alley off the main commercial stretch, |Yits goods considerably more expensive|n than anything on open display elsewhere - imported ivory, rare dyes, jewelry a step above the goldsmiths' usual stock. Foot traffic here is deliberately thin.""",
    "commerce",
)

room(
    "commerce_fountain_plaza",
    "The Merchants' Fountain Plaza",
    """|cA modest public fountain|n marks the point where every commercial row converges, water trickling steadily into a stone basin worn smooth by generations of hands and buckets both. |YIt's as close to a social hub as this district has|n - deals struck, gossip exchanged, appointments kept, all within sight of the same water.""",
    "commerce",
)

room(
    "commerce_auction_platform",
    "The Auctioneer's Platform",
    """|YA raised wooden platform|n where a herald's voice carries easily over the surrounding stalls, auctioning off everything from imported pottery to a disputed estate's leftover furniture. |wA small crowd|n has gathered, more out of habit than any real interest in bidding.""",
    "commerce",
)

room(
    "commerce_porters_yard",
    "The Porters' Staging Yard",
    """A working yard rather than a shopfront - |wcarts, crates, and hired porters|n waiting to haul goods wherever they're needed next. The atmosphere here is entirely different from the shopper-facing rows nearby: less selling, more sheer physical labor.""",
    "commerce",
)

room(
    "commerce_argiletum_exit",
    "Toward the Argiletum",
    """|YThe commercial district thins out here|n, stalls growing sparser as the road bends north, toward the Subura beyond. A street sign, carved and half-worn, marks this as the start of the Argiletum - |wa road that, for now, simply continues further than this city has been built|n.""",
    "commerce",
)

# ============================================================
# LINKS - each tuple is (room_a, dir_a_to_b, room_b, dir_b_to_a).
# "existing_via_sacra" is a special key mapped, at execution time, to
# the real already-built Via Sacra room (#661) rather than a new room -
# this is the actual attachment point to last session's road work.
# Defining links (not per-room exit dicts) makes a duplicate-direction
# collision on one room structurally impossible to introduce by
# accident for any SINGLE link - the validator below still checks
# across all links touching a room, since a room can appear in many.
# ============================================================

LINKS = [
    # --- Zone 1: Via Sacra spine ---
    ("existing_via_sacra", "west", "via_sacra_arch_approach", "east"),
    ("via_sacra_arch_approach", "west", "arch_of_titus", "east"),
    ("arch_of_titus", "west", "via_sacra_shrines", "east"),
    ("via_sacra_shrines", "west", "via_sacra_colonnade", "east"),
    ("via_sacra_colonnade", "west", "forum_square_approach", "east"),
    ("forum_square_approach", "west", "forum_threshold", "east"),
    ("forum_threshold", "west", "forum_square_east", "east"),

    # --- Zone 2: main square ---
    ("forum_square_east", "west", "forum_square_central", "east"),
    ("forum_square_central", "north", "forum_comitium", "south"),
    ("forum_square_central", "south", "forum_square_south", "north"),
    ("forum_square_central", "west", "forum_square_west", "east"),
    ("forum_comitium", "north", "forum_rostra", "south"),
    ("forum_comitium", "east", "forum_golden_milestone", "west"),
    ("forum_comitium", "west", "curia_portico", "east"),
    ("forum_square_west", "south", "temple_saturn_steps", "north"),
    ("forum_square_west", "north", "tabularium_entrance", "south"),
    ("forum_square_west", "west", "clivus_base", "east"),
    ("forum_square_south", "south", "basilica_julia_entrance", "north"),
    ("forum_square_south", "east", "temple_castor_facade", "west"),
    ("forum_square_south", "west", "basilica_julia_rear_exit", "east"),
    ("forum_square_east", "north", "basilica_aemilia_entrance", "south"),
    ("forum_square_east", "south", "basilica_aemilia_rear_exit", "north"),

    # --- Zone 3: Curia Julia ---
    # Retrofitted live to a real door - see the Saturn Vault comment above.
    ("curia_portico", "north", "curia_antechamber", "south"),
    ("curia_antechamber", "north", "curia_chamber", "south"),
    ("curia_chamber", "east", "curia_side_chamber", "west"),
    ("curia_chamber", "west", "curia_records_room", "east"),
    ("curia_chamber", "north", "curia_rear_chamber", "south"),

    # --- Zone 4: Basilica Julia ---
    ("basilica_julia_entrance", "up", "basilica_julia_gallery", "down"),
    ("basilica_julia_gallery", "east", "basilica_julia_court1", "west"),
    ("basilica_julia_gallery", "west", "basilica_julia_court2", "east"),
    ("basilica_julia_gallery", "north", "basilica_julia_tabernae_a", "south"),
    ("basilica_julia_gallery", "up", "basilica_julia_upper_gallery", "down"),
    ("basilica_julia_court1", "south", "basilica_julia_consult_hall", "north"),
    ("basilica_julia_tabernae_a", "east", "basilica_julia_tabernae_b", "west"),
    ("basilica_julia_tabernae_b", "north", "basilica_julia_rear_exit", "south"),

    # --- Zone 5: Basilica Aemilia ---
    ("basilica_aemilia_entrance", "north", "basilica_aemilia_hall", "south"),
    ("basilica_aemilia_hall", "east", "basilica_aemilia_court1", "west"),
    ("basilica_aemilia_hall", "west", "basilica_aemilia_court2", "east"),
    ("basilica_aemilia_hall", "north", "basilica_aemilia_tabernae_a", "south"),
    ("basilica_aemilia_hall", "up", "basilica_aemilia_upper_gallery", "down"),
    ("basilica_aemilia_tabernae_a", "east", "basilica_aemilia_tabernae_b", "west"),
    ("basilica_aemilia_tabernae_b", "north", "basilica_aemilia_moneylenders", "south"),
    ("basilica_aemilia_tabernae_b", "east", "temple_antoninus_steps", "west"),
    ("basilica_aemilia_moneylenders", "east", "basilica_aemilia_rear_exit", "west"),

    # --- Zone 6: Temple cluster ---
    # Temple of Saturn
    ("temple_saturn_steps", "up", "temple_saturn_cella", "down"),
    ("temple_saturn_cella", "east", "temple_saturn_side", "west"),
    ("temple_saturn_cella", "south", "temple_saturn_aerarium_ante", "north"),
    # Retrofitted live to a real world.doors.DescriptiveDoor pair - the
    # room's own desc already promised "a heavy, iron-bound door" here
    # that didn't mechanically exist. This LINKS entry is historical
    # (setup_forum_live.py already ran and isn't meant to be re-run
    # against a populated DB) - kept as plain-exit data for the record,
    # not because re-applying it would recreate the door correctly.
    ("temple_saturn_aerarium_ante", "down", "temple_saturn_vault", "up"),
    ("temple_saturn_aerarium_ante", "west", "temple_saturn_records", "east"),
    ("temple_saturn_side", "east", "temple_concord_steps", "west"),
    ("temple_saturn_records", "south", "commerce_bankers_row", "north"),
    # Temple of Concord
    ("temple_concord_steps", "north", "temple_concord_cella", "south"),
    ("temple_concord_cella", "north", "temple_concord_hall", "south"),
    ("temple_concord_cella", "east", "temple_concord_side", "west"),
    ("temple_concord_hall", "east", "temple_concord_rear", "west"),
    # Temple of Antoninus and Faustina
    ("temple_antoninus_steps", "north", "temple_antoninus_portico", "south"),
    ("temple_antoninus_portico", "north", "temple_antoninus_cella", "south"),
    ("temple_antoninus_cella", "east", "temple_antoninus_side", "west"),
    ("temple_antoninus_cella", "north", "temple_antoninus_rear", "south"),
    # Temple of Castor and Pollux
    ("temple_castor_facade", "east", "temple_castor_cella", "west"),
    ("temple_castor_cella", "east", "temple_castor_senate_chamber", "west"),
    ("temple_castor_cella", "south", "temple_castor_measures", "north"),
    ("temple_castor_cella", "north", "temple_castor_rear", "south"),
    ("temple_castor_rear", "east", "temple_caesar_altar", "west"),
    # Temple of Julius Caesar
    ("temple_caesar_altar", "east", "temple_caesar_steps", "west"),
    ("temple_caesar_altar", "south", "temple_vesta_approach", "north"),
    ("temple_caesar_steps", "east", "temple_caesar_cella", "west"),
    ("temple_caesar_cella", "east", "temple_caesar_offerings", "west"),
    # Temple of Vesta + House of the Vestals
    ("temple_vesta_approach", "south", "temple_vesta_exterior", "north"),
    # Retrofitted live to a real door - see the Saturn Vault comment above.
    ("temple_vesta_exterior", "south", "temple_vesta_sacred_fire", "north"),
    ("temple_vesta_exterior", "east", "vestal_house_courtyard", "west"),
    ("vestal_house_courtyard", "east", "vestal_house_statue_garden", "west"),
    ("vestal_house_courtyard", "south", "vestal_house_hall", "north"),
    ("vestal_house_statue_garden", "south", "vestal_house_chamber", "north"),
    ("vestal_house_courtyard", "north", "regia_courtyard", "south"),
    # The Regia
    ("regia_courtyard", "north", "regia_hall", "south"),
    ("regia_courtyard", "east", "regia_sacrificial_court", "west"),
    ("regia_hall", "north", "regia_chamber", "south"),
    ("regia_chamber", "east", "regia_archive", "west"),
    ("regia_chamber", "west", "regia_shrine", "east"),
    ("regia_chamber", "north", "regia_inner_chamber", "south"),

    # --- Zone 7: Tabularium ---
    ("tabularium_entrance", "north", "tabularium_legal_archive", "south"),
    ("tabularium_legal_archive", "east", "tabularium_military_archive", "west"),
    ("tabularium_legal_archive", "west", "tabularium_treaties_archive", "east"),
    ("tabularium_legal_archive", "north", "tabularium_gallery", "south"),

    # --- Zone 8: Clivus Capitolinus ---
    ("clivus_base", "north", "clivus_midway", "south"),
    ("clivus_midway", "north", "clivus_near_top", "south"),
    ("clivus_near_top", "east", "clivus_switchback", "west"),

    # --- Zone 9: Commercial district ---
    ("commerce_bankers_row", "east", "commerce_moneychanger", "west"),
    ("commerce_bankers_row", "south", "commerce_fountain_plaza", "north"),
    ("commerce_fountain_plaza", "east", "commerce_booksellers", "west"),
    ("commerce_fountain_plaza", "south", "commerce_market", "north"),
    ("commerce_fountain_plaza", "west", "commerce_cloth", "east"),
    ("commerce_booksellers", "east", "commerce_goldsmiths", "west"),
    ("commerce_goldsmiths", "east", "commerce_perfumers", "west"),
    ("commerce_market", "east", "commerce_scribes", "west"),
    ("commerce_market", "south", "commerce_porters_yard", "north"),
    ("commerce_cloth", "south", "commerce_luxury_alley", "north"),
    ("commerce_luxury_alley", "east", "commerce_auction_platform", "west"),
    ("commerce_auction_platform", "south", "commerce_argiletum_exit", "north"),
]

# ============================================================
# NPCS
# ============================================================
# Each entry: (room_key, name, desc, kind, extra)
#   kind "static"    - plain DefaultCharacter, stays put
#   kind "wander"    - DefaultCharacter + WanderingNPC script, extra
#                       is a list of room keys it's allowed to wander
#   kind "merchant"  - NPCMerchant, extra is a list of prototype keys
#                       to stock

NPCS = [
    # --- Wandering flavor NPCs ---
    (
        "forum_square_central", "a toga-clad Senator", "static",
        "A middle-aged man in a toga marked with the broad purple stripe "
        "of the senatorial order, moving through the square with the "
        "unhurried confidence of someone who belongs everywhere he goes.",
        None,
    ),
    (
        "forum_square_central", "a wandering herald", "wander",
        "A herald with a genuinely enormous voice, currently resting it, "
        "moving between the square's busiest corners in search of the "
        "next thing worth announcing.",
        ["forum_square_central", "forum_square_east", "forum_square_south",
         "forum_square_west", "forum_rostra", "forum_comitium"],
    ),
    (
        "temple_vesta_approach", "a Vestal Virgin", "wander",
        "A woman in white robes, hair bound in the distinctive style "
        "reserved for Vesta's priestesses, moving with quiet, practiced "
        "composure between the temple and the house behind it.",
        ["temple_vesta_approach", "temple_vesta_exterior",
         "vestal_house_courtyard", "vestal_house_statue_garden"],
    ),
    (
        "commerce_fountain_plaza", "a haggling commoner", "wander",
        "An ordinary Roman in a plain tunic, currently mid-argument with "
        "a vendor over the price of something, moving on to the next "
        "stall the moment this one refuses to budge.",
        ["commerce_fountain_plaza", "commerce_market", "commerce_cloth",
         "commerce_booksellers", "commerce_bankers_row"],
    ),
    (
        "temple_saturn_steps", "a beggar", "wander",
        "A thin, weathered figure seated near the temple steps more "
        "often than not, palm out, voice pitched to a practiced, "
        "unbothered murmur that somehow still carries.",
        ["temple_saturn_steps", "temple_concord_steps",
         "temple_castor_facade", "forum_square_west"],
    ),
    (
        "via_sacra_shrines", "a foreign merchant", "wander",
        "A traveler in unfamiliar dress, dark cloth wound differently "
        "than any toga, clearly more interested in the shrines' craft "
        "than their gods - a visitor from somewhere the Empire has only "
        "recently reached.",
        ["via_sacra_shrines", "via_sacra_colonnade", "forum_square_approach"],
    ),

    # --- Static flavor NPCs ---
    (
        "curia_portico", "a Curia lictor", "static",
        "An attendant standing near the Senate House entrance, a bundle "
        "of rods carried more as symbol than weapon, present to remind "
        "everyone passing exactly whose business happens inside.",
        None,
    ),
    (
        "curia_records_room", "a Senate clerk", "static",
        "A clerk hunched over a writing desk, stylus moving in short, "
        "practiced strokes, cataloguing the day's proceedings before "
        "anyone has the chance to remember them differently.",
        None,
    ),
    (
        "basilica_julia_court1", "an advocate", "static",
        "A lawyer mid-argument, voice pitched to carry, gesturing with "
        "the kind of practiced conviction that has very little to do "
        "with how the case is actually going.",
        None,
    ),
    (
        "basilica_aemilia_court1", "a shipping advocate", "static",
        "A lawyer arguing the fine details of a maritime contract, "
        "clearly more comfortable with cargo manifests than courtroom "
        "theater.",
        None,
    ),
    (
        "basilica_aemilia_moneylenders", "a moneylender", "static",
        "A man with an open ledger and a closed expression, doing the "
        "kind of quiet arithmetic that decides who eats well this month "
        "and who doesn't.",
        None,
    ),
    (
        "temple_saturn_aerarium_ante", "a treasury clerk", "static",
        "A clerk seated behind a small table, checking names against a "
        "list with the patient thoroughness of someone who has been "
        "told, more than once, exactly what happens if he gets this "
        "wrong.",
        None,
    ),
    (
        "temple_saturn_vault", "a treasury guard", "static",
        "An armed guard standing utterly still, unblinking, entirely "
        "unimpressed by anyone who wanders in without a very good "
        "reason.",
        None,
    ),
    (
        "regia_hall", "the Pontifex's attendant", "static",
        "An attendant managing an improbable volume of official business "
        "from behind a small desk, sorting priests, petitioners, and "
        "paperwork with the same brisk efficiency.",
        None,
    ),
    (
        "regia_archive", "a calendar priest", "static",
        "A priest cross-referencing entries in the religious calendar "
        "with real, visible care - getting a festival date wrong here "
        "has consequences for the entire city.",
        None,
    ),
    (
        "tabularium_legal_archive", "an archive clerk", "static",
        "A clerk moving between shelves of law and judgment with the "
        "quiet efficiency of someone who genuinely enjoys knowing where "
        "everything is.",
        None,
    ),
    (
        "temple_caesar_altar", "a grieving citizen", "static",
        "An older man kneeling briefly at the altar, leaving a small "
        "offering, murmuring something too quiet to make out before "
        "moving on - one of many who still come here, decades on.",
        None,
    ),

    # --- Shopkeepers (real NPCMerchants, matching the established
    # Colosseum vendor / Ludus weaponsmith pattern) ---
    (
        "commerce_booksellers", "a bookseller", "merchant",
        "A bookseller surrounded by tightly-rolled scrolls, cheerfully "
        "opinionated about which copyist's hand is actually worth the "
        "price being asked.",
        ["SCROLL_OF_POETRY", "SCROLL_OF_HISTORY", "MAP_OF_ROME"],
    ),
    (
        "commerce_goldsmiths", "a goldsmith", "merchant",
        "A goldsmith working in full view of the street, small tools "
        "moving with total precision despite the constant foot traffic "
        "just past his counter.",
        ["GOLD_RING", "GOLD_BRACELET"],
    ),
    (
        "commerce_perfumers", "a perfumer", "merchant",
        "A perfumer surrounded by small glass vials, each one uncorked "
        "just long enough to make a sale before being sealed again "
        "against the open air.",
        ["VIAL_OF_PERFUME"],
    ),
    (
        "commerce_market", "a food vendor", "merchant",
        "A vendor working a small brazier, the smell of roasting meat "
        "doing more of the selling than she ever has to.",
        ["ROASTED_MEAT_SKEWER", "HONEYED_BREAD"],
    ),
]

# ============================================================
# OBJECTS - lookable scenery, get:false() locked (never pickupable),
# matching the fountain pattern already established in the Meta Sudans.
# ============================================================

OBJECTS = [
    (
        "forum_rostra", "the rostra's bronze prows",
        "A row of real bronze ship prows, taken from enemy warships "
        "generations ago and mounted along the platform's face - a "
        "permanent, physical boast that gave this platform its name. "
        "Every one of them was once the front of a vessel that lost."
    ),
    (
        "forum_golden_milestone", "the Golden Milestone",
        "A gilded bronze column, unassuming in size but not in claim - "
        "every road in the empire is measured from this exact point. "
        "Distances are carved into the bronze in careful Latin numerals, "
        "naming cities most Romans will only ever hear of."
    ),
    (
        "curia_chamber", "the statue of Victory",
        "A gilded statue of the goddess Victory stands at the altar, "
        "wings spread, one hand extended as if offering something to "
        "whoever stands before her. Every Senate session formally opens "
        "in her presence."
    ),
    (
        "temple_saturn_cella", "the cult statue of Saturn",
        "An old statue of the god, paint faded to a shadow of what it "
        "once was, feet bound in wool cord for most of the year per an "
        "ancient custom nobody living remembers the original reason for."
    ),
    (
        "vestal_house_statue_garden", "the statues of former Vestals",
        "Rows of marble statues, each one a Vestal of particular "
        "historical distinction, name and years of service carved into "
        "the base. Ivy has been allowed to soften some of the older "
        "faces, worn as much by weather as by time."
    ),
    (
        "temple_concord_cella", "the statue of Concordia",
        "A serene cult statue of Concordia, rendered without the usual "
        "martial trappings of most Roman religious art - an olive branch "
        "in one hand, an open, upturned palm in the other."
    ),
    (
        "temple_castor_cella", "the twin statues of Castor and Pollux",
        "Two cult statues stand side by side, rendered deliberately "
        "identical - the resemblance between the divine twins left "
        "entirely unresolved by the sculptor, on purpose."
    ),
    (
        "forum_square_central", "a painted statue",
        "A statue of some minor civic figure, name half-worn from its "
        "base, still bearing traces of the original paint - reds and "
        "golds on the toga, flesh-tones on the face - a reminder that "
        "none of this was ever meant to look like bare stone."
    ),
    (
        "temple_antoninus_cella", "the statues of Antoninus and Faustina",
        "Statues of the deified emperor and empress stand together, "
        "rendered with the same divine dignity given to any god of the "
        "old pantheon - the imperial cult made plain in marble and gilt."
    ),
    # A real bug found live: the room's own desc already described this
    # statue in prose (the star, the comet) but nothing player-
    # examinable actually existed here - same gap as the Capitoline
    # Triad, fixed the same way. New detail below, not a restatement.
    (
        "temple_caesar_cella", "the statue of the deified Caesar",
        "A sliver of real polished silver is set into the carved star "
        "above his head, catching lamplight independently of the "
        "surrounding marble - a small, deliberate extravagance in an "
        "otherwise modest cella. The toga is carved mid-motion, as if "
        "caught walking rather than posing."
    ),
]

# ============================================================
# ECHOES - room_key -> list of ambient messages, using the same
# ColosseumEcho script already built for exactly this purpose.
# ============================================================

ECHOES = {
    "forum_square_central": [
        "|YA vendor's voice cuts through the crowd, hawking something impossible to make out from here.|n",
        "|cSomewhere nearby, an argument breaks out over a betting debt.|n",
        "|YA distant voice from the Rostra rises briefly over the general noise.|n",
        "|wThe smell of incense drifts across the square from one of the temples.|n",
    ],
    "forum_rostra": [
        "|YA voice - not yours - carries out over an imagined crowd, mid-argument.|n",
        "|cThe worn stone underfoot creaks faintly, familiar with the weight of speakers.|n",
    ],
    "basilica_julia_gallery": [
        "|wAn advocate's raised voice echoes from one of the court chambers.|n",
        "|YSomewhere above, footsteps cross the upper gallery.|n",
    ],
    "basilica_aemilia_hall": [
        "|wVoices from a court chamber rise and fall in practiced argument.|n",
        "|YA merchant haggles loudly over goods somewhere in the tabernae row.|n",
    ],
    "commerce_fountain_plaza": [
        "|cWater trickles steadily into the fountain's stone basin.|n",
        "|gA vendor calls out a price, then immediately a better one.|n",
        "|YCoins change hands somewhere nearby, more than once.|n",
    ],
    "commerce_market": [
        "|gThe smell of roasting meat drifts past, briefly overpowering everything else.|n",
        "|YA vendor calls out the day's prices to no one in particular.|n",
    ],
    "regia_sacrificial_court": [
        "|rA faint trace of old smoke lingers in the air, never quite clearing.|n",
        "|wA low, measured chant drifts from somewhere just out of sight.|n",
    ],
    "temple_vesta_sacred_fire": [
        "|cThe sacred flame shifts and crackles softly, tended by hands you can't see from here.|n",
    ],
    "tabularium_gallery": [
        "|cWind moves faintly through the gallery, carrying the Forum's noise up from far below.|n",
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

    all_keys = set(ROOMS.keys()) | {"existing_via_sacra"}

    # 1. every room name must be unique (case-sensitive exact match -
    # the real duplicate-detection this session's live audits used)
    names = [r["name"] for r in ROOMS.values()]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        errors.append("Duplicate room names: %s" % dupes)

    # 2. every link must reference real room keys
    for a, da, b, db in LINKS:
        if a not in all_keys:
            errors.append("Link references unknown room: %s" % a)
        if b not in all_keys:
            errors.append("Link references unknown room: %s" % b)
        if _reverse_dir(da) is None or _reverse_dir(db) is None:
            errors.append("Unrecognized direction in link %s" % ((a, da, b, db),))

    # 3. no room may use the same exit direction twice (the exact bug
    # class caught live in the Meta Sudans build)
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

    # 4. every room must be reachable from the entry point via BFS
    adjacency = {}
    for a, da, b, db in LINKS:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    visited = set()
    queue = ["existing_via_sacra"]
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

    # 5. NPCs/objects/echoes must reference real rooms
    for entry in NPCS:
        room_key = entry[0]
        if room_key not in all_keys:
            errors.append("NPC references unknown room: %s" % room_key)
        if entry[2] == "wander":
            for wr in entry[4]:
                if wr not in all_keys:
                    errors.append("Wander room unknown: %s" % wr)
    for room_key, _, _ in OBJECTS:
        if room_key not in all_keys:
            errors.append("Object references unknown room: %s" % room_key)
    for room_key in ECHOES:
        if room_key not in all_keys:
            errors.append("Echo references unknown room: %s" % room_key)

    return errors


if __name__ == "__main__":
    print("Loaded %d new rooms (99 total including the existing Via Sacra room)." % len(ROOMS))
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
