from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..utils.database import Base
from datetime import datetime

class NotificationQueue(Base):
    __tablename__ = "notification_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending") # e.g., "pending", "sent", "failed"

    user = relationship("User")
    product = relationship("Product")
