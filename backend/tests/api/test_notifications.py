from fastapi.testclient import TestClient
import pytest
from backend.app.models.notification_queue import NotificationQueue
from backend.app.models.product import Product, UserProduct
from backend.app.utils.database import SessionLocal
from datetime import datetime
import uuid # Added import for uuid

def test_get_user_notifications(client: TestClient, test_user, session):
    user_id = test_user["user_id"]
    access_token = test_user["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Add a dummy product and notification
    unique_url = f"url_{uuid.uuid4()}" # Generate unique URL
    product = Product(name="Test Notif Product", price=50.0, image_url="url", product_url=unique_url, site="site")
    session.add(product)
    session.commit()
    session.refresh(product)

    notification = NotificationQueue(
        user_id=user_id,
        product_id=product.id,
        message="Price drop for Test Notif Product!"
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)

    response = client.get(f"/notifications/{user_id}", headers=headers)
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 1
    assert notifications[0]["message"] == "Price drop for Test Notif Product!"
    assert notifications[0]["user_id"] == user_id
    assert notifications[0]["product_id"] == product.id

def test_get_user_notifications_unauthorized(client: TestClient, test_user):
    user_id = test_user["user_id"]
    response = client.get(f"/notifications/{user_id}")
    assert response.status_code == 401

def test_delete_notification(client: TestClient, test_user, session):
    user_id = test_user["user_id"]
    access_token = test_user["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Add a dummy product and notification
    unique_url = f"url_delete_{uuid.uuid4()}" # Generate unique URL
    product = Product(name="Product to Delete", price=10.0, image_url="url", product_url=unique_url, site="site")
    session.add(product)
    session.commit()
    session.refresh(product)

    notification = NotificationQueue(
        user_id=user_id,
        product_id=product.id,
        message="Delete me!"
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)

    notification_id = notification.id

    response = client.delete(f"/notifications/{notification_id}", headers=headers)
    assert response.status_code == 204

    # Verify it's deleted
    response = client.get(f"/notifications/{user_id}", headers=headers)
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 0

def test_delete_nonexistent_notification(client: TestClient, test_user):
    access_token = test_user["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.delete("/notifications/99999", headers=headers) # Non-existent ID
    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"

def test_delete_notification_unauthorized(client: TestClient):
    response = client.delete("/notifications/1")
    assert response.status_code == 401
