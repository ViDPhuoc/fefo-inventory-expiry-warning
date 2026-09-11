"""Xuất DDL PostgreSQL từ chính ORM, tránh lệch CHECK/index giữa hai nơi."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.database import Base
from app import models
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from dataset_io import read_dataset, ORDER

if __name__ == "__main__":
    dialect = postgresql.dialect()
    statements = [
        "-- PostgreSQL. Xuất từ backend/app/models.py. Dùng database demo mới.",
        "-- Không DROP bảng hoặc dữ liệu cũ. Tạo bảng có sẵn sẽ báo lỗi.",
    ]
    for table in Base.metadata.sorted_tables:
        statements.append(str(CreateTable(table).compile(dialect=dialect)) + ";")
        for index in sorted(table.indexes, key=lambda i: i.name):
            statements.append(str(CreateIndex(index).compile(dialect=dialect)) + ";")
    (ROOT / "database/schema.sql").write_text("\n\n".join(statements), encoding="utf-8")
    data = read_dataset(ROOT / "scripts/output")
    lines = [
        "-- Chạy từ thư mục scripts/. Database phải trống và đã có schema.",
        r"\set ON_ERROR_STOP on",
        "BEGIN;",
    ]
    for table in ORDER:
        columns = ",".join(data[table][0])
        lines.append(
            rf"\copy {table} ({columns}) FROM 'output/{table}.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');"
        )
    lines += [
        "SELECT setval(pg_get_serial_sequence('chi_tiet_ban','ma_ct'), COALESCE(MAX(ma_ct),1), COUNT(*) > 0) FROM chi_tiet_ban;",
        "COMMIT;",
    ]
    (ROOT / "scripts/load_to_postgres.sql").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("Đã xuất schema và COPY với danh sách cột khớp CSV.")
