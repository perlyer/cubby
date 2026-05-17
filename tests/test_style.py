import cubby_tool.style as style


def test_color_disabled_when_no_color_set(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert style.color_enabled() is False


def test_plain_when_color_disabled(monkeypatch):
    # under pytest, stdout is not a TTY -> color disabled
    assert style.green("hi") == "hi"
    assert style.dim("hi") == "hi"


def test_paint_wraps_when_color_forced_on(monkeypatch):
    monkeypatch.setattr(style, "color_enabled", lambda: True)
    assert style.green("hi") == "\033[32mhi\033[0m"
    assert style.red("hi") == "\033[31mhi\033[0m"


def test_ok_and_fail_carry_marks():
    assert style.OK_MARK in style.ok("done")
    assert "done" in style.ok("done")
    assert style.CROSS_MARK in style.fail("oops")
    assert "oops" in style.fail("oops")


def test_cyan_round_trips_when_color_disabled():
    # under pytest capsys stdout is not a TTY, so colour is off
    assert style.cyan("hi") == "hi"


def test_visible_width_ignores_ansi():
    assert style.visible_width("\033[32mhello\033[0m") == 5
    assert style.visible_width("plain") == 5
    assert style.visible_width("") == 0


def test_box_unframed_when_not_tty(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: False)
    out = style.box(["row one", "row two"], title="things", footer="2 total")
    assert "┌" not in out and "│" not in out
    assert out.splitlines() == ["things", "row one", "row two", "2 total"]


def test_box_framed_when_tty(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: True)
    out = style.box(["row one", "row two"], title="things", footer="2 total")
    lines = out.splitlines()
    assert lines[0].startswith("┌") and lines[0].endswith("┐")
    assert lines[-1].startswith("└") and lines[-1].endswith("┘")
    assert "things" in lines[0]
    assert "2 total" in lines[-1]
    # every rendered line has the same display width
    assert len({style.visible_width(l) for l in lines}) == 1


def test_box_sizes_to_a_title_wider_than_content(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: True)
    out = style.box(["x"], title="a fairly long title")
    assert len({style.visible_width(l) for l in out.splitlines()}) == 1


def test_box_framed_with_no_title_or_footer(monkeypatch):
    monkeypatch.setattr(style, "box_enabled", lambda: True)
    out = style.box(["row one", "row two"])
    lines = out.splitlines()
    assert lines[0].startswith("┌") and lines[0].endswith("┐")
    assert lines[-1].startswith("└") and lines[-1].endswith("┘")
    assert len({style.visible_width(l) for l in lines}) == 1
