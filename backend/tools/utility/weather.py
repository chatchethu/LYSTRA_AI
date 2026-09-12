import httpx
from backend.tools import BaseTool, ToolPermissionLevel, ToolRiskLevel, ToolResult

class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Get current weather information for a location"
    permission_level = ToolPermissionLevel.NETWORK
    risk_level = ToolRiskLevel.LOW
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "units": {"type": "string", "default": "metric", "enum": ["metric", "imperial"]}
            },
            "required": ["location"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, location: str, units: str = "metric") -> ToolResult:
        try:
            # Using wttr.in for simple text-based JSON weather info
            url = f"https://wttr.in/{location}?format=j1"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return ToolResult(success=False, data=None, error=f"Failed to fetch weather for {location}")
                    
                data = response.json()
                current = data.get("current_condition", [{}])[0]
                temp = current.get("temp_C") if units == "metric" else current.get("temp_F")
                desc = current.get("weatherDesc", [{"value": "Unknown"}])[0].get("value")
                
                return ToolResult(success=True, data={
                    "location": location,
                    "temperature": temp,
                    "units": "C" if units == "metric" else "F",
                    "description": desc,
                    "raw_data": current
                })
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))
