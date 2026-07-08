"""TUI module: Rich + questionary interactive screens for gitcommit."""

from enum import Enum

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class Action(Enum):
    """User action after reviewing a generated commit message."""
    COMMIT = "commit"
    REGENERATE = "regenerate"
    CANCEL = "cancel"
    EDIT = "edit"


def build_diff_table(stats: str) -> Table:
    """Parse git --stat output into a Rich Table.

    Args:
        stats: The output of ``git diff --staged --stat``.

    Returns:
        A Rich Table with columns "File" and "Changes", one row per file.
        Summary lines (e.g. "2 files changed") are ignored.
    """
    table = Table(title="Staged Changes", show_header=True, header_style="bold")
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Changes", style="green")

    for line in stats.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Only parse lines that contain the "|" separator (file stat lines)
        if "|" in line:
            parts = line.split("|", 1)
            file_part = parts[0].strip()
            changes_part = parts[1].strip()
            table.add_row(file_part, changes_part)

    return table


def show_diff_summary(stats: str) -> None:
    """Render a Rich Panel containing the diff stats table.

    Args:
        stats: The output of ``git diff --staged --stat``.
    """
    table = build_diff_table(stats)
    panel = Panel(table, title="Diff Summary", border_style="blue")
    console.print(panel)


def review_message(message: str) -> tuple[Action, str]:
    """Show the generated commit message and ask the user to decide.

    Displays the message in a Rich Panel, then presents a questionary
    select with four options: commit, edit, regenerate, cancel.

    Args:
        message: The generated commit message to review.

    Returns:
        A tuple of (Action, message).
    """
    panel = Panel(
        f"[bold white]{message}[/bold white]",
        title="Proposed Commit Message",
        border_style="yellow",
    )
    console.print(panel)

    choice = questionary.select(
        "What would you like to do?",
        choices=[
            {"name": "Yes, commit", "value": "yes, commit"},
            {"name": "Edit message", "value": "edit message"},
            {"name": "Regenerate", "value": "regenerate"},
            {"name": "Cancel", "value": "cancel"},
        ],
    ).unsafe_ask()

    if choice is None:
        return Action.CANCEL, message

    if choice == "edit message":
        edited = questionary.text("Edit commit message:", default=message).ask()
        if edited is None:
            return Action.CANCEL, message
        return _reconfirm(edited)
    elif choice == "regenerate":
        return Action.REGENERATE, message
    elif choice == "cancel":
        return Action.CANCEL, message
    else:
        return Action.COMMIT, message


def _reconfirm(message: str) -> tuple[Action, str]:
    """Reconfirm after the user has edited the message.

    Shows the edited message and asks whether to commit or cancel.

    Args:
        message: The edited commit message.

    Returns:
        A tuple of (Action, message).
    """
    panel = Panel(
        f"[bold white]{message}[/bold white]",
        title="Edited Commit Message",
        border_style="yellow",
    )
    console.print(panel)

    choice = questionary.select(
        "Confirm edited message?",
        choices=[
            {"name": "Yes, commit", "value": "yes, commit"},
            {"name": "Cancel", "value": "cancel"},
        ],
    ).unsafe_ask()

    if choice is None:
        return Action.CANCEL, message

    action_map = {
        "yes, commit": Action.COMMIT,
        "cancel": Action.CANCEL,
    }

    return action_map.get(choice, Action.CANCEL), message


def show_success(message: str) -> None:
    """Display a green success panel.

    Args:
        message: The commit message that was successfully used.
    """
    panel = Panel(
        f"[bold white]{message}[/bold white]",
        title="[bold green]Committed Successfully[/bold green]",
        border_style="green",
    )
    console.print(panel)


def show_cancelled() -> None:
    """Display a yellow cancelled message."""
    console.print("[yellow]Commit cancelled.[/yellow]")


def show_error(title: str, detail: str) -> None:
    """Display a red error panel.

    Args:
        title: Short error title.
        detail: Detailed error description.
    """
    panel = Panel(
        f"[white]{detail}[/white]",
        title=f"[bold red]{title}[/bold red]",
        border_style="red",
    )
    console.print(panel)
