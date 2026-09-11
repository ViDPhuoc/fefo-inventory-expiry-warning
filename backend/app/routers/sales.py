"""Boundary UC03: không nhận mã nhân viên từ client; lấy từ phiên xác thực."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas
from app.database import get_db
from app.security import staff_only
from app.services import sales_service

router = APIRouter(prefix="/api/ban-hang", tags=["Bán hàng FEFO"])


@router.post("")
def sell(
    data: schemas.BanHangRequest,
    db: Session = Depends(get_db),
    user=Depends(staff_only),
):
    return sales_service.sell_by_barcode(db, data, user)
