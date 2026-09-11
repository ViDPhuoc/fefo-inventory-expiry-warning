"""Boundary UC04: phân bổ toàn bộ các lô trước khi lọc, tránh tính sai FEFO."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal
from app.config import business_today
from app.database import get_db
from app.security import manager_only
from app.services import alert_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Manager"])


@router.get("")
def dashboard(
    so_ngay_lookback: int = Query(14, ge=1, le=180),
    ma_nhom: str | None = None,
    muc_rui_ro: Literal["Do", "Vang", "Xanh"] | None = None,
    q: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(manager_only),
):
    rows = alert_service.get_dashboard_data(db, so_ngay_lookback)
    # Phân bổ công suất không phụ thuộc bộ lọc màn hình; chỉ lọc SAU tính toán.
    filtered = [
        r
        for r in rows
        if (not ma_nhom or r["ma_nhom"] == ma_nhom)
        and (not muc_rui_ro or r["muc_rui_ro"] == muc_rui_ro)
        and (
            not q
            or q.casefold()
            in (" ".join([r["ten_sp"], r["ma_lo"], r["barcode"]])).casefold()
        )
    ]
    return {
        "ngay_tinh": business_today(),
        "so_ngay_lookback": so_ngay_lookback,
        "thong_ke": alert_service.summarize(filtered),
        "total": len(filtered),
        "page": page,
        "danh_sach": filtered[(page - 1) * page_size : page * page_size],
    }
