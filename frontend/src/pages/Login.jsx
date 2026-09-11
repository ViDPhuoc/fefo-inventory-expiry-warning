import { useState } from "react";
import { createApi } from "../api";
import { Notice } from "../components/Shared";
export default function Login({ onLogin }) {
  const [name, setName] = useState("manager1"),
    [password, setPassword] = useState("Demo@2026");
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const auth = btoa(`${name}:${password}`);
      const user = await createApi(auth)("/me");
      onLogin(auth, user);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login">
      <section className="login-panel">
        <div className="brand-mark">H</div>
        <p className="eyebrow">HẠN DÙNG</p>
        <h1>
          Theo dõi từng lô.
          <br />
          Xử lý trước khi quá hạn.
        </h1>
        <p className="muted">
          Không gian làm việc của quản lý và nhân viên cửa hàng.
        </p>
        <Notice error={error} />
        <form onSubmit={submit} className="form-stack">
          <label>
            Tài khoản
            <input
              required
              autoComplete="username"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label>
            Mật khẩu
            <input
              required
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button disabled={busy}>
            {busy ? "Đang xác nhận…" : "Vào không gian làm việc"}
          </button>
        </form>
        <div className="demo-accounts">
          <span>Tài khoản dữ liệu demo</span>
          <button
            className="secondary"
            onClick={() => {
              setName("manager1");
              setPassword("Demo@2026");
            }}
          >
            Điền Manager
          </button>
          <button
            className="secondary"
            onClick={() => {
              setName("staff1");
              setPassword("Demo@2026");
            }}
          >
            Điền Staff
          </button>
        </div>
      </section>
    </main>
  );
}
