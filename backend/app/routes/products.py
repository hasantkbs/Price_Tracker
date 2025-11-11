from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas
from ..models.product import Product, UserProduct
from ..models.user import User
from ..utils.database import SessionLocal
from ..scrapers.scraper_factory import get_scraper
from ..utils.security import decode_access_token
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/add")
async def add_product(product_data: schemas.ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scraper = get_scraper(product_data.product_url)
    product_info = scraper.get_product_info()

    if not product_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not scrape product information from the URL.",
        )

    product = db.query(Product).filter(Product.product_url == product_data.product_url).first()
    if not product:
        product = Product(
            name=product_info["name"],
            price=product_info["price"],
            image_url=product_info["image_url"],
            product_url=product_info["product_url"],
            site="Unknown" # Add logic to get site from URL
        )
        db.add(product)
        db.commit()
        db.refresh(product)

    user_product = UserProduct(
        user_id=current_user.id,
        product_id=product.id,
        target_price=product_data.target_price
    )
    db.add(user_product)
    db.commit()

    return {"message": "Product added successfully"}
