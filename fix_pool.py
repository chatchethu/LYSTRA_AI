with open('backend/db/session.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_engine = '''engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)'''

new_engine = '''from sqlalchemy.pool import NullPool
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=settings.DEBUG,
)'''

content = content.replace(old_engine, new_engine)

with open('backend/db/session.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied NullPool to fix multiprocessing socket corruption")
