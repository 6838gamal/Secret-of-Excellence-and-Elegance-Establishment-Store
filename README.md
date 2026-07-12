# منصة الدفع الإلكتروني — مؤسسة سر التميز والأناقة

منصة دفع إلكتروني خفيفة مبنية بـ FastAPI تتيح للمشغل إنشاء خدمات وروابط دفع ومشاركتها مع العملاء عبر بوابة Beezati.

---

## المتطلبات

| الأداة | الحد الأدنى |
|--------|-------------|
| Python | 3.11+ |
| pip | أي إصدار حديث |
| Docker + Compose | اختياري |

---

## طرق التشغيل

### 1 — Python مباشرة (أسرع للتطوير)

```bash
# 1. انسخ ملف البيئة وعدّله
cp .env.example .env

# 2. ثبّت المتطلبات
pip install -r requirements.txt

# 3. شغّل
./start.sh
# أو مباشرةً:
python main.py
```

### 2 — Docker (SQLite — مناسب للخوادم الصغيرة)

```bash
cp .env.example .env
# عدّل .env ثم:
docker compose -f docker-compose.sqlite.yml up -d --build
```

### 3 — Docker + PostgreSQL (الإنتاج الثقيل)

```bash
cp .env.example .env
# فعّل سطر DATABASE_URL الخاص بـ PostgreSQL في .env
docker compose up -d --build
```

---

## إعداد ملف `.env`

```env
# مفتاح سري قوي (أنشئه بـ: python -c "import secrets; print(secrets.token_hex(32))")
SESSION_SECRET=your-random-secret-here

# SQLite افتراضياً
DATABASE_URL=sqlite:///./tamayoz.db

# بيانات المدير الأول
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=YourStrongPassword123!

# بوابة Beezati
BEEZATI_API_KEY=...
BEEZATI_SECRET=...
BEEZATI_WEBHOOK_SECRET=...
```

---

## الوصول للنظام

| الرابط | الوصف |
|--------|--------|
| `http://localhost:5000/` | الصفحة الرئيسية |
| `http://localhost:5000/health` | فحص الحالة |
| `http://localhost:5000/admin/dashboard` | لوحة الإدارة |

**تسجيل الدخول للإدارة:** ادفع ضغطتين على شعار ✨ في الصفحة الرئيسية

---

## هيكل المشروع

```
.
├── main.py                  # نقطة الدخول
├── requirements.txt         # متطلبات Python
├── Dockerfile
├── docker-compose.yml       # مع PostgreSQL
├── docker-compose.sqlite.yml
├── start.sh                 # سكريبت تشغيل
├── .env.example
└── app/
    ├── api/
    │   ├── admin/           # مسارات لوحة الإدارة
    │   ├── payments/        # Webhook + إطلاق الدفع
    │   └── public/          # الصفحات العامة
    ├── config/settings.py   # إعدادات pydantic-settings
    ├── database/connection.py
    ├── integrations/beezati/ # عميل بوابة Beezati
    ├── middleware/security.py
    ├── models/              # جداول SQLAlchemy
    ├── repositories/        # طبقة الوصول للبيانات
    ├── schemas/             # Pydantic schemas
    ├── security/jwt.py
    ├── services/auth_service.py
    ├── templates/           # Jinja2 HTML (عربي RTL)
    └── utils/               # QR + PDF
```

---

## الأدوار

| الدور | الصلاحيات |
|-------|-----------|
| `admin` | كل شيء |
| `manager` | الخدمات + الروابط + الطلبات |
| `accountant` | الطلبات + التقارير |
| `viewer` | عرض فقط |

---

## متغيرات البيئة الكاملة

| المتغير | الافتراضي | الوصف |
|---------|-----------|-------|
| `SESSION_SECRET` | — | **مطلوب في الإنتاج** — مفتاح JWT |
| `DATABASE_URL` | `sqlite:///./tamayoz.db` | رابط قاعدة البيانات |
| `ADMIN_EMAIL` | `admin@tamayoz.com` | بريد المدير الأول |
| `ADMIN_PASSWORD` | `Admin@123456` | كلمة مرور المدير الأول |
| `BEEZATI_API_KEY` | — | مفتاح API لبيزاتي |
| `BEEZATI_SECRET` | — | سر التوقيع لبيزاتي |
| `BEEZATI_WEBHOOK_SECRET` | — | سر الـ Webhook |
| `DEBUG` | `False` | وضع التطوير |
| `PORT` | `5000` | رقم المنفذ |
| `WORKERS` | `2` | عدد عمليات Uvicorn |
