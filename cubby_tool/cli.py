import argparse
import difflib
import json
import subprocess
import sys

from cubby_tool import commands, style
from cubby_tool.help import command_names, render_help


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cubby")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ns = sub.add_parser("ns", help="manage namespaces")
    p_ns.set_defaults(func=commands.cmd_ns, ns_cmd=None)
    ns_sub = p_ns.add_subparsers(dest="ns_cmd")
    ns_sub.add_parser("list", help="list namespaces")
    p_ns_add = ns_sub.add_parser("add", help="add a namespace")
    p_ns_add.add_argument("name")
    p_ns_add.add_argument("--cwd-prefix", dest="cwd_prefix", default=None)
    p_ns_rm = ns_sub.add_parser("rm", help="remove a namespace")
    p_ns_rm.add_argument("name")
    p_ns_use = ns_sub.add_parser("use", help="set the default namespace")
    p_ns_use.add_argument("name")

    p_init = sub.add_parser("init", help="first-run setup")
    p_init.add_argument("--key-mode", dest="key_mode", choices=["file", "keychain"],
                        default="file")
    p_init.add_argument("--namespace", default=None)
    p_init.add_argument("--cwd-prefix", dest="cwd_prefix", default=None)
    p_init.set_defaults(func=commands.cmd_init)

    p_set = sub.add_parser("set", help="store a secret (hidden input)")
    p_set.add_argument("name")
    p_set.add_argument("-n", "--namespace", default=None)
    p_set.add_argument("--stdin", action="store_true", help="read value from stdin")
    p_set.set_defaults(func=commands.cmd_set)

    p_get = sub.add_parser("get", help="show secret metadata")
    p_get.add_argument("name")
    p_get.add_argument("-n", "--namespace", default=None)
    p_get.add_argument("--reveal", action="store_true", help="print plaintext (humans only)")
    p_get.set_defaults(func=commands.cmd_get)

    p_list = sub.add_parser("list", help="list secret names")
    p_list.add_argument("-n", "--namespace", default=None)
    p_list.set_defaults(func=commands.cmd_list)

    p_rm = sub.add_parser("rm", help="delete a secret")
    p_rm.add_argument("name")
    p_rm.add_argument("-n", "--namespace", default=None)
    p_rm.set_defaults(func=commands.cmd_rm)

    p_run = sub.add_parser("run", help="run a command with namespace secrets in its env")
    p_run.add_argument("-n", "--namespace", default=None)
    p_run.add_argument("command", nargs=argparse.REMAINDER)
    p_run.set_defaults(func=commands.cmd_run)

    p_import = sub.add_parser("import", help="import secrets from .env or AWS Secrets Manager")
    p_import.add_argument("-n", "--namespace", default=None)
    p_import.add_argument("--from-env", dest="from_env", default=None, metavar="PATH")
    p_import.add_argument("--from-aws", dest="from_aws", default=None, metavar="SECRET_ID")
    p_import.add_argument("--region", default=None)
    p_import.set_defaults(func=commands.cmd_import)

    p_agent = sub.add_parser("agent", help="manage agent integrations")
    p_agent.set_defaults(func=commands.cmd_agent, agent_cmd=None)
    agent_sub = p_agent.add_subparsers(dest="agent_cmd")
    agent_sub.add_parser("list", help="list agent adapters and their status")
    p_agent_add = agent_sub.add_parser("add", help="install integration for an agent")
    p_agent_add.add_argument("name")
    p_agent_rm = agent_sub.add_parser("rm", help="remove integration for an agent")
    p_agent_rm.add_argument("name")
    agent_sub.add_parser("refresh", help="re-install every currently-installed agent integration")

    return parser


HELP_TOKENS = {"-h", "--help", "help"}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)

    if not argv or argv[0] in HELP_TOKENS:
        print(render_help())
        return 0

    cmd = argv[0]
    if not cmd.startswith("-") and cmd not in command_names():
        print(style.fail(f"unknown command '{cmd}'"), file=sys.stderr)
        match = difflib.get_close_matches(cmd, command_names(), n=1)
        if match:
            print(f"  did you mean '{match[0]}'?", file=sys.stderr)
        print("  run 'cubby help' to see available commands", file=sys.stderr)
        return 2

    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except LookupError as e:
        print(style.fail(str(e)), file=sys.stderr)
        return 4
    except FileNotFoundError as e:
        print(style.fail(f"not found: {e.filename or e}"), file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print(style.fail(f"external command failed: {e.cmd[0]} (exit {e.returncode})"),
              file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(style.fail(f"invalid JSON ({e})"), file=sys.stderr)
        return 2
    except ValueError as e:
        print(style.fail(str(e)), file=sys.stderr)
        return 2
