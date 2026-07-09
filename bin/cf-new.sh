#!/usr/bin/env bash
# content-factory 一键发文流程(半自动)
# 用法: bin/cf-new.sh <slug> <topic>
# 例:   bin/cf-new.sh ai-server-power "AI 服务器电源"

set -e
SLUG="${1:?usage: cf-new.sh <slug> <topic>}"
TOPIC="${2:?usage: cf-new.sh <slug> <topic>}"
CF_ROOT="${CF_ROOT:-$HOME/content-factory}"
RAW_DIR="$CF_ROOT/drafts/raw/$SLUG"
DRAFT_POST="$CF_ROOT/drafts/posts/$SLUG.md"
FINAL="$CF_ROOT/publish/final/$SLUG/$SLUG.md"

# ── 颜色 ──
B="\033[1m"; G="\033[32m"; Y="\033[33m"; R="\033[31m"; N="\033[0m"

echo -e "${B}🚀 content-factory new article:${N} $SLUG ($TOPIC)"
echo

# ── Step 0: 白名单初始化(首次) ──
if [ ! -f ~/.cache/a-stock-names.json ]; then
  echo -e "${Y}⚠️  A 股白名单不存在,先拉全 A 股名单...${N}"
  python3 "$CF_ROOT/scripts/industry-kol-scan.py" --setup-whitelist
fi

# ── Step 1: Step 3 行业情报扫描 ──
echo -e "${B}📡 Step 3 行业情报扫描${N}"
mkdir -p "$RAW_DIR"
if [ -f "$RAW_DIR/00-kol-scan.md" ]; then
  echo -e "${G}✅ 已有 $RAW_DIR/00-kol-scan.md,跳过${N}"
else
  echo -e "${Y}👉 需要 web_search 15+ 条结果,保存到 /tmp/${SLUG}-search.json${N}"
  echo "   然后跑:"
  echo "   python3 $CF_ROOT/scripts/industry-kol-scan.py \\"
  echo "     --topic \"$TOPIC\" --slug $SLUG \\"
  echo "     --input /tmp/${SLUG}-search.json"
  echo
  read -p "   按回车继续 (确认已生成 00-kol-scan.md)..."
  [ -f "$RAW_DIR/00-kol-scan.md" ] || { echo -e "${R}❌ 还没生成 00-kol-scan.md,退出${N}"; exit 1; }
fi

# ── Step 2: 用户决定 A2 候选公司 ──
echo
echo -e "${B}📋 Step 2 A2 候选公司 20/30 家(用户决定)${N}"
echo -e "${Y}👉 阅读 $RAW_DIR/00-kol-scan.md,确定候选公司 + 5 分类,写入 $DRAFT_POST"
echo -e "${Y}👉 同时跑 myMCP + cninfo 拉数据:${N}"
echo "   mavis mcp call myMCP daily '{\"trade_date\":\"20260626\"}'  # 逐家"
echo "   python3 $CF_ROOT/scripts/cninfo-anns.py --ts-code XXX.SH --days 14"
echo
read -p "   按回车继续 (确认已写完 drafts/posts/${SLUG}.md + 5 张图)..."

# ── Step 3: 合规检查 ──
echo
echo -e "${B}🔍 Step 3 compliance-check.py 合规检查${N}"
python3 "$CF_ROOT/scripts/compliance-check.py" "$SLUG" || {
  echo -e "${R}❌ compliance FAIL,需要修复后再跑${N}"
  exit 1
}

# ── Step 4: 同步到 publish/final ──
echo
echo -e "${B}📤 Step 4 同步到 publish/final/${N}"
mkdir -p "$(dirname $FINAL)"
cp "$DRAFT_POST" "$FINAL"
echo -e "${G}✅ 已同步: $FINAL${N}"

# ── Step 5: tracking 初始化(如果没) ──
echo
TRACKING="$CF_ROOT/tracking/predictions/$SLUG.json"
if [ ! -f "$TRACKING" ]; then
  echo -e "${Y}📝 创建 tracking/predictions/$SLUG.json(可手动填 Top 7 + 升级/降级信号)${N}"
  read -p "   现在创建吗?(y/N) " yn
  if [ "$yn" = "y" ]; then
    cat > "$TRACKING" <<EOT
{
  "slug": "$SLUG",
  "verified_date": "$(date +%Y-%m-%d)",
  "next_review": "$(date -v+90d +%Y-%m-%d 2>/dev/null || date -d '+90 days' +%Y-%m-%d 2>/dev/null || echo 2026-12-22)",
  "top_companies": [],
  "upgrade_signals": [],
  "downgrade_signals": []
}
EOT
    echo -e "${G}✅ 已创建 $TRACKING${N}"
  fi
else
  echo -e "${G}✅ tracking 已存在: $TRACKING${N}"
fi

# ── Step 6: 提示 commit ──
echo
echo -e "${B}📦 Step 6 提交 commit${N}"
echo "   git add drafts/posts/$SLUG.md publish/final/$SLUG/$SLUG.md drafts/raw/$SLUG/ tracking/predictions/$SLUG.json"
echo "   git commit -m \"...\""
echo
echo -e "${G}✨ 完成!现在可以 git commit 了${N}"