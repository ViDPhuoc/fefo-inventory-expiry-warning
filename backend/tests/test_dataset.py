"""Kiểm tra toàn vẹn bộ dữ liệu và biên của công thức độc lập với API."""

from datetime import date, timedelta
from decimal import Decimal
import pytest
from scripts.dataset_io import validate_dataset
from app.services.forecast import allocate_fefo, classify_risk


def test_dataset_integrity(dataset):
    counts = validate_dataset(dataset, date(2026, 9, 7))
    assert counts["chi_tiet_ban"] > 0


def test_dataset_rejects_forged_stock(dataset):
    from copy import deepcopy

    bad = deepcopy(dataset)
    bad["lo_hang"][0]["so_luong_ton"] = 999999
    with pytest.raises(ValueError):
        validate_dataset(bad, date(2026, 9, 7))


def test_capacity_after_earlier_lot_expires():
    today = date(2026, 9, 7)
    lots = [
        {
            "ma_lo": "a",
            "ngay_nhap": today,
            "han_su_dung": today + timedelta(days=1),
            "so_luong_ton": 100,
            "trang_thai": "DangGiaoDich",
        },
        {
            "ma_lo": "b",
            "ngay_nhap": today,
            "han_su_dung": today + timedelta(days=10),
            "so_luong_ton": 100,
            "trang_thai": "DangGiaoDich",
        },
    ]
    result = allocate_fefo(lots, Decimal(3), today)
    assert result == {"a": (3, 97), "b": (27, 73)}


@pytest.mark.parametrize(
    "days,expected",
    [(0, "Do"), (-1, "Do"), (2, "Do"), (3, "Vang"), (7, "Vang"), (8, "Xanh")],
)
def test_threshold_boundaries(days, expected):
    assert classify_risk(days, 0, 7, 2)[0] == expected
