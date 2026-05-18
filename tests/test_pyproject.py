import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _pyproject():
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())


def test_pyproject_parses():
    data = _pyproject()
    assert data["project"]["name"]
    assert data["project"]["requires-python"]


def test_pyproject_has_no_runtime_dependencies():
    data = _pyproject()
    assert data["project"].get("dependencies", []) == []


def test_pyproject_entry_point():
    data = _pyproject()
    assert data["project"]["scripts"]["cubby"] == "cubby_tool.cli:main"


def test_pyproject_version_is_dynamic_from_init():
    data = _pyproject()
    assert "version" in data["project"]["dynamic"]
    assert data["tool"]["hatch"]["version"]["path"] == "cubby_tool/__init__.py"
