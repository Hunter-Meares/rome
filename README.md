<p align="center">
  <img src="hero-bg.jpg" width="400">
</p>

# Rome: The Eternal City - A Roman Roleplay MUD

**Rome: The Eternal City** is a free, text-based multiplayer **MUD** (Multi-User
Dungeon) set at the height of the Roman Empire, where the myths are true and the
gods actively shape the story. It is built on the
[Evennia MUD framework (Python + Django)](https://www.evennia.com/) and is a
roleplay-enforced world: players explore, scheme, craft, build power, and shape
the fate of an empire - or play a permanent pacifist and never draw a weapon.

---

### Play the Game
**Website:** https://rome.vineyard.haus/ - play instantly in your browser, or
connect with Mudlet, a MUSH client, or a mobile client.
**Discord:** https://discord.gg/uh6HPvuM42

New to MUDs? A MUD is a text-based online multiplayer game: you read a
description of the world, type commands to act, and share it with other players
in real time. See the [FAQ](https://rome.vineyard.haus/faq.html#what-is-a-mud).

---

### What's Built

Rome is in a Player Testing phase - the core game is complete and playable, and
under active development.

- **World:** over 800 rooms - the Colosseum and Ludus, the Forum Romanum and
  Capitoline Hill, the Subura, Trajan's Market, the Library of Rome, the Domus
  Aurea, the Aventine, the Pantheon and Campus Martius, the Palatine, the Baths,
  noble houses, the Cloaca Maxima sewers, the Underworld, a wilderness road out
  through the Porta Flaminia, the Germanic Stronghold, and the Amber Coast.
- **Characters:** 6 races and 8 classes, four core stats, levelling and
  stat points, earned titles and achievements.
- **Combat:** turn-based, with initiative, spells and skills, status conditions,
  gear, front/back row positioning, parties, and summoned companions and pets.
- **Crafting and economy:** gathering, two professions (Faber, Herbalist),
  fixed-location workshops, trainers, and merchants with distance and specialty
  bonuses.
- **Pacifism:** a permanent, one-way opt-out of combat for players who want to
  focus on roleplay, with crafting as their path forward.
- **Roleplay:** quests, a bounty board, eight factions and cults, devotion to
  fourteen gods, languages, 80 socials, descriptions, masks, and in-game mail.

Still ahead: a player-to-player marketplace, more crafting professions, more
races' signature abilities, and more of the world beyond Rome.

---

### Branches

| Branch | Purpose |
|---------|---------|
| `main` | Stable, production-ready code |
| `dev` | Active development (features, experiments, testing) |

Development happens on `dev`.  
Only proven, stable features are merged into `main`.

---

### Local Development

```bash
# Clone the repo
git clone https://github.com/Hunter-Meares/rome.git
cd rome

# Install dependencies
pip install evennia

# First-time setup only: create your own secret key.
# server/conf/secret_settings.py is gitignored (never committed) -
# the server will still start without it, falling back to Evennia's
# own default key with a warning, but a real deployment should
# always set its own. Create the file with:
#   SECRET_KEY = "<a long random string>"
# (see server/conf/secret_settings.py.example for the exact format)

# Setup database (first time only)
evennia migrate

# Start the game
evennia start
```

