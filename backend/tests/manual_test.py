from fastapi.testclient import TestClient
import pytest
import uuid
from app.main import app
from app.utils.database import SessionLocal, Base, engine
from app.dependencies import get_db
from app.models.product import Product, UserProduct
from app.models.price_history import PriceHistory
from app.models.notification_queue import NotificationQueue
from unittest.mock import MagicMock, patch
from app.scrapers.generic_scraper import GenericScraper
from app.dependencies import get_product_scraper

# Setup for test client and database
@pytest.fixture(scope="module")
def session():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        yield session
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="module")
def client(session):
    def override_get_db():
        yield session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# Fixture for a test user
@pytest.fixture(scope="module")
def test_user(client):
    unique_email = f"test_user_{uuid.uuid4()}@example.com"
    user_data = {
        "name": "Test User",
        "email": unique_email,
        "password": "testpassword"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    return response.json()

def test_price_tracking_scenario(client: TestClient, test_user, session):
    # Create the single mock scraper instance
    mock_scraper_instance = MagicMock(spec=GenericScraper)

    def override_get_product_scraper():
        return lambda url: mock_scraper_instance

    app.dependency_overrides[get_product_scraper] = override_get_product_scraper
    
    with patch('app.tasks.tasks.get_scraper', return_value=mock_scraper_instance):
        # 1. Add a product
        unique_product_url = f"http://example.com/tracked_product_{uuid.uuid4()}"
        product_data = {
            "product_url": unique_product_url,
            "target_price": 90.0
        }
        headers = {"Authorization": f"Bearer {test_user['access_token']}"}
        
        # Configure the mock scraper for the add product call
        mock_scraper_instance.get_product_info.return_value = {
            "name": "Mock Product",
            "price": 100.0,
            "image_url": "http://example.com/mock_image.jpg",
            "product_url": unique_product_url,
        }
        add_response = client.post("/products/add", json=product_data, headers=headers)
        assert add_response.status_code == 200
        print(f"Add Product Response: {add_response.json()}")

        # Verify product is added and initial price is recorded
        product_in_db = session.query(Product).filter(Product.product_url == unique_product_url).first()
        assert product_in_db is not None
        assert product_in_db.current_price == 100.0

        # 2. Simulate a price drop by changing the mock scraper's return value
        mock_scraper_instance.get_product_info.return_value = {
            "name": "Mock Product",
            "price": 85.0, # Price drop!
            "image_url": "http://example.com/mock_image.jpg",
            "product_url": unique_product_url,
        }

        # 3. Manually call the check_prices task (Celery task)
        from app.tasks.tasks import check_prices
        check_prices()

        # 4. Check if price is updated and notification is generated
        session.expire_all() # Refresh session to get latest data
        updated_product = session.query(Product).filter(Product.product_url == unique_product_url).first()
        assert updated_product.current_price == 85.0

        notification = session.query(NotificationQueue).filter(
            NotificationQueue.user_id == test_user['user_id'],
            NotificationQueue.product_id == updated_product.id
        ).first()
        assert notification is not None
        assert "dropped to 85.0" in notification.message
        print(f"Notification Message: {notification.message}")

        # 5. Check product details via API
        response = client.get(f"/products/{updated_product.id}", headers=headers)
        assert response.status_code == 200
        product_details = response.json()
        assert product_details["current_price"] == 85.0
        assert len(product_details["price_history"]) == 2 # Initial price + dropped price
        assert product_details["price_history"][0]["price"] == 100.0
        assert product_details["price_history"][1]["price"] == 85.0

        # 6. Check user's notifications via API
        notifications_response = client.get("/notifications/", headers=headers)
        assert notifications_response.status_code == 200
        user_notifications = notifications_response.json()
        assert len(user_notifications) >= 1 # Could be more if other tests added notifications
        assert any("dropped to 85.0" in n["message"] for n in user_notifications)
        print("Price tracking scenario completed successfully!")

    app.dependency_overrides.clear()
