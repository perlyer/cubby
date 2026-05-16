from pathlib import Path

from cubby_tool.agents.base import Adapter, has_section, remove_section, upsert_section
from cubby_tool.agents.guidance import GUIDANCE

SECTION_BODY = f"## cubby — secret store\n\n{GUIDANCE}"


class GeminiAdapter(Adapter):
    name = "gemini"

    def _root(self) -> Path:
        return Path.home() / ".gemini"

    def _gemini_md(self) -> Path:
        return self._root() / "GEMINI.md"

    def detect(self) -> bool:
        return self._root().is_dir()

    def install(self) -> None:
        upsert_section(self._gemini_md(), SECTION_BODY)

    def uninstall(self) -> None:
        remove_section(self._gemini_md())

    def _installed(self) -> bool:
        return has_section(self._gemini_md())


adapter = GeminiAdapter()
