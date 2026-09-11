# Kiểm thử

## Các nhóm đã có test tự động

- Kiểm tra số lượng bằng 0, âm, sai kiểu và bán quá tồn.
- Chặn bán lô hết hạn hoặc lô đang chờ xuất hủy.
- Phân bổ nhiều lô theo FEFO và rollback giao dịch không hoàn chỉnh.
- Tính tốc độ theo SKU, lượng có thể bán và lượng tồn có nguy cơ.
- Phân quyền Manager và Staff.
- Nhập lô, kiểm kê, lưu lịch sử điều chỉnh tồn.
- Duyệt, thực hiện và hủy lệnh giảm giá hoặc xuất hủy.
- Kiểm tra khoảng ngày báo cáo và ngưỡng cảnh báo.
- Kiểm tra tính hợp lệ của bộ dữ liệu mô phỏng.
- Kiểm tra các trường hiển thị bán hàng phía frontend.

## Cách chạy

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
```

Frontend:

```powershell
Set-Location frontend
npm ci
node --test tests/*.test.js
npm run build
```

Backend test mặc định dùng SQLite biệt lập để chạy nhanh và không sửa dữ liệu
local. Có thể đặt `TEST_DATABASE_URL` trỏ tới một database PostgreSQL test
riêng để kiểm tra trên PostgreSQL.

## Chưa được bao phủ đầy đủ

- Thao tác end-to-end trên nhiều trình duyệt.
- Tải đồng thời lớn, deadlock và chiến lược retry.
- Migration từ database cũ.
- Bảo mật và triển khai production.
- Độ chính xác dự báo trên dữ liệu bán lẻ thực.

Các giới hạn này cần được đánh giá trước khi dùng hệ thống ngoài môi trường
trình diễn hoặc học tập.
