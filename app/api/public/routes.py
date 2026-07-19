"""Public-facing routes: home page, payment page, Moyasar callback."""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database.connection import get_db
from app.repositories.payment_repo import get_link_by_token, get_order_by_uuid, update_order_status, log_audit
from app.models.payment_link import PaymentLinkStatus
from app.models.order import OrderStatus
from app.models.logs import AuditAction
from app.utils.qr import generate_qr_base64
from app.config.settings import settings
from app.integrations.moyasar.client import moyasar_client, MoyasarError

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {
        "company_name": settings.COMPANY_NAME,
    })


@router.get("/pay/{token}", response_class=HTMLResponse)
async def payment_page(token: str, request: Request, db: Session = Depends(get_db)):
    link = get_link_by_token(db, token)
    if not link:
        raise HTTPException(status_code=404, detail="رابط الدفع غير موجود")

    if link.expires_at and link.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        link.status = PaymentLinkStatus.expired
        db.commit()

    if link.status != PaymentLinkStatus.active:
        return templates.TemplateResponse(request, "pay_expired.html", {
            "status": link.status.value,
            "company_name": settings.COMPANY_NAME,
        })

    pay_url = str(request.base_url).rstrip("/") + f"/pay/{token}"
    qr_b64  = generate_qr_base64(pay_url)

    return templates.TemplateResponse(request, "pay.html", {
        "link":               link,
        "service":            link.service,
        "qr_b64":             qr_b64,
        "company_name":       settings.COMPANY_NAME,
        "moyasar_pk":         settings.MOYASAR_PUBLISHABLE_KEY,
        "moyasar_enabled":    bool(settings.MOYASAR_PUBLISHABLE_KEY),
    })


# ── Moyasar callback (redirect from Moyasar after payment) ─
@router.get("/payment/moyasar/callback", response_class=HTMLResponse)
async def moyasar_callback(
    request: Request,
    order_uuid: str = None,
    id: str = None,          # Moyasar payment ID
    status: str = None,      # paid | failed | ...
    message: str = None,
    db: Session = Depends(get_db),
):
    if not order_uuid:
        return RedirectResponse("/")

    order = get_order_by_uuid(db, order_uuid)
    if not order:
        return RedirectResponse("/")

    # Verify with Moyasar API if paid; else trust status param
    if id and order.status != OrderStatus.paid:
        try:
            payment = await moyasar_client.get_payment(id)
            remote_status = payment.get("status", status or "")
        except MoyasarError:
            remote_status = status or ""

        if remote_status == "paid":
            update_order_status(db, order, OrderStatus.paid, transaction_id=id)
            if order.payment_link:
                order.payment_link.status = PaymentLinkStatus.paid
                db.commit()
            log_audit(db, AuditAction.payment, description=f"Moyasar paid: {order_uuid}")
        elif remote_status in ("failed", "cancelled", "voided"):
            update_order_status(db, order, OrderStatus.failed, transaction_id=id)
            log_audit(db, AuditAction.payment, description=f"Moyasar failed: {order_uuid}")

    if order.status == OrderStatus.paid:
        return RedirectResponse(f"/payment/success?order_id={order.uuid}", status_code=303)
    else:
        return RedirectResponse(f"/payment/failed?order_id={order.uuid}", status_code=303)


@router.get("/payment/success", response_class=HTMLResponse)
async def payment_success(request: Request, order_id: str = None):
    return templates.TemplateResponse(request, "payment_success.html", {
        "order_id":     order_id,
        "company_name": settings.COMPANY_NAME,
    })


@router.get("/payment/failed", response_class=HTMLResponse)
async def payment_failed(request: Request, order_id: str = None):
    return templates.TemplateResponse(request, "payment_failed.html", {
        "order_id":     order_id,
        "company_name": settings.COMPANY_NAME,
    })


@router.get("/invoice/{order_id}", response_class=HTMLResponse)
async def invoice_page(order_id: int, request: Request, db: Session = Depends(get_db)):
    from app.models.order import Order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
    link    = order.payment_link
    service = link.service if link else None
    return templates.TemplateResponse(request, "invoice.html", {
        "order": order, "link": link, "service": service,
        "company_name": settings.COMPANY_NAME,
    })


@router.get("/invoice/{order_id}/pdf")
async def invoice_pdf(order_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import Response
    from app.utils.pdf import generate_invoice_pdf
    from app.models.order import Order

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
    link    = order.payment_link
    service = link.service if link else None
    pdf_bytes = generate_invoice_pdf(order, link, service)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{order_id}.pdf"},
    )
