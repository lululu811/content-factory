"""Common utilities for cninfo-toolkit.

This module provides shared HTTP helpers, filename sanitization, and
stock-code parsing utilities used by all submodules.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast

import requests

if TYPE_CHECKING:
    from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

CNINFO_API = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
"""The cninfo POST API for announcement queries (free, no auth required)."""

CNINFO_STOCK_LIST_ALL = "http://www.cninfo.com.cn/new/data/szse_stock.json"
"""JSON listing of all A-share stocks (sh/sz/bj) with their orgId mappings.

Note: Despite the filename `szse_stock.json`, this URL actually returns
**all** A-share stocks (Shanghai + Shenzhen + Beijing exchanges).
"""

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
"""Browser-like User-Agent header (cninfo blocks obvious bot UAs)."""

DEFAULT_TIMEOUT = 30
"""Default HTTP request timeout in seconds."""

DEFAULT_RETRIES = 3
"""Default number of retries for failed HTTP requests."""

DEFAULT_RATE_LIMIT_SECONDS = 0.5
"""Default delay between requests to avoid IP ban (cninfo's soft limit)."""

# Stock code regex pattern: 6 digits + '.' + 2-letter exchange (SH/SZ/BJ only)
TS_CODE_PATTERN = re.compile(r"^\d{6}\.(SH|SZ|BJ)$")
"""Regex matching a valid TS-format stock code (e.g., 600487.SH, 300308.SZ, 920438.BJ)."""


# ── HTTP helpers ─────────────────────────────────────────────────────────────


def post_json(
    url: str,
    data: dict[str, Any],
    *,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    user_agent: str = DEFAULT_USER_AGENT,
) -> dict[str, Any] | None:
    """POST form-encoded data and parse the JSON response.

    Args:
        url: Target URL.
        data: Form data to POST.
        timeout: Request timeout in seconds.
        retries: Number of retries on failure.
        user_agent: User-Agent header.

    Returns:
        Parsed JSON dict, or None on failure.
    """
    headers = {
        "User-Agent": user_agent,
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
    }
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, data=data, headers=headers, timeout=timeout)
            resp.raise_for_status()
            result: dict[str, Any] = cast("dict[str, Any]", resp.json())
            return result
        except (requests.RequestException, ValueError) as exc:
            last_err = exc
            if attempt < retries:
                continue
    if last_err is not None:
        raise RuntimeError(f"POST {url} failed after {retries} retries: {last_err}") from last_err
    return None


def get_json(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    user_agent: str = DEFAULT_USER_AGENT,
) -> dict[str, Any] | None:
    """GET a URL and parse the JSON response.

    Args:
        url: Target URL.
        timeout: Request timeout in seconds.
        retries: Number of retries on failure.
        user_agent: User-Agent header.

    Returns:
        Parsed JSON dict, or None on failure.
    """
    headers = {
        "User-Agent": user_agent,
        "Accept": "*/*",
    }
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            result: dict[str, Any] = cast("dict[str, Any]", resp.json())
            return result
        except (requests.RequestException, ValueError) as exc:
            last_err = exc
            if attempt < retries:
                continue
    if last_err is not None:
        raise RuntimeError(f"GET {url} failed after {retries} retries: {last_err}") from last_err
    return None


# ── Stock code helpers ───────────────────────────────────────────────────────


def is_valid_ts_code(code: str) -> bool:
    """Check if a string is a valid TS-format stock code.

    Examples:
        >>> is_valid_ts_code("600487.SH")
        True
        >>> is_valid_ts_code("300308.SZ")
        True
        >>> is_valid_ts_code("600487")
        False
        >>> is_valid_ts_code("600487.sh")
        False
    """
    return bool(TS_CODE_PATTERN.match(code))


def parse_ts_code_list(text: str) -> list[str]:
    """Parse a text blob for valid TS-format stock codes.

    Accepts any of: newlines, commas, semicolons, tabs, or spaces as separators.

    Examples:
        >>> parse_ts_code_list("600487.SH\\n300308.SZ")
        ['600487.SH', '300308.SZ']
        >>> parse_ts_code_list("600487.SH, 300308.SZ; 000070.SZ")
        ['600487.SH', '300308.SZ', '000070.SZ']
        >>> parse_ts_code_list("garbage\\n600487.SH\\nmore garbage")
        ['600487.SH']
    """
    raw_tokens = re.split(r"[\s,;]+", text)
    return [t.strip() for t in raw_tokens if is_valid_ts_code(t.strip())]


def detect_exchange(ts_code: str) -> str:
    """Detect the exchange from a TS-format stock code.

    Args:
        ts_code: Stock code in TS format (e.g., "600487.SH").

    Returns:
        Exchange identifier: "sse" (Shanghai), "szse" (Shenzhen),
        or "bj" (Beijing).

    Examples:
        >>> detect_exchange("600487.SH")
        'sse'
        >>> detect_exchange("300308.SZ")
        'szse'
        >>> detect_exchange("688498.SH")
        'sse'
        >>> detect_exchange("920438.BJ")
        'bj'
    """
    code = ts_code.split(".")[0]
    if code.startswith(("8", "4", "9")):
        return "bj"
    if code.startswith("6"):
        return "sse"
    return "szse"


# ── Filename helpers ─────────────────────────────────────────────────────────


_INVALID_FILENAME_CHARS = re.compile(r'[\\/:\*\?"<>|]')
_WHITESPACE_RUN = re.compile(r"\s+")


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """Sanitize a title into a safe filename slug.

    Args:
        title: Original title (may contain filesystem-unsafe chars).
        max_length: Maximum length of the resulting slug.

    Returns:
        A filesystem-safe filename slug.

    Examples:
        >>> sanitize_filename("关于 2024 年报的问询函")
        '关于 2024 年报的问询函'
        >>> sanitize_filename("foo/bar:baz*qux", max_length=10)
        'foo-bar-ba'
        >>> sanitize_filename("///")
        'untitled'
    """
    slug = _INVALID_FILENAME_CHARS.sub("-", title)
    slug = _WHITESPACE_RUN.sub(" ", slug).strip()
    if len(slug) > max_length:
        slug = slug[:max_length].strip()
    slug = slug.strip(". ").strip("-_")
    return slug or "untitled"


# ── Path helpers ─────────────────────────────────────────────────────────────


def ensure_directory(path: Path) -> Path:
    """Create a directory if it doesn't exist (parents=True).

    Args:
        path: Directory path.

    Returns:
        The same path (for chaining).
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
