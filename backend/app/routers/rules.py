"""Boundary UC01: nhận dữ liệu, gọi Control, trả kết quả; không xử lý luật tại đây."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.security import current_user, manager_only
from app.services import rule_service

router = APIRouter(prefix="/api/nhom-hang", tags=["Nhóm hàng & luật cảnh báo"])


@router.get("", response_model=list[schemas.NhomHangOut])
def groups(db: Session = Depends(get_db), user=Depends(current_user)):
    return db.query(models.NhomHang).order_by(models.NhomHang.ma_nhom).all()


@router.get("/{ma_nhom}", response_model=schemas.NhomHangOut)
def group(ma_nhom: str, db: Session = Depends(get_db), user=Depends(current_user)):
    return rule_service.load_rule(db, ma_nhom)


@router.put("/{ma_nhom}", response_model=schemas.NhomHangOut)
def update(
    ma_nhom: str,
    data: schemas.NhomHangUpdate,
    db: Session = Depends(get_db),
    user=Depends(manager_only),
):
    return rule_service.update_rule(db, ma_nhom, data)
