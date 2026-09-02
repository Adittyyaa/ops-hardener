import typer
from rich.console import Console
from ops_hardener.core.parser import parse_file
from ops_hardener.core.analyzer import analyze_file
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
    model: str = typer.Option("gpt-4o", help="LLM model to use (e.g., gpt-4o, ollama/llama3)")
):
    """
    Scan a Dockerfile or Kubernetes YAML manifest.
    """
    console.print(f"Scanning [bold cyan]{file_path}[/bold cyan]...", style="bold")
    try:
        file_metadata = parse_file(file_path)
        console.print(f"File Type Detected: [bold green]{file_metadata['file_type']}[/bold green]")
        
        console.print(f"Analyzing with model [bold yellow]{model}[/bold yellow]...", style="bold")
        report = analyze_file(file_metadata["content"], file_metadata["file_type"], model=model)
        
        console.print(f"\n[bold]Score:[ /bold] {report.score}/100")
        console.print(f"[bold]Findings:[ /bold] {len(report.findings)}")
        for finding in report.findings:
            color = "red" if finding.severity == "HIGH" else "yellow" if finding.severity == "MEDIUM" else "blue"
            console.print(f"- [[{color}]{finding.severity}[/{color}]] {finding.issue} (Line {finding.line_number})")
            
    except Exception as e:
        console.print(f"Error: {e}", style="bold red")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
