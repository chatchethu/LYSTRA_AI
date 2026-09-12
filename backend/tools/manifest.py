# Explicit manifest of approved tools to load.
# This prevents arbitrary code execution via dynamic file discovery and ensures deterministic load order.
TOOL_MODULES = [
    "backend.tools.code.code_runner",
    "backend.tools.communication.email_tool",
    "backend.tools.files.file_ops",
    "backend.tools.utility.calculator",
    "backend.tools.utility.datetime_tool",
    "backend.tools.utility.memory_tool",
    "backend.tools.utility.weather",
    "backend.tools.vision.vision_tool",
    "backend.tools.web.browser_tool",
    "backend.tools.web.web_search"
]
