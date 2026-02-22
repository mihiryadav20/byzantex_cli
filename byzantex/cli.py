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
from byzantex.parser.rtl_indexer import RTLIndexer
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
DEFAULT_OPENTITAN = Path(r"C:\Users\mihir\Codes and docs\opentitan")


@app.callback()
def default(ctx: typer.Context):
    """Run analyze when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        analyze(log_file=None, opentitan=DEFAULT_OPENTITAN)


@app.command()
def analyze(
    log_file: Optional[Path] = typer.Argument(
        None,
        help="Path to simulation log file. If omitted, opens interactive selector from tests/.",
    ),
    opentitan: Path = typer.Option(
        DEFAULT_OPENTITAN,
        "--opentitan", "-o",
        help="Path to OpenTitan repository root.",
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

    # Index OpenTitan files for path resolution
    indexer = RTLIndexer(str(opentitan))
    if opentitan.exists():
        show_spinner(f"Indexing OpenTitan files for '{detected_ip}'...")
        indexer.index_ip(detected_ip if detected_ip != "unknown" else None)

    show_spinner("Classifying failures...")
    results = []
    for failure in failures:
        file_name = failure.get('file_path', '')
        ip = detected_ip if detected_ip != "unknown" else None
        resolved_path = indexer.resolve(file_name, ip_name=ip)
        file_type = indexer.get_file_type(file_name, ip_name=ip)

        category, reasoning = Classifier.classify(
            resolved_path or file_name, failure.get('message', '')
        )
        results.append({
            'failure': failure,
            'category': category,
            'reasoning': reasoning,
            'resolved_path': resolved_path,
            'file_type': file_type,
        })

    elapsed = time.time() - start_time
    show_header(len(results), elapsed, detected_ip)

    if not results:
        console.print("[green]  No failures found in log.[/green]")
    else:
        for i, result in enumerate(results, 1):
            show_failure(
                i,
                result['failure'],
                result['category'],
                result['reasoning'],
                resolved_path=result['resolved_path'],
                file_type=result['file_type'],
            )

    show_tip("Run again: byzantex analyze <log_file>")


@app.command()
def version():
    """Show version."""
    console.print("[bold]Byzantex[/bold] v0.1.0")
