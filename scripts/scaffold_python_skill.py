#!/usr/bin/env python3
"""Add a minimal uv-based Python project layer to a Codex skill."""

from __future__ import annotations

import argparse
from pathlib import Path


CHECK_TEMPLATE = '''#!/usr/bin/env python3
"""Cheap runtime check for this skill."""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    required = ["SKILL.md", "pyproject.toml"]
    missing = [name for name in required if not (root / name).exists()]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"missing required file(s): {joined}")

    print("python skill check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def normalize_name(path: Path) -> str:
    return path.name.lower().replace("_", "-").replace(" ", "-")


def render_pyproject(name: str, python: str, deps: list[str], dev_deps: list[str]) -> str:
    runtime = "\n".join(f'    "{dep}",' for dep in deps)
    dev = "\n".join(f'    "{dep}",' for dep in dev_deps)
    return f'''[project]
name = "{name}"
version = "0.1.0"
description = "Python runtime helpers for the {name} skill."
requires-python = "{python}"
dependencies = [
{runtime}
]

[dependency-groups]
dev = [
{dev}
]

[tool.ruff]
line-length = 100
target-version = "py311"
'''


def write_new(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--python", default=">=3.11")
    parser.add_argument("--dep", action="append", default=[])
    parser.add_argument("--dev", action="append", default=[])
    args = parser.parse_args()

    root = args.skill_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)

    if not (root / "SKILL.md").exists():
        raise SystemExit(f"{root} does not look like a skill directory: SKILL.md is missing")

    dev_deps = args.dev or ["pytest>=8.0", "ruff>=0.6"]
    name = normalize_name(root)

    created = []
    if write_new(root / "pyproject.toml", render_pyproject(name, args.python, args.dep, dev_deps)):
        created.append("pyproject.toml")
    if write_new(root / "scripts" / "__init__.py", ""):
        created.append("scripts/__init__.py")
    if write_new(root / "scripts" / "check.py", CHECK_TEMPLATE):
        created.append("scripts/check.py")
        (root / "scripts" / "check.py").chmod(0o755)
    if write_new(root / "tests" / "__init__.py", ""):
        created.append("tests/__init__.py")
    if write_new(root / "tests" / "test_skill_files.py", render_test_file()):
        created.append("tests/test_skill_files.py")

    if created:
        print("created:")
        for item in created:
            print(f"  - {item}")
        print("next: run `uv lock` and `uv run python scripts/check.py`")
    else:
        print("nothing created; existing files were left untouched")
    return 0


def render_test_file() -> str:
    return '''from pathlib import Path


def test_required_skill_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "SKILL.md").exists()
    assert (root / "pyproject.toml").exists()
'''


if __name__ == "__main__":
    raise SystemExit(main())
