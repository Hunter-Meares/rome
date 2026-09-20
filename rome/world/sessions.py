"""
Project-specific ServerSession - extends the auditing contrib's own
AuditedServerSession with one more relay.

Real, direct request: 'snoop' (world/combat.py's CmdSnoop) only ever
showed a snooped character's OUTPUT - what they were seen to receive,
via CombatCharacter.msg's own relay to db.snoopers - never their
actual typed INPUT, even though a god watching someone is at least as
interested in what they're typing as what they're seeing back.

data_in() is the one place every raw client input passes through
regardless of protocol (telnet, webclient, SSH) - the exact same hook
the auditing contrib itself already uses to log input. Reusing
AuditedServerSession.audit() (rather than re-parsing the raw kwargs by
hand) means snoop's input relay gets the SAME password/PII masking
(AUDIT_MASKS, server/conf/settings.py) the audit log itself already
applies for free - a real safety property, not an afterthought: a
character's own login/character-creation password should never appear
in plaintext on a snooper's screen just because they happened to
already be snooping that account's *previous* character when a new
one logs in on the same connection.
"""

from evennia.contrib.utils.auditing.server import AuditedServerSession


class RomeServerSession(AuditedServerSession):
    def data_in(self, **kwargs):
        char = self.get_puppet()
        if char:
            snoopers = char.db.snoopers
            if snoopers:
                log = self.audit(src="client", **kwargs)
                text = (log.get("text") or "").strip()
                if text:
                    prefix = "|x[snoop %s types]|n " % char.key
                    for snooper in list(snoopers):
                        if snooper and snooper.pk and snooper != char:
                            snooper.msg(prefix + text)
        super().data_in(**kwargs)
