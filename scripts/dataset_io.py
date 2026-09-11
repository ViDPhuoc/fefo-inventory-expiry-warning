"""CSV có tên cột rõ ràng; dùng chung cho CLI import và bộ kiểm tra dữ liệu."""

import csv
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ORDER = [
    "nhom_hang",
    "nguoi_dung",
    "san_pham",
    "lo_hang",
    "hoa_don_ban",
    "chi_tiet_ban",
]
INTS = {
    "muc_canh_bao_vang",
    "muc_canh_bao_do",
    "gia_ban",
    "so_luong_nhap",
    "so_luong_ton",
    "ty_le_giam",
    "ma_ct",
    "so_luong",
    "don_gia",
}
DATES = {"ngay_san_xuat", "han_su_dung", "ngay_nhap"}
TIMES = {"ngay_tao", "thoi_gian_ban"}


def write_dataset(data, directory, as_of, seed):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for table in ORDER:
        with (directory / f"{table}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[table][0]))
            writer.writeheader()
            writer.writerows(data[table])
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "as_of": str(as_of),
                "seed": seed,
                "synthetic": True,
                "counts": {k: len(v) for k, v in data.items()},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def read_dataset(directory):
    result = {}
    for table in ORDER:
        with (Path(directory) / f"{table}.csv").open(
            encoding="utf-8-sig", newline=""
        ) as f:
            result[table] = []
            for row in csv.DictReader(f):
                parsed = {}
                for key, value in row.items():
                    if key in INTS:
                        value = int(value)
                    elif key in DATES:
                        value = date.fromisoformat(value)
                    elif key in TIMES:
                        value = datetime.fromisoformat(value)
                    elif key == "dang_kinh_doanh":
                        value = value.lower() == "true"
                    parsed[key] = value
                result[table].append(parsed)
    return result


def validate_dataset(data, as_of):
    """Fail trước import: PK/FK, ngày, số lượng, giao dịch và cân bằng từng lô."""
    errors = []
    primary = {
        "nhom_hang": "ma_nhom",
        "nguoi_dung": "ma_nv",
        "san_pham": "ma_sp",
        "lo_hang": "ma_lo",
        "hoa_don_ban": "ma_hd",
        "chi_tiet_ban": "ma_ct",
    }
    maps = {}
    for table, key in primary.items():
        rows = data[table]
        maps[table] = {r[key]: r for r in rows}
        if len(maps[table]) != len(rows):
            errors.append(f"{table}: trùng khóa chính")
    if len({r["barcode"] for r in data["san_pham"]}) != len(data["san_pham"]):
        errors.append("Trùng barcode")
    for group in data["nhom_hang"]:
        if not 0 <= group["muc_canh_bao_do"] < group["muc_canh_bao_vang"]:
            errors.append("Sai ngưỡng nhóm")
    for sp in data["san_pham"]:
        if sp["ma_nhom"] not in maps["nhom_hang"] or sp["gia_ban"] < 0:
            errors.append("Sai dữ liệu sản phẩm")
    for lo in data["lo_hang"]:
        if (
            lo["ma_sp"] not in maps["san_pham"]
            or lo["ma_nv_nhap"] not in maps["nguoi_dung"]
        ):
            errors.append(f'{lo["ma_lo"]}: FK sai')
        if (
            not lo["ngay_san_xuat"] <= lo["ngay_nhap"] < lo["han_su_dung"]
            or lo["ngay_nhap"] > as_of
        ):
            errors.append(f'{lo["ma_lo"]}: ngày sai')
        if (
            not 0 <= lo["so_luong_ton"] <= lo["so_luong_nhap"]
            or lo["so_luong_nhap"] <= 0
        ):
            errors.append(f'{lo["ma_lo"]}: tồn sai')
        if (lo["so_luong_ton"] == 0) != (lo["trang_thai"] == "DaBanHet"):
            errors.append(f'{lo["ma_lo"]}: trạng thái sai')
    for hd in data["hoa_don_ban"]:
        if hd["ma_nv"] not in maps["nguoi_dung"] or hd["thoi_gian_ban"].date() >= as_of:
            errors.append(f'{hd["ma_hd"]}: hóa đơn sai')
    totals, invoice_rows = Counter(), Counter()
    for sale in data["chi_tiet_ban"]:
        lot = maps["lo_hang"].get(sale["ma_lo"])
        invoice = maps["hoa_don_ban"].get(sale["ma_hd"])
        if not lot or not invoice:
            errors.append("Chi tiết bán sai FK")
            continue
        if not lot["ngay_nhap"] <= invoice["thoi_gian_ban"].date() < lot["han_su_dung"]:
            errors.append(f'{lot["ma_lo"]}: bán trước nhập hoặc sau/đúng HSD')
        if sale["so_luong"] <= 0 or sale["don_gia"] < 0:
            errors.append("Giao dịch có số lượng/giá sai")
        totals[sale["ma_lo"]] += sale["so_luong"]
        invoice_rows[sale["ma_hd"]] += 1
    for lot in data["lo_hang"]:
        if lot["so_luong_nhap"] - totals[lot["ma_lo"]] != lot["so_luong_ton"]:
            errors.append(f'{lot["ma_lo"]}: nhập - bán != tồn')
    if any(not invoice_rows[hd] for hd in maps["hoa_don_ban"]):
        errors.append("Hóa đơn rỗng")
    if errors:
        raise ValueError("Dữ liệu không hợp lệ: " + "; ".join(errors[:20]))
    return {k: len(v) for k, v in data.items()}
