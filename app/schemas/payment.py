from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.payment_link import PaymentLinkStatus
from app.models.order import OrderStatus


class PaymentLinkCreate(BaseModel):
    service_id: Optional[int] = None
    amount: float
    currency: str = "SAR"
    description: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    expires_at: Optional[datetime] = None


class PaymentLinkResponse(BaseModel):
    id: int
    token: str
    service_id: Optional[int]
    amount: float
    currency: str
    description: Optional[str]
    customer_name: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    expires_at: Optional[datetime]
    status: PaymentLinkStatus
    created_at: datetime
    pay_url: Optional[str] = None

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    payment_link_token: str
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    uuid: str
    amount: float
    currency: str
    status: OrderStatus
    transaction_id: Optional[str]
    created_at: datetime
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True


class BeezatiWebhookPayload(BaseModel):
    event: str
    transaction_id: str
    order_id: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    signature: Optional[str] = None
