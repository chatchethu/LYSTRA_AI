"""
Routing utility helpers for the ToolRouter.

Design principle: NO hardcoded keyword lists for routing decisions.
The LLM receives full semantic context and reasons about intent itself.
Only utilities (filler stripping, term matching) live here.
"""
import re

_FILLER_RE = re.compile(
    r"^(?:can you |could you |please |i want to know |i wanna know |tell me |"
    r"do you know |find out |let me know |check |would you |could you please |"
    r"i'd like to know |i need to know |i was wondering |can you tell me )+",
    re.I,
)


def build_search_query(original_message: str) -> str:
    """
    Strip conversational filler from the front of a user message to produce
    a cleaner search-engine-style query as a fallback.
    The LLM router generates its own optimised queries — this is only used
    as a last-resort fallback (e.g., for deep-research deterministic path).
    """
    text = _FILLER_RE.sub("", original_message.strip()).rstrip("?.! ").strip()
    return text or original_message.strip()


def contains_term(text: str, terms: list[str]) -> bool:
    """
    Whole-word/whole-phrase membership test. Used only for the small set
    of architecturally-safe deterministic checks (e.g., Lystra self-identity).
    """
    tokens = set(re.findall(r"[a-z0-9']+", text))
    for term in terms:
        if " " in term:
            if re.search(r"\b" + re.escape(term) + r"\b", text):
                return True
        elif term in tokens:
            return True
    return False
