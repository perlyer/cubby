import pytest

from cubby_tool import cli


def test_bare_cubby_prints_help_and_exits_0(capsys):
    assert cli.main([]) == 0
    assert "usage: cubby" in capsys.readouterr().out


def test_help_token_prints_help(capsys):
    assert cli.main(["help"]) == 0
    out = capsys.readouterr().out
    assert "usage: cubby" in out
    assert "set" in out and "agent" in out


def test_h_and_help_flags_print_help(capsys):
    assert cli.main(["-h"]) == 0
    capsys.readouterr()
    assert cli.main(["--help"]) == 0
    assert "usage: cubby" in capsys.readouterr().out


def test_unknown_command_exits_2(capsys):
    assert cli.main(["uninstall"]) == 2
    err = capsys.readouterr().err
    assert "unknown command 'uninstall'" in err
    assert "cubby help" in err


def test_unknown_command_suggests_a_close_match(capsys):
    assert cli.main(["improt"]) == 2
    assert "did you mean 'import'" in capsys.readouterr().err


def test_unknown_command_no_suggestion_for_gibberish(capsys):
    assert cli.main(["xyzzy"]) == 2
    assert "did you mean" not in capsys.readouterr().err


def test_leading_flag_token_falls_through_to_argparse():
    # an unknown leading flag is argparse's job, not the unknown-command branch;
    # argparse rejects it by raising SystemExit (not returning 2)
    with pytest.raises(SystemExit):
        cli.main(["--bogus"])
