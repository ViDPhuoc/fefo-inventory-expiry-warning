import { useEffect, useRef } from "react";
import { number, riskLabel } from "../api";
export function Notice({ error, success }) {
  return error ? (
    <div className="notice error" role="alert">
      {error}
    </div>
  ) : success ? (
    <div className="notice success" role="status">
      {success}
    </div>
  ) : null;
}
export function Badge({ risk, expired }) {
  return (
    <span className={`badge ${risk}`}>
      {expired ? "Đã hết hạn" : riskLabel[risk]}
    </span>
  );
}
export function Loading({ active }) {
  return active ? (
    <p className="muted" role="status">
      Đang cập nhật dữ liệu…
    </p>
  ) : null;
}
export function Empty({ children = "Chưa có dữ liệu phù hợp." }) {
  return <div className="empty">{children}</div>;
}
export function Pager({ page, total, size, onChange }) {
  const pages = Math.max(1, Math.ceil(total / size));
  return (
    <div className="pager">
      <span>
        {number(total)} kết quả · Trang {page}/{pages}
      </span>
      <div>
        <button
          className="secondary"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          Trước
        </button>
        <button
          className="secondary"
          disabled={page >= pages}
          onClick={() => onChange(page + 1)}
        >
          Sau
        </button>
      </div>
    </div>
  );
}
export function Modal({ title, children, onClose }) {
  const ref = useRef();
  // Native dialog giữ focus và hỗ trợ Escape để thao tác được bằng bàn phím.
  useEffect(() => {
    const d = ref.current;
    d.showModal();
    return () => d.close();
  }, []);
  return (
    <dialog ref={ref} onCancel={onClose}>
      <div className="dialog-head">
        <h2>{title}</h2>
        <button
          type="button"
          className="icon-button"
          aria-label="Đóng"
          onClick={onClose}
        >
          ×
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function Stat({ label, value, hint, tone = "" }) {
  return (
    <div className={`stat ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </div>
  );
}
