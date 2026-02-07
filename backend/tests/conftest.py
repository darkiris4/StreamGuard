import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = ROOT / "backend"
sys.path.insert(0, str(BACKEND_PATH))

TEST_DB = ROOT / "backend" / "tests" / "test.db"
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{TEST_DB}"


@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    if TEST_DB.exists():
        TEST_DB.unlink()
    from db import init_db

    init_db()
    yield
    if TEST_DB.exists():
        TEST_DB.unlink()
