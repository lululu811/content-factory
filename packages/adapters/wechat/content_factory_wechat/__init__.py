"""
微信公众号发布适配器

通过微信公众号 API 发布文章：
  1. 获取 access_token（缓存 7000 秒）
  2. 上传图文消息素材（media_id）
  3. 发布草稿 / 群发

需要环境变量:
  CF_WECHAT_APPID   - 公众号 AppID
  CF_WECHAT_SECRET  - 公众号 Secret

未配置时使用 mock 实现（用于开发/测试）。
"""
import os
import time
from typing import Any

import httpx
import structlog

from content_factory_core.events import ArticlePublished
from content_factory_core.models import Article
from content_factory_sdk.spi import PublisherProvider

logger = structlog.get_logger()


class WechatPublisher(PublisherProvider):
    """微信公众号发布器"""

    API_BASE = "https://api.weixin.qq.com/cgi-bin"

    def __init__(
        self,
        appid: str | None = None,
        secret: str | None = None,
    ) -> None:
        self.appid = appid or os.getenv("CF_WECHAT_APPID")
        self.secret = secret or os.getenv("CF_WECHAT_SECRET")
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._client: httpx.AsyncClient | None = None

        if self.appid and self.secret:
            logger.info("wechat_initialized", appid=self.appid[:6] + "***")
        else:
            logger.warning(
                "wechat_no_credentials",
                msg="未配置 CF_WECHAT_APPID/CF_WECHAT_SECRET，使用 mock 模式",
            )

    @property
    def is_mock(self) -> bool:
        return not (self.appid and self.secret)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0, trust_env=False)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get_access_token(self) -> str:
        """
        获取 access_token（带缓存）

        微信 access_token 有效期 7200 秒，这里提前 200 秒刷新。
        """
        now = time.time()
        if self._access_token and now < self._token_expires_at - 200:
            return self._access_token

        client = await self._get_client()
        url = f"{self.API_BASE}/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.secret,
        }
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        if "access_token" not in data:
            raise RuntimeError(f"WeChat API error: {data}")

        self._access_token = data["access_token"]
        self._token_expires_at = now + data.get("expires_in", 7200)
        logger.info("wechat_token_refreshed", expires_in=data.get("expires_in"))
        return self._access_token

    async def _upload_news(self, article: Article) -> str:
        """上传图文消息素材，返回 media_id"""
        token = await self._get_access_token()
        client = await self._get_client()

        url = f"{self.API_BASE}/media/uploadnews?access_token={token}"
        payload = {
            "articles": [
                {
                    "title": article.title,
                    "thumb_media_id": "",  # 封面图 media_id（可后续扩展）
                    "author": "AI 编辑部",
                    "digest": article.content[:120],
                    "show_cover_pic": 0,
                    "content": article.content,
                    "content_source_url": "",
                }
            ]
        }

        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        if "media_id" not in data:
            raise RuntimeError(f"Upload news failed: {data}")

        logger.info("wechat_news_uploaded", media_id=data["media_id"])
        return data["media_id"]

    async def _publish_draft(self, media_id: str) -> str:
        """发布草稿，返回 publish_id"""
        token = await self._get_access_token()
        client = await self._get_client()

        url = f"{self.API_BASE}/freepublish/submit?access_token={token}"
        payload = {"media_id": media_id}

        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        if data.get("errcode", 0) != 0:
            raise RuntimeError(f"Publish draft failed: {data}")

        publish_id = data.get("publish_id", "")
        logger.info("wechat_draft_published", publish_id=publish_id)
        return publish_id

    async def publish(self, article: Article) -> ArticlePublished:
        """
        发布文章到微信公众号

        流程：上传素材 → 发布草稿 → 生成 URL

        Returns:
            ArticlePublished 事件（包含 publish_url）
        """
        if self.is_mock:
            # Mock 模式：直接返回假 URL
            publish_url = f"https://mp.weixin.qq.com/s/mock_{article.id}"
            logger.info(
                "wechat_mock_publish",
                article_id=str(article.id),
                url=publish_url,
            )
        else:
            # 真实发布
            media_id = await self._upload_news(article)
            publish_id = await self._publish_draft(media_id)
            publish_url = f"https://mp.weixin.qq.com/s/{publish_id}"
            logger.info(
                "wechat_published",
                article_id=str(article.id),
                media_id=media_id,
                publish_id=publish_id,
            )

        event = ArticlePublished(
            tenant_id=article.tenant_id,
            article_id=article.id,
            publish_url=publish_url,
        )
        return event

    async def publish_to_wechat(self, article: Article) -> dict[str, Any]:
        """兼容旧接口"""
        event = await self.publish(article)
        return {
            "success": True,
            "url": event.publish_url,
            "media_id": f"media_{article.id}",
        }
