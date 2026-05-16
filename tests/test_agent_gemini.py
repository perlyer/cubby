from cubby_tool.agents.gemini import adapter


def _gemini_md(tmp_path):
    return tmp_path / ".gemini" / "GEMINI.md"


def test_detect(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert adapter.detect() is False
    (tmp_path / ".gemini").mkdir()
    assert adapter.detect() is True


def test_install_adds_section(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".gemini").mkdir()
    adapter.install()
    text = _gemini_md(tmp_path).read_text()
    assert "cubby run" in text
    assert "cubby:start" in text


def test_install_preserves_existing_gemini_md(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".gemini").mkdir()
    _gemini_md(tmp_path).write_text("# My context\n\nremember this\n")
    adapter.install()
    text = _gemini_md(tmp_path).read_text()
    assert "remember this" in text
    assert "cubby run" in text


def test_install_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".gemini").mkdir()
    adapter.install()
    adapter.install()
    assert _gemini_md(tmp_path).read_text().count("cubby:start") == 1


def test_uninstall_removes_section_only(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".gemini").mkdir()
    _gemini_md(tmp_path).write_text("# My context\n\nremember this\n")
    adapter.install()
    adapter.uninstall()
    text = _gemini_md(tmp_path).read_text()
    assert "remember this" in text
    assert "cubby run" not in text


def test_status(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert adapter.status() == "agent absent"
    (tmp_path / ".gemini").mkdir()
    assert adapter.status() == "not installed"
    adapter.install()
    assert adapter.status() == "installed"
