"""Boundary UC05: toàn bộ quyết định và cập nhật tồn nằm trong service."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.security import current_user, manager_only, staff_only
from app.services import risk_action_service

router = APIRouter(prefix="/api/xu-ly-rui-ro", tags=["Lệnh xử lý rủi ro"])


@router.get("")
def actions(
    chi_dang_cho: bool = False,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    query = db.query(models.XuLyRuiRo)
    if chi_dang_cho:
        query = query.filter_by(trang_thai="ChoXuLy")
    total = query.count()
    rows = (
        query.order_by(models.XuLyRuiRo.thoi_gian.desc(), models.XuLyRuiRo.ma_xl.desc())
        .offset((page - 1) * 50)
        .limit(50)
        .all()
    )
    return {
        "total": total,
        "items": [schemas.XuLyRuiRoOut.model_validate(r) for r in rows],
    }


@router.post("/{ma_lo}", response_model=schemas.XuLyRuiRoOut, status_code=201)
def approve(
    ma_lo: str,
    data: schemas.XuLyRuiRoRequest,
    db: Session = Depends(get_db),
    user=Depends(manager_only),
):
    return risk_action_service.approve(db, ma_lo, data, user)


@router.post("/lenh/{ma_xl}/hoan-tat", response_model=schemas.XuLyRuiRoOut)
def complete(ma_xl: int, db: Session = Depends(get_db), user=Depends(staff_only)):
    return risk_action_service.complete(db, ma_xl, user)


@router.post("/lenh/{ma_xl}/huy", response_model=schemas.XuLyRuiRoOut)
def cancel(
    ma_xl: int,
    data: schemas.HuyLenhRequest,
    db: Session = Depends(get_db),
    user=Depends(manager_only),
):
    return risk_action_service.cancel(db, ma_xl, data, user)
