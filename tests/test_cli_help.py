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


def test_find_help_target_for_a_command():
    parser = cli.build_parser()
    target = cli._find_help_target(parser, ["set", "-h"])
    assert target is not None
    _, path, _ = target
    assert path == ["cubby", "set"]


def test_find_help_target_for_a_sub_subcommand():
    parser = cli.build_parser()
    target = cli._find_help_target(parser, ["ns", "add", "-h"])
    assert target is not None
    _, path, _ = target
    assert path == ["cubby", "ns", "add"]


def test_find_help_target_none_for_run_remainder():
    parser = cli.build_parser()
    assert cli._find_help_target(parser, ["run", "--", "echo", "-h"]) is None


def test_find_help_target_none_when_help_follows_an_argument():
    parser = cli.build_parser()
    assert cli._find_help_target(parser, ["set", "db", "-h"]) is None


def test_find_help_target_none_without_a_help_token():
    parser = cli.build_parser()
    assert cli._find_help_target(parser, ["set"]) is None


def test_set_help_is_styled(capsys):
    assert cli.main(["set", "-h"]) == 0
    out = capsys.readouterr().out
    assert "cubby set" in out
    assert "name" in out
    assert "--stdin" in out


def test_ns_help_lists_its_subcommands(capsys):
    assert cli.main(["ns", "-h"]) == 0
    out = capsys.readouterr().out
    assert "cubby ns" in out
    for sub in ("list", "add", "rm", "use"):
        assert sub in out


def test_ns_add_help_is_styled(capsys):
    assert cli.main(["ns", "add", "-h"]) == 0
    out = capsys.readouterr().out
    assert "cubby ns add" in out
    assert "cwd-prefix" in out


def test_agent_rm_help_is_styled(capsys):
    assert cli.main(["agent", "rm", "-h"]) == 0
    assert "cubby agent rm" in capsys.readouterr().out


def test_set_help_shows_argument_descriptions(capsys):
    assert cli.main(["set", "-h"]) == 0
    out = capsys.readouterr().out
    assert "secret name" in out          # the `name` positional
    assert "namespace to use" in out     # the -n/--namespace option


def test_ns_add_help_shows_argument_descriptions(capsys):
    assert cli.main(["ns", "add", "-h"]) == 0
    out = capsys.readouterr().out
    assert "namespace name" in out
    assert "auto-selects this namespace" in out


def test_run_help_shows_command_description(capsys):
    assert cli.main(["run", "-h"]) == 0
    assert "the command to run" in capsys.readouterr().out


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert "cubby" in capsys.readouterr().out
