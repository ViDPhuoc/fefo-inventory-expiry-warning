"""UC02 và kiểm kê: chỉ nhận lô hợp lệ, ghi lịch sử mọi lần sửa số tồn."""

from app import models
from app.config import business_today
from app.errors import BusinessError
from app.services.common import lock_product, lock_lot, new_id


def create_batch(db, data, user):
    today = business_today()
    product = lock_product(db, data.ma_sp)
    if not product.dang_kinh_doanh:
        raise BusinessError("Sản phẩm đã ngừng kinh doanh.")
    if data.ngay_san_xuat > today:
        raise BusinessError("Ngày sản xuất không được ở tương lai.")
    if data.han_su_dung <= today or data.ngay_san_xuat >= data.han_su_dung:
        raise BusinessError("Hạn sử dụng phải sau ngày nhập và ngày sản xuất.")
    # Cụ thể hóa yêu cầu KSHT 4.3.1: từ chối nhập lô đã chạm ngưỡng Vàng.
    if (data.han_su_dung - today).days <= product.nhom_hang.muc_canh_bao_vang:
        raise BusinessError(
            "Lô đã cận hạn theo ngưỡng Vàng của nhóm; từ chối nhập mới."
        )
    lot = models.LoHang(
        ma_lo=new_id("LO"),
        ma_sp=product.ma_sp,
        ngay_san_xuat=data.ngay_san_xuat,
        han_su_dung=data.han_su_dung,
        ngay_nhap=today,
        so_luong_nhap=data.so_luong_nhap,
        so_luong_ton=data.so_luong_nhap,
        trang_thai="DangGiaoDich",
        ty_le_giam=0,
        ma_nv_nhap=user.ma_nv,
    )
    db.add(lot)
    db.flush()
    return lot


def adjust_stock(db, ma_lo, data, user):
    lot, _ = lock_lot(db, ma_lo)
    if lot.trang_thai in ("DaXuatHuy", "ChoXuatHuy"):
        raise BusinessError("Lô đã/chờ xuất hủy không được điều chỉnh tồn.", 409)
    if data.so_luong_thuc_te > lot.so_luong_nhap:
        raise BusinessError(
            "Số tồn không được vượt lượng nhập. Hàng nhập thêm phải tạo lô mới."
        )
    before = lot.so_luong_ton
    lot.cap_nhat_ton_kho(data.so_luong_thuc_te - before)
    db.add(
        models.DieuChinhTon(
            ma_lo=ma_lo,
            so_luong_truoc=before,
            so_luong_sau=lot.so_luong_ton,
            ly_do=data.ly_do,
            ma_nv=user.ma_nv,
        )
    )
    db.flush()
    return lot
