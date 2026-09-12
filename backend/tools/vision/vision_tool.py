from enum import Enum
from typing import Any
from backend.multimodal.vision import VisionProcessor, VisionCapability

class ToolPermissionLevel(str, Enum):
    READ = "read"
    EXECUTE = "execute"
    WRITE = "write"

class ToolRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class BaseTool:
    name: str
    description: str
    permission_level: ToolPermissionLevel
    risk_level: ToolRiskLevel

class ToolResult:
    def __init__(self, success: bool, data: Any, error: str = None):
        self.success = success
        self.data = data
        self.error = error

class AnalyzeImageTool(BaseTool):
    name = "analyze_image"
    description = "Analyze, describe, or extract text from an image"
    permission_level = ToolPermissionLevel.READ
    risk_level = ToolRiskLevel.LOW
    
    def __init__(self, vision_processor: VisionProcessor):
        self.vision_processor = vision_processor
        
    async def execute(self, user_id, task_id, conversation_id, request_id, image_path: str, capability: str = "describe", question: str = None) -> ToolResult:
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
                
            cap_enum = VisionCapability(capability)
            result = await self.vision_processor.process(image_data, cap_enum, prompt=question)
            return ToolResult(success=True, data=result.dict())
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

class TakeScreenshotTool(BaseTool):
    name = "capture_screenshot"
    description = "Take a screenshot of the current screen or a URL"
    permission_level = ToolPermissionLevel.EXECUTE
    risk_level = ToolRiskLevel.MEDIUM
    
    async def execute(self, user_id, task_id, conversation_id, request_id, url: str = None, region: dict = None) -> ToolResult:
        try:
            if url:
                from backend.multimodal.computer_use import ComputerUseAgent
                async with ComputerUseAgent(headless=True) as agent:
                    res = await agent.navigate(url)
                    if not res.success:
                        return ToolResult(success=False, data=None, error=res.error)
                    shot_res = await agent.take_screenshot()
                    return ToolResult(success=shot_res.success, data={"screenshot_bytes": shot_res.screenshot}, error=shot_res.error)
            else:
                import pyautogui
                import io
                screenshot = pyautogui.screenshot(region=(region['left'], region['top'], region['width'], region['height']) if region else None)
                output = io.BytesIO()
                screenshot.save(output, format="PNG")
                return ToolResult(success=True, data={"screenshot_bytes": output.getvalue()})
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))
