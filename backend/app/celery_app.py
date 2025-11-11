from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "price_tracker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.beat_schedule = {
    "check-prices-every-6-hours": {
        "task": "app.tasks.check_prices",
        "schedule": 21600.0,  # 6 hours in seconds
    }
}

celery_app.conf.timezone = "UTC"
