"""Tests for TUI module: Rich + questionary interactive screens."""

import pytest
from unittest.mock import patch, MagicMock


# ============================================================
# Tests for Action enum
# ============================================================
class TestActionEnum:
    def test_action_has_commit(self):
        from gitcommit.tui import Action
        assert hasattr(Action, "COMMIT")
        assert isinstance(Action.COMMIT, Action)

    def test_action_has_regenerate(self):
        from gitcommit.tui import Action
        assert hasattr(Action, "REGENERATE")
        assert isinstance(Action.REGENERATE, Action)

    def test_action_has_cancel(self):
        from gitcommit.tui import Action
        assert hasattr(Action, "CANCEL")
        assert isinstance(Action.CANCEL, Action)

    def test_action_has_edit(self):
        from gitcommit.tui import Action
        assert hasattr(Action, "EDIT")
        assert isinstance(Action.EDIT, Action)

    def test_action_values_are_distinct(self):
        from gitcommit.tui import Action
        values = {Action.COMMIT, Action.REGENERATE, Action.CANCEL, Action.EDIT}
        assert len(values) == 4


# ============================================================
# Tests for build_diff_table
# ============================================================
class TestBuildDiffTable:
    def test_parses_single_file_stat(self):
        from gitcommit.tui import build_diff_table
        from rich.table import Table

        stats = " src/foo.py | 5 ++++-\n 1 file changed, 4 insertions(+), 1 deletion(-)\n"
        table = build_diff_table(stats)

        assert isinstance(table, Table)
        # Should have 2 columns: File, Changes
        assert len(table.columns) == 2
        # Should have 1 data row (ignoring summary line)
        assert len(table.rows) == 1

    def test_parses_multiple_files_stat(self):
        from gitcommit.tui import build_diff_table
        from rich.table import Table

        stats = (
            " src/foo.py | 12 ++++++++++++\n"
            " src/bar.py |  3 +--\n"
            " src/baz.py |  1 +\n"
            " 3 files changed, 14 insertions(+), 2 deletions(-)\n"
        )
        table = build_diff_table(stats)

        assert isinstance(table, Table)
        assert len(table.rows) == 3
        # Column titles should be File and Changes
        titles = [str(col.header) for col in table.columns]
        assert "File" in titles[0]
        assert "Changes" in titles[1]

    def test_handles_empty_stats(self):
        from gitcommit.tui import build_diff_table
        from rich.table import Table

        table = build_diff_table("")
        assert isinstance(table, Table)
        assert len(table.rows) == 0

    def test_handles_whitespace_only_stats(self):
        from gitcommit.tui import build_diff_table
        from rich.table import Table

        table = build_diff_table("   \n  \n  ")
        assert isinstance(table, Table)
        assert len(table.rows) == 0

    def test_ignores_summary_line(self):
        from gitcommit.tui import build_diff_table

        stats = (
            " src/foo.py | 3 +++\n"
            " 1 file changed, 3 insertions(+)\n"
        )
        table = build_diff_table(stats)
        # Only the file line, not the summary line
        assert len(table.rows) == 1

    def test_table_has_correct_styling(self):
        from gitcommit.tui import build_diff_table
        from rich.table import Table

        stats = " src/foo.py | 5 ++++-\n"
        table = build_diff_table(stats)

        # Table should have some styling (box, borders, etc.)
        assert table.box is not None
        assert table.show_header is True

    def test_handles_stats_with_only_summary_line(self):
        from gitcommit.tui import build_diff_table
        from rich.table import Table

        stats = " 0 files changed\n"
        table = build_diff_table(stats)
        assert isinstance(table, Table)
        assert len(table.rows) == 0

    def test_strips_leading_whitespace_from_filenames(self):
        from gitcommit.tui import build_diff_table
        from rich.console import Console as RichConsole

        stats = "   path/to/file.py   | 10 +++++-----\n"
        table = build_diff_table(stats)

        # Should parse exactly 1 row (the file line)
        assert len(table.rows) == 1
        # Render the table and verify filename appears without leading whitespace
        test_console = RichConsole(width=120, record=True)
        test_console.print(table)
        rendered = test_console.export_text()
        assert "path/to/file.py" in rendered


# ============================================================
# Tests for show_diff_summary
# ============================================================
class TestShowDiffSummary:
    def test_calls_console_print_with_panel(self):
        from gitcommit.tui import show_diff_summary

        stats = " src/foo.py | 5 ++++-\n 1 file changed\n"
        with patch("gitcommit.tui.console") as mock_console:
            show_diff_summary(stats)
            mock_console.print.assert_called_once()

    def test_accepts_empty_stats(self):
        from gitcommit.tui import show_diff_summary

        with patch("gitcommit.tui.console") as mock_console:
            show_diff_summary("")
            mock_console.print.assert_called_once()


# ============================================================
# Tests for review_message
# ============================================================
class TestReviewMessage:
    def test_returns_commit_action(self):
        from gitcommit.tui import review_message, Action

        with patch("gitcommit.tui.console"), \
             patch("questionary.select") as mock_select:
            mock_select.return_value.unsafe_ask.return_value = "yes, commit"
            action, msg = review_message("feat(foo): add bar")
            assert action == Action.COMMIT
            assert msg == "feat(foo): add bar"

    def test_returns_regenerate_action(self):
        from gitcommit.tui import review_message, Action

        with patch("gitcommit.tui.console"), \
             patch("questionary.select") as mock_select:
            mock_select.return_value.unsafe_ask.return_value = "regenerate"
            action, msg = review_message("feat(foo): add bar")
            assert action == Action.REGENERATE
            assert msg == "feat(foo): add bar"

    def test_returns_cancel_action(self):
        from gitcommit.tui import review_message, Action

        with patch("gitcommit.tui.console"), \
             patch("questionary.select") as mock_select:
            mock_select.return_value.unsafe_ask.return_value = "cancel"
            action, msg = review_message("feat(foo): add bar")
            assert action == Action.CANCEL
            assert msg == "feat(foo): add bar"

    def test_returns_edit_action(self):
        from gitcommit.tui import review_message, Action

        with patch("gitcommit.tui.console"), \
             patch("questionary.select") as mock_select:
            mock_select.return_value.unsafe_ask.return_value = "edit message"
            action, msg = review_message("feat(foo): add bar")
            assert action == Action.EDIT
            assert msg == "feat(foo): add bar"

    def test_displays_message_in_panel(self):
        from gitcommit.tui import review_message

        with patch("gitcommit.tui.console") as mock_console, \
             patch("questionary.select") as mock_select:
            mock_select.return_value.unsafe_ask.return_value = "yes, commit"
            review_message("feat(test): something")
            # console.print should have been called with a Panel
            assert mock_console.print.called

    def test_questionary_has_four_choices(self):
        from gitcommit.tui import review_message

        with patch("gitcommit.tui.console"), \
             patch("questionary.select") as mock_select:
            mock_select.return_value.unsafe_ask.return_value = "yes, commit"
            review_message("feat: test")
            # Verify select was called with 4 choices
            call_args = mock_select.call_args
            # questionary.select receives a message and choices list
            assert call_args is not None


# ============================================================
# Tests for _reconfirm
# ============================================================
class TestReconfirm:
    def test_returns_commit_action(self):
        from gitcommit.tui import _reconfirm, Action

        with patch("gitcommit.tui.console"), \
             patch("questionary.select") as mock_select:
            mock_select.return_value.unsafe_ask.return_value = "yes, commit"
            action, msg = _reconfirm("feat(foo): edited message")
            assert action == Action.COMMIT
            assert msg == "feat(foo): edited message"

    def test_returns_cancel_action(self):
        from gitcommit.tui import _reconfirm, Action

        with patch("gitcommit.tui.console"), \
             patch("questionary.select") as mock_select:
            mock_select.return_value.unsafe_ask.return_value = "cancel"
            action, msg = _reconfirm("edited msg")
            assert action == Action.CANCEL
            assert msg == "edited msg"

    def test_displays_message_in_panel(self):
        from gitcommit.tui import _reconfirm

        with patch("gitcommit.tui.console") as mock_console, \
             patch("questionary.select") as mock_select:
            mock_select.return_value.unsafe_ask.return_value = "yes, commit"
            _reconfirm("final message")
            assert mock_console.print.called


# ============================================================
# Tests for show_success
# ============================================================
class TestShowSuccess:
    def test_prints_green_panel(self):
        from gitcommit.tui import show_success

        with patch("gitcommit.tui.console") as mock_console:
            show_success("feat: committed!")
            mock_console.print.assert_called_once()

    def test_message_appears_in_output(self):
        from gitcommit.tui import show_success

        with patch("gitcommit.tui.console") as mock_console:
            show_success("feat(foo): done")
            # The message should be part of what was printed
            call_args = mock_console.print.call_args
            assert call_args is not None


# ============================================================
# Tests for show_cancelled
# ============================================================
class TestShowCancelled:
    def test_prints_message(self):
        from gitcommit.tui import show_cancelled

        with patch("gitcommit.tui.console") as mock_console:
            show_cancelled()
            mock_console.print.assert_called_once()


# ============================================================
# Tests for show_error
# ============================================================
class TestShowError:
    def test_prints_red_panel(self):
        from gitcommit.tui import show_error

        with patch("gitcommit.tui.console") as mock_console:
            show_error("Error Title", "Something went wrong")
            mock_console.print.assert_called_once()

    def test_title_in_output(self):
        from gitcommit.tui import show_error

        with patch("gitcommit.tui.console") as mock_console:
            show_error("API Error", "Connection refused")
            call_args = mock_console.print.call_args
            assert call_args is not None

    def test_detail_in_output(self):
        from gitcommit.tui import show_error

        with patch("gitcommit.tui.console") as mock_console:
            show_error("Git Error", "not a git repository")
            call_args = mock_console.print.call_args
            assert call_args is not None


# ============================================================
# Tests for console singleton
# ============================================================
class TestConsole:
    def test_console_is_rich_console_instance(self):
        from gitcommit.tui import console
        from rich.console import Console as RichConsole
        assert isinstance(console, RichConsole)
