"""Shared pytest fixtures."""
from __future__ import annotations

import pytest

from jarvis.app.settings import Settings
from jarvis.storage.database import Database
from jarvis.storage.models import AgentMode


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "test.db")
    yield database
    database.close()


@pytest.fixture
def settings():
    # Default to controlled mode so confirmation logic is exercised without
    # assist-mode blocking everything.
    return Settings(agent_mode=AgentMode.CONTROLLED)
