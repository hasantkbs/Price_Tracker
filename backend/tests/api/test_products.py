from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch
from backend.app.models.product import Product, UserProduct
from backend.app.models.price_history import PriceHistory
from backend.app.utils.database import SessionLocal
from datetime import datetime, timedelta
import uuid # Added import for uuid

def test_add_product(client: TestClient, test_user, mock_scraper_factory):
    unique_url = f"http://example.com/product_{uuid.uuid4()}" # Generate unique URL
    product_data = {
        "product_url": unique_url,
        "target_price": 90.0
    }
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    # Call the mock_scraper_factory to get the mock scraper instance
    mock_scraper = mock_scraper_factory(unique_url) # Pass the unique_url to the mock scraper
    response = client.post("/products/add", json=product_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Product added successfully"

def test_add_product_already_tracked(client: TestClient, test_user, mock_scraper_factory):
    unique_url = f"http://example.com/product_tracked_{uuid.uuid4()}" # Generate unique URL
    product_data = {
        "product_url": unique_url,
        "target_price": 90.0
    }
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    # Call the mock_scraper_factory to get the mock scraper instance
    mock_scraper = mock_scraper_factory(unique_url) # Pass the unique_url to the mock scraper
    client.post("/products/add", json=product_data, headers=headers) # Add once
    response = client.post("/products/add", json=product_data, headers=headers) # Add again
    assert response.status_code == 400
    assert response.json()["detail"] == "Product already tracked by this user."

def test_get_my_products(client: TestClient, test_user, mock_scraper_factory):
    # Add a product first
    unique_url = f"http://example.com/my_product_{uuid.uuid4()}" # Generate unique URL
    product_data = {
        "product_url": unique_url,
        "target_price": 90.0
    }
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    # Call the mock_scraper_factory to get the mock scraper instance
    mock_scraper = mock_scraper_factory(unique_url) # Pass the unique_url to the mock scraper
    add_response = client.post("/products/add", json=product_data, headers=headers)
    if add_response.status_code != 200:
        print(f"Add Product Response JSON: {add_response.json()}")
    response = client.get("/products/my_products", headers=headers)
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 1
    assert products[0]["name"] == "Test Product"
    assert products[0]["price"] == 100.0
    assert products[0]["target_price"] == 90.0
    assert products[0]["id"] is not None

def test_get_product_details(client: TestClient, test_user, mock_scraper_factory, session):
    # Add a product first to get its ID
    unique_url = f"http://example.com/product_detail_test_{uuid.uuid4()}" # Generate unique URL
    product_data = {
        "product_url": unique_url,
        "target_price": 90.0
    }
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    # Call the mock_scraper_factory to get the mock scraper instance
    mock_scraper = mock_scraper_factory(unique_url) # Pass the unique_url to the mock scraper
    add_response = client.post("/products/add", json=product_data, headers=headers)
    assert add_response.status_code == 200

    # Retrieve the product ID from the database
    product = session.query(Product).filter(Product.product_url == product_data["product_url"]).first()
    assert product is not None
    product_id = product.id

    # Add some price history
    session.add(PriceHistory(product_id=product_id, price=100.0, date=datetime.now() - timedelta(days=2)))
    session.add(PriceHistory(product_id=product_id, price=95.0, date=datetime.now() - timedelta(days=1)))
    session.add(PriceHistory(product_id=product_id, price=92.0, date=datetime.now()))
    session.commit()

    response = client.get(f"/products/{product_id}", headers=headers)
    assert response.status_code == 200
    product_details = response.json()
    assert product_details["name"] == "Test Product"
    assert product_details["price"] == 92.0 # Should reflect the latest price from history or scrape
    assert "price_history" in product_details
    assert isinstance(product_details["price_history"], list)
    assert len(product_details["price_history"]) == 3
    assert product_details["price_history"][0]["price"] == 100.0 # Check order

def test_get_product_details_not_tracking(client: TestClient, test_user, test_user2, mock_scraper_factory, session):
    # User1 adds a product
    unique_url = f"http://example.com/product_user1_{uuid.uuid4()}" # Generate unique URL
    product_data = {
        "product_url": unique_url,
        "target_price": 90.0
    }
    headers_user1 = {"Authorization": f"Bearer {test_user['access_token']}"}
    # Call the mock_scraper_factory to get the mock scraper instance
    mock_scraper = mock_scraper_factory(unique_url) # Pass the unique_url to the mock scraper
    client.post("/products/add", json=product_data, headers=headers_user1)
    
    product = session.query(Product).filter(Product.product_url == product_data["product_url"]).first()
    assert product is not None
    product_id = product.id

    # User2 tries to get details of product tracked by User1
    headers_user2 = {"Authorization": f"Bearer {test_user2['access_token']}"}
    response = client.get(f"/products/{product_id}", headers=headers_user2)
    assert response.status_code == 403
    assert response.json()["detail"] == "User is not tracking this product"

def test_get_product_details_unauthorized(client: TestClient, mock_scraper_factory, test_user, session):
    # Add a product first using an authorized user
    unique_url = f"http://example.com/unauth_product_test_{uuid.uuid4()}" # Generate unique URL
    product_data = {
        "product_url": unique_url,
        "target_price": 80.0
    }
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    # Call the mock_scraper_factory to get the mock scraper instance
    mock_scraper = mock_scraper_factory(unique_url) # Pass the unique_url to the mock scraper
    add_response = client.post("/products/add", json=product_data, headers=headers)
    assert add_response.status_code == 200

    product = session.query(Product).filter(Product.product_url == product_data["product_url"]).first()
    assert product is not None
    product_id = product.id

    # Now, try to get product details without authentication
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 401
