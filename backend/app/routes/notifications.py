from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..dependencies import get_db, get_current_user # Import get_current_user
from ..models.notification_queue import NotificationQueue
from ..schemas import Notification
from ..models.user import User # Import User model for type hinting

router = APIRouter(
    tags=["notifications"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{user_id}", response_model=List[Notification])
def get_user_notifications(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Ensure the authenticated user is requesting their own notifications
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these notifications")

    notifications = db.query(NotificationQueue).filter(NotificationQueue.user_id == user_id).all()
    
    return notifications

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notification = db.query(NotificationQueue).filter(NotificationQueue.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Ensure the authenticated user owns this notification
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this notification")

    db.delete(notification)
    db.commit()
    return {"ok": True}
