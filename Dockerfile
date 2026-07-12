FROM python:3.11-slim

# System dependencies required by Pillow + ReportLab
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    libwebp-dev \
    libtiff-dev \
    zlib1g-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p app/static data

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# WEB_CONCURRENCY يُضبط من بيئة التشغيل (Render يضبطه تلقائياً).
# نستخدم 1 كافتراضي لأن SQLite لا يدعم الكتابة المتوازية بأمان.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 5000 --workers ${WEB_CONCURRENCY:-1}"]
