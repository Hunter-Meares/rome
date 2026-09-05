"""
Commands

Commands describe the input the account can do to the game.

"""

from evennia.commands.command import Command as BaseCommand
from evennia.commands.default.muxcommand import MuxCommand as BaseMuxCommand
from evennia.commands.cmdhandler import CMD_NOINPUT


class RomePromptMixin:
    """
    Mixin that sends an updated HP/MP/SP prompt after every command.
    Most MUD clients (Mudlet included) render Evennia's "prompt" as a
    persistent status line rather than scrolling text, so this keeps
    HP/MP/SP visible at all times without the player needing to type
    'status' manually.

    Mixed into both Command and MuxCommand below, so it applies
    whether a command inherits from the plain base or the Mux-style
    parser.
    """

    def at_pre_cmd(self):
        """Called right before the command runs, before its output prints."""
        ret = super().at_pre_cmd()

        caller = self.caller
        if caller and hasattr(caller, "attributes") and caller.attributes.has("max_hp"):
            # Blank line right after the prompt (and the command you just
            # typed) and before this command's output - moved here instead
            # of at_post_cmd so the gap lands after the prompt, not before it.
            caller.msg("\n")

        return ret

    def at_post_cmd(self):
        """Called after the command has finished executing."""
        super().at_post_cmd()

        caller = self.caller
        # Only send the prompt if caller is a Character with combat
        # stats set up - this skips Accounts in OOC mode, and any
        # object that hasn't run CombatCharacter.at_object_creation().
        if caller and hasattr(caller, "attributes") and caller.attributes.has("max_hp"):
            prompt = (
                f"|c<|n|gHP|n |w{caller.db.hp}|n/|w{caller.db.max_hp}|c>|n "
                f"|c<|n|CMP|n |w{caller.db.mp}|n/|w{caller.db.max_mp}|c>|n "
                f"|c<|n|YSP|n |w{caller.db.sp}|n/|w{caller.db.max_sp}|c>|n "
                f"|c:|n "
            )
            caller.msg(prompt=prompt)


class Command(RomePromptMixin, BaseCommand):
    """
    Base command (you may see this if a child command had no help text defined)

    Note that the class's `__doc__` string is used by Evennia to create the
    automatic help entry for the command, so make sure to document consistently
    here. Without setting one, the parent's docstring will show (like now).

    """

    # Each Command class implements the following methods, called in this order
    # (only func() is actually required):
    #
    #     - at_pre_cmd(): If this returns anything truthy, execution is aborted.
    #     - parse(): Should perform any extra parsing needed on self.args
    #         and store the result on self.
    #     - func(): Performs the actual work.
    #     - at_post_cmd(): Extra actions, often things done after
    #         every command, like prompts. (Handled by RomePromptMixin above.)
    #
    pass


# -------------------------------------------------------------
#
# The default commands inherit from
#
#   evennia.commands.default.muxcommand.MuxCommand.
#
# COMMAND_DEFAULT_CLASS is set to "commands.command.MuxCommand" in
# settings.py, so Evennia's default commands (look, get, movement,
# etc.) all use this class - meaning the prompt refreshes after
# every command, not just combat ones.
#
# -------------------------------------------------------------


class MuxCommand(RomePromptMixin, BaseMuxCommand):
    """
    This sets up the basis for a MUX command. The idea
    is that most other Mux-related commands should just
    inherit from this and don't have to implement much
    parsing of their own unless they do something particularly
    advanced.

    Note that the class's __doc__ string (this text) is
    used by Evennia to create the automatic help entry for
    the command, so make sure to document consistently here.
    """

    # parse() is intentionally NOT overridden here - the default
    # MuxCommand.parse() (inherited from default_cmds.MuxCommand) is
    # used as-is. Only at_post_cmd (via RomePromptMixin) is customized.
    pass


class CmdNoInput(MuxCommand):
    """
    Called by Evennia's own engine whenever a player hits return with
    no other input at all (CMD_NOINPUT) - normally a true no-op ("Do
    nothing", per evennia.commands.default.syscommands.SystemNoInput,
    the reference implementation this project was silently falling
    back to). A real question raised live: shouldn't a bare return at
    least refresh the HP/MP/SP prompt? It should - most players reach
    for an empty return exactly when they want a status refresh
    without spamming a real command into the room, and since this
    subclasses MuxCommand, RomePromptMixin's at_post_cmd fires here
    too and sends a fresh prompt for free. func() itself still does
    nothing - the refresh is the whole point.
    """

    key = CMD_NOINPUT
    locks = "cmd:all()"

    def func(self):
        pass