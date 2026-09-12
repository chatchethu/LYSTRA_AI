import json
import base64
import asyncio
from typing import AsyncGenerator
import httpx
from structlog import get_logger

from backend.config import get_settings
from backend.llm.gateway import LLMProvider

logger = get_logger()
settings = get_settings()



class OllamaProvider(LLMProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")

    def _build_messages(self, messages: list[dict]) -> list[dict]:
        """Pass messages through as-is — system prompt is built by the intelligence layer."""
        return messages

    def _build_options(self, kwargs: dict) -> dict:
        """Extract Ollama options (temperature, etc.) from kwargs."""
        options: dict = {}
        for key in ("temperature", "top_p", "top_k", "num_predict", "stop"):
            if key in kwargs:
                options[key] = kwargs.pop(key)
        return options

    async def _retry(self, func, *args, max_attempts: int = 3, **kwargs):
        for attempt in range(max_attempts):
            try:
                return await func(*args, **kwargs)
            except httpx.RequestError as e:
                if attempt == max_attempts - 1:
                    logger.error("ollama_request_failed", error=str(e), attempt=attempt)
                    raise
                wait = 2 ** attempt
                logger.warning("ollama_retry", attempt=attempt, wait=wait, error=str(e))
                await asyncio.sleep(wait)

    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        model = model or settings.OLLAMA_CHAT_MODEL
        options = self._build_options(kwargs)
        full_messages = self._build_messages(messages)

        payload = {
            "model": model,
            "messages": full_messages,
            "stream": False,
            **({"options": options} if options else {}),
        }
        
        if "format" in kwargs:
            payload["format"] = kwargs["format"]

        async def _make_request():
            logger.info("ollama_chat", model=model, messages_count=len(full_messages))
            async with httpx.AsyncClient(timeout=500.0) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                result = response.json()
                
                # Phase 60: Token Telemetry
                from backend.observability.logger import llm_usage_var
                llm_usage_var.set({
                    "prompt_tokens": result.get("prompt_eval_count"),
                    "completion_tokens": result.get("eval_count")
                })
                
                return result["message"]["content"]

        return await self._retry(_make_request)

    async def stream(
        self, messages: list[dict], model: str | None = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        model = model or settings.OLLAMA_CHAT_MODEL
        options = self._build_options(kwargs)
        full_messages = self._build_messages(messages)

        payload = {
            "model": model,
            "messages": full_messages,
            "stream": True,
            **({"options": options} if options else {}),
        }

        # Pass format if specified (e.g., format="json" for structured output)
        if "format" in kwargs:
            payload["format"] = kwargs["format"]

        logger.info("ollama_stream", model=model, messages_count=len(full_messages))
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=500.0) as client:
                    async with client.stream(
                        "POST", f"{self.base_url}/api/chat", json=payload
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line.strip():
                                continue
                            try:
                                data = json.loads(line)
                                content = data.get("message", {}).get("content", "")
                                if content:
                                    yield content
                                if data.get("done"):
                                    from backend.observability.logger import llm_usage_var
                                    llm_usage_var.set({
                                        "prompt_tokens": data.get("prompt_eval_count"),
                                        "completion_tokens": data.get("eval_count")
                                    })
                                    break
                            except json.JSONDecodeError:
                                logger.warning("ollama_stream_json_error", line=line)
                                continue
                # If we succeed without raising, break out of the retry loop
                break
            except httpx.RequestError as e:
                if attempt == max_attempts - 1:
                    logger.error("ollama_stream_failed", error=str(e), attempt=attempt)
                    raise
                wait = 2 ** attempt
                logger.warning("ollama_retry_stream", attempt=attempt, wait=wait, error=str(e))
                await asyncio.sleep(wait)

    async def embed(self, text: str, model: str | None = None, **kwargs) -> list[float]:
        model = model or settings.OLLAMA_EMBEDDING_MODEL
        payload = {"model": model, "prompt": text}

        async def _make_request():
            async with httpx.AsyncClient(timeout=500.0) as client:
                response = await client.post(f"{self.base_url}/api/embeddings", json=payload)
                response.raise_for_status()
                return response.json()["embedding"]

        return await self._retry(_make_request)

    async def vision(self, prompt: str, image_data: bytes, model: str | None = None, **kwargs) -> str:
        model = model or settings.OLLAMA_VISION_MODEL
        base64_image = base64.b64encode(image_data).decode("utf-8")

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt, "images": [base64_image]}
            ],
            "stream": False,
        }

        async def _make_request():
            async with httpx.AsyncClient(timeout=500.0) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                return response.json()["message"]["content"]

        return await self._retry(_make_request)

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
