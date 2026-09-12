from opentelemetry import metrics as otel_metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.metrics import Counter, Histogram, UpDownCounter

from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models.metric import MetricEvent

class AgentMetrics:
    """
    Custom metrics for the agent system.
    """
    
    def __init__(self, meter_provider: MeterProvider = None):
        if meter_provider is None:
            self.meter = otel_metrics.get_meter("agent_metrics")
        else:
            self.meter = meter_provider.get_meter("agent_metrics")
            
        self.request_count: Counter = self.meter.create_counter(
            "agent.request.count",
            description="Number of requests processed by the agent"
        )
        self.request_duration: Histogram = self.meter.create_histogram(
            "agent.request.duration",
            description="Duration of requests in ms"
        )
        self.llm_token_count: Counter = self.meter.create_counter(
            "agent.llm.tokens",
            description="Tokens used in LLM calls"
        )
        self.tool_execution_count: Counter = self.meter.create_counter(
            "agent.tool.execution.count",
            description="Number of tool executions"
        )
        self.tool_error_count: Counter = self.meter.create_counter(
            "agent.tool.error.count",
            description="Number of tool execution errors"
        )
        self.memory_retrieval_count: Counter = self.meter.create_counter(
            "agent.memory.retrieval.count",
            description="Number of memory retrievals"
        )
        self.active_tasks: UpDownCounter = self.meter.create_up_down_counter(
            "agent.tasks.active",
            description="Current number of active background tasks"
        )
        self.task_completion_rate: Counter = self.meter.create_counter(
            "agent.tasks.completed",
            description="Completed tasks"
        )
        
    async def _persist_to_db(self, session: AsyncSession, metric_type: str, value: float, attributes: dict):
        if session:
            event = MetricEvent(metric_type=metric_type, value=value, attributes=attributes)
            session.add(event)
            await session.commit()
    
    async def record_request(self, intent: str, status: str, duration_ms: float, session: AsyncSession = None):
        attributes = {"intent": intent, "status": status}
        self.request_count.add(1, attributes)
        self.request_duration.record(duration_ms, attributes)
        if session:
            await self._persist_to_db(session, "agent_run", 1.0, attributes)
            await self._persist_to_db(session, "model_latency", duration_ms, attributes)
        
    async def record_llm_call(self, model: str, prompt_tokens: int, completion_tokens: int, session: AsyncSession = None):
        attributes = {"model": model}
        self.llm_token_count.add(prompt_tokens, {"type": "prompt", **attributes})
        self.llm_token_count.add(completion_tokens, {"type": "completion", **attributes})
        if session:
            await self._persist_to_db(session, "token_usage", float(prompt_tokens + completion_tokens), attributes)
        
    async def record_tool_call(self, tool_name: str, success: bool, duration_ms: float, session: AsyncSession = None):
        attributes = {"tool": tool_name}
        self.tool_execution_count.add(1, attributes)
        if not success:
            self.tool_error_count.add(1, attributes)
        if session:
            await self._persist_to_db(session, "tool_latency", duration_ms, {"tool": tool_name, "success": success})
            if not success:
                await self._persist_to_db(session, "errors", 1.0, {"tool": tool_name, "type": "tool_error"})
            
    async def record_memory_hit(self, memory_type: str, results_count: int, session: AsyncSession = None):
        self.memory_retrieval_count.add(results_count, {"type": memory_type})
        if session:
            await self._persist_to_db(session, "memory_retrieval", float(results_count), {"type": memory_type})
            
    async def record_task_status(self, status: str, task_id: str, session: AsyncSession = None):
        # Additional method for task status
        if session:
            await self._persist_to_db(session, f"task_{status.lower()}", 1.0, {"task_id": task_id})
            
    async def record_fallback(self, reason: str, session: AsyncSession = None):
        # Additional method for fallbacks
        if session:
            await self._persist_to_db(session, "fallback_frequency", 1.0, {"reason": reason})
