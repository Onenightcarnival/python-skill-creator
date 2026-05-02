# AGENTS.md

## 写作风格

1. 不要 AI 味儿、翻译腔。
2. 少做概念解释，直接说清楚判断和做法。
3. 中文表达要自然，别为了显得完整而绕远。
4. 避免自证式口吻，不用反复强调“我已经”“为了确保”。

## 仓库结构

- 这个仓库是单 skill repo，仓库根目录就是 skill root。
- `SKILL.md`、`pyproject.toml`、`uv.lock`、`scripts/`、`tests/` 都放在根目录。
- 不再使用 `skills/<skill-name>/` 这种 monorepo 结构。

## Python Skill 约定

- Python-backed skill 要按小工程处理，不只写 `SKILL.md`。
- `SKILL.md` 先符合 Agent Skills spec，再叠加 Python 工程规范。
- 需要 Python 运行时的 skill 应包含 `pyproject.toml`、`uv.lock`、固定验证命令和最小测试。
- 依赖用 `uv` 管理，`uv.lock` 要提交。
- 缓存、虚拟环境、IDE 文件不要提交。

## 验证命令

在 skill 目录内运行：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/validate_skill.py . --python
UV_CACHE_DIR=.uv-cache uv run python scripts/check.py
UV_CACHE_DIR=.uv-cache uv run pytest
UV_CACHE_DIR=.uv-cache uv run ruff check .
```
