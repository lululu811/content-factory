#!/usr/bin/env bash
# content-factory 公告流水线 — cninfo-toolkit 薄封装
#
# 调用全局 `cninfo` CLI(由 cninfo-toolkit 提供),不是 scripts/cninfo-*.py。
# 前置:`pip install cninfo-toolkit` 或 `pip install -e cninfo-toolkit/`
#
# 用法:
#   bin/cninfo-pipeline.sh <topic> <code-list-file> [days]
#
# 例:
#   bin/cninfo-pipeline.sh ai-fiber-value-chain drafts/raw/ai-fiber-value-chain/companies.txt 14
#
# 输入:
#   topic           — content-factory 主题名(如 ai-fiber-value-chain)
#   code-list-file  — 文本文件,每行一个 ts_code(如 600487.SH)
#   days            — 查询最近 N 天(默认 14)
#
# 输出(全部在 drafts/raw/<topic>/cninfo/ 下):
#   <date>.json     — 公告元数据
#   pdfs/           — PDF 原文
#   extracted/      — 解析后的 JSON

set -e

# ── 参数 ──
TOPIC="${1:?usage: cninfo-pipeline.sh <topic> <code-list-file> [days]}"
CODES_FILE="${2:?usage: cninfo-pipeline.sh <topic> <code-list-file> [days]}"
DAYS="${3:-14}"

CF_ROOT="${CF_ROOT:-/Users/chenlei/content-factory}"
RAW_DIR="$CF_ROOT/drafts/raw/$TOPIC"
CNINFO_DIR="$RAW_DIR/cninfo"

# ── 颜色 ──
B="\033[1m"; G="\033[32m"; Y="\033[33m"; R="\033[31m"; N="\033[0m"

echo -e "${B}🚀 content-factory 公告流水线 (cninfo-toolkit)${N}"
echo -e "  topic:        ${Y}$TOPIC${N}"
echo -e "  codes:        ${Y}$CODES_FILE${N}"
echo -e "  days:         ${Y}$DAYS${N}"
echo -e "  output:       ${Y}$CNINFO_DIR${N}"
echo

mkdir -p "$CNINFO_DIR"

# ── Pipeline(cninfo-toolkit 全局 CLI)──
echo -e "${B}📋 cninfo pipeline 启动(anns + pdf-dl + pdf-extract)${N}"
cninfo pipeline \
  --code-file "$CODES_FILE" \
  --days "$DAYS" \
  --output-dir "$CNINFO_DIR"

echo
echo -e "${G}════════════════════════════════════════${N}"
echo -e "${G}✅ 流水线完成${N}"
echo -e "${G}════════════════════════════════════════${N}"
echo
echo -e "  📂 输出目录:${B}$CNINFO_DIR${N}"