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
