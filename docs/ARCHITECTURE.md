# Kiến trúc hệ thống

## Luồng xử lý

1. React gửi request tới FastAPI.
2. Router xác thực người dùng và kiểm tra dữ liệu đầu vào bằng Pydantic.
3. Service áp dụng quy tắc nghiệp vụ trong một transaction.
4. SQLAlchemy đọc hoặc cập nhật PostgreSQL.
5. API trả kết quả để giao diện cập nhật trạng thái.

## Backend

| Thành phần | Trách nhiệm |
| --- | --- |
| `app/main.py` | Khởi tạo FastAPI, middleware, router và phục vụ React build |
| `app/config.py` | Đọc biến môi trường và cung cấp ngày nghiệp vụ |
| `app/database.py` | Quản lý engine, session, commit và rollback |
| `app/models.py` | Định nghĩa bảng, quan hệ, ràng buộc và index |
| `app/schemas.py` | Kiểm tra kiểu dữ liệu và giới hạn request |
| `app/security.py` | Xác thực Basic Auth và kiểm tra vai trò |
| `app/routers/` | Định nghĩa endpoint và response HTTP |
| `app/services/` | Xử lý kho, bán hàng, cảnh báo, dự báo và báo cáo |

Nghiệp vụ bán hàng khóa và duyệt các lô theo thứ tự FEFO. Một hóa đơn chỉ được
commit khi toàn bộ số lượng có thể phân bổ; nếu có lỗi, transaction được
rollback để tránh trừ tồn một phần.

## Frontend

| Thành phần | Trách nhiệm |
| --- | --- |
| `src/App.jsx` | Điều hướng và phiên đăng nhập trong bộ nhớ |
| `src/api.js` | Gọi API, gửi thông tin xác thực và chuẩn hóa lỗi |
| `src/pages/` | Dashboard, vận hành, quy tắc, xử lý và báo cáo |
| `src/components/` | Form, modal, phân trang và thành phần dùng chung |
| `src/hooks/` | Trạng thái loading, error và dữ liệu bất đồng bộ |

## Dữ liệu

`scripts/mock_dataset.py` sinh bộ dữ liệu có thể tái lập bằng seed.
`scripts/dataset_io.py` kiểm tra khóa chính, khóa ngoại, ngày và cân đối tồn
trước khi ghi CSV hoặc nạp database. `database/schema.sql` thể hiện schema
PostgreSQL tương ứng với model.

## Quy tắc cảnh báo

- **Đỏ:** lô đã hết hạn, chờ xuất hủy hoặc chạm ngưỡng đỏ.
- **Vàng:** lô chạm ngưỡng vàng, thiếu lịch sử bán hoặc được ước lượng còn dư.
- **Xanh:** các trường hợp còn lại.

Tốc độ bán được tính một lần cho mỗi SKU trong cửa sổ lịch sử. Khả năng bán
được phân bổ lần lượt cho các lô theo hạn sử dụng, tránh nhân đôi nhu cầu khi
một sản phẩm có nhiều lô.

## Quyết định thiết kế

- Dùng `Decimal` và kiểu `NUMERIC` cho tiền.
- Dùng UUID cho mã nghiệp vụ để tránh cách sinh mã bằng `COUNT + 1`.
- Lưu người thực hiện và thời điểm cho điều chỉnh tồn cùng lệnh xử lý.
- Duyệt và thực hiện xuất hủy ở hai bước; lô bị chặn bán từ lúc chờ xử lý.
- Giữ công thức dự báo trong service thuần để API, script phân tích và test dùng
  chung một cách tính.
