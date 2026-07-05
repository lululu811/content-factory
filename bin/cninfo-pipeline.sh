#!/usr/bin/env bash
# content-factory 公告流水线 — 通用 cninfo 工具的薄封装
#
# 把 scripts/cninfo-{anns,pdf-dl,pdf-extract}.py 三个通用工具
# 串成 content-factory 项目内的一键流水线。
#
# 用法:
#   bin/cninfo-pipeline.sh <topic> <code-list-file> [days]
#
# 例:
#   bin/cninfo-pipeline.sh ai-fiber-value-chain drafts/raw/ai-fiber-value-chain/companies.txt 14
#
# 输入:
#   topic        — content-factory 主题名(如 ai-fiber-value-chain)
#   code-list-file — 文本文件,每行一个 ts_code(如 600487.SH)
#   days         — 查询最近 N 天(默认 14)
#
# 输出(全部在 drafts/raw/<topic>/cninfo/ 下):
#   anns/{YYYY-MM-DD}.json   — 公告元数据
#   pdfs/                    — PDF 原文
#   extracted/               — 解析后的 JSON
#   manifest.json            — 下载清单
#
# 设计原则:
#   - **薄封装**:不重新发明轮子,只调用通用工具
#   - **可单独运行**:脚本里的 3 步也可用通用工具直接调
#   - **失败可恢复**:每一步都有 skip-existing,可断点续跑

set -e

# ── 参数 ──
TOPIC="${1:?usage: cninfo-pipeline.sh <topic> <code-list-file> [days]}"
CODES_FILE="${2:?usage: cninfo-pipeline.sh <topic> <code-list-file> [days]}"
DAYS="${3:-14}"

CF_ROOT="${CF_ROOT:-/Users/chenlei/content-factory}"
RAW_DIR="$CF_ROOT/drafts/raw/$TOPIC"
CNINFO_DIR="$RAW_DIR/cninfo"
PDFS_DIR="$CNINFO_DIR/pdfs"
EXTRACTED_DIR="$CNINFO_DIR/extracted"
TODAY="$(date +%Y-%m-%d)"

# ── 颜色 ──
B="\033[1m"; G="\033[32m"; Y="\033[33m"; R="\033[31m"; N="\033[0m"

echo -e "${B}🚀 content-factory 公告流水线${N}"
echo -e "  topic:        ${Y}$TOPIC${N}"
echo -e "  codes:        ${Y}$CODES_FILE${N}"
echo -e "  days:         ${Y}$DAYS${N}"
echo -e "  output:       ${Y}$CNINFO_DIR${N}"
echo

# ── 准备 ──
mkdir -p "$PDFS_DIR" "$EXTRACTED_DIR"

# ── Step 1: 拉公告元数据 ──
echo -e "${B}📋 Step 1: 拉公告元数据 (cninfo-anns.py)${N}"
ANNS_FILE="$CNINFO_DIR/$TODAY.json"
python3 "$CF_ROOT/scripts/cninfo-anns.py" \
  --code-file "$CODES_FILE" \
  --days "$DAYS" \
  --json \
  --output "$ANNS_FILE"

# 统计
TOTAL=$(python3 -c "
import json
with open('$ANNS_FILE') as f:
    d = json.load(f)
print(sum(len(v) for v in d.values()))
")
COMPANIES=$(python3 -c "
import json
with open('$ANNS_FILE') as f:
    d = json.load(f)
print(len(d))
")
echo -e "${G}✅ Step 1 完成:$COMPANIES 家公司,$TOTAL 条公告${N}"
echo

# ── Step 2: 下载 PDF ──
echo -e "${B}⬇️  Step 2: 下载 PDF (cninfo-pdf-dl.py)${N}"
python3 "$CF_ROOT/scripts/cninfo-pdf-dl.py" \
  --anns "$ANNS_FILE" \
  --output-dir "$PDFS_DIR" \
  --skip-existing

echo -e "${G}✅ Step 2 完成${N}"
echo

# ── Step 3: 解析 PDF ──
echo -e "${B}📄 Step 3: 解析 PDF (cninfo-pdf-extract.py)${N}"
MANIFEST_FILE="$PDFS_DIR/manifest.json"
if [ -f "$MANIFEST_FILE" ]; then
  python3 "$CF_ROOT/scripts/cninfo-pdf-extract.py" \
    --manifest "$MANIFEST_FILE" \
    --output-dir "$EXTRACTED_DIR" \
    --skip-existing
else
  echo -e "${Y}⚠️  manifest.json 不存在,跳过 Step 3${N}"
fi

echo
echo -e "${G}════════════════════════════════════════${N}"
echo -e "${G}✅ 流水线完成${N}"
echo -e "${G}════════════════════════════════════════${N}"
echo
echo -e "  📂 输出目录:${B}$CNINFO_DIR${N}"
echo -e "  📋 公告清单:${B}$ANNS_FILE${N}"
echo -e "  📁 PDF 目录:${B}$PDFS_DIR${N}"
echo -e "  📄 解析目录:${B}$EXTRACTED_DIR${N}"