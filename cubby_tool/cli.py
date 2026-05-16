import argparse

from cubby_tool import commands


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

    p_init = sub.add_parser("init", help="first-run setup")
    p_init.add_argument("--key-mode", dest="key_mode", choices=["file", "keychain"],
                        default="file")
    p_init.add_argument("--namespace", default=None)
    p_init.add_argument("--cwd-prefix", dest="cwd_prefix", default=None)
    p_init.set_defaults(func=commands.cmd_init)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
