"""UC05: Manager tạo lệnh, Staff xác nhận thực hiện; mỗi bước có dấu vết."""

from app import models
from app.config import business_today, business_now
from app.errors import BusinessError
from app.services.common import lock_lot


def approve(db, ma_lo, data, user):
    lot, product = lock_lot(db, ma_lo)
    if lot.so_luong_ton == 0 or lot.trang_thai in ("DaXuatHuy", "ChoXuatHuy"):
        raise BusinessError("Lô không còn hàng hoặc đang/đã xuất hủy.", 409)
    if db.query(models.XuLyRuiRo).filter_by(ma_lo=ma_lo, trang_thai="ChoXuLy").first():
        raise BusinessError("Lô đã có lệnh chờ thực hiện.", 409)
    if data.loai_xu_ly == "GiamGia" and lot.han_su_dung <= business_today():
        raise BusinessError("Hàng hết hạn không được giảm giá để tiếp tục bán.")
    action = models.XuLyRuiRo(
        ma_lo=ma_lo,
        loai_xu_ly=data.loai_xu_ly,
        ty_le_giam=data.ty_le_giam,
        so_luong=lot.so_luong_ton,
        gia_tham_chieu=product.gia_ban,
        ma_nv_duyet=user.ma_nv,
        trang_thai="ChoXuLy",
        ghi_chu=data.ghi_chu,
    )
    if data.loai_xu_ly == "XuatHuy":
        lot.trang_thai = "ChoXuatHuy"
    db.add(action)
    db.flush()
    return action


def complete(db, ma_xl, user):
    original = db.query(models.XuLyRuiRo).filter_by(ma_xl=ma_xl).first()
    if not original:
        raise BusinessError("Không tìm thấy lệnh xử lý.", 404)
    lot, _ = lock_lot(db, original.ma_lo)
    action = (
        db.query(models.XuLyRuiRo)
        .filter_by(ma_xl=ma_xl)
        .populate_existing()
        .with_for_update()
        .one()
    )
    if action.trang_thai != "ChoXuLy":
        raise BusinessError("Lệnh đã hoàn tất; không thể thực hiện lần hai.", 409)
    if not lot.so_luong_ton:
        raise BusinessError("Lô đã hết hàng, không còn hàng để thực hiện lệnh.", 409)
    if action.loai_xu_ly == "GiamGia":
        if lot.han_su_dung <= business_today():
            raise BusinessError(
                "Lô đã hết hạn trong lúc chờ; cần xử lý xuất hủy, không áp dụng giảm giá.",
                409,
            )
        lot.ty_le_giam = action.ty_le_giam
    else:
        lot.so_luong_ton = 0
        lot.trang_thai = "DaXuatHuy"
    action.ma_nv_thuc_hien = user.ma_nv
    action.hoan_tat_luc = business_now()
    action.trang_thai = "DaHoanTat"
    db.flush()
    return action


def cancel(db, ma_xl, data, user):
    """Hủy lệnh chưa làm để giải quyết lô đã bán hết/đã quá hạn trong lúc chờ."""
    original = db.query(models.XuLyRuiRo).filter_by(ma_xl=ma_xl).first()
    if not original:
        raise BusinessError("Không tìm thấy lệnh xử lý.", 404)
    lot, _ = lock_lot(db, original.ma_lo)
    action = (
        db.query(models.XuLyRuiRo)
        .filter_by(ma_xl=ma_xl)
        .populate_existing()
        .with_for_update()
        .one()
    )
    if action.trang_thai != "ChoXuLy":
        raise BusinessError("Chỉ hủy được lệnh đang chờ.", 409)
    action.trang_thai = "DaHuyLenh"
    action.huy_luc, action.ma_nv_huy, action.ly_do_huy = (
        business_now(),
        user.ma_nv,
        data.ly_do,
    )
    if lot.trang_thai == "ChoXuatHuy":
        lot.trang_thai = "DangGiaoDich" if lot.so_luong_ton else "DaBanHet"
    db.flush()
    return action
