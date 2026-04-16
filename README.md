# 🔍 PhantomTrace

![Python](https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)
![Status](https://img.shields.io/badge/status-active-brightgreen?style=for-the-badge)

🌐 **[osintintelligence.xyz/phantomtrace](https://osintintelligence.xyz/phantomtrace.php)** — Official page & Pro version

**PhantomTrace** is a professional, modular OSINT (Open Source Intelligence) CLI framework for gathering publicly available intelligence on individuals and digital assets. Built with Python and Rich for a clean, production-grade experience.

> ⚠️ **For authorized and legal use only.** Always obtain proper consent before investigating any individual. Misuse is your sole responsibility.

---

## Screenshots

> 📸 Screenshots below — take these after your first run and drop the images into a `docs/` folder in the repo, then they'll show here automatically.

### Main Menu
![PhantomTrace Main Menu](docs/screenshot-menu.png)

### Username Lookup
![Username Lookup](docs/screenshot-username.png)

### IP Lookup Result
![IP Lookup](docs/screenshot-ip.png)

### HTML Report Export
![Report](docs/screenshot-report.png)

**To add your own screenshots:**
1. Run `python main.py` and take a screenshot of each screen
2. Save them into a `docs/` folder inside the repo
3. Name them to match the filenames above
4. Push — they'll appear here on GitHub automatically

---

## Features

- **Username Lookup** — Search 50+ platforms for username presence
- **Email Intelligence** — Breach detection (HIBP), MX records, domain analysis
- **IP Lookup** — Geolocation via FrostedServices GeoIP + ip-api.com, ASN, ISP, proxy/VPN detection
- **Phone Lookup** — Carrier, region, line type via `phonenumbers` + optional NumVerify
- **Domain Lookup** — WHOIS, DNS (A/MX/NS/TXT/SOA/CNAME), HTTP headers
- **Social Media Scan** — Public profile discovery across 15 major platforms
- **Full Profile Scan** — Run all modules against a single target
- **Report Export** — JSON and styled HTML reports saved locally
- **Scoring System** — Risk/profile completeness scores per module
- **Activity Logging** — All sessions logged to `logs/`

---

## Installation

```bash
git clone https://github.com/yourusername/PhantomTrace.git
cd PhantomTrace
pip install -r requirements.txt
cp config/.env.example config/.env
# Edit config/.env with your optional API keys
python main.py
```

---

## Configuration

The tool works **without any API keys** — keys unlock additional data sources.

Copy `config/.env.example` to `config/.env` and optionally add keys:

| Variable | Service | Notes |
|---|---|---|
| `HIBP_API_KEY` | HaveIBeenPwned | Email breach lookup |
| `NUMVERIFY_API_KEY` | NumVerify | Enhanced phone data |
| `HUNTER_API_KEY` | Hunter.io | Email verification |

IP geolocation uses the built-in [FrostedServices GeoIP API](https://frostedservices.xyz/api/geoip/) — no key needed.

---

## Usage

```bash
python main.py
```

Select modules from the interactive menu. Results are displayed in formatted tables and optionally exported to `reports/`.

---

## Project Structure

```
PhantomTrace/
├── main.py              # Entry point & CLI menu
├── modules/             # OSINT modules (one per data type)
│   ├── username_lookup.py
│   ├── email_intel.py
│   ├── ip_lookup.py
│   ├── phone_lookup.py
│   ├── domain_lookup.py
│   └── social_media.py
├── utils/               # Helpers: API, logging, formatting, reporting
├── config/              # Settings & API key configuration
├── reports/             # Exported reports (JSON & HTML)
└── logs/                # Activity logs
```

---

## Disclaimer

PhantomTrace is intended for **legal OSINT research only** — penetration testers, security researchers, journalists, and investigators with proper authorization. The authors accept no liability for misuse.

---

## License

MIT — see [LICENSE](LICENSE)
