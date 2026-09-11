"""Lệnh quản lý local. Không tự xóa CSDL khi khởi động web server."""

import argparse
import sys
from pathlib import Path
from sqlalchemy import text
from app import models
from app.database import Base, engine, SessionLocal
from app.config import business_today

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.mock_dataset import build_dataset
from scripts.dataset_io import read_dataset, validate_dataset, write_dataset, ORDER
from scripts.product_catalog import update_catalog


def insert_dataset(db, data, reset=False):
    if not reset and any(
        db.execute(text(f"SELECT 1 FROM {name} LIMIT 1")).first() for name in ORDER
    ):
        raise ValueError(
            "CSDL đã có dữ liệu. Dùng database demo mới; --reset-demo sẽ xóa dữ liệu hiện có nếu bạn chủ động chọn."
        )
    if reset:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
    for name in ORDER:
        db.execute(Base.metadata.tables[name].insert(), data[name])
    if db.bind.dialect.name == "postgresql":
        # COPY/bulk insert có ma_ct tường minh: cập nhật sequence để giao dịch sau không trùng.
        for table, col in [
            ("chi_tiet_ban", "ma_ct"),
            ("dieu_chinh_ton", "ma_dc"),
            ("xu_ly_rui_ro", "ma_xl"),
        ]:
            db.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table}','{col}'), COALESCE(MAX({col}),1), COUNT(*) > 0) FROM {table}"
                )
            )


def main():
    parser = argparse.ArgumentParser(
        description="Cảnh báo hết hạn — chuẩn bị dữ liệu demo"
    )
    parser.add_argument(
        "command", choices=["init-db", "ensure-demo", "seed-demo", "import-csv", "update-catalog", "add-presentation", "refresh-calendar", "restore-calendar"]
    )
    parser.add_argument("--products", type=int, default=120)
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--reset-demo",
        action="store_true",
        help="Xóa dữ liệu trong DATABASE_URL trước khi nạp; chỉ dùng DB demo.",
    )
    args = parser.parse_args()
    if args.command in {"refresh-calendar", "restore-calendar"}:
        from scripts.refresh_calendar import refresh_database
        from app.services.alert_service import get_dashboard_data, summarize
        restoring = args.command == "restore-calendar"
        with SessionLocal.begin() as db:
            count, backup = refresh_database(db, ROOT, business_today(), restore=restoring)
            report = summarize(get_dashboard_data(db))
        print("Đã khôi phục ngày cũ." if restoring else "Đã cập nhật lịch dữ liệu mẫu.")
        print("Số dòng đổi ngày:", count)
        print("Bản sao ngày cũ:", backup)
        print("Ngày hệ thống:", business_today())
        print("Số lô quá hạn:", report["lo_da_het_han"])
        print("Số lô Đỏ / Vàng / Xanh:", report["so_luong_theo_muc"])
        print("Giữ nguyên số lượng, mã, giá, tài khoản và kết quả xử lý/kiểm kê.")
        return
    if args.command == "add-presentation":
        import json
        from scripts.presentation_data import add_presentation_data, presentation_summary
        # Lệnh chủ động riêng, không tự thêm dữ liệu mỗi lần mở website.
        with SessionLocal.begin() as db:
            result = add_presentation_data(db, business_today())
            report = presentation_summary(db)
            if result["da_them"] and report["thong_ke"]["so_luong_theo_muc"] != {"Do": 5, "Vang": 5, "Xanh": 5}:
                raise ValueError("Chưa tạo được đủ 5 đỏ / 5 vàng / 5 xanh; đã hoàn tác lần bổ sung.")
        print("Đã thêm bộ mô phỏng." if result["da_them"] else result["ghi_chu"])
        print("Ngày nghiệp vụ:", business_today())
        print("Số lô hiện tại của bộ bổ sung:", report["thong_ke"]["so_luong_theo_muc"])
        print("Trên Manager: xóa bộ lọc nhóm/màu cũ, tìm LOBS để xem riêng 15 lô.")
        print("Các số đếm là của bộ bổ sung, không phải toàn bộ dữ liệu cũ.")
        payload = {"ngay_tinh": business_today(), **result, **report}
        try:
            (ROOT / "KET_QUA_BO_SUNG.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        except OSError:
            print("Dữ liệu đã lưu; không ghi được báo cáo ra file. Xem kết quả ở trên.")
        return
    Base.metadata.create_all(engine)
    if args.command == "update-catalog":
        with SessionLocal.begin() as db:
            changed = update_catalog(db)
        print(f"Đã cập nhật {changed} tên sản phẩm. Giữ nguyên tồn kho và giao dịch.")
        return
    if args.command == "init-db":
        print(
            "Đã tạo bảng nếu chưa có. Không thay cấu trúc bảng cũ; bản này cần DB demo mới."
        )
        return
    if args.command == "ensure-demo":
        # File CHAY_DEMO_WINDOWS.bat có thể chạy nhiều lần: chỉ seed khi DB hoàn toàn
        # trống, tuyệt đối không reset ngầm hay xóa giao dịch mà người dùng đã thử.
        with SessionLocal() as db:
            table_counts = {
                name: db.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
                for name in ORDER
            }
        if all(value > 0 for value in table_counts.values()):
            with SessionLocal.begin() as db:
                changed = update_catalog(db)
            print(f"Đã cập nhật {changed} tên hàng theo danh mục mới.")
            print("CSDL demo đã có dữ liệu; giữ nguyên và không seed lại.")
            print("Tài khoản local demo: manager1 / staff1; mật khẩu chung: Demo@2026")
            return
        if any(value > 0 for value in table_counts.values()):
            raise ValueError(
                f"CSDL đang có dữ liệu chưa đầy đủ: {table_counts}. "
                "Không tự xóa; hãy kiểm tra dữ liệu trước khi tiếp tục."
            )
        data = build_dataset(business_today(), args.products, args.days, args.seed)
        counts = validate_dataset(data, business_today())
        with SessionLocal.begin() as db:
            insert_dataset(db, data)
        write_dataset(
            data,
            ROOT / "scripts/output",
            business_today(),
            args.seed,
        )
        print("Đã nạp trong một transaction:", counts)
        print("Tài khoản local demo: manager1 / staff1; mật khẩu chung: Demo@2026")
        return
    as_of = business_today()
    directory = ROOT / "scripts/output"
    data = (
        build_dataset(as_of, args.products, args.days, args.seed)
        if args.command == "seed-demo"
        else read_dataset(directory)
    )
    counts = validate_dataset(data, as_of)
    with SessionLocal.begin() as db:
        insert_dataset(db, data, args.reset_demo)
    if args.command == "seed-demo":
        write_dataset(data, directory, as_of, args.seed)
    print("Đã nạp trong một transaction:", counts)
    print("Tài khoản local demo: manager1 / staff1; mật khẩu chung: Demo@2026")
    print("Ngày nghiệp vụ:", as_of)


if __name__ == "__main__":
    main()
