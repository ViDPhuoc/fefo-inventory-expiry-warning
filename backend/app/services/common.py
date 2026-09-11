"""Các thao tác khóa dùng chung để mọi luồng thay tồn đều cùng một thứ tự."""

from uuid import uuid4
from app import models
from app.errors import BusinessError


def new_id(prefix):
    # Không dùng COUNT + 1: xóa bản ghi/nhập đồng thời không làm trùng mã.
    return prefix + uuid4().hex


def lock_product(db, ma_sp):
    product = db.query(models.SanPham).filter_by(ma_sp=ma_sp).with_for_update().first()
    if not product:
        raise BusinessError("Không tìm thấy sản phẩm.", 404, "PRODUCT_NOT_FOUND")
    return product


def lock_lot(db, ma_lo):
    initial = db.query(models.LoHang).filter_by(ma_lo=ma_lo).first()
    if not initial:
        raise BusinessError("Không tìm thấy lô hàng.", 404, "LOT_NOT_FOUND")
    # Mọi ghi tồn khóa sản phẩm trước rồi mới khóa lô, tránh đổi thứ tự gây deadlock.
    product = lock_product(db, initial.ma_sp)
    lot = (
        db.query(models.LoHang)
        .filter_by(ma_lo=ma_lo)
        .populate_existing()
        .with_for_update()
        .one()
    )
    return lot, product
