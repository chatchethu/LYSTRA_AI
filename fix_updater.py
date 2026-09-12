with open('backend/lystra/memory/memory_updater.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_methods = '''
    async def find_semantic_conflict(self, candidate: MemoryObject, existing: List[MemoryObject], llm) -> Optional[MemoryObject]:
        """Phase 22: Semantic Deduplication."""
        # Fast filter by type
        same_type = [m for m in existing if m.type == candidate.type]
        if not same_type:
            return None
            
        import json
        mem_json = [{"id": str(m.id), "content": m.value} for m in same_type]
        
        prompt = f"""We want to store a new memory: '{candidate.value}'
Here are existing memories: {json.dumps(mem_json)}

Does the new memory mean the EXACT SAME THING as any existing memory, or does it directly contradict/update one of them?
If yes, return a JSON object with 'conflict_id': '<the id>'.
If no, return 'conflict_id': null.
Return ONLY valid JSON."""

        try:
            messages = [{"role": "system", "content": "You are a semantic memory deduplicator."}, {"role": "user", "content": prompt}]
            resp = await llm.chat(messages, model="llama3.2:latest", format="json")
            data = json.loads(resp)
            c_id = data.get("conflict_id")
            if c_id:
                for m in same_type:
                    if str(m.id) == c_id:
                        return m
        except Exception:
            pass
        return None

    async def consolidate_memories(self, memories: List[MemoryObject], storage, llm):
        """Phase 23: Memory Consolidation."""
        from .schemas import MemoryType, MemoryStatus
        # Consolidate communication preferences if there are many
        comm_mems = [m for m in memories if m.type == MemoryType.COMMUNICATION and m.status == MemoryStatus.ACTIVE]
        if len(comm_mems) < 3:
            return
            
        import json
        mem_json = [{"id": str(m.id), "content": m.value} for m in comm_mems]
        
        prompt = f"""The user has multiple communication preferences: {json.dumps(mem_json)}.
Can you consolidate these into a SINGLE, comprehensive preference sentence?
Return JSON: {{"consolidated": "The single sentence..."}}"""

        try:
            messages = [{"role": "system", "content": "You consolidate preferences."}, {"role": "user", "content": prompt}]
            resp = await llm.chat(messages, model="llama3.2:latest", format="json")
            data = json.loads(resp)
            consolidated_text = data.get("consolidated")
            
            if consolidated_text:
                # Mark old ones as superseded
                for m in comm_mems:
                    m.status = MemoryStatus.SUPERSEDED
                    await storage.update_memory(m)
                
                # Create the new consolidated memory
                from .schemas import MemoryObject, MemorySource
                new_mem = MemoryObject(
                    user_id=comm_mems[0].user_id,
                    type=MemoryType.COMMUNICATION,
                    key="consolidated_preference",
                    value=consolidated_text,
                    importance=0.8,
                    confidence=0.9,
                    source=MemorySource.INFERRED
                )
                await storage.add_memory(new_mem)
        except Exception:
            pass
'''

content += new_methods

with open('backend/lystra/memory/memory_updater.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated memory_updater.py")
