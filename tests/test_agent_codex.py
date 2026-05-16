from cubby_tool.agents.codex import adapter


def _agents_md(tmp_path):
    return tmp_path / ".codex" / "AGENTS.md"


def test_detect(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert adapter.detect() is False
    (tmp_path / ".codex").mkdir()
    assert adapter.detect() is True


def test_install_adds_section(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex").mkdir()
    adapter.install()
    text = _agents_md(tmp_path).read_text()
    assert "cubby run" in text
    assert "cubby:start" in text


def test_install_preserves_existing_agents_md(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex").mkdir()
    _agents_md(tmp_path).write_text("# House rules\n\nbe nice\n")
    adapter.install()
    text = _agents_md(tmp_path).read_text()
    assert "be nice" in text
    assert "cubby run" in text


def test_install_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex").mkdir()
    adapter.install()
    adapter.install()
    assert _agents_md(tmp_path).read_text().count("cubby:start") == 1


def test_uninstall_removes_section_only(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex").mkdir()
    _agents_md(tmp_path).write_text("# House rules\n\nbe nice\n")
    adapter.install()
    adapter.uninstall()
    text = _agents_md(tmp_path).read_text()
    assert "be nice" in text
    assert "cubby run" not in text


def test_status(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert adapter.status() == "agent absent"
    (tmp_path / ".codex").mkdir()
    assert adapter.status() == "not installed"
    adapter.install()
    assert adapter.status() == "installed"
