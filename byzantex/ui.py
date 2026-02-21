import datetime
import time
from pathlib import Path
from typing import List, Optional

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

console = Console()

_BANNER_LINES = [
    "██████╗██╗   █████████╗█████╗███╗   ███████████████████╗  ██╗",
    "██╔══██╚██╗ ██╔╚══███╔██╔══██████╗  ██╚══██╔══██╔════╚██╗██╔╝",
    "██████╔╝╚████╔╝  ███╔╝█████████╔██╗ ██║  ██║  █████╗  ╚███╔╝ ",
    "██╔══██╗ ╚██╔╝  ███╔╝ ██╔══████║╚██╗██║  ██║  ██╔══╝  ██╔██╗ ",
    "██████╔╝  ██║  █████████║  ████║ ╚████║  ██║  █████████╔╝ ██╗",
    "╚═════╝   ╚═╝  ╚══════╚═╝  ╚═╚═╝  ╚═══╝  ╚═╝  ╚══════╚═╝  ╚═╝",
]

_BANNER_COLOR = "#FF3131"


def show_banner():
    """Render the BYZANTEX ASCII banner."""
    console.print()
    for line in _BANNER_LINES:
        console.print(Align.center(f"[bold {_BANNER_COLOR}]{line}[/bold {_BANNER_COLOR}]"))
    console.print()
    subtitle = Text("⚡  Regression Triage in 30 Seconds  •  v0.1.0", style="dim white")
    console.print(Align.center(subtitle))
    console.print()
    console.print(Rule(style="dim bright_blue"))
    console.print()


def show_file_selector(log_files: List[Path]) -> Optional[Path]:
    """Display a numbered file table and return the chosen Path."""

    table = Table(
        box=box.ROUNDED,
        border_style="bright_blue",
        show_header=True,
        header_style="bold bright_blue",
        title="[bold white]  Select a Log File  [/bold white]",
        padding=(0, 2),
        min_width=60,
    )
    table.add_column("#", style="bold yellow", width=4, justify="right")
    table.add_column("File", min_width=42)
    table.add_column("Size", style="dim", justify="right", width=9)
    table.add_column("Modified", style="dim cyan", width=17)

    for i, path in enumerate(log_files, 1):
        stat = path.stat()
        size_str = _fmt_size(stat.st_size)
        mtime_str = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%b %d  %H:%M")

        name = path.name
        if "regression" in name:
            name_style = "bright_blue"
        elif "issue" in name:
            name_style = "yellow"
        elif "data_integrity" in name or "escalation" in name:
            name_style = "bright_green"
        else:
            name_style = "white"

        table.add_row(
            str(i),
            f"[{name_style}]{name}[/{name_style}]",
            size_str,
            mtime_str,
        )

    console.print(table)
    console.print()

    choices = [str(i) for i in range(1, len(log_files) + 1)]
    raw = Prompt.ask(
        "[bold yellow]  >[/bold yellow] [bold white]Enter number[/bold white]",
        choices=choices,
        show_choices=False,
    )
    return log_files[int(raw) - 1]


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024**2:.1f} MB"


# ── Analysis display ──────────────────────────────────────────────────────────

def show_spinner(message: str, duration: float = 0.5):
    """Animated spinner that disappears after completion."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(message, total=None)
        time.sleep(duration)


def show_header(failures_count: int, time_taken: float, ip_name: str):
    """Summary panel shown before individual failures."""
    console.print()
    console.print(Panel(
        f"[bold green]IP:[/bold green]  [white]{ip_name}[/white]\n"
        f"[bold green]Found[/bold green] [white]{failures_count}[/white] "
        f"[bold green]failure(s) in[/bold green] [white]{time_taken:.2f}s[/white]",
        title="[bold white]⚡ BYZANTEX[/bold white]",
        border_style="green",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
    console.print()


def show_failure(num: int, failure: dict, category: str, reasoning: str):
    """Render one failure in a colored bordered panel."""

    cat_display = {
        "BUG":     ("🔴", "red"),
        "TEST":    ("🟡", "yellow"),
        "INFRA":   ("🔵", "bright_blue"),
        "UNKNOWN": ("⚪", "white"),
    }
    icon, color = cat_display.get(category, ("⚪", "white"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style=f"bold {color}", width=12)
    table.add_column("Value", style="white")

    table.add_row("Category", f"{icon}  [{color}]{category}[/{color}]")
    table.add_row("Type",     f"[bold]{failure.get('error_type', 'UNKNOWN')}[/bold]")
    table.add_row("Time",     failure.get('timestamp', 'unknown'))
    table.add_row("File",     f"[bold white]{failure.get('file_path', 'unknown')}[/bold white]")
    table.add_row("Line",     f"[yellow]{failure.get('line_number', '?')}[/yellow]")

    if failure.get('assertion_name'):
        table.add_row("Assertion", f"[cyan]{failure['assertion_name']}[/cyan]")

    message = failure.get('message', '') or '[dim](no message)[/dim]'
    if len(message) > 80:
        message = message[:77] + '...'
    table.add_row("Message", message)

    table.add_row("", "")
    table.add_row("Reasoning", f"[italic dim]{reasoning}[/italic dim]")

    console.print(Panel(
        table,
        title=f"[bold {color}] FAILURE {num} [/bold {color}]",
        border_style=color,
        box=box.ROUNDED,
    ))
    console.print()


def show_tip(message: str):
    console.print(Rule(style="dim bright_blue"))
    console.print(f"\n[dim]  💡  {message}[/dim]\n")


def show_error(message: str):
    console.print(f"\n[bold red]  ✗  {message}[/bold red]\n")
