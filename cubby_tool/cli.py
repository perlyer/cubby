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

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
