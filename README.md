# python-skill-creator

给 Python-backed Codex skill 补工程规范。

很多 skill 只有 `SKILL.md` 和几个脚本，作者自己知道怎么跑，换一台机器就容易出问题。这个 skill 做的事很具体：创建或更新带 Python 代码的 skill 时，把依赖、锁文件、固定命令、最小验证和运行环境说明一起补上。

## 适用场景

- skill 里有 Python 脚本。
- skill 依赖 `pandas`、`openpyxl`、`duckdb`、`playwright` 等 Python 包。
- skill 会生成文件、处理数据、渲染文档、调用浏览器或外部工具。
- 你希望 skill 复制到另一个环境后，别人不用猜怎么安装、怎么验证。

如果一个 skill 只有 `SKILL.md` 和少量参考文档，不需要 Python 运行时，就不必用这套结构。

## 这个 skill 会要求什么

Python-backed skill 至少应该有：

- 符合 Agent Skills spec 的 `SKILL.md`：`name`、`description`、frontmatter、目录名都要对。
- `pyproject.toml`：声明 Python 版本和依赖。
- `uv.lock`：锁住依赖版本。
- `scripts/check.py`：提供一个便宜、可重复的自检命令。
- `tests/`：给容易悄悄坏掉的逻辑加最小测试。
- 清楚的运行说明：输入输出路径、环境变量、网络、权限、字体、浏览器、系统工具等。

## 目录结构

```text
.
|-- scripts/                         # OpenAI 标准-可选：可执行代码
|   |-- __init__.py
|   |-- check.py
|   |-- scaffold_python_skill.py
|   `-- validate_skill.py
|-- references/                      # OpenAI 标准-可选：补充文档
|   `-- python_project.md
|-- agents/                          # OpenAI 标准-可选：agent 侧展示信息和默认提示
|   `-- openai.yaml
|-- tests/                           # 本 skill 新增：Python 行为的最小测试
|   |-- __init__.py
|   `-- test_scaffold_python_skill.py
|-- SKILL.md                         # OpenAI 标准-必须：metadata 和 instructions
|-- pyproject.toml                   # 本 skill 新增：Python 版本和依赖声明
|-- uv.lock                          # 本 skill 新增：锁定 Python 依赖版本
|-- AGENTS.md
|-- LICENSE
`-- README.md
```

## 安装

这个仓库本身就是 skill 目录，skill 路径是仓库根目录：

```text
.
```

用 Codex 的 skill installer 安装时，指定这个 path 即可。

安装后重启 Codex，让新 skill 生效。

## 使用

在创建或更新 Python-backed skill 时调用：

```text
Use $python-skill-creator to create a portable Python-backed Codex skill.
```

也可以直接使用脚手架脚本给已有 skill 补基础文件：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/scaffold_python_skill.py /path/to/skill-name --python ">=3.11"
```

脚手架只生成起点。生成后还要根据实际 skill 调整依赖、检查命令、测试和运行说明。

## 校验

校验器分两层：

- Agent Skills spec：检查 `SKILL.md`、frontmatter、目录名、`description`、`compatibility`、`metadata`、`agents/openai.yaml` 等。
- Python 工程规范：检查 `pyproject.toml`、`uv.lock`、`scripts/check.py`、`__init__.py`、Python 依赖声明等。

检查当前 skill：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/validate_skill.py . --python
```

检查这个 skill 产出的新 skill：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/validate_skill.py /path/to/skill-name --python
```

## 验证

在仓库根目录运行：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/check.py
UV_CACHE_DIR=.uv-cache uv run pytest
UV_CACHE_DIR=.uv-cache uv run ruff check .
```
