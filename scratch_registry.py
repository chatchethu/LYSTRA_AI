import re

with open("backend/tools/registry.py", "r") as f:
    content = f.read()

# Remove execute_tool entirely
content = re.sub(r"    async def execute_tool.*?return f\"Error executing tool {name}: {str\(e\)}\"", "", content, flags=re.DOTALL)

# Add property `tools`
property_str = """
    @property
    def tools(self) -> Dict[str, BaseTool]:
        return self._tools
"""
content = content.replace("    def get_all_tools(self) -> List[BaseTool]:\n        return list(self._tools.values())", "    def get_all_tools(self) -> List[BaseTool]:\n        return list(self._tools.values())\n" + property_str)

with open("backend/tools/registry.py", "w") as f:
    f.write(content)
