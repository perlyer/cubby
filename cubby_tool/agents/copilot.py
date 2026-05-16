from pathlib import Path

from cubby_tool.agents.base import Adapter
from cubby_tool.agents.guidance import GUIDANCE

DOC = f"""\
---
applyTo: "**"
---

{GUIDANCE}"""


class CopilotAdapter(Adapter):
    name = "copilot"

    def _root(self) -> Path:
        return Path.home() / ".copilot"

    def _doc(self) -> Path:
        return self._root() / "instructions" / "cubby.instructions.md"

    def detect(self) -> bool:
        return self._root().is_dir()

    def install(self) -> None:
        doc = self._doc()
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text(DOC)

    def uninstall(self) -> None:
        self._doc().unlink(missing_ok=True)

    def _installed(self) -> bool:
        return self._doc().exists()


adapter = CopilotAdapter()
