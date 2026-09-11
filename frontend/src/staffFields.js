// Tiện ích riêng cho kiểm kê của nhân viên; không đổi mã trong CSDL.
export function countLotLabel(lot) {
  const date = (value) => {
    if (!value) return "chưa có ngày";
    const [year, month, day] = value.slice(0, 10).split("-");
    return `${Number(day)}/${Number(month)}/${year}`;
  };
  return `Lô nhập ngày ${date(lot.ngay_nhap)} · HSD ${date(lot.han_su_dung)}`;
}

export const canCountLot = (lot) =>
  Boolean(lot) && !["ChoXuatHuy", "DaXuatHuy"].includes(lot.trang_thai);

export function visibleCountLots(lots, showEmpty) {
  return lots
    .filter((lot) => showEmpty || lot.so_luong_ton > 0)
    .sort(
      (a, b) =>
        Number(canCountLot(b)) - Number(canCountLot(a)) ||
        Number(b.so_luong_ton > 0) - Number(a.so_luong_ton > 0) ||
        a.han_su_dung.localeCompare(b.han_su_dung) ||
        a.ma_lo.localeCompare(b.ma_lo),
    );
}

export async function loadProductLots(api, product, isCurrent = () => true) {
  const items = [];
  // API giới hạn 200 lô/trang. Lấy tiếp để không bỏ sót lô còn hàng ở trang sau.
  for (let page = 1; ; page += 1) {
    const data = await api(
      `/lo-hang?ma_sp=${encodeURIComponent(product)}&chi_con_hang=false&page_size=200&page=${page}`,
    );
    if (!isCurrent()) return [];
    if (data.items.some((lot) => lot.ma_sp !== product)) {
      throw new Error("Dữ liệu lô không đúng sản phẩm. Vui lòng tải lại.");
    }
    items.push(...data.items);
    if (items.length >= data.total) return items;
    if (!data.items.length)
      throw new Error("Danh sách lô vừa thay đổi. Vui lòng tải lại.");
  }
}
