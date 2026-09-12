import sys

content = '''import logging
from typing import Optional, List
from backend.lystra.generation.response_strategy import (
    ResponseStrategy, 
    EmojiStrategy,
    DepthLevel, 
    ToneType, 
    EmojiIntensity,
    EmojiPurpose
)

logger = logging.getLogger(__name__)

class StyleController:
    """
    StyleController handles the injection of styling, tone, depth, and structural 
    rules into the AI's system prompt.
    """
    
    _BASE_DIRECTIVES = [
        "CRITICAL STYLE & INTELLIGENCE DIRECTIVES:",
        "- ADVANCED REASONING: Always analyze the user's implicit needs and anticipate follow-up questions. Provide smart, proactive insights rather than just literal answers.",
        "- CONTINUITY: You are talking to a known user in an ongoing workspace. NEVER say 'I am a new conversation' or 'I don't have prior knowledge'. Act like a seamless, continuous AI partner.",
        "- LOGICAL STRUCTURE: Break down complex problems step-by-step. Use highly organized formatting (bullet points, bold text) for readability.",
        "- FACTUAL RIGOR: Prioritize deep accuracy over conversational filler. If a request is ambiguous, state your assumptions clearly before answering.",
        "- LANGUAGE REQUIREMENT: You MUST use simple, easy-to-understand English. Avoid overly academic or archaic vocabulary, but remain highly intelligent and articulate.",
        "- LOCALIZATION: Use Indian English spellings and phrasing.",
        "- QUALITY: Proofread your output carefully. Zero tolerance for grammatical mistakes.",
        "- ANTI-ROBOTIC: Start the answer naturally. DO NOT use repetitive, subservient openings like 'Sure! Here is...' or 'Absolutely! I can help with that.'",
        "- IDENTITY: You are LYSTRA, an elite, hyper-intelligent AI assistant. Never refer to the user as 'the human'.",
    ]

    _DEPTH_DIRECTIVES = {
        DepthLevel.CONCISE.value: "- LENGTH REQUIREMENT: Keep the response extremely brief, conversational, and directly to the point. No more than 1-2 short sentences. Do NOT write paragraphs.",
        DepthLevel.STANDARD.value: "- LENGTH REQUIREMENT: Keep the response concise and natural. Use a maximum of 3-4 short sentences unless explaining a complex technical topic. Avoid writing unnecessary paragraphs.",
        DepthLevel.COMPREHENSIVE.value: "- LENGTH REQUIREMENT: Provide a highly detailed, comprehensive, and exhaustive response.",
    }

    _DEFAULT_DEPTH = DepthLevel.STANDARD
    _DEFAULT_TONE = ToneType.NEUTRAL
    _DEFAULT_PURPOSE = EmojiPurpose.ACKNOWLEDGMENT
    _DEFAULT_INTENSITY = EmojiIntensity.LOW
    
    # Safe structure elements regex or allow-list (alphanumeric and spaces)
    _SAFE_STRUCTURE_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -")

    def get_system_prompt_additions(self, strategy: Optional[ResponseStrategy]) -> str:
        """
        Orchestrates the assembly of system prompt directives based on the ResponseStrategy.
        """
        # 1 & 2: Construct a default strategy to avoid logic duplication
        if strategy is None:
            logger.debug("Strategy is None. Using default fallback strategy.")
            strategy = ResponseStrategy(
                depth=self._DEFAULT_DEPTH,
                tone=self._DEFAULT_TONE,
                structure=["paragraphs"],
                emoji_strategy=EmojiStrategy(
                    use=False, 
                    purpose=self._DEFAULT_PURPOSE, 
                    intensity=self._DEFAULT_INTENSITY
                )
            )

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

        return "\\n".join(directives)

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
            if clean_item:
                valid_items.append(clean_item)
                
        if not valid_items:
            logger.debug("No valid structure items found after filtering. Skipping structural directive.")
            return None
            
        struct_str = ", ".join(valid_items)
        return f"- STRUCTURAL REQUIREMENT: Format your response using: {struct_str}."
'''

with open('backend/lystra/generation/style_controller.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("style_controller.py patched")
