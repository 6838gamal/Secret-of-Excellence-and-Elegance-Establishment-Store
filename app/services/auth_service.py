from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request, Depends
from typing import Optional
from app.repositories.user_repo import get_user_by_email, verify_password
from app.security.jwt import create_access_token, decode_token, get_token_from_cookie
from app.models.user import User, UserRole
from app.database.connection import get_db


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول أولاً",
        )
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رمز غير صالح")

    from app.repositories.user_repo import get_user_by_id
    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="المستخدم غير موجود")
    return user


def require_roles(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية للوصول إلى هذه الصفحة",
            )
        return current_user
    return dependency


require_admin = require_roles(UserRole.admin)
require_admin_or_manager = require_roles(UserRole.admin, UserRole.manager)
require_any_staff = require_roles(UserRole.admin, UserRole.manager, UserRole.accountant, UserRole.viewer)
