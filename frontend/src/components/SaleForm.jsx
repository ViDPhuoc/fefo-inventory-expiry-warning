import { useEffect, useMemo, useRef, useState } from "react";
import { jsonBody } from "../api";
import { sortSaleProducts } from "../saleDisplay";
import { Notice } from "./Shared";
import SaleReceipt from "./SaleReceipt";
import "../sale.css";

export default function SaleForm({ api, products }) {
  const [lookedUp, setLookedUp] = useState(null);
  const sortedProducts = useMemo(
    () =>
      sortSaleProducts(
        lookedUp && !products.some((p) => p.ma_sp === lookedUp.ma_sp)
          ? [...products, lookedUp]
          : products,
      ),
    [products, lookedUp],
  );
  const [productId, setProductId] = useState(
    () => sortSaleProducts(products)[0]?.ma_sp || "",
  );
  const [qty, setQty] = useState(1),
    [code, setCode] = useState("");
  const [error, setError] = useState(""),
    [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false),
    [looking, setLooking] = useState(false);
  const requestId = useRef(0);
  useEffect(
    () => () => {
      requestId.current += 1;
    },
    [],
  );
  const product =
    lookedUp?.ma_sp === productId
      ? lookedUp
      : products.find((p) => p.ma_sp === productId);

  function selectProduct(id) {
    requestId.current += 1;
    setLooking(false);
    setProductId(id);
    setCode("");
    setQty(1);
    setError("");
    setResult(null);
  }
  function changeCode(value) {
    // Gõ mã mới hủy lựa chọn cũ ngay, tránh nhấn bán nhầm mặt hàng trước đó.
    requestId.current += 1;
    setLooking(false);
    setCode(value);
    setProductId("");
    setQty(1);
    setError("");
    setResult(null);
  }
  async function lookup() {
    if (busy || looking || !code.trim()) return;
    const id = ++requestId.current;
    setLooking(true);
    setError("");
    setResult(null);
    setProductId("");
    try {
      const found = await api(
        `/san-pham/tra-cuu?${new URLSearchParams({ ma: code.trim() })}`,
      );
      if (id !== requestId.current) return;
      setLookedUp(found);
      setProductId(found.ma_sp);
    } catch (err) {
      if (id === requestId.current) setError(err.message);
    } finally {
      if (id === requestId.current) setLooking(false);
    }
  }
  async function submit(e) {
    e.preventDefault();
    if (busy || looking) return;
    if (!product) {
      setError("Vui lòng chọn sản phẩm hoặc tìm đúng mã trước khi bán.");
      return;
    }
    if (!Number.isInteger(Number(qty)) || Number(qty) <= 0) {
      setError("Số lượng bán phải là số nguyên lớn hơn 0.");
      return;
    }
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const invoice = await api("/ban-hang", {
        method: "POST",
        body: jsonBody({ barcode: product.barcode, so_luong: Number(qty) }),
      });
      // Giá/giảm giá lấy theo từng lô trong hóa đơn trả về, không đoán từ màu cảnh báo.
      setResult({ ...invoice, ten_sp: product.ten_sp });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="operation-grid">
      <form className="panel form-stack" onSubmit={submit}>
        <h2>Bán hàng</h2>
        <Notice error={error} />
        <div className="sale-code-search">
          <label>
            Tìm bằng mã vạch / mã lô
            <input
              value={code}
              disabled={busy}
              placeholder="Dán mã từ Manager"
              autoComplete="off"
              spellCheck={false}
              onChange={(e) => changeCode(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  lookup();
                }
              }}
            />
          </label>
          <button
            type="button"
            className="secondary"
            disabled={busy || looking || !code.trim()}
            onClick={lookup}
          >
            {looking ? "Đang tìm…" : "Tìm sản phẩm"}
          </button>
        </div>
        <label>
          Chọn sản phẩm
          <select
            value={productId}
            disabled={busy}
            onChange={(e) => selectProduct(e.target.value)}
          >
            <option value="" disabled>
              Chọn sản phẩm
            </option>
            {sortedProducts.map((p) => (
              <option key={p.ma_sp} value={p.ma_sp}>
                {p.ten_sp}
              </option>
            ))}
          </select>
        </label>
        <label>
          Số lượng
          <input
            required
            disabled={busy || looking || !product}
            type="number"
            min="1"
            step="1"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
          />
        </label>
        <button disabled={busy || looking || !product}>
          {busy ? "Đang ghi nhận…" : "Ghi nhận bán hàng"}
        </button>
        <p className="help">
          Tự chọn lô hạn gần nhất đủ điều kiện bán. Khi thiếu hàng, toàn bộ giao
          dịch bị từ chối.
        </p>
      </form>
      <SaleReceipt result={result} />
    </div>
  );
}
