"""Boundary nhập kho/kiểm kê và tra cứu sản phẩm, lô hàng có phân trang."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.security import current_user, staff_only
from app.services import inventory_service
from app.errors import BusinessError

router = APIRouter(prefix="/api", tags=["Nhập kho & tồn kho"])


@router.get("/cau-hinh-han-su-dung")
def expiry_suggestions(user=Depends(staff_only)):
    from app.services.shelf_life import shelf_life_settings
    return shelf_life_settings()


@router.get("/san-pham/tra-cuu", response_model=schemas.SanPhamOut)
def lookup_product(ma: str = Query(min_length=1, max_length=100), db: Session = Depends(get_db), user=Depends(staff_only)):
    """Mã dưới tên hàng ở Manager là mã lô; tra về SKU, không đổi lô bán FEFO."""
    value = ma.strip()
    if not value:
        raise BusinessError("Vui lòng nhập mã cần tìm.", 422)
    lot_products = db.query(models.LoHang.ma_sp).filter(models.LoHang.ma_lo == value)
    matches = db.query(models.SanPham).filter(or_(
        models.SanPham.barcode == value,
        models.SanPham.ma_sp == value,
        models.SanPham.ma_sp.in_(lot_products),
    )).all()
    if not matches:
        raise BusinessError("Không tìm thấy sản phẩm theo mã này. Hãy sao chép đầy đủ mã từ Manager.", 404)
    if len(matches) > 1:
        raise BusinessError("Mã trùng giữa nhiều sản phẩm. Vui lòng chọn sản phẩm bằng tên.", 409)
    return matches[0]


@router.get("/san-pham", response_model=list[schemas.SanPhamOut])
def products(q: str = "", db: Session = Depends(get_db), user=Depends(current_user)):
    return (
        db.query(models.SanPham)
        .filter(
            or_(
                models.SanPham.ten_sp.ilike(f"%{q}%"),
                models.SanPham.barcode.ilike(f"%{q}%"),
            )
        )
        .order_by(models.SanPham.ma_sp)
        .limit(1000)
        .all()
    )


@router.get("/lo-hang")
def lots(
    ma_sp: str | None = None,
    chi_con_hang: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    query = db.query(models.LoHang)
    if ma_sp:
        query = query.filter_by(ma_sp=ma_sp)
    if chi_con_hang:
        query = query.filter(models.LoHang.so_luong_ton > 0)
    total = query.count()
    rows = (
        query.order_by(models.LoHang.han_su_dung, models.LoHang.ma_lo)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "items": [schemas.LoHangOut.model_validate(row) for row in rows],
    }


@router.post("/lo-hang", response_model=schemas.LoHangOut, status_code=201)
def receive(
    data: schemas.LoHangCreate, db: Session = Depends(get_db), user=Depends(staff_only)
):
    return inventory_service.create_batch(db, data, user)


@router.patch("/lo-hang/{ma_lo}/dieu-chinh", response_model=schemas.LoHangOut)
def adjust(
    ma_lo: str,
    data: schemas.DieuChinhTonRequest,
    db: Session = Depends(get_db),
    user=Depends(staff_only),
):
    return inventory_service.adjust_stock(db, ma_lo, data, user)
