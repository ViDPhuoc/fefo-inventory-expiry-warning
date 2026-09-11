import { useMemo, useState } from "react";
import { createApi } from "./api";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Rules from "./pages/Rules";
import Actions from "./pages/Actions";
import Operations from "./pages/Operations";
import Reports from "./pages/Reports";

export default function App() {
  // Thông tin Basic chỉ giữ trong bộ nhớ, không lưu vào localStorage.
  const [session, setSession] = useState(null),
    [page, setPage] = useState("dashboard");
  const api = useMemo(() => createApi(session?.auth), [session?.auth]);
  if (!session)
    return (
      <Login
        onLogin={(auth, user) => {
          setSession({ auth, user });
          setPage(user.vai_tro === "Manager" ? "dashboard" : "operations");
        }}
      />
    );
  const manager = session.user.vai_tro === "Manager";
  const navigation = manager
    ? [
        ["dashboard", "Cảnh báo tồn kho"],
        ["reports", "Báo cáo tiêu thụ"],
        ["rules", "Ngưỡng cảnh báo"],
        ["actions", "Lệnh xử lý"],
      ]
    : [
        ["operations", "Nhập · Bán · Kiểm kê"],
        ["actions", "Việc cần thực hiện"],
      ];
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">H</span>
          <div>
            <strong>HẠN DÙNG</strong>
            <small>Quản lý theo lô</small>
          </div>
        </div>
        <p className="nav-label">
          {manager ? "KHÔNG GIAN QUẢN LÝ" : "VẬN HÀNH CỬA HÀNG"}
        </p>
        <nav aria-label="Chức năng chính">
          {navigation.map(([id, label]) => (
            <button
              key={id}
              className={page === id ? "active" : ""}
              aria-current={page === id ? "page" : undefined}
              onClick={() => setPage(id)}
            >
              {label}
            </button>
          ))}
        </nav>
        <div className="account">
          <strong>{session.user.ho_ten}</strong>
          <span>{manager ? "Quản lý cửa hàng" : "Nhân viên cửa hàng"}</span>
          <button onClick={() => setSession(null)}>Đổi tài khoản</button>
        </div>
      </aside>
      <main className="workspace">
        {page === "dashboard" && <Dashboard api={api} />}{" "}
        {page === "reports" && <Reports api={api} />}{" "}
        {page === "rules" && <Rules api={api} />}{" "}
        {page === "actions" && <Actions api={api} manager={manager} />}{" "}
        {page === "operations" && <Operations api={api} />}
      </main>
    </div>
  );
}
