"""Thuật toán thuần Python: API, phân tích CSV và kiểm thử dùng chung một bản.

Giả định tốc độ bán ổn định, không nhập thêm, bán đúng FEFO. Đây là ước tính
hỗ trợ quyết định, không phải mô hình ML đã được kiểm chứng bằng dữ liệu thật.
"""

from decimal import Decimal, ROUND_FLOOR


def allocate_fefo(lots, daily_rate, today):
    """Chia MỘT năng lực tiêu thụ của SKU cho các lô theo từng mốc hết hạn.

    Công suất đến hạn của lô = floor(tốc độ * số ngày). Trừ phần đã phân bổ
    cho lô trước rồi chặn trong [0, tồn]. Hàng dư của lô trước không chiếm công
    suất sau khi lô đó hết hạn. Lô chờ hủy không được phân bổ công suất bán.
    """
    allocated, result = 0, {}
    for lot in sorted(
        lots, key=lambda x: (x["han_su_dung"], x["ngay_nhap"], x["ma_lo"])
    ):
        days = (lot["han_su_dung"] - today).days
        stock = lot["so_luong_ton"]
        if days <= 0 or lot["trang_thai"] == "ChoXuatHuy":
            expected, surplus = 0, stock
        elif daily_rate is None:
            expected, surplus = None, None
        else:
            capacity = int(
                (daily_rate * Decimal(days)).to_integral_value(rounding=ROUND_FLOOR)
            )
            expected = min(stock, max(0, capacity - allocated))
            surplus = stock - expected
            allocated += expected
        result[lot["ma_lo"]] = (expected, surplus)
    return result


def classify_risk(days, surplus, yellow, red, pending=False):
    if days <= 0:
        return "Do", "Đã đến/quá hạn sử dụng; không được bán."
    if pending:
        return "Do", "Đang chờ nhân viên xuất hủy; đã chặn bán."
    if days <= red:
        return "Do", "Số ngày còn lại đã chạm ngưỡng Đỏ."
    if days <= yellow:
        return "Vang", "Số ngày còn lại đã chạm ngưỡng Vàng."
    if surplus is None:
        return (
            "Vang",
            "Chưa có giao dịch trong cửa sổ quan sát; chưa đủ dữ liệu để ước tính.",
        )
    if surplus > 0:
        return (
            "Vang",
            "Có nguy cơ còn hàng khi đến hạn sử dụng vì lượng tồn lớn hơn lượng dự kiến bán được.",
        )
    return "Xanh", "Ước tính bán hết trước hạn theo giả định hiện tại."
