"""Bổ sung 15 tình huống mô phỏng; không cập nhật/xóa hàng hay giao dịch cũ.

Mức màu được tính bằng nghiệp vụ đang dùng, không ghi nhãn màu vào CSDL.
Lịch sử 30 ngày bán 12 đơn vị/ngày giúp thử các cửa sổ từ 7 đến 180 ngày.
"""

from datetime import datetime, time, timedelta
from app import models
from app.services.alert_service import get_dashboard_data, summarize

CATALOG = {
    "NH01": ["Sữa tươi thanh trùng 200 ml", "Sữa chua việt quất 100 g", "Phô mai lát 100 g"],
    "NH02": ["Bánh mì sandwich gà 120 g", "Bánh mì Thổ Nhĩ Kỳ 180 g", "Bánh mì chà bông 90 g"],
    "NH03": ["Nước cam chai 350 ml", "Trà ô long chai 500 ml", "Nước khoáng chai 500 ml"],
    "NH04": ["Cá hộp sốt cà 155 g", "Đậu đỏ đóng hộp 400 g", "Mì ly hải sản 65 g"],
    "NH05": ["Xà lách thủy tinh 300 g", "Cà chua bi 500 g", "Táo đỏ túi 1 kg"],
}
LEVELS = ("D", "V", "X")


def add_presentation_data(db, today):
    """Caller bọc trong transaction: lỗi bất kỳ thì hoàn tác cả lần bổ sung.

    Mã cố định làm lệnh chạy lại không nhân đôi hay phục hồi hàng đã bán thử.
    """
    groups = {g.ma_nhom: g for g in db.query(models.NhomHang).all()}
    if not set(CATALOG).issubset(groups):
        raise ValueError("Thiếu nhóm hàng của bài. Hãy chạy CHAY_DEMO_WINDOWS.bat trước.")
    staff = db.query(models.NguoiDung).filter_by(vai_tro="Staff").order_by(models.NguoiDung.ma_nv).first()
    if not staff:
        raise ValueError("Chưa có nhân viên để ghi nhận dữ liệu bổ sung.")
    specs = [(f"BS{group[-2:]}{level}", group, level, name)
             for group, names in CATALOG.items() for level, name in zip(LEVELS, names)]
    ids = [s[0] for s in specs]
    existing = {p.ma_sp: p for p in db.query(models.SanPham).filter(models.SanPham.ma_sp.in_(ids)).all()}
    if existing:
        # Không nhận nhầm mã trùng của người dùng là bộ dữ liệu của script.
        if len(existing) != len(specs) or any(
            existing[code].ten_sp != name or existing[code].ma_nhom != group
            or existing[code].barcode != f"NOIBO-{code}"
            or db.get(models.LoHang, f"LO{code}") is None
            or db.get(models.LoHang, f"LO{code}").ma_sp != code
            for code, group, _, name in specs
        ):
            raise ValueError("Mã BS đang có dữ liệu khác hoặc bộ bổ sung chưa đầy đủ; không ghi đè.")
        return {"da_them": False, "so_san_pham_moi": 0, "ghi_chu": "Đã có bộ bổ sung; giữ nguyên các thao tác bạn đã thử."}

    for code, group_id, level, name in specs:
        db.add(models.SanPham(ma_sp=code, barcode=f"NOIBO-{code}", ten_sp=name,
                             gia_ban=20000, ma_nhom=group_id, dang_kinh_doanh=True))
    db.flush()

    # Một hóa đơn mô phỏng/ngày, gồm 15 sản phẩm; không tạo giao dịch tương lai.
    for offset in range(30, 0, -1):
        sold_on = today - timedelta(days=offset)
        hd = f"BHBS{offset:02d}"
        db.add(models.HoaDonBan(ma_hd=hd, ma_nv=staff.ma_nv,
                               thoi_gian_ban=datetime.combine(sold_on, time(12))))
        for code, group_id, _, _ in specs:
            yellow = groups[group_id].muc_canh_bao_vang
            received = sold_on - timedelta(days=yellow + 1)
            # HSD sau ngày bán; nhập khi chưa cận hạn. Lô lịch sử được bán hết.
            lot_id = f"LS{code}{offset:02d}"
            db.add(models.LoHang(ma_lo=lot_id, ma_sp=code,
                                 ngay_san_xuat=received, ngay_nhap=received,
                                 han_su_dung=sold_on + timedelta(days=1),
                                 so_luong_nhap=12, so_luong_ton=0, trang_thai="DaBanHet",
                                 ty_le_giam=0, ma_nv_nhap=staff.ma_nv))
        db.flush()
        for code, _, _, _ in specs:
            db.add(models.ChiTietBan(ma_hd=hd, ma_lo=f"LS{code}{offset:02d}", so_luong=12, don_gia=20000))
    db.flush()

    for code, group_id, level, _ in specs:
        group = groups[group_id]
        if level == "D":
            days, stock = group.muc_canh_bao_do, 30
        elif level == "V":
            # Vàng do nguy cơ tồn dư: đủ lớn ngay cả ở tốc độ cao nhất 12/ngày.
            # Không sát ranh đỏ để sáng hôm sau cả 5 lô vàng lại chuyển sang đỏ.
            days = max(group.muc_canh_bao_vang + 3, 7)
            stock = 12 * days + 24
        else:
            # Với N=180, rate=360/180=2: vẫn đủ bán 20 trước HSD.
            days, stock = max(group.muc_canh_bao_vang + 7, 14), 20
        received = today - timedelta(days=group.muc_canh_bao_vang + 1)
        db.add(models.LoHang(ma_lo=f"LO{code}", ma_sp=code,
                             ngay_san_xuat=received, ngay_nhap=received,
                             han_su_dung=today + timedelta(days=days),
                             so_luong_nhap=stock, so_luong_ton=stock,
                             trang_thai="DangGiaoDich", ty_le_giam=0, ma_nv_nhap=staff.ma_nv))
    db.flush()
    return {"da_them": True, "so_san_pham_moi": 15, "so_lo_con_hang_moi": 15,
            "so_lo_lich_su_da_ban_het": 450, "so_hoa_don_mo_phong": 30}


def presentation_summary(db, lookback=14):
    rows = [r for r in get_dashboard_data(db, lookback) if r["ma_lo"].startswith("LOBS")]
    return {"thong_ke": summarize(rows), "danh_sach": rows}
