import re
with open('alembic/env.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''def run_migrations_online() -> None:
    config_section = config.get_section(config.config_ini_section, {})
    config_section['sqlalchemy.url'] = get_url()
    connectable = engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata,
            compare_type=True, compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

text = re.sub(r'def run_migrations_online\(\).*?$', replacement, text, flags=re.DOTALL)
with open('alembic/env.py', 'w', encoding='utf-8') as f:
    f.write(text)
