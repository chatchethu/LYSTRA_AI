with open('backend/lystra/memory/memory_extractor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix storing TEMPORARY info and implement Phase 7 & 8 logic
old_block = '''        # Do not store temporary, irrelevant, or sensitive information
        if mem_type in [MemoryType.IRRELEVANT, MemoryType.TEMPORARY, MemoryType.SENSITIVE]:
            return None
            
        persistence = classification.get("persistence", "none")
        if persistence == "none":
            return None'''

new_block = '''        # Do not store irrelevant or sensitive information
        if mem_type in [MemoryType.IRRELEVANT, MemoryType.SENSITIVE]:
            return None
            
        persistence = classification.get("persistence", "none")
        if persistence == "none" and mem_type != MemoryType.TEMPORARY:
            return None'''

content = content.replace(old_block, new_block)

# Fix object creation
old_obj = '''        # Step 3: Create the Structured Object (Phase 3)
        return MemoryObject(
            user_id=user_id,
            type=mem_type,
            key=self._generate_key(mem_type, message),'''

new_obj = '''        # Phase 7: Semantic Importance
        importance = 0.5
        if mem_type == MemoryType.IDENTITY:
            importance = 0.95
        elif mem_type == MemoryType.COMMUNICATION:
            importance = 0.75
        elif mem_type == MemoryType.TEMPORARY:
            importance = 0.3

        # Phase 8: Expiration for temporary
        from datetime import datetime, timezone, timedelta
        expires_at = None
        if mem_type == MemoryType.TEMPORARY:
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Step 3: Create the Structured Object (Phase 3)
        return MemoryObject(
            user_id=user_id,
            type=mem_type,
            importance=importance,
            expires_at=expires_at,
            key=self._generate_key(mem_type, message),'''

content = content.replace(old_obj, new_obj)

with open('backend/lystra/memory/memory_extractor.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated memory_extractor.py")
