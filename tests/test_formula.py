from pathlib import Path

FORMULA = Path(__file__).resolve().parents[1] / "Formula" / "cubby.rb"


def test_formula_exists():
    assert FORMULA.exists()


def test_formula_structure():
    text = FORMULA.read_text()
    assert "class Cubby < Formula" in text
    assert 'homepage "https://github.com/perlyer/cubby"' in text
    assert 'depends_on "age"' in text
    assert 'license "MIT"' in text
    assert "test do" in text
    assert "--version" in text
