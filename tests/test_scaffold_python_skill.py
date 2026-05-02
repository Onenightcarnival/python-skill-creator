from pathlib import Path

from scripts.scaffold_python_skill import main
from scripts.validate_skill import validate


def test_scaffold_adds_python_project_files(tmp_path: Path, monkeypatch) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Demo.\n---\n# Demo\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["scaffold_python_skill.py", str(skill_dir), "--dep", "click>=8", "--dev", "pytest>=8"],
    )

    assert main() == 0
    pyproject = (skill_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "demo-skill"' in pyproject
    assert '"click>=8",' in pyproject
    assert (skill_dir / "scripts" / "__init__.py").exists()
    assert (skill_dir / "scripts" / "check.py").exists()
    assert (skill_dir / "tests" / "__init__.py").exists()
    assert (skill_dir / "tests" / "test_skill_files.py").exists()


def test_validate_rejects_name_that_does_not_match_directory(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: other-skill\ndescription: Demo skill for tests.\n---\n# Demo\n",
        encoding="utf-8",
    )

    result = validate(skill_dir, python=False)

    assert not result.ok
    assert any("must match the skill directory name" in error for error in result.errors)


def test_validate_accepts_python_backed_skill(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Demo skill for tests.\n---\n# Demo\n",
        encoding="utf-8",
    )
    (skill_dir / "pyproject.toml").write_text(
        '[project]\nname = "demo-skill"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n',
        encoding="utf-8",
    )
    (skill_dir / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "__init__.py").write_text("", encoding="utf-8")
    (scripts_dir / "check.py").write_text("def main() -> int:\n    return 0\n", encoding="utf-8")

    result = validate(skill_dir, python=True)

    assert result.ok
