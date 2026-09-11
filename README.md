# FEFO Inventory Expiry Warning

Ứng dụng web quản lý tồn kho theo lô, ưu tiên xuất hàng theo FEFO và cảnh báo
nguy cơ tồn dư trước hạn sử dụng. Dự án mô phỏng quy trình của một cửa hàng bán
lẻ với hai vai trò: **Manager** và **Staff**.

## Chức năng chính

- Theo dõi sản phẩm, lô hàng, ngày nhập, ngày sản xuất và hạn sử dụng.
- Phân loại lô theo ba mức cảnh báo Đỏ, Vàng và Xanh.
- Bán hàng theo FEFO, chặn bán lô hết hạn và rollback khi không đủ tồn.
- Nhập lô, kiểm kê và lưu lịch sử điều chỉnh tồn kho.
- Duyệt và thực hiện giảm giá hoặc xuất hủy theo hai bước.
- Báo cáo doanh thu, sản phẩm bán chạy và giá trị hàng đã xuất hủy.
- Tính tốc độ bán trung bình theo SKU và ước lượng lượng tồn có nguy cơ còn lại.

## Công nghệ

| Thành phần | Công nghệ |
| --- | --- |
| Backend | Python, FastAPI, SQLAlchemy |
| Database | PostgreSQL |
| Frontend | React, Vite |
| Phân tích dữ liệu | Pandas |
| Kiểm thử | Pytest, Node test runner |
| Đóng gói | Docker Compose |

## Kiến trúc

```text
React UI -> FastAPI router -> service nghiệp vụ -> SQLAlchemy -> PostgreSQL
```

Router xử lý hợp đồng HTTP; service giữ quy tắc nghiệp vụ và transaction; model
định nghĩa quan hệ cùng ràng buộc dữ liệu. Chi tiết nằm trong
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Chạy nhanh bằng Docker

Yêu cầu: Docker Desktop hoặc Docker Engine có Docker Compose.

```bash
docker compose up --build
```

Mở <http://localhost:8000>. Lệnh trên tạo database, build React và chỉ nạp dữ
liệu mẫu khi database đang trống.

## Chạy trực tiếp trên Windows

Yêu cầu:

- Python 3.11 trở lên;
- Node.js 22;
- PostgreSQL 16 và lệnh `psql` có trong `PATH`.

Nhấp đúp `CHAY_DEMO_WINDOWS.bat`, sau đó nhập tài khoản PostgreSQL trên máy.
Script sẽ tạo môi trường Python, build frontend khi cần, tạo database và mở
<http://localhost:8000>.

## Tài khoản mẫu

| Vai trò | Tên đăng nhập | Mật khẩu |
| --- | --- | --- |
| Manager | `manager1` | `Demo@2026` |
| Staff | `staff1` | `Demo@2026` |

Đây là tài khoản của dữ liệu mô phỏng dùng trên localhost. Không sử dụng các
thông tin này khi triển khai công khai.

## Chạy kiểm thử

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

Phạm vi và giới hạn kiểm thử được ghi tại
[`docs/TESTING.md`](docs/TESTING.md).

## Dữ liệu và giới hạn

Dữ liệu mẫu được sinh cố định bằng seed, gồm 120 sản phẩm và lịch sử giao dịch
mô phỏng. Phần ước lượng dùng tốc độ bán trung bình và phân bổ FEFO; đây không
phải mô hình machine learning và chưa được đánh giá bằng dữ liệu bán lẻ thực.

Xác thực Basic Auth, tài khoản mẫu và cấu hình database mặc định chỉ phục vụ
môi trường local. Dự án chưa bao gồm migration, thông báo nền, tích hợp POS,
thanh toán hoặc triển khai production.

## Cấu trúc thư mục

```text
backend/    API, model, service và kiểm thử
frontend/   giao diện React và kiểm thử giao diện
database/   PostgreSQL schema
scripts/    sinh dữ liệu, phân tích và công cụ khởi động
docs/       kiến trúc và phạm vi kiểm thử
```

## Tác giả

Võ Duy Phước — [GitHub](https://github.com/ViDPhuoc)
