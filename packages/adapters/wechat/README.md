# content-factory-wechat

微信公众号发布适配器。

## 配置

环境变量：
- `CF_WECHAT_APPID`: 公众号 AppID
- `CF_WECHAT_SECRET`: 公众号 Secret

## 使用

```python
from content_factory_wechat import WechatPublisher

publisher = WechatPublisher()
event = await publisher.publish(article)
print(event.publish_url)
```

## 流程

1. 获取 access_token（带 7000 秒缓存）
2. 上传图文消息素材（media_id）
3. 提交发布（publish_id）

未配置环境变量时使用 mock 模式。
