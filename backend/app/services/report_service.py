"""Báo cáo Manager: tổng hợp giao dịch thật theo khoảng ngày, không hard-code KPI."""

from datetime import datetime, time, timedelta
from sqlalchemy import func
from app import models


def report(db, start_date, end_date):
    start = datetime.combine(start_date, time.min)
    end = datetime.combine(end_date + timedelta(days=1), time.min)
    day = func.date(models.HoaDonBan.thoi_gian_ban)
    revenue = models.ChiTietBan.so_luong * models.ChiTietBan.don_gia
    query = (
        db.query(
            day.label("day"), func.sum(models.ChiTietBan.so_luong), func.sum(revenue)
        )
        .join(models.HoaDonBan, models.HoaDonBan.ma_hd == models.ChiTietBan.ma_hd)
        .filter(
            models.HoaDonBan.thoi_gian_ban >= start,
            models.HoaDonBan.thoi_gian_ban < end,
        )
    )
    indexed = {
        str(d): (int(q), int(v)) for d, q, v in query.group_by(day).order_by(day).all()
    }
    daily = []
    cursor = start_date
    while cursor <= end_date:
        q, v = indexed.get(cursor.isoformat(), (0, 0))
        daily.append({"ngay": cursor.isoformat(), "so_luong_ban": q, "doanh_thu": v})
        cursor += timedelta(days=1)
    top = (
        db.query(
            models.SanPham.ten_sp,
            func.sum(models.ChiTietBan.so_luong),
            func.sum(revenue),
        )
        .select_from(models.ChiTietBan)
        .join(models.HoaDonBan, models.HoaDonBan.ma_hd == models.ChiTietBan.ma_hd)
        .join(models.LoHang, models.LoHang.ma_lo == models.ChiTietBan.ma_lo)
        .join(models.SanPham, models.SanPham.ma_sp == models.LoHang.ma_sp)
        .filter(
            models.HoaDonBan.thoi_gian_ban >= start,
            models.HoaDonBan.thoi_gian_ban < end,
        )
        .group_by(models.SanPham.ma_sp, models.SanPham.ten_sp)
        .order_by(func.sum(revenue).desc())
        .limit(10)
        .all()
    )
    disposed = (
        db.query(
            func.sum(models.XuLyRuiRo.so_luong),
            func.sum(models.XuLyRuiRo.so_luong * models.XuLyRuiRo.gia_tham_chieu),
        )
        .filter(
            models.XuLyRuiRo.loai_xu_ly == "XuatHuy",
            models.XuLyRuiRo.trang_thai == "DaHoanTat",
            models.XuLyRuiRo.hoan_tat_luc >= start,
            models.XuLyRuiRo.hoan_tat_luc < end,
        )
        .one()
    )
    invoices = (
        db.query(func.count(models.HoaDonBan.ma_hd))
        .filter(
            models.HoaDonBan.thoi_gian_ban >= start,
            models.HoaDonBan.thoi_gian_ban < end,
        )
        .scalar()
    )
    return {
        "tu_ngay": start_date,
        "den_ngay": end_date,
        "theo_ngay": daily,
        "tong_doanh_thu": sum(x["doanh_thu"] for x in daily),
        "tong_so_luong_ban": sum(x["so_luong_ban"] for x in daily),
        "so_hoa_don": invoices,
        "so_luong_da_huy": int(disposed[0] or 0),
        "gia_tri_huy_tham_chieu": int(disposed[1] or 0),
        "top_san_pham": [
            {"ten_sp": n, "so_luong_ban": int(q), "doanh_thu": int(v)}
            for n, q, v in top
        ],
    }
