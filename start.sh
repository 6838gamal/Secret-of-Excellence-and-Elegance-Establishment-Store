#!/bin/bash
# ─── سكريبت تشغيل منصة سر التميز والأناقة ───────────────────────────────────
set -e

# ── التحقق من وجود ملف البيئة ─────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo "⚠️  لم يُعثر على ملف .env — سيتم نسخه من .env.example"
    cp .env.example .env
    echo "✅ تم إنشاء .env — يرجى تعديله بقيمك الحقيقية قبل المتابعة"
    echo ""
fi

# ── تثبيت المتطلبات ────────────────────────────────────────────────────────
if [ "${INSTALL_DEPS:-true}" = "true" ]; then
    echo "📦 تثبيت المتطلبات..."
    pip install -r requirements.txt --quiet
fi

# ── إعداد متغيرات البيئة ──────────────────────────────────────────────────
export $(grep -v '^#' .env | grep -v '^$' | xargs) 2>/dev/null || true

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5000}"
WORKERS="${WORKERS:-1}"
RELOAD="${RELOAD:-false}"

echo ""
echo "🚀 تشغيل المنصة على http://${HOST}:${PORT}"
echo "   Workers: ${WORKERS} | Reload: ${RELOAD}"
echo ""

if [ "${RELOAD}" = "true" ]; then
    exec uvicorn main:app --host "$HOST" --port "$PORT" --reload
else
    exec uvicorn main:app --host "$HOST" --port "$PORT" --workers "$WORKERS"
fi
