"""Đổi danh mục không được thay giao dịch, tồn kho hay kết quả dự báo."""
from scripts.product_catalog import product_name, update_catalog
from app import models


def test_variety_names():
    names = [product_name(i, f"NH{((i - 6) % 5) + 1:02d}") for i in range(6, 121)]
    assert len(set(names)) == len(names)
    for text in ["sandwich", "Thổ Nhĩ Kỳ", "Việt Nam", "Nước cam", "Cá ngừ", "Cà rốt"]:
        assert any(text in name for name in names)
    assert all("demo" not in name.lower() for name in names)


def test_catalog_update_preserves_data(env, manager):
    client, Session = env
    with Session.begin() as db:
        db.get(models.SanPham, "SP0001").ten_sp = "Sữa demo — tên cũ"
    with Session.begin() as db:
        before = [(l.ma_lo, l.so_luong_ton, l.han_su_dung) for l in db.query(models.LoHang).order_by(models.LoHang.ma_lo)]
        invoices = db.query(models.HoaDonBan).count()
        assert update_catalog(db) == 1
        assert update_catalog(db) == 0
        assert before == [(l.ma_lo, l.so_luong_ton, l.han_su_dung) for l in db.query(models.LoHang).order_by(models.LoHang.ma_lo)]
        assert invoices == db.query(models.HoaDonBan).count()
    rows = client.get("/api/dashboard?q=Sữa tươi nguyên kem", auth=manager).json()["danh_sach"]
    row = next(r for r in rows if r["ma_lo"] == "DEMO_100_10_3")
    assert row["so_luong_nguy_co_ton_du"] == 70
    assert row["ten_sp"] == "Sữa tươi nguyên kem 180 ml"
