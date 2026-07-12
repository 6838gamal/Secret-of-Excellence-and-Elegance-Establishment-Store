from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import enum
import uuid as _uuid


class OrderStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    paid = "paid"
    failed = "failed"
    cancelled = "cancelled"
    expired = "expired"
    refunded = "refunded"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(_uuid.uuid4()))
    payment_link_id = Column(Integer, ForeignKey("payment_links.id"), nullable=True)
    customer_name = Column(String(100), nullable=True)
    customer_email = Column(String(150), nullable=True)
    customer_phone = Column(String(30), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="SAR")
    status = Column(SAEnum(OrderStatus), default=OrderStatus.pending)
    transaction_id = Column(String(100), nullable=True)
    gateway_reference = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)

    payment_link = relationship("PaymentLink", backref="orders")
    payments = relationship("Payment", back_populates="order")
