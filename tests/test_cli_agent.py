from cubby_tool import agents, cli


def test_registry_has_five_adapters():
    assert set(agents.names()) == {"claude-code", "codex", "gemini", "cursor", "copilot"}


def test_agent_list(capsys):
    assert cli.main(["agent", "list"]) == 0
    out = capsys.readouterr().out
    for name in ("claude-code", "codex", "gemini", "cursor", "copilot"):
        assert name in out


def test_agent_add_unknown_returns_4(capsys):
    assert cli.main(["agent", "add", "no-such-agent"]) == 4


def test_agent_rm_unknown_returns_4(capsys):
    assert cli.main(["agent", "rm", "no-such-agent"]) == 4


def test_agent_add_and_rm_codex(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex").mkdir()
    assert cli.main(["agent", "add", "codex"]) == 0
    assert (tmp_path / ".codex" / "AGENTS.md").exists()
    assert cli.main(["agent", "rm", "codex"]) == 0
    assert not (tmp_path / ".codex" / "AGENTS.md").exists()


def test_agent_refresh_with_no_integrations(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert cli.main(["agent", "refresh"]) == 0
    assert "no agent integrations" in capsys.readouterr().out


def test_agent_refresh_regenerates_installed(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".codex").mkdir()
    assert cli.main(["agent", "add", "codex"]) == 0
    agents_md = tmp_path / ".codex" / "AGENTS.md"
    canonical = agents_md.read_text()
    # tamper inside the cubby section (markers stay, so it still reads as installed)
    agents_md.write_text(canonical.replace("<!-- cubby:end -->", "TAMPERED\n<!-- cubby:end -->"))
    capsys.readouterr()
    assert cli.main(["agent", "refresh"]) == 0
    out = capsys.readouterr().out
    assert "codex" in out
    assert agents_md.read_text() == canonical


def test_agent_list_is_framed_under_a_title(capsys):
    assert cli.main(["agent", "list"]) == 0
    assert "agent integrations" in capsys.readouterr().out
