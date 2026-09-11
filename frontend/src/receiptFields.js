// Tính bằng ngày lịch UTC để không lệch một ngày do múi giờ máy người dùng.
export function suggestedExpiry(manufactured, days) {
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(manufactured) ||
    !Number.isInteger(days) ||
    days < 1
  )
    return "";
  const value = new Date(`${manufactured}T00:00:00Z`);
  if (
    Number.isNaN(value.getTime()) ||
    value.toISOString().slice(0, 10) !== manufactured
  )
    return "";
  value.setUTCDate(value.getUTCDate() + days);
  return value.toISOString().slice(0, 10);
}

export function updateReceipt(form, key, value, settings) {
  const next = { ...form, [key]: value };
  if (["ma_sp", "ngay_san_xuat"].includes(key)) {
    next.han_su_dung = suggestedExpiry(
      next.ngay_san_xuat,
      settings[next.ma_sp],
    );
  }
  return next;
}
