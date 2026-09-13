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
Why this project needed its own version (two real bugs found live)
----------------------------------------------------------------------------
Every player Character in this game is rpsystem's own ContribRPCharacter,
which means every ordinary caller.search() call - 'consider ludus', 'look
trainer', etc. - is routed through rpsystem's sdesc-aware search override
(get_search_result in evennia/contrib/rpg/rpsystem/rpsystem.py), not
Evennia's plain object-manager search. That override only recognizes a
LEADING number - "1-trainer" - as a disambiguator; it never sees a
trailing "-1" or a space-separated "1" at all (both get treated as one
literal search string and simply fail to match anything). This is a
completely separate step from at_search_result below - it's parsed out
of the search string before matching even happens, so it keeps working
unchanged regardless of anything at_search_result itself does with a
genuine remaining ambiguity.

Second, and more consequential: a real player spent roughly 10 minutes
of a 75-minute first session trying to `consider`/`fight` "the Ludus
recruit trainer" - not because of a typo, but because three separate
NPCs in that room are all literally named "a Ludus recruit trainer"
(deliberately identical, by design - see CLAUDE.md), so every guess
("recruit", "trainer", "ludus recruit trainer") landed on a genuine
multi-match. They eventually found the "1-trainer" disambiguation
format on their own and it worked correctly - but making a brand new
player hunt for that before their FIRST ambiguous search even
succeeds once is real, avoidable friction for something that, in
every case observed so far, doesn't actually matter which match gets
picked (the candidates are meant to be interchangeable). Multi-matches
now auto-resolve to the first candidate instead of blocking on a
disambiguation prompt - a player who genuinely needs to pick a
specific one (multiple real players' summoned pets sharing a name,
say) still can, via the exact same "1-name" leading-number format
documented above; it just isn't forced on everyone by default anymore.
"""

from django.utils.translation import gettext as _


def at_search_result(matches, caller, query="", quiet=False, **kwargs):
    """
    Same contract as Evennia's own version of this function (see the
    module docstring) - 0 matches reports a not-found error, 1 match
    passes straight through. The real departure from both Evennia's
    default and this project's own earlier version: 2+ matches no
    longer block on a disambiguation prompt - they resolve to the
    first candidate automatically (see the module docstring for why).
    quiet=True keeps returning the full match list unchanged, for any
    caller that explicitly wants multiple results rather than one
    resolved target.
    """
    if not matches:
        if not quiet:
            error = kwargs.get("nofound_string") or _("Could not find '{query}'.").format(
                query=query
            )
            caller.msg(error)
        return None

    if quiet:
        return matches

    return matches[0]
