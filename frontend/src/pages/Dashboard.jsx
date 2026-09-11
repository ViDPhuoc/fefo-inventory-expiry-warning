import { useState } from "react";
import useResource from "../hooks/useResource";
import {
  Badge,
  Empty,
  Loading,
  Notice,
  Pager,
  Stat,
} from "../components/Shared";
import RiskActionModal from "../components/RiskActionModal";
import GroupRiskBar from "../components/GroupRiskBar";
import { dateVN, money, number, dailyRate } from "../api";

export default function Dashboard({ api }) {
  const [filters, setFilters] = useState({
    q: "",
    ma_nhom: "",
    muc_rui_ro: "",
    so_ngay_lookback: 14,
  });
  const [search, setSearch] = useState(""),
    [page, setPage] = useState(1),
    [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState(null),
    [notice, setNotice] = useState("");
  const { data, loading, error } = useResource(
    () =>
      api(
        `/dashboard?${new URLSearchParams({ ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== "")), page })}`,
      ),
    [api, filters, page, revision],
  );
  const groups = useResource(() => api("/nhom-hang"), [api]);
  const stats = data?.thong_ke;
  function change(key, value) {
    setPage(1);
    setFilters((f) => ({ ...f, [key]: value }));
  }
  return (
    <>
      <header className="page-head">
        <div>
          <p className="eyebrow">QUẢN LÝ CỬA HÀNG</p>
          <h1>Cảnh báo tồn kho</h1>
          <p className="muted">
            Xác định lô cần xử lý từ tồn kho, hạn dùng và tốc độ bán.
          </p>
        </div>
        <button
          className="secondary"
          onClick={() => setRevision((v) => v + 1)}
          disabled={loading}
        >
          Làm mới
        </button>
      </header>
      <Notice error={error || groups.error} success={notice} />
      <form
        className="filters"
        onSubmit={(e) => {
          e.preventDefault();
          change("q", search);
        }}
      >
        <label className="search-field">
          Tìm sản phẩm, mã lô, mã vạch
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Ví dụ: Sữa tươi, bánh mì, nước cam"
          />
        </label>
        <label>
          Nhóm hàng
          <select
            value={filters.ma_nhom}
            onChange={(e) => change("ma_nhom", e.target.value)}
          >
            <option value="">Tất cả nhóm</option>
            {groups.data?.map((g) => (
              <option key={g.ma_nhom} value={g.ma_nhom}>
                {g.ten_nhom}
              </option>
            ))}
          </select>
        </label>
        <label>
          Mức cảnh báo
          <select
            value={filters.muc_rui_ro}
            onChange={(e) => change("muc_rui_ro", e.target.value)}
          >
            <option value="">Tất cả mức</option>
            <option value="Do">Báo động</option>
            <option value="Vang">Cần chú ý</option>
            <option value="Xanh">An toàn</option>
          </select>
        </label>
        <label>
          Lịch sử bán
          <select
            value={filters.so_ngay_lookback}
            onChange={(e) => change("so_ngay_lookback", Number(e.target.value))}
          >
            {[7, 14, 30, 60, 90, 180].map((n) => (
              <option key={n} value={n}>
                {n} ngày
              </option>
            ))}
          </select>
        </label>
        <button>Tìm</button>
      </form>
      <Loading active={loading} />
      {stats && (
        <div aria-busy={loading}>
          <div className="stats-grid dashboard-stats">
            <Stat
              label="Lô cần xử lý / xem xét"
              value={number(
                stats.so_luong_theo_muc.Do + stats.so_luong_theo_muc.Vang,
              )}
              hint={`Trên ${number(stats.tong_lo)} lô đang hiển thị`}
              tone="accent"
            />
            <Stat
              label="Lô đã đến / quá hạn"
              value={number(stats.lo_da_het_han)}
              hint="Đã chặn bán theo ngày HSD"
            />
            <Stat
              label="Giá trị tồn dư tham chiếu"
              value={money(stats.gia_tri_ton_du_tham_chieu)}
              hint="Theo giá bán gốc, không phải lợi nhuận mất đi"
            />
          </div>
          <div className="dashboard-overview">
            <section className="panel">
              <div className="section-head">
                <h2>Phân bố cảnh báo theo nhóm</h2>
                <span className="muted">{dateVN(data.ngay_tinh)}</span>
              </div>
              <div className="legend">
                <span className="legend-red">Báo động</span>
                <span className="legend-yellow">Cần chú ý</span>
                <span className="legend-green">An toàn</span>
                <small>Rê chuột vào thanh để xem số lô ở từng mức.</small>
              </div>
              {stats.theo_nhom.map((g) => <GroupRiskBar key={g.ten_nhom} group={g} />)}
            </section>
          </div>
          <section className="panel table-panel">
            <div className="section-head">
              <div>
                <h2>Danh sách lô hàng</h2>
                <p className="muted">
                  Tốc độ bán trung bình được tính từ lịch sử bán; lô có hạn gần nhất được ưu tiên trước.
                </p>
              </div>
            </div>
            {data.danh_sach.length ? (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Sản phẩm / lô</th>
                      <th>Hạn sử dụng</th>
                      <th>Tồn</th>
                      <th title="Tổng số lượng bán của sản phẩm trong khoảng đã chọn, chia cho số ngày">Bán TB/ngày</th>
                      <th>Ước bán trước HSD</th>
                      <th>Nguy cơ dư</th>
                      <th>Cảnh báo</th>
                      <th>Xử lý</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.danh_sach.map((l) => (
                      <tr key={l.ma_lo}>
                        <td>
                          <strong>{l.ten_sp}</strong>
                          <small className="code">{l.ma_lo}</small>
                          <small>{l.ten_nhom}</small>
                        </td>
                        <td>
                          {dateVN(l.han_su_dung)}
                          <small>
                            {l.so_ngay_con_lai > 0
                              ? `Còn ${l.so_ngay_con_lai} ngày`
                              : "Đã đến / quá hạn"}
                          </small>
                        </td>
                        <td>{number(l.so_luong_ton)}</td>
                        <td title={`Trung bình số lượng bán trong ${filters.so_ngay_lookback} ngày đã kết thúc; hiển thị làm tròn 1 chữ số thập phân.`}>
                          {dailyRate(l.toc_do_tieu_thu_ngay)}
                          <small>
                            {l.co_du_lieu_ban
                              ? `${number(l.tong_so_luong_ban_trong_ky)} đã bán`
                              : "Chưa có lịch sử bán"}
                          </small>
                        </td>
                        <td>{l.so_luong_uoc_ban_duoc ?? "—"}</td>
                        <td
                          className={
                            l.so_luong_nguy_co_ton_du > 0 ? "risk-number" : ""
                          }
                        >
                          {l.so_luong_nguy_co_ton_du ?? "—"}
                        </td>
                        <td>
                          <Badge risk={l.muc_rui_ro} expired={l.da_het_han} />
                          <small className="reason">{l.ly_do}</small>
                        </td>
                        <td>
                          <button
                            className="secondary compact"
                            disabled={loading || l.trang_thai === "ChoXuatHuy"}
                            onClick={() => setSelected(l)}
                          >
                            {l.trang_thai === "ChoXuatHuy"
                              ? "Chờ hủy"
                              : "Giao việc"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty />
            )}
            <Pager
              page={page}
              total={data.total}
              size={30}
              onChange={setPage}
            />
          </section>
        </div>
      )}
      {selected && (
        <RiskActionModal
          lot={selected}
          api={api}
          onClose={() => setSelected(null)}
          onDone={() => {
            setSelected(null);
            setRevision((x) => x + 1);
            setNotice("Đã giao việc. Theo dõi tiến độ trong Lệnh xử lý.");
          }}
        />
      )}
    </>
  );
}
