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

CASUAL_TERMS = [
    "hi", "hello", "hey", "morning", "good morning", "good evening",
    "how are you", "what's up", "sup", "yo", "thanks", "thank you",
    "okay", "ok", "bye", "goodbye", "see you"
]

# Note: Explicit phrase matching for emotions ("i am sad", "i feel") 
# was requested to be removed to prevent hardcoded brittleness.
# We keep the array empty or minimal, relying on Semantic Analyzer.
PERSONAL_TERMS = []

MANDATORY_WEB_TERMS = [
    "latest", "current", "today", "recent", "news", "price",
    "availability", "version", "launch", "released", "stock", "weather"
]

# Entertainment recommendations always need web search — LLM knowledge of
# regional movies, songs, and shows is unreliable and causes hallucinations.
ENTERTAINMENT_WEB_TERMS = [
    # Movie/show triggers
    "movies", "movie", "films", "film", "web series", "series", "shows", "show",
    "watch", "streaming", "ott", "netflix", "amazon prime", "hotstar",
    # Music triggers
    "songs", "song", "music", "album", "singer", "artist", "playlist",
    # Regional keywords that the LLM hallucinates badly
    "kannada", "tamil", "telugu", "malayalam", "bollywood", "tollywood",
    "kollywood", "sandalwood",
    # Recommendation/suggestion triggers
    "recommend", "suggest", "suggestion", "recommendations",
    "what to watch", "should i watch", "worth watching",
    # Food/place recommendations
    "restaurants", "restaurant", "places to visit", "tourist", "travel",
]

DEEP_RESEARCH_TERMS = [
    "deep research", "comprehensive analysis", "write a report on"
]

STATIC_EXPLANATION_PREFIXES = [
    "explain ",
    "define ",
    "what does ",
    "how does ",
    "why does ",
    "what time",
    "what day",
    "what is the date",
    "what is today"
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
