from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# SQLite with WAL mode for better concurrency
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)

# Enable WAL mode for SQLite
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    إنشاء الجداول إن لم تكن موجودة.
    checkfirst=True يتجنب خطأ "already exists" عند تشغيل عامل واحد،
    لكن مع عدة عمال متوازين على SQLite يمكن أن تحدث سباقة (race condition).
    نعالجها بـ try/except لأن الحالة آمنة: الجدول موجود بالفعل.
    """
    from app.models import user, service, payment_link, order, payment, logs
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except Exception as exc:
        if "already exists" in str(exc):
            # عامل آخر سبق وأنشأ الجداول — هذا طبيعي مع multi-worker
            pass
        else:
            raise
