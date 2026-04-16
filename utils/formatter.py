"""Rich formatting helpers for PhantomTrace."""
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box


DISCLAIMER = """
PhantomTrace is designed exclusively for LEGAL and AUTHORIZED intelligence gathering.

  - Only investigate targets you have explicit permission to research.
  - All data collected is sourced from publicly available information.
  - Misuse of this tool may violate laws in your jurisdiction.
  - The authors accept NO liability for misuse or illegal activity.

By continuing, you accept full legal responsibility for your actions.
"""


def print_disclaimer(console: Console):
    console.print(
        Panel(
            Text(DISCLAIMER.strip(), style="yellow", justify="center"),
            title="[bold red]  LEGAL DISCLAIMER  [/]",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 4),
        )
    )
    console.print()


def section_header(console: Console, title: str):
    console.print(f"\n[bold cyan]{'─' * 20} {title} {'─' * 20}[/]\n")


def result_not_found(console: Console, message: str = "No results found."):
    console.print(f"[yellow]  {message}[/]")


def success(console: Console, message: str):
    console.print(f"[bold green]  {message}[/]")


def error(console: Console, message: str):
    console.print(f"[bold red]  {message}[/]")


def score_color(score: int) -> str:
    if score >= 80:
        return "bold red"
    elif score >= 50:
        return "bold yellow"
    else:
        return "bold green"
