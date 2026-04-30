---
name: python-skill-creator
description: Use when creating or updating Codex skills that include Python scripts, Python dependencies, generated assets, validation commands, or any Python-based runtime behavior. This skill extends skill-creator by adding Python project structure, uv-managed dependencies, lock files, reproducible commands, minimal tests, and portability checks.
metadata:
  short-description: Create portable Python-backed skills
---

# Python Skill Creator

Use this skill after `skill-creator` when the skill has Python code or Python dependencies.

The goal is simple: a Python-backed skill should behave like a small project, not a loose folder of prompts and scripts. The user should be able to copy the skill, install dependencies, run one fixed check command, and know whether the runtime pieces work.

## Workflow

1. First create or update the normal skill surface:
   - `SKILL.md` with clear trigger metadata and concise workflow instructions.
   - `agents/openai.yaml` when UI metadata is useful.
   - `references/`, `assets/`, and `scripts/` only when they support the skill directly.

2. If Python is involved, add the engineering layer:
   - `pyproject.toml`
   - `uv.lock`
   - a fixed validation command
   - minimal tests or executable checks
   - explicit runtime notes for paths, environment variables, network, fonts, browsers, and other system dependencies

3. Prefer `uv` for Python dependency management:
   - declare Python version in `project.requires-python`
   - declare runtime dependencies in `project.dependencies`
   - declare dev tools in dependency groups
   - commit `uv.lock`
   - run tools through `uv run ...`

4. Keep the skill lean:
   - do not add README, install guides, changelogs, or duplicate docs
   - put detailed Python project rules in `references/python_project.md`
   - keep `SKILL.md` focused on when to use the skill and what path to follow

## Standard Files

For a Python-backed skill, create or check this shape:

```text
skill-name/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- pyproject.toml
|-- uv.lock
|-- scripts/
|   |-- check.py
|   `-- ...
|-- tests/
|   `-- test_*.py
|-- references/
|   `-- ...
`-- assets/
    `-- ...
```

`scripts/check.py` should be cheap and deterministic. It should verify imports, fixture availability, basic script behavior, and any required external binary that the skill depends on.

## Commands

Use these commands unless the target repo already has equivalent commands:

```bash
uv lock
uv run python scripts/check.py
uv run pytest
uv run ruff check .
```

If a skill does not need `pytest` or `ruff`, do not add them by reflex. For one small script, `scripts/check.py` may be enough.

## Scaffolding Helper

This skill includes `scripts/scaffold_python_skill.py` for adding the standard Python layer to a target skill directory.

Use it when you want a deterministic starting point:

```bash
uv run python scripts/scaffold_python_skill.py /path/to/skill-name --python ">=3.11" --dev "pytest>=8" --dev "ruff>=0.6"
```

After scaffolding, inspect the generated files and tune dependencies, commands, and runtime notes to match the actual skill.

## Portability Check

Before finishing, confirm:

- dependencies are declared and locked
- fixed commands are listed in `SKILL.md` or a linked reference
- path inputs and outputs are explicit
- network and permission needs are explicit
- external resources are bundled or have download and verification steps
- at least one validation command has been run, or the reason is stated

For the detailed checklist and templates, read `references/python_project.md`.
