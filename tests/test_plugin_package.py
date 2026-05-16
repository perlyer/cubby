import json
from pathlib import Path

from cubby_tool.agents.claude_code import SKILL

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_marketplace_manifest_is_valid_json():
    data = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert data["name"]
    assert data["plugins"]


def test_static_skill_matches_adapter_output():
    static = (REPO_ROOT / "plugin" / "skills" / "cubby" / "SKILL.md").read_text()
    assert static == SKILL


def test_settings_snippet_is_removed():
    assert not (REPO_ROOT / "docs" / "settings-snippet.json").exists()
