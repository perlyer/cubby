import sys

from cubby_tool import agents, style


def cmd_agent(args):
    if args.agent_cmd is None:
        print(style.fail("usage: cubby agent {list|add|rm|refresh}"), file=sys.stderr)
        return 2
    if args.agent_cmd == "list":
        names = agents.names()
        width = max(len(n) for n in names)
        marks = {
            "installed": style.green(style.OK_MARK),
            "not installed": style.dim(style.DOT_MARK),
            "agent absent": style.dim(style.CROSS_MARK),
        }
        counts = {"installed": 0, "not installed": 0, "agent absent": 0}
        lines = []
        for name in names:
            st = agents.ADAPTERS[name].status()
            counts[st] = counts.get(st, 0) + 1
            lines.append(f" {marks.get(st, ' ')}  {name.ljust(width)}  {style.dim(st)}")
        summary = (
            f"{counts['installed']} installed · "
            f"{counts['not installed']} available · "
            f"{counts['agent absent']} not found"
        )
        print(style.box(lines, title="agent integrations", footer=summary))
        return 0
    if args.agent_cmd == "refresh":
        refreshed = []
        for name in agents.names():
            adapter = agents.ADAPTERS[name]
            if adapter.status() == "installed":
                adapter.install()
                refreshed.append(name)
        print()
        for name in refreshed:
            print(style.ok(f"refreshed {name}"))
        if refreshed:
            print()
            print(style.dim(f"  refreshed {len(refreshed)} agent integration(s)"))
        else:
            print(style.dim("  no agent integrations installed"))
        return 0
    adapter = agents.get(args.name)
    if adapter is None:
        print(style.fail(f"unknown agent '{args.name}' — see `cubby agent list`"),
              file=sys.stderr)
        return 4
    if args.agent_cmd == "add":
        adapter.install()
        print(style.ok(f"integration installed for {adapter.name}"))
        return 0
    if args.agent_cmd == "rm":
        adapter.uninstall()
        print(style.ok(f"integration removed for {adapter.name}"))
        return 0
    print(style.fail("usage: cubby agent {list|add|rm|refresh}"), file=sys.stderr)
    return 2
