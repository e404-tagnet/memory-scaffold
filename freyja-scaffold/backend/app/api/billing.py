from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import current_user_id
from app.core.config import get_settings
from app.services.payment import StripeService
from app.services.user import UserService
from app.schemas.user import CheckoutSession, CheckoutSessionResponse

router = APIRouter(prefix="/api/billing", tags=["billing"])
settings = get_settings()


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def checkout(
    data: CheckoutSession,
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_db),
):
    user_svc = UserService(session)
    user = await user_svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    svc = StripeService()
    price_id = settings.stripe_price_premium
    if not price_id:
        raise HTTPException(status_code=500, detail="Premium price ID not configured")

    result = await svc.create_checkout_session(
        user_id=user_id,
        price_id=price_id,
        success_url=data.success_url,
        cancel_url=data.cancel_url,
        customer_email=user.email,
    )
    return CheckoutSessionResponse(url=result["url"], session_id=result["session_id"])


@router.post("/webhook")
async def webhook(request: Request, session: AsyncSession = Depends(get_db)):
    """Stripe webhook endpoint — no auth required."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature")

    svc = StripeService()
    try:
        result = await svc.handle_webhook(payload, sig_header)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if result["status"] == "success":
        user_id = result["user_id"]
        user_svc = UserService(session)
        await user_svc.upgrade_tier(user_id, "premium")

    return {"received": True}
