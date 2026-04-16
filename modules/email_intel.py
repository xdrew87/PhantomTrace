"""Email intelligence module - breach checks, domain analysis, MX records."""
import os
import dns.resolver
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich import box
from utils.api_handler import make_request, safe_json
from utils.logger import get_logger
from utils.formatter import section_header

logger = get_logger("email_intel")


class EmailIntel:
    def __init__(self, console: Console):
        self.console = console
        self.hibp_key = os.getenv("HIBP_API_KEY", "")
        self.hunter_key = os.getenv("HUNTER_API_KEY", "")

    def run(self, email: str) -> Dict[str, Any]:
        logger.info(f"Email intel: {email}")
        domain = email.split("@")[-1] if "@" in email else ""

        result = {
            "email": email,
            "domain": domain,
            "breaches": self._check_hibp(email),
            "domain_info": self._domain_info(domain) if domain else {},
            "mx_records": self._mx_lookup(domain) if domain else [],
            "hunter_info": self._hunter_info(email) if self.hunter_key else {"note": "No Hunter.io API key configured"},
            "disposable": self._is_disposable(domain),
        }
        result["score"] = self._score(result)
        return result

    def _check_hibp(self, email: str) -> Dict:
        if not self.hibp_key:
            return {"error": "No HIBP API key configured — add HIBP_API_KEY to config/.env", "breaches": []}
        resp = make_request(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            headers={"hibp-api-key": self.hibp_key, "User-Agent": "PhantomTrace-OSINT"},
            params={"truncateResponse": "false"},
            timeout=10,
        )
        if resp is None:
            return {"breaches": [], "error": "Request failed"}
        if resp.status_code == 404:
            return {"breaches": [], "found": False}
        if resp.status_code == 200:
            data = safe_json(resp) or []
            return {
                "found": True,
                "count": len(data),
                "breaches": [
                    {"name": b.get("Name"), "date": b.get("BreachDate"), "data_classes": b.get("DataClasses", [])}
                    for b in data
                ],
            }
        return {"breaches": [], "status_code": resp.status_code}

    def _domain_info(self, domain: str) -> Dict:
        resp = make_request(f"https://dns.google/resolve?name={domain}&type=A", timeout=8)
        data = safe_json(resp) or {}
        return {
            "a_records": [a.get("data") for a in data.get("Answer", []) if a.get("type") == 1],
        }

    def _mx_lookup(self, domain: str) -> list:
        try:
            records = dns.resolver.resolve(domain, "MX")
            return [str(r.exchange).rstrip(".") for r in records]
        except Exception:
            return []

    def _hunter_info(self, email: str) -> Dict:
        resp = make_request(
            "https://api.hunter.io/v2/email-verifier",
            params={"email": email, "api_key": self.hunter_key},
            timeout=10,
        )
        data = safe_json(resp)
        if data and "data" in data:
            d = data["data"]
            return {
                "status": d.get("status"),
                "score": d.get("score"),
                "disposable": d.get("disposable"),
                "webmail": d.get("webmail"),
            }
        return {"error": "Hunter.io request failed"}

    def _is_disposable(self, domain: str) -> bool:
        disposable_domains = {
            "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
            "throwam.com", "yopmail.com", "trashmail.com", "sharklasers.com",
            "guerrillamailblock.com", "grr.la", "guerrillamail.info", "spam4.me",
            "maildrop.cc", "dispostable.com", "mailnull.com",
        }
        return domain.lower() in disposable_domains

    def _score(self, data: Dict) -> int:
        score = 0
        breaches = data.get("breaches", {})
        if isinstance(breaches, dict):
            count = breaches.get("count", 0)
            score += min(60, count * 10)
        if data.get("mx_records"):
            score += 20
        if data.get("disposable"):
            score -= 10
        return max(0, min(100, score))

    def display(self, data: Dict):
        section_header(self.console, "EMAIL INTELLIGENCE")
        self.console.print(
            f"[bold white]Email:[/] [cyan]{data['email']}[/]  "
            f"[bold white]Domain:[/] [cyan]{data['domain']}[/]  "
            f"[bold white]Risk Score:[/] [yellow]{data['score']}/100[/]\n"
        )

        breaches = data.get("breaches", {})
        if isinstance(breaches, dict) and breaches.get("found"):
            table = Table(
                title=f"[red]Found in {breaches['count']} Breaches[/]",
                box=box.ROUNDED, border_style="red"
            )
            table.add_column("Breach", style="bold white")
            table.add_column("Date", style="yellow")
            table.add_column("Data Exposed", style="red")
            for b in breaches.get("breaches", []):
                table.add_row(b["name"], b["date"] or "-", ", ".join(b["data_classes"][:4]))
            self.console.print(table)
        elif isinstance(breaches, dict) and "error" in breaches:
            self.console.print(f"[yellow]HIBP: {breaches['error']}[/]")
        else:
            self.console.print("[green]No known breaches found[/]")

        mx = data.get("mx_records", [])
        if mx:
            self.console.print(f"\n[bold white]MX Records:[/] {', '.join(mx)}")

        if data.get("disposable"):
            self.console.print("[red]Disposable/temporary email domain detected[/]")

        hunter = data.get("hunter_info", {})
        if hunter and "error" not in hunter and "note" not in hunter:
            self.console.print(
                f"\n[bold white]Hunter.io:[/] Status=[cyan]{hunter.get('status')}[/]  "
                f"Score=[yellow]{hunter.get('score')}[/]  Webmail=[cyan]{hunter.get('webmail')}[/]"
            )
