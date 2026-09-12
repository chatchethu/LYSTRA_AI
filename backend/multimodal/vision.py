import base64
import io
from enum import Enum
from pydantic import BaseModel

try:
    from PIL import Image as _PILImage
    _PIL_AVAILABLE = True
except ImportError:
    _PILImage = None
    _PIL_AVAILABLE = False


class VisionCapability(str, Enum):
    DESCRIBE = "describe"       # General image description
    OCR = "ocr"                 # Extract text from image
    ANALYZE_UI = "analyze_ui"   # Analyze UI/screenshot
    ANALYZE_CHART = "analyze_chart"  # Analyze charts/diagrams
    ANSWER_QUESTION = "answer_question"  # VQA

class VisionResult(BaseModel):
    capability: VisionCapability
    description: str
    extracted_text: str | None = None
    objects_detected: list[str] | None = None
    confidence: float
    metadata: dict = {}

class VisionProcessor:
    """
    Multi-capability vision processing using qwen2.5vl:3b via Ollama.
    Handles image preprocessing, capability routing, and result formatting.
    """
    
    def __init__(self, llm_gateway):
        self.llm_gateway = llm_gateway
        
    async def process(self, image_data: bytes, capability: VisionCapability, prompt: str = None) -> VisionResult:
        processed_data = self._preprocess_image(image_data)
        
        if capability == VisionCapability.DESCRIBE:
            result = await self.describe_image(processed_data)
            return VisionResult(capability=capability, description=result, confidence=0.9)
        elif capability == VisionCapability.OCR:
            result = await self.extract_text(processed_data)
            return VisionResult(capability=capability, description="Text extracted successfully", extracted_text=result, confidence=0.9)
        elif capability == VisionCapability.ANALYZE_UI:
            result = await self.analyze_screenshot(processed_data, prompt)
            return VisionResult(capability=capability, description=result, confidence=0.85)
        elif capability == VisionCapability.ANALYZE_CHART:
            result = await self.analyze_chart(processed_data)
            return VisionResult(capability=capability, description=result, confidence=0.85)
        elif capability == VisionCapability.ANSWER_QUESTION:
            result = await self.answer_question(processed_data, prompt or "What is in this image?")
            return VisionResult(capability=capability, description=result, confidence=0.9)
        else:
            raise ValueError(f"Unknown vision capability: {capability}")

    async def describe_image(self, image_data: bytes) -> str:
        prompt = "Describe this image in detail."
        b64_image = self._encode_image(image_data)
        return await self._call_llm_with_image(prompt, b64_image)

    async def extract_text(self, image_data: bytes) -> str:
        prompt = "Extract all text from this image exactly as it appears. Do not include any other text."
        b64_image = self._encode_image(image_data)
        return await self._call_llm_with_image(prompt, b64_image)

    async def analyze_screenshot(self, image_data: bytes, question: str = None) -> str:
        base_prompt = "Analyze this screenshot and describe the UI elements, layout, and functionality."
        prompt = f"{base_prompt} {question}" if question else base_prompt
        b64_image = self._encode_image(image_data)
        return await self._call_llm_with_image(prompt, b64_image)

    async def analyze_chart(self, image_data: bytes) -> str:
        prompt = "Analyze this chart or diagram. Extract the key data points, trends, and conclusions."
        b64_image = self._encode_image(image_data)
        return await self._call_llm_with_image(prompt, b64_image)

    async def answer_question(self, image_data: bytes, question: str) -> str:
        b64_image = self._encode_image(image_data)
        return await self._call_llm_with_image(question, b64_image)

    def _preprocess_image(self, image_data: bytes) -> bytes:
        if not _PIL_AVAILABLE:
            return image_data  # Skip preprocessing — Pillow not installed
        max_size = (1024, 1024)
        try:
            image = _PILImage.open(io.BytesIO(image_data))
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.thumbnail(max_size, _PILImage.Resampling.LANCZOS)
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=85)
            return output.getvalue()
        except Exception:
            return image_data

    def _encode_image(self, image_data: bytes) -> str:
        return base64.b64encode(image_data).decode('utf-8')
        
    async def _call_llm_with_image(self, prompt: str, base64_image: str) -> str:
        # Mock LLM API call formatting
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
        response = await self.llm_gateway.chat(messages=messages, model="qwen2.5vl:3b")
        return response.choices[0].message.content
