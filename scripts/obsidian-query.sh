#!/bin/bash
# scripts/obsidian-query.sh
# 封装 Obsidian /query skill 调用
# 用法：
#   ./obsidian-query.sh "<query>" [--mode fast|deep|cross|timeline]

set -e

if [ -z "$1" ]; then
  cat << 'EOF'
用法：./obsidian-query.sh "<query>" [--mode MODE]

模式：
  fast       标题级快查（5 秒，5-8 条 sources）
  deep       深度综合（30 秒，10-15 条 sources + 概念 + 实体）
  cross      跨 MOC 综合（2-5 分钟）
  timeline   时间线（按日期排序 5-8 个事件）

示例：
  ./obsidian-query.sh "AI 算力 2026 H1 最新进展" --mode fast
  ./obsidian-query.sh "稀土 价格 供需" --mode deep
  ./obsidian-query.sh "AI + 半导体 跨链" --mode cross

输出：
  - 在 Claude/Codex/Hermes 中执行的 prompt
  - 或通过 mavis team plan 自动调用
EOF
  exit 1
fi

QUERY="$1"
MODE="${2:-deep}"
TOPIC_DIR="$HOME/content-factory/drafts/research"
mkdir -p "$TOPIC_DIR"

# 生成时间戳文件名
DATE=$(date +%Y-%m-%d)
HASH=$(echo "$QUERY" | md5sum | cut -c1-8)
OUTPUT="$TOPIC_DIR/${MODE}-${DATE}-${HASH}.md"

# 根据模式生成 prompt
case "$MODE" in
  fast)
    PROMPT="/query \"${QUERY}\"
要求：
1. 在知识库中检索相关 sources
2. 列出 5-8 条最相关的（按相关性排序）
3. 每条用 1 句话概括核心观点
4. 标注每条的 source 文件名
输出：markdown 表格"
    ;;
  deep)
    PROMPT="/query \"${QUERY}\"
要求（深度综合）：
1. 列出 10-15 条核心 sources（按主题相关性排序）
2. 列出 5-10 个关键概念（用 [[wikilink]] 格式）
3. 列出涉及的 3-5 个实体（公司/人物/工具）
4. 总结这些 sources 的核心共识和分歧
5. 指出还有哪些方向 sources 覆盖不足
输出：markdown 格式"
    ;;
  cross)
    PROMPT="/query \"${QUERY}\"
要求（跨 MOC 综合）：
1. 跨多个 MOC 检索
2. 列出 10-15 条 sources
3. 覆盖所有相关 MOC
4. 标注每条的 MOC 归属
输出：markdown 格式"
    ;;
  timeline)
    PROMPT="/query \"${QUERY}\"
要求（时间线）：
1. 按时间排序 5-8 个关键事件/政策/数据点
2. 每个事件标注日期
3. 标注 source
4. 总结时间线反映的趋势
输出：markdown 格式"
    ;;
  *)
    echo "❌ 未知模式：$MODE（支持：fast/deep/cross/timeline）"
    exit 1
    ;;
esac

# 调用方式 1：直接打印给用户复制
echo "════════════════════════════════════════"
echo "📚 Obsidian /query Prompt"
echo "════════════════════════════════════════"
echo ""
echo "$PROMPT"
echo ""
echo "════════════════════════════════════════"
echo "📋 调用方式（任选其一）"
echo "════════════════════════════════════════"
echo ""
echo "方式 1：在 Claude Code / Codex / Hermes 中执行"
echo "  $ claude --print --message \"$PROMPT\""
echo ""
echo "方式 2：通过 mavis team plan（推荐）"
echo "  $ mavis team plan --prompt \"$PROMPT\" --output \"$OUTPUT\""
echo ""
echo "方式 3：通过 mavis communication"
SESSION_ID=$(echo $HOME | md5sum | cut -c1-16)
echo "  $ mavis communication send --to <your-session> --command prompt --content \"$PROMPT\""
echo ""

# 保存 prompt 到文件，方便复跑
echo "$PROMPT" > "$OUTPUT.prompt"
echo "💾 Prompt 已保存到：$OUTPUT.prompt"
echo "💡 跑完后把结果粘贴到：$OUTPUT"