"""Payment processing routes: initiate, webhook, verify."""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database.connection import get_db
from app.schemas.payment import OrderCreate, BeezatiWebhookPayload
from app.repositories.payment_repo import (
    get_link_by_token, create_order, update_order_status,
    create_payment_record, log_webhook, get_order_by_uuid, log_audit
)
from app.models.payment_link import PaymentLinkStatus
from app.models.order import OrderStatus
from app.models.logs import AuditAction
from app.integrations.beezati.client import beezati_client, BeezatiError
from app.config.settings import settings

router = APIRouter(prefix="/api/payment", tags=["payments"])


@router.post("/initiate")
async def initiate_payment(
    payload: OrderCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    link = get_link_by_token(db, payload.payment_link_token)
    if not link:
        raise HTTPException(status_code=404, detail="رابط الدفع غير موجود")
    if link.status != PaymentLinkStatus.active:
        raise HTTPException(status_code=400, detail="رابط الدفع غير نشط أو منتهي")
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="انتهت صلاحية رابط الدفع")

    # Create order
    order = create_order(
        db,
        payment_link_id=link.id,
        amount=link.amount,
        currency=link.currency,
        customer_name=payload.customer_name or link.customer_name,
        customer_email=payload.customer_email or link.customer_email,
        customer_phone=payload.customer_phone or link.customer_phone,
    )

    base = str(request.base_url).rstrip("/")
    success_url = f"{base}/payment/success?order_id={order.uuid}"
    failed_url = f"{base}/payment/failed?order_id={order.uuid}"
    webhook_url = f"{base}/api/payment/beezati/webhook"

    try:
        result = await beezati_client.create_payment(
            order_uuid=order.uuid,
            amount=order.amount,
            currency=order.currency,
            description=link.description or (link.service.title if link.service else "دفع إلكتروني"),
            customer_name=order.customer_name or "",
            customer_email=order.customer_email or "",
            customer_phone=order.customer_phone or "",
            success_url=success_url,
            failed_url=failed_url,
            webhook_url=webhook_url,
        )

        transaction_id = result.get("transaction_id")
        payment_url = result.get("payment_url")

        update_order_status(db, order, OrderStatus.processing, transaction_id=transaction_id)
        create_payment_record(
            db, order.id, "beezati", json.dumps(result), transaction_id=transaction_id
        )

        log_audit(db, AuditAction.payment, description=f"Order {order.uuid} initiated", ip=request.client.host)
        return {"payment_url": payment_url, "order_uuid": order.uuid}

    except BeezatiError as e:
        update_order_status(db, order, OrderStatus.failed)
        raise HTTPException(status_code=502, detail=f"خطأ في بوابة الدفع: {str(e)}")


@router.post("/beezati/webhook")
async def beezati_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    body = await request.body()
    signature = request.headers.get("X-Beezati-Signature", "")

    # Verify signature
    if not beezati_client.verify_webhook_signature(body, signature):
        log_webhook(db, "webhook", body.decode(), "invalid_signature")
        raise HTTPException(status_code=400, detail="توقيع غير صالح")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="بيانات غير صالحة")

    log_webhook(db, data.get("event", "unknown"), json.dumps(data), "processing")

    order_uuid = data.get("order_id")
    transaction_id = data.get("transaction_id")
    event = data.get("event", "")
    status_str = data.get("status", "")

    if order_uuid:
        order = get_order_by_uuid(db, order_uuid)
        if order:
            # Idempotency: skip if already paid
            if order.status == OrderStatus.paid:
                return {"status": "already_processed"}

            if event in ("payment.success", "payment.paid") or status_str == "paid":
                update_order_status(db, order, OrderStatus.paid, transaction_id=transaction_id)
                if order.payment_link:
                    order.payment_link.status = PaymentLinkStatus.paid
                    db.commit()
                log_audit(db, AuditAction.payment, description=f"Paid: {order_uuid}")

            elif event in ("payment.failed", "payment.cancelled") or status_str in ("failed", "cancelled"):
                update_order_status(db, order, OrderStatus.failed, transaction_id=transaction_id)
                log_audit(db, AuditAction.payment, description=f"Failed: {order_uuid}")

    return {"status": "ok"}


@router.get("/verify/{order_uuid}")
async def verify_payment(order_uuid: str, db: Session = Depends(get_db)):
    order = get_order_by_uuid(db, order_uuid)
    if not order:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    if order.transaction_id and order.status == OrderStatus.processing:
        try:
            result = await beezati_client.verify_payment(order.transaction_id)
            status_str = result.get("status", "")
            if status_str == "paid":
                update_order_status(db, order, OrderStatus.paid)
            elif status_str in ("failed", "cancelled"):
                update_order_status(db, order, OrderStatus.failed)
        except BeezatiError:
            pass

    return {"order_uuid": order_uuid, "status": order.status.value}
