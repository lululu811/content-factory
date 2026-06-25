#!/bin/bash
# scripts/quarterly-review.sh
# 季度回看自动化 + 提醒推送
# cron: 0 9 1 */3 * /Users/chenlei/content-factory/scripts/quarterly-review.sh
#       (每季度首月 1 号 9:00 跑)

set -e

# 注入 cron 环境变量路径
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"

WORKDIR=$HOME/content-factory
PYTHON=python3
SCRIPT_DIR=$WORKDIR/scripts

# 输出目录
REPORT_DIR=$WORKDIR/tracking/reports
DATE_STAMP=$(date +%Y%m%d)
QUARTER=$(date +%Y-Q$(( ($(date +%-m) - 1) / 3 + 1 )))
mkdir -p "$REPORT_DIR"

LOG=$REPORT_DIR/quarterly-review-$DATE_STAMP.log

echo "════════════════════════════════════════════════════" | tee -a $LOG
echo "📅 季度回看 · $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $LOG
echo "════════════════════════════════════════════════════" | tee -a $LOG

# 1. 列出到期未验证的预测
echo "" | tee -a $LOG
echo "▶ Step 1: 检查到期未验证的预测" | tee -a $LOG
echo "────────────────────────────────────────────────────" | tee -a $LOG
DUE_OUTPUT=$($PYTHON $SCRIPT_DIR/verify-predictions.py --check-due 2>&1)
echo "$DUE_OUTPUT" | tee -a $LOG

DUE_COUNT=$(echo "$DUE_OUTPUT" | grep -c "└──" || true)
echo "" | tee -a $LOG
echo "  → 到期未验证预测数: $DUE_COUNT" | tee -a $LOG

# 2. 生成季度战绩表
echo "" | tee -a $LOG
echo "▶ Step 2: 生成季度战绩表 markdown" | tee -a $LOG
echo "────────────────────────────────────────────────────" | tee -a $LOG
REPORT_FILE=$REPORT_DIR/战绩表-${QUARTER}-$DATE_STAMP.md
$PYTHON $SCRIPT_DIR/verify-predictions.py --generate-report --quarter > "$REPORT_FILE" 2>&1
echo "  → 季度报告: $REPORT_FILE" | tee -a $LOG
echo "  → 大小: $(wc -l < "$REPORT_FILE" 2>/dev/null || echo 0) 行" | tee -a $LOG

# 3. 检查每篇文章的合规状态(可选但推荐)
echo "" | tee -a $LOG
echo "▶ Step 3: 抽查最近 3 篇文章的合规状态" | tee -a $LOG
echo "────────────────────────────────────────────────────" | tee -a $LOG
COMPLIANCE_FAILED=0
for draft in $(ls -t $WORKDIR/drafts/posts/*.md 2>/dev/null | head -3); do
    slug=$(basename "$draft" .md)
    if $PYTHON $SCRIPT_DIR/compliance-check.py "$slug" --strict --pre-publish > /tmp/comp-$slug.log 2>&1; then
        echo "  ✅ $slug: 合规通过" | tee -a $LOG
    else
        echo "  ❌ $slug: 合规未通过(见 /tmp/comp-$slug.log)" | tee -a $LOG
        COMPLIANCE_FAILED=$((COMPLIANCE_FAILED + 1))
    fi
done

# 4. 推送摘要到 console / 飞书(留 hook,默认 console)
echo "" | tee -a $LOG
echo "▶ Step 4: 季度回看摘要" | tee -a $LOG
echo "────────────────────────────────────────────────────" | tee -a $LOG

if [ "$DUE_COUNT" -gt 0 ] || [ "$COMPLIANCE_FAILED" -gt 0 ]; then
    SUMMARY="🚨 季度回看需要处理:
- 到期待验证预测: $DUE_COUNT 条
- 最近文章合规未通过: $COMPLIANCE_FAILED 篇
- 完整报告: $REPORT_FILE
- 详细日志: $LOG"
else
    SUMMARY="✅ 季度回看正常:
- 到期待验证预测: 0 条(都还没到期)
- 最近文章合规: 全部通过
- 战绩表: $REPORT_FILE"
fi

echo "$SUMMARY" | tee -a $LOG

# 5. (可选) 推送飞书 webhook - 默认禁用,需用户配置
# FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/XXXXX"
# if [ -n "$FEISHU_WEBHOOK_URL" ]; then
#     curl -X POST -H "Content-Type: application/json" \
#         -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$SUMMARY\"}}" \
#         "$FEISHU_WEBHOOK_URL" > /dev/null
#     echo "  → 飞书推送完成" | tee -a $LOG
# fi

echo "" | tee -a $LOG
echo "🎉 季度回看完成 · 下次运行: 下季度首月 1 号 09:00" | tee -a $LOG
echo "════════════════════════════════════════════════════" | tee -a $LOG

# 注意:log 已经在 REPORT_DIR 下,无需再 mv