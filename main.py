"""
منصة الدفع الإلكتروني — مؤسسة سر التميز والأناقة
FastAPI Payment Checkout Platform
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config.settings import settings
from app.database.connection import create_tables
from app.middleware.security import SecurityHeadersMiddleware, RequestTimingMiddleware
from app.api.public.routes import router as public_router
from app.api.admin.routes import router as admin_router
from app.api.payments.routes import router as payment_router


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed admin
    create_tables()
    await seed_admin()
    yield
    # Shutdown


async def seed_admin():
    """Create default admin if none exists."""
    from app.database.connection import SessionLocal
    from app.repositories.user_repo import get_user_by_email, create_user
    from app.models.user import UserRole

    db = SessionLocal()
    try:
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@tamayoz.com")
        admin_pass = os.environ.get("ADMIN_PASSWORD", "Admin@123456")
        if not get_user_by_email(db, admin_email):
            create_user(db, name="مدير النظام", email=admin_email, password=admin_pass, role=UserRole.admin)
            print(f"✅ Admin created: {admin_email}")
        else:
            print(f"ℹ️  Admin already exists: {admin_email}")
    finally:
        db.close()


# App factory
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=None,   # Disable public docs
    redoc_url=None,
    lifespan=lifespan,
)

# State for rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Static files
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers
app.include_router(public_router)
app.include_router(admin_router)
app.include_router(payment_router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True,
    )
