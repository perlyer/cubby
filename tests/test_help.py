import argparse

from cubby_tool import help as cubby_help, style


def test_command_names_lists_every_command():
    assert set(cubby_help.command_names()) == {
        "set", "get", "list", "rm", "run", "import", "map", "rename", "rotate",
        "ttl", "ns", "agent", "init", "doctor", "audit", "export", "restore",
    }


def test_render_help_lists_every_command_and_group(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: False)
    out = cubby_help.render_help()
    for name in cubby_help.command_names():
        assert name in out
    for group in ("secrets", "namespaces", "agents", "backup", "setup"):
        assert group in out
    assert "usage: cubby" in out
    assert "command details" in out


def test_render_help_shows_banner_on_a_tty(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: True)
    out = cubby_help.render_help()
    assert "encrypted secret store" in out


def test_render_command_help_lists_arguments_and_options(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: False)
    p = argparse.ArgumentParser(prog="cubby demo")
    p.add_argument("name")
    p.add_argument("--flag", action="store_true", help="a flag")
    out = cubby_help.render_command_help(p, ["cubby", "demo"], "demo desc")
    assert "cubby demo" in out
    assert "demo desc" in out
    assert "name" in out
    assert "--flag" in out and "a flag" in out
    assert "arguments" in out and "options" in out
    assert "usage" in out


def test_render_command_help_lists_subcommands(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: False)
    p = argparse.ArgumentParser(prog="cubby demo")
    psub = p.add_subparsers()
    psub.add_parser("alpha", help="the alpha thing")
    out = cubby_help.render_command_help(p, ["cubby", "demo"], None)
    assert "subcommands" in out
    assert "alpha" in out and "the alpha thing" in out


def test_render_command_help_shows_banner_on_a_tty(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: True)
    p = argparse.ArgumentParser(prog="cubby demo")
    p.add_argument("name")
    out = cubby_help.render_command_help(p, ["cubby", "demo"], None)
    assert "encrypted secret store" in out
