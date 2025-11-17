import pytest
import uuid # Added import for uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.utils.database import Base # Only import Base
from app.dependencies import get_db # Import get_db from dependencies
from app.models import user, product, price_history, notification_queue # Import all models

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:" # Use this for a truly in-memory db that resets on each test run

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="session", scope="module")
def session_fixture():
    Base.metadata.drop_all(engine) # Drop existing tables
    Base.metadata.create_all(engine) # Create tables
    with TestingSessionLocal() as session:
        yield session
    Base.metadata.drop_all(engine) # Clean up after tests

@pytest.fixture(name="client", scope="module")
def client_fixture(session):
    def override_get_db():
        yield session
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# Fixture for a test user
@pytest.fixture(name="test_user")
def test_user_fixture(client, session):
    unique_email = f"test_{uuid.uuid4()}@example.com" # Generate unique email
    user_data = {
        "name": "Test User",
        "email": unique_email,
        "password": "testpass"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    return response.json()

from unittest.mock import patch, MagicMock # Import patch and MagicMock
from bs4 import BeautifulSoup # Import BeautifulSoup
from app.scrapers.generic_scraper import GenericScraper # Import GenericScraper
from app.scrapers.scraper_factory import get_scraper as original_get_scraper # Import original get_scraper
from app.dependencies import get_product_scraper # Import get_product_scraper

# Fixture for a second test user
@pytest.fixture(name="test_user2")
def test_user2_fixture(client, session):
    unique_email = f"test2_{uuid.uuid4()}@example.com" # Generate unique email
    user_data = {
        "name": "Test User 2",
        "email": unique_email,
        "password": "testpass2"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    return response.json()

# Mock the scraper factory
@pytest.fixture(scope="module")
def mock_scraper_factory():
    def _mock_scraper_callable(url):
        mock_scraper_instance = MagicMock(spec=GenericScraper)
        mock_scraper_instance.get_product_info.return_value = {
            "name": "Test Product",
            "price": 100.0,
            "image_url": "http://example.com/image.jpg",
            "product_url": url, # Use the URL passed to the callable
        }
        return mock_scraper_instance

    app.dependency_overrides[get_product_scraper] = lambda: _mock_scraper_callable
    yield _mock_scraper_callable # Explicitly yield the callable
    app.dependency_overrides.pop(get_product_scraper, None)
