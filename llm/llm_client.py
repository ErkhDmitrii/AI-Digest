"""LLM-клиент — OpenAI-совместимый API."""
import json
import logging
from typing import Any, Dict

from openai import AsyncOpenAI

from config.settings import settings

log = logging.getLogger("llm.client")


class LLMClient:
    """Клиент для работы с LLM через OpenAI-совместимый API."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL

    async def chat(self, system_prompt: str, user_message: str) -> str:
        """Простой chat-запрос. Возвращает текст ответа."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            log.error("LLM chat error: %s", e)
            raise

    async def chat_json(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """Chat-запрос с ожиданием JSON-ответа."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except json.JSONDecodeError as e:
            log.error("LLM JSON parse error: %s | raw: %s", e, content[:200])
            raise
        except Exception as e:
            log.error("LLM chat_json error: %s", e)
            raise
