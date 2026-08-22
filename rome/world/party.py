"""
Party system

A lightweight leader-based party/group system. The leader owns the
canonical member list (db.party_members); everyone else just points
at the leader (db.party_leader). This keeps membership in exactly one
place instead of trying to keep several independent lists in sync.

This module is the foundation for every "group" ability mentioned in
the Skills & Spells design (Mass Cure Wounds, Testudo, Sacred Chant,
War Cry, etc.) - none of those can know who your allies are without
this existing first. Spells/abilities should call get_party_members()
below to resolve "who do I affect" rather than reinventing this logic.

Commands:
  party invite <name>   - invite someone to your party (forms one if
                           you don't have one yet; leader-only once a
                           party exists)
  party accept          - accept a pending invite
  party decline         - decline a pending invite
  party leave           - leave your current party
  party kick <name>     - leader-only, remove a member
  party                 - show your current party roster
"""

from commands.command import Command


def _find_character(caller, name, candidates):
    """
    Robust name search among a given candidate list.

    Plain caller.search() alone isn't enough here: this game's
    Character typeclass mixes in Evennia's rpsystem contrib
    (ContribRPObject), which overrides get_search_result to match
    primarily by sdesc/recog data. For a non-Builder caller (i.e.
    virtually everyone), that override never falls back to a plain
    real-name match - even an exact, unambiguous key - unless the
    searcher has already recog'd/greeted that person. Without this
    fallback, 'party invite <name>' or 'party kick <name>' can fail
    to find someone standing right there, typed exactly correctly,
    which is confusing and was never actually confirmed working.

    This mirrors the identical, already-applied fix in
    world/combat.py's find_combat_target - same root cause, same
    fallback shape (a case-insensitive startswith match against key
    or aliases), just scoped to whatever candidate list makes sense
    for the caller (room contents for invite, party roster for kick).
    """
    result = caller.search(name, candidates=candidates, quiet=True)
    if result:
        return result[0] if isinstance(result, list) else result

    name_lower = name.lower()
    for obj in candidates:
        if obj.key.lower().startswith(name_lower):
            return obj
        if any(alias.lower().startswith(name_lower) for alias in obj.aliases.all()):
            return obj

    caller.msg("Could not find '%s'." % name)
    return None


def get_party_members(character):
    """
    Returns the full list of a character's party members, including
    themselves. If they're not in a party, returns just [character] -
    this means calling code (group spells etc.) never needs a special
    case for "solo" characters, a party of one is just the normal case.
    """
    leader = character.db.party_leader or character
    members = leader.db.party_members
    if not members:
        return [character]
    # Defensive filter: drop any stale/deleted references
    return [m for m in members if m and m.pk]


def is_party_leader(character):
    """True if this character is the leader of their own party (or solo)."""
    leader = character.db.party_leader or character
    return leader == character


class CmdParty(Command):
    """
    Manage your party.

    Usage:
      party
      party invite <name>
      party accept
      party decline
      party leave
      party kick <name>

    Party members are who your group abilities (heals, buffs, shield
    walls, and the like) will actually affect. Being in a party is
    entirely optional - solo characters are always still eligible for
    solo-only spells, they just don't have anyone to share a group
    effect with.

    Your party matters in combat too: when a fight breaks out with
    'fight all', your whole party is automatically grouped together
    as one side against everyone else, rather than every person
    being treated as their own separate combatant. If you jump into
    a fight that a party member is already in, you'll automatically
    land on their side. Summoned allies (familiars, beasts, and the
    like) always fight on their summoner's side, regardless of party.

    See 'help groupcombat' for the full picture of how sides work.
    """

    key = "party"
    aliases = ["group"]
    help_category = "social"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            self.show_roster()
            return

        parts = args.split(None, 1)
        subcmd = parts[0].lower()
        target_name = parts[1].strip() if len(parts) > 1 else ""

        if subcmd == "invite":
            self.do_invite(target_name)
        elif subcmd == "accept":
            self.do_accept()
        elif subcmd == "decline":
            self.do_decline()
        elif subcmd == "leave":
            self.do_leave()
        elif subcmd == "kick":
            self.do_kick(target_name)
        else:
            caller.msg(
                "Usage: party, party invite <name>, party accept, party decline, "
                "party leave, party kick <name>"
            )

    def show_roster(self):
        caller = self.caller
        members = get_party_members(caller)
        if len(members) <= 1:
            caller.msg("You're not currently in a party. Use 'party invite <name>' to form one.")
            return
        leader = caller.db.party_leader or caller
        lines = ["|wYour party:|n"]
        for m in members:
            tag = " |y(leader)|n" if m == leader else ""
            lines.append("  %s%s" % (m.key, tag))
        caller.msg("\n".join(lines))

    def do_invite(self, target_name):
        caller = self.caller
        if not target_name:
            caller.msg("Invite whom? Usage: party invite <name>")
            return

        candidates = caller.location.contents if caller.location else []
        target = _find_character(caller, target_name, candidates)
        if not target:
            return

        if target == caller:
            caller.msg("You can't invite yourself.")
            return

        if not is_party_leader(caller):
            caller.msg("Only your party's leader can invite new members.")
            return

        if target in get_party_members(caller):
            caller.msg("%s is already in your party." % target.key)
            return

        if get_party_members(target) != [target]:
            caller.msg("%s is already in another party." % target.key)
            return

        # Forming a fresh party if caller doesn't have one yet
        if not caller.db.party_members:
            caller.db.party_leader = caller
            caller.db.party_members = [caller]

        target.db.party_invite = caller
        target.msg(
            "%s has invited you to their party. Type 'party accept' or 'party decline'."
            % caller.key
        )
        caller.msg("You invite %s to your party." % target.key)

    def do_accept(self):
        caller = self.caller
        inviter = caller.db.party_invite
        if not inviter or not inviter.pk:
            caller.msg("You don't have a pending party invite.")
            return

        leader = inviter.db.party_leader or inviter
        members = leader.db.party_members or [leader]

        if caller in members:
            caller.msg("You're already in that party.")
            caller.db.party_invite = None
            return

        members.append(caller)
        leader.db.party_members = members
        caller.db.party_leader = leader
        caller.db.party_invite = None

        leader.location.msg_contents(
            "%s has joined %s's party." % (caller.key, leader.key)
        )

    def do_decline(self):
        caller = self.caller
        inviter = caller.db.party_invite
        if not inviter:
            caller.msg("You don't have a pending party invite.")
            return
        caller.db.party_invite = None
        caller.msg("You decline the invitation.")
        if inviter.pk:
            inviter.msg("%s declines your party invitation." % caller.key)

    def do_leave(self):
        caller = self.caller
        leader = caller.db.party_leader or caller
        members = get_party_members(caller)

        if len(members) <= 1:
            caller.msg("You're not in a party.")
            return

        members = [m for m in members if m != caller]
        caller.db.party_leader = None
        caller.db.party_members = None
        caller.msg("You leave the party.")

        if caller == leader:
            # Leader left - promote the next member, or disband if that
            # was the last one.
            if members:
                new_leader = members[0]
                new_leader.db.party_leader = new_leader
                new_leader.db.party_members = members
                for m in members:
                    m.db.party_leader = new_leader
                new_leader.location.msg_contents(
                    "%s is now the party leader." % new_leader.key
                )
            # else: party disbanded, nothing further to clean up
        else:
            leader.db.party_members = members
            leader.location.msg_contents("%s has left the party." % caller.key)

    def do_kick(self, target_name):
        caller = self.caller
        if not target_name:
            caller.msg("Kick whom? Usage: party kick <name>")
            return

        if not is_party_leader(caller):
            caller.msg("Only your party's leader can kick members.")
            return

        target = _find_character(caller, target_name, get_party_members(caller))
        if not target:
            return
        if target == caller:
            caller.msg("You can't kick yourself - use 'party leave' instead.")
            return

        members = [m for m in get_party_members(caller) if m != target]
        caller.db.party_members = members
        target.db.party_leader = None
        target.db.party_members = None

        target.msg("You have been removed from %s's party." % caller.key)
        caller.msg("You remove %s from the party." % target.key)