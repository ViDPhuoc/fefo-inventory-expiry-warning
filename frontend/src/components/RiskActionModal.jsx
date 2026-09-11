import { useState } from "react";
import { Modal, Notice } from "./Shared";
import { dateVN, jsonBody } from "../api";
export default function RiskActionModal({ lot, api, onClose, onDone }) {
  const [type, setType] = useState(lot.da_het_han ? "XuatHuy" : "GiamGia");
  const [discount, setDiscount] = useState(30);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/xu-ly-rui-ro/${encodeURIComponent(lot.ma_lo)}`, {
        method: "POST",
        body: jsonBody({
          loai_xu_ly: type,
          ty_le_giam: type === "GiamGia" ? Number(discount) : null,
          ghi_chu: reason,
        }),
      });
      onDone();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title="Giao việc xử lý lô" onClose={onClose}>
      <p>
        <strong>{lot.ten_sp}</strong>
        <br />
        <span className="muted">
          {lot.ma_lo} · HSD {dateVN(lot.han_su_dung)} · Tồn {lot.so_luong_ton}
        </span>
      </p>
      <Notice error={error} />
      <form onSubmit={submit} className="form-stack">
        <label>
          Hướng xử lý
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="GiamGia" disabled={lot.da_het_han}>
              Giảm giá, dán tem
            </option>
            <option value="XuatHuy">Xuất hủy toàn bộ lô</option>
          </select>
        </label>
        {type === "GiamGia" && (
          <label>
            Tỷ lệ giảm (%)
            <input
              required
              type="number"
              min="0.01"
              max="99.99"
              step="0.01"
              value={discount}
              onChange={(e) => setDiscount(e.target.value)}
            />
          </label>
        )}
        <label>
          Lý do / hướng dẫn cho nhân viên
          <textarea
            required
            minLength={3}
            maxLength={255}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </label>
        <p className="help">
          {type === "XuatHuy"
            ? "Lô sẽ bị chặn bán ngay khi giao việc. Tồn chỉ được trừ khi nhân viên xác nhận đã hủy."
            : "Giá bán chỉ thay đổi sau khi nhân viên xác nhận đã dán tem."}
        </p>
        <button disabled={busy}>{busy ? "Đang lưu…" : "Tạo lệnh xử lý"}</button>
      </form>
    </Modal>
  );
}
