import logging
from typing import Optional

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class StripeService:
    """Stripe payment scaffolding. Set keys in .env to activate."""

    def __init__(self):
        self.enabled = bool(settings.stripe_secret_key)
        if self.enabled:
            import stripe
            stripe.api_key = settings.stripe_secret_key
            self.stripe = stripe
        else:
            self.stripe = None

    async def create_checkout_session(
        self,
        user_id: int,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
    ) -> dict:
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")

        # Create customer if needed
        customer = None
        # In real usage: look up existing stripe_customer_id from DB
        # For scaffold, we create new each time
        customer_data = {}
        if customer_email:
            customer_data["email"] = customer_email

        customer = self.stripe.Customer.create(**customer_data)

        session = self.stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": str(user_id)},
        )
        return {"url": session.url, "session_id": session.id}

    async def handle_webhook(self, payload: bytes, sig_header: str) -> dict:
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")

        event = self.stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = int(session.get("metadata", {}).get("user_id", 0))
            # Here: upgrade user tier in DB
            logger.info(f"Checkout completed for user {user_id}")
            return {"status": "success", "user_id": user_id, "event": event["type"]}

        return {"status": "ignored", "event": event["type"]}
