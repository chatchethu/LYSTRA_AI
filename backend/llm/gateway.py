from typing import Any, AsyncGenerator, Protocol
import asyncio
import structlog

# Top-level imports — moved out of hot-path functions (Fix #7).
# These are safe to import at module level; no circular-import issues exist here.
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
        # Fix #5: half-open trial lock — only ONE caller gets through when recovering.
        # All other concurrent callers that arrive while state == HALF_OPEN are rejected,
        # which is the correct behaviour for a controlled trial after OPEN.
        self._half_open_trial_in_flight = False

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
        # If the trial call in HALF_OPEN failed, the trial lock must be released
        # so a future recovery window can try again.
        self._half_open_trial_in_flight = False

    def record_success(self) -> None:
        self.failures = 0
        self.state = "CLOSED"
        self._half_open_trial_in_flight = False

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            elapsed = asyncio.get_event_loop().time() - self.last_failure_time
            if elapsed > self.recovery_timeout:
                # Fix #5: transition to HALF_OPEN and allow exactly ONE trial call through.
                # Concurrent callers that race here after the timeout will see
                # _half_open_trial_in_flight=True and be rejected until the trial resolves.
                self.state = "HALF_OPEN"
                if not self._half_open_trial_in_flight:
                    self._half_open_trial_in_flight = True
                    return True
                return False
            return False
        # HALF_OPEN: only one trial at a time
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
        self.timeout_seconds = 500.0
        # Fix #6: overall deadline budget across all model attempts and retries.
        # With local Llama 3.2 routinely taking 80-250s per call, the old 120s cap
        # was killing memory conflict checks and other background LLM calls mid-flight.
        # 500s = safe ceiling that lets a single slow call finish while still bounding
        # a truly hung request.
        self.total_deadline_seconds = 500.0
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
        """Fix #8: single telemetry helper — eliminates the 4 near-identical log blocks
        that were scattered across success/failure paths in _execute_with_resilience and stream().
        All paths now share the same field set, preventing drift (e.g. stream() previously
        never tracked fallback status correctly).
        """
        log_fn = self.logger.info if level == "info" else self.logger.error
        log_fn(
            "llm_telemetry",
            operation=operation,
            primary_model=primary_model,
            model=model,
            # Fix #9: model_version removed — it was hardcoded as "unknown" everywhere,
            # which is misleading. Add it back when the Ollama provider can supply it.
            is_fallback=is_fallback,
            latency_ms=round(latency_ms * 1000, 2),
            usage_available=bool(usage),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            error=error,
        )

        # Fix #2: wire token accountant — previously initialized but never fed data.
        if usage:
            self.token_accountant.add(
                TokenUsage(
                    prompt_tokens=usage.get("prompt_tokens") or 0,
                    completion_tokens=usage.get("completion_tokens") or 0,
                    total_tokens=(usage.get("prompt_tokens") or 0) + (usage.get("completion_tokens") or 0),
                )
            )

    # Fix #3: return type was `-> any` (the builtin function, not a type annotation).
    # Corrected to `-> Any` from typing.
    async def _execute_with_resilience(
        self,
        operation: str,
        model: str | None,
        kwargs: dict,
        func,
    ) -> Any:
        request_id = kwargs.pop("request_id", None)
        task_id = kwargs.pop("task_id", None)

        settings = get_settings()
        primary_model = model or settings.OLLAMA_CHAT_MODEL
        fallback_model = self._router.get_fallback_model(primary_model) if self._router else None

        models_to_try = [(primary_model, False)]
        if fallback_model:
            models_to_try.append((fallback_model, True))

        last_error: Exception | None = None

        # Fix #1 (latency mislabeling): track total elapsed time from before the outer
        # model loop, not from inside the inner retry loop. The inner `start_time` is
        # only used for per-attempt latency on the success path.
        total_start_time = asyncio.get_event_loop().time()

        # Fix #6: enforce a hard deadline across ALL model attempts and retries combined.
        deadline = total_start_time + self.total_deadline_seconds

        for current_model, is_fallback in models_to_try:
            cb = self._get_circuit_breaker(current_model)
            if not cb.can_execute():
                self.logger.warning("circuit_breaker_open", model=current_model)
                last_error = CircuitBreakerOpenException(f"Circuit breaker open for {current_model}")
                continue

            for attempt in range(self.max_retries + 1):
                # Fix #6: check remaining budget before each attempt
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    self.logger.warning("llm_total_deadline_exceeded", operation=operation)
                    break

                attempt_start = asyncio.get_event_loop().time()
                try:
                    async with self._semaphore:
                        provider_kwargs = {
                            **kwargs,
                            "request_id": request_id,
                            "task_id": task_id,
                            "operation": operation,
                        }
                        # Use the smaller of per-attempt timeout and remaining budget
                        effective_timeout = min(self.timeout_seconds, remaining)
                        result = await asyncio.wait_for(
                            func(model=current_model, **provider_kwargs),
                            timeout=effective_timeout,
                        )

                    latency = asyncio.get_event_loop().time() - attempt_start
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
                    await asyncio.sleep(2 ** attempt)

        # Fix #1: failure-path latency now correctly reflects total elapsed wall time,
        # not just the last attempt's duration.
        total_latency = asyncio.get_event_loop().time() - total_start_time
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
        """Fix #4: stream() now participates in circuit breaker checking and fallback model
        selection, consistent with chat()/embed()/vision(). Previously it bypassed all
        resilience — if the primary model was down, streaming failed immediately with no
        fallback attempt, and the circuit breaker state was never updated from stream failures.
        """
        request_id = kwargs.pop("request_id", None)
        task_id = kwargs.pop("task_id", None)

        settings = get_settings()
        primary_model = model or settings.OLLAMA_CHAT_MODEL
        fallback_model = self._router.get_fallback_model(primary_model) if self._router else None

        models_to_try = [(primary_model, False)]
        if fallback_model:
            models_to_try.append((fallback_model, True))

        last_error: Exception | None = None
        total_start_time = asyncio.get_event_loop().time()

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

            attempt_start = asyncio.get_event_loop().time()
            try:
                async with self._semaphore:
                    async for chunk in self._provider.stream(messages, current_model, **provider_kwargs):
                        yield chunk

                latency = asyncio.get_event_loop().time() - attempt_start
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
                return  # stream completed successfully — do not try fallback

            except Exception as e:
                last_error = e
                cb.record_failure()
                self.logger.warning(
                    "llm_stream_error",
                    error=str(e),
                    model=current_model,
                    trying_fallback=bool(fallback_model and not is_fallback),
                )
                # If there's a fallback model, continue the loop to try it.
                # If this was already the fallback (or there is none), fall through to raise.
                if is_fallback or not fallback_model:
                    break

        # All models exhausted — log total elapsed and re-raise
        total_latency = asyncio.get_event_loop().time() - total_start_time
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
