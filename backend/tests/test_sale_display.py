from app import models


def test_manager_lot_and_barcode_resolve_same_product(env, manager, staff):
    client, Session = env
    rows = client.get("/api/dashboard?page_size=200", auth=manager).json()["danh_sach"]
    with Session() as db:
        before = db.query(models.HoaDonBan).count()
    for row in rows:
        for code in (row["ma_lo"], row["barcode"], row["ma_sp"]):
            result = client.get("/api/san-pham/tra-cuu", params={"ma": f" {code} "}, auth=staff)
            assert result.status_code == 200, result.text
            assert result.json()["ma_sp"] == row["ma_sp"]
    with Session() as db:
        assert db.query(models.HoaDonBan).count() == before  # Tìm không tự bán.
    assert client.get("/api/san-pham/tra-cuu?ma=NOT_FOUND", auth=staff).status_code == 404
    assert client.get("/api/san-pham/tra-cuu?ma=%20", auth=staff).status_code == 422
    assert client.get("/api/san-pham/tra-cuu?ma=DEMO000001").status_code == 401


def test_ambiguous_code_does_not_choose_wrong_product(env, staff):
    client, Session = env
    with Session.begin() as db:
        db.get(models.SanPham, "SP0002").barcode = "SP0001"
    result = client.get("/api/san-pham/tra-cuu?ma=SP0001", auth=staff)
    assert result.status_code == 409


def test_original_price_per_lot_does_not_change_fefo_or_total(env, manager, staff):
    client, Session = env
    with Session.begin() as db:
        db.get(models.SanPham, "SP0002").gia_ban = 12000
    command = client.post("/api/xu-ly-rui-ro/DEMO_SHARED_A", auth=manager,
        json={"loai_xu_ly": "GiamGia", "ty_le_giam": 30, "ghi_chu": "Giảm 30% để kiểm tra giá"})
    assert command.status_code == 201, command.text
    done = client.post(f"/api/xu-ly-rui-ro/lenh/{command.json()['ma_xl']}/hoan-tat", auth=staff)
    assert done.status_code == 200
    sale = client.post("/api/ban-hang", auth=staff, json={"barcode": "DEMO000002", "so_luong": 25})
    assert sale.status_code == 200
    invoice = sale.json()
    a, b = invoice["cac_lo_da_tru"]
    assert (a["ma_lo"], a["gia_goc"], a["don_gia"], a["ty_le_giam"], a["so_luong_tru"]) == ("DEMO_SHARED_A", 12000, 8400, 30, 20)
    assert (b["ma_lo"], b["gia_goc"], b["don_gia"], b["ty_le_giam"], b["so_luong_tru"]) == ("DEMO_SHARED_B", 12000, 12000, 0, 5)
    assert invoice["tong_tien"] == 228000
