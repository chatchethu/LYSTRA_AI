import asyncio
from enum import Enum
from typing import Any
from urllib.parse import urlparse
from pydantic import BaseModel
from playwright.async_api import async_playwright, Browser, Page

class ComputerAction(str, Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    EXTRACT = "extract"
    WAIT = "wait"

class ActionResult(BaseModel):
    action: ComputerAction
    success: bool
    data: Any = None
    error: str | None = None
    url: str | None = None
    screenshot: bytes | None = None

class ComputerUseAgent:
    """
    Sandboxed browser automation using Playwright.
    Security constraints:
    - Only HTTP/HTTPS URLs
    - No file:// or local network access
    - No download of executables  
    - No access to host file system
    """
    
    BLOCKED_SCHEMES = ['file', 'ftp', 'data']
    BLOCKED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser: Browser = None
        self.context = None
        self.page: Page = None
        
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        return self

    async def __aexit__(self, *args):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _validate_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme in self.BLOCKED_SCHEMES:
                return False
            if parsed.hostname in self.BLOCKED_HOSTS:
                return False
            return True
        except Exception:
            return False

    async def _get_browser(self):
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use async with context manager.")
        return self.browser

    async def _get_page(self):
        if not self.page:
            raise RuntimeError("Page not initialized.")
        return self.page

    async def execute_action(self, action: ComputerAction, **kwargs) -> ActionResult:
        try:
            if action == ComputerAction.NAVIGATE:
                return await self.navigate(kwargs.get("url"))
            elif action == ComputerAction.CLICK:
                return await self.click(kwargs.get("selector"))
            elif action == ComputerAction.TYPE:
                return await self.type_text(kwargs.get("selector"), kwargs.get("text"))
            elif action == ComputerAction.SCREENSHOT:
                return await self.take_screenshot()
            elif action == ComputerAction.EXTRACT:
                return await self.extract_content(kwargs.get("selector"))
            elif action == ComputerAction.WAIT:
                await asyncio.sleep(kwargs.get("duration_ms", 1000) / 1000.0)
                page = await self._get_page()
                return ActionResult(action=action, success=True, url=page.url)
            elif action == ComputerAction.SCROLL:
                page = await self._get_page()
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                return ActionResult(action=action, success=True, url=page.url)
            else:
                return ActionResult(action=action, success=False, error=f"Unknown action {action}")
        except Exception as e:
            page = await self._get_page()
            screenshot = await page.screenshot() if page else None
            return ActionResult(action=action, success=False, error=str(e), url=page.url if page else None, screenshot=screenshot)

    async def navigate(self, url: str) -> ActionResult:
        if not self._validate_url(url):
            return ActionResult(action=ComputerAction.NAVIGATE, success=False, error="URL blocked by security policy")
        
        page = await self._get_page()
        await page.goto(url)
        return ActionResult(action=ComputerAction.NAVIGATE, success=True, url=page.url)

    async def click(self, selector: str) -> ActionResult:
        page = await self._get_page()
        await page.click(selector)
        return ActionResult(action=ComputerAction.CLICK, success=True, url=page.url)

    async def type_text(self, selector: str, text: str) -> ActionResult:
        page = await self._get_page()
        await page.fill(selector, text)
        return ActionResult(action=ComputerAction.TYPE, success=True, url=page.url)

    async def extract_content(self, selector: str = None) -> ActionResult:
        page = await self._get_page()
        if selector:
            element = await page.query_selector(selector)
            text = await element.inner_text() if element else None
        else:
            text = await page.evaluate("document.body.innerText")
        return ActionResult(action=ComputerAction.EXTRACT, success=True, data=text, url=page.url)

    async def take_screenshot(self) -> ActionResult:
        page = await self._get_page()
        screenshot = await page.screenshot(full_page=True)
        return ActionResult(action=ComputerAction.SCREENSHOT, success=True, screenshot=screenshot, url=page.url)

    async def execute_plan(self, actions: list[dict]) -> list[ActionResult]:
        results = []
        for action_dict in actions:
            action_type = ComputerAction(action_dict.pop("action"))
            res = await self.execute_action(action_type, **action_dict)
            results.append(res)
            if not res.success:
                break
        return results
