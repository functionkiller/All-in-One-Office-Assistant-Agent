from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()


def print_title(text: str) -> None:
    """Print a styled title."""
    console.print()
    console.print(Panel(text, style="bold cyan"))


def print_markdown(text: str) -> None:
    """Print markdown content with Rich rendering."""
    console.print(Markdown(text))


def print_success(text: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {text}")


def print_info(text: str) -> None:
    """Print an info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {text}")


def print_table(
    title: str,
    columns: list[str],
    rows: list[list[str]],
) -> None:
    """Print a Rich table."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def print_file_output(paths: list[Path]) -> None:
    """Print generated file paths."""
    if not paths:
        return
    console.print("\n[bold]生成的文件:[/bold]")
    for p in paths:
        console.print(f"  [cyan]📄 {p}[/cyan]")
