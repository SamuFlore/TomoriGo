# src/gitcommit/git.py
import subprocess
import sys


class GitError(Exception):
    """Raised when a git operation fails."""
    pass


def _run_git(args: list[str], timeout: int = 10) -> subprocess.CompletedProcess:
    """Run a git command. Raises GitError on non-zero exit or other failures."""
    try:
        proc = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise GitError("未找到 git 命令，请确认 git 已安装并在 PATH 中")
    except subprocess.TimeoutExpired as e:
        raise GitError(f"git 命令超时（{timeout}秒）") from e

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        if "not a git repository" in stderr.lower():
            raise GitError("当前目录不是 git 仓库")
        raise GitError(stderr or f"git {' '.join(args)} 失败 (exit code {proc.returncode})")

    return proc


def has_staged_changes() -> bool:
    """Check if there are any staged changes.

    Uses git diff --staged --quiet which exits 0 for no changes, 1 for changes.
    """
    try:
        proc = subprocess.run(
            ["git", "diff", "--staged", "--quiet"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        raise GitError("未找到 git 命令，请确认 git 已安装并在 PATH 中")
    except subprocess.TimeoutExpired as e:
        raise GitError(f"git 命令超时（10秒）") from e

    if proc.returncode == 0:
        return False
    elif proc.returncode == 1:
        return True
    else:
        stderr = (proc.stderr or "").strip()
        if "not a git repository" in stderr.lower():
            raise GitError("当前目录不是 git 仓库")
        raise GitError(stderr or f"git diff --staged --quiet 失败 (exit code {proc.returncode})")


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
