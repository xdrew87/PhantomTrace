"""Phone number lookup module - carrier, region, line type."""
import os
import phonenumbers
from phonenumbers import geocoder, carrier, timezone as pn_timezone
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich import box
from utils.api_handler import make_request, safe_json
from utils.logger import get_logger
from utils.formatter import section_header

logger = get_logger("phone_lookup")


class PhoneLookup:
    def __init__(self, console: Console):
        self.console = console
        self.numverify_key = os.getenv("NUMVERIFY_API_KEY", "")

    def run(self, phone: str) -> Dict[str, Any]:
        logger.info(f"Phone lookup: {phone}")
        result = {
            "input": phone,
            "phonenumbers": self._parse_phonenumbers(phone),
            "numverify": self._numverify(phone) if self.numverify_key else {"note": "No NumVerify API key configured"},
        }
        return result

    def _parse_phonenumbers(self, phone: str) -> Dict:
        try:
            parsed = phonenumbers.parse(phone, None)
            valid = phonenumbers.is_valid_number(parsed)
            possible = phonenumbers.is_possible_number(parsed)
            fmt_intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            fmt_e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            fmt_national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            region = geocoder.description_for_number(parsed, "en")
            carrier_name = carrier.name_for_number(parsed, "en")
            timezones = list(pn_timezone.time_zones_for_number(parsed))
            number_type_map = {
                phonenumbers.PhoneNumberType.MOBILE: "Mobile",
                phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed Line",
                phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed/Mobile",
                phonenumbers.PhoneNumberType.TOLL_FREE: "Toll-Free",
                phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
                phonenumbers.PhoneNumberType.VOIP: "VoIP",
                phonenumbers.PhoneNumberType.UNKNOWN: "Unknown",
            }
            number_type = number_type_map.get(phonenumbers.number_type(parsed), "Unknown")
            return {
                "valid": valid,
                "possible": possible,
                "international": fmt_intl,
                "e164": fmt_e164,
                "national": fmt_national,
                "country_code": f"+{parsed.country_code}",
                "national_number": str(parsed.national_number),
                "region": region,
                "carrier": carrier_name,
                "timezones": timezones,
                "number_type": number_type,
            }
        except phonenumbers.NumberParseException as e:
            return {"error": f"Could not parse number: {e}"}

    def _numverify(self, phone: str) -> Dict:
        clean = phone.replace("+", "").replace(" ", "").replace("-", "")
        resp = make_request(
            "http://apilayer.net/api/validate",
            params={"access_key": self.numverify_key, "number": clean, "country_code": "", "format": 1},
            timeout=10,
        )
        data = safe_json(resp)
        if data:
            return {
                "valid": data.get("valid"),
                "local_format": data.get("local_format"),
                "international_format": data.get("international_format"),
                "country_name": data.get("country_name"),
                "carrier": data.get("carrier"),
                "line_type": data.get("line_type"),
            }
        return {"error": "NumVerify request failed"}

    def display(self, data: Dict):
        section_header(self.console, "PHONE NUMBER LOOKUP")
        self.console.print(f"[bold white]Input:[/] [cyan]{data['input']}[/]\n")

        pn = data.get("phonenumbers", {})
        if "error" not in pn:
            table = Table(title="Phone Intelligence", box=box.ROUNDED, border_style="cyan")
            table.add_column("Field", style="bold white", width=22)
            table.add_column("Value", style="cyan")
            fields = [
                ("Valid", "[green]Yes[/]" if pn.get("valid") else "[red]No[/]"),
                ("International", pn.get("international")),
                ("National", pn.get("national")),
                ("E.164", pn.get("e164")),
                ("Country Code", pn.get("country_code")),
                ("Region", pn.get("region")),
                ("Carrier", pn.get("carrier") or "Unknown"),
                ("Line Type", pn.get("number_type")),
                ("Timezones", ", ".join(pn.get("timezones", []))),
            ]
            for field, value in fields:
                if value:
                    table.add_row(field, str(value))
            self.console.print(table)
        else:
            self.console.print(f"[red]{pn['error']}[/]")

        nv = data.get("numverify", {})
        if nv and "note" not in nv and "error" not in nv:
            self.console.print(
                f"\n[dim]NumVerify:[/] carrier=[cyan]{nv.get('carrier')}[/]  "
                f"line_type=[cyan]{nv.get('line_type')}[/]  country=[cyan]{nv.get('country_name')}[/]"
            )
