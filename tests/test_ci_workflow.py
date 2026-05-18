from pathlib import Path

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_exists():
    assert CI.exists()


def test_ci_runs_pytest_on_supported_pythons():
    text = CI.read_text()
    assert "pytest" in text
    for version in ("3.11", "3.12", "3.13"):
        assert version in text
