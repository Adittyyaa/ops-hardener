import typer
from rich.console import Console
from ops_hardener.core.parser import parse_file
from ops_hardener.core.analyzer import analyze_file
from ops_hardener.core.hardener import generate_diff, apply_fix
from ops_hardener.ui.formatter import print_audit_report
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

app = typer.Typer(help="ops-hardener: Security scanner for Dockerfiles and K8s manifests")
console = Console()

__version__ = "0.1.0"

def version_callback(value: bool):
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
    )
):
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
        help="Path to the Dockerfile or Kubernetes YAML manifest to scan."
    ),
    model: str = typer.Option("gpt-4o", help="LLM model to use (e.g., gpt-4o, ollama/llama3)"),
    show_diff: bool = typer.Option(False, "--diff", help="Display a side-by-side terminal diff before writing changes."),
    fix: bool = typer.Option(False, "--fix", help="Automatically write the hardened output to a new file (e.g., Dockerfile.hardened).")
):
    """
    Scan a Dockerfile or Kubernetes YAML manifest.
    """
    console.print(f"Scanning [bold cyan]{file_path}[/bold cyan]...", style="bold")
    try:
        file_metadata = parse_file(file_path)
        console.print(f"File Type Detected: [bold green]{file_metadata['file_type']}[/bold green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Analyzing with model [bold yellow]{model}[/bold yellow]...", total=None)
            report = analyze_file(file_metadata["content"], file_metadata["file_type"], model=model)
        
        print_audit_report(report)
            
        if show_diff:
            generate_diff(file_metadata["content"], report.hardened_code, file_path)
            
        if fix:
            new_file_path = apply_fix(file_path, report.hardened_code)
            console.print(f"\n[bold green]Success![/bold green] Hardened file saved to: {new_file_path}")
            
    except Exception as e:
        console.print(f"Error: {e}", style="bold red")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
