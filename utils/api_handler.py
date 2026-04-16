"""Centralized API request handler with retry, timeout, and rate limiting."""
import time
import requests
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger("api_handler")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def make_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict] = None,
    params: Optional[Dict] = None,
    timeout: int = 10,
    retries: int = 3,
    retry_delay: float = 2.0,
    **kwargs
) -> Optional[requests.Response]:
    """Make an HTTP request with retry and timeout logic."""
    hdrs = {**DEFAULT_HEADERS, **(headers or {})}
    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(
                method, url, headers=hdrs, params=params,
                timeout=timeout, **kwargs
            )
            logger.debug(f"[{method}] {url} -> {resp.status_code}")
            return resp
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt}/{retries}: {url}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error on attempt {attempt}/{retries}: {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            break
        if attempt < retries:
            time.sleep(retry_delay)
    return None


def safe_json(response: Optional[requests.Response]) -> Optional[Dict]:
    """Safely parse JSON from a response."""
    if response is None:
        return None
    try:
        return response.json()
    except Exception:
        return None
