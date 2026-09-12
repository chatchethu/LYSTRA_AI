import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine
from backend.config import get_settings

@pytest.mark.integration
def test_schema_is_consistent():
    """
    Ensures that the SQLAlchemy models match the Alembic migrations
    and the actual PostgreSQL schema without any pending changes.
    """
    settings = get_settings()
    # Use sync engine for alembic check
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(db_url)
    
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        
        # Check if current DB revision is up to date with heads
        current_rev = context.get_current_revision()
        heads = script.get_revisions(script.get_heads())
        
        # We assume a single head in our setup
        head_rev = heads[0].revision if heads else None
        
        assert current_rev == head_rev, f"Database schema is not up to date. Current: {current_rev}, Head: {head_rev}"

        # We cannot easily programmatically run `alembic check` without capturing stdout or using internals,
        # but the command `alembic check` itself asserts there are no missing auto-generations.
        # As long as heads match, we consider it consistent for this test.
        # We can also use alembic.autogenerate.compare_metadata to strictly verify no changes are pending.

    # Advanced verification: check if there are any un-migrated changes in SQLAlchemy models
    from backend.db.models.base import Base
    from backend.db.models import __all__ # Ensure all models are loaded
    from alembic.autogenerate import compare_metadata
    
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        diff = compare_metadata(context, Base.metadata)
        
        # If diff is empty, there are no pending changes
        assert not diff, f"Schema mismatch detected: {diff}"
