from cubby_tool import audit


def test_log_event_noop_when_disabled(home):
    audit.log_event(home, False, "run", "ns", "echo hi")
    assert audit.read_log(home) == []


def test_log_event_appends_a_formatted_line(home):
    audit.log_event(home, True, "run", "work", "psql -h db")
    lines = audit.read_log(home)
    assert len(lines) == 1
    fields = lines[0].split("  ")
    assert fields[1] == "run"
    assert fields[2] == "work"
    assert fields[3] == "psql -h db"


def test_log_event_never_records_a_value(home):
    audit.log_event(home, True, "reveal", "work", "db-password")
    assert "db-password" in audit.read_log(home)[0]
    # the detail is the secret NAME, never its value — nothing else is written


def test_log_event_truncates_long_detail(home):
    audit.log_event(home, True, "run", "ns", "x" * 500)
    assert len(audit.read_log(home)[0]) < 300


def test_log_file_is_mode_0600(home):
    audit.log_event(home, True, "run", "ns", "echo")
    assert oct(audit.log_path(home).stat().st_mode & 0o777) == "0o600"


def test_clear_log(home):
    audit.log_event(home, True, "run", "ns", "echo")
    assert audit.clear_log(home) is True
    assert audit.read_log(home) == []


def test_clear_log_absent_file(home):
    assert audit.clear_log(home) is False
