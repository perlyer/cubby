"""cubby command functions, grouped into focused submodules.

`cli.py` and the tests use `commands.cmd_<name>`; this package re-exports every
command from its submodule so that surface is unchanged.
"""

from cubby_tool.commands.secrets import (
    cmd_cp, cmd_get, cmd_list, cmd_map, cmd_mv, cmd_rename, cmd_rm, cmd_rotate,
    cmd_set, cmd_ttl,
)
from cubby_tool.commands.run import cmd_run
from cubby_tool.commands.importing import cmd_import
from cubby_tool.commands.namespaces import cmd_ns
from cubby_tool.commands.agents import cmd_agent
from cubby_tool.commands.backup import cmd_export, cmd_restore
from cubby_tool.commands.setup import (
    cmd_audit, cmd_completion, cmd_doctor, cmd_init,
)

__all__ = [
    "cmd_agent", "cmd_audit", "cmd_completion", "cmd_cp", "cmd_doctor",
    "cmd_export", "cmd_get", "cmd_import", "cmd_init", "cmd_list", "cmd_map",
    "cmd_mv", "cmd_ns", "cmd_rename", "cmd_restore", "cmd_rm", "cmd_rotate",
    "cmd_run", "cmd_set", "cmd_ttl",
]
