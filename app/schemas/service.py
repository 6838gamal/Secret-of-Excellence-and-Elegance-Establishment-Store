from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ServiceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    currency: str = "SAR"
    image: Optional[str] = None
    status: bool = True


class ServiceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    image: Optional[str] = None
    status: Optional[bool] = None


class ServiceResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    price: float
    currency: str
    image: Optional[str]
    status: bool
    created_at: datetime

    class Config:
        from_attributes = True
