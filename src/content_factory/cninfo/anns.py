"""Announcements metadata API for cninfo.com.cn (巨潮资讯网).

This module provides functions to query A-share company announcements via the
free cninfo POST API, bypassing the Tushare paid wall.

Example:
    >>> from content_factory.cninfo import get_announcements, batch_query
    >>> # Single company
    >>> anns = get_announcements("600487.SH", days=14)
    >>> print(f"Found {len(anns)} announcements")
    >>> # Multiple companies
    >>> results = batch_query(["600487.SH", "300308.SZ"], days=14)
    >>> for ts_code, anns in results.items():
    ...     print(f"{ts_code}: {len(anns)} announcements")
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, cast

from content_factory.cninfo._utils import (
    CNINFO_API,
    CNINFO_STOCK_LIST_ALL,
    DEFAULT_RATE_LIMIT_SECONDS,
    detect_exchange,
    get_json,
    is_valid_ts_code,
    post_json,
)

# ── Data model ───────────────────────────────────────────────────────────────


@dataclass
class Announcement:
    """A single announcement from cninfo.

    Attributes:
        ann_id: The cninfo announcement ID (e.g., "1225380372").
        ts_code: TS-format stock code (e.g., "600487.SH").
        org_id: The cninfo internal orgId for the company.
        ann_date: The announcement date in YYYY-MM-DD format.
        title: The announcement title.
        url: The full URL to the announcement PDF on static.cninfo.com.cn.
        sec_code: The 6-digit securities code (e.g., "600487").
    """

    ann_id: str
    ts_code: str
    org_id: str
    ann_date: str
    title: str
    url: str
    sec_code: str

    def to_dict(self) -> dict[str, str]:
        """Convert to a dict (for JSON serialization)."""
        return asdict(self)

    @classmethod
    def from_api_response(cls, raw: dict[str, Any], ts_code: str, org_id: str) -> Announcement:
        """Build an Announcement from a cninfo API response item.

        Args:
            raw: The raw dict from cninfo API.
            ts_code: The TS-format stock code we queried.
            org_id: The orgId we resolved for the company.
        """
        ts_ms = raw.get("announcementTime", 0)
        ann_date = datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d")
        adj_url = raw.get("adjunctUrl", "")
        return cls(
            ann_id=str(raw.get("announcementId", "")),
            ts_code=ts_code,
            org_id=org_id,
            ann_date=ann_date,
            title=raw.get("announcementTitle", "").strip(),
            url=f"http://static.cninfo.com.cn/{adj_url}" if adj_url else "",
            sec_code=raw.get("secCode", ts_code.split(".")[0]),
        )


# ── OrgId resolution ─────────────────────────────────────────────────────────


_ORG_ID_CACHE: dict[str, str | None] = {}


def _get_org_id(ts_code: str) -> str | None:
    """Resolve the cninfo orgId for a TS-format stock code.

    Results are cached to avoid repeated downloads of the stock list.

    Args:
        ts_code: TS-format stock code (e.g., "600487.SH").

    Returns:
        The orgId string, or None if not found.
    """
    if ts_code in _ORG_ID_CACHE:
        return _ORG_ID_CACHE[ts_code]

    code = ts_code.split(".")[0]
    data = get_json(CNINFO_STOCK_LIST_ALL)
    if data is None:
        _ORG_ID_CACHE[ts_code] = None
        return None

    for stock in data.get("stockList", []):
        if stock.get("code") == code:
            org_id = cast("str | None", stock.get("orgId"))
            _ORG_ID_CACHE[ts_code] = org_id
            return org_id

    _ORG_ID_CACHE[ts_code] = None
    return None


# ── Public API ───────────────────────────────────────────────────────────────


def get_announcements(
    ts_code: str,
    days: int = 14,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    page_size: int = 30,
) -> list[Announcement]:
    """Query announcements for a single company.

    Args:
        ts_code: TS-format stock code (e.g., "600487.SH").
        days: Number of days to look back (default 14). Ignored if start_date is given.
        start_date: Start date in YYYY-MM-DD format (overrides days).
        end_date: End date in YYYY-MM-DD format (default: today).
        page_size: Number of announcements per page (default 30).

    Returns:
        List of Announcement objects (may be empty).

    Raises:
        ValueError: If ts_code is not in valid TS format.

    Examples:
        >>> anns = get_announcements("600487.SH", days=14)
        >>> for a in anns[:3]:
        ...     print(f"[{a.ann_date}] {a.title}")
    """
    if not is_valid_ts_code(ts_code):
        raise ValueError(
            f"Invalid TS code: {ts_code!r}. Expected format: '600487.SH' (6 digits + '.' + 2 letters)."
        )

    org_id = _get_org_id(ts_code)
    if not org_id:
        return []

    end = end_date or datetime.now().strftime("%Y-%m-%d")
    start = start_date or (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    payload = {
        "stock": f"{ts_code.split('.')[0]},{org_id}",
        "tabName": "fulltext",
        "pageSize": page_size,
        "pageNum": 1,
        "column": detect_exchange(ts_code),
        "category": "",
        "seDate": f"{start}~{end}",
        "isHLtitle": "true",
    }

    data = post_json(CNINFO_API, payload)
    if not data:
        return []

    return [
        Announcement.from_api_response(item, ts_code, org_id)
        for item in (data.get("announcements") or [])
    ]


def batch_query(
    ts_codes: list[str],
    days: int = 14,
    *,
    rate_limit: float = DEFAULT_RATE_LIMIT_SECONDS,
) -> dict[str, list[Announcement]]:
    """Query announcements for multiple companies.

    Args:
        ts_codes: List of TS-format stock codes.
        days: Number of days to look back (default 14).
        rate_limit: Seconds to sleep between requests (default 0.5s).

    Returns:
        Dict mapping ts_code → list of Announcement.

    Examples:
        >>> results = batch_query(["600487.SH", "300308.SZ"], days=14)
        >>> print(f"{sum(len(v) for v in results.values())} total announcements")
    """
    results: dict[str, list[Announcement]] = {}
    for i, ts_code in enumerate(ts_codes, 1):
        try:
            anns = get_announcements(ts_code, days=days)
        except ValueError as e:
            print(f"  ⚠️  Skipping {ts_code}: {e}")
            anns = []
        results[ts_code] = anns
        print(
            f"[{i}/{len(ts_codes)}] {ts_code}: {len(anns)} announcements",
            file=__import__("sys").stderr,
        )
        if i < len(ts_codes):
            time.sleep(rate_limit)
    return results


# ── Output formatting ────────────────────────────────────────────────────────


def format_markdown_summary(
    results: dict[str, list[Announcement]],
    *,
    title: str = "公告摘要",
) -> str:
    """Format batch results as a Markdown summary.

    Args:
        results: Dict mapping ts_code → list of Announcement.
        title: Section title.

    Returns:
        Markdown-formatted string.
    """
    total = sum(len(v) for v in results.values())
    lines = [f"\n## {title}({len(results)} 家公司 · {total} 条公告)\n"]
    for ts_code, anns in results.items():
        if not anns:
            lines.append(f"### {ts_code} — 0 条\n")
            continue
        lines.append(f"### {ts_code} — {len(anns)} 条")
        for a in anns[:10]:
            lines.append(f"- [{a.ann_date}] {a.title[:80]}")
            lines.append(f"  - {a.url}")
        if len(anns) > 10:
            lines.append(f"- ... +{len(anns) - 10} more")
        lines.append("")
    return "\n".join(lines)
