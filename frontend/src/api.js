// Điểm gọi API duy nhất: thông báo lỗi có nghĩa, không giấu lỗi thành dữ liệu rỗng.
export function createApi(credentials) {
  return async function api(path, options = {}) {
    const response = await fetch(`/api${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(credentials ? { Authorization: `Basic ${credentials}` } : {}),
        ...options.headers,
      },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const fields = body.errors
        ?.map((e) => `${e.field}: ${e.message}`)
        .join("; ");
      throw new Error(
        fields || body.detail || `Yêu cầu thất bại (${response.status}).`,
      );
    }
    return body;
  };
}
export const jsonBody = (value) => JSON.stringify(value);
export const number = (value) =>
  value == null
    ? "Chưa đủ dữ liệu"
    : new Intl.NumberFormat("vi-VN").format(value);
export const money = (value) => `${number(value)} ₫`;
// Chỉ làm tròn khi hiển thị; không thay tốc độ dùng trong công thức dự báo.
export const dailyRate = (value) => value == null ? "—" :
  new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 1 }).format(value);
export const dateVN = (value) =>
  value
    ? new Date(`${String(value).slice(0, 10)}T00:00:00`).toLocaleDateString(
        "vi-VN",
      )
    : "—";
export const riskLabel = { Do: "Báo động", Vang: "Cần chú ý", Xanh: "An toàn" };
export const stateLabel = {
  DangGiaoDich: "Đang lưu kho",
  DaBanHet: "Đã bán hết",
  ChoXuatHuy: "Chờ xuất hủy",
  DaXuatHuy: "Đã xuất hủy",
  ChoXuLy: "Chờ thực hiện",
  DaHoanTat: "Đã hoàn tất",
  DaHuyLenh: "Đã hủy lệnh",
};
