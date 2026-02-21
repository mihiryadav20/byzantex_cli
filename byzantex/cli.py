import io
import sys
import time
from pathlib import Path
from typing import Optional

import typer

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from byzantex.classifier import Classifier
from byzantex.parser.log_parser import LogParser
from byzantex.ui import (
    console,
    show_banner,
    show_error,
    show_failure,
    show_file_selector,
    show_header,
    show_spinner,
    show_tip,
)

app = typer.Typer(
    help="⚡ Byzantex - Regression Triage in 30 Seconds",
    add_completion=False,
    invoke_without_command=True,
)

TESTS_DIR = Path(__file__).parent.parent / "tests"


@app.callback()
def default(ctx: typer.Context):
    """Run analyze when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        analyze(log_file=None)


@app.command()
def analyze(
    log_file: Optional[Path] = typer.Argument(
        None,
        help="Path to simulation log file. If omitted, opens interactive selector from tests/.",
    ),
):
    """Analyze a simulation log and identify failures."""
    show_banner()

    if log_file is None:
        log_files = sorted(TESTS_DIR.glob("*.log"))
        if not log_files:
            show_error(f"No .log files found in {TESTS_DIR}")
            raise typer.Exit(1)
        log_file = show_file_selector(log_files)
        console.print()
    elif not log_file.exists():
        show_error(f"File not found: {log_file}")
        raise typer.Exit(1)

    start_time = time.time()

    show_spinner("Reading log file...")
    log_content = log_file.read_text(errors='ignore')

    show_spinner("Parsing failures...")
    parser = LogParser(log_content)
    failures = parser.parse()
    detected_ip = parser.detect_ip() or "unknown"

    show_spinner("Classifying failures...")
    results = []
    for failure in failures:
        category, reasoning = Classifier.classify(
            failure.get('file_path', ''),
            failure.get('message', ''),
        )
        results.append({'failure': failure, 'category': category, 'reasoning': reasoning})

    elapsed = time.time() - start_time
    show_header(len(results), elapsed, detected_ip)

    if not results:
        console.print("[green]  No failures found in log.[/green]")
    else:
        for i, result in enumerate(results, 1):
            show_failure(i, result['failure'], result['category'], result['reasoning'])

    show_tip("Run again: byzantex analyze <log_file>")


@app.command()
def version():
    """Show version."""
    console.print("[bold]Byzantex[/bold] v0.1.0")
