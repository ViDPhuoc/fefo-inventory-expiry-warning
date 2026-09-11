import { useState } from "react";
import useResource from "../hooks/useResource";
import { Loading, Notice } from "../components/Shared";
import { jsonBody } from "../api";
function RuleCard({ group, api, onSaved }) {
  const [yellow, setYellow] = useState(group.muc_canh_bao_vang),
    [red, setRed] = useState(group.muc_canh_bao_do);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/nhom-hang/${group.ma_nhom}`, {
        method: "PUT",
        body: jsonBody({
          muc_canh_bao_vang: Number(yellow),
          muc_canh_bao_do: Number(red),
        }),
      });
      onSaved(group.ten_nhom);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="panel rule-card" onSubmit={save}>
      <h2>{group.ten_nhom}</h2>
      <Notice error={error} />
      <label>
        Ngưỡng Vàng — số ngày còn lại
        <input
          type="number"
          required
          min="1"
          step="1"
          value={yellow}
          onChange={(e) => setYellow(e.target.value)}
        />
      </label>
      <label>
        Ngưỡng Đỏ — số ngày còn lại
        <input
          type="number"
          required
          min="0"
          max={Number(yellow) - 1}
          step="1"
          value={red}
          onChange={(e) => setRed(e.target.value)}
        />
      </label>
      <p className="help">
        Đỏ ≤ {red} ngày · Vàng ≤ {yellow} ngày. Hàng có nguy cơ tồn dư vẫn được
        cảnh báo sớm.
      </p>
      <button disabled={busy}>{busy ? "Đang lưu…" : "Lưu ngưỡng"}</button>
    </form>
  );
}
export default function Rules({ api }) {
  const { data, loading, error } = useResource(() => api("/nhom-hang"), [api]);
  const [success, setSuccess] = useState("");
  return (
    <>
      <header className="page-head">
        <div>
          <p className="eyebrow">THIẾT LẬP NGHIỆP VỤ</p>
          <h1>Ngưỡng cảnh báo</h1>
          <p className="muted">
            Cấu hình theo vòng đời từng nhóm hàng. Dashboard dùng luật mới ngay
            lần cập nhật tiếp theo.
          </p>
        </div>
      </header>
      <Notice error={error} success={success} />
      <Loading active={loading} />
      <div className="rule-grid">
        {data?.map((g) => (
          <RuleCard
            key={g.ma_nhom}
            group={g}
            api={api}
            onSaved={(name) => setSuccess(`Đã cập nhật ${name}.`)}
          />
        ))}
      </div>
    </>
  );
}
