#!/usr/bin/env python3
"""
scripts/bibi-safe.py
bibigpt 防御式包装器（v1）

解决 bibigpt silent hallucination bug：
  - get-subtitle:  返回 success=true + subtitlesArray=[] + costDuration=60（没字幕也扣额度）
  - summarize:    没字幕时 LLM 编造"符合专业水准的总结框架"，返回 success=true
  - feed:         部分频道 (巫师财经/Acquired/All-In/Bg2 Pod) fetchRSSCached timeout

策略：
  - 不改 bibi 行为，后处理 bibi 返回值，给出明确的 available/isHallucination 信号
  - 调用方可以基于 available 判断"是否值得用"，不会把 fallback 总结当真的用
  - 记录每次调用到 logs/bibi-calls.json，方便审计哪些视频没字幕

用法：
  python3 bibi-safe.py get-subtitle --url <URL>
  python3 bibi-safe.py summarize --url <URL>
  python3 bibi-safe.py feed --limit 50
  python3 bibi-safe.py me

JSON 输出统一 schema：
  {
    "tool": "bibi",
    "command": "get-subtitle" | "summarize" | "feed" | "me",
    "url": "...",
    "called_at": "ISO8601",
    "bibi_success": bool,        # bibi 自己返回的 success
    "available": bool,           # 我们的判断：是否真拿到了字幕/总结
    "is_hallucination": bool,    # summarize 专用：是否 LLM 编造
    "cost_duration": int,        # bibi 扣的秒数
    "reason": str,               # 不可用时给的原因
    "raw": {...}                 # 原始 bibi 返回（裁剪）
  }
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ============ 配置 ============
LOG_DIR = Path.home() / "content-factory" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "bibi-calls.jsonl"

# summarize fallback 的关键词（LLM 编造内容的标志）
HALLUCINATION_MARKERS = [
    "由于您未提供具体的文字转录稿",
    "由于您没有提供具体的",
    "由于未提供",
    "为您构建了一份符合专业水准的总结框架",
    "请补充具体的转录内容",
    "请您补充",
    "我已根据视频标题",
    "根据视频标题所涵盖",
    "无法提供具体的转录",
    "无法获取视频的文字转录",
    "无法获取到转录内容",
    "I have not been provided with",
    "based on the video title",
    "constructed a summary framework",
]


# ============ bibi 调用 ============
def bibi_call(args: list, timeout: int = 60) -> dict:
    """调用 bibi 子命令，返回解析后的 JSON dict。失败返回 dict(error=...)"""
    try:
        result = subprocess.run(
            ["bibi"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"bibi 调用超时（{timeout}s）", "stderr": ""}
    except FileNotFoundError:
        return {"error": "bibi 命令未找到（请安装 BibiGPT Desktop）"}

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    # bibi 输出格式：先是 "Calling..." 行，再是 JSON
    # 从 stdout 中找 JSON
    json_start = stdout.find("{")
    if json_start == -1:
        return {
            "error": f"bibi 返回无 JSON 内容",
            "stdout": stdout[:500],
            "stderr": stderr[:500],
            "returncode": result.returncode,
        }

    try:
        return json.loads(stdout[json_start:])
    except json.JSONDecodeError as e:
        return {
            "error": f"JSON 解析失败: {e}",
            "raw": stdout[json_start:json_start + 500],
        }


# ============ 后处理判断 ============
def judge_get_subtitle(bibi_resp: dict, url: str) -> dict:
    """判断 get-subtitle 是否真拿到了字幕"""
    detail = bibi_resp.get("detail", {})
    subs = detail.get("subtitlesArray", [])
    raw_lang = detail.get("rawLang", "")
    audio_url = detail.get("audioUrl", "")
    play_url = detail.get("playUrl", "")
    content_text = detail.get("contentText", "")

    # 真实可用的信号
    has_subs = isinstance(subs, list) and len(subs) > 0
    has_lang = bool(raw_lang)
    has_audio = bool(audio_url)
    has_play = bool(play_url)
    has_text = bool(content_text.strip())

    available = has_subs or has_audio or has_text

    # 推理原因
    if available:
        reason = "OK"
    else:
        signals = []
        if not has_subs:
            signals.append("subtitlesArray 空")
        if not has_lang:
            signals.append("rawLang 空")
        if not has_audio:
            signals.append("audioUrl 空")
        if not has_play:
            signals.append("playUrl 空")
        if not has_text:
            signals.append("contentText 空")
        reason = "; ".join(signals) if signals else "未提供字幕数据"

    return {
        "tool": "bibi",
        "command": "get-subtitle",
        "url": url,
        "called_at": datetime.now(timezone.utc).isoformat(),
        "bibi_success": bibi_resp.get("success", False),
        "available": available,
        "is_hallucination": False,
        "cost_duration": bibi_resp.get("costDuration", 0),
        "reason": reason,
        "raw": {
            "title": detail.get("title", "")[:200],
            "duration": detail.get("duration", 0),
            "subtitles_count": len(subs) if isinstance(subs, list) else 0,
            "raw_lang": raw_lang,
            "has_audio_url": has_audio,
            "has_play_url": has_play,
        },
    }


def judge_summarize(bibi_resp: dict, url: str) -> dict:
    """判断 summarize 是否真的有用（基于真实字幕），还是 LLM 编造的 fallback"""
    summary = bibi_resp.get("summary", "")
    detail = bibi_resp.get("detail", {})
    subs = detail.get("subtitlesArray", [])

    has_subs = isinstance(subs, list) and len(subs) > 0
    summary_text = (summary or "").strip()

    # 检测 hallucination
    is_hallucination = False
    hallucination_reason = ""

    if not summary_text:
        is_hallucination = True
        hallucination_reason = "summary 字段为空"
    else:
        for marker in HALLUCINATION_MARKERS:
            if marker in summary_text:
                is_hallucination = True
                hallucination_reason = f"包含 fallback 标志: '{marker[:30]}...'"
                break

    # 如果没拿到字幕 + 有 summary → 几乎肯定是编造
    if not has_subs and summary_text and not is_hallucination:
        is_hallucination = True
        hallucination_reason = "无字幕但返回了 summary，疑似 LLM 编造"

    # 一些额外信号：summary 里有过期年份 / 推测性表述
    if not is_hallucination and summary_text:
        for suspicious in ["2023 年", "2024 年", "据预测", "可能", "预计"]:
            # 注意：这些词不一定都是幻觉，只是提示
            pass  # 不强制标记

    available = (not is_hallucination) and bool(summary_text)

    return {
        "tool": "bibi",
        "command": "summarize",
        "url": url,
        "called_at": datetime.now(timezone.utc).isoformat(),
        "bibi_success": bibi_resp.get("success", False),
        "available": available,
        "is_hallucination": is_hallucination,
        "cost_duration": bibi_resp.get("costDuration", 0),
        "reason": hallucination_reason if is_hallucination else ("OK" if available else "不可用"),
        "raw": {
            "summary_preview": summary_text[:200] if summary_text else "",
            "summary_length": len(summary_text),
            "subtitles_count": len(subs) if isinstance(subs, list) else 0,
        },
    }


def judge_feed(bibi_resp: dict) -> dict:
    """判断 feed 抓取结果"""
    items = bibi_resp.get("items", [])
    failed = bibi_resp.get("failedChannels", [])

    return {
        "tool": "bibi",
        "command": "feed",
        "url": None,
        "called_at": datetime.now(timezone.utc).isoformat(),
        "bibi_success": bibi_resp.get("success", True),
        "available": len(items) > 0,
        "is_hallucination": False,
        "cost_duration": 0,  # feed 不扣额度
        "reason": "OK" if items else "feed 返回 0 条",
        "raw": {
            "items_count": len(items),
            "failed_channels_count": len(failed),
            "failed_channels": [
                {
                    "title": ch.get("channelTitle", ""),
                    "url": ch.get("channelUrl", ""),
                    "message": ch.get("message", ""),
                }
                for ch in failed
            ],
            "next_cursor": bibi_resp.get("nextCursor"),
        },
    }


def judge_me(bibi_resp: dict) -> dict:
    """me 命令"""
    return {
        "tool": "bibi",
        "command": "me",
        "url": None,
        "called_at": datetime.now(timezone.utc).isoformat(),
        "bibi_success": True,
        "available": True,
        "is_hallucination": False,
        "cost_duration": 0,
        "reason": "OK",
        "raw": {
            "remaining_minutes": bibi_resp.get("remainingMinutes"),
            "plan_tier": bibi_resp.get("plan", {}).get("tier"),
            "expires_at": bibi_resp.get("plan", {}).get("expiresAt"),
        },
    }


# ============ 日志 ============
def append_log(record: dict):
    """追加到 logs/bibi-calls.jsonl"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"⚠️  写日志失败: {e}", file=sys.stderr)


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description="bibigpt 防御式包装器")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # get-subtitle
    p_gs = sub.add_parser("get-subtitle", help="获取视频字幕（带可用性判断）")
    p_gs.add_argument("--url", required=True)

    # summarize
    p_sm = sub.add_parser("summarize", help="总结视频（带 hallucination 检测）")
    p_sm.add_argument("--url", required=True)

    # feed
    p_fd = sub.add_parser("feed", help="抓取订阅 feed（带 failedChannels 提示）")
    p_fd.add_argument("--limit", type=int, default=50)

    # me
    sub.add_parser("me", help="查账户额度")

    args = parser.parse_args()

    # 调用 bibi
    if args.cmd == "get-subtitle":
        bibi_resp = bibi_call(["get-subtitle", "--url", args.url, "--json"])
        if "error" in bibi_resp:
            record = {
                "tool": "bibi",
                "command": "get-subtitle",
                "url": args.url,
                "called_at": datetime.now(timezone.utc).isoformat(),
                "bibi_success": False,
                "available": False,
                "is_hallucination": False,
                "cost_duration": 0,
                "reason": bibi_resp["error"],
                "raw": bibi_resp,
            }
        else:
            record = judge_get_subtitle(bibi_resp, args.url)
    elif args.cmd == "summarize":
        bibi_resp = bibi_call(["summarize", args.url, "--json"])
        if "error" in bibi_resp:
            record = {
                "tool": "bibi",
                "command": "summarize",
                "url": args.url,
                "called_at": datetime.now(timezone.utc).isoformat(),
                "bibi_success": False,
                "available": False,
                "is_hallucination": False,
                "cost_duration": 0,
                "reason": bibi_resp["error"],
                "raw": bibi_resp,
            }
        else:
            record = judge_summarize(bibi_resp, args.url)
    elif args.cmd == "feed":
        bibi_resp = bibi_call(["feed", "--limit", str(args.limit), "--json"])
        if "error" in bibi_resp:
            record = {
                "tool": "bibi",
                "command": "feed",
                "url": None,
                "called_at": datetime.now(timezone.utc).isoformat(),
                "bibi_success": False,
                "available": False,
                "is_hallucination": False,
                "cost_duration": 0,
                "reason": bibi_resp["error"],
                "raw": bibi_resp,
            }
        else:
            record = judge_feed(bibi_resp)
    elif args.cmd == "me":
        bibi_resp = bibi_call(["me"])
        if "error" in bibi_resp:
            record = {
                "tool": "bibi",
                "command": "me",
                "url": None,
                "called_at": datetime.now(timezone.utc).isoformat(),
                "bibi_success": False,
                "available": False,
                "is_hallucination": False,
                "cost_duration": 0,
                "reason": bibi_resp["error"],
                "raw": bibi_resp,
            }
        else:
            record = judge_me(bibi_resp)

    # 输出 + 日志
    append_log(record)
    print(json.dumps(record, ensure_ascii=False, indent=2))

    # 如果不可用，stderr 给提示
    if not record["available"] and record["command"] in ("get-subtitle", "summarize"):
        print(
            f"\n⚠️  bibi 返回 success={record['bibi_success']} 但内容不可用。"
            f"原因: {record['reason']}",
            file=sys.stderr,
        )
        print(
            "💡 替代方案: 用 playwright/yt-dlp 抓 description，或用 web_search 验证",
            file=sys.stderr,
        )

    # exit code: available=0 else 2 (有别于 1 错误)
    sys.exit(0 if record["available"] else 2)


if __name__ == "__main__":
    main()