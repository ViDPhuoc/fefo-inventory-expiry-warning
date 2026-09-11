"""Kiểm thử hồi quy cho các quy tắc và giao dịch làm thay đổi tồn kho."""

from datetime import date
import pytest
from app import models


def sale(client, staff, qty, barcode="DEMO000002"):
    return client.post(
        "/api/ban-hang", auth=staff, json={"barcode": barcode, "so_luong": qty}
    )


def test_expired_cannot_sell(env, staff):
    client, Session = env
    r = sale(client, staff, 1, "DEMO000003")
    assert r.status_code == 409
    with Session() as db:
        assert db.get(models.LoHang, "DEMO_EXPIRED").so_luong_ton == 15


@pytest.mark.parametrize("qty", [0, -1, 1.5, True, "3"])
def test_bad_quantity_rejected(env, staff, qty):
    client, Session = env
    with Session() as db:
        before = db.query(models.HoaDonBan).count()
    assert sale(client, staff, qty).status_code == 422
    with Session() as db:
        assert db.query(models.HoaDonBan).count() == before


def test_fefo_split_and_no_partial_sale(env, staff):
    client, Session = env
    assert sale(client, staff, 41).status_code == 409
    with Session() as db:
        assert db.get(models.LoHang, "DEMO_SHARED_A").so_luong_ton == 20
    result = sale(client, staff, 25)
    assert result.status_code == 200
    rows = result.json()["cac_lo_da_tru"]
    assert [(r["ma_lo"], r["so_luong_tru"]) for r in rows] == [
        ("DEMO_SHARED_A", 20),
        ("DEMO_SHARED_B", 5),
    ]


def test_forecast_shared_capacity(env, manager):
    client, _ = env
    r = client.get("/api/dashboard?q=DEMO_SHARED", auth=manager)
    assert r.status_code == 200
    lots = {x["ma_lo"]: x for x in r.json()["danh_sach"]}
    assert lots["DEMO_SHARED_A"]["so_luong_uoc_ban_duoc"] == 20
    assert lots["DEMO_SHARED_B"]["so_luong_uoc_ban_duoc"] == 10
    assert lots["DEMO_SHARED_B"]["so_luong_nguy_co_ton_du"] == 10


def test_example_100_10_3_and_unknown(env, manager):
    client, _ = env
    rows = client.get("/api/dashboard?page_size=200", auth=manager).json()["danh_sach"]
    lots = {r["ma_lo"]: r for r in rows}
    assert lots["DEMO_100_10_3"]["so_luong_nguy_co_ton_du"] == 70
    assert lots["DEMO_100_10_3"]["tong_so_luong_ban_trong_ky"] == 42
    assert lots["DEMO_NO_HISTORY"]["so_luong_nguy_co_ton_du"] is None
    assert lots["DEMO_NO_HISTORY"]["muc_rui_ro"] == "Vang"
    assert lots["DEMO_SAFE"]["muc_rui_ro"] == "Xanh"


@pytest.mark.parametrize("lookback", [0, -1, 181])
def test_lookback_validation(env, manager, lookback):
    assert (
        env[0]
        .get(f"/api/dashboard?so_ngay_lookback={lookback}", auth=manager)
        .status_code
        == 422
    )


def test_roles_and_credentials(env, manager, staff):
    c, _ = env
    assert c.get("/api/dashboard").status_code == 401
    assert c.get("/api/me", auth=("manager1", "wrong")).status_code == 401
    assert c.get("/api/dashboard", auth=staff).status_code == 403
    assert sale(c, manager, 1).status_code == 403
    assert c.get("/api/me", auth=staff).json()["vai_tro"] == "Staff"


def test_receipt_and_adjustment(env, staff):
    c, Session = env
    body = {
        "ma_sp": "SP0001",
        "ngay_san_xuat": "2026-09-06",
        "han_su_dung": "2026-10-10",
        "so_luong_nhap": 10,
    }
    created = c.post("/api/lo-hang", auth=staff, json=body)
    assert created.status_code == 201
    ma = created.json()["ma_lo"]
    assert (
        c.patch(
            f"/api/lo-hang/{ma}/dieu-chinh",
            auth=staff,
            json={"so_luong_thuc_te": -5, "ly_do": "Kiểm kê"},
        ).status_code
        == 422
    )
    assert (
        c.patch(
            f"/api/lo-hang/{ma}/dieu-chinh",
            auth=staff,
            json={"so_luong_thuc_te": 11, "ly_do": "Kiểm kê"},
        ).status_code
        == 400
    )
    for q, status in [(0, "DaBanHet"), (5, "DangGiaoDich")]:
        response = c.patch(
            f"/api/lo-hang/{ma}/dieu-chinh",
            auth=staff,
            json={"so_luong_thuc_te": q, "ly_do": "Kiểm kê thực tế"},
        )
        assert response.status_code == 200
        assert response.json()["trang_thai"] == status
    with Session() as db:
        assert db.query(models.DieuChinhTon).filter_by(ma_lo=ma).count() == 2
    body["han_su_dung"] = "2026-09-08"
    assert c.post("/api/lo-hang", auth=staff, json=body).status_code == 400
    body["han_su_dung"] = "2026-10-10"
    body["ma_sp"] = "MISSING"
    assert c.post("/api/lo-hang", auth=staff, json=body).status_code == 404


def test_discount_workflow_and_price(env, manager, staff):
    c, _ = env
    data = {"loai_xu_ly": "GiamGia", "ty_le_giam": 50, "ghi_chu": "Dán tem giảm giá"}
    assert (
        c.post("/api/xu-ly-rui-ro/DEMO_SHARED_A", auth=staff, json=data).status_code
        == 403
    )
    response = c.post("/api/xu-ly-rui-ro/DEMO_SHARED_A", auth=manager, json=data)
    assert response.status_code == 201
    action = response.json()["ma_xl"]
    assert sale(c, staff, 1).json()["tong_tien"] == 10000  # Chưa dán tem.
    assert (
        c.post(f"/api/xu-ly-rui-ro/lenh/{action}/hoan-tat", auth=staff).status_code
        == 200
    )
    assert sale(c, staff, 1).json()["tong_tien"] == 5000
    assert (
        c.post(f"/api/xu-ly-rui-ro/lenh/{action}/hoan-tat", auth=staff).status_code
        == 409
    )


@pytest.mark.parametrize("pct", [-1, 0, 100, 150, None])
def test_invalid_discount(env, manager, pct):
    r = env[0].post(
        "/api/xu-ly-rui-ro/DEMO_SHARED_A",
        auth=manager,
        json={"loai_xu_ly": "GiamGia", "ty_le_giam": pct, "ghi_chu": "Kiểm tra tỷ lệ"},
    )
    assert r.status_code == 422


def test_disposal_pending_blocks_sale_then_report(env, manager, staff):
    c, Session = env
    response = c.post(
        "/api/xu-ly-rui-ro/DEMO_SHARED_A",
        auth=manager,
        json={"loai_xu_ly": "XuatHuy", "ghi_chu": "Hàng có vấn đề chất lượng"},
    )
    assert response.status_code == 201
    action = response.json()["ma_xl"]
    assert sale(c, staff, 21).status_code == 409  # Chỉ còn lô B được bán.
    assert (
        c.post(f"/api/xu-ly-rui-ro/lenh/{action}/hoan-tat", auth=staff).status_code
        == 200
    )
    report = c.get(
        "/api/bao-cao?tu_ngay=2026-09-07&den_ngay=2026-09-07", auth=manager
    ).json()
    assert report["so_luong_da_huy"] == 20
    assert report["gia_tri_huy_tham_chieu"] == 200000
    with Session() as db:
        assert db.get(models.LoHang, "DEMO_SHARED_A").trang_thai == "DaXuatHuy"


def test_rules_and_report_range(env, manager):
    c, _ = env
    assert (
        c.put(
            "/api/nhom-hang/NH01",
            auth=manager,
            json={"muc_canh_bao_do": -2, "muc_canh_bao_vang": -1},
        ).status_code
        == 422
    )
    assert (
        c.put(
            "/api/nhom-hang/NH01",
            auth=manager,
            json={"muc_canh_bao_do": 10, "muc_canh_bao_vang": 15},
        ).status_code
        == 200
    )
    rows = c.get("/api/dashboard?q=100", auth=manager).json()["danh_sach"]
    assert next(r for r in rows if r["ma_lo"] == "DEMO_100_10_3")["muc_rui_ro"] == "Do"
    assert (
        c.get(
            "/api/bao-cao?tu_ngay=2026-09-08&den_ngay=2026-09-07", auth=manager
        ).status_code
        == 400
    )


def test_future_sales_do_not_leak_into_velocity(env, manager):
    c, Session = env
    from datetime import datetime

    with Session.begin() as db:
        db.add(
            models.HoaDonBan(
                ma_hd="FUTURE", ma_nv="NV002", thoi_gian_ban=datetime(2026, 9, 8)
            )
        )
        db.flush()
        db.add(
            models.ChiTietBan(
                ma_hd="FUTURE", ma_lo="DEMO_100_10_3", so_luong=999, don_gia=10000
            )
        )
    row = next(
        r
        for r in c.get("/api/dashboard?q=100", auth=manager).json()["danh_sach"]
        if r["ma_lo"] == "DEMO_100_10_3"
    )
    assert row["toc_do_tieu_thu_ngay"] == 3


def test_cancel_pending_disposal_reopens_valid_lot(env, manager, staff):
    c, _ = env
    action = c.post(
        "/api/xu-ly-rui-ro/DEMO_SHARED_A",
        auth=manager,
        json={"loai_xu_ly": "XuatHuy", "ghi_chu": "Chờ kiểm tra chất lượng"},
    ).json()["ma_xl"]
    assert sale(c, staff, 21).status_code == 409
    result = c.post(
        f"/api/xu-ly-rui-ro/lenh/{action}/huy",
        auth=manager,
        json={"ly_do": "Kiểm tra lại: lô còn đủ điều kiện bán"},
    )
    assert result.status_code == 200
    assert result.json()["trang_thai"] == "DaHuyLenh"
    assert sale(c, staff, 21).status_code == 200
