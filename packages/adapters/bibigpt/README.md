# content-factory-bibigpt

BibiGPT 视频/音频摘要适配器，把任意视频/音频 URL 转为结构化摘要、完整字幕、思维导图。

## 配置

通过环境变量 `CF_BIBIGPT_TOKEN` 提供 BibiGPT API Token。

未配置时自动降级为 mock 模式，返回占位结果，方便本地开发与测试。

## 使用

```python
from content_factory_bibigpt import BibiGPTDataSource

ds = BibiGPTDataSource()
result = await ds.summarize_video("https://example.com/video.mp4")
```

## API 参考

- OpenAPI: <https://bibigpt.co/api/openapi.json>
- Base URL: `https://api.bibigpt.co/api`
