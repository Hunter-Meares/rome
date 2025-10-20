<p align="center">
  <img src="assets/hero-bg.jpg" width="400">
</p>

# Rome — An Evennia-Based Multiplayer Text Adventure

**Rome** is a custom multiplayer text-based game built using the  
[Evennia MUD framework (Python + Django)](https://www.evennia.com/).  
Players explore, scheme, build power, command legions, and shape the fate of an empire.

---

### Play the Game
**Homepage:** https://rome.vineyard.haus/

---

### Project Overview

This project blends elements of:
- Roman history and mythology  
- Political roleplay and intrigue  
- PvE and PvP progression  
- Exploration, faction conflicts, and character development

Rome is currently in development and will evolve as more systems, lore, and mechanics are introduced.

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
git clone https://github.com/Reese-Thurman/rome.git
cd rome

# Install dependencies
pip install evennia

# Setup database (first time only)
evennia migrate

# Start the game
evennia start
