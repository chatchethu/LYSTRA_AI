from pydantic import BaseModel, Field
from .clock import get_current_datetime, get_current_date, get_current_time, get_timezone, get_day_of_week

class RuntimeContext(BaseModel):
    current_datetime: str = Field(default_factory=lambda: get_current_datetime().isoformat())
    current_date: str = Field(default_factory=get_current_date)
    current_time: str = Field(default_factory=get_current_time)
    timezone: str = Field(default_factory=get_timezone)
    day_of_week: str = Field(default_factory=get_day_of_week)
    
    @property
    def formatted_time(self) -> str:
        return self.current_datetime

def get_runtime_context() -> RuntimeContext:
    return RuntimeContext()
