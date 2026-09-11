from copy import deepcopy
from datetime import date, datetime
import json
import pytest
from app import models
from scripts.refresh_calendar import build_changes, replay_changes, refresh_csv_data, refresh_database
from scripts.dataset_io import validate_dataset, write_dataset


def snapshot(db):
    return {t.name: [dict(r) for r in db.execute(t.select().order_by(*t.primary_key.columns)).mappings()]
            for t in models.LoHang.metadata.sorted_tables}


def test_refresh_preserves_values_is_repeatable_and_restorable(env, dataset):
    _, Session = env
    with Session.begin() as db:
        before = snapshot(db)
        changes = build_changes(db, dataset, date(2026, 9, 11))
        assert replay_changes(db, changes) > 0
        after = snapshot(db)
        assert replay_changes(db, changes) == 0
        # Chỉ ba cột ngày lô và thời gian hóa đơn được phép đổi.
        for table, rows in before.items():
            ignore = {"ngay_san_xuat", "ngay_nhap", "han_su_dung"} if table == "lo_hang" else {"thoi_gian_ban"} if table == "hoa_don_ban" else set()
            assert [{k: v for k, v in r.items() if k not in ignore} for r in rows] == [
                {k: v for k, v in r.items() if k not in ignore} for r in after[table]]
        assert replay_changes(db, changes, restore=True) > 0
        assert snapshot(db) == before


def test_manual_sale_count_and_pending_action_preserved(env, dataset, staff, manager):
    client, Session = env
    sale = client.post('/api/ban-hang', auth=staff, json={"barcode": "DEMO000001", "so_luong": 1})
    assert sale.status_code == 200
    invoice = sale.json()["ma_hd"]
    with Session.begin() as db:
        original_stamp = db.get(models.HoaDonBan, invoice).thoi_gian_ban
        changes = build_changes(db, dataset, date(2026, 9, 11))
        assert not any(c['key'] == invoice for c in changes)
        replay_changes(db, changes)
        assert db.get(models.HoaDonBan, invoice).thoi_gian_ban == original_stamp
        for detail in db.query(models.ChiTietBan).filter_by(ma_hd=invoice):
            lot = db.get(models.LoHang, detail.ma_lo)
            assert lot.ngay_nhap <= original_stamp.date() < lot.han_su_dung


def test_backup_written_before_update_and_second_run_no_op(env, dataset, tmp_path):
    _, Session = env
    write_dataset(dataset, tmp_path/'scripts/output', date(2026,9,7), 42)
    with Session.begin() as db:
        count, path = refresh_database(db, tmp_path, date(2026,9,11))
        assert count > 0 and path.exists()
        assert json.loads(path.read_text())['changes']
    with Session.begin() as db:
        assert refresh_database(db, tmp_path, date(2026,9,12))[0] == 0
        assert refresh_database(db, tmp_path, date(2026,9,12), restore=True)[0] == count


def test_conflicting_date_rejected_before_any_write(env, dataset):
    _, Session = env
    with Session.begin() as db:
        changes = build_changes(db, dataset, date(2026,9,11))
        replay_changes(db, changes)
        lot_change = next(c for c in changes if c['table'] == 'lo_hang')
        db.get(models.LoHang, lot_change['key']).ngay_san_xuat = date(2020,1,1)
        db.flush()
        before = snapshot(db)
        with pytest.raises(ValueError, match='đã được sửa'):
            replay_changes(db, changes, restore=True)
        assert snapshot(db) == before


def test_csv_foreign_keys_chronology_and_balances(dataset):
    data = refresh_csv_data(deepcopy(dataset), date(2026,9,11))
    validate_dataset(data, date(2026,9,11))
    assert all(date(2026,8,1) <= h['thoi_gian_ban'].date() <= date(2026,9,10) for h in data['hoa_don_ban'])


def test_staff_gets_expiry_configuration_without_changing_existing_lots(env, staff):
    client, Session = env
    with Session() as db:
        before = snapshot(db)
    response = client.get('/api/cau-hinh-han-su-dung', auth=staff)
    assert response.status_code == 200
    assert response.json()['SP0001'] == 30
    assert response.json()['SP0007'] == 7
    assert client.get('/api/cau-hinh-han-su-dung').status_code == 401
    with Session() as db:
        assert snapshot(db) == before


def test_restore_rejects_new_sale_after_original_expiry(env, dataset):
    from datetime import timedelta
    _, Session = env
    with Session.begin() as db:
        lot = db.query(models.LoHang).filter(models.LoHang.so_luong_ton > 0).first()
        old_expiry = lot.han_su_dung
        changes = [{"table": "lo_hang", "key": lot.ma_lo,
                    "before": {"han_su_dung": str(old_expiry)},
                    "after": {"han_su_dung": str(old_expiry + timedelta(days=5))}}]
        replay_changes(db, changes)
        sold_on = lot.han_su_dung - timedelta(days=1)
        db.add(models.HoaDonBan(ma_hd='NEW_USER_SALE', ma_nv=lot.ma_nv_nhap,
                               thoi_gian_ban=datetime.combine(sold_on, datetime.min.time())))
        db.flush()
        db.add(models.ChiTietBan(ma_hd='NEW_USER_SALE', ma_lo=lot.ma_lo, so_luong=1, don_gia=10000))
        lot.cap_nhat_ton_kho(-1)
        db.flush()
        before = snapshot(db)
        with pytest.raises(ValueError, match='không phù hợp'):
            replay_changes(db, changes, restore=True)
        assert snapshot(db) == before
