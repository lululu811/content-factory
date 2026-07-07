# B站一手资料适配器 (content-factory-bilibili)

通过 HTTP 客户端调用本地 `bilibili_toolkit` FastAPI 服务，获取 B站字幕、弹幕、UP主动态、充电问答等一手素材。

## 前置依赖

需要启动 B站工具服务：

```bash
cd /Users/chenlei/002_tools/bilibili-subtitle-downloader
uvicorn bilibili_toolkit.server:app --host 127.0.0.1 --port 8100
```

## 环境变量

| 变量名 | 必需 | 说明 |
|---|---|---|
| `CF_BILIBILI_URL` | 否 | B站服务地址，默认 `http://127.0.0.1:8100` |
| `CF_BILIBILI_API_KEY` | 否 | API Key（对应 `BILIBILI_API_KEY`） |

## 用法

```python
from content_factory_bilibili import BilibiliDataSource

bili = BilibiliDataSource()

# 字幕
result = await bili.fetch_video_subtitle("BV1xx411c7mD")
print(result["markdown"])

# 弹幕
dm = await bili.fetch_danmaku("BV1xx411c7mD")

# UP主动态
dynamics = await bili.fetch_up_dynamics("12345678")

# 充电问答
qa = await bili.fetch_qa("12345678")
```
