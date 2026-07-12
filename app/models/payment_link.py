from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import enum


class PaymentLinkStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    expired = "expired"
    paid = "paid"


class PaymentLink(Base):
    __tablename__ = "payment_links"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(32), unique=True, index=True, nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="SAR")
    description = Column(String(500), nullable=True)
    customer_name = Column(String(100), nullable=True)
    customer_email = Column(String(150), nullable=True)
    customer_phone = Column(String(30), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(PaymentLinkStatus), default=PaymentLinkStatus.active)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    service = relationship("Service", backref="payment_links")
    creator = relationship("User", backref="payment_links")
