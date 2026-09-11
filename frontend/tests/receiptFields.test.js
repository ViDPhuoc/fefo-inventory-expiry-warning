import test from "node:test";
import assert from "node:assert/strict";
import { suggestedExpiry, updateReceipt } from "../src/receiptFields.js";
import { countLotLabel } from "../src/staffFields.js";

test("HSD sữa tự chuyển tháng, qua năm và năm nhuận đúng ngày lịch", () => {
  assert.equal(suggestedExpiry("2026-09-11", 30), "2026-10-11");
  assert.equal(suggestedExpiry("2026-12-30", 7), "2027-01-06");
  assert.equal(suggestedExpiry("2028-02-28", 2), "2028-03-01");
  assert.equal(suggestedExpiry("2026-02-30", 30), "");
  assert.equal(suggestedExpiry("2026-09-11", undefined), "");
});

test("Chuyển SKU/NSX tính lại HSD; sửa tay và số lượng không làm mất HSD đã nhập", () => {
  const config = { MILK: 30, BREAD: 7 };
  const form = {
    ma_sp: "MILK",
    ngay_san_xuat: "2026-09-11",
    han_su_dung: "2026-10-11",
    so_luong_nhap: 10,
  };
  const bread = updateReceipt(form, "ma_sp", "BREAD", config);
  assert.equal(bread.han_su_dung, "2026-09-18");
  assert.equal(
    updateReceipt(bread, "ngay_san_xuat", "2026-09-10", config).han_su_dung,
    "2026-09-17",
  );
  const manual = updateReceipt(bread, "han_su_dung", "2026-09-20", config);
  assert.equal(
    updateReceipt(manual, "so_luong_nhap", 20, config).han_su_dung,
    "2026-09-20",
  );
  assert.equal(
    updateReceipt(manual, "ma_sp", "UNKNOWN", config).han_su_dung,
    "",
  );
  assert.equal(form.han_su_dung, "2026-10-11");
});

test("Nhãn kiểm kê dùng ngày nhập thật và HSD, không dùng số thứ tự lô", () => {
  assert.equal(
    countLotLabel({
      ma_lo: "DEMO_X",
      ngay_nhap: "2026-08-01",
      han_su_dung: "2026-08-31",
    }),
    "Lô nhập ngày 1/8/2026 · HSD 31/8/2026",
  );
});
