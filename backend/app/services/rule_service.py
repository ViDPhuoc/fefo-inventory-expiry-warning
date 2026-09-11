"""UC01: ngưỡng cảnh báo là dữ liệu do Manager cấu hình, không hard-code."""

from app import models
from app.errors import BusinessError


def load_rule(db, ma_nhom):
    group = db.query(models.NhomHang).filter_by(ma_nhom=ma_nhom).first()
    if not group:
        raise BusinessError("Không tìm thấy nhóm hàng.", 404)
    return group


def update_rule(db, ma_nhom, data):
    group = load_rule(db, ma_nhom)
    group.muc_canh_bao_vang = data.muc_canh_bao_vang
    group.muc_canh_bao_do = data.muc_canh_bao_do
    db.flush()
    return group
