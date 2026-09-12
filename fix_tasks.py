with open('backend/workers/tasks.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Wait for background tasks to finish before closing the loop
cleanup_code = '''
            # Phase 40: Safe Async Shutdown
            # The execution_manager fires off background tasks (like memory extraction)
            # using asyncio.create_task(). If we exit this function, asyncio.run() will
            # instantly murder the event loop, causing DB socket crashes for memory extraction.
            # We must gracefully await all outstanding background tasks before returning.
            pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if pending:
                logger.info("awaiting_background_tasks", count=len(pending))
                await asyncio.gather(*pending, return_exceptions=True)
                
    except Exception as e:'''

content = content.replace('    except Exception as e:', cleanup_code)

with open('backend/workers/tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied graceful shutdown to Celery tasks")
