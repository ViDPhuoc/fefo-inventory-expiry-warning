"""HSD gợi ý riêng từng SKU. Không sửa ngưỡng cảnh báo hay ngày của lô đã có."""

import json
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "data/han_su_dung_goi_y.json"


def shelf_life_settings():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    result = {}
    for code, item in data["san_pham"].items():
        days = item["so_ngay"]
        if type(days) is not int or not 1 <= days <= 3650:
            raise ValueError(f"HSD gợi ý của {code} phải từ 1 đến 3650 ngày.")
        result[code] = days
    return result
