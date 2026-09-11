import { useState } from "react";
import useResource from "../hooks/useResource";
import { dateVN, money, number } from "../api";
import { Empty, Loading, Notice, Stat } from "../components/Shared";
export default function Reports({ api }) {
  const [start, setStart] = useState(""),
    [end, setEnd] = useState(""),
    [query, setQuery] = useState("");
  const { data, loading, error } = useResource(
    () => api(`/bao-cao${query}`),
    [api, query],
  );
  function submit(e) {
    e.preventDefault();
    setQuery(
      `?${new URLSearchParams({ tu_ngay: start || data?.tu_ngay, den_ngay: end || data?.den_ngay })}`,
    );
  }
  const max = Math.max(1, ...(data?.theo_ngay.map((d) => d.doanh_thu) || []));
  return (
    <>
      <header className="page-head">
        <div>
          <p className="eyebrow">TỔNG HỢP CHO QUẢN LÝ</p>
          <h1>Báo cáo tiêu thụ</h1>
          <p className="muted">
            Doanh thu đã ghi nhận và hàng đã xuất hủy trong khoảng thời gian lựa
            chọn.
          </p>
        </div>
      </header>
      <Notice error={error} />
      <form className="filters report-filters" onSubmit={submit}>
        <label>
          Từ ngày
          <input
            type="date"
            required
            value={start || data?.tu_ngay || ""}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label>
          Đến ngày
          <input
            type="date"
            required
            value={end || data?.den_ngay || ""}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
        <button disabled={loading}>Xem báo cáo</button>
      </form>
      <Loading active={loading} />
      {data && (
        <>
          <div className="stats-grid">
            <Stat
              label="Doanh thu ghi nhận"
              value={money(data.tong_doanh_thu)}
              hint="Theo đơn giá thực bán, gồm giảm giá"
              tone="accent"
            />
            <Stat
              label="Số lượng đã bán"
              value={number(data.tong_so_luong_ban)}
              hint={`${number(data.so_hoa_don)} hóa đơn`}
            />
            <Stat
              label="Số lượng đã xuất hủy"
              value={number(data.so_luong_da_huy)}
              hint="Chỉ lệnh nhân viên đã xác nhận"
            />
            <Stat
              label="Giá trị hủy tham chiếu"
              value={money(data.gia_tri_huy_tham_chieu)}
              hint="Theo giá bán gốc lúc duyệt, không phải giá vốn"
            />
          </div>
          <section className="panel">
            <div className="section-head">
              <h2>Doanh thu theo ngày</h2>
              <span className="muted">
                Mức cao nhất:{" "}
                {money(max === 1 && data.tong_doanh_thu === 0 ? 0 : max)}
              </span>
            </div>
            <div className="chart-scroll">
              <div
                className="daily-chart"
                style={{ minWidth: Math.max(400, data.theo_ngay.length * 12) }}
              >
                {data.theo_ngay.map((d) => (
                  <div
                    key={d.ngay}
                    className="daily-column"
                    title={`${dateVN(d.ngay)}: ${money(d.doanh_thu)}`}
                  >
                    <div
                      className="daily-bar"
                      style={{ height: `${(d.doanh_thu / max) * 100}%` }}
                    />
                  </div>
                ))}
              </div>
            </div>
            <div className="axis-labels">
              <span>{dateVN(data.tu_ngay)}</span>
              <span>{dateVN(data.den_ngay)}</span>
            </div>
            <details>
              <summary>Xem bảng số liệu từng ngày</summary>
              <div className="table-scroll bounded">
                <table>
                  <thead>
                    <tr>
                      <th>Ngày</th>
                      <th>Số lượng bán</th>
                      <th>Doanh thu</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.theo_ngay.map((d) => (
                      <tr key={d.ngay}>
                        <td>{dateVN(d.ngay)}</td>
                        <td>{number(d.so_luong_ban)}</td>
                        <td>{money(d.doanh_thu)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          </section>
          <section className="panel table-panel">
            <div className="section-head">
              <h2>10 sản phẩm doanh thu cao nhất</h2>
            </div>
            {data.top_san_pham.length ? (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Sản phẩm</th>
                      <th>Số lượng bán</th>
                      <th>Doanh thu</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_san_pham.map((p) => (
                      <tr key={p.ten_sp}>
                        <td>{p.ten_sp}</td>
                        <td>{number(p.so_luong_ban)}</td>
                        <td>{money(p.doanh_thu)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty>Chưa có giao dịch bán trong khoảng ngày này.</Empty>
            )}
          </section>
        </>
      )}
    </>
  );
}
