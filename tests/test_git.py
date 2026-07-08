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
            mock_run.return_value = MagicMock(returncode=1, stderr="")
            assert has_staged_changes() is True
            mock_run.assert_called_once_with(
                ["git", "diff", "--staged", "--quiet"],
                capture_output=True,
                text=True,
                timeout=10,
            )

    def test_returns_false_when_no_staged_changes(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            assert has_staged_changes() is False

    def test_not_a_git_repo_raises_git_error(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=128, stderr="fatal: not a git repository"
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
            assert len(result) <= 8200
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
                check=True,
            )

    def test_commit_failure_raises_git_error(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "git commit", stderr=b"pre-commit hook failed"
            )
            with pytest.raises(GitError, match="pre-commit hook failed"):
                commit("test")
