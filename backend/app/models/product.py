from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from ..utils.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    image_url = Column(String)
    product_url = Column(String, unique=True, index=True)
    site = Column(String)

    users = relationship("UserProduct", back_populates="product")

class UserProduct(Base):
    __tablename__ = "user_products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    target_price = Column(Float)

    user = relationship("User", back_populates="products")
    product = relationship("Product", back_populates="users")

# Add the relationship to the User model
from ..models.user import User
User.products = relationship("UserProduct", back_populates="user")
