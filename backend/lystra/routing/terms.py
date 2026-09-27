import re

USER_IDENTITY_TERMS = [
    "who am i", "my name", "know about me", "do you know me", "about myself", 
    "my details", "remember me", "my preferences", "about me", "know me",
    "what you know about me", "what do you know about me"
]

IDENTITY_TERMS = [
    "who are you", "what are you", "tell me about yourself", "are you ai",
    "are you human", "are you a robot", "are you alive", "what can you do",
    "who made you", "your name", "introduce yourself", "lystra"
]

DEEP_RESEARCH_TERMS = [
    "deep research", "comprehensive analysis", "write a report on"
]

_FILLER_RE = re.compile(
    r"^(?:can you |could you |please |i want to know |i wanna know |tell me |do you know |find out |let me know |check )+",
    re.I
)

def build_search_query(original_message: str) -> str:
    text = _FILLER_RE.sub("", original_message.strip()).rstrip("?.! ").strip()
    return text or original_message.strip()

def contains_term(text: str, terms: list[str]) -> bool:
    tokens = set(re.findall(r"[a-z0-9']+", text))
    for term in terms:
        if " " in term:
            if re.search(r"\b" + re.escape(term) + r"\b", text):
                return True
        elif term in tokens:
            return True
    return False
