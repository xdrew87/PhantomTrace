"""PhantomTrace - Professional OSINT Intelligence Framework"""
import sys
import time
import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "config" / ".env")

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.align import Align
from rich.rule import Rule
from rich import box

from modules.username_lookup import UsernameLookup
from modules.email_intel import EmailIntel
from modules.ip_lookup import IPLookup
from modules.phone_lookup import PhoneLookup
from modules.domain_lookup import DomainLookup
from modules.social_media import SocialMedia
from utils.logger import get_logger
from utils.reporter import Reporter
from utils.formatter import print_disclaimer, section_header, score_color

console = Console()
logger = get_logger("main")

VERSION = "1.0.0"
NUM_MODULES = 6

BANNER = r"""
 ____  _           _ _             _____                    
|  _ \| |__   __ _| | |_ ___  _ _|_   _| __ __ _  ___ ___ 
| |_) | '_ \ / _` | | __/ _ \| '_ \| || '__/ _` |/ __/ _ \
|  __/| | | | (_| | | || (_) | | | | || | | (_| | (_|  __/
|_|   |_| |_|\__,_|_|\__\___/|_| |_|_||_|  \__,_|\___\___|
"""


# ─── Session State ─────────────────────────────────────────────────────────

class SessionState:
    """Tracks live session data for contextual display in the UI."""

    def __init__(self):
        self.target: str = ""
        self.last_scan: str = "None"
        self.last_scan_time: str = ""
        self.scan_count: int = 0
        self.api_status: str = "OK"
        self.mode: str = "Passive OSINT"
        self.modules_loaded: int = NUM_MODULES

    def set_target(self, target: str):
        self.target = target

    def record_scan(self, module: str, target: str):
        self.last_scan = f"{module} → {target}"
        self.last_scan_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.scan_count += 1


# ─── UI Components ─────────────────────────────────────────────────────────

def _build_header(state: SessionState) -> Panel:
    """Header panel: banner + version bar + target context line."""
    banner_text = Text(BANNER, style="bold cyan", justify="center")

    # Version / info strip
    info = Text(justify="center")
    info.append("  v" + VERSION + "  ", style="bold white on grey11")
    info.append("  Open-Source OSINT Intelligence Framework  ", style="dim white")
    info.append("  Authorized Use Only  ", style="bold red on grey11")

    # Target context
    if state.target:
        ctx = Text(justify="center")
        ctx.append("  Target: ", style="dim white")
        ctx.append(state.target, style="bold bright_white")
        if state.last_scan_time:
            ctx.append("   Last Scan: ", style="dim white")
            ctx.append(state.last_scan, style="bold cyan")
            ctx.append(f"  [{state.last_scan_time}]", style="dim")
    else:
        ctx = Text(
            "  No target set — select a module to begin",
            style="dim",
            justify="center",
        )

    content = Text.assemble(banner_text, "\n", info, "\n", ctx)
    return Panel(
        content,
        style="on grey3",
        border_style="cyan",
        box=box.HEAVY,
        padding=(0, 2),
    )


def _build_menu_table() -> Table:
    """Main menu table with fixed column widths and highlighted Full Scan row."""
    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta on grey11",
        show_header=True,
        min_width=72,
        pad_edge=True,
        style="on grey3",
    )
    table.add_column("OPT",         style="bold cyan",  justify="center", width=6,  no_wrap=True)
    table.add_column("MODULE",      style="bold white",                   width=25, no_wrap=True)
    table.add_column("DESCRIPTION", style="dim white",                    min_width=38)

    _SEP = ("───", "─────────────────────────", "──────────────────────────────────────")

    entries = [
        ("1", "Username Lookup",    "Search 50+ platforms for a username"),
        ("2", "Email Intelligence", "Breach checks & domain analysis"),
        ("3", "IP Lookup",          "Geolocation, ASN & ISP data"),
        ("4", "Phone Lookup",       "Carrier, region & line type"),
        ("5", "Domain Lookup",      "WHOIS & DNS record analysis"),
        ("6", "Social Media Scan",  "Public profile discovery"),
        _SEP,
        ("7", "Full Profile Scan",  "⚠  Run ALL modules — confirmation required"),
        _SEP,
        ("8", "View Reports",       "Browse saved scan reports"),
        ("9", "Settings",           "View current configuration"),
        ("0", "Exit",               "Close PhantomTrace session"),
    ]

    for entry in entries:
        opt, module, desc = entry
        if opt.startswith("─"):
            table.add_row(f"[dim]{opt}[/]", f"[dim]{module}[/]", f"[dim]{desc}[/]")
        elif opt == "7":
            # Full scan — highlighted yellow as a warning
            table.add_row(
                f"[bold yellow]{opt}[/]",
                f"[bold yellow]{module}[/]",
                f"[yellow]{desc}[/]",
            )
        else:
            table.add_row(opt, module, desc)

    return table


def _build_status_bar(state: SessionState) -> Panel:
    """Persistent status line at the bottom of the UI."""
    api_color = "bold green" if state.api_status == "OK" else "bold red"

    bar = Text(justify="center")
    bar.append("  STATUS  ", style="bold black on cyan")
    bar.append("   APIs: ",   style="dim white")
    bar.append(state.api_status, style=api_color)
    bar.append("   |   Modules: ", style="dim white")
    bar.append(f"{state.modules_loaded} Loaded", style="bold white")
    bar.append("   |   Mode: ", style="dim white")
    bar.append(state.mode, style="bold cyan")
    if state.scan_count:
        bar.append("   |   Scans This Session: ", style="dim white")
        bar.append(str(state.scan_count), style="bold white")

    return Panel(
        bar,
        style="on grey7",
        border_style="dim cyan",
        box=box.HORIZONTALS,
        padding=(0, 1),
    )


def print_ui(state: SessionState):
    """Render the full menu screen: header + menu table + status bar."""
    console.clear()
    console.print(_build_header(state))
    console.print(Align.center(_build_menu_table()))
    console.print(_build_status_bar(state))
    console.print()


# ─── Helpers ───────────────────────────────────────────────────────────────

def get_target(input_type: str, state: SessionState) -> str:
    labels = {
        "username": "Enter target username",
        "email":    "Enter target email address",
        "ip":       "Enter target IP address",
        "phone":    "Enter phone number (with country code, e.g. +14155552671)",
        "domain":   "Enter domain name (e.g. example.com)",
        "any":      "Enter target (username / email / IP / phone / domain)",
    }
    value = Prompt.ask(
        f"\n[bold cyan]{labels.get(input_type, labels['any'])}[/]"
    ).strip()
    if value:
        state.set_target(value)
    return value


def run_module(module_name: str, target: str, reporter: Reporter, state: SessionState):
    module_map = {
        "username": UsernameLookup,
        "email":    EmailIntel,
        "ip":       IPLookup,
        "phone":    PhoneLookup,
        "domain":   DomainLookup,
        "social":   SocialMedia,
    }
    if module_name not in module_map:
        console.print("[red]Unknown module.[/]")
        return

    ModClass = module_map[module_name]
    mod = ModClass(console)

    with console.status(
        f"[bold cyan]Running {ModClass.__name__} on [white]{target}[/]...[/]",
        spinner="dots",
    ):
        results = mod.run(target)

    mod.display(results)
    state.record_scan(ModClass.__name__, target)
    reporter.add_result(module_name, target, results)

    if Confirm.ask("\n[cyan]Export this result?[/]", default=False):
        fmt = Prompt.ask("[cyan]Format[/]", choices=["json", "html", "both"], default="json")
        if fmt in ("json", "both"):
            path = reporter.export_json(module_name, target, results)
            console.print(f"[bold green]✓ JSON saved:[/] {path}")
        if fmt in ("html", "both"):
            path = reporter.export_html(module_name, target, results)
            console.print(f"[bold green]✓ HTML saved:[/] {path}")


def full_profile_scan(reporter: Reporter, state: SessionState):
    target = get_target("any", state)
    if not target:
        return

    # Warning panel before confirmation
    console.print()
    console.print(
        Panel(
            "[bold yellow]⚠  FULL PROFILE SCAN[/]\n\n"
            "This will run [bold white]ALL 6 modules[/] on the target.\n"
            "Ensure you are [bold red]authorized[/] to investigate this target.",
            style="on grey3",
            border_style="yellow",
            box=box.HEAVY,
            title="[bold yellow]  WARNING  [/]",
            title_align="center",
        )
    )

    if not Confirm.ask(
        f"[yellow]Confirm full scan on[/] [bold white]{target}[/]?",
        default=False,
    ):
        console.print("[dim]Full scan cancelled.[/]")
        return

    console.print(
        f"\n[bold cyan]Starting full profile scan on:[/] [bold white]{target}[/]\n"
    )

    for module_name in ["username", "email", "ip", "phone", "domain", "social"]:
        console.print(Rule(f"[dim cyan]{module_name.upper()} MODULE[/]", style="dim cyan"))
        try:
            run_module(module_name, target, reporter, state)
        except Exception as e:
            logger.error(f"Module {module_name} failed: {e}")
            console.print(f"[red]✗ {module_name} failed: {e}[/]")

    path = reporter.export_combined_html(target)
    console.print(f"\n[bold green]✓ Combined report saved:[/] {path}")


def view_reports():
    reports_dir = Path(__file__).parent / "reports"
    files = [
        f for f in reports_dir.iterdir()
        if f.is_file() and f.suffix in (".json", ".html")
    ]
    if not files:
        console.print("[yellow]No reports found in reports/ directory.[/]")
        return

    table = Table(
        title="[bold cyan]Saved Reports[/]",
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        style="on grey3",
        header_style="bold magenta on grey11",
    )
    table.add_column("#",        style="bold cyan",  justify="center", width=4)
    table.add_column("Filename", style="bold white")
    table.add_column("Type",     style="cyan",       justify="center", width=6)
    table.add_column("Size",     style="dim",        justify="right",  width=10)
    table.add_column("Modified", style="dim",                          width=17)

    for i, f in enumerate(
        sorted(files, key=lambda x: x.stat().st_mtime, reverse=True), 1
    ):
        stat = f.stat()
        size = f"{stat.st_size / 1024:.1f} KB"
        mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        table.add_row(str(i), f.name, f.suffix.lstrip(".").upper(), size, mod_time)

    console.print(Align.center(table))


def show_settings():
    import json
    config_path = Path(__file__).parent / "config" / "settings.json"
    with open(config_path, encoding="utf-8") as f:
        settings = json.load(f)

    table = Table(
        title="[bold cyan]Current Configuration[/]",
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        style="on grey3",
        header_style="bold magenta on grey11",
    )
    table.add_column("Setting", style="bold white", width=35)
    table.add_column("Value",   style="bold yellow")

    def flatten(d, prefix=""):
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                flatten(v, key)
            else:
                table.add_row(key, str(v))

    flatten(settings)
    console.print(Align.center(table))
    console.print(
        "\n[dim]Edit [bold white]config/settings.json[/] or "
        "[bold white]config/.env[/] to change settings.[/]"
    )


# ─── Entry Point ───────────────────────────────────────────────────────────

def main():
    state = SessionState()

    # Splash + disclaimer before entering the loop
    console.clear()
    console.print(Text(BANNER, style="bold cyan"), justify="center")
    print_disclaimer(console)

    if not Confirm.ask(
        "[yellow]I confirm I will only use PhantomTrace on targets I am authorized to investigate[/]",
        default=False,
    ):
        console.print("\n[red]Authorization not confirmed. Exiting PhantomTrace.[/]\n")
        sys.exit(0)

    reporter = Reporter()
    logger.info("PhantomTrace session started")

    menu_actions = {
        "1": lambda: run_module("username", get_target("username", state), reporter, state),
        "2": lambda: run_module("email",    get_target("email",    state), reporter, state),
        "3": lambda: run_module("ip",       get_target("ip",       state), reporter, state),
        "4": lambda: run_module("phone",    get_target("phone",    state), reporter, state),
        "5": lambda: run_module("domain",   get_target("domain",   state), reporter, state),
        "6": lambda: run_module("social",   get_target("username", state), reporter, state),
        "7": lambda: full_profile_scan(reporter, state),
        "8": view_reports,
        "9": show_settings,
    }

    while True:
        print_ui(state)
        choice = Prompt.ask(
            "[bold cyan]›[/] [bold white]Select option[/]",
            default="0",
        )

        if choice == "0":
            console.print("\n[bold cyan]Session closed. Stay ethical.[/]\n")
            logger.info("PhantomTrace session ended")
            break

        if choice in menu_actions:
            try:
                menu_actions[choice]()
            except KeyboardInterrupt:
                console.print("\n[yellow]Module interrupted.[/]")
            except Exception as e:
                logger.error(f"Unhandled error in option {choice}: {e}", exc_info=True)
                console.print(f"\n[red]Error: {e}[/]")

            console.print()
            Prompt.ask("[dim]Press Enter to return to menu[/]", default="")
        else:
            console.print("[red]Invalid option. Please select 0–9.[/]")
            time.sleep(1)


if __name__ == "__main__":
    main()
