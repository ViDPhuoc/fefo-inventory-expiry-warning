"""Boundary báo cáo tổng hợp theo khoảng thời gian do Manager lựa chọn."""

from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config import business_today
from app.database import get_db
from app.errors import BusinessError
from app.security import manager_only
from app.services.report_service import report

router = APIRouter(prefix="/api/bao-cao", tags=["Báo cáo Manager"])


@router.get("")
def get_report(
    tu_ngay: date | None = None,
    den_ngay: date | None = None,
    db: Session = Depends(get_db),
    user=Depends(manager_only),
):
    end = den_ngay or business_today()
    start = tu_ngay or end - timedelta(days=29)
    if start > end or (end - start).days > 365 or end > business_today():
        raise BusinessError(
            "Chọn khoảng ngày hợp lệ, tối đa 366 ngày và không sau hôm nay."
        )
    return report(db, start, end)
