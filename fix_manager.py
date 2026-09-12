with open('backend/lystra/memory/memory_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_process = '''    async def process_user_message(self, user_id: str, message: str, context_history: List[str]):
        """
        Phase 1-9: Analyzes incoming messages to extract and update long-term memories.
        """
        candidate = await self.extractor.extract_candidate_memory(user_id, message, context_history)
        if candidate:
            # We would fetch existing for conflict resolution here
            existing_memories = await self.storage.fetch_active_memories(user_id)
            conflict = next((m for m in existing_memories if m.key == candidate.key), None)
            
            if conflict:
                resolved = self.updater.resolve_conflict(conflict, candidate)
                await self.storage.update_memory(resolved)
            else:
                await self.storage.add_memory(candidate)'''

new_process = '''    async def process_user_message(self, user_id: str, message: str, context_history: List[str], intent: str = "conversation"):
        """
        Phase 1-9 & 20-23: Analyzes incoming messages to extract, deduplicate, and update memories.
        """
        # Phase 20: Memory Extraction Timing
        # We only attempt extraction if the intent implies there might be personal info.
        if intent in ["greeting", "farewell", "acknowledgment"]:
            return

        candidate = await self.extractor.extract_candidate_memory(user_id, message, context_history)
        if candidate:
            existing_memories = await self.storage.fetch_active_memories(user_id)
            
            # Phase 22: Memory Deduplication (Semantic Identification)
            # Find semantic conflict instead of exact key match
            conflict = await self.updater.find_semantic_conflict(candidate, existing_memories, self.extractor.llm)
            
            if conflict:
                resolved = self.updater.resolve_conflict(conflict, candidate)
                await self.storage.update_memory(resolved)
            else:
                await self.storage.add_memory(candidate)
                
            # Phase 23: Memory Consolidation
            await self.updater.consolidate_memories(existing_memories, self.storage, self.extractor.llm)'''

content = content.replace(old_process, new_process)

with open('backend/lystra/memory/memory_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated memory_manager.py")
