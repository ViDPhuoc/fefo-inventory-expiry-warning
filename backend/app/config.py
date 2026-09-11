"""Cấu hình tập trung: đổi môi trường mà không sửa nghiệp vụ."""

import os
from pathlib import Path
from datetime import date, datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/canhbao_hethan_demo"
)
LOCAL_ZONE = ZoneInfo("Asia/Ho_Chi_Minh")


def business_today() -> date:
    """APP_TODAY chỉ dùng đóng băng ngày demo/test; mặc định theo ngày Việt Nam."""
    fixed = os.getenv("APP_TODAY")
    return date.fromisoformat(fixed) if fixed else datetime.now(LOCAL_ZONE).date()


def business_now() -> datetime:
    # PostgreSQL TIMESTAMP không múi giờ: toàn ứng dụng cùng quy ước giờ Việt Nam.
    now = datetime.now(LOCAL_ZONE).replace(tzinfo=None)
    return datetime.combine(business_today(), now.time())
