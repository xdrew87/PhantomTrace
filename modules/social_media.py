"""Social media footprint module - public profile discovery across major platforms."""
import concurrent.futures
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich import box
from utils.api_handler import make_request
from utils.logger import get_logger
from utils.formatter import section_header

logger = get_logger("social_media")

SOCIAL_PLATFORMS = [
    ("Twitter/X", "https://twitter.com/{}", "This account doesn't exist"),
    ("Instagram", "https://www.instagram.com/{}/", "Sorry, this page"),
    ("Facebook", "https://www.facebook.com/{}", None),
    ("LinkedIn", "https://www.linkedin.com/in/{}", None),
    ("TikTok", "https://www.tiktok.com/@{}", "Couldn't find this account"),
    ("YouTube", "https://www.youtube.com/@{}", None),
    ("Reddit", "https://www.reddit.com/user/{}/about.json", None),
    ("Pinterest", "https://www.pinterest.com/{}/", None),
    ("Snapchat", "https://www.snapchat.com/add/{}", "Sorry, we couldn't find that username"),
    ("Telegram", "https://t.me/{}", "If you have Telegram"),
    ("Twitch", "https://www.twitch.tv/{}", None),
    ("Mastodon", "https://mastodon.social/@{}", None),
    ("BeReal", "https://bere.al/{}", None),
    ("Threads", "https://www.threads.net/@{}", None),
    ("Bluesky", "https://bsky.app/profile/{}", None),
]


def _check(username: str, name: str, url_tmpl: str, error_text: str, timeout: int):
    url = url_tmpl.format(username)
    try:
        resp = make_request(url, timeout=timeout, retries=1)
        if resp is None:
            return {"platform": name, "url": url, "found": False, "status": "Error"}
        found = resp.status_code == 200
        if found and error_text and error_text.lower() in resp.text.lower():
            found = False
        return {"platform": name, "url": url, "found": found, "status": resp.status_code}
    except Exception as e:
        logger.debug(f"Error checking {name}: {e}")
        return {"platform": name, "url": url, "found": False, "status": "Error"}


class SocialMedia:
    def __init__(self, console: Console):
        self.console = console

    def run(self, username: str) -> Dict[str, Any]:
        logger.info(f"Social media scan: {username}")
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = {
                executor.submit(_check, username, name, url, err, 10): name
                for name, url, err in SOCIAL_PLATFORMS
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Social future error: {e}")

        found = [r for r in results if r["found"]]
        score = min(100, len(found) * 8)
        return {
            "username": username,
            "total_checked": len(SOCIAL_PLATFORMS),
            "found_count": len(found),
            "score": score,
            "profiles": sorted(results, key=lambda x: (not x["found"], x["platform"])),
        }

    def display(self, data: Dict):
        section_header(self.console, "SOCIAL MEDIA FOOTPRINT")
        self.console.print(
            f"[bold white]Username:[/] [cyan]{data['username']}[/]  "
            f"[bold white]Found:[/] [green]{data['found_count']}[/]/{data['total_checked']}  "
            f"[bold white]Footprint Score:[/] [yellow]{data['score']}/100[/]\n"
        )

        table = Table(title="Social Media Profiles", box=box.ROUNDED, border_style="cyan", show_lines=False)
        table.add_column("Platform", style="bold white", width=20)
        table.add_column("Status", width=12)
        table.add_column("URL", style="dim")

        for r in data["profiles"]:
            status = "[bold green]FOUND[/]" if r["found"] else "[dim red]Not Found[/]"
            table.add_row(r["platform"], status, r["url"] if r["found"] else "-")
        self.console.print(table)
