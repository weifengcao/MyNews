"""FastAPI application for managing user subscriptions."""
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from common import config
from common.database import get_db_session
from database.models import Subscription

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)

app = FastAPI(
    title="MyNews API",
    description="API for managing user subscriptions.",
    version="1.0.0",
)


class SubscriptionUpdate(BaseModel):
    selected_topics: Optional[List[str]] = None
    selected_sources: Optional[List[str]] = None
    delivery_schedule: Optional[str] = None
    breaking_news_enabled: Optional[bool] = None


class SubscriptionResponse(SubscriptionUpdate):
    user_id: str


@app.put("/subscriptions/{user_id}", response_model=SubscriptionResponse)
def update_subscription(user_id: str, sub_update: SubscriptionUpdate):
    """Update a user's subscription preferences in PostgreSQL."""
    with get_db_session() as db_session:
        subscription = (
            db_session.query(Subscription)
            .filter(Subscription.user_id == user_id)
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=404,
                detail=f"Subscription for user_id '{user_id}' not found.",
            )

        update_data = sub_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided.")

        for key, value in update_data.items():
            setattr(subscription, key, value)

        db_session.refresh(subscription)
        logging.info("Updated subscription for user: %s", user_id)
        return subscription
