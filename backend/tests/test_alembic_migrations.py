import os
import tempfile
from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, inspect


@pytest.fixture
def temp_db_url():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    # Close file handle and remove it so sqlite creates it fresh
    if os.path.exists(db_path):
        os.remove(db_path)
    clean_path = db_path.replace("\\", "/")
    url = f"sqlite:///{clean_path}"
    yield url, db_path
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass


def test_alembic_upgrade_and_downgrade(temp_db_url):
    db_url, db_path = temp_db_url

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_path = os.path.join(backend_dir, "alembic.ini")

    alembic_cfg = Config(ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))

    # 1. Run upgrade head
    command.upgrade(alembic_cfg, "head")

    # Verify tables created
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = {
        "users",
        "connections",
        "subscriptions",
        "billing_evidence",
        "findings",
        "transactions",
        "actions",
    }
    assert expected_tables.issubset(set(tables))

    # 2. Run downgrade base
    command.downgrade(alembic_cfg, "base")

    # Verify tables removed
    inspector_after = inspect(engine)
    tables_after = inspector_after.get_table_names()
    for t in expected_tables:
        assert t not in tables_after

    engine.dispose()
