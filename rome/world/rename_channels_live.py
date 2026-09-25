"""
One-time live repair: capitalize the first letter of every channel name.

A direct request: channels should all read like "Public" - but the divine
channel and the fourteen religion channels ("divine", "mars-religion", ...)
were created lowercase. world/religion.py now creates them capitalized, but
that only affects channels created AFTER the change (CLAUDE.md gotcha #20),
so the existing ones are renamed here. Only the first letter changes
("mars-religion" -> "Mars-religion"); subscriptions, locks and aliases are
untouched, and channel lookups are case-insensitive, so nothing that finds a
channel by name is affected. Safe to re-run.

Run once via `evennia shell < world/rename_channels_live.py`, then
`evennia reload` (the running server may have the channels cached).
"""

from evennia.comms.models import ChannelDB

renamed = 0
for channel in ChannelDB.objects.all():
    key = channel.key
    if key and key[0].islower():
        new_key = key[0].upper() + key[1:]
        channel.key = new_key
        print("%-22s -> %s" % (key, new_key))
        renamed += 1
print("Renamed %d channel(s); %d total." % (renamed, ChannelDB.objects.count()))
