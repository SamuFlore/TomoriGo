# GitCommit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a TUI CLI tool that reads staged git changes, calls an AI provider to generate a Conventional Commits message, lets the user review/edit, then executes `git commit`.

**Architecture:** Seven focused modules wired through a CLI entry point. `config.py` handles three-layer cascading (defaults → global → project → CLI args). `git.py` wraps subprocess calls to git. `ai.py` provides a single OpenAI-compatible provider class. `prompt.py` builds the system/user prompts. `tui.py` renders Rich panels and questionary prompts. `cli.py` glues everything together.

**Tech Stack:** Python 3.10+, Rich, questionary, openai SDK, tomli

---

## File Structure

```
gitcommit/
├── pyproject.toml              # Project metadata + dependencies + entry point
├── src/gitcommit/
│   ├── __init__.py             # Empty init
│   ├── prompt.py               # Prompt templates and build function
│   ├── config.py               # Config loading with three-layer cascade
│   ├── git.py                  # Subprocess wrappers for git commands
│   ├── ai.py                   # OpenAICompatProvider class
│   ├── tui.py                  # Rich + questionary UI components
│   └── cli.py                  # Argparse entry point, wires everything together
└── tests/
    ├── __init__.py             # Empty init for test discovery
    ├── test_prompt.py
    ├── test_config.py
    ├── test_git.py
    ├── test_ai.py
    └── test_tui.py
```

---

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/gitcommit/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Write pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "gitcommit"
version = "0.1.0"
description = "AI-powered git commit message generator"
requires-python = ">=3.10"
dependencies = [
    "rich>=13.0",
    "questionary>=2.0",
    "openai>=1.0",
    "tomli>=2.0; python_version < '3.11'",
]

[project.scripts]
gitcommit = "gitcommit.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 2: Create empty init files**

Create `src/gitcommit/__init__.py` (empty file).

Create `tests/__init__.py` (empty file).

- [ ] **Step 3: Verify project structure**

Run: `ls -R src/ tests/`
Expected: shows the three files.

- [ ] **Step 4: Install in development mode**

Run: `pip install -e .`
Expected: installs gitcommit with all dependencies. Verify with `pip show gitcommit`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/gitcommit/__init__.py tests/__init__.py
git commit -m "chore: scaffold project structure"
```

---

### Task 2: Prompt Module

**Files:**
- Create: `src/gitcommit/prompt.py`
- Create: `tests/test_prompt.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_prompt.py
import pytest
from gitcommit.prompt import build_prompt, SYSTEM_PROMPT

def test_build_prompt_includes_file_summary():
    result = build_prompt(
        diff="--- a/foo.py\n+++ b/foo.py\n+print('hello')",
        file_summary="foo.py | +1",
        language="zh",
        max_length=72,
    )
    assert "foo.py" in result
    assert "print('hello')" in result

def test_build_prompt_includes_language():
    result = build_prompt(
        diff="diff content",
        file_summary="f.py",
        language="en",
        max_length=72,
    )
    assert "English" in result

def test_build_prompt_trims_diff_when_too_long():
    long_diff = "x" * 9000
    result = build_prompt(
        diff=long_diff,
        file_summary="f.py",
        language="zh",
        max_length=72,
    )
    # Should be truncated
    assert len(result) < 9000 + 500  # prompt overhead ok, but diff should be cut

def test_system_prompt_is_string():
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 50
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_prompt.py -v`
Expected: all 4 tests FAIL with "ModuleNotFoundError: No module named 'gitcommit.prompt'" or "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# src/gitcommit/prompt.py
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


def build_prompt(diff: str, file_summary: str, language: str = "zh", max_length: int = 72) -> tuple[str, str]:
    """Build system and user prompts for the AI.

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    lang_name = {"zh": "中文", "en": "English"}.get(language, language)
    system = SYSTEM_PROMPT.format(language=lang_name, max_length=max_length)

    # Truncate diff if too long (> 8000 chars)
    if len(diff) > 8000:
        diff = diff[:8000] + "\n... (diff truncated)"

    user = f"""以下文件发生了变更：
{file_summary}

git diff:
{diff}

请生成 commit message:"""

    return system, user
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_prompt.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gitcommit/prompt.py tests/test_prompt.py
git commit -m "feat(prompt): add prompt template and build function"
```

---

### Task 3: Config Module

**Files:**
- Create: `src/gitcommit/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config.py
import tempfile
import os
from pathlib import Path
from gitcommit.config import load_config, DEFAULT_CONFIG

def test_default_config_has_required_fields():
    """Default config must have provider and format sections."""
    assert "provider" in DEFAULT_CONFIG
    assert "format" in DEFAULT_CONFIG
    assert "endpoint" in DEFAULT_CONFIG["provider"]
    assert "model" in DEFAULT_CONFIG["provider"]
    assert "api_key" in DEFAULT_CONFIG["provider"]

def test_loads_global_config(tmp_path, monkeypatch):
    """Global config overrides defaults."""
    config_path = tmp_path / ".gitcommit.toml"
    config_path.write_text("""[provider]
api_key = "sk-global-test"
model = "gpt-4"
""")
    monkeypatch.setattr("gitcommit.config.GLOBAL_CONFIG_PATH", config_path)
    monkeypatch.setattr("gitcommit.config.PROJECT_CONFIG_PATH", tmp_path / "nonexistent.toml")

    config = load_config()

    assert config["provider"]["api_key"] == "sk-global-test"
    assert config["provider"]["model"] == "gpt-4"
    # Default fields should still be present
    assert config["provider"]["endpoint"] == DEFAULT_CONFIG["provider"]["endpoint"]

def test_project_overrides_global(tmp_path, monkeypatch):
    """Project config overrides global config."""
    global_path = tmp_path / "global.toml"
    global_path.write_text("""[provider]
api_key = "sk-global"
model = "gpt-4"
""")
    project_path = tmp_path / "project.toml"
    project_path.write_text("""[provider]
api_key = "sk-project"
""")
    monkeypatch.setattr("gitcommit.config.GLOBAL_CONFIG_PATH", global_path)
    monkeypatch.setattr("gitcommit.config.PROJECT_CONFIG_PATH", project_path)

    config = load_config()

    assert config["provider"]["api_key"] == "sk-project"  # overridden
    assert config["provider"]["model"] == "gpt-4"  # inherited from global

def test_cli_overrides_all(tmp_path, monkeypatch):
    """CLI args override all config layers."""
    global_path = tmp_path / "global.toml"
    global_path.write_text('[provider]\napi_key = "sk-global"\nmodel = "gpt-4"\n')
    monkeypatch.setattr("gitcommit.config.GLOBAL_CONFIG_PATH", global_path)
    monkeypatch.setattr("gitcommit.config.PROJECT_CONFIG_PATH", tmp_path / "nonexistent.toml")

    config = load_config(cli_overrides={
        "provider": {"api_key": "sk-cli"},
        "format": {"language": "en"},
    })

    assert config["provider"]["api_key"] == "sk-cli"
    assert config["provider"]["model"] == "gpt-4"
    assert config["format"]["language"] == "en"

def test_missing_config_files_no_error(tmp_path, monkeypatch):
    """Missing config files should not raise errors."""
    monkeypatch.setattr("gitcommit.config.GLOBAL_CONFIG_PATH", tmp_path / "noexist.toml")
    monkeypatch.setattr("gitcommit.config.PROJECT_CONFIG_PATH", tmp_path / "noexist2.toml")

    config = load_config()
    assert config["provider"]["endpoint"] == DEFAULT_CONFIG["provider"]["endpoint"]

def test_toml_syntax_error(tmp_path, monkeypatch):
    """Malformed TOML should raise a readable error."""
    bad_path = tmp_path / "bad.toml"
    bad_path.write_text("this is not valid toml {{{")
    monkeypatch.setattr("gitcommit.config.GLOBAL_CONFIG_PATH", bad_path)
    monkeypatch.setattr("gitcommit.config.PROJECT_CONFIG_PATH", tmp_path / "nonexistent.toml")

    with pytest.raises(SystemExit) as exc:
        load_config()
    assert exc.value.code == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: all 6 tests FAIL with import error.

- [ ] **Step 3: Write minimal implementation**

```python
# src/gitcommit/config.py
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # Python < 3.11

GLOBAL_CONFIG_PATH = Path.home() / ".gitcommit.toml"
PROJECT_CONFIG_PATH = Path.cwd() / ".gitcommit.toml"

DEFAULT_CONFIG: dict[str, Any] = {
    "provider": {
        "name": "openai",
        "api_key": "",
        "model": "gpt-4o-mini",
        "endpoint": "https://api.openai.com/v1",
    },
    "format": {
        "template": "{{type}}({{scope}}): {{message}}",
        "max_length": 72,
        "language": "zh",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override takes precedence."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_toml(path: Path) -> dict:
    """Load a TOML file. Returns empty dict if file doesn't exist."""
    if not path.exists():
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        print(f"错误：配置文件 {path} 语法错误 — {e}", file=sys.stderr)
        sys.exit(1)


def load_config(cli_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load and cascade config from defaults → global → project → CLI args.

    Args:
        cli_overrides: Dict of config sections to override, e.g.
            {"provider": {"api_key": "sk-xxx"}}

    Returns:
        Merged config dict.
    """
    config = DEFAULT_CONFIG.copy()
    config = _deep_merge(config, _load_toml(GLOBAL_CONFIG_PATH))
    config = _deep_merge(config, _load_toml(PROJECT_CONFIG_PATH))
    if cli_overrides:
        config = _deep_merge(config, cli_overrides)
    return config
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gitcommit/config.py tests/test_config.py
git commit -m "feat(config): add three-layer cascading config loader"
```

---

### Task 4: Git Module

**Files:**
- Create: `src/gitcommit/git.py`
- Create: `tests/test_git.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_git.py
import subprocess
import pytest
from unittest.mock import patch, MagicMock
from gitcommit.git import (
    has_staged_changes,
    get_staged_diff,
    get_staged_stats,
    commit,
    GitError,
)

class TestHasStagedChanges:
    def test_returns_true_when_staged_changes_exist(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert has_staged_changes() is True
            mock_run.assert_called_once_with(
                ["git", "diff", "--staged", "--quiet"],
                capture_output=True,
                timeout=10,
            )

    def test_returns_false_when_no_staged_changes(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert has_staged_changes() is False

    def test_not_a_git_repo_raises_git_error(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                128, "git diff", stderr=b"fatal: not a git repository"
            )
            with pytest.raises(GitError, match="git 仓库"):
                has_staged_changes()


class TestGetStagedDiff:
    def test_returns_diff_text(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="--- a/foo.py\n+++ b/foo.py\n+print('hello')",
            )
            result = get_staged_diff()
            assert "foo.py" in result
            mock_run.assert_called_once_with(
                ["git", "diff", "--staged"],
                capture_output=True,
                text=True,
                timeout=10,
            )

    def test_truncates_long_diff(self):
        long_output = "x" * 9000
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=long_output)
            result = get_staged_diff(max_chars=8000)
            assert len(result) <= 8200  # diff + truncation message
            assert "截断" in result


class TestGetStagedStats:
    def test_returns_stats_text(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="foo.py | 5 ++++-\n1 file changed, 4 insertions(+), 1 deletion(-)",
            )
            result = get_staged_stats()
            assert "foo.py" in result
            mock_run.assert_called_once_with(
                ["git", "diff", "--staged", "--stat"],
                capture_output=True,
                text=True,
                timeout=10,
            )

    def test_empty_stats(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = get_staged_stats()
            assert result == ""


class TestCommit:
    def test_commits_with_message(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            commit("feat: test")
            mock_run.assert_called_once_with(
                ["git", "commit", "-m", "feat: test"],
                capture_output=True,
                text=True,
                timeout=30,
            )

    def test_commit_failure_raises_git_error(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "git commit", stderr=b"pre-commit hook failed"
            )
            with pytest.raises(GitError, match="pre-commit hook failed"):
                commit("test")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_git.py -v`
Expected: all tests FAIL with import error.

- [ ] **Step 3: Write minimal implementation**

```python
# src/gitcommit/git.py
import subprocess
import sys


class GitError(Exception):
    """Raised when a git operation fails."""
    pass


def _run_git(args: list[str], timeout: int = 10) -> subprocess.CompletedProcess:
    """Run a git command. Raises GitError on failure."""
    try:
        return subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        if "not a git repository" in stderr.lower():
            raise GitError("当前目录不是 git 仓库") from e
        raise GitError(stderr or str(e)) from e
    except FileNotFoundError:
        raise GitError("未找到 git 命令，请确认 git 已安装并在 PATH 中")
    except subprocess.TimeoutExpired as e:
        raise GitError(f"git 命令超时（{timeout}秒）") from e


def has_staged_changes() -> bool:
    """Check if there are any staged changes."""
    try:
        proc = _run_git(["diff", "--staged", "--quiet"])
        return proc.returncode == 1
    except GitError:
        raise


def get_staged_diff(max_chars: int = 8000) -> str:
    """Get the full staged diff text. Truncates if too long."""
    proc = _run_git(["diff", "--staged"])
    diff = proc.stdout
    if len(diff) > max_chars:
        diff = diff[:max_chars] + "\n... (diff 过长已截断)"
    return diff


def get_staged_stats() -> str:
    """Get staged changes summary (--stat)."""
    proc = _run_git(["diff", "--staged", "--stat"])
    return proc.stdout


def commit(message: str) -> None:
    """Execute git commit with the given message."""
    try:
        subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise GitError((e.stderr or "").strip() or str(e)) from e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_git.py -v`
Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gitcommit/git.py tests/test_git.py
git commit -m "feat(git): add git operation wrappers with error handling"
```

---

### Task 5: AI Module

**Files:**
- Create: `src/gitcommit/ai.py`
- Create: `tests/test_ai.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ai.py
import pytest
from unittest.mock import patch, MagicMock
from gitcommit.ai import generate_message, AIError


class TestGenerateMessage:
    def test_calls_openai_with_correct_params(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="feat(test): add thing"))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("gitcommit.ai.OpenAI", return_value=mock_client):
            result = generate_message(
                system_prompt="sys",
                user_prompt="usr",
                api_key="sk-test",
                endpoint="https://api.test.com/v1",
                model="test-model",
            )

        assert result == "feat(test): add thing"
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args.kwargs
        assert call_args["model"] == "test-model"
        assert call_args["messages"][0]["role"] == "system"
        assert call_args["messages"][1]["role"] == "user"
        assert call_args["temperature"] == 0.3
        assert call_args["max_tokens"] == 150

    def test_returns_stripped_message(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="  feat: test  \n\n"))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("gitcommit.ai.OpenAI", return_value=mock_client):
            result = generate_message(
                system_prompt="s",
                user_prompt="u",
                api_key="sk",
                endpoint="https://a.com/v1",
                model="m",
            )

        assert result == "feat: test"

    def test_missing_api_key_raises(self):
        with pytest.raises(AIError, match="API key"):
            generate_message(
                system_prompt="s",
                user_prompt="u",
                api_key="",  # empty
                endpoint="https://a.com/v1",
                model="m",
            )

    def test_network_error_raises(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = OSError("Connection refused")

        with patch("gitcommit.ai.OpenAI", return_value=mock_client):
            with pytest.raises(AIError, match="网络"):
                generate_message(
                    system_prompt="s",
                    user_prompt="u",
                    api_key="sk",
                    endpoint="https://a.com/v1",
                    model="m",
                )

    def test_http_error_shows_status(self):
        from openai import APIStatusError

        mock_client = MagicMock()
        mock_response = MagicMock(status_code=401)
        mock_client.chat.completions.create.side_effect = APIStatusError(
            "Unauthorized", response=mock_response, body={"error": "bad key"}
        )

        with patch("gitcommit.ai.OpenAI", return_value=mock_client):
            with pytest.raises(AIError, match="401"):
                generate_message(
                    system_prompt="s",
                    user_prompt="u",
                    api_key="sk",
                    endpoint="https://a.com/v1",
                    model="m",
                )

    def test_empty_response_raises(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=""))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("gitcommit.ai.OpenAI", return_value=mock_client):
            with pytest.raises(AIError, match="返回了空内容"):
                generate_message(
                    system_prompt="s",
                    user_prompt="u",
                    api_key="sk",
                    endpoint="https://a.com/v1",
                    model="m",
                )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ai.py -v`
Expected: all 6 tests FAIL with import error.

- [ ] **Step 3: Write minimal implementation**

```python
# src/gitcommit/ai.py
from openai import OpenAI


class AIError(Exception):
    """Raised when an AI API call fails."""
    pass


def generate_message(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    endpoint: str,
    model: str,
    timeout: float = 15.0,
) -> str:
    """Call the AI API to generate a commit message.

    Args:
        system_prompt: System-level instructions for the AI.
        user_prompt: User-level prompt with the diff content.
        api_key: API key for authentication.
        endpoint: API base URL (OpenAI-compatible).
        model: Model name to use.
        timeout: Request timeout in seconds.

    Returns:
        Generated commit message string.

    Raises:
        AIError: On any API failure.
    """
    if not api_key:
        raise AIError(
            "API key 未配置。请在 ~/.gitcommit.toml 或项目 .gitcommit.toml 中设置 provider.api_key。"
        )

    client = OpenAI(api_key=api_key, base_url=endpoint, timeout=timeout)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=150,
        )
    except Exception as e:
        # Convert generic exceptions to AIError with useful messages
        error_str = str(e)
        if hasattr(e, "status_code"):
            status = e.status_code
            raise AIError(f"API 返回错误 (HTTP {status}): {error_str}") from e
        if "Connection" in error_str or "connect" in error_str.lower():
            raise AIError(f"网络错误，无法连接 API: {error_str}") from e
        raise AIError(f"API 调用失败: {error_str}") from e

    content = (response.choices[0].message.content or "").strip()

    if not content:
        raise AIError("AI 返回了空内容，请重试。")

    return content
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ai.py -v`
Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gitcommit/ai.py tests/test_ai.py
git commit -m "feat(ai): add OpenAI-compatible provider with error handling"
```

---

### Task 6: TUI Module

**Files:**
- Create: `src/gitcommit/tui.py`
- Create: `tests/test_tui.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tui.py
from gitcommit.tui import Action, build_diff_table


class TestActionEnum:
    def test_action_values(self):
        assert Action.COMMIT == "commit"
        assert Action.REGENERATE == "regenerate"
        assert Action.CANCEL == "cancel"
        assert Action.EDIT == "edit"


class TestBuildDiffTable:
    def test_parses_stat_line(self):
        stats = "foo.py | 10 +++++-----\nbar.py | 3 +++\n2 files changed"
        table = build_diff_table(stats)

        # build_diff_table returns a Rich Table; check it has rows
        assert table.row_count >= 2  # header + at least 1 file
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tui.py -v`
Expected: tests FAIL with import error.

- [ ] **Step 3: Write minimal implementation**

```python
# src/gitcommit/tui.py
from enum import Enum

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


class Action(str, Enum):
    COMMIT = "commit"
    REGENERATE = "regenerate"
    CANCEL = "cancel"
    EDIT = "edit"


def show_diff_summary(stats: str) -> None:
    """Display staged changes summary as a Rich table."""
    table = build_diff_table(stats)

    if table.row_count > 0:
        console.print(Panel(table, title="📋 Staged Changes", border_style="blue"))
    else:
        console.print("[yellow]没有暂存的变更[/yellow]")


def build_diff_table(stats: str) -> Table:
    """Parse git --stat output into a Rich table."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("文件", style="cyan")
    table.add_column("变更", style="green")

    lines = stats.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line or "file" in line.lower() and "changed" in line.lower():
            # Skip the summary line like "2 files changed, 10 insertions..."
            continue
        if "|" in line:
            file_part, change_part = line.rsplit("|", 1)
            table.add_row(file_part.strip(), change_part.strip())
        else:
            # Line without | — add as plain text
            table.add_row(line, "")

    return table


def review_message(message: str) -> tuple[Action, str]:
    """Show AI-generated message and let user decide.

    Args:
        message: The AI-generated commit message.

    Returns:
        Tuple of (action, final_message).
        final_message is the edited message if action is EDIT.
    """
    panel = Panel(
        Text(message, style="bold green"),
        title="🤖 AI 生成的 Commit Message",
        border_style="green",
    )
    console.print(panel)

    choice = questionary.select(
        "选择操作：",
        choices=[
            {"name": "✓ 确认提交", "value": "commit"},
            {"name": "✎ 编辑", "value": "edit"},
            {"name": "↻ 重新生成", "value": "regenerate"},
            {"name": "✗ 取消", "value": "cancel"},
        ],
    ).ask()

    if choice is None:  # User pressed Ctrl+C
        return (Action.CANCEL, "")

    if choice == "edit":
        edited = questionary.text("编辑 commit message：", default=message).ask()
        if edited is None:
            return (Action.CANCEL, "")
        # After editing, ask again what to do
        return _reconfirm(edited)
    elif choice == "regenerate":
        return (Action.REGENERATE, message)
    elif choice == "cancel":
        return (Action.CANCEL, "")
    else:
        return (Action.COMMIT, message)


def _reconfirm(message: str) -> tuple[Action, str]:
    """Show edited message and ask for final confirmation."""
    panel = Panel(
        Text(message, style="bold yellow"),
        title="📝 编辑后的 Commit Message",
        border_style="yellow",
    )
    console.print(panel)

    choice = questionary.select(
        "确认提交？",
        choices=[
            {"name": "✓ 提交", "value": "commit"},
            {"name": "↻ 重新生成", "value": "regenerate"},
            {"name": "✗ 取消", "value": "cancel"},
        ],
    ).ask()

    if choice is None:
        return (Action.CANCEL, "")
    return (Action(choice), message)


def show_success(message: str) -> None:
    """Display successful commit confirmation."""
    panel = Panel(
        Text(message, style="bold green"),
        title="✅ 提交成功！",
        border_style="green",
    )
    console.print(panel)


def show_cancelled() -> None:
    """Display cancellation message."""
    console.print("[yellow]已取消，未进行任何提交。[/yellow]")


def show_error(title: str, detail: str) -> None:
    """Display an error panel."""
    panel = Panel(
        Text(detail, style="red"),
        title=f"❌ {title}",
        border_style="red",
    )
    console.print(panel)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tui.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/gitcommit/tui.py tests/test_tui.py
git commit -m "feat(tui): add Rich + questionary interactive screens"
```

---

### Task 7: CLI Module (Wiring Everything Together)

**Files:**
- Create: `src/gitcommit/cli.py`

- [ ] **Step 1: Write the CLI module**

```python
# src/gitcommit/cli.py
import argparse
import sys

from gitcommit.config import load_config
from gitcommit.git import (
    has_staged_changes,
    get_staged_diff,
    get_staged_stats,
    commit,
    GitError,
)
from gitcommit.prompt import build_prompt
from gitcommit.ai import generate_message, AIError
from gitcommit.tui import (
    Action,
    show_diff_summary,
    review_message,
    show_success,
    show_cancelled,
    show_error,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI 驱动的 git commit message 生成工具",
        prog="gitcommit",
    )
    parser.add_argument(
        "-p", "--provider",
        help="AI provider 名称（覆盖配置文件）",
    )
    parser.add_argument(
        "-m", "--model",
        help="模型名称（覆盖配置文件）",
    )
    parser.add_argument(
        "-f", "--format",
        help="自定义 message 格式模板",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="只生成和展示 message，不执行 git commit",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="显示当前生效的配置",
    )
    args = parser.parse_args()

    # Build CLI overrides from args
    cli_overrides = {}
    provider_override = {}
    if args.provider:
        provider_override["name"] = args.provider
    if args.model:
        provider_override["model"] = args.model
    if provider_override:
        cli_overrides["provider"] = provider_override
    format_override = {}
    if args.format:
        format_override["template"] = args.format
    if format_override:
        cli_overrides["format"] = format_override

    # Load config
    try:
        config = load_config(cli_overrides if cli_overrides else None)
    except SystemExit:
        return  # config.load already printed error

    # --config flag: show config and exit
    if args.config:
        import json
        print(json.dumps(config, indent=2, ensure_ascii=False))
        return

    # Check for staged changes
    try:
        if not has_staged_changes():
            show_error("没有暂存的变更", "请先使用 git add 暂存要提交的文件。")
            sys.exit(1)
    except GitError as e:
        show_error("Git 错误", str(e))
        sys.exit(1)

    # Get diff and stats
    try:
        diff = get_staged_diff()
        stats = get_staged_stats()
    except GitError as e:
        show_error("Git 错误", str(e))
        sys.exit(1)

    # Show diff summary
    show_diff_summary(stats)

    # Build prompts
    provider_cfg = config["provider"]
    format_cfg = config["format"]
    system_prompt, user_prompt = build_prompt(
        diff=diff,
        file_summary=stats,
        language=format_cfg.get("language", "zh"),
        max_length=format_cfg.get("max_length", 72),
    )

    # Interactive loop: generate → review → commit or regenerate
    while True:
        try:
            message = generate_message(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                api_key=provider_cfg.get("api_key", ""),
                endpoint=provider_cfg.get("endpoint", "https://api.openai.com/v1"),
                model=provider_cfg.get("model", "gpt-4o-mini"),
            )
        except AIError as e:
            show_error("AI 调用失败", str(e))
            # Ask if user wants to retry
            import questionary
            retry = questionary.confirm("是否重试？", default=True).ask()
            if retry:
                continue
            else:
                sys.exit(1)

        action, final_message = review_message(message)

        if action == Action.CANCEL:
            show_cancelled()
            return
        elif action == Action.REGENERATE:
            continue
        elif action == Action.COMMIT:
            if args.dry_run:
                show_success(f"[DRY RUN] {final_message}")
                return
            try:
                commit(final_message)
                show_success(final_message)
                return
            except GitError as e:
                show_error("提交失败", str(e))
                sys.exit(1)
```

- [ ] **Step 2: Verify the module imports correctly**

Run: `python -c "from gitcommit.cli import main; print('CLI imports OK')"`
Expected: "CLI imports OK"

- [ ] **Step 3: Verify CLI help text**

Run: `python -m gitcommit.cli --help`
Expected: shows help text with all 5 options.

- [ ] **Step 4: Test --config flag**

Run: `python -m gitcommit.cli --config`
Expected: prints default config as JSON.

- [ ] **Step 5: Test error when not in git repo**

Run: `cd /tmp && python -m gitcommit.cli` (or any non-git directory)
Expected: error message "当前目录不是 git 仓库"

- [ ] **Step 6: Test error when no staged changes**

Run: inside a git repo with no staged changes: `python -m gitcommit.cli`
Expected: "没有暂存的变更" message.

- [ ] **Step 7: Commit**

```bash
git add src/gitcommit/cli.py
git commit -m "feat(cli): add CLI entry point wiring all modules"
```

---

### Task 8: Integration Verification

- [ ] **Step 1: Create a test git repo and verify end-to-end**

```bash
mkdir /tmp/test-gitcommit && cd /tmp/test-gitcommit
git init
echo "test" > file.txt
git add file.txt
```

Run: `cd /tmp/test-gitcommit && python -m gitcommit.cli --dry-run`
Expected: shows diff summary, then shows AI-generated message (will fail at AI call unless API key is configured, but dry-run logic before that should work).

If API key is configured, the full flow should work:
```bash
gitcommit -n  # dry-run
gitcommit     # actual commit (after configuring API key)
```

- [ ] **Step 2: Run all tests one final time**

Run: `pytest tests/ -v`
Expected: all tests PASS (20+ tests).

- [ ] **Step 3: Add .gitignore and commit**

Create `e:\GitCommit\.gitignore`:
```gitignore
__pycache__/
*.pyc
.egg-info/
dist/
build/
.pytest_cache/
.superpowers/
```

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
```

---

## Dependency Graph

```
prompt.py  ──┐
config.py  ──┤
git.py     ──┼──→ cli.py
ai.py      ──┤
tui.py     ──┘
```

All modules are independent of each other; only `cli.py` imports them all.

---

## Testing Summary

| Module | Test File | Test Count |
|--------|-----------|------------|
| prompt | test_prompt.py | 4 |
| config | test_config.py | 6 |
| git | test_git.py | 9 |
| ai | test_ai.py | 6 |
| tui | test_tui.py | 2 |
| **Total** | | **27** |
