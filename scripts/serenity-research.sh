#!/bin/bash
# scripts/serenity-research.sh
# 封装 serenity-skill 4 种标准 prompt
# 用法：
#   ./serenity-research.sh "<topic>" [--mode theme|company|compare|timeline]

set -e

if [ -z "$1" ]; then
  cat << 'EOF'
用法：./serenity-research.sh "<topic>" [--mode MODE]

模式：
  theme      主题研究（产业链深度调研，找 5 个优先研究标的）
  company    单公司挑战（评估单家公司，给升降级信号）
  compare    多公司对比（按产业链位置 + 证据 + 风险排序）
  timeline   时间线梳理（特定主题的发展演变）

示例：
  ./serenity-research.sh "AI 算力 8 层级" --mode theme
  ./serenity-research.sh "绿的谐波" --mode company
  ./serenity-research.sh "减速器国产替代" --mode compare
EOF
  exit 1
fi

TOPIC="$1"
MODE="${2:-theme}"
OUTPUT_DIR="$HOME/content-factory/drafts/research"
mkdir -p "$OUTPUT_DIR"

DATE=$(date +%Y-%m-%d)
HASH=$(echo "$TOPIC-$MODE" | md5sum | cut -c1-8)
OUTPUT="$OUTPUT_DIR/serenity-${MODE}-${DATE}-${HASH}.md"

# 根据模式生成 Serenity 标准 prompt
case "$MODE" in
  theme)
    PROMPT="用 serenity-skill 深度调研 ${TOPIC} 的产业链。
请联网查公告、财报、问询函、互动易、招投标、环评/能评、
专利、客户认证和财务质量，先排产业链层级，
再找 5 个最值得优先研究的标的，
并说明卡住的环节、产业链位置、证据、排序理由和主要风险。

要求：
1. 输出 8 个层级的产业链拆解
2. 每个卡点层级列出海外/国内龙头对比
3. Top 5 标的每个含 5 要素（环节/位置/原因/证据/风险）
4. 至少 25 个来源
5. 输出 markdown 格式"
    ;;
  company)
    PROMPT="用 serenity-skill 挑战 ${TOPIC}。

要求：
1. 确定该公司确切的价值链位置
2. 评估证据质量
3. 市场可能没看清的地方
4. 什么情况说明这个判断是错的（降级信号）
5. 给出研究优先级（值得研究/谨慎/避开）

输出 markdown 格式，包含：
- 公司概况
- 价值链定位
- 5 要素分析（卡住环节/位置/排序原因/证据/风险）
- 升降级信号"
    ;;
  compare)
    PROMPT="用 serenity-skill 帮我研究最近 ${TOPIC}。

要求：
1. 构建至少 20 个候选公司清单
2. 按产业链位置 + 证据强度 + 估值压力 + 风险排序
3. Top 7 每个含 5 要素
4. 包括至少一个排名较低的热门方向（解释为什么）
5. 输出 markdown 格式"
    ;;
  timeline)
    PROMPT="用 serenity-skill 帮我梳理 ${TOPIC} 的发展时间线。

要求：
1. 列出 5-10 个关键事件（政策/产品/财报/订单）
2. 按时间排序
3. 标注每个事件的 source
4. 总结时间线反映的趋势
5. 输出 markdown 格式"
    ;;
  *)
    echo "❌ 未知模式：$MODE（支持：theme/company/compare/timeline）"
    exit 1
    ;;
esac

# 输出
echo "════════════════════════════════════════"
echo "🔬 Serenity 研究 Prompt"
echo "════════════════════════════════════════"
echo ""
echo "$PROMPT"
echo ""
echo "════════════════════════════════════════"
echo "📋 调用方式（任选其一）"
echo "════════════════════════════════════════"
echo ""
echo "方式 1：直接调用（推荐）"
echo "  $ claude --print --message \"$PROMPT\""
echo ""
echo "方式 2：保存到文件 + mavis team plan"
echo "  $ mavis team plan --prompt-file $OUTPUT.prompt --output $OUTPUT"
echo ""
echo "方式 3：保存到文件 + 手动跑"
echo "  $ claude < $OUTPUT.prompt > $OUTPUT"
echo ""

# 保存
echo "$PROMPT" > "$OUTPUT.prompt"
echo "💾 Prompt 已保存：$OUTPUT.prompt"
echo "💡 跑完后结果粘贴到：$OUTPUT"