#!/usr/bin/env python3
"""
scripts/rss-feed.py
自建 RSS 源聚合器 — 替代 BibiGPT 的 feed 命令

支持平台:
  - YouTube (官方 RSS)
  - B站 (RSSHub / B站官方 API)
  - 播客 (标准 RSS)
  - 抖音 (暂不支持 RSS，需要其他方案)

输出格式与 bibi feed --json 一致，可直接接入 filter-candidates.py → topic-scorer.py

用法:
  python3 scripts/rss-feed.py --config scripts/rss-channels.json
  python3 scripts/rss-feed.py --config scripts/rss-channels.json --days 7 --limit 50
"""

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKDIR = Path.home() / "content-factory"
DEFAULT_CONFIG = WORKDIR / "scripts" / "rss-channels.json"

# 超时设置
TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) content-factory-rss/1.0"

# 代理配置（cron 环境下可能没有环境变量，硬编码备用）
DEFAULT_PROXY = "http://127.0.0.1:7897"


def fetch_url(url: str) -> str:
    """通用 HTTP 请求（使用 curl 以支持代理）"""
    try:
        # 检测代理（优先环境变量，否则用默认）
        proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy") or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or DEFAULT_PROXY
        cmd = ["curl", "-s", "-L", "--max-time", str(TIMEOUT), "-A", USER_AGENT]
        if proxy:
            cmd.extend(["-x", proxy])
        cmd.append(url)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT + 5,
        )
        return result.stdout
    except Exception as e:
        return ""


def parse_duration_iso(s: str) -> str:
    """ISO 8601 duration (PT1H2M3S) → HH:MM:SS or MM:SS"""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
    if not m:
        return "00:00"
    h, mi, sec = (int(m.group(i) or 0) for i in (1, 2, 3))
    total = h * 3600 + mi * 60 + sec
    if h > 0:
        return f"{h:02d}:{mi:02d}:{sec:02d}"
    return f"{mi:02d}:{sec:02d}"


def parse_youtube_rss(xml_text: str, channel_title: str) -> list:
    """解析 YouTube RSS (Atom feed)"""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }

    for entry in root.findall("atom:entry", ns):
        video_id = entry.findtext("yt:videoId", "", ns)
        title = entry.findtext("atom:title", "", ns) or entry.findtext("media:group/media:title", "", ns)
        published = entry.findtext("atom:published", "", ns)
        thumbnail = ""
        media_group = entry.find("media:group", ns)
        if media_group is not None:
            thumb = media_group.find("media:thumbnail", ns)
            if thumb is not None:
                thumbnail = thumb.get("url", "")
        # duration
        duration_str = "00:00"
        if media_group is not None:
            content_el = media_group.find("media:content", ns)
            if content_el is not None:
                dur_sec = content_el.get("duration", "")
                if dur_sec and dur_sec.isdigit():
                    total = int(dur_sec)
                    h, rem = divmod(total, 3600)
                    m, s = divmod(rem, 60)
                    duration_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

        if video_id:
            items.append({
                "channelTitle": channel_title,
                "title": title,
                "sourceUrl": f"https://www.youtube.com/watch?v={video_id}",
                "coverUrl": thumbnail,
                "duration": duration_str,
                "publishedAt": published,
                "isUnseen": True,
            })
    return items


def parse_podcast_rss(xml_text: str, channel_title: str) -> list:
    """解析播客 RSS (标准 RSS 2.0)"""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    channel = root.find("channel")
    if channel is None:
        return items

    for item in channel.findall("item"):
        title = item.findtext("title", "")
        pub_date = item.findtext("pubDate", "")
        enclosure = item.find("enclosure")
        url = enclosure.get("url", "") if enclosure is not None else ""
        # 尝试解析 duration
        duration_str = "00:00"
        itunes_dur = item.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}duration", "")
        if itunes_dur:
            duration_str = parse_duration_iso(itunes_dur) if itunes_dur.startswith("PT") else itunes_dur

        items.append({
            "channelTitle": channel_title,
            "title": title,
            "sourceUrl": url,
            "coverUrl": "",
            "duration": duration_str,
            "publishedAt": pub_date,
            "isUnseen": True,
        })
    return items


def parse_bilibili_rss(xml_text: str, channel_title: str) -> list:
    """解析 B站 RSS (RSSHub 格式)"""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    channel = root.find("channel")
    if channel is None:
        # 可能是 Atom
        return parse_youtube_rss(xml_text, channel_title)

    for item in channel.findall("item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub_date = item.findtext("pubDate", "")
        # 从 link 提取 BV 号
        bv_match = re.search(r"(BV\w+)", link)
        cover = ""
        desc = item.findtext("description", "")
        img_match = re.search(r'<img[^>]+src="([^"]+)"', desc)
        if img_match:
            cover = img_match.group(1)

        if link:
            items.append({
                "channelTitle": channel_title,
                "title": title,
                "sourceUrl": link,
                "coverUrl": cover,
                "duration": "00:00",  # RSS 通常没有时长
                "publishedAt": pub_date,
                "isUnseen": True,
            })
    return items


def fetch_channel(ch: dict) -> tuple:
    """抓取单个频道，返回 (items, error_msg)"""
    url = ch.get("rss_url", "")
    title = ch.get("title", "")
    platform = ch.get("platform", "")

    if not url:
        return [], "no rss_url"

    xml_text = fetch_url(url)
    if not xml_text:
        return [], f"fetch failed: {url}"

    if platform == "youtube":
        return parse_youtube_rss(xml_text, title), ""
    elif platform == "bilibili":
        return parse_bilibili_rss(xml_text, title), ""
    elif platform == "podcast":
        return parse_podcast_rss(xml_text, title), ""
    else:
        # 自动检测
        if "youtube.com" in url:
            return parse_youtube_rss(xml_text, title), ""
        elif "bilibili" in url or "rsshub" in url:
            return parse_bilibili_rss(xml_text, title), ""
        else:
            return parse_podcast_rss(xml_text, title), ""


def enrich_youtube_durations(items: list) -> list:
    """用 yt-dlp 补充 YouTube 视频时长（批量查询）

    优化:
    - batch_size:3 → 8(并行查更多,减少 round trip)
    - 单 batch timeout:60s → 30s(避免卡死)
    - 静默失败:不阻断主流程
    """
    # 筛选出需要补充时长的 YouTube 视频
    yt_items = [it for it in items if "youtube.com/watch" in it.get("sourceUrl", "") and it.get("duration") == "00:00"]
    if not yt_items:
        return items

    # 批量查询视频信息
    proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy") or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or DEFAULT_PROXY

    # 分批处理(batch_size 调大,降低总耗时)
    batch_size = 8
    duration_map = {}

    for i in range(0, len(yt_items), batch_size):
        batch = yt_items[i:i+batch_size]
        urls = [it["sourceUrl"] for it in batch]

        try:
            cmd = ["yt-dlp", "--flat-playlist", "--print", "%(id)s|||%(duration)s|||%(duration_string)s", "--no-warnings"]
            if proxy:
                cmd.extend(["--proxy", proxy])
            cmd.extend(urls)

            # 单 batch 30s timeout(从 60s 降低,避免卡死)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                continue

            # 解析结果
            for line in result.stdout.strip().split("\n"):
                if "|||" not in line:
                    continue
                parts = line.split("|||")
                if len(parts) >= 3:
                    video_id = parts[0]
                    duration_str = parts[2] if parts[2] else parts[1]
                    if video_id and duration_str:
                        duration_map[video_id] = duration_str

        except Exception as e:
            continue  # 静默失败，不影响主流程

    # 更新 items
    for it in items:
        url = it.get("sourceUrl", "")
        match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
        if match:
            video_id = match.group(1)
            if video_id in duration_map:
                it["duration"] = duration_map[video_id]

    return items


def main():
    parser = argparse.ArgumentParser(description="自建 RSS 源聚合器")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="频道配置 JSON")
    parser.add_argument("--days", type=int, default=7, help="只保留最近 N 天")
    parser.add_argument("--limit", type=int, default=100, help="最大返回条数")
    parser.add_argument("--output", help="输出文件路径（默认 stdout）")
    parser.add_argument("--meta", help="同时输出 meta JSON 到指定路径")
    parser.add_argument("--no-enrich", action="store_true", help="跳过 yt-dlp 时长补充(快速模式,适合 limit > 20)")
    args = parser.parse_args()

    # 读取配置
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        channels = json.load(f)

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    all_items = []
    failed = []

    for ch in channels:
        items, err = fetch_channel(ch)
        if err:
            failed.append({"title": ch.get("title", ""), "url": ch.get("rss_url", ""), "message": err})
            continue

        # 时间过滤
        for item in items:
            pub = item.get("publishedAt", "")
            if pub:
                try:
                    pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    if pub_dt < cutoff:
                        continue
                except ValueError:
                    pass
            all_items.append(item)

    # 按时间排序
    all_items.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    all_items = all_items[:args.limit]

    # 用 yt-dlp 补充 YouTube 视频时长(--no-enrich 跳过,适合大批量)
    if not args.no_enrich:
        all_items = enrich_youtube_durations(all_items)

    result = {
        "items": all_items,
        "failedChannels": failed,
    }

    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ RSS feed: {len(all_items)} 条视频 → {args.output}", file=sys.stderr)
        if failed:
            print(f"⚠️  失败频道: {len(failed)} 个", file=sys.stderr)
            for ch in failed:
                print(f"    {ch['title']:30s} | {ch['message'][:60]}", file=sys.stderr)
    else:
        print(output)

    # meta 输出
    if args.meta:
        meta = {
            "tool": "rss-feed",
            "called_at": datetime.now(timezone.utc).isoformat(),
            "items_count": len(all_items),
            "failed_count": len(failed),
            "channels_count": len(channels),
        }
        Path(args.meta).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
