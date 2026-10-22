import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bots.engine.db import Database  # noqa: E402
from bots.tarot.cards import Deck  # noqa: E402


@pytest.fixture
def db():
    return Database(":memory:")


@pytest.fixture(scope="session")
def deck():
    return Deck()


@pytest.fixture
def now():
    return datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)
