"""Username lookup module - cross-platform search across 50+ sites."""
import concurrent.futures
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich import box
from utils.api_handler import make_request
from utils.logger import get_logger
from utils.formatter import section_header

logger = get_logger("username_lookup")

# (display_name, url_template, expected_status_code, error_string_in_body)
PLATFORMS = [
    ("GitHub", "https://github.com/{}", 200, None),
    ("GitLab", "https://gitlab.com/{}", 200, None),
    ("Twitter/X", "https://twitter.com/{}", 200, "This account doesn't exist"),
    ("Instagram", "https://www.instagram.com/{}/", 200, "Sorry, this page"),
    ("Reddit", "https://www.reddit.com/user/{}/about.json", 200, None),
    ("TikTok", "https://www.tiktok.com/@{}", 200, "Couldn't find this account"),
    ("Pinterest", "https://www.pinterest.com/{}/", 200, None),
    ("Twitch", "https://www.twitch.tv/{}", 200, None),
    ("YouTube", "https://www.youtube.com/@{}", 200, None),
    ("LinkedIn", "https://www.linkedin.com/in/{}", 200, None),
    ("Tumblr", "https://{}.tumblr.com", 200, None),
    ("Medium", "https://medium.com/@{}", 200, None),
    ("Dev.to", "https://dev.to/{}", 200, None),
    ("Hashnode", "https://hashnode.com/@{}", 200, None),
    ("Steam", "https://steamcommunity.com/id/{}", 200, "The specified profile could not be found"),
    ("Pastebin", "https://pastebin.com/u/{}", 200, None),
    ("Replit", "https://replit.com/@{}", 200, None),
    ("HackerNews", "https://news.ycombinator.com/user?id={}", 200, "No such user"),
    ("ProductHunt", "https://www.producthunt.com/@{}", 200, None),
    ("Keybase", "https://keybase.io/{}", 200, None),
    ("Gravatar", "https://www.gravatar.com/{}", 200, None),
    ("About.me", "https://about.me/{}", 200, None),
    ("Flickr", "https://www.flickr.com/people/{}", 200, None),
    ("VK", "https://vk.com/{}", 200, None),
    ("Spotify", "https://open.spotify.com/user/{}", 200, None),
    ("SoundCloud", "https://soundcloud.com/{}", 200, None),
    ("Bandcamp", "https://{}.bandcamp.com", 200, None),
    ("Behance", "https://www.behance.net/{}", 200, None),
    ("Dribbble", "https://dribbble.com/{}", 200, None),
    ("Deviantart", "https://www.deviantart.com/{}", 200, None),
    ("Fiverr", "https://www.fiverr.com/{}", 200, None),
    ("Freelancer", "https://www.freelancer.com/u/{}", 200, None),
    ("Kaggle", "https://www.kaggle.com/{}", 200, None),
    ("HuggingFace", "https://huggingface.co/{}", 200, None),
    ("NPM", "https://www.npmjs.com/~{}", 200, None),
    ("PyPI", "https://pypi.org/user/{}/", 200, None),
    ("DockerHub", "https://hub.docker.com/u/{}", 200, None),
    ("Bitbucket", "https://bitbucket.org/{}/", 200, None),
    ("Codepen", "https://codepen.io/{}", 200, None),
    ("Leetcode", "https://leetcode.com/{}", 200, None),
    ("HackerRank", "https://www.hackerrank.com/{}", 200, None),
    ("Codeforces", "https://codeforces.com/profile/{}", 200, None),
    ("Chess.com", "https://www.chess.com/member/{}", 200, None),
    ("Roblox", "https://www.roblox.com/user.aspx?username={}", 200, None),
    ("Minecraft", "https://namemc.com/profile/{}", 200, None),
    ("Poshmark", "https://poshmark.com/closet/{}", 200, None),
    ("Etsy", "https://www.etsy.com/shop/{}", 200, None),
]


def _check_platform(username: str, name: str, url_tmpl: str, expected_status: int, error_text: str, timeout: int):
    url = url_tmpl.format(username) if "{}" in url_tmpl else url_tmpl
    try:
        resp = make_request(url, timeout=timeout, retries=1)
        if resp is None:
            return {"platform": name, "url": url, "status": "Error", "found": False}
        if resp.status_code == expected_status:
            if error_text and error_text.lower() in resp.text.lower():
                found = False
            else:
                found = True
        elif resp.status_code == 404:
            found = False
        else:
            found = None
        return {"platform": name, "url": url, "status": resp.status_code, "found": found}
    except Exception as e:
        logger.debug(f"Error checking {name}: {e}")
        return {"platform": name, "url": url, "status": "Error", "found": False}


class UsernameLookup:
    def __init__(self, console: Console):
        self.console = console

    def run(self, username: str) -> Dict[str, Any]:
        logger.info(f"Username lookup: {username}")
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {
                executor.submit(_check_platform, username, name, url, status, err, 10): name
                for name, url, status, err in PLATFORMS
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Future error: {e}")

        found = [r for r in results if r["found"] is True]
        not_found = [r for r in results if r["found"] is False]
        uncertain = [r for r in results if r["found"] is None]
        score = min(100, len(found) * 4)

        return {
            "username": username,
            "total_checked": len(PLATFORMS),
            "found_count": len(found),
            "score": score,
            "found": found,
            "not_found": not_found,
            "uncertain": uncertain,
        }

    def display(self, data: Dict):
        section_header(self.console, "USERNAME LOOKUP RESULTS")
        self.console.print(
            f"[bold white]Username:[/] [cyan]{data['username']}[/]  "
            f"[bold white]Found on:[/] [green]{data['found_count']}[/]/{data['total_checked']} platforms  "
            f"[bold white]Profile Score:[/] [yellow]{data['score']}/100[/]\n"
        )

        if data["found"]:
            table = Table(title="Accounts Found", box=box.ROUNDED, border_style="green", show_lines=False)
            table.add_column("Platform", style="bold white", width=20)
            table.add_column("URL", style="cyan")
            for r in sorted(data["found"], key=lambda x: x["platform"]):
                table.add_row(r["platform"], r["url"])
            self.console.print(table)
        else:
            self.console.print("[yellow]No accounts found.[/]")
