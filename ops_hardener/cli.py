import json
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

import typer
from dotenv import load_dotenv
from pydantic import ValidationError
from rich.progress import Progress, SpinnerColumn, TextColumn

from ops_hardener.core.parser import parse_file
from ops_hardener.core.analyzer import analyze_file
from ops_hardener.core.hardener import generate_diff, apply_fix
from ops_hardener.ui.formatter import console, print_audit_report

# Load environment variables at the entry point
load_dotenv()

# Read the version from package metadata
try:
    __version__ = version("ops-hardener")
except PackageNotFoundError:
    __version__ = "dev"

app = typer.Typer(help="ops-hardener: Security scanner for Dockerfiles and K8s manifests")


def version_callback(value: bool) -> None:
    if value:
        console.print(f"ops-hardener version: {__version__}", style="bold green")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the application's version and exit.",
    ),
) -> None:
    pass


@app.command()
def scan(
    file_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Path to the Dockerfile or Kubernetes YAML manifest to scan.",
    ),
    model: str = typer.Option(
        "gpt-4o",
        help="LLM model to use (e.g., gpt-4o, groq/llama3-70b-8192, ollama/llama3).",
    ),
    show_diff: bool = typer.Option(
        False, "--diff", help="Display a unified diff of the hardened changes."
    ),
    fix: bool = typer.Option(
        False, "--fix", help="Write the hardened output to <file>.hardened."
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite an existing <file>.hardened without prompting.",
    ),
) -> None:
    """Scan a Dockerfile or Kubernetes YAML manifest for security issues."""
    console.print(f"Scanning [bold cyan]{file_path}[/bold cyan]...", style="bold")

    try:
        file_metadata = parse_file(file_path)
    except FileNotFoundError as e:
        console.print(f"[bold red]File not found:[/bold red] {e}")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[bold red]Parse error:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print(
        f"File type detected: [bold green]{file_metadata['file_type']}[/bold green]"
    )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(
                description=f"Analyzing with [bold yellow]{model}[/bold yellow]...",
                total=None,
            )
            report = analyze_file(
                file_metadata["content"], file_metadata["file_type"], model=model
            )
    except RuntimeError as e:
        # Network / auth / API-level failure
        console.print(f"[bold red]LLM error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except (ValueError, ValidationError) as e:
        # Bad JSON or schema mismatch in the model response
        console.print(f"[bold red]Response parsing error:[/bold red] {e}")
        raise typer.Exit(code=1)

    print_audit_report(report)

    if report.hardened_code is None:
        if show_diff or fix:
            console.print(
                "\n[bold yellow]⚠ Warning:[/bold yellow] The LLM did not return "
                "hardened code, so --diff / --fix have been skipped."
            )
        return

    if show_diff:
        generate_diff(file_metadata["content"], report.hardened_code, file_path)

    if fix:
        new_file_path = apply_fix(file_path, report.hardened_code, force=force)
        if new_file_path:
            console.print(
                f"\n[bold green]✔ Hardened file saved to:[/bold green] {new_file_path}"
            )


if __name__ == "__main__":
    app()
