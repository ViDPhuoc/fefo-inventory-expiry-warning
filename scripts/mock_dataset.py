"""Sinh dữ liệu giao dịch theo thời gian; không sửa tồn/HSD sau khi đã bán.

Chỉ dùng thư viện chuẩn. Các tình huống demo được tạo bằng nhập hàng và
bán hàng hợp lệ, cùng thỏa phương trình nhập - bán = tồn.
"""

import random
from datetime import date, datetime, time, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.passwords import hash_password
from scripts.product_catalog import product_name

GROUPS = [
    ("NH01", "Sữa và chế phẩm", 20, 7, 2, 8),
    ("NH02", "Bánh và thực phẩm chế biến", 5, 2, 1, 6),
    ("NH03", "Đồ uống đóng chai", 180, 30, 10, 10),
    ("NH04", "Đồ hộp và thực phẩm khô", 540, 45, 15, 4),
    ("NH05", "Rau củ quả", 7, 3, 1, 12),
]


def build_dataset(as_of: date, products=120, days=180, seed=42):
    if products < 5 or days < 14:
        raise ValueError("Cần ít nhất 5 sản phẩm và 14 ngày lịch sử.")
    rng = random.Random(seed)
    data = {
        name: []
        for name in [
            "nhom_hang",
            "nguoi_dung",
            "san_pham",
            "lo_hang",
            "hoa_don_ban",
            "chi_tiet_ban",
        ]
    }
    for code, name, shelf, yellow, red, rate in GROUPS:
        data["nhom_hang"].append(
            dict(
                ma_nhom=code,
                ten_nhom=name,
                muc_canh_bao_vang=yellow,
                muc_canh_bao_do=red,
            )
        )
    created = datetime.combine(as_of - timedelta(days=days + 30), time(8))
    for code, username, name, role in [
        ("NV001", "manager1", "Quản lý demo", "Manager"),
        ("NV002", "staff1", "Nhân viên demo", "Staff"),
    ]:
        data["nguoi_dung"].append(
            dict(
                ma_nv=code,
                ho_ten=name,
                ten_dang_nhap=username,
                mat_khau_hash=hash_password("Demo@2026"),
                vai_tro=role,
                ngay_tao=created,
            )
        )
    for i in range(1, products + 1):
        g = 0 if i <= 5 else (i - 6) % 5
        # Barcode nội bộ duy nhất để demo; không giả nhận là mã EAN-13 thương mại.
        data["san_pham"].append(
            dict(
                ma_sp=f"SP{i:04d}",
                barcode=f"DEMO{i:06d}",
                ten_sp=product_name(i, GROUPS[g][0]),
                gia_ban=(
                    10000 if i <= 5 else rng.choice([8000, 12000, 18000, 22000, 35000])
                ),
                ma_nhom=GROUPS[g][0],
                dang_kinh_doanh=True,
            )
        )
    by_product = {p["ma_sp"]: [] for p in data["san_pham"]}

    def receipt(product, received, expiry, quantity, code=None):
        lot = dict(
            ma_lo=code or f'LO{len(data["lo_hang"])+1:07d}',
            ma_sp=product["ma_sp"],
            ngay_san_xuat=received - timedelta(days=1),
            han_su_dung=expiry,
            ngay_nhap=received,
            so_luong_nhap=quantity,
            so_luong_ton=quantity,
            trang_thai="DangGiaoDich",
            ty_le_giam=0,
            ma_nv_nhap="NV002",
        )
        data["lo_hang"].append(lot)
        by_product[product["ma_sp"]].append(lot)
        return lot

    def sell(product, sold_on, quantity):
        candidates = sorted(
            [
                l
                for l in by_product[product["ma_sp"]]
                if l["so_luong_ton"] > 0
                and l["ngay_nhap"] <= sold_on < l["han_su_dung"]
            ],
            key=lambda l: (l["han_su_dung"], l["ngay_nhap"], l["ma_lo"]),
        )
        quantity = min(quantity, sum(l["so_luong_ton"] for l in candidates))
        if quantity <= 0:
            return
        hd = f'HD{len(data["hoa_don_ban"])+1:08d}'
        data["hoa_don_ban"].append(
            dict(
                ma_hd=hd,
                ma_nv="NV002",
                thoi_gian_ban=datetime.combine(
                    sold_on, time(rng.randrange(8, 22), rng.randrange(60))
                ),
            )
        )
        for lot in candidates:
            if quantity == 0:
                break
            sold = min(quantity, lot["so_luong_ton"])
            data["chi_tiet_ban"].append(
                dict(
                    ma_ct=len(data["chi_tiet_ban"]) + 1,
                    ma_hd=hd,
                    ma_lo=lot["ma_lo"],
                    so_luong=sold,
                    don_gia=product["gia_ban"],
                )
            )
            quantity -= sold
            lot["so_luong_ton"] -= sold
            if lot["so_luong_ton"] == 0:
                lot["trang_thai"] = "DaBanHet"

    for offset in range(days):
        day = as_of - timedelta(days=days - offset)
        for product in data["san_pham"][5:]:
            meta = GROUPS[int(product["ma_nhom"][-2:]) - 1]
            if offset == 0 or rng.random() < 1 / 6:
                # Hàng nhập đều còn xa ngưỡng Vàng tại ngày nhập.
                receipt(
                    product,
                    day,
                    day + timedelta(days=meta[2] + rng.randrange(4)),
                    rng.randrange(40, 121),
                )
            sell(product, day, max(0, round(rng.gauss(meta[5], meta[5] * 0.35))))
    for index, daily in [(0, 3), (1, 3), (4, 10)]:
        product = data["san_pham"][index]
        receipt(
            product,
            as_of - timedelta(days=20),
            as_of + timedelta(days=1),
            14 * daily,
            f"DEMO_HISTORY_{index+1}",
        )
        for back in range(14, 0, -1):
            sell(product, as_of - timedelta(days=back), daily)
    receipt(
        data["san_pham"][0], as_of, as_of + timedelta(days=10), 100, "DEMO_100_10_3"
    )
    receipt(data["san_pham"][1], as_of, as_of + timedelta(days=10), 20, "DEMO_SHARED_A")
    receipt(data["san_pham"][1], as_of, as_of + timedelta(days=10), 20, "DEMO_SHARED_B")
    receipt(
        data["san_pham"][2],
        as_of - timedelta(days=20),
        as_of - timedelta(days=1),
        15,
        "DEMO_EXPIRED",
    )
    receipt(
        data["san_pham"][3], as_of, as_of + timedelta(days=30), 20, "DEMO_NO_HISTORY"
    )
    receipt(data["san_pham"][4], as_of, as_of + timedelta(days=60), 20, "DEMO_SAFE")
    return data
