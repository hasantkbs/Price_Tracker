from pydantic import BaseModel
from datetime import datetime
from typing import List

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int

class TokenData(BaseModel):
    email: str | None = None

class ProductCreate(BaseModel):
    product_url: str
    target_price: float | None = None

class Notification(BaseModel):
    id: int
    user_id: int
    product_id: int
    message: str
    created_at: datetime

    class Config:
        from_attributes = True

class PriceHistoryEntry(BaseModel):
    price: float
    timestamp: datetime

    class Config:
        from_attributes = True

class ProductDetail(BaseModel):
    id: int
    name: str
    price: float
    image_url: str
    product_url: str
    site: str
    price_history: List[PriceHistoryEntry] = []

    class Config:
        from_attributes = True

class ProductListItem(BaseModel):
    id: int
    name: str
    price: float
    image_url: str
    product_url: str
    site: str
    target_price: float | None = None # Include target price from UserProduct

    class Config:
        from_attributes = True
