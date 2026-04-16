"""IP lookup module - geolocation, ASN, ISP via FrostedServices GeoIP + ip-api.com."""
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich import box
from utils.api_handler import make_request, safe_json
from utils.logger import get_logger
from utils.formatter import section_header

logger = get_logger("ip_lookup")

FROSTED_GEOIP = "https://frostedservices.xyz/api/geoip/{ip}"


class IPLookup:
    def __init__(self, console: Console):
        self.console = console

    def run(self, ip: str) -> Dict[str, Any]:
        logger.info(f"IP lookup: {ip}")
        result = {
            "ip": ip,
            "frosted_geoip": self._frosted_geoip(ip),
            "ip_api": self._ip_api(ip),
            "rdap": self._rdap(ip),
        }
        result["score"] = self._score(result)
        return result

    def _frosted_geoip(self, ip: str) -> Dict:
        """Query FrostedServices GeoIP API."""
        resp = make_request(
            FROSTED_GEOIP.format(ip=ip),
            params={"json": "1"},
            timeout=10,
        )
        data = safe_json(resp)
        if data:
            return data
        return {"error": "FrostedServices GeoIP request failed"}

    def _ip_api(self, ip: str) -> Dict:
        """Secondary lookup via ip-api.com (free, no key needed)."""
        resp = make_request(
            f"http://ip-api.com/json/{ip}",
            params={
                "fields": "status,message,country,countryCode,region,regionName,"
                          "city,zip,lat,lon,timezone,isp,org,as,query,proxy,hosting"
            },
            timeout=10,
        )
        data = safe_json(resp)
        if data and data.get("status") == "success":
            return {k: v for k, v in data.items() if k != "status"}
        return {"error": "ip-api.com request failed"}

    def _rdap(self, ip: str) -> Dict:
        resp = make_request(f"https://rdap.org/ip/{ip}", timeout=10)
        data = safe_json(resp)
        if data:
            return {
                "name": data.get("name"),
                "type": data.get("type"),
                "handle": data.get("handle"),
                "country": data.get("country"),
            }
        return {}

    def _score(self, data: Dict) -> int:
        score = 0
        ipapi = data.get("ip_api", {})
        if ipapi.get("proxy"):
            score += 40
        if ipapi.get("hosting"):
            score += 20
        if not ipapi.get("country"):
            score += 10
        return min(100, score)

    def display(self, data: Dict):
        section_header(self.console, "IP LOOKUP RESULTS")
        self.console.print(f"[bold white]IP:[/] [cyan]{data['ip']}[/]  [bold white]Risk Score:[/] [yellow]{data['score']}/100[/]\n")

        # FrostedServices GeoIP (primary)
        fg = data.get("frosted_geoip", {})
        if fg and "error" not in fg:
            table = Table(title="GeoIP (FrostedServices)", box=box.ROUNDED, border_style="cyan")
            table.add_column("Field", style="bold white", width=22)
            table.add_column("Value", style="cyan")
            for k, v in fg.items():
                if v is not None and str(v).strip():
                    table.add_row(str(k), str(v))
            self.console.print(table)
        elif "error" in fg:
            self.console.print(f"[yellow]FrostedServices: {fg['error']}[/]")

        # ip-api.com (secondary)
        ipapi = data.get("ip_api", {})
        if ipapi and "error" not in ipapi:
            table = Table(title="Network Info (ip-api.com)", box=box.ROUNDED, border_style="cyan")
            table.add_column("Field", style="bold white", width=22)
            table.add_column("Value", style="cyan")
            fields = [
                ("Country", f"{ipapi.get('country')} ({ipapi.get('countryCode')})"),
                ("Region", ipapi.get("regionName")),
                ("City", ipapi.get("city")),
                ("ZIP", ipapi.get("zip")),
                ("Coordinates", f"{ipapi.get('lat')}, {ipapi.get('lon')}"),
                ("Timezone", ipapi.get("timezone")),
                ("ISP", ipapi.get("isp")),
                ("Organization", ipapi.get("org")),
                ("ASN", ipapi.get("as")),
                ("Proxy/VPN", "[red]YES[/]" if ipapi.get("proxy") else "[green]No[/]"),
                ("Hosting/DC", "[yellow]YES[/]" if ipapi.get("hosting") else "[green]No[/]"),
            ]
            for field, value in fields:
                if value:
                    table.add_row(field, str(value))
            self.console.print(table)

        # RDAP
        rdap = data.get("rdap", {})
        if rdap and rdap.get("name"):
            self.console.print(f"\n[dim]RDAP:[/] name=[cyan]{rdap.get('name')}[/]  handle=[cyan]{rdap.get('handle')}[/]  country=[cyan]{rdap.get('country')}[/]")
