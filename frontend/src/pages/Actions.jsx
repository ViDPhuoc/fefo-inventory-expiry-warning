import { useState } from "react";
import useResource from "../hooks/useResource";
import { Empty, Loading, Modal, Notice, Pager } from "../components/Shared";
import { jsonBody, money, stateLabel } from "../api";
export default function Actions({ api, manager }) {
  const [pending, setPending] = useState(true),
    [page, setPage] = useState(1),
    [rev, setRev] = useState(0);
  const [chosen, setChosen] = useState(null),
    [reason, setReason] = useState(""),
    [busy, setBusy] = useState(false);
  const [error, setError] = useState(""),
    [success, setSuccess] = useState("");
  const state = useResource(
    () => api(`/xu-ly-rui-ro?chi_dang_cho=${pending}&page=${page}`),
    [api, pending, page, rev],
  );
  async function confirm(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(
        `/xu-ly-rui-ro/lenh/${chosen.ma_xl}/${manager ? "huy" : "hoan-tat"}`,
        {
          method: "POST",
          ...(manager ? { body: jsonBody({ ly_do: reason }) } : {}),
        },
      );
      setChosen(null);
      setRev((x) => x + 1);
      setSuccess(
        manager
          ? "Đã hủy lệnh và lưu lý do."
          : "Đã ghi nhận thực hiện và cập nhật lô hàng.",
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <header className="page-head">
        <div>
          <p className="eyebrow">PHỐI HỢP XỬ LÝ</p>
          <h1>{manager ? "Lệnh xử lý rủi ro" : "Việc cần thực hiện"}</h1>
          <p className="muted">
            {manager
              ? "Theo dõi việc đã giao và kết quả nhân viên xác nhận."
              : "Kiểm tra đúng lô và thực hiện công việc tại cửa hàng trước khi xác nhận."}
          </p>
        </div>
        <button
          className="secondary"
          disabled={state.loading}
          onClick={() => setRev((x) => x + 1)}
        >
          Làm mới
        </button>
      </header>
      <Notice error={!chosen && (error || state.error)} success={success} />
      <label className="checkbox">
        <input
          type="checkbox"
          checked={pending}
          onChange={(e) => {
            setPending(e.target.checked);
            setPage(1);
          }}
        />
        Chỉ hiển thị lệnh đang chờ
      </label>
      <Loading active={state.loading} />
      <section className="panel table-panel">
        {state.data?.items.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Lệnh / lô</th>
                  <th>Yêu cầu xử lý</th>
                  <th>Số lượng lúc duyệt</th>
                  <th>Trạng thái</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {state.data.items.map((a) => (
                  <tr key={a.ma_xl}>
                    <td>
                      <strong>
                        #{a.ma_xl} ·{" "}
                        {a.loai_xu_ly === "GiamGia" ? "Giảm giá" : "Xuất hủy"}
                      </strong>
                      <small className="code">{a.ma_lo}</small>
                      <small>Người duyệt: {a.ma_nv_duyet}</small>
                    </td>
                    <td>
                      {a.ghi_chu}
                      <small>
                        {a.loai_xu_ly === "GiamGia"
                          ? `Giảm ${a.ty_le_giam}%`
                          : `Giá tham chiếu: ${money(a.gia_tham_chieu)}`}
                      </small>
                      {a.ly_do_huy && (
                        <small>Lý do hủy lệnh: {a.ly_do_huy}</small>
                      )}
                    </td>
                    <td>{a.so_luong}</td>
                    <td>
                      <span
                        className={`badge ${a.trang_thai === "ChoXuLy" ? "Vang" : "neutral"}`}
                      >
                        {stateLabel[a.trang_thai]}
                      </span>
                      {a.ma_nv_thuc_hien && (
                        <small>Thực hiện: {a.ma_nv_thuc_hien}</small>
                      )}
                    </td>
                    <td>
                      {a.trang_thai === "ChoXuLy" && (
                        <button
                          className="secondary compact"
                          onClick={() => {
                            setChosen(a);
                            setReason("");
                            setError("");
                          }}
                        >
                          {manager ? "Hủy lệnh" : "Xác nhận đã làm"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty>
            Không có lệnh phù hợp. Manager tạo lệnh từ danh sách cảnh báo.
          </Empty>
        )}
        {state.data && (
          <Pager
            page={page}
            total={state.data.total}
            size={50}
            onChange={setPage}
          />
        )}
      </section>
      {chosen && (
        <Modal
          title={
            manager ? "Hủy lệnh đang chờ" : "Xác nhận công việc đã hoàn tất"
          }
          onClose={() => setChosen(null)}
        >
          <Notice error={error} />
          <form className="form-stack" onSubmit={confirm}>
            <p>
              Lô <strong>{chosen.ma_lo}</strong> ·{" "}
              {chosen.loai_xu_ly === "GiamGia"
                ? `Dán tem giảm ${chosen.ty_le_giam}%`
                : "Xuất hủy toàn bộ số hàng còn lại"}
              .
            </p>
            {manager ? (
              <label>
                Lý do hủy lệnh
                <textarea
                  required
                  minLength={3}
                  maxLength={255}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>
            ) : (
              <p className="help">
                Chỉ xác nhận sau khi đã thực hiện với hàng thật. Hệ thống sẽ lưu
                người thực hiện và thời điểm hoàn tất.
              </p>
            )}
            <button disabled={busy}>
              {busy
                ? "Đang ghi nhận…"
                : manager
                  ? "Hủy lệnh và lưu lý do"
                  : "Đã thực hiện — xác nhận"}
            </button>
          </form>
        </Modal>
      )}
    </>
  );
}
