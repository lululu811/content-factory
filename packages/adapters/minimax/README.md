# MiniMax (妙想 AI) 多模态生成适配器

MiniMax 多模态生成服务的内容工厂适配器，支持图片 / 视频 / 音乐 / 语音四种内容类型的 AI 生成。

## 支持的内容类型

| 类型 | 方法 | 说明 |
|------|------|------|
| `image` | `generate_image` | 文生图 / 图生图 |
| `video` | `generate_video` | 文生视频 / 图生视频 |
| `music` | `generate_music` | 音乐生成（带词 / 纯音乐） |
| `speech` | `generate_speech` | 语音合成 (TTS) |

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `CF_MINIMAX_API_KEY` | 是 | MiniMax API 密钥 |
| `CF_MINIMAX_GROUP_ID` | 是 | MiniMax Group ID |

**未配置时自动降级为 mock 模式**，返回占位 URL，便于本地开发和测试。

## 使用示例

```python
from content_factory_minimax import MiniMaxGenerator
import asyncio

gen = MiniMaxGenerator()

# 通过统一入口 generate() 按 type 分发
result = asyncio.run(gen.generate(
    "赛博朋克风格的猫",
    params={"type": "image"}
))
print(result["url"])

# 也可以直接调用具体方法
result = asyncio.run(gen.generate_speech("Hello, world!"))
```

## SPI 集成

实现 `ContentGeneratorProvider` SPI，通过 entry point `content_factory.content_generators` 注册为 `minimax`。
