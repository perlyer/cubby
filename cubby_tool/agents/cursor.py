from pathlib import Path

from cubby_tool.agents.base import Adapter
from cubby_tool.agents.guidance import GUIDANCE

RULE = f"""\
---
description: cubby — use the cubby CLI for secrets, never read plaintext
alwaysApply: true
---

{GUIDANCE}"""


class CursorAdapter(Adapter):
    name = "cursor"

    def _rule(self) -> Path:
        return Path.cwd() / ".cursor" / "rules" / "cubby.mdc"

    def detect(self) -> bool:
        return (Path.home() / ".cursor").is_dir()

    def install(self) -> None:
        rule = self._rule()
        rule.parent.mkdir(parents=True, exist_ok=True)
        rule.write_text(RULE)

    def uninstall(self) -> None:
        self._rule().unlink(missing_ok=True)

    def _installed(self) -> bool:
        return self._rule().exists()


adapter = CursorAdapter()
