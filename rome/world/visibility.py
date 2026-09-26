"""
How the world talks about invisible, sleeping and flying characters.

Two things live here, both shared by every room typeclass (Room and the
wilderness's FixedWildernessRoom) through InvisibleAwareRoom:

  - Room listings tag a character's state, so passers-by can tell at a glance:
    "(asleep)" for someone held in a Sleep spell, "(flying)" for someone
    airborne, and "(invis)" for an invisible character - shown only to those
    who can see through it (everyone else can't see them at all).
  - Anything a room announces has an invisible character's name replaced with
    "Someone" for every onlooker who can't see them. Speech, poses and
    movement already resolve names per onlooker through get_display_name
    (world/combat.py); this catches the many plain-text broadcasts that name
    a character directly, so an invisible caster never gives themself away by
    doing something ordinary - casting, eating, drawing a weapon.
"""

import re

_SENTENCE_END = (".", "!", "?", ":", '"', "\n")
_COLOR_CODE = re.compile(r"\|[a-zA-Z0-9=\[\]!\*_/>]")


def _hidden_from(character, looker):
    from world.concentration import invisible_hides_from

    return invisible_hides_from(character, looker)


def state_tags(character, looker):
    """The parenthesised state markers shown after a name in a room list."""
    from world.concentration import asleep_blocks, is_flying, is_invisible

    tags = []
    if asleep_blocks(character):
        tags.append("|y(asleep)|n")
    if is_flying(character):
        tags.append("|c(flying)|n")
    if is_invisible(character):
        tags.append("|x(invis)|n")
    return (" " + " ".join(tags)) if tags else ""


def anonymize(text, keys):
    """Replaces each name in `keys` in `text` with 'Someone' / 'someone'."""
    for key in keys:
        if not key:
            continue
        # A colour code (|Y) may sit right against the name - it counts as a boundary.
        pattern = re.compile(
            r"(?:(?<![A-Za-z0-9])|(?<=\|[A-Za-z]))%s(?![A-Za-z0-9])" % re.escape(key)
        )

        def _sub(match, text=text):
            before = _COLOR_CODE.sub("", text[: match.start()]).rstrip(" ")
            if not before or before.endswith(_SENTENCE_END):
                return "Someone"
            return "someone"

        text = pattern.sub(_sub, text)
    return text


class InvisibleAwareRoom:
    """Mixin for room typeclasses: state tags in listings, Someone in messages."""

    def get_display_characters(self, looker, **kwargs):
        from evennia.utils.utils import iter_to_str

        characters = self.filter_visible(
            self.contents_get(content_type="character"), looker, **kwargs
        )
        names = iter_to_str(
            (
                char.get_display_name(looker, **kwargs) + state_tags(char, looker)
                for char in characters
            ),
            endsep=", and",
        )
        return "|wCharacters:|n %s" % names if names else ""

    def msg_contents(self, text=None, exclude=None, from_obj=None, mapping=None, **kwargs):
        from evennia.utils.utils import make_iter

        hidden = [
            obj for obj in self.contents if obj.attributes.has("concentrations") and _is_invisible(obj)
        ]
        if not hidden or not isinstance(text, str):
            return super().msg_contents(
                text, exclude=exclude, from_obj=from_obj, mapping=mapping, **kwargs
            )

        exclude = list(make_iter(exclude)) if exclude else []
        receivers = [obj for obj in self.contents if obj not in exclude]
        # Group receivers by which of the hidden characters they can't see, so
        # each group gets one correctly anonymised copy of the message.
        groups = {}
        for receiver in receivers:
            blind_to = frozenset(h for h in hidden if _hidden_from(h, receiver))
            groups.setdefault(blind_to, []).append(receiver)
        for blind_to, group in groups.items():
            group_text = anonymize(text, [h.key for h in blind_to]) if blind_to else text
            skip = exclude + [obj for obj in self.contents if obj not in group and obj not in exclude]
            super().msg_contents(
                group_text, exclude=skip, from_obj=from_obj, mapping=mapping, **kwargs
            )


def _is_invisible(obj):
    from world.concentration import is_invisible

    return is_invisible(obj)
