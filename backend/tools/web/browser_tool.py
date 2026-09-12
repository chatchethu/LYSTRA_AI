from typing import Optional
from backend.tools import BaseTool, ToolPermissionLevel, ToolRiskLevel, ToolResult

# Note: Requires `playwright` to be installed and `playwright install` to have been run
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class BrowserTool(BaseTool):
    name = "browse_web"
    description = "Navigate to a URL and extract content from the page"
    permission_level = ToolPermissionLevel.NETWORK
    risk_level = ToolRiskLevel.MEDIUM
    
    def __init__(self):
        super().__init__()
        self._browser = None
        self._playwright = None
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "action": {"type": "string", "default": "read", "enum": ["read"]},
                "selector": {"type": "string"}
            },
            "required": ["url"]
        }
        
    async def _get_browser(self):
        if not self._playwright:
            self._playwright = await async_playwright().start()
        if not self._browser:
            self._browser = await self._playwright.chromium.launch(headless=True)
        return self._browser

    async def execute(self, user_id, task_id, conversation_id, request_id, url: str, action: str = "read", selector: Optional[str] = None) -> ToolResult:
        if not PLAYWRIGHT_AVAILABLE:
            return ToolResult(success=False, data=None, error="Playwright is not installed")
            
        from backend.tools.web.ssrf_check import validate_url, SSRFBlockedError, InvalidURLError
        try:
            await validate_url(url)
            browser = await self._get_browser()
            page = await browser.new_page()
            
            # Prevent redirects to internal IPs via request interception
            async def handle_route(route):
                request_url = route.request.url
                try:
                    await validate_url(request_url)
                    await route.continue_()
                except (ValueError, SSRFBlockedError, InvalidURLError):
                    await route.abort()
                    
            await page.route("**/*", handle_route)
            
            # Limit timeout to 15 seconds
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            if selector:
                elements = await page.locator(selector).all_inner_texts()
                content = "\n".join(elements)
            else:
                # Basic readability extraction
                content = await page.evaluate("document.body.innerText")
                
            await page.close()
            return ToolResult(success=True, data={"url": url, "content": content[:10000]})
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

class ScreenshotTool(BaseTool):
    name = "take_screenshot"
    description = "Take a screenshot of a webpage"
    permission_level = ToolPermissionLevel.NETWORK
    risk_level = ToolRiskLevel.LOW
    
    def __init__(self):
        super().__init__()
        self._browser_tool = BrowserTool()
        
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string"}
            },
            "required": ["url"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, url: str) -> ToolResult:
        if not PLAYWRIGHT_AVAILABLE:
            return ToolResult(success=False, data=None, error="Playwright is not installed")
            
        from backend.tools.web.ssrf_check import validate_url, SSRFBlockedError, InvalidURLError
        try:
            await validate_url(url)
            browser = await self._browser_tool._get_browser()
            page = await browser.new_page()
            
            async def handle_route(route):
                request_url = route.request.url
                try:
                    await validate_url(request_url)
                    await route.continue_()
                except (ValueError, SSRFBlockedError, InvalidURLError):
                    await route.abort()
                    
            await page.route("**/*", handle_route)
            
            await page.goto(url, timeout=15000)
            screenshot_bytes = await page.screenshot(full_page=True)
            import base64
            b64_img = base64.b64encode(screenshot_bytes).decode('utf-8')
            await page.close()
            
            return ToolResult(success=True, data={"image_base64": b64_img, "url": url})
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))
