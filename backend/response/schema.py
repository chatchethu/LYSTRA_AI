"""
Schema Definitions — LYSTRA Dynamic Response System
Phase 1 & 2: Defines generic semantic UI blocks, completely decoupled from specific layouts.
"""

from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field

class BlockMetadata(BaseModel):
    priority: Literal["critical", "high", "normal", "low"] = "normal"
    density: Literal["compact", "comfortable"] = "comfortable"
    expandable: bool = False

class UIBlock(BaseModel):
    id: str = Field(description="Unique block identifier")
    type: str = Field(description="Semantic type: text, heading, list, table, code, callout, highlight_group")
    data: Dict[str, Any] = Field(description="The actual content data for the block")
    metadata: BlockMetadata = Field(default_factory=BlockMetadata)

class ResponseSchema(BaseModel):
    blocks: List[UIBlock]
