"""Per-agent integration adapters."""

from cubby_tool.agents import claude_code, codex, copilot, cursor, gemini

ADAPTERS = {
    a.name: a
    for a in (
        claude_code.adapter,
        codex.adapter,
        gemini.adapter,
        cursor.adapter,
        copilot.adapter,
    )
}


def get(name):
    return ADAPTERS.get(name)


def names():
    return sorted(ADAPTERS)
