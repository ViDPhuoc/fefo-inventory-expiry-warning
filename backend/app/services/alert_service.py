"""UC04: tổng hợp tốc độ một lần cho các SKU, rồi phân bổ chung theo FEFO."""

from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from app import models
from app.config import business_today
from app.services.forecast import allocate_fefo, classify_risk


def get_dashboard_data(db, so_ngay_lookback=14):
    today = business_today()
    start = datetime.combine(today - timedelta(days=so_ngay_lookback), time.min)
    end = datetime.combine(today, time.min)
    # Cửa sổ [hôm nay - N, hôm nay): đúng N ngày trọn vẹn, không lấy ngày tương lai.
    sales = dict(
        db.query(models.LoHang.ma_sp, func.sum(models.ChiTietBan.so_luong))
        .join(models.ChiTietBan, models.ChiTietBan.ma_lo == models.LoHang.ma_lo)
        .join(models.HoaDonBan, models.HoaDonBan.ma_hd == models.ChiTietBan.ma_hd)
        .filter(
            models.HoaDonBan.thoi_gian_ban >= start,
            models.HoaDonBan.thoi_gian_ban < end,
        )
        .group_by(models.LoHang.ma_sp)
        .all()
    )
    lots = (
        db.query(models.LoHang)
        .options(
            joinedload(models.LoHang.san_pham).joinedload(models.SanPham.nhom_hang)
        )
        .filter(models.LoHang.so_luong_ton > 0, models.LoHang.trang_thai != "DaXuatHuy")
        .all()
    )
    by_product = defaultdict(list)
    for lot in lots:
        by_product[lot.ma_sp].append(lot)
    output = []
    for product_id, product_lots in by_product.items():
        rate = (
            Decimal(sales[product_id]) / Decimal(so_ngay_lookback)
            if product_id in sales
            else None
        )
        raw = [
            {
                "ma_lo": l.ma_lo,
                "han_su_dung": l.han_su_dung,
                "ngay_nhap": l.ngay_nhap,
                "so_luong_ton": l.so_luong_ton,
                "trang_thai": l.trang_thai,
            }
            for l in product_lots
        ]
        allocation = allocate_fefo(raw, rate, today)
        for lot in product_lots:
            sp, group = lot.san_pham, lot.san_pham.nhom_hang
            days = lot.tinh_so_ngay_con_lai(today)
            expected, surplus = allocation[lot.ma_lo]
            risk, reason = classify_risk(
                days,
                surplus,
                group.muc_canh_bao_vang,
                group.muc_canh_bao_do,
                lot.trang_thai == "ChoXuatHuy",
            )
            output.append(
                {
                    "ma_lo": lot.ma_lo,
                    "ma_sp": sp.ma_sp,
                    "barcode": sp.barcode,
                    "ten_sp": sp.ten_sp,
                    "ma_nhom": group.ma_nhom,
                    "ten_nhom": group.ten_nhom,
                    "han_su_dung": lot.han_su_dung,
                    "so_ngay_con_lai": days,
                    "so_luong_ton": lot.so_luong_ton,
                    "trang_thai": lot.trang_thai,
                    "ty_le_giam": float(lot.ty_le_giam),
                    "gia_ban": int(sp.gia_ban),
                    "toc_do_tieu_thu_ngay": (
                        round(float(rate), 3) if rate is not None else None
                    ),
                    "tong_so_luong_ban_trong_ky": (
                        int(sales[product_id]) if product_id in sales else None
                    ),
                    "co_du_lieu_ban": rate is not None,
                    "so_luong_uoc_ban_duoc": expected,
                    "so_luong_nguy_co_ton_du": surplus,
                    "muc_rui_ro": risk,
                    "ly_do": reason,
                    "da_het_han": days <= 0,
                    "gia_tri_ton_du_tham_chieu": (
                        surplus * int(sp.gia_ban) if surplus is not None else None
                    ),
                }
            )
    order = {"Do": 0, "Vang": 1, "Xanh": 2}
    output.sort(
        key=lambda r: (order[r["muc_rui_ro"]], r["so_ngay_con_lai"], r["ma_lo"])
    )
    return output


def summarize(rows):
    levels = {
        key: sum(r["muc_rui_ro"] == key for r in rows) for key in ["Do", "Vang", "Xanh"]
    }
    groups = {}
    for r in rows:
        group = groups.setdefault(
            r["ma_nhom"],
            {"ten_nhom": r["ten_nhom"], "Do": 0, "Vang": 0, "Xanh": 0, "ton_du": 0},
        )
        group[r["muc_rui_ro"]] += 1
        group["ton_du"] += r["so_luong_nguy_co_ton_du"] or 0
    return {
        "so_luong_theo_muc": levels,
        "tong_lo": len(rows),
        "tong_ton": sum(r["so_luong_ton"] for r in rows),
        "lo_da_het_han": sum(r["da_het_han"] for r in rows),
        "lo_thieu_du_lieu": sum(not r["co_du_lieu_ban"] for r in rows),
        "tong_so_luong_nguy_co": sum(r["so_luong_nguy_co_ton_du"] or 0 for r in rows),
        "gia_tri_ton_du_tham_chieu": sum(
            r["gia_tri_ton_du_tham_chieu"] or 0 for r in rows
        ),
        "theo_nhom": list(groups.values()),
    }
