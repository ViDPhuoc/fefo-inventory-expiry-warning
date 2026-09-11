"""Chạy riêng: python scripts/generate_mock_data.py --so_san_pham 120 --so_ngay_lich_su 180."""

import argparse
from datetime import date
from pathlib import Path
from mock_dataset import build_dataset
from dataset_io import write_dataset, validate_dataset

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--so_san_pham", type=int, default=120)
    parser.add_argument("--so_ngay_lich_su", type=int, default=180)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    data = build_dataset(args.as_of, args.so_san_pham, args.so_ngay_lich_su, args.seed)
    print(validate_dataset(data, args.as_of))
    write_dataset(data, Path(__file__).parent / "output", args.as_of, args.seed)
    print(
        "Đã sinh dữ liệu hợp lệ. Đây là dữ liệu mô phỏng, không phải dữ liệu khảo sát cửa hàng thật."
    )
