"""
MiniMax (妙想 AI) 多模态生成适配器

支持:
  - 文生图 / 图生图
  - 文生视频 / 图生视频
  - 音乐生成（带词 / 纯音乐）
  - 语音合成 (TTS)

环境变量:
  CF_MINIMAX_API_KEY    - API 密钥
  CF_MINIMAX_GROUP_ID   - Group ID

未配置时降级 mock。
"""

import os
from typing import Any

import httpx
import structlog
from content_factory_sdk.spi import ContentGeneratorProvider

logger = structlog.get_logger()


class MiniMaxGenerator(ContentGeneratorProvider):
    """MiniMax 多模态生成器"""

    API_BASE = "https://api.minimax.chat/v1"

    def __init__(
        self,
        api_key: str | None = None,
        group_id: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("CF_MINIMAX_API_KEY")
        self.group_id = group_id or os.getenv("CF_MINIMAX_GROUP_ID")
        self._client: httpx.AsyncClient | None = None

        if self.api_key and self.group_id:
            logger.info("minimax_initialized", group_id=self.group_id[:6] + "***")
        else:
            logger.warning(
                "minimax_no_credentials", msg="未配置 CF_MINIMAX_API_KEY/GROUP_ID，mock 模式"
            )

    @property
    def is_mock(self) -> bool:
        return not (self.api_key and self.group_id)

    def supported_types(self) -> list[str]:
        return ["image", "video", "music", "speech"]

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.API_BASE,
                headers={
                    "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
                trust_env=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate_image(self, prompt: str, **kwargs) -> dict[str, Any]:
        """文生图"""
        if self.is_mock:
            return {
                "type": "image",
                "url": f"https://placeholder.minimax.mock/image/{hash(prompt) % 10000}.png",
                "content": prompt,
                "metadata": {"model": "mock-image-1", "prompt": prompt},
            }
        client = await self._get_client()
        resp = await client.post(
            f"/text_to_image/{self.group_id}",
            json={"prompt": prompt, "model": "image-01", **kwargs},
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "type": "image",
            "url": data.get("image", ""),
            "content": prompt,
            "metadata": data,
        }

    async def generate_video(self, prompt: str, **kwargs) -> dict[str, Any]:
        """文生视频"""
        if self.is_mock:
            return {
                "type": "video",
                "url": f"https://placeholder.minimax.mock/video/{hash(prompt) % 10000}.mp4",
                "content": prompt,
                "metadata": {"model": "mock-video-1", "prompt": prompt},
            }
        client = await self._get_client()
        resp = await client.post(
            f"/video_generation/{self.group_id}",
            json={"prompt": prompt, "model": "video-01", **kwargs},
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "type": "video",
            "url": data.get("video", ""),
            "content": prompt,
            "metadata": data,
        }

    async def generate_music(self, prompt: str, lyrics: str = "", **kwargs) -> dict[str, Any]:
        """音乐生成"""
        if self.is_mock:
            return {
                "type": "music",
                "url": f"https://placeholder.minimax.mock/music/{hash(prompt) % 10000}.mp3",
                "content": {"prompt": prompt, "lyrics": lyrics},
                "metadata": {"model": "mock-music-1"},
            }
        client = await self._get_client()
        resp = await client.post(
            f"/music_generation/{self.group_id}",
            json={"prompt": prompt, "lyrics": lyrics, "model": "music-01", **kwargs},
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "type": "music",
            "url": data.get("audio", ""),
            "content": {"prompt": prompt, "lyrics": lyrics},
            "metadata": data,
        }

    async def generate_speech(
        self, text: str, voice_id: str = "default", **kwargs
    ) -> dict[str, Any]:
        """语音合成 (TTS)"""
        if self.is_mock:
            return {
                "type": "speech",
                "url": f"https://placeholder.minimax.mock/speech/{hash(text) % 10000}.mp3",
                "content": text,
                "metadata": {"voice_id": voice_id, "model": "mock-tts-1"},
            }
        client = await self._get_client()
        resp = await client.post(
            f"/t2a_v2/{self.group_id}",
            json={"text": text, "voice_id": voice_id, "model": "speech-02", **kwargs},
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "type": "speech",
            "url": data.get("audio", ""),
            "content": text,
            "metadata": data,
        }

    # ── ContentGeneratorProvider SPI 统一入口 ──────────────────────
    async def generate(self, prompt: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """根据 params['type'] 分发到对应生成方法"""
        params = params or {}
        content_type = params.get("type", "image")
        extra = {k: v for k, v in params.items() if k != "type"}

        if content_type == "image":
            return await self.generate_image(prompt, **extra)
        elif content_type == "video":
            return await self.generate_video(prompt, **extra)
        elif content_type == "music":
            lyrics = extra.pop("lyrics", "")
            return await self.generate_music(prompt, lyrics, **extra)
        elif content_type == "speech":
            voice_id = extra.pop("voice_id", "default")
            return await self.generate_speech(prompt, voice_id, **extra)
        else:
            raise ValueError(
                f"Unsupported type: {content_type}. Supported: {self.supported_types()}"
            )
