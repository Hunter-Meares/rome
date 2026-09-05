"""
Search and multimatch handling

This module allows for overloading two functions used by Evennia's
search functionality:

    at_search_result:
        This is called whenever a result is returned from an object
        search (a common operation in commands).  It should (together
        with at_multimatch_input below) define some way to present and
        differentiate between multiple matches (by default these are
        presented as 1-ball, 2-ball etc)
    at_multimatch_input:
        This is called with a search term and should be able to
        identify if the user wants to separate a multimatch-result
        (such as that from a previous search). By default, this
        function understands input on the form 1-ball, 2-ball etc as
        indicating that the 1st or 2nd match for "ball" should be
        used.

This module is not called by default, to use it, add the following
line to your settings file:

    SEARCH_AT_RESULT = "server.conf.at_search.at_search_result"

----------------------------------------------------------------------------
Why this project needed its own version (a real bug found live)
----------------------------------------------------------------------------
Every player Character in this game is rpsystem's own ContribRPCharacter,
which means every ordinary caller.search() call - 'consider ludus', 'look
trainer', etc. - is routed through rpsystem's sdesc-aware search override
(get_search_result in evennia/contrib/rpg/rpsystem/rpsystem.py), not
Evennia's plain object-manager search. That override only recognizes a
LEADING number - "1-trainer" - as a disambiguator; it never sees a
trailing "-1" or a space-separated "1" at all (both get treated as one
literal search string and simply fail to match anything).

Evennia's own *default* at_search_result (evennia/utils/utils.py) doesn't
know that - it prints multimatch results using SEARCH_MULTIMATCH_TEMPLATE,
whose default format is "{name}-{number}" (trailing), because that's what
the base engine's own manager-level search actually accepts. So a real
player, told "a Ludus recruit trainer-1", typing exactly that back, got a
flat "could not find" error - the displayed syntax and the only syntax
that actually works were simply different conventions, and nothing about
the message said so. This override fixes that by displaying the number
FIRST, matching what will actually work for every real player in this
game. It also drops the bracketed "[alias;alias]" noise the default
template adds per match (confirmed confusing/immersion-breaking directly
by a live player) - the numbered name plus a one-line hint on how to pick
one is enough to act on, and shorter besides.
"""

from django.utils.translation import gettext as _


def at_search_result(matches, caller, query="", quiet=False, **kwargs):
    """
    Same contract as Evennia's own version of this function (see the
    module docstring) - 0 matches reports a not-found error, 1 match
    passes straight through, 2+ reports a numbered disambiguation list
    and returns None either way. The only real change is presentation:
    leading-number format ("1-name") instead of trailing ("name-1"),
    since that's the format that will actually resolve for a player
    typing it back in - see the module docstring for why.
    """
    if not matches:
        if not quiet:
            error = kwargs.get("nofound_string") or _("Could not find '{query}'.").format(
                query=query
            )
            caller.msg(error)
        return None

    if len(matches) == 1:
        return matches[0]

    if quiet:
        return matches

    multimatch_string = kwargs.get("multimatch_string")
    if multimatch_string:
        lines = ["%s\n" % multimatch_string]
    else:
        lines = [_("More than one match for '{query}' (please narrow target):\n").format(query=query)]

    for num, result in enumerate(matches, 1):
        display_name = (
            result.get_display_name(caller) if hasattr(result, "get_display_name") else str(result)
        )
        extra_info = result.get_extra_info(caller) if hasattr(result, "get_extra_info") else ""
        lines.append("  %d-%s%s\n" % (num, display_name, extra_info))

    lines.append(_("Type the number first, e.g. '1-{query}'.").format(query=query))
    caller.msg("".join(lines))
    return None
