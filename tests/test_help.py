from cubby_tool import help as cubby_help, style


def test_command_names_lists_all_nine():
    assert set(cubby_help.command_names()) == {
        "set", "get", "list", "rm", "run", "import", "ns", "agent", "init",
    }


def test_render_help_lists_every_command_and_group(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: False)
    out = cubby_help.render_help()
    for name in cubby_help.command_names():
        assert name in out
    for group in ("secrets", "namespaces", "agents", "setup"):
        assert group in out
    assert "usage: cubby" in out
    assert "command details" in out


def test_render_help_shows_banner_on_a_tty(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: True)
    out = cubby_help.render_help()
    assert "encrypted secret store" in out
