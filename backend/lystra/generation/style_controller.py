import structlog
from typing import List, Optional
from backend.lystra.generation.response_strategy import (
    ResponseStrategy, get_default_strategy, DepthLevel, ToneType, EmojiPurpose, EmojiIntensity
)

logger = structlog.get_logger(__name__)

class StyleController:
    """
    Phase 17: Style Enforcement & Output Quality.
    Translates ResponseStrategy structs into concrete system prompt directives.
    """
    _BASE_DIRECTIVES = [
        # Identity & self-awareness
        (
            "- IDENTITY: You are LYSTRA — a personal AI built for the user. "
            "You are not a generic assistant. You are direct, thoughtful, and self-aware. "
            "When asked about yourself, answer with honesty and specificity. "
            "Do NOT use generic filler phrases like 'I am a large language model trained on a massive dataset', "
            "'I am here to help', 'fun facts about me', or 'what can I help you with today'. "
            "Instead, explain what you actually do, what you can genuinely help with, and be honest about your limitations. "
            "Speak like a knowledgeable person who is comfortable with who they are — not like a customer service bot."
        ),
        # Output cleanliness
        (
            "- ABSOLUTE OUTPUT RULE: Your response is the FINAL text the user reads. "
            "NEVER print internal step labels, planning stages, section headers, or reasoning phases as visible text. "
            "Examples of FORBIDDEN outputs: '* User Request Validation*', '* Breaking the Loop*', '**Step 1:**', '## Analysis'. "
            "These are YOUR private thoughts — the user must NEVER see them. "
            "Speak directly and conversationally at all times."
        ),
        # Language register
        (
            "- PLAIN LANGUAGE: ALWAYS speak in plain, everyday conversational language. "
            "Match the register the user is speaking in. "
            "NEVER use formal, literary, or old-fashioned vocabulary words such as: "
            "'pry', 'henceforth', 'indeed', 'thereafter', 'bestow', 'commence', 'perchance', 'whilst', 'whereupon'. "
            "If the user says 'yeah probably right', respond simply and casually — do not escalate to formal English."
        ),
        # Response maturity
        (
            "- RESPONSE QUALITY: Every response should feel like it came from someone who genuinely thought about the question. "
            "Avoid surface-level, generic, or copy-paste-feeling answers. "
            "Be specific. If you are explaining something, explain the actual thing — not a vague description of the category it belongs to. "
            "If you don't know something, say so plainly. If something has limitations or trade-offs, name them. "
            "Never pad a response to seem more helpful than you are."
        ),
        # Conversation naturalness
        (
            "- CONVERSATION STYLE: Do not end every response with a hollow question like 'How can I help you today?' or "
            "'What else would you like to know?'. Only ask a follow-up question if it is genuinely useful to the conversation. "
            "Do not repeat the user's words back to them as the opening line of your response. "
            "Get to the point."
        ),
        # Greeting awareness and time-of-day
        (
            "- GREETING AWARENESS: When the user greets you (e.g. 'hi', 'hello', 'hey'), respond warmly and naturally. "
            "Always check the 'Current System Time' in your context — it tells you whether it is Morning, Afternoon, Evening, or Night. "
            "Use that label when greeting. NEVER say 'Good Morning' if it is Afternoon or Evening. "
            "Use the user's verified name from [VERIFIED IDENTITY] naturally in the greeting. "
            "Be warm and personable — like a friend who knows them, not a customer service script. "
            "If you know something relevant about what they've been working on, you can naturally reference it."
        ),
        # Recommendation awareness
        (
            "- RECOMMENDATION AWARENESS: If the user asks for a recommendation (movies, music, food, travel, etc.) "
            "and their request is broad, DO NOT just list a bunch of items blindly. "
            "Instead, give 1 or 2 initial safe suggestions, and then ask a natural clarifying question "
            "about their preferences (e.g. favorite genre, language, mood, actors) to narrow it down. "
            "Be conversational and curious, not robotic."
        ),
        # Language and Tone
        (
            "- LANGUAGE & TONE: Use ONLY simple, natural Indian English. Keep sentences clear and accessible. "
            "Do NOT use complex, deep, or formal vocabulary. Speak naturally as if chatting with a friend in India. "
            "Ensure perfect spelling and grammar without being overly academic."
        ),
    ]

    _DEPTH_DIRECTIVES = {
        DepthLevel.CONCISE.value: (
            "- LENGTH REQUIREMENT: Keep the response extremely brief, conversational, and directly to the point. "
            "Maximum 1-2 sentences. Do NOT write paragraphs, lists, or headers."
        ),
        DepthLevel.STANDARD.value: (
            "- LENGTH REQUIREMENT: Keep the response focused and proportional. "
            "A simple question gets 2-3 sentences. A moderately complex question gets a short paragraph or a tight list. "
            "Never pad the response with background information the user didn't ask for."
        ),
        DepthLevel.COMPREHENSIVE.value: (
            "- LENGTH REQUIREMENT: Provide a thorough, detailed response covering all important aspects. "
            "Be complete but not repetitive. Use whatever length the content genuinely needs. "
            "Do NOT artificially pad or inflate the response."
        ),
    }

    _DEFAULT_DEPTH = DepthLevel.STANDARD
    _DEFAULT_TONE = ToneType.NEUTRAL
    _DEFAULT_PURPOSE = EmojiPurpose.ACKNOWLEDGMENT
    _DEFAULT_INTENSITY = EmojiIntensity.LOW
    
    # Safe structure elements regex or allow-list (alphanumeric, spaces, and underscores)
    _SAFE_STRUCTURE_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")

    def get_system_prompt_additions(self, strategy: Optional[ResponseStrategy]) -> str:
        """
        Orchestrates the assembly of system prompt directives based on the ResponseStrategy.
        """
        # 1 & 2: Construct a default strategy to avoid logic duplication
        if strategy is None:
            logger.debug("Strategy is None. Using default fallback strategy.")
            strategy = get_default_strategy()

        directives = self._BASE_DIRECTIVES.copy()

        # Tone
        raw_tone = getattr(strategy, "tone", None)
        if not raw_tone:
            logger.debug("Missing tone in strategy. Falling back to default.")
            tone_val = self._DEFAULT_TONE.value
        else:
            try:
                tone_val = ToneType(raw_tone).value
            except ValueError:
                logger.warning(f"Invalid tone value received: {raw_tone}. Falling back to default.")
                tone_val = self._DEFAULT_TONE.value
                
        directives.append(f"- TONE REQUIREMENT: Maintain a {tone_val} tone throughout the response.")

        # Emoji
        emoji_directives = self._build_emoji_directive(strategy)
        if emoji_directives:
            directives.extend(emoji_directives)

        # Depth
        depth_directive = self._build_depth_directive(strategy)
        directives.append(depth_directive)

        # Structure
        struct_directive = self._build_structure_directive(strategy)
        if struct_directive:
            directives.append(struct_directive)

        return "\n".join(directives)

    def _build_emoji_directive(self, strategy: ResponseStrategy) -> List[str]:
        emoji_strategy = getattr(strategy, "emoji_strategy", None)
        if not emoji_strategy:
            logger.debug("Missing emoji strategy. Skipping emoji rules.")
            return []
            
        use = getattr(emoji_strategy, "use", False)
        if not use:
            return ["- EMOJI REQUIREMENT: DO NOT use any emojis. The topic sensitivity or tone forbids it."]
            
        raw_purpose = getattr(emoji_strategy, "purpose", self._DEFAULT_PURPOSE.value)
        try:
            purpose = EmojiPurpose(raw_purpose).value
        except ValueError:
            logger.warning(f"Invalid emoji purpose: {raw_purpose}. Falling back.")
            purpose = self._DEFAULT_PURPOSE.value
            
        raw_intensity = getattr(emoji_strategy, "intensity", self._DEFAULT_INTENSITY.value)
        try:
            intensity = EmojiIntensity(raw_intensity).value
        except ValueError:
            logger.warning(f"Invalid emoji intensity: {raw_intensity}. Falling back.")
            intensity = self._DEFAULT_INTENSITY.value

        return [
            f"- EMOJI REQUIREMENT: Emojis are permitted. Purpose: {purpose}. Intensity: {intensity}.",
            "- Do NOT mechanically append emojis at the very end. Place them naturally inline (e.g., opening, mid-sentence) where they best convey the semantic emotion."
        ]

    def _build_depth_directive(self, strategy: ResponseStrategy) -> str:
        raw_depth = getattr(strategy, "depth", None)
        if not raw_depth:
            logger.debug(f"Missing depth in strategy. Falling back to {self._DEFAULT_DEPTH.value}.")
            depth_val = self._DEFAULT_DEPTH.value
        else:
            try:
                depth_val = DepthLevel(raw_depth).value
            except ValueError:
                logger.warning(f"Invalid depth value received: {raw_depth}. Falling back to default.")
                depth_val = self._DEFAULT_DEPTH.value
            
        return self._DEPTH_DIRECTIVES[depth_val]

    def _build_structure_directive(self, strategy: ResponseStrategy) -> Optional[str]:
        structure = getattr(strategy, "structure", None)
        if not structure:
            logger.debug("Missing structure list in strategy. Skipping structural directive.")
            return None
            
        if not isinstance(structure, list):
            logger.warning(f"Structure is not a list (got {type(structure)}). Skipping structural directive.")
            return None
            
        valid_items = []
        for item in structure:
            if not isinstance(item, str):
                logger.warning(f"Invalid structure item type (not string): {type(item)}. Skipping item.")
                continue
            
            # Injection defense: allow only safe characters
            clean_item = "".join(c for c in item if c in self._SAFE_STRUCTURE_CHARS).strip()
            clean_item = clean_item.replace("_", " ")
            if clean_item:
                valid_items.append(clean_item.lower())
                
        if not valid_items:
            logger.debug("No valid structure items found after filtering. Skipping structural directive.")
            return None

        item_set = set(valid_items)

        # ── Pure prose (conversational/emotional responses) ──────────────────────
        if item_set == {"paragraphs"}:
            return (
                "- FORMAT REQUIREMENT: Respond in natural, flowing prose. "
                "Do NOT use markdown headers (##), bullet points (- or *), or numbered lists. "
                "Write as you would speak — in connected sentences and paragraphs."
            )

        # ── Headers + bullets (information, explanation, planning, problem solving) ──
        if "headers" in item_set and "bullet points" in item_set:
            return (
                "- FORMAT REQUIREMENT: Use structured markdown formatting to make your response easy to scan and understand. "
                "Use bold section headers (### Header) to group related points. "
                "Under each header, use bullet points (- item) for individual items. "
                "Use **bold** for the key term or concept at the start of a bullet, followed by a dash and the explanation. "
                "Example: '**Reasoning** — analyze problems, requirements, and complex ideas.' "
                "Only use a header if there are genuinely 2+ bullets under it — don't create a header for a single point. "
                "Do NOT use headers as decorative labels for single sentences."
            )

        # ── Bullets only (comparisons, decision support) ─────────────────────────
        if "bullet points" in item_set:
            return (
                "- FORMAT REQUIREMENT: Present your response as a structured list using bullet points (- item). "
                "Use **bold** for the key term or label at the start of each bullet. "
                "Keep each bullet tight — one idea per bullet. "
                "Only add a short intro sentence before the list if context genuinely needs it."
            )

        # ── Fallback for any other combination ───────────────────────────────────
        struct_str = ", ".join(valid_items)
        return f"- FORMAT REQUIREMENT: Structure your response using these visual formats: [{struct_str}]."

