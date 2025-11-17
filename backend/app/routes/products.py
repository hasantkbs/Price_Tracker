from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas
from ..models.product import Product, UserProduct
from ..models.price_history import PriceHistory # Import PriceHistory
from ..models.user import User
from ..dependencies import get_db, get_current_user, get_product_scraper # Import get_db and get_current_user
# Removed: from ..scrapers.scraper_factory import get_scraper
from typing import List # Import List

router = APIRouter(
    tags=["products"],
    responses={404: {"description": "Not found"}},
)
# Removed oauth2_scheme and local get_current_user function

@router.post("/add")
async def add_product(
    product_data: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    get_scraper_dependency: callable = Depends(get_product_scraper) # Inject the scraper dependency
):
    scraper = get_scraper_dependency(product_data.product_url) # Use the injected dependency
    product_info = scraper.get_product_info()

    if not product_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not scrape product information from the URL.",
        )
    
    # Ensure product_info is a plain dictionary
    product_info_dict = dict(product_info)

    # Check if product already exists in the products table
    product = db.query(Product).filter(Product.product_url == product_data.product_url).first()
    if not product:
        # If product does not exist, create and add it
        product = Product(
            product_name=product_info_dict["name"],
            current_price=product_info_dict["price"],
            image_url=product_info_dict["image_url"],
            product_url=product_info_dict["product_url"],
            site_name="Unknown" # Add logic to get site from URL
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Add initial price to history
        price_history = PriceHistory(
            product_id=product.id,
            price=product.current_price
        )
        db.add(price_history)
        db.commit()
    else:
        # If product exists, update its info (optional, but good practice)
        product.product_name = product_info_dict["name"]
        product.current_price = product_info_dict["price"]
        product.image_url = product_info_dict["image_url"]
        # product.site_name = "Unknown" # Update site if logic is added
        db.commit()
        db.refresh(product)

    # Check if the user is already tracking this product
    user_product = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.product_id == product.id
    ).first()

    if user_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already tracked by this user.",
        )

    # If not tracked, add it to user's tracked products
    user_product = UserProduct(
        user_id=current_user.id,
        product_id=product.id,
        target_price=product_data.target_price
    )
    db.add(user_product)
    db.commit()

    return {"message": "Product added successfully"}

@router.get("/my_products", response_model=List[schemas.ProductListItem])
async def get_my_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_products = db.query(UserProduct).filter(UserProduct.user_id == current_user.id).all()
    
    products_list = []
    for user_product in user_products:
        product = db.query(Product).filter(Product.id == user_product.product_id).first()
        if product:
            products_list.append(schemas.ProductListItem(
                id=product.id,
                product_name=product.product_name,
                current_price=product.current_price,
                image_url=product.image_url,
                product_url=product.product_url,
                site_name=product.site_name,
                last_checked=product.last_checked,
                target_price=user_product.target_price
            ))
    return products_list

@router.get("/{product_id}", response_model=schemas.ProductDetail)
async def get_product_details(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Ensure the user is tracking this product before showing details
    user_product = db.query(UserProduct).filter(
        UserProduct.user_id == current_user.id,
        UserProduct.product_id == product_id
    ).first()
    if not user_product:
        raise HTTPException(status_code=403, detail="User is not tracking this product")

    price_history_records = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id
    ).order_by(PriceHistory.checked_at).all()

    # Convert PriceHistory records to PriceHistoryEntry schema
    price_history_entries = [
        schemas.PriceHistoryEntry(price=record.price, checked_at=record.checked_at)
        for record in price_history_records
    ]

    return schemas.ProductDetail(
        id=product.id,
        product_name=product.product_name,
        current_price=product.current_price,
        image_url=product.image_url,
        product_url=product.product_url,
        site_name=product.site_name,
        last_checked=product.last_checked,
        price_history=price_history_entries
    )
