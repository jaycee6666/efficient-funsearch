# 任务执行前检查清单（Environment / Test Baseline / Branch Status）

**Feature**: `001-efficient-funsearch`  
**Created**: 2026-03-26  
**Purpose**: 在执行 `specs/001-efficient-funsearch/tasks.md` 之前，先确认环境、测试基线、分支状态可支持稳定迭代。

---

## A. 环境检查（Environment）

- [ ] Python 版本满足 `pyproject.toml` 要求（`requires-python = ">=3.10"`）
  - 当前快照：`Python 3.9.12` ❌
  - 命令：`python --version`

- [ ] pytest 可用
  - 当前快照：`pytest 7.1.1` ✅
  - 命令：`pytest --version`

- [ ] ruff 可用
  - 当前快照：`ruff: command not found` ❌
  - 命令：`ruff --version`

- [ ] 安装开发依赖（建议）
  - 命令：`pip install -e .[dev]`

---

## B. 测试基线（Test Baseline）

- [ ] AGENTS 基线命令可运行
  - 规范命令来源：`AGENTS.md` → `cd src; pytest; ruff check .`

- [ ] 根目录 pytest 基线通过或明确记录失败原因
  - 当前快照：`pytest` 在收集阶段失败 ❌
  - 关键错误：`ModuleNotFoundError: No module named 'src'`（`tests/unit/test_normalizer.py`）
  - 命令：`pytest`

- [ ] src 目录 pytest 基线结果被记录
  - 当前快照：`cd src; pytest` → `collected 0 items`（无测试执行）⚠️
  - 命令：`cd src; pytest`

- [ ] lint 基线可运行
  - 当前快照：`ruff check .` 无法执行（ruff 未安装）❌
  - 命令：`ruff check .`

---

## C. 分支与工作区状态（Branch Status）

- [ ] 当前分支与目标 feature 一致（建议为 `001-efficient-funsearch`）
  - 当前快照：`001-update-proposal-spec` ❌
  - 命令：`git branch --show-current`

- [ ] 分支已配置 upstream（便于同步和后续 PR）
  - 当前快照：`no upstream configured` ❌
  - 命令：`git rev-parse --abbrev-ref --symbolic-full-name @{u}`

- [ ] 工作树是否干净（或明确允许带改动执行）
  - 当前快照：存在未提交改动与未跟踪文件 ⚠️
  - 命令：`git status -sb`

---

## D. 执行前阻塞项（必须先解决）

- [ ] 升级到 Python 3.10+（与项目声明一致）
- [ ] 安装 `ruff` 与 dev 依赖（建议 `pip install -e .[dev]`）
- [ ] 修复测试导入路径问题（`src` 包不可导入）
- [ ] 切换到目标 feature 分支 `001-efficient-funsearch`

---

## E. 通过标准（Go / No-Go）

满足以下全部条件后，再开始执行 `tasks.md`：

1. `python --version` 显示 `>=3.10`
2. `pytest` 可完成收集且无导入级错误
3. `ruff check .` 可运行
4. 当前分支为目标 feature 分支
5. 分支状态（upstream/工作树）已按团队约定处理

---

## F. 复查命令清单（可直接复制）

```bash
python --version
pytest --version
ruff --version
pytest
cd src; pytest
ruff check .
git branch --show-current
git rev-parse --abbrev-ref --symbolic-full-name @{u}
git status -sb
```
