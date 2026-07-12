from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    accountant = "accountant"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.viewer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
