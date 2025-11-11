from fastapi import FastAPI
from .utils.error_handler import exception_handler
from .utils.database import create_tables
from .routes import auth, products, notifications
from .celery_app import celery_app # Import celery_app

app = FastAPI()

app.add_event_handler("startup", create_tables)
app.add_exception_handler(Exception, exception_handler)

app.include_router(auth.router, prefix="/auth")
app.include_router(products.router, prefix="/products")
app.include_router(notifications.router, prefix="/notifications") # Include the new notifications router

@app.get("/")
def read_root():
    return {"Hello": "World"}
