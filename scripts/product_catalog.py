"""Tên hàng dùng chung cho dữ liệu mới và cập nhật danh mục cũ.

Chỉ đổi tên, giữ mã sản phẩm/nhóm/lô để không làm mất liên kết hóa đơn.
Đây vẫn là dữ liệu mô phỏng, không phải danh mục hay HSD của cửa hàng thật.
"""

FIRST_NAMES = [
    "Sữa tươi nguyên kem 180 ml",
    "Sữa tươi ít đường 180 ml",
    "Sữa chua có đường 100 g",
    "Sữa chua uống dâu 180 ml",
    "Sữa tươi không đường 180 ml",
]
VARIETIES = {
    "NH01": ["Sữa tươi nguyên kem", "Sữa tươi ít đường", "Sữa tươi không đường", "Sữa chua uống dâu", "Sữa chua uống cam"],
    "NH02": ["Bánh mì sandwich", "Bánh mì Thổ Nhĩ Kỳ", "Bánh mì Việt Nam", "Bánh bao", "Bánh bông lan"],
    "NH03": ["Nước suối", "Trà xanh", "Nước cam", "Nước táo", "Nước dừa"],
    "NH04": ["Cá ngừ đóng hộp", "Cá mòi đóng hộp", "Đậu đóng hộp", "Ngô đóng hộp", "Thịt hộp"],
    "NH05": ["Rau cải", "Cà rốt", "Cà chua", "Dưa leo", "Táo"],
}
PACKS = {
    "NH01": ["200 ml", "250 ml", "500 ml", "1 lít", "hộp 4 chai"],
    "NH02": ["gói nhỏ", "gói vừa", "gói lớn", "hộp 2 phần", "hộp 4 phần"],
    "NH03": ["250 ml", "350 ml", "500 ml", "1 lít", "1,5 lít"],
    "NH04": ["150 g", "200 g", "250 g", "300 g", "400 g"],
    "NH05": ["200 g", "300 g", "500 g", "750 g", "1 kg"],
}


def product_name(index, group):
    if 1 <= index <= 5 and group == "NH01":
        return FIRST_NAMES[index - 1]
    position = max(0, (index - 6) // 5)
    varieties = VARIETIES[group]
    return f"{varieties[position % len(varieties)]} — {PACKS[group][(position // len(varieties)) % 5]}"


def update_catalog(db):
    """Cập nhật tên bộ SP mẫu; không chạm tồn, giá, ngày, mã hay giao dịch."""
    from app.models import SanPham

    changed = 0
    for product in db.query(SanPham).all():
        code = product.ma_sp
        if not code.startswith("SP") or not code[2:].isdigit():
            continue
        index = int(code[2:])
        if not 1 <= index <= 120 or product.ma_nhom not in VARIETIES:
            continue
        name = product_name(index, product.ma_nhom)
        if product.ten_sp != name:
            product.ten_sp = name
            changed += 1
    db.flush()
    return changed
