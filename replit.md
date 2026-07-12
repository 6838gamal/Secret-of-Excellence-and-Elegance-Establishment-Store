# متجر مؤسسة سر التميز والأناقة — Payment Checkout Platform

## Project Overview

A lightweight, production-ready **Payment Checkout Platform** built with FastAPI for **مؤسسة سر التميز والأناقة**. The system allows the business owner to create services/invoices and share payment links with customers who pay directly via Beezati.

## Stack

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy 2.x
- **Database**: SQLite (dev) — upgradeable to PostgreSQL
- **Frontend**: Jinja2 + Tailwind CSS + vanilla JS (Arabic RTL)
- **Auth**: JWT in HttpOnly cookies + bcrypt password hashing
- **PDF**: ReportLab
- **QR**: qrcode[pil]
- **Payment**: Beezati payment gateway integration

## How to Run

```bash
python main.py
```

Or via uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## Project Structure

```
app/
├── config/         # Settings (pydantic-settings)
├── database/       # SQLAlchemy engine & session
├── models/         # DB models (User, Service, PaymentLink, Order, Payment, Logs)
├── schemas/        # Pydantic request/response schemas
├── repositories/   # Data access layer
├── services/       # Business logic (auth, etc.)
├── api/
│   ├── public/     # Public routes: home, /pay/{token}, /invoice/{id}
│   ├── admin/      # Hidden admin dashboard: /admin/*
│   └── payments/   # Payment API: /api/payment/*
├── integrations/
│   └── beezati/    # Beezati payment gateway client
├── templates/      # Jinja2 HTML templates (Arabic RTL)
├── static/         # Static assets (CSS, images)
├── middleware/      # Security headers middleware
├── security/       # JWT helpers
└── utils/          # QR code, PDF generation
main.py             # App entry point
```

## Key Pages

| URL | Description |
|-----|-------------|
| `/` | Public home — double-click logo to open admin login |
| `/pay/{token}` | Customer payment page |
| `/payment/success` | Success confirmation |
| `/payment/failed` | Failure page |
| `/invoice/{id}` | Invoice view |
| `/invoice/{id}/pdf` | Download PDF invoice |
| `/admin/dashboard` | Admin dashboard (JWT protected) |
| `/admin/services` | Service management |
| `/admin/links` | Payment link management |
| `/admin/orders` | Order management |
| `/admin/users` | User management (admin only) |

## Admin Access (Hidden)

1. Go to the home page `/`
2. **Double-click** the logo (✨) — a login modal appears
3. Login with admin credentials
4. Redirected to `/admin/dashboard`

## Default Admin Credentials

Set via environment variables:
- `ADMIN_EMAIL` (default: `admin@tamayoz.com`)
- `ADMIN_PASSWORD` (default: `Admin@123456`)

**Change these in production!**

## Environment Variables

Copy `.env.example` to `.env` and fill in:
- `SESSION_SECRET` — already set via Replit secrets
- `BEEZATI_API_KEY`, `BEEZATI_SECRET`, `BEEZATI_WEBHOOK_SECRET` — from Beezati dashboard
- `DATABASE_URL` — SQLite by default, PostgreSQL for production

## User Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access including user management and service deletion |
| `manager` | Create/edit services, create/cancel payment links |
| `accountant` | View dashboard, orders, links |
| `viewer` | Read-only access |

## Beezati Integration

Configure in `.env`:
```
BEEZATI_API_KEY=your-key
BEEZATI_SECRET=your-secret
BEEZATI_WEBHOOK_SECRET=your-webhook-secret
```

Webhook endpoint: `POST /api/payment/beezati/webhook`

## User Preferences

- Arabic RTL UI throughout
- Tailwind CSS via CDN
- Mobile-first design
- No React/Vue — pure Jinja2 + vanilla JS
