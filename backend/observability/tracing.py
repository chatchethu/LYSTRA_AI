import structlog
from functools import wraps
from typing import Callable, Any
# Pseudo OpenTelemetry implementations for Phase 83/84
# In a real environment: from opentelemetry import trace
# tracer = trace.get_tracer(__name__)

logger = structlog.get_logger(__name__)

class PseudoSpan:
    def __init__(self, name: str):
        self.name = name
        self.attributes = {}
        
    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value
        
    def __enter__(self):
        logger.info(f"span_started", span_name=self.name)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"span_failed", span_name=self.name, error=str(exc_val))
        else:
            logger.info(f"span_ended", span_name=self.name, attributes=self.attributes)

def get_tracer():
    class Tracer:
        def start_as_current_span(self, name: str):
            return PseudoSpan(name)
    return Tracer()

def trace_agent_step(step_name: str):
    """
    Decorator that injects an OpenTelemetry span around an agentic action.
    Ensures that private chain-of-thought is not emitted to the trace attributes.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(f"lystra.{step_name}") as span:
                # Execute the actual function
                result = await func(*args, **kwargs)
                
                # We could introspect the result to add safe attributes to the span
                if hasattr(result, "tool_name"):
                    span.set_attribute("tool.name", getattr(result, "tool_name"))
                if hasattr(result, "intent"):
                    span.set_attribute("agent.intent", getattr(result, "intent"))
                    
                return result
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(f"lystra.{step_name}") as span:
                result = func(*args, **kwargs)
                return result
                
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator

