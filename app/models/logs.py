from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(Integer, primary_key=True, index=True)
    event = Column(String(100), nullable=False)
    payload = Column(Text, nullable=True)
    status = Column(String(20), default="received")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditAction(str, enum.Enum):
    login = "login"
    logout = "logout"
    create_invoice = "create_invoice"
    update_data = "update_data"
    payment = "payment"
    admin_change = "admin_change"
    create_service = "create_service"
    delete_service = "delete_service"
    create_link = "create_link"
    cancel_link = "cancel_link"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(SAEnum(AuditAction), nullable=False)
    description = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    extra_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
