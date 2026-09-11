import { useState } from "react";
import useResource from "../hooks/useResource";
import { Loading, Notice } from "../components/Shared";
import SaleForm from "../components/SaleForm";
import ReceiptForm from "../components/ReceiptForm";
import StockForm from "../components/StockForm";
export default function Operations({ api }) {
  const [tab, setTab] = useState("sell");
  const { data, loading, error } = useResource(
    () => Promise.all([api("/san-pham"), api("/health")]),
    [api],
  );
  return (
    <>
      <header className="page-head">
        <div>
          <p className="eyebrow">VẬN HÀNH CỬA HÀNG</p>
          <h1>Nhập · Bán · Kiểm kê</h1>
          <p className="muted">
            Ghi nhận đúng theo lô để cảnh báo của quản lý phản ánh tồn kho thực
            tế.
          </p>
        </div>
      </header>
      <Notice error={error} />
      <div className="tabs" role="tablist" aria-label="Nghiệp vụ">
        {[
          ["sell", "Bán hàng"],
          ["receive", "Nhập kho"],
          ["stock", "Kiểm kê"],
        ].map(([id, label]) => (
          <button
            key={id}
            role="tab"
            aria-selected={tab === id}
            className={tab === id ? "active" : ""}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <Loading active={loading} />
      {data && (
        <div role="tabpanel">
          {tab === "sell" && <SaleForm api={api} products={data[0]} />}{" "}
          {tab === "receive" && (
            <ReceiptForm
              api={api}
              products={data[0]}
              today={data[1].ngay_nghiep_vu}
            />
          )}{" "}
          {tab === "stock" && <StockForm api={api} products={data[0]} />}
        </div>
      )}
    </>
  );
}
