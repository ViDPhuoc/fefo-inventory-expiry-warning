"""Xác nhận dữ liệu bổ sung chạy qua cùng API thật và không đụng dữ liệu cũ."""
from datetime import date
import pytest
from sqlalchemy.exc import IntegrityError
from app import models
from app.database import Base
from scripts.presentation_data import add_presentation_data


def test_balanced_colors_all_windows_and_next_day(env, manager, monkeypatch):
    client, Session = env
    with Session.begin() as db:
        result = add_presentation_data(db, date(2026, 9, 7))
        assert result["so_lo_con_hang_moi"] == 15
    for today in ("2026-09-07", "2026-09-08"):
        monkeypatch.setenv("APP_TODAY", today)
        for window in (7, 14, 30, 60, 90, 180):
            response = client.get(f"/api/dashboard?q=LOBS&so_ngay_lookback={window}", auth=manager)
            assert response.status_code == 200, response.text
            data = response.json()
            assert data["total"] == 15
            assert data["thong_ke"]["so_luong_theo_muc"] == {"Do": 5, "Vang": 5, "Xanh": 5}
            assert data["thong_ke"]["lo_thieu_du_lieu"] == 0
            assert all({r["muc_rui_ro"] for r in data["danh_sach"] if r["ma_nhom"] == f"NH{i:02d}"} == {"Do", "Vang", "Xanh"} for i in range(1, 6))


def test_old_rows_unchanged_and_rerun_preserves_sale(env, staff):
    client, Session = env
    with Session.begin() as db:
        before = {t.name: set(db.execute(t.select()).all()) for t in Base.metadata.sorted_tables}
        add_presentation_data(db, date(2026, 9, 7))
        for table in Base.metadata.sorted_tables:
            assert before[table.name].issubset(set(db.execute(table.select()).all()))
    # UI chỉ chọn tên và vẫn dùng API bán hiện có để trừ đúng lô mới.
    sale = client.post("/api/ban-hang", json={"barcode": "NOIBO-BS01X", "so_luong": 2}, auth=staff)
    assert sale.status_code == 200, sale.text
    assert sale.json()["cac_lo_da_tru"][0]["ma_lo"] == "LOBS01X"
    with Session.begin() as db:
        before_repeat = {t.name: set(db.execute(t.select()).all()) for t in Base.metadata.sorted_tables}
        assert add_presentation_data(db, date(2026, 9, 7))["da_them"] is False
        for table in Base.metadata.sorted_tables:
            assert before_repeat[table.name] == set(db.execute(table.select()).all())
        assert db.get(models.LoHang, "LOBS01X").so_luong_ton == 18


def test_history_consistent_and_expired_red_blocked(env, staff, monkeypatch):
    client, Session = env
    with Session.begin() as db:
        add_presentation_data(db, date(2026, 9, 7))
        history = db.query(models.ChiTietBan, models.LoHang, models.HoaDonBan).join(
            models.LoHang, models.ChiTietBan.ma_lo == models.LoHang.ma_lo
        ).join(models.HoaDonBan, models.ChiTietBan.ma_hd == models.HoaDonBan.ma_hd).filter(
            models.LoHang.ma_lo.like("LSBS%")
        ).all()
        assert len(history) == 450
        for detail, lot, invoice in history:
            assert lot.so_luong_nhap - detail.so_luong == lot.so_luong_ton == 0
            assert lot.ngay_nhap <= invoice.thoi_gian_ban.date() < lot.han_su_dung
    monkeypatch.setenv("APP_TODAY", "2026-09-08")
    response = client.post("/api/ban-hang", json={"barcode": "NOIBO-BS02D", "so_luong": 1}, auth=staff)
    assert response.status_code == 409


def test_failure_rolls_back_whole_addition(env):
    _, Session = env
    with Session.begin() as db:
        db.add(models.HoaDonBan(ma_hd="BHBS30", ma_nv="NV002"))
    with pytest.raises(IntegrityError):
        with Session.begin() as db:
            add_presentation_data(db, date(2026, 9, 7))
    with Session() as db:
        assert db.query(models.SanPham).filter(models.SanPham.ma_sp.like("BS%" )).count() == 0
