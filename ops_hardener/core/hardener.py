import difflib
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax

console = Console()

def generate_diff(original_content: str, hardened_code: str, file_path: Path) -> None:
    """
    Generates and prints a unified diff between the original content and the hardened code.
    """
    original_lines = original_content.splitlines(keepends=True)
    hardened_lines = hardened_code.splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(
        original_lines,
        hardened_lines,
        fromfile=str(file_path),
        tofile=f"{file_path.name}.hardened",
        n=3
    ))
    
    if not diff:
        console.print("[bold green]No changes were suggested by the LLM.[/bold green]")
        return
        
    diff_text = "".join(diff)
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    
    console.print("\n[bold]Proposed Changes (Diff):[/bold]")
    console.print(syntax)

def apply_fix(file_path: Path, hardened_code: str) -> Path:
    """
    Writes the hardened code to a new file.
    """
    new_path = file_path.with_name(f"{file_path.name}.hardened")
    new_path.write_text(hardened_code, encoding="utf-8")
    return new_path
