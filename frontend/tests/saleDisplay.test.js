import test from "node:test";
import assert from "node:assert/strict";
import { sortSaleProducts } from "../src/saleDisplay.js";

const products = (names) =>
  names.map((ten_sp, i) => ({ ten_sp, ma_sp: `P${i}` }));
const names = (items) => items.map((p) => p.ten_sp);

test("Cùng loại sắp lượng nhỏ trước lớn, quy đổi kg/g và lít/ml", () => {
  const items = products([
    "Sữa tươi nguyên kem — 1 lít",
    "Rau cải — 1 kg",
    "Rau cải — 500 g",
    "Rau cải — 200 g",
    "Sữa tươi nguyên kem 180 ml",
    "Sữa tươi nguyên kem — 200 ml",
    "Sữa tươi nguyên kem — 1,5 lít",
  ]);
  const before = names(items);
  assert.deepEqual(names(sortSaleProducts(items)), [
    "Rau cải — 200 g",
    "Rau cải — 500 g",
    "Rau cải — 1 kg",
    "Sữa tươi nguyên kem 180 ml",
    "Sữa tươi nguyên kem — 200 ml",
    "Sữa tươi nguyên kem — 1 lít",
    "Sữa tươi nguyên kem — 1,5 lít",
  ]);
  assert.deepEqual(names(items), before);
});

test("Gói nhỏ, vừa, lớn và số phần có thứ tự dễ tìm", () => {
  const items = products([
    "Bánh mì sandwich — gói lớn",
    "Bánh mì sandwich — gói vừa",
    "Bánh mì sandwich — gói nhỏ",
  ]);
  assert.deepEqual(names(sortSaleProducts(items)), [...names(items)].reverse());
  assert.deepEqual(
    names(
      sortSaleProducts(
        products(["Bánh bao — hộp 10 phần", "Bánh bao — hộp 2 phần"]),
      ),
    ),
    ["Bánh bao — hộp 2 phần", "Bánh bao — hộp 10 phần"],
  );
});

test("Hóa đơn render giá gốc và giảm đúng từng lô, không lộ mã HD/DEMO", async () => {
  const { createServer } = await import("vite");
  const React = await import("react");
  const { renderToStaticMarkup } = await import("react-dom/server");
  const server = await createServer({
    server: { middlewareMode: true },
    appType: "custom",
  });
  try {
    const { default: Receipt } = await server.ssrLoadModule(
      "/src/components/SaleReceipt.jsx",
    );
    const html = renderToStaticMarkup(
      React.createElement(Receipt, {
        result: {
          ma_hd: "HDdc010a514c3d4368a94ce8b7ce264c21",
          ten_sp: "Rau cải — 500 g",
          tong_tien: 20400,
          cac_lo_da_tru: [
            {
              ma_lo: "DEMO_A",
              gia_goc: 12000,
              don_gia: 8400,
              ty_le_giam: 30,
              so_luong_tru: 1,
              han_su_dung: "2026-09-20",
            },
            {
              ma_lo: "DEMO_B",
              gia_goc: 12000,
              don_gia: 12000,
              ty_le_giam: 0,
              so_luong_tru: 1,
              han_su_dung: "2026-09-30",
            },
          ],
        },
      }),
    );
    assert.ok(html.includes("Giá gốc: 12.000 ₫"));
    assert.ok(html.includes("Giảm 30%"));
    assert.ok(html.includes("Giá bán: 8.400 ₫"));
    assert.ok(html.includes("Không giảm giá"));
    assert.ok(html.includes("20.400 ₫"));
    assert.ok(!html.includes("HDdc010") && !html.includes("DEMO_"));
  } finally {
    await server.close();
  }
});
