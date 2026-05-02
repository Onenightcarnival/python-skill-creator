#!/usr/bin/env python3
"""Validate an Agent Skill and optional Python project conventions."""

from __future__ import annotations

import argparse
import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".uv-cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
}
FORBIDDEN_PROJECT_DIRS = {
    ".pytest_cache",
    ".ruff_cache",
    ".uv-cache",
    ".venv",
    "__pycache__",
}


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: "ValidationResult") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def parse_frontmatter(skill_md: Path) -> tuple[dict[str, Any] | None, str, str | None]:
    content = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)(.*)$", content, re.DOTALL)
    if not match:
        return None, content, "SKILL.md must start with YAML frontmatter"

    frontmatter_text = match.group(1)
    body = match.group(2)
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        return None, body, f"SKILL.md frontmatter is not valid YAML: {exc}"

    if not isinstance(frontmatter, dict):
        return None, body, "SKILL.md frontmatter must be a mapping"
    return frontmatter, body, None


def validate_agent_skill(root: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        return ValidationResult(["SKILL.md is missing"], warnings)

    frontmatter, body, error = parse_frontmatter(skill_md)
    if error:
        return ValidationResult([error], warnings)
    assert frontmatter is not None

    unexpected = set(frontmatter) - ALLOWED_FRONTMATTER_KEYS
    if unexpected:
        allowed = ", ".join(sorted(ALLOWED_FRONTMATTER_KEYS))
        found = ", ".join(sorted(unexpected))
        errors.append(f"SKILL.md frontmatter has unsupported key(s): {found}. Allowed: {allowed}")

    name = frontmatter.get("name")
    if not isinstance(name, str) or not name:
        errors.append("SKILL.md frontmatter must include a non-empty string name")
    elif not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?", name):
        errors.append(
            "SKILL.md name must be 1-64 characters, lowercase letters, numbers, and hyphens, "
            "and must not start or end with a hyphen"
        )
    elif "--" in name:
        errors.append("SKILL.md name must not contain consecutive hyphens")
    elif name != root.name:
        errors.append(f"SKILL.md name must match the skill directory name: {root.name}")

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("SKILL.md frontmatter must include a non-empty string description")
    elif len(description) > 1024:
        errors.append("SKILL.md description must be 1024 characters or fewer")

    license_value = frontmatter.get("license")
    if license_value is not None and not isinstance(license_value, str):
        errors.append("SKILL.md license must be a string when provided")

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str) or not compatibility.strip():
            errors.append("SKILL.md compatibility must be a non-empty string when provided")
        elif len(compatibility) > 500:
            errors.append("SKILL.md compatibility must be 500 characters or fewer")

    metadata = frontmatter.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            errors.append("SKILL.md metadata must be a mapping when provided")
        else:
            for key, value in metadata.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    errors.append("SKILL.md metadata must map string keys to string values")
                    break

    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is not None and not isinstance(allowed_tools, str):
        errors.append("SKILL.md allowed-tools must be a string when provided")

    if not body.strip():
        errors.append("SKILL.md must include Markdown instructions after the frontmatter")

    line_count = len(skill_md.read_text(encoding="utf-8").splitlines())
    if line_count > 500:
        warnings.append("SKILL.md is over 500 lines; move details into references/")

    openai_yaml = root / "agents" / "openai.yaml"
    if openai_yaml.exists():
        errors.extend(validate_openai_yaml(openai_yaml, str(name) if isinstance(name, str) else None))

    return ValidationResult(errors, warnings)


def validate_openai_yaml(path: Path, skill_name: str | None) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"agents/openai.yaml is not valid YAML: {exc}"]

    if not isinstance(data, dict):
        return ["agents/openai.yaml must be a mapping"]

    interface = data.get("interface")
    if interface is not None:
        if not isinstance(interface, dict):
            errors.append("agents/openai.yaml interface must be a mapping")
        else:
            for key in ("display_name", "short_description", "default_prompt"):
                value = interface.get(key)
                if value is not None and not isinstance(value, str):
                    errors.append(f"agents/openai.yaml interface.{key} must be a string")
            default_prompt = interface.get("default_prompt")
            if skill_name and isinstance(default_prompt, str) and f"${skill_name}" not in default_prompt:
                errors.append(f"agents/openai.yaml interface.default_prompt must mention ${skill_name}")

    policy = data.get("policy")
    if policy is not None and not isinstance(policy, dict):
        errors.append("agents/openai.yaml policy must be a mapping")
    return errors


def iter_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return files


def has_python_runtime(root: Path) -> bool:
    return bool(iter_python_files(root)) or (root / "pyproject.toml").exists()


def validate_python_project(root: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    skill_name = read_skill_name(root)
    py_files = iter_python_files(root)

    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        errors.append("Python-backed skills must include pyproject.toml")
    else:
        errors.extend(validate_pyproject(pyproject, skill_name))

    if not (root / "uv.lock").exists():
        errors.append("Python-backed skills must commit uv.lock")

    check_script = root / "scripts" / "check.py"
    if not check_script.exists():
        errors.append("Python-backed skills must include scripts/check.py")

    for directory in sorted({path.parent for path in py_files}):
        if directory == root:
            continue
        if not (directory / "__init__.py").exists():
            errors.append(f"Python directory must include __init__.py: {directory.relative_to(root)}")

    for forbidden in tracked_forbidden_paths(root):
        errors.append(f"Generated directory must not be committed: {forbidden}")

    return ValidationResult(errors, warnings)


def tracked_forbidden_paths(root: Path) -> list[str]:
    tracked: list[str] = []
    for forbidden in sorted(FORBIDDEN_PROJECT_DIRS):
        path = root / forbidden
        if not path.exists():
            continue
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), "ls-files", "--", forbidden],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            completed = None

        if completed is None or completed.returncode != 0:
            tracked.append(forbidden)
            continue

        if completed.stdout.strip():
            tracked.append(forbidden)
    return tracked


def read_skill_name(root: Path) -> str | None:
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        return None
    frontmatter, _, error = parse_frontmatter(skill_md)
    if error or not frontmatter:
        return None
    name = frontmatter.get("name")
    return name if isinstance(name, str) else None


def validate_pyproject(path: Path, skill_name: str | None) -> list[str]:
    errors: list[str] = []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        return [f"pyproject.toml is not valid TOML: {exc}"]

    project = data.get("project")
    if not isinstance(project, dict):
        return ["pyproject.toml must include [project]"]

    project_name = project.get("name")
    if not isinstance(project_name, str) or not project_name:
        errors.append("pyproject.toml [project].name must be a non-empty string")
    elif skill_name and project_name != skill_name:
        errors.append(f"pyproject.toml [project].name must match the skill name: {skill_name}")

    requires_python = project.get("requires-python")
    if not isinstance(requires_python, str) or not requires_python:
        errors.append("pyproject.toml [project].requires-python must be set")

    dependencies = project.get("dependencies")
    if dependencies is not None and not (
        isinstance(dependencies, list) and all(isinstance(item, str) for item in dependencies)
    ):
        errors.append("pyproject.toml [project].dependencies must be a list of strings")

    return errors


def validate(root: Path, *, python: bool | None = None) -> ValidationResult:
    root = root.resolve()
    result = validate_agent_skill(root)

    should_validate_python = has_python_runtime(root) if python is None else python
    if should_validate_python:
        result.extend(validate_python_project(root))

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--python", action="store_true", help="Require Python project checks")
    parser.add_argument("--no-python", action="store_true", help="Skip Python project checks")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    if args.python and args.no_python:
        raise SystemExit("--python and --no-python cannot be used together")

    python: bool | None
    if args.python:
        python = True
    elif args.no_python:
        python = False
    else:
        python = None

    result = validate(args.skill_dir, python=python)
    for warning in result.warnings:
        print(f"warning: {warning}")
    for error in result.errors:
        print(f"error: {error}")

    if result.errors or (args.strict and result.warnings):
        return 1

    print("skill validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
