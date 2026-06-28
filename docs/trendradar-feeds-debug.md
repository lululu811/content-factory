# TrendRadar 7 个未拉通 feed 排查报告(2026/6/28)

> **问题**:TrendRadar `config.yaml` 注册 49 个 feed,但 `rss_feeds` 表只有 44 个,缺 7 个未抓到数据。
> **排查人**:Mavis
> **解决状态**:已加入 `scripts/paused-channels.txt` 暂停名单,等用户手动修 RSSHub/wewe-rss 通路。

---

## 一、缺失的 7 个 feed

| Feed ID | 名称 | 类型 | URL |
|---|---|---|---|
| `ruanyifeng` | 阮一峰的网络日志 | 博客 RSS | (config.yaml) |
| `wechat-bdtcygc` | 半导体行业观察 | 微信公众号 | `https://wechat.zknowledge.site/feeds/MP_WXS_3864835480.rss` |
| `wechat-htzqcl` | 华泰证券策略研究 | 微信公众号 | `https://wechat.zknowledge.site/feeds/MP_WXS_3924429173.rss` |
| `wechat-kdcc` | 看懂产业链 | 微信公众号 | `https://wechat.zknowledge.site/feeds/MP_WXS_3707226911.rss` |
| `wechat-tfyanjiu` | 天风研究 | 微信公众号 | `https://wechat.zknowledge.site/feeds/MP_WXS_3003237702.rss` |
| `wechat-yckjpl` | 远川科技评论 | 微信公众号 | `https://wechat.zknowledge.site/feeds/MP_WXS_3570917737.rss` |
| `wechat-zgzqb` | 中国证券报 | 微信公众号 | `https://wechat.zknowledge.site/feeds/MP_WXS_2393306340.rss` |

---

## 二、根因分析

**TrendRadar 的 rss_feeds 表注册逻辑**(代码位置:`trendradar/storage/sqlite_mixin.py`):

```python
# 同步 RSS 源信息到 rss_feeds 表
for feed_id, feed_name in data.id_to_name.items():
    cursor.execute("""
        INSERT INTO rss_feeds (id, name, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET ...
    """, (feed_id, feed_name, now_str))
```

**关键发现**:`id_to_name` 不是从 `config.yaml` 静态读取,而是**从本次 RSS 抓取的结果**动态获取。

**含义**:
- config.yaml 里注册 ≠ 一定进 rss_feeds 表
- 必须**实际抓到 RSS 文章**,才会被注册
- 抓不到 → 不在表里 → 也不会被 AI 筛选

**结论**:**这 7 个 feed 的 RSS 抓取本身失败**(RSSHub / wewe-rss 服务端拉不到),不是 TrendRadar 自身的 bug。

---

## 三、可能的具体失败原因

### A. 微信公众号(6 个)
- **可能性 1**:wewe-rss 服务端 `wechat.zknowledge.site` **没有收录这些公众号**(可能未订阅或服务到期)
- **可能性 2**:公众号 ID 失效(被封号/改名)
- **可能性 3**:wewe-rss API 接口变更
- **建议验证**:
  ```bash
  # 浏览器打开 RSS URL 看返回
  curl -v "https://wechat.zknowledge.site/feeds/MP_WXS_3924429173.rss"
  # 或浏览器访问 wechat.zknowledge.site 后台看订阅列表
  ```

### B. ruanyifeng 博客
- **可能性 1**:RSSHub 路径变更(`/ruanyifeng/weekly` 可能改名)
- **建议验证**:
  ```bash
  # 看 RSSHub 支持的 ruanyifeng 路径
  curl "https://rsshub.zknowledge.site/ruanyifeng"
  ```

---

## 四、对比已拉通的 4 个微信公众号

config.yaml 里其他 4 个微信公众号正常抓到数据:
- `wechat-wsj` 华尔街见闻(WXS_2397003540)
- `wechat-bdt` 半导体产业纵横(WXS_3912227540)
- `wechat-tmt` TMT 研究院(WXS_3911732113)
- `wechat-cytouyan` 产业投研院(WXS_3873823266)

→ 同样的 `wechat.zknowledge.site/feeds/MP_WXS_*.rss` 模式能拉通,说明**服务端没问题**。
→ **未拉通的 6 个公众号 ID 可能服务端没收录**(待用户去 wechat.zknowledge.site 后台验证)。

---

## 五、临时解决方案(已落地)

### 1. 加入 paused 名单
文件:`scripts/paused-channels.txt` 末尾追加段:

```
# --- TrendRadar feed RSSHub/wewe-rss 抓取失败(2026/6/28 排查) ---
wechat-bdtcygc:半导体行业观察
wechat-htzqcl:华泰证券策略研究
wechat-kdcc:看懂产业链
wechat-tfyanjiu:天风研究
wechat-yckjpl:远川科技评论
wechat-zgzqb:中国证券报
ruanyifeng:阮一峰的网络日志
```

### 2. SOP 4.1.1 / data-source-hierarchy.md 已标注
"6 个微信公众号在 config.yaml 里注册但今日未拉到数据(需排查 RSSHub 通路)→ 默认加入 paused 名单"

---

## 六、用户手动修复步骤

### 修 RSSHub / wewe-rss 通路

```bash
# 1. 浏览器访问 wechat.zknowledge.site 后台
#    - 看订阅列表是否有这 6 个公众号
#    - 如果没有,重新添加订阅
#    - 如果有,检查 RSS feed URL 是否 200

# 2. 验证单个 RSS URL
curl -sL "https://wechat.zknowledge.site/feeds/MP_WXS_3924429173.rss" | head -20
# 期望:XML 格式 + 至少 1 个 <item>

# 3. 修好后,删除 paused 名单里的对应行
# 4. 重新跑 TrendRadar:
cd ~/001_project/TrendRadar && python3 main.py --now
# 5. 验证 rss_feeds 表是否更新:
python3 -c "
import sqlite3, os
c = sqlite3.connect(os.path.expanduser('~/001_project/TrendRadar/output/rss/2026-06-28.db'))
print(c.execute('SELECT COUNT(*) FROM rss_feeds').fetchone()[0])
"
# 期望从 44 → 50
```

---

## 七、相关文件

- `~/001_project/TrendRadar/config/config.yaml` — 49 个 feed 注册
- `~/001_project/TrendRadar/output/rss/2026-06-28.db` — 44 个 rss_feeds(实际抓到的)
- `~/001_project/TrendRadar/trendradar/storage/sqlite_mixin.py` — rss_feeds 注册逻辑
- `~/content-factory/scripts/paused-channels.txt` — 暂停名单(已加 7 个)
- `~/content-factory/SOP.md` 4.1.1 — TrendRadar 章节(已刷新到 44 个)
- `~/content-factory/docs/data-source-hierarchy.md` — TrendRadar 行(已刷新)