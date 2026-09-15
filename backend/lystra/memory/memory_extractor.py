import re
import hashlib
import structlog
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from .schemas import MemoryObject, MemoryType, MemorySource, MemoryStatus
from .memory_classifier import MemoryClassifier

logger = structlog.get_logger(__name__)

class MemoryExtractor:
    """
    Phase 5 & 6: Explicit vs Inferred Memory and Memory Confidence.
    Extracts structured memory objects from user interaction history.
    """
    def __init__(self, llm_gateway, 
                 base_inferred_confidence: float = 0.40,
                 context_history_bonus: float = 0.05,
                 max_context_history_bonus_turns: int = 5,
                 explicit_confidence: float = 0.95):
        self.classifier = MemoryClassifier(llm_gateway)
        self.llm = llm_gateway
        
        self.base_inferred_confidence = base_inferred_confidence
        self.context_history_bonus = context_history_bonus
        self.max_context_history_bonus_turns = max_context_history_bonus_turns
        self.explicit_confidence = explicit_confidence

    def _contains_pii(self, text: str) -> bool:
        """Secondary defense-in-depth against sensitive PII data."""
        # Simple regex checks for CC, SSN, Phone numbers
        cc_pattern = r"\b(?:\d[ -]*?){13,16}\b"
        ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
        # 10+ digit phone numbers loosely
        phone_pattern = r"\b\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        
        if re.search(cc_pattern, text) or re.search(ssn_pattern, text) or re.search(phone_pattern, text):
            return True
        return False

    async def extract_candidate_memory(self, user_id: str, message: str, context_history: List[str]) -> Optional[MemoryObject]:
        # Fix #6: Length cap before classification to prevent LLM bloat
        message = message[:2000]

        # Fix #4: Check PII before sending to the LLM to prevent data leaks.
        if self._contains_pii(message):
            logger.info("memory_candidate_dropped", user_id=user_id, reason="pii_matched_before_classification")
            return None

        # Step 1: Semantic Classification
        classification = await self.classifier.classify_statement(message)
        
        if classification.is_manipulation_attempt:
            logger.info("memory_candidate_dropped", user_id=user_id, reason="manipulation_attempt")
            return None
            
        mem_type_str = classification.type
        try:
            mem_type = MemoryType(mem_type_str)
        except ValueError:
            mem_type = MemoryType.IRRELEVANT

        # Do not store irrelevant or sensitive information
        if mem_type in [MemoryType.IRRELEVANT, MemoryType.SENSITIVE, getattr(MemoryType, "DO_NOT_STORE", "DO_NOT_STORE")]:
            return None
            
        if self._contains_pii(classification.extracted_fact):
            logger.info("memory_candidate_dropped", user_id=user_id, reason="pii_matched_in_extracted_fact")
            return None
            
        persistence = classification.persistence
        if persistence == "none" and mem_type != MemoryType.TEMPORARY:
            return None

        # Step 2: Determine Explicit vs Inferred and Confidence
        if classification.source == "explicit":
            source = MemorySource.EXPLICIT
            confidence = self.explicit_confidence
        else:
            source = MemorySource.INFERRED
            confidence = self.base_inferred_confidence + (min(len(context_history), self.max_context_history_bonus_turns) * self.context_history_bonus) 

        importance = classification.importance

        # Phase 8: Expiration for temporary
        expires_at = None
        if mem_type == MemoryType.TEMPORARY:
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        fact = classification.extracted_fact if classification.extracted_fact else message
        
        # Fix #3: Use stable hash instead of built-in hash()
        if classification.canonical_key and classification.canonical_key != "memory":
            safe_key = classification.canonical_key
        else:
            fact_hash = hashlib.sha256(fact.encode("utf-8")).hexdigest()[:8]
            safe_key = f"{mem_type.value if hasattr(mem_type, 'value') else mem_type}_{fact_hash}"

        # Phase 8: Lifecycle Status
        # Explicit memories are instantly active. Inferred ones must be validated over time.
        initial_status = MemoryStatus.ACTIVE if source == MemorySource.EXPLICIT else MemoryStatus.CANDIDATE

        # Step 3: Create the Structured Object
        return MemoryObject(
            user_id=user_id,
            type=mem_type,
            importance=importance,
            expires_at=expires_at,
            key=safe_key,
            value=fact, 
            confidence=confidence,
            source=source,
            status=initial_status
        )
