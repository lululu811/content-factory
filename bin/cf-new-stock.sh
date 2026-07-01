#!/usr/bin/env bash
# content-factory 个股深度报告一键发文流程
# 用法: bin/cf-new-stock.sh <股票代码> [公司名]
# 例:   bin/cf-new-stock.sh 603688.SH 石英股份

set -e

TS_CODE="${1:?usage: cf-new-stock.sh <股票代码> [公司名]}"
COMPANY_NAME="${2:-$(echo $TS_CODE | grep -oE '^[0-9]+')}"

CF_ROOT="${CF_ROOT:-/Users/chenlei/content-factory}"
RAW_DIR="$CF_ROOT/drafts/raw/stock-$TS_CODE"
DRAFT_POST="$CF_ROOT/drafts/posts/stock-$TS_CODE.md"
FINAL="$CF_ROOT/publish/final/stock-$TS_CODE/stock-$TS_CODE.md"
TRACKING="$CF_ROOT/tracking/predictions/stock-$TS_CODE.json"

# ── 颜色 ──
B="\033[1m"; G="\033[32m"; Y="\033[33m"; R="\033[31m"; N="\033[0m"

echo -e "${B}🚀 content-factory new stock report:${N} $TS_CODE ($COMPANY_NAME)"
echo

# ── Step 1: 创建工作目录 ──
echo -e "${B}📁 Step 1 创建工作目录${N}"
mkdir -p "$RAW_DIR"
echo -e "${G}✅ 工作目录:$RAW_DIR${N}"
echo

# ── Step 2: 拉 myMCP 基础数据(股票信息 + 行情 + 财务) ──
echo -e "${B}📡 Step 2 拉 myMCP 基础数据${N}"
echo -e "${Y}👉 建议手动跑以下命令,把输出贴到 $RAW_DIR/01-mymcp-data.md:${N}"
echo "   mavis mcp call myMCP stock_basic '{\"ts_code\":\"$TS_CODE\"}'"
echo "   mavis mcp call myMCP daily '{\"ts_code\":\"$TS_CODE\",\"limit\":120}'"
echo "   mavis mcp call myMCP daily_basic '{\"ts_code\":\"$TS_CODE\",\"limit\":120}'"
echo "   mavis mcp call myMCP income '{\"ts_code\":\"$TS_CODE\",\"limit\":20}'"
echo "   mavis mcp call myMCP balancesheet '{\"ts_code\":\"$TS_CODE\",\"limit\":20}'"
echo "   mavis mcp call myMCP cashflow '{\"ts_code\":\"$TS_CODE\",\"limit\":20}'"
echo "   mavis mcp call myMCP fina_indicator '{\"ts_code\":\"$TS_CODE\",\"limit\":20}'"
echo "   mavis mcp call myMCP forecast '{\"ts_code\":\"$TS_CODE\"}'"
echo "   mavis mcp call myMCP express '{\"ts_code\":\"$TS_CODE\"}'"
echo "   mavis mcp call myMCP stk_managers '{\"ts_code\":\"$TS_CODE\"}'"
echo "   mavis mcp call myMCP stk_rewards '{\"ts_code\":\"$TS_CODE\"}'"
echo
read -p "   按回车继续(确认已保存到 01-mymcp-data.md)..."

# ── Step 3: 拉 cninfo 公告 ──
echo
echo -e "${B}📋 Step 3 拉 cninfo 公告(最近 365 天)${N}"
echo -e "${Y}👉 跑:${N}"
echo "   python3 $CF_ROOT/scripts/cninfo-anns.py --ts-code $TS_CODE --days 365 --output $RAW_DIR/02-cninfo-anns.json"
echo
read -p "   按回车继续(确认已生成 02-cninfo-anns.json)..."

# ── Step 4: 自动生成第 11 章三源对比表 ──
echo
echo -e "${B}📊 Step 4 自动生成第 11 章三源对比表${N}"
echo -e "${Y}👉 跑:${N}"
echo "   python3 $CF_ROOT/scripts/data-validator.py stock-$TS_CODE --generate-table --ts-code $TS_CODE"
echo
read -p "   按回车继续(确认第 11 章已写入草稿)..."

# ── Step 5: 模板初始化 ──
echo
echo -e "${B}📝 Step 5 模板初始化${N}"
if [ ! -f "$DRAFT_POST" ]; then
  echo -e "${Y}👉 复制模板:${N}"
  echo "   cp $CF_ROOT/templates/post-template-single-stock.md $DRAFT_POST"
  echo
  echo -e "${Y}👉 然后填充 12 章 + frontmatter:${N}"
  echo "   - title / tldr / data_sources / data_verified / zsxq_crawler"
  echo "   - 一 公司速览 / 二 投资逻辑 / 三 业务结构 / 四 行业格局"
  echo "   - 五 5 年财务 / 六 业务亮点 / 七 估值+反共识 / 八 关键风险"
  echo "   - 九 反共识判断 / 十 跟踪信号 / 十一 数据校验(自动)/ 十二 免责声明"
  read -p "   按回车继续(确认草稿完成)..."
else
  echo -e "${G}✅ 草稿已存在:$DRAFT_POST,跳过${N}"
fi

# ── Step 6: 个股完整性检查 ──
echo
echo -e "${B}🔍 Step 6 个股完整性检查(A1-S12 + A18/A19/A20)${N}"
python3 "$CF_ROOT/scripts/single-stock-completeness-check.py" "stock-$TS_CODE" --strict || {
  echo -e "${R}❌ 个股完整性检查 FAIL,需要修复后再跑${N}"
  exit 1
}

# ── Step 7: 合规检查(行业版 18 项 + 个股 3 项) ──
echo
echo -e "${B}📋 Step 7 合规检查(18 项 + A18/A19/A20)${N}"
python3 "$CF_ROOT/scripts/compliance-check.py" "stock-$TS_CODE" --strict --pre-publish || {
  echo -e "${R}❌ compliance FAIL,需要修复后再跑${N}"
  exit 1
}

# ── Step 8: 同步到 publish/final ──
echo
echo -e "${B}📤 Step 8 同步到 publish/final/${N}"
mkdir -p "$(dirname $FINAL)"
cp "$DRAFT_POST" "$FINAL"
echo -e "${G}✅ 已同步:$FINAL${N}"

# ── Step 9: tracking 初始化 ──
echo
TRACKING="$CF_ROOT/tracking/predictions/stock-$TS_CODE.json"
if [ ! -f "$TRACKING" ]; then
  echo -e "${Y}📝 创建 tracking/predictions/stock-$TS_CODE.json${N}"
  read -p "   现在创建吗?(y/N) " yn
  if [ "$yn" = "y" ]; then
    cat > "$TRACKING" <<EOT
{
  "slug": "stock-$TS_CODE",
  "ts_code": "$TS_CODE",
  "verified_date": "$(date +%Y-%m-%d)",
  "next_review": "$(date -v+90d +%Y-%m-%d 2>/dev/null || date -d '+90 days' +%Y-%m-%d 2>/dev/null || echo 2026-12-22)",
  "data_sources": ["myMCP", "cninfo", "ZsxqCrawler"],
  "predictions": [],
  "non_consensus": [],
  "followup_signals": {
    "upgrade": [],
    "downgrade": []
  }
}
EOT
    echo -e "${G}✅ 已创建 $TRACKING${N}"
  fi
else
  echo -e "${G}✅ tracking 已存在:$TRACKING${N}"
fi

# ── Step 10: 提示 commit ──
echo
echo -e "${B}📦 Step 10 提交 commit${N}"
echo "   git add drafts/posts/stock-$TS_CODE.md publish/final/stock-$TS_CODE/stock-$TS_CODE.md drafts/raw/stock-$TS_CODE/ tracking/predictions/stock-$TS_CODE.json"
echo "   git commit -m \"...\""
echo
echo -e "${G}✨ 完成!现在可以 git commit 了${N}"