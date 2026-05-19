from pathlib import Path

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_exists():
    assert CI.exists()


def test_ci_runs_pytest_on_supported_pythons():
    text = CI.read_text()
    assert "pytest" in text
    for version in ("3.11", "3.12", "3.13"):
        assert version in text


PUBLISH = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "publish.yml"


def test_publish_workflow_exists():
    assert PUBLISH.exists()


def test_publish_workflow_uses_trusted_publishing_on_release():
    text = PUBLISH.read_text()
    assert "release:" in text
    assert "id-token: write" in text
    assert "gh-action-pypi-publish" in text
