"""Hidden admin dashboard routes."""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.services.auth_service import get_current_user, require_any_staff, require_admin_or_manager, require_admin
from app.models.user import User, UserRole
from app.repositories.user_repo import (
    get_user_by_email, verify_password, create_user, get_all_users
)
from app.repositories.service_repo import (
    get_all_services, get_service_by_id, create_service, update_service, delete_service
)
from app.repositories.payment_repo import (
    create_payment_link, get_all_links, get_link_by_id, cancel_link,
    get_all_orders, get_dashboard_stats, log_audit
)
from app.schemas.service import ServiceUpdate, ServiceCreate
from app.schemas.payment import PaymentLinkCreate
from app.security.jwt import create_access_token
from app.models.logs import AuditAction
from app.config.settings import settings
from app.utils.qr import generate_qr_base64

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


# ── Auth ───────────────────────────────────────────────────
@router.post("/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        log_audit(db, AuditAction.login, description=f"Failed login: {email}", ip=request.client.host if request.client else None)
        return JSONResponse(
            {"success": False, "message": "البريد الإلكتروني أو كلمة المرور غير صحيحة"},
            status_code=401
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    log_audit(db, AuditAction.login, user_id=user.id, description="Login success", ip=request.client.host if request.client else None)

    response = JSONResponse({"success": True, "redirect": "/admin/dashboard"})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 8,
    )
    return response


@router.post("/logout")
async def admin_logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


# ── Dashboard ──────────────────────────────────────────────
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    stats = get_dashboard_stats(db)
    recent_orders = get_all_orders(db)[:10]
    return templates.TemplateResponse(request, "admin/dashboard.html", {
        "user": current_user,
        "stats": stats,
        "recent_orders": recent_orders,
        "company_name": settings.COMPANY_NAME,
    })


# ── Services ───────────────────────────────────────────────
@router.get("/services", response_class=HTMLResponse)
async def services_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    services = get_all_services(db)
    return templates.TemplateResponse(request, "admin/services.html", {
        "user": current_user,
        "services": services,
        "company_name": settings.COMPANY_NAME,
    })


@router.post("/services")
async def create_service_endpoint(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    currency: str = Form("SAR"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    svc = create_service(db, title=title, description=description, price=price, currency=currency)
    log_audit(db, AuditAction.create_service, user_id=current_user.id, description=f"Service: {title}")
    return JSONResponse({"success": True, "id": svc.id})


@router.put("/services/{service_id}")
async def update_service_endpoint(
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    svc = get_service_by_id(db, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="الخدمة غير موجودة")
    update_service(db, svc, **data.model_dump(exclude_none=True))
    log_audit(db, AuditAction.update_data, user_id=current_user.id, description=f"Update service {service_id}")
    return JSONResponse({"success": True})


@router.delete("/services/{service_id}")
async def delete_service_endpoint(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    svc = get_service_by_id(db, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="الخدمة غير موجودة")
    delete_service(db, svc)
    log_audit(db, AuditAction.delete_service, user_id=current_user.id, description=f"Delete service {service_id}")
    return JSONResponse({"success": True})


# ── Services JSON API (used by payment links page) ─────────
@router.get("/api/services")
async def list_services_json(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    services = get_all_services(db)
    return JSONResponse([{
        "id": s.id,
        "title": s.title,
        "description": s.description or "",
        "price": s.price,
        "currency": s.currency,
        "status": s.status,
    } for s in services])


@router.post("/api/services")
async def create_service_json(
    data: ServiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    svc = create_service(db, title=data.title, description=data.description or "",
                         price=data.price, currency=data.currency)
    log_audit(db, AuditAction.create_service, user_id=current_user.id, description=f"Service: {data.title}")
    return JSONResponse({"success": True, "id": svc.id, "title": svc.title,
                         "price": svc.price, "currency": svc.currency,
                         "description": svc.description or "", "status": svc.status})


# ── Payment Links ──────────────────────────────────────────
@router.get("/links", response_class=HTMLResponse)
async def payment_links_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    links = get_all_links(db)
    services = get_all_services(db, active_only=True)
    base = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(request, "admin/payment_links.html", {
        "user": current_user,
        "links": links,
        "services": services,
        "base_url": base,
        "company_name": settings.COMPANY_NAME,
    })


@router.post("/links")
async def create_payment_link_endpoint(
    data: PaymentLinkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    link = create_payment_link(
        db,
        created_by=current_user.id,
        service_id=data.service_id,
        amount=data.amount,
        currency=data.currency,
        description=data.description,
        customer_name=data.customer_name,
        customer_email=str(data.customer_email) if data.customer_email else None,
        customer_phone=data.customer_phone,
        expires_at=data.expires_at,
    )
    base = str(request.base_url).rstrip("/")
    pay_url = f"{base}/pay/{link.token}"
    qr_b64 = generate_qr_base64(pay_url)
    log_audit(db, AuditAction.create_link, user_id=current_user.id, description=f"Link {link.token}")
    return JSONResponse({"success": True, "token": link.token, "pay_url": pay_url, "qr": qr_b64})


@router.post("/links/{link_id}/cancel")
async def cancel_payment_link_endpoint(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    link = get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="الرابط غير موجود")
    cancel_link(db, link)
    log_audit(db, AuditAction.cancel_link, user_id=current_user.id, description=f"Cancel link {link_id}")
    return JSONResponse({"success": True})


@router.get("/links/{link_id}/qr")
async def get_link_qr(
    link_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    link = get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404)
    base = str(request.base_url).rstrip("/")
    pay_url = f"{base}/pay/{link.token}"
    return JSONResponse({"qr": generate_qr_base64(pay_url), "url": pay_url})


# ── Orders ─────────────────────────────────────────────────
@router.get("/orders", response_class=HTMLResponse)
async def orders_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    orders = get_all_orders(db)
    return templates.TemplateResponse(request, "admin/orders.html", {
        "user": current_user,
        "orders": orders,
        "company_name": settings.COMPANY_NAME,
    })


# ── Users (admin only) ─────────────────────────────────────
@router.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    users = get_all_users(db)
    return templates.TemplateResponse(request, "admin/users.html", {
        "user": current_user,
        "users": users,
        "roles": [r.value for r in UserRole],
        "company_name": settings.COMPANY_NAME,
    })


@router.post("/users")
async def create_user_endpoint(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("viewer"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if get_user_by_email(db, email):
        return JSONResponse(
            {"success": False, "message": "البريد الإلكتروني مستخدم بالفعل"},
            status_code=400
        )
    user = create_user(db, name=name, email=email, password=password, role=UserRole(role))
    log_audit(db, AuditAction.admin_change, user_id=current_user.id, description=f"Created user {email}")
    return JSONResponse({"success": True, "id": user.id})


# ── Stats API ──────────────────────────────────────────────
@router.get("/api/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    return get_dashboard_stats(db)
