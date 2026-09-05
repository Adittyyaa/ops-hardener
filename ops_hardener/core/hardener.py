import difflib
from pathlib import Path

from rich.syntax import Syntax

# Re-use the single shared console from formatter so all Rich output is
# consistent (width, theme, file handle).
from ops_hardener.ui.formatter import console


def generate_diff(original_content: str, hardened_code: str, file_path: Path) -> None:
    """Print a unified diff between *original_content* and *hardened_code*."""
    original_lines = original_content.splitlines(keepends=True)
    hardened_lines = hardened_code.splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            original_lines,
            hardened_lines,
            fromfile=str(file_path),
            tofile=f"{file_path.name}.hardened",
            n=3,
        )
    )

    if not diff:
        console.print("[bold green]No changes were suggested by the LLM.[/bold green]")
        return

    diff_text = "".join(diff)
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    console.print("\n[bold]Proposed Changes (Diff):[/bold]")
    console.print(syntax)


def apply_fix(file_path: Path, hardened_code: str, *, force: bool = False) -> Path:
    """Write *hardened_code* to ``<file_path>.hardened``.

    Parameters
    ----------
    force:
        When ``False`` (default) and the target file already exists, the user
        is warned and the existing file is left untouched.  Pass ``True`` (via
        the ``--force`` CLI flag) to overwrite silently.

    Returns
    -------
    Path
        The path that was written (or that already existed when not forced).
    """
    new_path = file_path.with_name(f"{file_path.name}.hardened")

    if new_path.exists() and not force:
        console.print(
            f"\n[bold yellow]⚠ Warning:[/bold yellow] {new_path} already exists. "
            "Pass [bold]--force[/bold] to overwrite it.",
        )
        return new_path

    new_path.write_text(hardened_code, encoding="utf-8")
    return new_path
