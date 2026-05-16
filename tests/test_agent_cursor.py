from cubby_tool.agents.cursor import adapter


def _rule(tmp_path):
    return tmp_path / ".cursor" / "rules" / "cubby.mdc"


def test_detect_checks_cursor_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert adapter.detect() is False
    (tmp_path / ".cursor").mkdir()
    assert adapter.detect() is True


def test_install_writes_project_rule(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    adapter.install()
    text = _rule(tmp_path).read_text()
    assert "alwaysApply: true" in text
    assert "cubby run" in text


def test_install_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    adapter.install()
    adapter.install()
    assert _rule(tmp_path).exists()


def test_uninstall_removes_rule(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    adapter.install()
    adapter.uninstall()
    assert not _rule(tmp_path).exists()


def test_status(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert adapter.status() == "agent absent"
    (tmp_path / ".cursor").mkdir()
    assert adapter.status() == "not installed"
    adapter.install()
    assert adapter.status() == "installed"
