import structlog
from typing import Dict, Any

logger = structlog.get_logger(__name__)

class AIReleaseController:
    """
    Phase 91: Automatic Rollback
    Monitors metrics during a canary release and executes rollbacks if thresholds are breached.
    """
    def __init__(self):
        self.error_threshold_percent = 1.0
        self.latency_threshold_ms = 1500

    async def evaluate_canary_health(self, metrics: Dict[str, Any]) -> bool:
        """Returns False if a rollback should be triggered."""
        if metrics.get("error_rate", 0) > self.error_threshold_percent:
            logger.error("rollback_triggered", reason="error_rate_exceeded")
            return False
            
        if metrics.get("p90_latency_ms", 0) > self.latency_threshold_ms:
            logger.error("rollback_triggered", reason="latency_exceeded")
            return False
            
        if metrics.get("safety_violations", 0) > 0:
            logger.error("rollback_triggered", reason="safety_violation")
            return False
            
        return True
        
    async def trigger_rollback(self, version: str):
        # In a real environment, this invokes Kubernetes API or CI/CD webhooks
        logger.warning(f"ROLLING BACK VERSION {version} to previous stable release.")

