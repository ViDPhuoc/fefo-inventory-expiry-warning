"""Đổi lịch của bộ dữ liệu mô phỏng, không sửa số lượng/giá/mã hay xóa giao dịch.

Lịch hóa đơn mẫu được gom vào tháng trước đến hôm qua. Hóa đơn người dùng
tự tạo giữ nguyên. Ngày lô luôn bao quanh các lần bán, kể cả lần bán mới.
Chỉ CLI chủ động chạy; khởi động ứng dụng không tự đổi ngày.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
import json
from pathlib import Path

from sqlalchemy import select
from app import models

DATE_FIELDS = ("ngay_san_xuat", "ngay_nhap", "han_su_dung")


def calendar_plan(lots, invoices, details, groups, today, other_events=None):
    """Hàm thuần dùng chung cho CSV đính kèm và CSDL hiện có.

invoices chứa cả hóa đơn thực tế; chỉ mã trong seed_invoice_ids được đổi.
lots chỉ chứa lô thuộc bộ mẫu đã xác định ở bước gọi.
    """
    previous_month = today.replace(day=1) - timedelta(days=1)
    start = previous_month.replace(day=1)
    end = today - timedelta(days=1)
    seed_invoices = [v for v in invoices.values() if v["seed"]]
    source_start = min((v["thoi_gian_ban"].date() for v in seed_invoices), default=start)
    source_end = max((v["thoi_gian_ban"].date() for v in seed_invoices), default=end)

    def redate(value):
        span = max(1, (source_end - source_start).days)
        offset = min(span, max(0, (value - source_start).days))
        return start + timedelta(days=offset * (end - start).days // span)

    invoice_dates = {}
    for key, item in invoices.items():
        original = item["thoi_gian_ban"]
        invoice_dates[key] = datetime.combine(redate(original.date()), original.time()) if item["seed"] else original
    sale_days = defaultdict(list)
    for detail in details:
        if detail["ma_lo"] in lots:
            sale_days[detail["ma_lo"]].append(invoice_dates[detail["ma_hd"]].date())

    grouped = defaultdict(list)
    for lot in lots.values():
        grouped[lot["ma_sp"]].append(lot)
    lot_dates = {}
    for product_lots in grouped.values():
        # Tách lô hết hàng để việc thêm lịch sử không làm lệch phân bố lô còn hàng.
        active = sorted((l for l in product_lots if l["so_luong_ton"] > 0), key=lambda l: l["ma_lo"])
        positions = {l["ma_lo"]: index for index, l in enumerate(active)}
        for lot in product_lots:
            key = lot["ma_lo"]
            yellow, red = groups[lot["ma_nhom"]]
            received = redate(lot["ngay_nhap"])
            sales = sale_days[key]
            if lot["so_luong_ton"] == 0:
                expiry = max(sales, default=received) + timedelta(days=1)
            else:
                bucket = positions[key] % 5
                if bucket == 0:
                    expiry = previous_month - timedelta(days=positions[key] % 7)
                elif bucket == 1:
                    expiry = today + timedelta(days=max(1, red))
                elif bucket == 2:
                    expiry = today + timedelta(days=yellow)
                elif lot["ma_nhom"] in {"NH03", "NH04"}:
                    month_offset = 1 if bucket == 3 else 3
                    absolute_month = today.year * 12 + today.month - 1 + month_offset
                    expiry = date(absolute_month // 12, absolute_month % 12 + 1, 15)
                    if (expiry - today).days <= yellow:
                        # Nhóm đồ hộp cần hơn 45 ngày: dùng mốc tháng 12,
                        # không tạo thêm một mốc tháng 11 nằm ngoài kịch bản.
                        absolute_month = today.year * 12 + today.month - 1 + 3
                        expiry = date(absolute_month // 12, absolute_month % 12 + 1, 15)
                        expiry = max(expiry, today + timedelta(days=yellow + 7))
                else:
                    extra = 4 if bucket == 3 else 9
                    expiry = today + timedelta(days=yellow + extra)
                # Không đổi ngày của hóa đơn người dùng đã bán thử.
                # Một lô vừa bán hôm nay không thể bị đẩy HSD về tháng trước.
                if sales:
                    expiry = max(expiry, max(sales) + timedelta(days=1))
            event_dates = sales + (other_events or {}).get(key, [])
            received = min([received, today, expiry - timedelta(days=1)] + event_dates)
            produced = min(redate(lot["ngay_san_xuat"]), received)
            lot_dates[key] = {"ngay_san_xuat": produced, "ngay_nhap": received, "han_su_dung": expiry}
    return lot_dates, invoice_dates


def refresh_csv_data(data, today):
    products = {p["ma_sp"]: p for p in data["san_pham"]}
    lots = {l["ma_lo"]: {**l, "ma_nhom": products[l["ma_sp"]]["ma_nhom"]} for l in data["lo_hang"]}
    invoices = {h["ma_hd"]: {**h, "seed": True} for h in data["hoa_don_ban"]}
    groups = {g["ma_nhom"]: (g["muc_canh_bao_vang"], g["muc_canh_bao_do"]) for g in data["nhom_hang"]}
    lot_dates, invoice_dates = calendar_plan(lots, invoices, data["chi_tiet_ban"], groups, today)
    for lot in data["lo_hang"]:
        lot.update(lot_dates[lot["ma_lo"]])
    for invoice in data["hoa_don_ban"]:
        invoice["thoi_gian_ban"] = invoice_dates[invoice["ma_hd"]]
    return data


def build_changes(db, template, today):
    seed_lots = {l["ma_lo"]: l["ma_sp"] for l in template["lo_hang"]}
    seed_invoices = {h["ma_hd"] for h in template["hoa_don_ban"]}
    products = {p.ma_sp: p for p in db.query(models.SanPham).all()}
    all_lots = db.query(models.LoHang).all()
    lots = {l.ma_lo: l for l in all_lots if seed_lots.get(l.ma_lo) == l.ma_sp}
    if not lots:
        raise ValueError("Không tìm thấy lô của bộ dữ liệu mẫu; không thay đổi CSDL.")
    details = [dict(r) for r in db.execute(select(models.ChiTietBan.ma_hd, models.ChiTietBan.ma_lo)).mappings()]
    # Hóa đơn liên quan lô ngoài bộ mẫu cũng phải giữ nguyên ngày.
    blocked_invoices = {d["ma_hd"] for d in details if d["ma_lo"] not in lots}
    invoices = {h.ma_hd: {"thoi_gian_ban": h.thoi_gian_ban, "seed": h.ma_hd in seed_invoices and h.ma_hd not in blocked_invoices}
                for h in db.query(models.HoaDonBan).all()}
    groups = {g.ma_nhom: (g.muc_canh_bao_vang, g.muc_canh_bao_do) for g in db.query(models.NhomHang).all()}
    events = defaultdict(list)
    for row in db.query(models.DieuChinhTon).all():
        events[row.ma_lo].append(row.thoi_gian.date())
    for row in db.query(models.XuLyRuiRo).all():
        events[row.ma_lo].append(row.thoi_gian.date())
    raw_lots = {key: {**{c.name: getattr(lot, c.name) for c in models.LoHang.__table__.columns},
                       "ma_nhom": products[lot.ma_sp].ma_nhom} for key, lot in lots.items()}
    lot_dates, invoice_dates = calendar_plan(raw_lots, invoices, details, groups, today, events)
    changes = []
    for key, after in lot_dates.items():
        before = {f: getattr(lots[key], f) for f in DATE_FIELDS}
        if before != after:
            changes.append({"table": "lo_hang", "key": key, "before": before, "after": after})
    for key, value in invoice_dates.items():
        old = invoices[key]["thoi_gian_ban"]
        if old != value:
            changes.append({"table": "hoa_don_ban", "key": key, "before": {"thoi_gian_ban": old}, "after": {"thoi_gian_ban": value}})
    return json.loads(json.dumps(changes, default=str))


def replay_changes(db, changes, restore=False):
    """Kiểm tra toàn bộ trước khi ghi; chạy lại không dịch lịch lần thứ hai."""
    types = {"lo_hang": models.LoHang, "hoa_don_ban": models.HoaDonBan}
    objects = {name: {getattr(row, "ma_lo" if name == "lo_hang" else "ma_hd"): row
                      for row in db.query(model).all()} for name, model in types.items()}
    source, target = ("after", "before") if restore else ("before", "after")
    prepared = []
    for change in changes:
        row = objects[change["table"]].get(change["key"])
        if row is None:
            raise ValueError("Dữ liệu đã thay đổi hoặc sai database; không thể áp dụng bản sao ngày.")
        current = {f: str(getattr(row, f)) for f in change[source]}
        if current == change[target]:
            continue
        if current != change[source]:
            raise ValueError(f"Ngày của {change['key']} đã được sửa sau bản sao. Không ghi đè.")
        prepared.append((row, change[target]))
    # Khôi phục chỉ được phép khi vẫn giữ đúng trình tự các giao dịch mới.
    # Ví dụ đã bán một lô sau cập nhật: không đưa HSD cũ về trước ngày bán đó.
    planned = {(change["table"], change["key"]): change[target] for change in changes}
    for detail in db.query(models.ChiTietBan).all():
        lot = objects["lo_hang"][detail.ma_lo]
        invoice = objects["hoa_don_ban"][detail.ma_hd]
        fields = planned.get(("lo_hang", detail.ma_lo), {})
        received = date.fromisoformat(fields["ngay_nhap"]) if "ngay_nhap" in fields else lot.ngay_nhap
        expiry = date.fromisoformat(fields["han_su_dung"]) if "han_su_dung" in fields else lot.han_su_dung
        stamp = planned.get(("hoa_don_ban", detail.ma_hd), {}).get("thoi_gian_ban")
        sold = datetime.fromisoformat(stamp).date() if stamp else invoice.thoi_gian_ban.date()
        if not received <= sold < expiry:
            raise ValueError(f"Không đổi ngày: lô {lot.ma_lo} có giao dịch không phù hợp lịch đích. Giữ nguyên dữ liệu.")
    for model in (models.DieuChinhTon, models.XuLyRuiRo):
        for event in db.query(model).all():
            fields = planned.get(("lo_hang", event.ma_lo), {})
            if "ngay_nhap" in fields and date.fromisoformat(fields["ngay_nhap"]) > event.thoi_gian.date():
                raise ValueError("Không đổi ngày: sẽ đặt ngày nhập sau lịch sử kiểm kê/xử lý.")
    for row, fields in prepared:
        for field, value in fields.items():
            setattr(row, field, datetime.fromisoformat(value) if field == "thoi_gian_ban" else date.fromisoformat(value))
    db.flush()
    return len(prepared)


def refresh_database(db, root, today, restore=False):
    from scripts.dataset_io import read_dataset
    backup = Path(root) / "backups/lich_du_lieu_truoc_cap_nhat.json"
    if backup.exists():
        payload = json.loads(backup.read_text(encoding="utf-8"))
    else:
        if restore:
            raise ValueError("Chưa có bản sao ngày cũ để khôi phục.")
        payload = {"ngay_cap_nhat": str(today), "changes": build_changes(db, read_dataset(Path(root) / "scripts/output"), today)}
        backup.parent.mkdir(parents=True, exist_ok=True)
        # Sao lưu trước khi commit. Nếu transaction lỗi, lần sau dùng lại kế hoạch này.
        with backup.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
    count = replay_changes(db, payload["changes"], restore)
    return count, backup
