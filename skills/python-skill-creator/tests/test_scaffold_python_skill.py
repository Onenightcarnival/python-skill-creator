from pathlib import Path

from scripts.scaffold_python_skill import main


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
    assert (skill_dir / "scripts" / "check.py").exists()
    assert (skill_dir / "tests" / "test_skill_files.py").exists()
