import requests
import json
import subprocess
import time
import os

BASE_URL = "http://127.0.0.1:8000"

def start_backend():
    print("Starting backend server with uvicorn...")
    # Start uvicorn in a separate process
    # Use --reload for development, remove for production
    process = subprocess.Popen(
        ["uvicorn", "backend.app.main:app", "--reload", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Give the server some time to start up
    time.sleep(5) 
    print("Backend server started.")
    return process

def register_and_login():
    email = input("Enter user email (e.g., test@example.com): ")
    password = input("Enter password: ")
    name = input("Enter your name: ")

    # Register
    register_data = {"name": name, "email": email, "password": password}
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 200:
            print("Registration successful!")
        elif response.status_code == 400 and "Email already registered" in response.text:
            print("Email already registered. Attempting to log in...")
        else:
            print(f"Registration failed: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("Could not connect to the backend. Is it running?")
        return None

    # Login
    login_data = {"email": email, "password": password} # Changed username to email
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data) # Changed data=login_data to json=login_data
        if response.status_code == 200:
            print("Login successful!")
            return response.json()["access_token"]
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("Could not connect to the backend. Is it running?")
        return None

def add_product(access_token):
    while True:
        product_url = input("Enter product URL (or 'q' to quit): ")
        if product_url.lower() == 'q':
            break
        try:
            target_price = float(input("Enter target price: "))
        except ValueError:
            print("Invalid price. Please enter a number.")
            continue

        headers = {"Authorization": f"Bearer {access_token}"}
        product_data = {"product_url": product_url, "target_price": target_price}
        
        try:
            response = requests.post(f"{BASE_URL}/products/add", json=product_data, headers=headers)
            if response.status_code == 200:
                print("Product added successfully!")
            else:
                print(f"Failed to add product: {response.status_code} - {response.text}")
        except requests.exceptions.ConnectionError:
            print("Could not connect to the backend. Is it running?")
            break

def main():
    backend_process = None
    try:
        backend_process = start_backend()
        access_token = register_and_login()

        if access_token:
            add_product(access_token)
        else:
            print("Authentication failed. Exiting.")

    finally:
        if backend_process:
            print("Stopping backend server...")
            backend_process.terminate()
            backend_process.wait()
            print("Backend server stopped.")
        print("\nTo run the Celery worker for price checking, open a new terminal in the 'Price_Tracker' directory and run:")
        print("celery -A backend.app.celery_app worker --loglevel=info -P solo")
        print("Or, if you want to run the beat scheduler (for periodic tasks), run in another terminal:")
        print("celery -A backend.app.celery_app beat --loglevel=info")

if __name__ == "__main__":
    main()
