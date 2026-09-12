from pydantic import BaseModel
from typing import List, Optional

class Project(BaseModel):
    """Phase 99: Personal Project Memory"""
    id: str
    user_id: str
    name: str # e.g. "Travel", "Coding"
    goals: List[str] = []
    
class ProjectManager:
    def create_project(self, user_id: str, name: str) -> Project:
        pass
        
    def associate_memory_with_project(self, memory_id: str, project_id: str):
        # All retrieval scopes can be restricted to `project_id`
        pass

