#!/usr/bin/env python3
"""Runtime check for the python-skill-creator skill."""

from __future__ import annotations

import py_compile
from pathlib import Path

from validate_skill import validate


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    required = [
        "SKILL.md",
        "pyproject.toml",
        "references/python_project.md",
        "scripts/scaffold_python_skill.py",
        "scripts/validate_skill.py",
        "agents/openai.yaml",
    ]
    missing = [name for name in required if not (root / name).exists()]
    if missing:
        raise SystemExit(f"missing required file(s): {', '.join(missing)}")

    py_compile.compile(str(root / "scripts" / "scaffold_python_skill.py"), doraise=True)
    py_compile.compile(str(root / "scripts" / "validate_skill.py"), doraise=True)

    result = validate(root, python=True)
    for warning in result.warnings:
        print(f"warning: {warning}")
    if result.errors:
        for error in result.errors:
            print(f"error: {error}")
        return 1

    print("python-skill-creator check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
