from cubby_tool.agents.copilot import adapter


def _doc(tmp_path):
    return tmp_path / ".copilot" / "instructions" / "cubby.instructions.md"


def test_detect(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert adapter.detect() is False
    (tmp_path / ".copilot").mkdir()
    assert adapter.detect() is True


def test_install_writes_instructions_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".copilot").mkdir()
    adapter.install()
    text = _doc(tmp_path).read_text()
    assert "applyTo:" in text
    assert "cubby run" in text


def test_install_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".copilot").mkdir()
    adapter.install()
    adapter.install()
    assert _doc(tmp_path).exists()


def test_uninstall_removes_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".copilot").mkdir()
    adapter.install()
    adapter.uninstall()
    assert not _doc(tmp_path).exists()


def test_status(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert adapter.status() == "agent absent"
    (tmp_path / ".copilot").mkdir()
    assert adapter.status() == "not installed"
    adapter.install()
    assert adapter.status() == "installed"
