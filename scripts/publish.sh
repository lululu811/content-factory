#!/bin/bash
# scripts/publish.sh
# 一键打包发布（v2 标准）
# 用法：./scripts/publish.sh <slug>

set -e

if [ -z "$1" ]; then
  echo "用法：$0 <slug>"
  echo "示例：$0 morgan-ai-supply-chain"
  exit 1
fi

SLUG=$1
DATE=$(date +%Y-%m-%d)
WORKDIR="${CF_ROOT:-$HOME/content-factory}"
SRC_DRAFTS=$WORKDIR/drafts/posts
SRC_IMAGES=$WORKDIR/publish/images/$SLUG
FINAL_DIR=$WORKDIR/publish/final/$SLUG
ARCHIVE_DIR=$WORKDIR/archives/$(date +%Y-%m)

echo "════════════════════════════════════════════════════"
echo "🚀 发布打包：$SLUG"
echo "════════════════════════════════════════════════════"

# 0. 发布前合规检查(v3 · 14 项 + --strict:任意 FAIL exit 1)
if [ -f "$WORKDIR/scripts/compliance-check.py" ]; then
    if ! python3 "$WORKDIR/scripts/compliance-check.py" "$SLUG" --strict --pre-publish > /dev/null 2>&1; then
        echo "❌ 合规检查未通过,请修复后再发布:"
        python3 "$WORKDIR/scripts/compliance-check.py" "$SLUG" --pre-publish
        exit 1
    fi
    echo "✅ 合规检查通过"
fi

# 1. 创建发布目录
mkdir -p $FINAL_DIR/images $ARCHIVE_DIR

# 2. 复制文章 markdown
if [ ! -f "$SRC_DRAFTS/$SLUG.md" ]; then
  echo "❌ 文章不存在：$SRC_DRAFTS/$SLUG.md"
  exit 1
fi
cp $SRC_DRAFTS/$SLUG.md $FINAL_DIR/$SLUG.md
echo "✅ 复制文章：$SLUG.md"

# 3. 复制封面图
if [ -d "$SRC_IMAGES/cover-v2" ]; then
  cp $SRC_IMAGES/cover-v2/image_002.jpg $FINAL_DIR/images/cover.jpg 2>/dev/null || \
    cp $(ls $SRC_IMAGES/cover-v2/image_*.jpg | head -1) $FINAL_DIR/images/cover.jpg
  echo "✅ 复制封面"
elif [ -d "$SRC_IMAGES/cover" ]; then
  cp $(ls $SRC_IMAGES/cover/image_*.jpg | head -1) $FINAL_DIR/images/cover.jpg
  echo "✅ 复制封面"
fi

# 4. 复制所有信息图
if [ -d "$SRC_IMAGES/charts" ]; then
  IMG_COUNT=$(ls $SRC_IMAGES/charts/*.png 2>/dev/null | wc -l)
  cp $SRC_IMAGES/charts/*.png $FINAL_DIR/images/ 2>/dev/null
  echo "✅ 复制 $IMG_COUNT 张信息图"
fi

# 5. 归档
cp $FINAL_DIR/$SLUG.md $ARCHIVE_DIR/${SLUG}-$(date +%Y%m%d).md
echo "✅ 归档到：$ARCHIVE_DIR"

# 6. 修正图片路径为相对路径
sed -i '' 's|images/cover-v2/image_002.jpg|images/cover.jpg|g' $FINAL_DIR/$SLUG.md
sed -i '' 's|charts/|images/|g' $FINAL_DIR/$SLUG.md

# 7. 生成发布说明
cat > $FINAL_DIR/发布说明.md << 'EOF'
# 发布说明 · <SLUG>

## 📋 发布检查清单

- [ ] 标题在公众号编辑器里再次核对
- [ ] 封面图上传到公众号（900×383 比例）
- [ ] 文章中的 5 张图上传到公众号素材库
- [ ] 替换文章内图片引用为公众号的图文链接
- [ ] 摘要/封面引导语
- [ ] 原创声明（如需要）
- [ ] 留言区互动引导

## 📁 文件清单

参见本目录下的 $SLUG.md 和 images/ 子目录。

## 🎯 推荐发布信息

**首发平台**：公众号
**首发时间**：建议周二/周四 20:00

## 📌 同步发布

- **知乎**（2-3 天后）：选相关话题回答
- **即刻**（当天）：短内容钩子（核心判断 + 链接）
- **小红书**（当天）：图表卡片 2-3 张
- **B 站**（可选）：如果做视频，复用素材

## ⚠️ 合规自检

发布前必查：
- [ ] 全文免责声明已加（中版本）
- [ ] 证据等级标注完整（🟢🟡🔴）
- [ ] 没有"目标价/推荐/保证/加仓/稳赚"等高风险词
- [ ] 数据源已更新到 2026 H1
- [ ] 提及的公司都是"研究案例"标注
EOF

# 替换 slug
sed -i '' "s|<SLUG>|$SLUG|g" $FINAL_DIR/发布说明.md

echo "✅ 生成发布说明"

# 7.5 自动记录跟踪数据到 tracking/predictions/
if [ -f "$WORKDIR/scripts/tracking-record.py" ]; then
  python3 "$WORKDIR/scripts/tracking-record.py" add "$SLUG" >/dev/null 2>&1 || true
  echo "✅ 自动生成并写入跟踪记录到 predictions/$SLUG.json"
fi

# 8. 输出最终包结构
echo ""
echo "════════════════════════════════════════"
echo "📦 发布包结构"
echo "════════════════════════════════════════"
find $FINAL_DIR -type f | sort | while read f; do
  rel=${f#$FINAL_DIR/}
  size=$(ls -la "$f" | awk '{print $5}')
  printf "  %-50s %s KB\n" "$rel" "$((size/1024))"
done

# 9. 验证
echo ""
echo "════════════════════════════════════════"
echo "📊 最终验证"
echo "════════════════════════════════════════"
echo "字数：$(wc -m < $FINAL_DIR/$SLUG.md) 字符"
echo "图片引用："
grep -E "!\[" $FINAL_DIR/$SLUG.md | sed 's/.*!\[\([^]]*\).*/  - \1/'

echo ""
echo "🎉 发布包已就绪：$FINAL_DIR"
echo ""
echo "下一步："
echo "  1. 打开 $FINAL_DIR/$SLUG.md"
echo "  2. 复制内容到公众号编辑器"
echo "  3. 上传图片到公众号素材库"
echo "  4. 替换图片引用"
echo "  5. 预览 → 发布"