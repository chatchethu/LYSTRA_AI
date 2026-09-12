"""
Phase 11: Open Threads
Tracks unresolved issues in the conversation.
"""
from typing import List
from pydantic import BaseModel, Field

class OpenThread(BaseModel):
    topic: str = Field(description="The topic of the thread (e.g. 'friendship', 'authentication bug')")
    issue: str = Field(description="The core unresolved issue")
    user_feeling: str = Field(description="How the user feels about this issue")
    unresolved: bool = True

class ThreadTracker:
    def __init__(self):
        self.threads: List[OpenThread] = []
        
    def add_or_update_thread(self, topic: str, issue: str, feeling: str):
        for t in self.threads:
            if t.topic == topic:
                t.issue = issue
                t.user_feeling = feeling
                t.unresolved = True
                return
        self.threads.append(OpenThread(topic=topic, issue=issue, user_feeling=feeling))
        
    def resolve_thread(self, topic: str):
        for t in self.threads:
            if t.topic == topic:
                t.unresolved = False
                
    def get_unresolved_threads_context(self) -> str:
        unresolved = [t for t in self.threads if t.unresolved]
        if not unresolved:
            return ""
        
        ctx = "OPEN UNRESOLVED THREADS:\n"
        for t in unresolved:
            ctx += f"- Topic: {t.topic} | Issue: {t.issue} | User Feeling: {t.user_feeling}\n"
        return ctx
