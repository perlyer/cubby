from pathlib import Path

from cubby_tool.agents.base import Adapter, has_section, remove_section, upsert_section
from cubby_tool.agents.guidance import GUIDANCE

SECTION_BODY = f"## cubby — secret store\n\n{GUIDANCE}"


class CodexAdapter(Adapter):
    name = "codex"

    def _root(self) -> Path:
        return Path.home() / ".codex"

    def _agents_md(self) -> Path:
        return self._root() / "AGENTS.md"

    def detect(self) -> bool:
        return self._root().is_dir()

    def install(self) -> None:
        upsert_section(self._agents_md(), SECTION_BODY)

    def uninstall(self) -> None:
        remove_section(self._agents_md())

    def _installed(self) -> bool:
        return has_section(self._agents_md())


adapter = CodexAdapter()
