"""Pytest configuration and shared fixtures"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.base import Base
# Import models to ensure they are registered with Base
from src.db import models  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["SECRET_KEY"] = "test_secret_key"
    os.environ["DEBUG"] = "True"
    yield
    # Cleanup after tests
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session with in-memory SQLite
    
    Using a shared memory database with URI to allow multiple connections
    """
    engine = create_engine(
        "sqlite:///file:testdb?mode=memory&cache=shared&uri=true",
        echo=False,
        connect_args={"check_same_thread": False, "uri": True}
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()

