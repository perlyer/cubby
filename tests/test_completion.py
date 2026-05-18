import pytest

from cubby_tool import cli, completion
from cubby_tool.help import command_names


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
def test_render_contains_command_names(shell):
    script = completion.render(shell, command_names())
    assert script
    for name in ("set", "get", "run", "export"):
        assert name in script


def test_render_rejects_unknown_shell():
    with pytest.raises(ValueError):
        completion.render("powershell", command_names())


def test_completion_command_prints_script(capsys):
    assert cli.main(["completion", "bash"]) == 0
    out = capsys.readouterr().out
    assert out.strip()
    assert "complete" in out


def test_completion_unknown_shell_errors():
    with pytest.raises(SystemExit):
        cli.main(["completion", "tcsh"])
