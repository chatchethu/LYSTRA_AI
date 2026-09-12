import contextvars
import logging
import structlog
import re
from typing import Any, Dict

# Context vars for Observability (Part 40)
request_id_var = contextvars.ContextVar('request_id', default=None)
conversation_id_var = contextvars.ContextVar('conversation_id', default=None)
message_id_var = contextvars.ContextVar('message_id', default=None)
task_id_var = contextvars.ContextVar('task_id', default=None)
model_run_id_var = contextvars.ContextVar('model_run_id', default=None)
tool_call_id_var = contextvars.ContextVar('tool_call_id', default=None)
user_id_var = contextvars.ContextVar('user_id', default=None)
llm_usage_var = contextvars.ContextVar('llm_usage', default=None)

def add_context_ids(logger: logging.Logger, log_method: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    for var, key in [
        (request_id_var, 'request_id'),
        (conversation_id_var, 'conversation_id'),
        (message_id_var, 'message_id'),
        (task_id_var, 'task_id'),
        (model_run_id_var, 'model_run_id'),
        (tool_call_id_var, 'tool_call_id'),
        (user_id_var, 'user_id'),
    ]:
        val = var.get()
        if val:
            event_dict[key] = val
    return event_dict

def redact_secrets(logger: logging.Logger, log_method: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive fields like passwords, tokens, API keys."""
    sensitive_keys = re.compile(r'(password|token|api_key|secret|authorization|refresh_token)', re.IGNORECASE)
    
    # Recursively redact dicts
    def _redact(d: Any) -> Any:
        if isinstance(d, dict):
            return {
                k: ("***REDACTED***" if sensitive_keys.search(k) else _redact(v))
                for k, v in d.items()
            }
        elif isinstance(d, list):
            return [_redact(i) for i in d]
        return d

    # Also avoid logging sensitive user content by default if not explicitly allowed
    for sensitive_content_key in ["user_content", "user_message", "message_content"]:
        if sensitive_content_key in event_dict:
            event_dict[sensitive_content_key] = "***REDACTED_USER_CONTENT***"

    return _redact(event_dict)

def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog with JSON output, request ID binding, timestamps, and redaction"""
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_context_ids,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            redact_secrets,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=getattr(logging, log_level.upper(), logging.INFO)
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a bound logger with common context"""
    return structlog.get_logger(name)
