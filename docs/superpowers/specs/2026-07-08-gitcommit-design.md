# GitCommit — AI 生成 Commit Message 工具 · 设计文档

> 日期：2026-07-08
> 状态：设计完成

## 1. 概述

GitCommit 是一个 **TUI 交互式 CLI 工具**，读取 `git diff --staged` 的变更内容，调用可配置的 AI provider 生成 Conventional Commits 格式的 commit message，经用户确认后自动执行 `git commit`。

### 核心体验

```
$ gitcommit

  📋 Staged Changes
  ────────────────────────────────────
  src/git.py       │ +45 -12
  tests/test_git.py│ +120
  2 files, 165+/12-

  🤖 AI 生成的 Commit Message
  ────────────────────────────────────
  feat(git): add staged diff and commit utils

  [Enter] 确认  [e] 编辑  [r] 重新生成  [q] 取消

  ✅ 提交成功！
  feat(git): add staged diff and commit utils
```

---

## 2. 技术选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 语言 | Python 3.10+ | 上手快，生态丰富 |
| TUI | Rich + questionary | 最轻量，一个依赖搞定渲染+交互 |
| AI 接口 | openai SDK（OpenAI 兼容协议） | 几乎所有 provider 都兼容，单类覆盖全部 |
| 配置 | TOML 三层级联 | 灵活，符合 Python 工具惯例 |
| 分发 | `pipx install` + `pyproject.toml` | 全局命令可用，零运行时依赖 |
| Git 操作 | subprocess 调用 `git` 命令 | 零第三方 Git 库，轻量 |

---

## 3. 项目结构

```
gitcommit/
├── pyproject.toml              # 项目元数据 + 依赖 + entry point
├── src/gitcommit/
│   ├── __init__.py
│   ├── cli.py                  # CLI 入口，argparse 参数解析
│   ├── git.py                  # Git 操作（diff, commit, status）
│   ├── ai.py                   # AI provider 抽象与实现
│   ├── config.py               # 配置加载（三层级联）
│   ├── tui.py                  # Rich + questionary 交互界面
│   └── prompt.py               # Prompt 模板与格式处理
└── tests/
    ├── test_config.py
    ├── test_git.py
    ├── test_prompt.py
    ├── test_ai.py
    └── test_tui.py
```

---

## 4. 模块设计

### 4.1 `cli.py` — CLI 入口

**职责**：参数解析，串联模块调用，唯一入口。

```python
# 支持的参数
gitcommit [options]

--provider, -p    指定 AI provider（覆盖配置文件）
--model, -m       指定模型
--format, -f      自定义 message 格式模板
--dry-run, -n     只生成和展示 message，不执行 git commit
--config          显示当前生效的配置
```

**流程**：

```
parse_args()
  → 检查 staged changes (git.has_staged_changes)
  → 加载最终配置 (config.load)
  → 获取 diff (git.get_staged_diff)
  → 构建 prompt (prompt.build)
  → 调用 AI (ai.generate)
  → TUI 展示+确认+编辑循环 (tui.review_loop)
  → 执行提交 (git.commit)
```

### 4.2 `config.py` — 配置层

**三层级联**（后覆盖前）：

1. **默认值** — 内置硬编码
2. **全局配置** — `~/.gitcommit.toml`
3. **项目配置** — `./.gitcommit.toml`
4. **CLI 参数** — 运行时传入

**配置结构**：

```toml
[provider]
name = "deepseek"           # provider 标识
api_key = "sk-xxx"          # API key
model = "deepseek-chat"     # 模型名
endpoint = "https://api.deepseek.com/v1"  # 可选，OpenAI 兼容 endpoint

[format]
template = "{{type}}({{scope}}): {{message}}"  # 自定义格式模板，默认 Conventional Commits
max_length = 72
language = "zh"
```

**实现要点**：
- 用 `tomllib`（Python 3.11+ stdlib）或 `tomli`（Python 3.10）读取 TOML
- 全局 `~/.gitcommit.toml` 不存在时不报错，用默认值
- 项目 `.gitcommit.toml` 不存在时不报错，回退到全局配置
- CLI 参数只覆盖传入的字段，未传的保留配置文件值
- `.gitcommit.toml` 建议加入 `.gitignore`（包含 API key）

### 4.3 `git.py` — Git 操作

纯函数模块，通过 `subprocess` 调用 `git` 命令。

| 函数 | 实现 | 错误处理 |
|------|------|----------|
| `has_staged_changes()` | `git diff --staged --quiet`，exit code 1 = 有变更 | 不在 git 仓库时报错退出 |
| `get_staged_diff()` | `git diff --staged`，返回完整 diff 文本 | subprocess 异常捕获，转为友好提示 |
| `get_staged_stats()` | `git diff --staged --stat`，返回文件列表+行数 | 同上 |
| `commit(message)` | `git commit -m "..."` | 显示 git 原始错误（如 hook 失败）|

**约束**：
- 不引入任何 Python Git 库（如 GitPython）
- 所有 subprocess 调用使用 `capture_output=True`，不污染终端
- diff 过长时（>8000 字符），截断并提示用户

### 4.4 `ai.py` — AI Provider

**单一类覆盖所有 provider**：因为主流 AI API（OpenAI、DeepSeek、通义千问、Ollama 等）都兼容 OpenAI 的 `/v1/chat/completions` 协议，一个 `OpenAICompatProvider` 类即可。

```python
from openai import OpenAI

class OpenAICompatProvider:
    def __init__(self, config):
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.endpoint or "https://api.openai.com/v1"
        )
        self.model = config.model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # 低温度，提高稳定性和可重复性
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
```

**错误处理**：
- API key 未配置 → 提示设置配置文件
- 网络错误 → 显示具体错误 + 建议检查 endpoint/网络
- 超时 → 默认 15s，提示后可重试
- HTTP 错误（4xx/5xx）→ 显示状态码+body，不吞掉

### 4.5 `tui.py` — 交互界面

三个步骤，每个步骤一个函数：

**Step 1 — `show_diff_summary(stats, diff_size)`**

用 Rich 的 `Panel`、`Table` 展示 staged 文件和变更统计。这一步纯展示，不需要用户输入。

**Step 2 — `review_message(message)`**

核心交互循环：
- 用 Rich Panel 展示 AI 生成的 message
- 用 questionary 提供四个选项：确认 / 编辑 / 重新生成 / 取消

```python
def review_message(message: str) -> tuple[Action, str]:
    """
    Returns (action, final_message)
    action: "commit" | "regenerate" | "cancel"
    """
```

- 编辑模式用 questionary 的 `text()` 输入框，预填 AI 生成的内容
- 重新生成时调用者（cli.py）再次调 AI，然后重新进入 Step 2
- 取消时优雅退出，不做任何操作

**Step 3 — `show_success(message)`**

Rich 绿色 Panel 显示提交成功的 message。

### 4.6 `prompt.py` — Prompt 构建

```python
SYSTEM_PROMPT = """你是一个专业的 commit message 生成助手。
根据用户提供的 git diff，生成一行简洁准确的 commit message。

规则：
- 使用 Conventional Commits 格式：type(scope): description
- type 从以下选择：feat, fix, refactor, docs, style, test, chore, perf, ci
- scope 根据改动的文件/模块自动推断
- 描述部分用{language}写
- 描述不超过 {max_length} 字符，简洁有力
- 如果 diff 很大，聚焦最核心的变更
- 只返回 commit message 本身，一行，不要任何解释"""

USER_PROMPT_TEMPLATE = """以下文件发生了变更：
{file_summary}

git diff:
{diff}

请生成 commit message:"""
```

**格式模板**：用户可通过 `format.template` 自定义输出格式，变量包括 `{type}`、`{scope}`、`{message}`、`{emoji}`。AI 如果返回不符合模板的格式，不做强制校验（避免过度复杂），让用户自己编辑。

---

## 5. 错误处理一览

| 场景 | 处理方式 |
|------|----------|
| 不在 git 仓库 | 友好提示"当前目录不是 git 仓库"，exit code 1 |
| 无 staged changes | 提示"没有暂存的变更，请先使用 git add"，exit code 1 |
| 配置文件语法错误 | 显示具体行号和错误，exit code 1 |
| API key 未配置 | 提示设置路径 + TOML 示例片段，exit code 1 |
| API 网络/超时错误 | 显示错误详情，询问"是否重试？"（y/n） |
| API 返回格式异常 | 显示原始返回 + 提示"AI 返回异常，重试时可能更换 provider" |
| diff 超过 8000 字符 | 截断并告知"diff 过长已截断（前 8000 字符）" |
| git commit 失败 | 显示 git 原始错误（如 pre-commit hook 拒绝），不吞掉 |

---

## 6. 测试策略

| 测试文件 | 测试内容 | 工具 |
|----------|----------|------|
| `test_config.py` | 三层级联覆盖逻辑：默认值 → 全局 → 项目 → CLI | 标准单元测试 |
| `test_git.py` | mock `subprocess.run`，验证 git 命令参数正确性 + 错误分支 | `unittest.mock` |
| `test_prompt.py` | 模板渲染：变量替换、截断逻辑 | 标准单元测试 |
| `test_ai.py` | mock `openai.OpenAI` 的 API 响应，验证请求参数 + 错误分支 | `unittest.mock` |
| `test_tui.py` | 渲染输出内容验证（不需要 mock Rich，直接测返回值） | 标准单元测试 |

测试不强制 100% 覆盖，但核心路径（config 级联、git 命令调用、prompt 构造、AI 调用）必须有测试。

---

## 7. 依赖

```toml
# pyproject.toml [project] dependencies
dependencies = [
    "rich>=13.0",
    "questionary>=2.0",
    "openai>=1.0",
    "tomli>=2.0; python_version < '3.11'",
]
```

全部是纯 Python 包，无系统依赖。总安装体积 < 30MB。

---

## 8. 分发

`pyproject.toml` 配置 entry point：

```toml
[project.scripts]
gitcommit = "gitcommit.cli:main"
```

用户安装：

```bash
pipx install git+https://github.com/xxx/gitcommit.git
# 或本地开发
pipx install -e .
```

安装后 `gitcommit` 命令全局可用。

---

## 9. 不做的（YAGNI）

- ❌ 不做 git hook 集成（`prepare-commit-msg`）——手动运行 TUI 即可
- ❌ 不做 Gitmoji 自动匹配——用户可以用自定义格式模板实现
- ❌ 不做交互式的 scope 选择器——AI 从 diff 自动推断，用户不满意就编辑
- ❌ 不做历史 message 学习——复杂性太高，先做好基础功能
- ❌ 不做多轮对话优化 message——单次生成，用户可手动触发重新生成
- ❌ 不做 VS Code 插件——专注于 CLI
