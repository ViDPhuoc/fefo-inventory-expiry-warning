import test from "node:test";
import assert from "node:assert/strict";
import {
  canCountLot,
  visibleCountLots,
  loadProductLots,
} from "../src/staffFields.js";

const batch = (
  ma_lo,
  so_luong_ton,
  han_su_dung,
  trang_thai = "DangGiaoDich",
) => ({ ma_lo, ma_sp: "SP1", so_luong_ton, han_su_dung, trang_thai });

test("Không mặc định chọn lô tồn 0 hoặc lô chờ hủy; vẫn truy cập được lô 0 để kiểm kê", () => {
  const lots = [
    batch("empty", 0, "2026-09-01", "DaBanHet"),
    batch("later", 10, "2026-10-01"),
    batch("pending", 5, "2026-09-02", "ChoXuatHuy"),
    batch("first", 10, "2026-09-18"),
  ];
  assert.deepEqual(
    visibleCountLots(lots, false).map((l) => l.ma_lo),
    ["first", "later", "pending"],
  );
  assert.deepEqual(
    visibleCountLots(lots, true).map((l) => l.ma_lo),
    ["first", "later", "empty", "pending"],
  );
  assert.equal(canCountLot(lots[0]), true);
  assert.equal(canCountLot(lots[2]), false);
  assert.equal(
    canCountLot(batch("discard", 0, "2026-09-01", "DaXuatHuy")),
    false,
  );
});

test("Lấy được lô còn hàng ở trang 2 sau 200 lô tồn 0", async () => {
  const history = Array.from({ length: 200 }, (_, i) =>
    batch(`old${i}`, 0, "2026-09-01"),
  );
  const requests = [];
  const items = await loadProductLots(async (path) => {
    requests.push(path);
    return {
      total: 201,
      items: path.endsWith("page=1")
        ? history
        : [batch("saleable", 20, "2026-10-01")],
    };
  }, "SP1");
  assert.equal(requests.length, 2);
  assert.deepEqual(
    visibleCountLots(items, false).map((l) => l.ma_lo),
    ["saleable"],
  );
});

test("Từ chối dữ liệu lô thuộc sản phẩm khác", async () => {
  await assert.rejects(
    loadProductLots(
      async () => ({ total: 1, items: [batch("wrong", 10, "2026-10-01")] }),
      "SP2",
    ),
    /không đúng sản phẩm/,
  );
});

test("Bỏ kết quả tải cũ sau khi chuyển sản phẩm, không gọi tiếp trang sau", async () => {
  let count = 0;
  const items = await loadProductLots(
    async () => {
      count += 1;
      return { total: 201, items: [batch("old", 0, "2026-09-01")] };
    },
    "SP1",
    () => false,
  );
  assert.deepEqual(items, []);
  assert.equal(count, 1);
});

test("API không trả đủ danh sách phải báo lỗi, không coi phần thiếu là hết hàng", async () => {
  await assert.rejects(
    loadProductLots(async () => ({ total: 1, items: [] }), "SP1"),
    /Vui lòng tải lại/,
  );
});
