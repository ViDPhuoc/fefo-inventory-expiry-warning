"""Pandas phân tích CSV; dùng chung allocate_fefo/classify_risk với FastAPI.
Không duy trì hai phiên bản công thức khác nhau như bản code ban đầu.
"""

import argparse
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.forecast import allocate_fefo, classify_risk
from dataset_io import read_dataset


def analyze(directory, as_of, lookback=14):
    if not 1 <= lookback <= 180:
        raise ValueError("Cửa sổ lịch sử phải trong 1..180 ngày.")
    dataset = read_dataset(directory)
    lots = pd.DataFrame(dataset["lo_hang"])
    invoices = pd.DataFrame(dataset["hoa_don_ban"])
    details = pd.DataFrame(dataset["chi_tiet_ban"])
    joined = details.merge(
        invoices[["ma_hd", "thoi_gian_ban"]], on="ma_hd", validate="many_to_one"
    ).merge(lots[["ma_lo", "ma_sp"]], on="ma_lo", validate="many_to_one")
    start, end = pd.Timestamp(as_of - timedelta(days=lookback)), pd.Timestamp(as_of)
    sales = (
        joined[(joined.thoi_gian_ban >= start) & (joined.thoi_gian_ban < end)]
        .groupby("ma_sp")
        .so_luong.sum()
        .to_dict()
    )
    products = {p["ma_sp"]: p for p in dataset["san_pham"]}
    groups = {g["ma_nhom"]: g for g in dataset["nhom_hang"]}
    active = defaultdict(list)
    for lot in dataset["lo_hang"]:
        if lot["so_luong_ton"] > 0 and lot["trang_thai"] != "DaXuatHuy":
            active[lot["ma_sp"]].append(lot)
    result = []
    for ma_sp, product_lots in active.items():
        rate = (
            Decimal(int(sales[ma_sp])) / Decimal(lookback) if ma_sp in sales else None
        )
        allocation = allocate_fefo(product_lots, rate, as_of)
        product = products[ma_sp]
        group = groups[product["ma_nhom"]]
        for lot in product_lots:
            days = (lot["han_su_dung"] - as_of).days
            expected, surplus = allocation[lot["ma_lo"]]
            risk, reason = classify_risk(
                days,
                surplus,
                group["muc_canh_bao_vang"],
                group["muc_canh_bao_do"],
                lot["trang_thai"] == "ChoXuatHuy",
            )
            result.append(
                {
                    "ma_lo": lot["ma_lo"],
                    "ten_sp": product["ten_sp"],
                    "so_luong_ton": lot["so_luong_ton"],
                    "so_ngay_con_lai": days,
                    "toc_do_tieu_thu_ngay": (
                        round(float(rate), 3) if rate is not None else None
                    ),
                    "so_luong_uoc_ban_duoc": expected,
                    "so_luong_nguy_co_ton_du": surplus,
                    "muc_rui_ro": risk,
                    "ly_do": reason,
                }
            )
    return pd.DataFrame(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--lookback", type=int, default=14)
    args = parser.parse_args()
    result = analyze(ROOT / "scripts/output", args.as_of, args.lookback)
    result.to_csv(
        ROOT / "scripts/output/dashboard_snapshot.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print(result.muc_rui_ro.value_counts().to_string())
    print(
        "Tổng lượng nguy cơ dư (chỉ phần ước tính được):",
        int(result.so_luong_nguy_co_ton_du.sum()),
    )
    print(result[result.ma_lo.str.startswith("DEMO_")].to_string(index=False))
