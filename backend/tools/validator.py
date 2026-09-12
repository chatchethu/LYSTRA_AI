from typing import Dict, Any, Type
from pydantic import BaseModel, create_model, Field

def json_schema_to_pydantic(name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
    """
    Dynamically creates a Pydantic model from a JSON schema.
    Used for Phase 41 Tool Argument Validation.
    """
    fields = {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    for field_name, field_info in properties.items():
        field_type = str
        t = field_info.get("type", "string")
        if t == "integer": field_type = int
        elif t == "number": field_type = float
        elif t == "boolean": field_type = bool
        elif t == "array": field_type = list
        elif t == "object": field_type = dict

        is_required = field_name in required
        default_val = field_info.get("default", ...) if is_required else field_info.get("default", None)
        
        fields[field_name] = (field_type, Field(default=default_val, description=field_info.get("description", "")))

    return create_model(name, **fields)
