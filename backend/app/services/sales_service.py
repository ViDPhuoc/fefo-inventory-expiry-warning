"""UC03: bán theo FEFO; cùng một transaction chứa hóa đơn và tất cả lần trừ lô."""

from decimal import Decimal, ROUND_HALF_UP
from app import models
from app.config import business_today, business_now
from app.errors import BusinessError
from app.services.common import lock_product, new_id


def sell_by_barcode(db, data, user):
    product = db.query(models.SanPham).filter_by(barcode=data.barcode).first()
    if not product:
        raise BusinessError("Không tìm thấy mã vạch.", 404)
    product = lock_product(db, product.ma_sp)
    if not product.dang_kinh_doanh:
        raise BusinessError("Sản phẩm đã ngừng kinh doanh.")
    # Khóa theo sản phẩm bảo vệ cả trường hợp hai thu ngân bán cùng lúc.
    lots = (
        db.query(models.LoHang)
        .filter(
            models.LoHang.ma_sp == product.ma_sp,
            models.LoHang.so_luong_ton > 0,
            models.LoHang.han_su_dung > business_today(),
            models.LoHang.trang_thai == "DangGiaoDich",
        )
        .order_by(
            models.LoHang.han_su_dung, models.LoHang.ngay_nhap, models.LoHang.ma_lo
        )
        .with_for_update()
        .all()
    )
    available = sum(lot.so_luong_ton for lot in lots)
    if available < data.so_luong:
        raise BusinessError(
            f"Chỉ còn {available} sản phẩm đủ điều kiện bán; lô hết hạn/chờ hủy bị loại.",
            409,
            "INSUFFICIENT_STOCK",
        )
    invoice = models.HoaDonBan(
        ma_hd=new_id("HD"), ma_nv=user.ma_nv, thoi_gian_ban=business_now()
    )
    db.add(invoice)
    db.flush()
    remaining, details, total = data.so_luong, [], Decimal(0)
    for lot in lots:
        if remaining == 0:
            break
        quantity = min(remaining, lot.so_luong_ton)
        # Tỷ lệ nằm ở từng lô: cùng mã vạch có thể bán từ các lô với đơn giá khác nhau.
        price = (
            product.gia_ban * (Decimal(100) - lot.ty_le_giam) / Decimal(100)
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        lot.cap_nhat_ton_kho(-quantity)
        db.add(
            models.ChiTietBan(
                ma_hd=invoice.ma_hd, ma_lo=lot.ma_lo, so_luong=quantity, don_gia=price
            )
        )
        details.append(
            {
                "ma_lo": lot.ma_lo,
                "so_luong_tru": quantity,
                "han_su_dung": lot.han_su_dung,
                "don_gia": int(price),
                # Giá gốc tại lúc bán để UI hiển thị chính xác, không suy ngược từ giá đã làm tròn.
                "gia_goc": int(product.gia_ban),
                "ty_le_giam": float(lot.ty_le_giam),
            }
        )
        total += quantity * price
        remaining -= quantity
    db.flush()
    return {"ma_hd": invoice.ma_hd, "cac_lo_da_tru": details, "tong_tien": int(total)}
