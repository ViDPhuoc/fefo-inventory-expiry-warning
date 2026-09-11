import { useEffect, useState } from "react";
import { jsonBody, dateVN } from "../api";
import { Notice } from "./Shared";
import { suggestedExpiry, updateReceipt } from "../receiptFields";
export default function ReceiptForm({ api, products, today }) {
  const [form, setForm] = useState({
    ma_sp: products[0]?.ma_sp || "",
    ngay_san_xuat: today,
    han_su_dung: "",
    so_luong_nhap: 10,
  });
  const [result, setResult] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [settings, setSettings] = useState({});
  const [settingsError, setSettingsError] = useState("");
  const [loadingSettings, setLoadingSettings] = useState(true);
  useEffect(() => {
    let active = true;
    api("/cau-hinh-han-su-dung")
      .then((data) => {
        if (!active) return;
        setSettings(data);
        setForm((f) => ({
          ...f,
          han_su_dung:
            f.han_su_dung || suggestedExpiry(f.ngay_san_xuat, data[f.ma_sp]),
        }));
      })
      .catch(() => {
        if (active)
          setSettingsError(
            "Chưa tải được HSD gợi ý. Bạn vẫn có thể nhập HSD trên bao bì.",
          );
      })
      .finally(() => {
        if (active) setLoadingSettings(false);
      });
    return () => {
      active = false;
    };
  }, [api]);
  const update = (key, value) => {
    setForm((f) => updateReceipt(f, key, value, settings));
    setResult(null);
    setError("");
  };
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(
        await api("/lo-hang", {
          method: "POST",
          body: jsonBody({
            ...form,
            so_luong_nhap: Number(form.so_luong_nhap),
          }),
        }),
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="operation-grid">
      <form onSubmit={submit} className="panel form-stack">
        <h2>Nhập lô mới</h2>
        <Notice error={error} />
        <Notice error={settingsError} />
        <label>
          Sản phẩm
          <select
            disabled={busy}
            value={form.ma_sp}
            onChange={(e) => update("ma_sp", e.target.value)}
          >
            {products.map((p) => (
              <option key={p.ma_sp} value={p.ma_sp}>
                {p.ten_sp}
              </option>
            ))}
          </select>
        </label>
        <div className="form-row">
          <label>
            Ngày sản xuất
            <input
              disabled={busy}
              required
              type="date"
              max={today}
              value={form.ngay_san_xuat}
              onChange={(e) => update("ngay_san_xuat", e.target.value)}
            />
          </label>
          <label>
            Hạn sử dụng
            <input
              disabled={busy}
              required
              type="date"
              min={today}
              value={form.han_su_dung}
              onChange={(e) => update("han_su_dung", e.target.value)}
            />
          </label>
        </div>
        <p className="help" aria-live="polite">
          {loadingSettings
            ? "Đang tải HSD gợi ý…"
            : settings[form.ma_sp]
              ? `Gợi ý: ${settings[form.ma_sp]} ngày kể từ ngày sản xuất. Kiểm tra ngày sản xuất và HSD trên bao bì; có thể sửa HSD bên trên.`
              : "Sản phẩm chưa có thời hạn bảo quản được cấu hình. Nhập HSD trên bao bì hoặc hỏi quản lý."}
        </p>
        {settings[form.ma_sp] &&
          form.han_su_dung !==
            suggestedExpiry(form.ngay_san_xuat, settings[form.ma_sp]) && (
            <button
              type="button"
              className="secondary"
              disabled={busy}
              onClick={() =>
                update(
                  "han_su_dung",
                  suggestedExpiry(form.ngay_san_xuat, settings[form.ma_sp]),
                )
              }
            >
              Dùng lại HSD gợi ý
            </button>
          )}
        <label>
          Số lượng nhập
          <input
            required
            type="number"
            min="1"
            step="1"
            value={form.so_luong_nhap}
            onChange={(e) => update("so_luong_nhap", e.target.value)}
          />
        </label>
        <button disabled={busy}>{busy ? "Đang lưu…" : "Tạo lô hàng"}</button>
        <p className="help">
          Ghi đúng HSD trên hàng. Lô đã cận hạn theo ngưỡng Vàng của nhóm sẽ bị
          từ chối.
        </p>
      </form>
      <section className="panel">
        <h2>Thông tin lô vừa nhập</h2>
        {result ? (
          <>
            <Notice success="Đã tạo lô mới, không cộng gộp hạn dùng vào sản phẩm." />
            <p className="code">{result.ma_lo}</p>
            <p>
              Số lượng tồn: <strong>{result.so_luong_ton}</strong>
            </p>
            <p>
              Hạn sử dụng: <strong>{dateVN(result.han_su_dung)}</strong>
            </p>
          </>
        ) : (
          <p className="muted">
            Mỗi lần nhập tạo một mã lô riêng để theo dõi hạn dùng.
          </p>
        )}
      </section>
    </div>
  );
}
