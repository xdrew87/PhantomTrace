"""Domain lookup module - WHOIS and DNS records."""
import whois
import dns.resolver
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich import box
from utils.api_handler import make_request, safe_json
from utils.logger import get_logger
from utils.formatter import section_header

logger = get_logger("domain_lookup")

DNS_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]


class DomainLookup:
    def __init__(self, console: Console):
        self.console = console

    def run(self, domain: str) -> Dict[str, Any]:
        logger.info(f"Domain lookup: {domain}")
        result = {
            "domain": domain,
            "whois": self._whois(domain),
            "dns": self._dns(domain),
            "http_headers": self._http_headers(domain),
            "rdap": self._rdap(domain),
        }
        return result

    def _whois(self, domain: str) -> Dict:
        try:
            w = whois.whois(domain)
            return {
                "registrar": w.registrar,
                "creation_date": str(w.creation_date) if w.creation_date else None,
                "expiration_date": str(w.expiration_date) if w.expiration_date else None,
                "updated_date": str(w.updated_date) if w.updated_date else None,
                "name_servers": w.name_servers if isinstance(w.name_servers, list) else ([w.name_servers] if w.name_servers else []),
                "status": w.status if isinstance(w.status, list) else ([w.status] if w.status else []),
                "emails": w.emails if isinstance(w.emails, list) else ([w.emails] if w.emails else []),
                "org": w.org,
                "country": w.country,
            }
        except Exception as e:
            logger.warning(f"WHOIS failed for {domain}: {e}")
            return {"error": str(e)}

    def _dns(self, domain: str) -> Dict:
        records = {}
        for rtype in DNS_RECORD_TYPES:
            try:
                answers = dns.resolver.resolve(domain, rtype, lifetime=8)
                records[rtype] = [str(r) for r in answers]
            except dns.resolver.NXDOMAIN:
                records[rtype] = ["NXDOMAIN"]
            except dns.resolver.NoAnswer:
                records[rtype] = []
            except Exception:
                records[rtype] = []
        return records

    def _http_headers(self, domain: str) -> Dict:
        resp = make_request(f"https://{domain}", timeout=10, retries=1)
        if resp is None:
            resp = make_request(f"http://{domain}", timeout=10, retries=1)
        if resp:
            interesting = [
                "server", "x-powered-by", "x-frame-options", "content-security-policy",
                "strict-transport-security", "x-content-type-options", "set-cookie"
            ]
            return {k: v for k, v in resp.headers.items() if k.lower() in interesting}
        return {}

    def _rdap(self, domain: str) -> Dict:
        resp = make_request(f"https://rdap.org/domain/{domain}", timeout=10)
        data = safe_json(resp)
        if data:
            return {
                "handle": data.get("handle"),
                "ldhName": data.get("ldhName"),
                "status": data.get("status", []),
            }
        return {}

    def display(self, data: Dict):
        section_header(self.console, "DOMAIN LOOKUP RESULTS")
        self.console.print(f"[bold white]Domain:[/] [cyan]{data['domain']}[/]\n")

        w = data.get("whois", {})
        if "error" not in w:
            table = Table(title="WHOIS Information", box=box.ROUNDED, border_style="cyan")
            table.add_column("Field", style="bold white", width=22)
            table.add_column("Value", style="cyan")
            fields = [
                ("Registrar", w.get("registrar")),
                ("Created", w.get("creation_date")),
                ("Expires", w.get("expiration_date")),
                ("Updated", w.get("updated_date")),
                ("Org", w.get("org")),
                ("Country", w.get("country")),
                ("Name Servers", ", ".join((w.get("name_servers") or [])[:4])),
                ("Emails", ", ".join((w.get("emails") or [])[:4])),
            ]
            for field, value in fields:
                if value:
                    table.add_row(field, str(value))
            self.console.print(table)
        else:
            self.console.print(f"[yellow]WHOIS: {w['error']}[/]")

        dns_data = data.get("dns", {})
        if dns_data:
            table = Table(title="DNS Records", box=box.ROUNDED, border_style="cyan")
            table.add_column("Type", style="bold yellow", width=8)
            table.add_column("Records", style="cyan")
            for rtype, records in dns_data.items():
                if records:
                    table.add_row(rtype, "\n".join(records[:5]))
            self.console.print(table)

        headers = data.get("http_headers", {})
        if headers:
            self.console.print("\n[bold white]Notable HTTP Headers:[/]")
            for k, v in headers.items():
                self.console.print(f"  [yellow]{k}:[/] [cyan]{v[:80]}[/]")
