from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ops_hardener.schemas.audit import AuditReport

console = Console()

def get_grade_and_color(score: int) -> tuple[str, str]:
    if score >= 90:
        return "A", "green"
    elif score >= 80:
        return "B", "blue"
    elif score >= 70:
        return "C", "yellow"
    elif score >= 60:
        return "D", "orange3"
    return "F", "red"

def print_audit_report(report: AuditReport) -> None:
    # Print the score banner
    grade, color = get_grade_and_color(report.score)
    score_text = f"[bold {color}]Security Grade: {grade} ({report.score}/100)[/bold {color}]"
    console.print(Panel(score_text, expand=False, title="Audit Result", border_style=color))

    if not report.findings:
        console.print("\n[bold green]✅ No vulnerabilities or anti-patterns found![/bold green]")
        return

    # Print the findings table
    table = Table(title="Security Findings & Recommendations", show_header=True, header_style="bold magenta")
    table.add_column("Severity", justify="center")
    table.add_column("Rule ID", justify="left")
    table.add_column("Issue")
    table.add_column("Line")
    table.add_column("Recommendation")

    for finding in report.findings:
        sev_color = "red" if finding.severity == "HIGH" else "yellow" if finding.severity == "MEDIUM" else "cyan"
        line_num = str(finding.line_number) if finding.line_number else "N/A"
        
        table.add_row(
            f"[{sev_color}]{finding.severity}[/{sev_color}]",
            finding.rule_id,
            finding.issue,
            line_num,
            finding.recommendation
        )

    console.print("\n")
    console.print(table)
