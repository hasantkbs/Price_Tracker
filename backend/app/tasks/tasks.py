from ..celery_app import celery_app
from ..utils.database import SessionLocal
from ..models.product import Product, UserProduct # Import UserProduct
from ..models.price_history import PriceHistory
from ..models.notification_queue import NotificationQueue
from ..scrapers.scraper_factory import get_scraper
from ..utils.logging import get_logger

logger = get_logger(__name__)

@celery_app.task(name="app.tasks.check_prices")
def check_prices():
    logger.info("Starting price check task...")
    db = SessionLocal()
    try:
        # Fetch all UserProduct entries to check prices for each user's tracked products
        user_products = db.query(UserProduct).all()
        
        processed_products = set() # To avoid scraping the same product multiple times if tracked by multiple users

        for user_product in user_products:
            product = db.query(Product).filter(Product.id == user_product.product_id).first()
            if not product:
                logger.warning(f"Product with ID {user_product.product_id} not found for UserProduct ID {user_product.id}")
                continue

            # Only scrape if the product hasn't been processed in this run yet
            if product.id not in processed_products:
                scraper = get_scraper(product.product_url)
                product_info = scraper.get_product_info()

                if product_info:
                    new_price = product_info["price"]
                    if new_price != product.price:
                        logger.info(f"Price change detected for {product.name}. Old price: {product.price}, New price: {new_price}")
                        
                        # Save price history
                        price_history = PriceHistory(
                            product_id=product.id,
                            price=new_price
                        )
                        db.add(price_history)
                        
                        # Update product price
                        product.price = new_price
                        db.add(product)
                        db.commit()
                        db.refresh(product)
                    else:
                        logger.info(f"No general price change for {product.name}")
                else:
                    logger.warning(f"Could not get product info for {product.name} ({product.product_url})")
                
                processed_products.add(product.id) # Mark as processed

            # Now, check for user-specific price drop against target_price
            # Re-fetch product to ensure we have the latest price after potential update
            product = db.query(Product).filter(Product.id == user_product.product_id).first()
            if product and product.price <= user_product.target_price:
                # Check if a notification for this user/product/price has already been sent recently
                # This prevents spamming notifications for the same price drop
                # For simplicity, we'll just add a new one for now. A more robust solution
                # would involve checking the NotificationQueue for recent entries.
                
                notification_message = f"Price of {product.name} dropped to {product.price}! Your target was {user_product.target_price}."
                logger.info(f"Price drop detected for user {user_product.user_id} on {product.name}. New price: {product.price}. Target: {user_product.target_price}. Adding to NotificationQueue.")
                
                notification = NotificationQueue(
                    user_id=user_product.user_id,
                    product_id=product.id,
                    message=notification_message
                )
                db.add(notification)
                db.commit()
                logger.info(f"Notification added for user {user_product.user_id} and product {product.name}")
            else:
                if product:
                    logger.info(f"No price drop to target for user {user_product.user_id} on {product.name}. Current price: {product.price}, Target: {user_product.target_price}")
                else:
                    logger.warning(f"Product not found for UserProduct ID {user_product.id} during target price check.")

    except Exception as e:
        logger.error(f"Error in price check task: {e}", exc_info=True)
    finally:
        db.close()
    logger.info("Price check task finished.")
