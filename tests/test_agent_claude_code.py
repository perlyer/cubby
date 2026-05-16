import json

import pytest

from cubby_tool.agents.claude_code import adapter


def _claude(tmp_path):
    return tmp_path / ".claude"


def test_detect(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert adapter.detect() is False
    _claude(tmp_path).mkdir()
    assert adapter.detect() is True


def test_install_writes_skill_command_and_permissions(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _claude(tmp_path).mkdir()
    adapter.install()
    skill = _claude(tmp_path) / "skills" / "cubby" / "SKILL.md"
    command = _claude(tmp_path) / "commands" / "cubby.md"
    settings = json.loads((_claude(tmp_path) / "settings.json").read_text())
    assert "name: cubby" in skill.read_text()
    assert command.exists()
    assert "Bash(cubby run:*)" in settings["permissions"]["allow"]
    assert "Bash(cubby get:* --reveal*)" in settings["permissions"]["deny"]


def test_install_preserves_existing_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _claude(tmp_path).mkdir()
    (_claude(tmp_path) / "settings.json").write_text(
        json.dumps({"model": "opus", "permissions": {"allow": ["Bash(ls:*)"]}})
    )
    adapter.install()
    settings = json.loads((_claude(tmp_path) / "settings.json").read_text())
    assert settings["model"] == "opus"
    assert "Bash(ls:*)" in settings["permissions"]["allow"]
    assert "Bash(cubby run:*)" in settings["permissions"]["allow"]


def test_install_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _claude(tmp_path).mkdir()
    adapter.install()
    adapter.install()
    settings = json.loads((_claude(tmp_path) / "settings.json").read_text())
    assert settings["permissions"]["allow"].count("Bash(cubby run:*)") == 1


def test_uninstall_removes_files_and_permissions(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _claude(tmp_path).mkdir()
    (_claude(tmp_path) / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}})
    )
    adapter.install()
    adapter.uninstall()
    assert not (_claude(tmp_path) / "skills" / "cubby" / "SKILL.md").exists()
    assert not (_claude(tmp_path) / "commands" / "cubby.md").exists()
    settings = json.loads((_claude(tmp_path) / "settings.json").read_text())
    assert "Bash(cubby run:*)" not in settings["permissions"]["allow"]
    assert "Bash(ls:*)" in settings["permissions"]["allow"]


def test_uninstall_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _claude(tmp_path).mkdir()
    adapter.install()
    adapter.uninstall()
    adapter.uninstall()
    settings = json.loads((_claude(tmp_path) / "settings.json").read_text())
    assert "Bash(cubby run:*)" not in settings["permissions"]["allow"]


def test_install_raises_on_corrupt_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _claude(tmp_path).mkdir()
    (_claude(tmp_path) / "settings.json").write_text("{not json}")
    with pytest.raises(ValueError, match="not valid JSON"):
        adapter.install()


def test_install_raises_on_non_dict_permissions(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _claude(tmp_path).mkdir()
    (_claude(tmp_path) / "settings.json").write_text(
        json.dumps({"permissions": ["deny-all"]})
    )
    with pytest.raises(ValueError, match="permissions"):
        adapter.install()


def test_status(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert adapter.status() == "agent absent"
    _claude(tmp_path).mkdir()
    assert adapter.status() == "not installed"
    adapter.install()
    assert adapter.status() == "installed"
