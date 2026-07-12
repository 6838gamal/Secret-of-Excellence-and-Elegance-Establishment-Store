from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timezone
from app.models.payment_link import PaymentLink, PaymentLinkStatus
from app.models.order import Order, OrderStatus
from app.models.payment import Payment
from app.models.logs import WebhookLog, AuditLog, AuditAction
import secrets


def generate_token(length: int = 12) -> str:
    return secrets.token_urlsafe(length)[:length]


# ── Payment Links ──────────────────────────────────────────
def create_payment_link(db: Session, created_by: int, **data) -> PaymentLink:
    token = generate_token()
    while db.query(PaymentLink).filter(PaymentLink.token == token).first():
        token = generate_token()

    link = PaymentLink(token=token, created_by=created_by, **data)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def get_link_by_token(db: Session, token: str) -> Optional[PaymentLink]:
    return db.query(PaymentLink).filter(PaymentLink.token == token).first()


def get_link_by_id(db: Session, link_id: int) -> Optional[PaymentLink]:
    return db.query(PaymentLink).filter(PaymentLink.id == link_id).first()


def get_all_links(db: Session) -> list[PaymentLink]:
    return db.query(PaymentLink).order_by(PaymentLink.created_at.desc()).all()


def cancel_link(db: Session, link: PaymentLink) -> PaymentLink:
    link.status = PaymentLinkStatus.cancelled
    db.commit()
    db.refresh(link)
    return link


# ── Orders ─────────────────────────────────────────────────
def create_order(db: Session, payment_link_id: int, amount: float, currency: str, **kwargs) -> Order:
    order = Order(payment_link_id=payment_link_id, amount=amount, currency=currency, **kwargs)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_order_by_uuid(db: Session, uuid: str) -> Optional[Order]:
    return db.query(Order).filter(Order.uuid == uuid).first()


def get_order_by_transaction(db: Session, transaction_id: str) -> Optional[Order]:
    return db.query(Order).filter(Order.transaction_id == transaction_id).first()


def update_order_status(db: Session, order: Order, status: OrderStatus,
                        transaction_id: str = None, gateway_reference: str = None) -> Order:
    order.status = status
    if transaction_id:
        order.transaction_id = transaction_id
    if gateway_reference:
        order.gateway_reference = gateway_reference
    if status == OrderStatus.paid:
        order.paid_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order


def get_all_orders(db: Session) -> list[Order]:
    return db.query(Order).order_by(Order.created_at.desc()).all()


# ── Payments ───────────────────────────────────────────────
def create_payment_record(db: Session, order_id: int, gateway: str, response_data: str,
                          transaction_id: str = None, payment_method: str = None) -> Payment:
    payment = Payment(
        order_id=order_id,
        gateway=gateway,
        transaction_id=transaction_id,
        payment_method=payment_method,
        response_data=response_data,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


# ── Dashboard Stats ────────────────────────────────────────
def get_dashboard_stats(db: Session) -> dict:
    from app.models.order import OrderStatus

    total_orders = db.query(func.count(Order.id)).scalar() or 0
    paid_orders = db.query(func.count(Order.id)).filter(Order.status == OrderStatus.paid).scalar() or 0
    failed_orders = db.query(func.count(Order.id)).filter(Order.status == OrderStatus.failed).scalar() or 0
    total_revenue = db.query(func.sum(Order.amount)).filter(Order.status == OrderStatus.paid).scalar() or 0.0

    today = datetime.now(timezone.utc).date()
    daily_revenue = (
        db.query(func.sum(Order.amount))
        .filter(Order.status == OrderStatus.paid)
        .filter(func.date(Order.paid_at) == today)
        .scalar() or 0.0
    )

    this_month = datetime.now(timezone.utc).replace(day=1).date()
    monthly_revenue = (
        db.query(func.sum(Order.amount))
        .filter(Order.status == OrderStatus.paid)
        .filter(func.date(Order.paid_at) >= this_month)
        .scalar() or 0.0
    )

    return {
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "failed_orders": failed_orders,
        "total_revenue": round(float(total_revenue), 2),
        "daily_revenue": round(float(daily_revenue), 2),
        "monthly_revenue": round(float(monthly_revenue), 2),
    }


# ── Logs ───────────────────────────────────────────────────
def log_webhook(db: Session, event: str, payload: str, status: str = "received") -> WebhookLog:
    log = WebhookLog(event=event, payload=payload, status=status)
    db.add(log)
    db.commit()
    return log


def log_audit(db: Session, action: AuditAction, user_id: int = None,
              description: str = None, ip: str = None, extra: str = None) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        action=action,
        description=description,
        ip_address=ip,
        extra_data=extra,
    )
    db.add(log)
    db.commit()
    return log
