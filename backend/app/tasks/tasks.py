from ..celery_app import celery_app
from ..utils.database import SessionLocal
from ..models.product import Product
from ..models.price_history import PriceHistory
from ..models.notification_queue import NotificationQueue # Keep import for future use
from ..scrapers.scraper_factory import get_scraper
from ..utils.logging import get_logger

logger = get_logger(__name__)

@celery_app.task(name="app.tasks.check_prices")
def check_prices():
    logger.info("Starting price check task...")
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        for product in products:
            scraper = get_scraper(product.product_url)
            product_info = scraper.get_product_info()

            if product_info and product_info["price"] != product.price:
                logger.info(f"Price change detected for {product.name}. Old price: {product.price}, New price: {product_info['price']}")
                
                # Save price history
                price_history = PriceHistory(
                    product_id=product.id,
                    price=product_info["price"]
                )
                db.add(price_history)
                
                # Update product price
                product.price = product_info["price"]
                db.add(product)
                db.commit()
                db.refresh(product)

                # For now, just log the notification instead of sending to queue
                if product_info["price"] < product.price: # This logic needs to be refined to compare with target price
                    logger.info(f"Price drop detected for {product.name}. New price: {product_info['price']}. Notification would be sent.")
                    # In future, this would be replaced with actual notification sending logic
                    # notification = NotificationQueue(
                    #     user_id=1, # This needs to be dynamic, based on users tracking this product
                    #     product_id=product.id,
                    #     message=f"Price of {product.name} dropped to {product_info['price']}"
                    # )
                    # db.add(notification)
                    # db.commit()
                    # logger.info(f"Notification added for {product.name}")
            else:
                logger.info(f"No price change for {product.name}")
    except Exception as e:
        logger.error(f"Error in price check task: {e}")
    finally:
        db.close()
    logger.info("Price check task finished.")
