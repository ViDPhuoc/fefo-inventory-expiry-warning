import { useEffect, useState } from "react";
import { dateVN, jsonBody, stateLabel } from "../api";
import {
  canCountLot,
  countLotLabel,
  loadProductLots,
  visibleCountLots,
} from "../staffFields";
import { Loading, Notice } from "./Shared";

export default function StockForm({ api, products }) {
  const [product, setProduct] = useState(products[0]?.ma_sp || "");
  const [busy, setBusy] = useState(false);
  return (
    <section className="panel form-stack narrow-form">
      <h2>Kiểm kê theo lô</h2>
      <label>
        Sản phẩm
        <select
          value={product}
          disabled={busy}
          onChange={(e) => setProduct(e.target.value)}
        >
          {products.map((p) => (
            <option key={p.ma_sp} value={p.ma_sp}>
              {p.ten_sp}
            </option>
          ))}
        </select>
      </label>
      {/* Đổi sản phẩm tạo lại biểu mẫu, không giữ số đếm/lý do của sản phẩm cũ. */}
      {product && (
        <StockEditor
          key={product}
          api={api}
          product={product}
          onBusy={setBusy}
        />
      )}
    </section>
  );
}

function StockEditor({ api, product, onBusy }) {
  const [lots, setLots] = useState([]),
    [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(""),
    [rev, setRev] = useState(0);
  const [ma, setMa] = useState(""),
    [quantity, setQuantity] = useState(null);
  const [reason, setReason] = useState(""),
    [showEmpty, setShowEmpty] = useState(false);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let current = true;
    setLoading(true);
    setLots([]);
    setLoadError("");
    loadProductLots(api, product, () => current).then(
      (rows) => {
        if (current) {
          setLots(rows);
          setLoading(false);
        }
      },
      (err) => {
        if (current) {
          setLoadError(err.message);
          setLoading(false);
        }
      },
    );
    return () => {
      current = false;
    };
  }, [api, product, rev]);

  const visible = visibleCountLots(lots, showEmpty);
  const lot = visible.find((l) => l.ma_lo === ma) || visible.find(canCountLot);
  const editable =
    !loading && !loadError && canCountLot(lot) && lot.ma_sp === product;
  function clearEntry() {
    setQuantity(null);
    setReason("");
    setError("");
    setSuccess("");
  }
  function refresh() {
    setLoading(true);
    setLots([]);
    setMa("");
    setQuantity(null);
    setRev((v) => v + 1);
  }

  async function submit(e) {
    e.preventDefault();
    if (busy || !editable) return;
    const count = Number(quantity ?? lot.so_luong_ton);
    if (
      quantity === "" ||
      !Number.isInteger(count) ||
      count < 0 ||
      count > lot.so_luong_nhap
    ) {
      setError("Số tồn phải là số nguyên, từ 0 đến số lượng đã nhập.");
      return;
    }
    if (reason.trim().length < 3) {
      setError("Nhập lý do ít nhất 3 ký tự.");
      return;
    }
    setBusy(true);
    onBusy(true);
    setError("");
    setSuccess("");
    try {
      const saved = await api(
        `/lo-hang/${encodeURIComponent(lot.ma_lo)}/dieu-chinh`,
        {
          method: "PATCH",
          body: jsonBody({ so_luong_thuc_te: count, ly_do: reason.trim() }),
        },
      );
      setSuccess(
        `Đã lưu ${countLotLabel(lot)}: ${lot.so_luong_ton} → ${saved.so_luong_ton}.`,
      );
      setReason("");
      refresh();
    } catch (err) {
      setError(err.message);
      refresh(); // Tải lại nếu lô vừa được bán/khóa ở một phiên khác.
    } finally {
      setBusy(false);
      onBusy(false);
    }
  }

  return (
    <form className="form-stack" onSubmit={submit}>
      <Notice error={error || loadError} success={success} />
      <label>
        Hiển thị lô
        <select
          value={showEmpty ? "all" : "stock"}
          disabled={busy}
          onChange={(e) => {
            setShowEmpty(e.target.value === "all");
            setMa("");
            clearEntry();
          }}
        >
          <option value="stock">Lô còn hàng</option>
          <option value="all">Tất cả lô, kể cả tồn bằng 0</option>
        </select>
      </label>
      <Loading active={loading} />
      <label>
        Lô cần kiểm kê
        <select
          required
          value={lot?.ma_lo || ""}
          disabled={busy || loading || Boolean(loadError)}
          onChange={(e) => {
            setMa(e.target.value);
            clearEntry();
          }}
        >
          <option value="" disabled>
            {loading ? "Đang tải lô…" : "Không có lô có thể kiểm kê"}
          </option>
          {visible.map((l) => (
            <option key={l.ma_lo} value={l.ma_lo} disabled={!canCountLot(l)}>
              {countLotLabel(l)} · Tồn {l.so_luong_ton}
              {visible.some(
                (other) =>
                  other.ma_lo !== l.ma_lo &&
                  other.ngay_nhap === l.ngay_nhap &&
                  other.han_su_dung === l.han_su_dung,
              )
                ? ` · Mã ${l.ma_lo}`
                : ""}
              {!canCountLot(l) ? ` · ${stateLabel[l.trang_thai]}` : ""}
            </option>
          ))}
        </select>
      </label>
      {!loading && !loadError && !visible.length && (
        <p className="help">
          Không có lô còn hàng. Chọn “Tất cả lô” nếu cần kiểm tra lô đang ghi
          nhận tồn bằng 0.
        </p>
      )}
      {lot && !loading && (
        <>
          <p className="help">
            Nhập ngày {dateVN(lot.ngay_nhap)} · Đã nhập {lot.so_luong_nhap} ·
            Đang ghi nhận {lot.so_luong_ton} · {stateLabel[lot.trang_thai]}
          </p>
          <details className="help">
            <summary>Xem mã lô gốc để đối chiếu</summary>
            <span className="code">{lot.ma_lo}</span>
          </details>
        </>
      )}
      <label>
        Số lượng thực tế đếm được
        <input
          required
          type="number"
          min="0"
          max={lot?.so_luong_nhap}
          step="1"
          disabled={busy || !editable}
          value={quantity ?? lot?.so_luong_ton ?? ""}
          onChange={(e) => setQuantity(e.target.value)}
        />
      </label>
      <label>
        Lý do chênh lệch
        <textarea
          required
          minLength={3}
          maxLength={255}
          value={reason}
          disabled={busy || !editable}
          onChange={(e) => setReason(e.target.value)}
        />
      </label>
      <button disabled={busy || !editable}>
        {busy ? "Đang ghi nhận…" : "Lưu kết quả kiểm kê"}
      </button>
      <button
        type="button"
        className="secondary"
        disabled={busy || loading}
        onClick={() => {
          clearEntry();
          refresh();
        }}
      >
        Tải lại danh sách lô
      </button>
      <p className="help">
        Nhập số tồn mới, không nhập phần cộng thêm. Điều chỉnh sẽ được lưu người
        làm, số trước/sau và lý do. Lô chờ hủy hoặc đã hủy không được điều
        chỉnh.
      </p>
    </form>
  );
}
