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
            pass
        else:
            raise

    # ── Column migrations (add new columns to existing tables) ──
    _run_column_migrations()


def _run_column_migrations():
    """Add new columns to existing tables without dropping data."""
    from sqlalchemy import text, inspect as sa_inspect
    inspector = sa_inspect(engine)
    with engine.connect() as conn:
        # orders.gateway — added when PayPal/Moyasar support was introduced
        existing_cols = [c["name"] for c in inspector.get_columns("orders")]
        if "gateway" not in existing_cols:
            try:
                conn.execute(text("ALTER TABLE orders ADD COLUMN gateway VARCHAR(50) DEFAULT 'beezati'"))
                conn.commit()
            except Exception:
                pass  # Already exists or SQLite race
