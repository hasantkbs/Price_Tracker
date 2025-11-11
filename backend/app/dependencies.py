from sqlalchemy.orm import Session
from backend.app.utils.database import SessionLocal
from fastapi import Depends, HTTPException, status # Added
from backend.app.models.user import User # Added
from backend.app.utils.security import decode_access_token # Added
from fastapi.security import OAuth2PasswordBearer # Added
from backend.app.scrapers.scraper_factory import get_scraper as scraper_factory_get_scraper # Import the actual get_scraper

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") # Added

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Added get_current_user function
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

# New dependency for get_scraper
def get_product_scraper():
    return scraper_factory_get_scraper
