from cubby_tool.agents import base
from cubby_tool.agents.guidance import GUIDANCE


def test_guidance_mentions_core_commands():
    assert "cubby run" in GUIDANCE
    assert "--reveal" in GUIDANCE


def test_upsert_section_creates_file_with_markers(tmp_path):
    f = tmp_path / "AGENTS.md"
    base.upsert_section(f, "hello")
    text = f.read_text()
    assert base.SECTION_START in text
    assert base.SECTION_END in text
    assert "hello" in text


def test_upsert_section_is_idempotent(tmp_path):
    f = tmp_path / "AGENTS.md"
    base.upsert_section(f, "hello")
    base.upsert_section(f, "hello")
    assert f.read_text().count(base.SECTION_START) == 1


def test_upsert_section_preserves_existing_content(tmp_path):
    f = tmp_path / "AGENTS.md"
    f.write_text("# My notes\n\nkeep me\n")
    base.upsert_section(f, "hello")
    text = f.read_text()
    assert "keep me" in text
    assert "hello" in text


def test_remove_section_cuts_only_the_section(tmp_path):
    f = tmp_path / "AGENTS.md"
    f.write_text("# My notes\n\nkeep me\n")
    base.upsert_section(f, "hello")
    assert base.remove_section(f) is True
    text = f.read_text()
    assert "keep me" in text
    assert "hello" not in text
    assert base.SECTION_START not in text


def test_remove_section_deletes_file_when_only_content(tmp_path):
    f = tmp_path / "AGENTS.md"
    base.upsert_section(f, "hello")
    assert base.remove_section(f) is True
    assert not f.exists()


def test_remove_section_absent_returns_false(tmp_path):
    f = tmp_path / "AGENTS.md"
    assert base.remove_section(f) is False


def test_remove_section_with_inverted_markers_leaves_file_untouched(tmp_path):
    f = tmp_path / "AGENTS.md"
    original = f"{base.SECTION_END}\nstuff\n{base.SECTION_START}\n"
    f.write_text(original)
    assert base.remove_section(f) is False
    assert f.read_text() == original


def test_upsert_section_with_inverted_markers_appends_valid_section(tmp_path):
    f = tmp_path / "AGENTS.md"
    f.write_text(f"{base.SECTION_END}\nstuff\n{base.SECTION_START}\n")
    base.upsert_section(f, "hello")
    text = f.read_text()
    assert "hello" in text
    assert text.index(base.SECTION_START) < text.rindex(base.SECTION_END)


def test_has_section(tmp_path):
    f = tmp_path / "AGENTS.md"
    assert base.has_section(f) is False
    base.upsert_section(f, "hello")
    assert base.has_section(f) is True
