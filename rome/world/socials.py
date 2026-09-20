"""
Social commands (emotes) - the genre-standard "socials" library every
major Diku/ROM/Circle-derived MUD ships with (smile, wave, bow, and
so on), built here as native content since Evennia doesn't bundle one.

One data-driven dispatcher (CmdSocial below) backed by the SOCIALS
dict, rather than ~90 hand-written command classes - each entry is
instantiated as its own thin Command with `key` set to the social's
own name, all sharing the exact same func(). Adding a new social later
is a one-line dict entry, not a new class.

Every entry has two message pairs:
    "no_target": (what the actor sees, what the room sees)
    "targeted":  (what the actor sees, what the target sees,
                  what everyone else in the room sees)
{name} is replaced with the actor's own display name, {target} with
the target's.

Deliberately simple by direct request ("keep them simple and
intuitive... no multiple word socials"):
  - Every social name is a single word - no "roll eyes"/"shake head"
    style commands requiring an exact multi-word phrase.
  - Targeting yourself falls back to the plain no-target message
    rather than a separate hand-written reflexive line for all ~90
    entries - simpler to build and to read, at the cost of the
    (optional, not requested) more elaborate self-target flavor a
    fuller design could add later.
  - Checked against every existing command key/alias in the game
    before finalizing this list - two real, direct collisions were
    found and handled: "greet" already exists as a real, mechanically
    important command (the mask-proof identity-reveal tied to the
    sdesc/mask/recog system, world/combat.py's CmdGreet) and "hold" is
    already an alias of CmdPass ("hold your action" in combat) - both
    dropped from this list entirely rather than forced into an
    awkward rename.
"""

from commands.command import Command

SOCIALS = {
    # --- Friendly / Affectionate ---
    "smile": {
        "no_target": ("You smile.", "{name} smiles."),
        "targeted": ("You smile at {target}.", "{name} smiles at you.", "{name} smiles at {target}."),
    },
    "grin": {
        "no_target": ("You grin.", "{name} grins."),
        "targeted": ("You grin at {target}.", "{name} grins at you.", "{name} grins at {target}."),
    },
    "laugh": {
        "no_target": ("You laugh.", "{name} laughs."),
        "targeted": ("You laugh with {target}.", "{name} laughs with you.", "{name} laughs with {target}."),
    },
    "chuckle": {
        "no_target": ("You chuckle.", "{name} chuckles."),
        "targeted": ("You chuckle at {target}.", "{name} chuckles at you.", "{name} chuckles at {target}."),
    },
    "wave": {
        "no_target": ("You wave.", "{name} waves."),
        "targeted": ("You wave at {target}.", "{name} waves at you.", "{name} waves at {target}."),
    },
    "hug": {
        "no_target": ("You spread your arms for a hug, but there's no one here to give one to.", "{name} spreads their arms for a hug that goes ungiven."),
        "targeted": ("You hug {target}.", "{name} hugs you.", "{name} hugs {target}."),
    },
    "embrace": {
        "no_target": ("You wrap your arms around yourself for a moment.", "{name} wraps their arms around themself for a moment."),
        "targeted": ("You embrace {target} warmly.", "{name} embraces you warmly.", "{name} embraces {target} warmly."),
    },
    "cuddle": {
        "no_target": ("You could use a cuddle, but there's no one here to give one.", "{name} looks like they could use a cuddle."),
        "targeted": ("You cuddle up to {target}.", "{name} cuddles up to you.", "{name} cuddles up to {target}."),
    },
    "kiss": {
        "no_target": ("You purse your lips, but there's no one here to kiss.", "{name} purses their lips at no one in particular."),
        "targeted": ("You kiss {target}.", "{name} kisses you.", "{name} kisses {target}."),
    },
    "nuzzle": {
        "no_target": ("You have no one to nuzzle.", "{name} looks like they have no one to nuzzle."),
        "targeted": ("You nuzzle {target} affectionately.", "{name} nuzzles you affectionately.", "{name} nuzzles {target} affectionately."),
    },
    "pat": {
        "no_target": ("You pat the air, feeling a little silly.", "{name} pats the air, looking a little silly."),
        "targeted": ("You pat {target} on the back.", "{name} pats you on the back.", "{name} pats {target} on the back."),
    },
    "highfive": {
        "no_target": ("You raise a hand for a high-five that goes ungiven.", "{name} raises a hand for a high-five that goes ungiven."),
        "targeted": ("You high-five {target}.", "{name} high-fives you.", "{name} high-fives {target}."),
    },
    "handshake": {
        "no_target": ("You offer a handshake to no one in particular.", "{name} offers a handshake to no one in particular."),
        "targeted": ("You shake hands with {target}.", "{name} shakes hands with you.", "{name} shakes hands with {target}."),
    },
    "comfort": {
        "no_target": ("You could use some comforting yourself.", "{name} looks like they could use some comforting."),
        "targeted": ("You offer {target} a few words of comfort.", "{name} offers you a few words of comfort.", "{name} offers {target} a few words of comfort."),
    },
    "toast": {
        "no_target": ("You raise an imaginary cup in a toast.", "{name} raises an imaginary cup in a toast."),
        "targeted": ("You raise your cup and toast {target}.", "{name} raises their cup and toasts you.", "{name} raises their cup and toasts {target}."),
    },
    "snuggle": {
        "no_target": ("You wrap your arms around yourself.", "{name} wraps their arms around themself."),
        "targeted": ("You snuggle close to {target}.", "{name} snuggles close to you.", "{name} snuggles close to {target}."),
    },

    # --- Playful / Teasing ---
    "wink": {
        "no_target": ("You wink.", "{name} winks."),
        "targeted": ("You wink at {target}.", "{name} winks at you.", "{name} winks at {target}."),
    },
    "giggle": {
        "no_target": ("You giggle.", "{name} giggles."),
        "targeted": ("You giggle at {target}.", "{name} giggles at you.", "{name} giggles at {target}."),
    },
    "snicker": {
        "no_target": ("You snicker.", "{name} snickers."),
        "targeted": ("You snicker at {target}.", "{name} snickers at you.", "{name} snickers at {target}."),
    },
    "smirk": {
        "no_target": ("You smirk.", "{name} smirks."),
        "targeted": ("You smirk at {target}.", "{name} smirks at you.", "{name} smirks at {target}."),
    },
    "tease": {
        "no_target": ("You look around for someone to tease, but come up empty.", "{name} looks around for someone to tease."),
        "targeted": ("You tease {target} mercilessly.", "{name} teases you mercilessly.", "{name} teases {target} mercilessly."),
    },
    "poke": {
        "no_target": ("You poke at the air.", "{name} pokes at the air."),
        "targeted": ("You poke {target}.", "{name} pokes you.", "{name} pokes {target}."),
    },
    "tickle": {
        "no_target": ("You wiggle your fingers menacingly at no one.", "{name} wiggles their fingers menacingly at no one."),
        "targeted": ("You tickle {target}.", "{name} tickles you.", "{name} tickles {target}."),
    },
    "nudge": {
        "no_target": ("You nudge no one in particular.", "{name} nudges no one in particular."),
        "targeted": ("You nudge {target}.", "{name} nudges you.", "{name} nudges {target}."),
    },
    "flirt": {
        "no_target": ("You feel flirtatious, but there's no one here to notice.", "{name} looks distinctly flirtatious."),
        "targeted": ("You flirt shamelessly with {target}.", "{name} flirts shamelessly with you.", "{name} flirts shamelessly with {target}."),
    },
    "dance": {
        "no_target": ("You dance a few steps, alone.", "{name} dances a few steps, alone."),
        "targeted": ("You pull {target} into a dance.", "{name} pulls you into a dance.", "{name} pulls {target} into a dance."),
    },
    "twirl": {
        "no_target": ("You twirl in place.", "{name} twirls in place."),
        "targeted": ("You take {target}'s hand and twirl them.", "{name} takes your hand and twirls you.", "{name} takes {target}'s hand and twirls them."),
    },
    "blush": {
        "no_target": ("You blush.", "{name} blushes."),
        "targeted": ("You blush at {target}.", "{name} blushes at you.", "{name} blushes at {target}."),
    },
    "tongue": {
        "no_target": ("You stick out your tongue.", "{name} sticks out their tongue."),
        "targeted": ("You stick your tongue out at {target}.", "{name} sticks their tongue out at you.", "{name} sticks their tongue out at {target}."),
    },
    "purr": {
        "no_target": ("You make a low, satisfied sound.", "{name} makes a low, satisfied sound."),
        "targeted": ("You purr at {target}.", "{name} purrs at you.", "{name} purrs at {target}."),
    },

    # --- Sympathetic / Melancholy ---
    "sigh": {
        "no_target": ("You sigh.", "{name} sighs."),
        "targeted": ("You sigh at {target}.", "{name} sighs at you.", "{name} sighs at {target}."),
    },
    "cry": {
        "no_target": ("You cry.", "{name} cries."),
        "targeted": ("You cry on {target}'s shoulder.", "{name} cries on your shoulder.", "{name} cries on {target}'s shoulder."),
    },
    "sob": {
        "no_target": ("You sob quietly.", "{name} sobs quietly."),
        "targeted": ("You sob into {target}'s shoulder.", "{name} sobs into your shoulder.", "{name} sobs into {target}'s shoulder."),
    },
    "weep": {
        "no_target": ("You weep.", "{name} weeps."),
        "targeted": ("You weep before {target}.", "{name} weeps before you.", "{name} weeps before {target}."),
    },
    "pout": {
        "no_target": ("You pout.", "{name} pouts."),
        "targeted": ("You pout at {target}.", "{name} pouts at you.", "{name} pouts at {target}."),
    },
    "frown": {
        "no_target": ("You frown.", "{name} frowns."),
        "targeted": ("You frown at {target}.", "{name} frowns at you.", "{name} frowns at {target}."),
    },
    "whimper": {
        "no_target": ("You whimper.", "{name} whimpers."),
        "targeted": ("You whimper at {target}.", "{name} whimpers at you.", "{name} whimpers at {target}."),
    },
    "shiver": {
        "no_target": ("You shiver.", "{name} shivers."),
        "targeted": ("You shiver and press close to {target}.", "{name} shivers and presses close to you.", "{name} shivers and presses close to {target}."),
    },
    "tremble": {
        "no_target": ("You tremble.", "{name} trembles."),
        "targeted": ("You tremble before {target}.", "{name} trembles before you.", "{name} trembles before {target}."),
    },
    "mourn": {
        "no_target": ("You mourn quietly.", "{name} mourns quietly."),
        "targeted": ("You mourn alongside {target}.", "{name} mourns alongside you.", "{name} mourns alongside {target}."),
    },
    "console": {
        "no_target": ("You could use some consoling.", "{name} looks like they could use some consoling."),
        "targeted": ("You console {target}.", "{name} consoles you.", "{name} consoles {target}."),
    },
    "grieve": {
        "no_target": ("You grieve.", "{name} grieves."),
        "targeted": ("You grieve with {target}.", "{name} grieves with you.", "{name} grieves with {target}."),
    },

    # --- Hostile / Contemptuous ---
    "glare": {
        "no_target": ("You glare at nothing in particular.", "{name} glares at nothing in particular."),
        "targeted": ("You glare at {target}.", "{name} glares at you.", "{name} glares at {target}."),
    },
    "scowl": {
        "no_target": ("You scowl.", "{name} scowls."),
        "targeted": ("You scowl at {target}.", "{name} scowls at you.", "{name} scowls at {target}."),
    },
    "sneer": {
        "no_target": ("You sneer.", "{name} sneers."),
        "targeted": ("You sneer at {target}.", "{name} sneers at you.", "{name} sneers at {target}."),
    },
    "spit": {
        "no_target": ("You spit on the ground.", "{name} spits on the ground."),
        "targeted": ("You spit at {target}'s feet.", "{name} spits at your feet.", "{name} spits at {target}'s feet."),
    },
    "snarl": {
        "no_target": ("You snarl.", "{name} snarls."),
        "targeted": ("You snarl at {target}.", "{name} snarls at you.", "{name} snarls at {target}."),
    },
    "growl": {
        "no_target": ("You growl.", "{name} growls."),
        "targeted": ("You growl at {target}.", "{name} growls at you.", "{name} growls at {target}."),
    },
    "hiss": {
        "no_target": ("You hiss.", "{name} hisses."),
        "targeted": ("You hiss at {target}.", "{name} hisses at you.", "{name} hisses at {target}."),
    },
    "slap": {
        "no_target": ("You slap at the empty air.", "{name} slaps at the empty air."),
        "targeted": ("You slap {target}.", "{name} slaps you.", "{name} slaps {target}."),
    },
    "shove": {
        "no_target": ("You shove at nothing.", "{name} shoves at nothing."),
        "targeted": ("You shove {target}.", "{name} shoves you.", "{name} shoves {target}."),
    },
    "mock": {
        "no_target": ("You mock no one in particular.", "{name} mocks no one in particular."),
        "targeted": ("You mock {target} openly.", "{name} mocks you openly.", "{name} mocks {target} openly."),
    },
    "scoff": {
        "no_target": ("You scoff.", "{name} scoffs."),
        "targeted": ("You scoff at {target}.", "{name} scoffs at you.", "{name} scoffs at {target}."),
    },
    "snort": {
        "no_target": ("You snort.", "{name} snorts."),
        "targeted": ("You snort derisively at {target}.", "{name} snorts derisively at you.", "{name} snorts derisively at {target}."),
    },
    "eyeroll": {
        "no_target": ("You roll your eyes.", "{name} rolls their eyes."),
        "targeted": ("You roll your eyes at {target}.", "{name} rolls their eyes at you.", "{name} rolls their eyes at {target}."),
    },
    "point": {
        "no_target": ("You point at nothing.", "{name} points at nothing."),
        "targeted": ("You point at {target}.", "{name} points at you.", "{name} points at {target}."),
    },
    "threaten": {
        "no_target": ("You make a threatening gesture at no one.", "{name} makes a threatening gesture at no one."),
        "targeted": ("You make a threatening gesture at {target}.", "{name} makes a threatening gesture at you.", "{name} makes a threatening gesture at {target}."),
    },
    "curse": {
        "no_target": ("You curse under your breath.", "{name} curses under their breath."),
        "targeted": ("You curse at {target}.", "{name} curses at you.", "{name} curses at {target}."),
    },

    # --- Gestures / Physical Reactions ---
    "nod": {
        "no_target": ("You nod.", "{name} nods."),
        "targeted": ("You nod to {target}.", "{name} nods to you.", "{name} nods to {target}."),
    },
    "headshake": {
        "no_target": ("You shake your head.", "{name} shakes their head."),
        "targeted": ("You shake your head at {target}.", "{name} shakes their head at you.", "{name} shakes their head at {target}."),
    },
    "shrug": {
        "no_target": ("You shrug.", "{name} shrugs."),
        "targeted": ("You shrug at {target}.", "{name} shrugs at you.", "{name} shrugs at {target}."),
    },
    "salute": {
        "no_target": ("You come to attention and salute.", "{name} comes to attention and salutes."),
        "targeted": ("You salute {target}.", "{name} salutes you.", "{name} salutes {target}."),
    },
    "bow": {
        "no_target": ("You bow.", "{name} bows."),
        "targeted": ("You bow to {target}.", "{name} bows to you.", "{name} bows to {target}."),
    },
    "kneel": {
        "no_target": ("You kneel.", "{name} kneels."),
        "targeted": ("You kneel before {target}.", "{name} kneels before you.", "{name} kneels before {target}."),
    },
    "stretch": {
        "no_target": ("You stretch.", "{name} stretches."),
        "targeted": None,
    },
    "yawn": {
        "no_target": ("You yawn.", "{name} yawns."),
        "targeted": None,
    },
    "cough": {
        "no_target": ("You cough.", "{name} coughs."),
        "targeted": ("You cough pointedly at {target}.", "{name} coughs pointedly at you.", "{name} coughs pointedly at {target}."),
    },
    "sneeze": {
        "no_target": ("You sneeze.", "{name} sneezes."),
        "targeted": None,
    },
    "faint": {
        "no_target": ("You feign a faint.", "{name} feigns a faint."),
        "targeted": None,
    },
    "stumble": {
        "no_target": ("You stumble.", "{name} stumbles."),
        "targeted": ("You stumble into {target}.", "{name} stumbles into you.", "{name} stumbles into {target}."),
    },
    "clap": {
        "no_target": ("You clap.", "{name} claps."),
        "targeted": ("You clap for {target}.", "{name} claps for you.", "{name} claps for {target}."),
    },
    "cheer": {
        "no_target": ("You cheer.", "{name} cheers."),
        "targeted": ("You cheer for {target}.", "{name} cheers for you.", "{name} cheers for {target}."),
    },

    # --- Roman-flavored bonus socials ---
    "toga": {
        "no_target": ("You adjust the fall of your toga with practiced ease.", "{name} adjusts the fall of their toga with practiced ease."),
        "targeted": None,
    },
    "libation": {
        "no_target": ("You pour out a small libation.", "{name} pours out a small libation."),
        "targeted": ("You pour a libation in {target}'s honor.", "{name} pours a libation in your honor.", "{name} pours a libation in {target}'s honor."),
    },
    "thumbsdown": {
        "no_target": ("You turn your thumb down - pollice verso.", "{name} turns their thumb down."),
        "targeted": ("You turn your thumb down at {target}.", "{name} turns their thumb down at you.", "{name} turns their thumb down at {target}."),
    },
    "thumbsup": {
        "no_target": ("You turn your thumb up in approval.", "{name} turns their thumb up in approval."),
        "targeted": ("You turn your thumb up at {target}.", "{name} turns their thumb up at you.", "{name} turns their thumb up at {target}."),
    },
    "acclaim": {
        "no_target": ("You raise a fist and shout your acclaim.", "{name} raises a fist and shouts their acclaim."),
        "targeted": ("You raise a fist and acclaim {target}.", "{name} raises a fist and acclaims you.", "{name} raises a fist and acclaims {target}."),
    },
    "wardoff": {
        "no_target": ("You spit three times, warding off ill fortune.", "{name} spits three times, warding off ill fortune."),
        "targeted": None,
    },
    "evileye": {
        "no_target": ("You make the sign against the evil eye.", "{name} makes the sign against the evil eye."),
        "targeted": ("You make the sign against the evil eye at {target}.", "{name} makes the sign against the evil eye at you.", "{name} makes the sign against the evil eye at {target}."),
    },
    "auspex": {
        "no_target": ("You glance skyward, reading the flight of birds out of old habit.", "{name} glances skyward, reading the flight of birds out of old habit."),
        "targeted": None,
    },
}


class CmdSocial(Command):
    """
    A social command (emote) - see 'help socials' for the full list.

    Usage:
      <social>
      <social> <target>
    """

    help_category = "social"

    def _send_no_target(self, caller, entry):
        actor_msg, room_msg = entry["no_target"]
        caller.msg(actor_msg)
        if caller.location:
            caller.location.msg_contents(
                room_msg.format(name=caller.key), exclude=[caller]
            )

    def func(self):
        caller = self.caller
        entry = SOCIALS.get(self.key)
        if not entry:
            # Should never happen - every registered instance's key is
            # a real SOCIALS entry - but fail quietly rather than with
            # a raw KeyError if this ever drifts out of sync.
            return

        if not self.args:
            self._send_no_target(caller, entry)
            return

        typed = self.args.strip()

        # Deliberately simple, by direct request: targeting yourself
        # just falls back to the plain no-target message rather than
        # a hand-written reflexive line for all ~80 entries. Checked
        # BEFORE searching, not after - Evennia's own caller.search()
        # never matches a plain typed name against the searcher
        # itself (only the special "me"/"self" keywords do), so
        # relying on "target == caller" after a search would silently
        # never fire for someone typing their own actual name.
        if typed.lower() in ("me", "self", caller.key.lower()) or typed.lower() in (
            alias.lower() for alias in caller.aliases.all()
        ):
            self._send_no_target(caller, entry)
            return

        target = caller.search(typed, location=caller.location)
        if not target:
            return  # caller.search() already sent its own not-found message

        targeted = entry["targeted"]
        if not targeted:
            caller.msg("That's not something you can do to someone else.")
            return

        actor_msg, target_msg, room_msg = targeted
        caller.msg(actor_msg.format(target=target.key))
        target.msg(target_msg.format(name=caller.key))
        if caller.location:
            caller.location.msg_contents(
                room_msg.format(name=caller.key, target=target.key),
                exclude=[caller, target],
            )


def make_social_commands():
    """
    Builds one CmdSocial instance per SOCIALS entry, each with its own
    key - called once from the character cmdset (commands/
    default_cmdsets.py) rather than hand-listing all ~90 self.add()
    calls there.
    """
    return [type(
        "CmdSocial_%s" % name, (CmdSocial,), {"key": name}
    )() for name in SOCIALS]
