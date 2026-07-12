from sqlalchemy.orm import Session
from typing import Optional
from app.models.service import Service


def get_all_services(db: Session, active_only: bool = False) -> list[Service]:
    q = db.query(Service)
    if active_only:
        q = q.filter(Service.status == True)
    return q.order_by(Service.created_at.desc()).all()


def get_service_by_id(db: Session, service_id: int) -> Optional[Service]:
    return db.query(Service).filter(Service.id == service_id).first()


def create_service(db: Session, **data) -> Service:
    service = Service(**data)
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def update_service(db: Session, service: Service, **data) -> Service:
    for k, v in data.items():
        if v is not None:
            setattr(service, k, v)
    db.commit()
    db.refresh(service)
    return service


def delete_service(db: Session, service: Service) -> None:
    db.delete(service)
    db.commit()
