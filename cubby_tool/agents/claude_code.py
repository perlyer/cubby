import json
from pathlib import Path

from cubby_tool.agents.base import Adapter
from cubby_tool.agents.guidance import GUIDANCE

ALLOW = [
    "Bash(cubby run:*)",
    "Bash(cubby get:*)",
    "Bash(cubby list:*)",
    "Bash(cubby ns:*)",
]
DENY = [
    "Bash(cubby get* --reveal*)",
    "Bash(cubby get* --copy*)",
]

SKILL = f"""\
---
name: cubby
description: Use when a task needs a password, API token, or connection string — resolve secrets through the `cubby` CLI instead of reading plaintext.
---

# cubby — using secrets safely

{GUIDANCE}"""

COMMAND = """\
---
description: Show cubby status — active namespace and available secret names
---

Run `cubby ns` to show the active namespace, then `cubby list` for the secret names.
Do not reveal any values.
"""


class ClaudeCodeAdapter(Adapter):
    name = "claude-code"

    def _root(self) -> Path:
        return Path.home() / ".claude"

    def _skill(self) -> Path:
        return self._root() / "skills" / "cubby" / "SKILL.md"

    def _command(self) -> Path:
        return self._root() / "commands" / "cubby.md"

    def _settings(self) -> Path:
        return self._root() / "settings.json"

    def detect(self) -> bool:
        return self._root().is_dir()

    def install(self) -> None:
        skill = self._skill()
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(SKILL)
        command = self._command()
        command.parent.mkdir(parents=True, exist_ok=True)
        command.write_text(COMMAND)
        self._merge_settings(add=True)

    def uninstall(self) -> None:
        self._skill().unlink(missing_ok=True)
        self._command().unlink(missing_ok=True)
        self._merge_settings(add=False)

    def _installed(self) -> bool:
        return self._skill().exists()

    def _merge_settings(self, *, add: bool) -> None:
        path = self._settings()
        if not add and not path.exists():
            return
        if path.exists():
            try:
                data = json.loads(path.read_text())
            except json.JSONDecodeError:
                raise ValueError(
                    f"{path} is not valid JSON — fix or delete it, then retry"
                ) from None
        else:
            data = {}
        perms = data.setdefault("permissions", {})
        if not isinstance(perms, dict):
            raise ValueError(f"{path}: 'permissions' must be a JSON object")
        allow = perms.setdefault("allow", [])
        deny = perms.setdefault("deny", [])
        if not isinstance(allow, list) or not isinstance(deny, list):
            raise ValueError(
                f"{path}: 'permissions.allow' and 'permissions.deny' must be JSON arrays"
            )
        for entry in ALLOW:
            if add and entry not in allow:
                allow.append(entry)
            elif not add and entry in allow:
                allow.remove(entry)
        for entry in DENY:
            if add and entry not in deny:
                deny.append(entry)
            elif not add and entry in deny:
                deny.remove(entry)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n")


adapter = ClaudeCodeAdapter()
