from typing import Any, AsyncGenerator, Protocol
import asyncio
import structlog
import time
import random

from backend.config import get_settings
from backend.observability.logger import llm_usage_var


class LLMProvider(Protocol):
    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        ...

    async def stream(self, messages: list[dict], model: str | None = None, **kwargs) -> AsyncGenerator[str, None]:
        ...

    async def embed(self, text: str, model: str | None = None, **kwargs) -> list[float]:
        ...

    async def vision(self, prompt: str, image_data: bytes, model: str | None = None, **kwargs) -> str:
        ...

    async def health_check(self) -> bool:
        ...


class TokenUsage:
    def __init__(self, prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens


class CircuitBreakerOpenException(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"
        self._half_open_trial_in_flight = False

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure_time = time.monotonic()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
        self._half_open_trial_in_flight = False

    def record_success(self) -> None:
        self.failures = 0
        self.state = "CLOSED"
        self._half_open_trial_in_flight = False

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            elapsed = time.monotonic() - self.last_failure_time
            if elapsed > self.recovery_timeout:
                self.state = "HALF_OPEN"
                if not self._half_open_trial_in_flight:
                    self._half_open_trial_in_flight = True
                    return True
                return False
            return False
        if self.state == "HALF_OPEN":
            if not self._half_open_trial_in_flight:
                self._half_open_trial_in_flight = True
                return True
            return False
        return True


class TokenAccountant:
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def add(self, usage: TokenUsage) -> None:
        self.prompt_tokens += usage.prompt_tokens
        self.completion_tokens += usage.completion_tokens
        self.total_tokens += usage.total_tokens


class LLMGateway:
    def __init__(self, provider: LLMProvider, router=None, max_concurrency: int = 10):
        self._provider = provider
        self._router = router
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self.token_accountant = TokenAccountant()
        self.max_retries = 2
        
        settings = get_settings()
        self.timeout_seconds = getattr(settings, "LLM_CALL_TIMEOUT_SECONDS", 60.0)
        self.total_deadline_seconds = getattr(settings, "LLM_TOTAL_DEADLINE_SECONDS", 120.0)
        
        self.logger = structlog.get_logger(__name__)

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    def _get_circuit_breaker(self, model: str) -> CircuitBreaker:
        if model not in self._circuit_breakers:
            self._circuit_breakers[model] = CircuitBreaker()
        return self._circuit_breakers[model]

    def _log_telemetry(
        self,
        *,
        level: str,
        operation: str,
        primary_model: str,
        model: str,
        is_fallback: bool,
        latency_ms: float,
        usage: dict,
        error: str | None,
    ) -> None:
        log_fn = self.logger.info if level == "info" else self.logger.error
        log_fn(
            "llm_telemetry",
            operation=operation,
            primary_model=primary_model,
            model=model,
            is_fallback=is_fallback,
            latency_ms=latency_ms,
            usage=usage,
            error=error,
        )

    def _get_models_to_try(self, model: str | None = None) -> list[tuple[str, bool]]:
        settings = get_settings()
        primary_model = model or getattr(settings, "OLLAMA_CHAT_MODEL", "llama3.2:latest")
        fallback_model = self._router.get_fallback_model(primary_model) if self._router else None
        
        models = [(primary_model, False)]
        if fallback_model and fallback_model != primary_model:
            models.append((fallback_model, True))
            
        return models

    async def _execute_with_resilience(self, operation: str, model: str | None, kwargs: dict, func) -> Any:
        request_id = kwargs.pop("request_id", None)
        task_id = kwargs.pop("task_id", None)
        
        models_to_try = self._get_models_to_try(model)
        primary_model = models_to_try[0][0]
        fallback_model = models_to_try[1][0] if len(models_to_try) > 1 else None

        last_error: Exception | None = None
        total_start_time = time.monotonic()
        deadline = total_start_time + self.total_deadline_seconds

        for current_model, is_fallback in models_to_try:
            cb = self._get_circuit_breaker(current_model)

            for attempt in range(self.max_retries + 1):
                if not cb.can_execute():
                    self.logger.warning("circuit_breaker_open", model=current_model)
                    last_error = CircuitBreakerOpenException(f"Circuit breaker open for {current_model}")
                    break

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.logger.warning("llm_total_deadline_exceeded", operation=operation)
                    break

                attempt_start = time.monotonic()
                try:
                    async with self._semaphore:
                        provider_kwargs = {
                            **kwargs,
                            "request_id": request_id,
                            "task_id": task_id,
                            "operation": operation,
                        }
                        effective_timeout = min(self.timeout_seconds, remaining)
                        result = await asyncio.wait_for(
                            func(model=current_model, **provider_kwargs),
                            timeout=effective_timeout,
                        )

                    latency = time.monotonic() - attempt_start
                    cb.record_success()

                    usage = llm_usage_var.get() or {}
                    self._log_telemetry(
                        level="info",
                        operation=operation,
                        primary_model=primary_model,
                        model=current_model,
                        is_fallback=is_fallback,
                        latency_ms=latency,
                        usage=usage,
                        error=None,
                    )
                    return result

                except asyncio.TimeoutError as e:
                    last_error = e
                    cb.record_failure()
                    self.logger.warning("llm_request_timeout", attempt=attempt, model=current_model)

                except Exception as e:
                    last_error = e
                    cb.record_failure()
                    self.logger.warning(
                        "llm_request_error",
                        error=str(e),
                        attempt=attempt,
                        model=current_model,
                    )

                if attempt < self.max_retries:
                    remaining = deadline - time.monotonic()
                    backoff = min(2 ** attempt + random.uniform(0, 0.5), max(remaining, 0))
                    if backoff > 0:
                        await asyncio.sleep(backoff)

        total_latency = time.monotonic() - total_start_time
        self._log_telemetry(
            level="error",
            operation=operation,
            primary_model=primary_model,
            model=fallback_model if fallback_model else primary_model,
            is_fallback=bool(fallback_model),
            latency_ms=total_latency,
            usage={},
            error=str(last_error),
        )
        raise last_error

    async def chat(self, messages: list[dict], model: str | None = None, **kwargs) -> str:
        async def _do_chat(model, **kw):
            return await self._provider.chat(messages, model, **kw)
        return await self._execute_with_resilience("chat", model, kwargs, _do_chat)

    async def stream(
        self, messages: list[dict], model: str | None = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        request_id = kwargs.pop("request_id", None)
        task_id = kwargs.pop("task_id", None)

        models_to_try = self._get_models_to_try(model)
        primary_model = models_to_try[0][0]
        fallback_model = models_to_try[1][0] if len(models_to_try) > 1 else None

        last_error: Exception | None = None
        total_start_time = time.monotonic()
        deadline = total_start_time + self.total_deadline_seconds
        
        chunks_yielded = 0

        for current_model, is_fallback in models_to_try:
            cb = self._get_circuit_breaker(current_model)
            if not cb.can_execute():
                self.logger.warning("circuit_breaker_open", model=current_model)
                last_error = CircuitBreakerOpenException(f"Circuit breaker open for {current_model}")
                continue

            provider_kwargs = {
                **kwargs,
                "request_id": request_id,
                "task_id": task_id,
                "operation": "stream",
            }

            attempt_start = time.monotonic()
            try:
                async with self._semaphore:
                    # Implement chunk timeout to avoid hanging streams
                    agen = self._provider.stream(messages, current_model, **provider_kwargs).__aiter__()
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise asyncio.TimeoutError("Stream exceeded total deadline")
                            
                        effective_timeout = min(self.timeout_seconds, remaining)
                        try:
                            chunk = await asyncio.wait_for(agen.__anext__(), timeout=effective_timeout)
                        except StopAsyncIteration:
                            break
                            
                        chunks_yielded += 1
                        yield chunk

                latency = time.monotonic() - attempt_start
                cb.record_success()
                usage = llm_usage_var.get() or {}
                self._log_telemetry(
                    level="info",
                    operation="stream",
                    primary_model=primary_model,
                    model=current_model,
                    is_fallback=is_fallback,
                    latency_ms=latency,
                    usage=usage,
                    error=None,
                )
                return

            except Exception as e:
                last_error = e
                cb.record_failure()
                self.logger.warning(
                    "llm_stream_error",
                    error=str(e),
                    model=current_model,
                    trying_fallback=bool(fallback_model and not is_fallback),
                )
                
                # Fix #1: Garbled output. Only fallback if no chunks yielded.
                if chunks_yielded > 0:
                    yield "\n[Error: response interrupted]"
                    raise
                    
                if is_fallback or not fallback_model:
                    break

        total_latency = time.monotonic() - total_start_time
        self._log_telemetry(
            level="error",
            operation="stream",
            primary_model=primary_model,
            model=fallback_model if fallback_model else primary_model,
            is_fallback=bool(fallback_model),
            latency_ms=total_latency,
            usage={},
            error=str(last_error),
        )
        raise last_error

    async def embed(self, text: str, model: str | None = None, **kwargs) -> list[float]:
        async def _do_embed(model, **kw):
            return await self._provider.embed(text, model, **kw)
        return await self._execute_with_resilience("embed", model, kwargs, _do_embed)

    async def vision(self, prompt: str, image_data: bytes, model: str | None = None, **kwargs) -> str:
        async def _do_vision(model, **kw):
            return await self._provider.vision(prompt, image_data, model, **kw)
        return await self._execute_with_resilience("vision", model, kwargs, _do_vision)

    async def health_check(self) -> bool:
        return await self._provider.health_check()
