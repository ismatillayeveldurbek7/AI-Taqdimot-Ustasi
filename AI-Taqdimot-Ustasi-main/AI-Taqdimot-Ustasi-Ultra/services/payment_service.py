"""
Payment service layer.
Future-ready: add Click, Payme, Stripe, Telegram Payments as separate providers here.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Payment, User, CoinPackage


async def create_payment(
    session: AsyncSession,
    user: User,
    package: CoinPackage,
) -> Payment:
    payment = Payment(
        user_id=user.id,
        package_id=package.id,
        amount_uzs=package.price_uzs,
        coins=package.coins,
        status="pending",
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def approve_payment(session: AsyncSession, payment: Payment) -> bool:
    """Approve payment and credit coins. Returns False if already processed."""
    if payment.status != "pending":
        return False
    payment.status = "approved"
    user = await session.get(User, payment.user_id)
    if user:
        user.balance += payment.coins
    await session.commit()
    return True


async def reject_payment(session: AsyncSession, payment: Payment) -> bool:
    """Reject payment. Returns False if already processed."""
    if payment.status != "pending":
        return False
    payment.status = "rejected"
    await session.commit()
    return True


async def get_pending_payments(session: AsyncSession) -> list[Payment]:
    result = await session.execute(
        select(Payment)
        .where(Payment.status == "pending")
        .order_by(Payment.created_at)
    )
    return list(result.scalars().all())


# ─── Future provider stubs ────────────────────────────────────────────────────

class ClickPaymentProvider:
    """Stub for Click payment integration."""
    async def create_invoice(self, amount: int, order_id: int) -> str:
        raise NotImplementedError("Click integration not yet implemented")


class PaymePaymentProvider:
    """Stub for Payme payment integration."""
    async def create_invoice(self, amount: int, order_id: int) -> str:
        raise NotImplementedError("Payme integration not yet implemented")


class StripePaymentProvider:
    """Stub for Stripe payment integration."""
    async def create_session(self, amount: int, currency: str = "usd") -> str:
        raise NotImplementedError("Stripe integration not yet implemented")
