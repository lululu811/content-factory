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
def bibi_call(args: list, timeout: int = 60, raw: bool = False) -> dict:
    """调用 bibi 子命令，返回解析后的 JSON dict。raw=True 时返回 dict(stdout=...)

    失败返回 dict(error=...)
    """
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

    # raw 模式：直接返回 stdout（用于 auth check 等非 JSON 命令）
    if raw:
        return {"raw_output": stdout, "stderr": stderr, "returncode": result.returncode}

    # 标准模式：从 stdout 中找 JSON
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


def judge_auth_check(raw_output: str, bibi_resp: dict = None) -> dict:
    """auth check 命令（输出不是 JSON，需要解析纯文本）"""
    has_token = "token loaded" in raw_output.lower() or "session" in raw_output.lower()
    has_auth_line = "Auth:" in raw_output

    return {
        "tool": "bibi",
        "command": "auth-check",
        "url": None,
        "called_at": datetime.now(timezone.utc).isoformat(),
        "bibi_success": has_auth_line,
        "available": has_token,
        "is_hallucination": False,
        "cost_duration": 0,
        "reason": "OK" if has_token else "未检测到 token",
        "raw": {
            "output_preview": raw_output[:500],
            "token_loaded": has_token,
        },
    }


def judge_channel_health(bibi_resp: dict) -> dict:
    """channel-health 命令（每个频道独立 ok 状态）"""
    items = bibi_resp.get("items", [])
    ok_count = sum(1 for it in items if it.get("ok"))
    fail_count = len(items) - ok_count

    failed_channels = [
        {
            "title": it.get("channelTitle", ""),
            "url": it.get("channelUrl", ""),
            "message": it.get("message", ""),
            "latest_published_at": it.get("latestPublishedAt"),
        }
        for it in items if not it.get("ok")
    ]

    return {
        "tool": "bibi",
        "command": "channel-health",
        "url": None,
        "called_at": datetime.now(timezone.utc).isoformat(),
        "bibi_success": bibi_resp.get("success", True),
        "available": len(items) > 0,
        "is_hallucination": False,
        "cost_duration": 0,
        "reason": f"{ok_count}/{len(items)} 频道健康" if items else "无频道数据",
        "raw": {
            "total_channels": len(items),
            "ok_count": ok_count,
            "fail_count": fail_count,
            "failed_channels": failed_channels,
            "checked_at": items[0].get("checkedAt") if items else None,
        },
    }


def judge_expand_url(bibi_resp: dict, original_url: str) -> dict:
    """expand-url 命令（短链接展开）"""
    expanded = bibi_resp.get("url", "")

    # 判断是否真的展开了（不同 = 展开成功）
    actually_expanded = bool(expanded) and expanded != original_url

    return {
        "tool": "bibi",
        "command": "expand-url",
        "url": original_url,
        "called_at": datetime.now(timezone.utc).isoformat(),
        "bibi_success": bibi_resp.get("success", True),
        "available": actually_expanded,
        "is_hallucination": False,
        "cost_duration": 0,
        "reason": "展开成功" if actually_expanded else f"未展开（仍是 {expanded or '空'}）",
        "raw": {
            "original_url": original_url,
            "expanded_url": expanded,
            "is_short_link": "b23.tv" in original_url or "youtu.be" in original_url,
        },
    }


def judge_summarize_chapter(bibi_resp: dict, url: str) -> dict:
    """summarize --chapter 命令（按章节总结，复用 hallucination 检测 + 独立判断 chapters 数组）"""
    # 复用 summarize 的 hallucination 判断
    base = judge_summarize(bibi_resp, url)
    base["command"] = "summarize-chapter"

    # chapters 数组单独判断（即使整体 hallucination，chapters 时间戳可能有用）
    chapters = bibi_resp.get("chapters", [])
    chapter_summary = bibi_resp.get("chapterSummary", "")

    has_real_chapters = (
        isinstance(chapters, list)
        and len(chapters) > 0
        and any(ch.get("summary") or ch.get("title") for ch in chapters)
    )

    # 检查 chapters 自身是否 hallucination
    chapter_hallucination = False
    for ch in chapters:
        ch_summary = ch.get("summary", "")
        if ch_summary:
            for marker in HALLUCINATION_MARKERS:
                if marker in ch_summary:
                    chapter_hallucination = True
                    break
        if chapter_hallucination:
            break

    base["raw"]["chapters_count"] = len(chapters) if isinstance(chapters, list) else 0
    base["raw"]["chapter_hallucination"] = chapter_hallucination
    base["raw"]["has_real_chapters"] = has_real_chapters

    return base


def judge_async_task(bibi_resp: dict, action: str, task_id: str = None) -> dict:
    """async-task 命令（创建或查询 async 任务）

    action: 'create' 或 'status'
    """
    if action == "create":
        task_id_out = bibi_resp.get("id") or bibi_resp.get("taskId") or bibi_resp.get("task_id")
        success = bool(task_id_out)
        return {
            "tool": "bibi",
            "command": "async-task",
            "url": bibi_resp.get("sourceUrl"),
            "called_at": datetime.now(timezone.utc).isoformat(),
            "bibi_success": bibi_resp.get("success", False),
            "available": success,
            "is_hallucination": False,
            "cost_duration": bibi_resp.get("costDuration", 0),
            "reason": "OK" if success else "未拿到 task_id",
            "raw": {
                "action": "create",
                "task_id": task_id_out,
                "status": bibi_resp.get("status", "unknown"),
                "title": bibi_resp.get("title", "")[:200],
            },
        }
    else:  # status
        status = bibi_resp.get("status", "unknown")
        is_done = status in ("completed", "done", "finished", "success")
        is_failed = status in ("failed", "error")
        return {
            "tool": "bibi",
            "command": "async-task",
            "url": None,
            "called_at": datetime.now(timezone.utc).isoformat(),
            "bibi_success": bibi_resp.get("success", is_done),
            "available": is_done,
            "is_hallucination": False,
            "cost_duration": bibi_resp.get("costDuration", 0),
            "reason": f"status={status}" + (" (完成)" if is_done else " (处理中)" if not is_failed else " (失败)"),
            "raw": {
                "action": "status",
                "task_id": task_id,
                "status": status,
                "summary_preview": (bibi_resp.get("summary") or "")[:200],
                "summary_length": len(bibi_resp.get("summary") or ""),
            },
        }


def judge_polish(bibi_resp: dict, url: str) -> dict:
    """polish 命令（get-polished-text，抛光字幕成文章）

    复用 hallucination 检测（polish 没字幕也会 LLM 编造）
    """
    polished_text = bibi_resp.get("polishedText") or bibi_resp.get("text") or bibi_resp.get("summary") or ""
    subs = bibi_resp.get("subtitlesArray", [])

    is_hallucination = False
    hallucination_reason = ""

    if not polished_text.strip():
        is_hallucination = True
        hallucination_reason = "polishedText 字段为空"
    else:
        for marker in HALLUCINATION_MARKERS:
            if marker in polished_text:
                is_hallucination = True
                hallucination_reason = f"包含 fallback 标志: '{marker[:30]}...'"
                break

    # 如果没字幕但有 polishedText → 几乎肯定是编造
    if not isinstance(subs, list) or len(subs) == 0:
        if polished_text.strip() and not is_hallucination:
            is_hallucination = True
            hallucination_reason = "无字幕但返回了 polishedText，疑似 LLM 编造"

    available = (not is_hallucination) and bool(polished_text.strip())

    return {
        "tool": "bibi",
        "command": "polish",
        "url": url,
        "called_at": datetime.now(timezone.utc).isoformat(),
        "bibi_success": bibi_resp.get("success", False),
        "available": available,
        "is_hallucination": is_hallucination,
        "cost_duration": bibi_resp.get("costDuration", 0),
        "reason": hallucination_reason if is_hallucination else ("OK" if available else "不可用"),
        "raw": {
            "polished_preview": polished_text[:300] if polished_text else "",
            "polished_length": len(polished_text),
            "subtitles_count": len(subs) if isinstance(subs, list) else 0,
        },
    }


# ============ 日志 ============
def _err_record(cmd: str, url, bibi_resp: dict) -> dict:
    """构造一个 error 状态的 record（避免在 main() 重复同样的字典字面量）"""
    return {
        "tool": "bibi",
        "command": cmd,
        "url": url,
        "called_at": datetime.now(timezone.utc).isoformat(),
        "bibi_success": False,
        "available": False,
        "is_hallucination": False,
        "cost_duration": 0,
        "reason": bibi_resp.get("error", "unknown error"),
        "raw": bibi_resp,
    }


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

    # 已有：get-subtitle
    p_gs = sub.add_parser("get-subtitle", help="获取视频字幕（带可用性判断）")
    p_gs.add_argument("--url", required=True)

    # 已有：summarize
    p_sm = sub.add_parser("summarize", help="总结视频（带 hallucination 检测）")
    p_sm.add_argument("--url", required=True)

    # 已有：feed
    p_fd = sub.add_parser("feed", help="抓取订阅 feed（带 failedChannels 提示）")
    p_fd.add_argument("--limit", type=int, default=50)

    # 已有：me
    sub.add_parser("me", help="查账户额度")

    # 新增 1：auth-check
    sub.add_parser("auth-check", help="检查 bibi 账户登录状态")

    # 新增 2：channel-health
    p_ch = sub.add_parser("channel-health", help="检查所有订阅频道 RSS 健康状态")
    p_ch.add_argument("--json-only", action="store_true", help="只输出 JSON 给管道用")

    # 新增 3：expand-url
    p_eu = sub.add_parser("expand-url", help="展开短链接（如 b23.tv / youtu.be）")
    p_eu.add_argument("--url", required=True)

    # 新增 4：summarize-chapter（按章节总结）
    p_sc = sub.add_parser("summarize-chapter", help="按章节总结（带 hallucination + chapters 独立判断）")
    p_sc.add_argument("--url", required=True)

    # 新增 5：async-task（创建/查询 async 总结任务，长视频用）
    p_at = sub.add_parser("async-task", help="异步任务：create 创建 / status 查询")
    p_at.add_argument("action", choices=["create", "status"], help="动作")
    p_at.add_argument("--url", help="create 时必填：视频 URL")
    p_at.add_argument("--task-id", help="status 时必填：任务 ID")

    # 新增 6：polish（抛光字幕成文章）
    p_pl = sub.add_parser("polish", help="抛光字幕为可读文章（带 hallucination 检测）")
    p_pl.add_argument("--url", required=True)

    args = parser.parse_args()

    # 调用 bibi — 重构后分发
    if args.cmd == "get-subtitle":
        bibi_resp = bibi_call(["get-subtitle", "--url", args.url, "--json"])
        record = (
            judge_get_subtitle(bibi_resp, args.url)
            if "error" not in bibi_resp
            else _err_record("get-subtitle", args.url, bibi_resp)
        )

    elif args.cmd == "summarize":
        bibi_resp = bibi_call(["summarize", args.url, "--json"])
        record = (
            judge_summarize(bibi_resp, args.url)
            if "error" not in bibi_resp
            else _err_record("summarize", args.url, bibi_resp)
        )

    elif args.cmd == "feed":
        bibi_resp = bibi_call(["feed", "--limit", str(args.limit), "--json"])
        record = (
            judge_feed(bibi_resp)
            if "error" not in bibi_resp
            else _err_record("feed", None, bibi_resp)
        )

    elif args.cmd == "me":
        bibi_resp = bibi_call(["me"])
        record = (
            judge_me(bibi_resp)
            if "error" not in bibi_resp
            else _err_record("me", None, bibi_resp)
        )

    # ── 新增命令分发 ──
    elif args.cmd == "auth-check":
        bibi_resp = bibi_call(["auth", "check"], raw=True)
        record = (
            judge_auth_check(bibi_resp.get("raw_output", ""), bibi_resp)
            if "error" not in bibi_resp
            else _err_record("auth-check", None, bibi_resp)
        )

    elif args.cmd == "channel-health":
        bibi_resp = bibi_call(["channel-health", "--json"])
        record = (
            judge_channel_health(bibi_resp)
            if "error" not in bibi_resp
            else _err_record("channel-health", None, bibi_resp)
        )

    elif args.cmd == "expand-url":
        bibi_resp = bibi_call(["expand-url", "--url", args.url, "--json"])
        record = (
            judge_expand_url(bibi_resp, args.url)
            if "error" not in bibi_resp
            else _err_record("expand-url", args.url, bibi_resp)
        )

    elif args.cmd == "summarize-chapter":
        bibi_resp = bibi_call(["summarize", args.url, "--chapter", "--json"])
        record = (
            judge_summarize_chapter(bibi_resp, args.url)
            if "error" not in bibi_resp
            else _err_record("summarize-chapter", args.url, bibi_resp)
        )

    elif args.cmd == "async-task":
        if args.action == "create":
            if not args.url:
                print("❌ async-task create 需要 --url", file=sys.stderr)
                sys.exit(1)
            bibi_resp = bibi_call(["create-summary-task", "--url", args.url, "--json"])
            record = (
                judge_async_task(bibi_resp, "create")
                if "error" not in bibi_resp
                else _err_record("async-task", args.url, bibi_resp)
            )
        else:  # status
            if not args.task_id:
                print("❌ async-task status 需要 --task-id", file=sys.stderr)
                sys.exit(1)
            bibi_resp = bibi_call(["get-summary-task-status", "--id", args.task_id, "--json"])
            if "error" not in bibi_resp:
                record = judge_async_task(bibi_resp, "status", task_id=args.task_id)
            else:
                # bibi 校验错误友好化
                stderr_text = bibi_resp.get("stderr", "")
                reason = bibi_resp["error"]
                if "Input validation failed" in stderr_text:
                    reason = "task_id 格式无效（应是 UUID，不是 fake-xxx）"
                elif "task not found" in stderr_text.lower():
                    reason = "task_id 不存在或已过期"
                record = _err_record("async-task", None, {"error": reason, "raw": bibi_resp})

    elif args.cmd == "polish":
        bibi_resp = bibi_call(["get-polished-text", "--url", args.url, "--json"])
        if "error" not in bibi_resp:
            record = judge_polish(bibi_resp, args.url)
        else:
            # polish 在无字幕时返回 "Error: No subtitles found" 等纯文本
            # 从 stderr 提取更友好的原因
            stderr_text = bibi_resp.get("stderr", "")
            reason = bibi_resp["error"]
            if "No subtitles found" in stderr_text:
                reason = "无字幕，无法 polish（这是 bibi 正常失败，不是 LLM 编造）"
            record = _err_record("polish", args.url, {"error": reason, "raw": bibi_resp})

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