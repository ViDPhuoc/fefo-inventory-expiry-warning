import { dateVN, money } from "../api";
import { Notice } from "./Shared";

export default function SaleReceipt({ result }) {
  return (
    <section className="panel sale-receipt">
      <h2>Kết quả giao dịch</h2>
      {result ? (
        <>
          <Notice success="Đã lưu hóa đơn và cập nhật tồn kho." />
          {/* Không hiện mã HD dài; mã thật vẫn nằm trong phản hồi và lịch sử CSDL. */}
          <p className="help">Tổng thanh toán</p>
          <div className="invoice-total">{money(result.tong_tien)}</div>
          {result.cac_lo_da_tru.map((lot, index) => (
            <div className="receipt-line" key={lot.ma_lo}>
              <div>
                <strong>{result.ten_sp}</strong>
                <small>
                  Lô xuất {index + 1} · HSD {dateVN(lot.han_su_dung)}
                </small>
                {lot.gia_goc != null && (
                  <p className="sale-price-original">
                    Giá gốc: {money(lot.gia_goc)} / sản phẩm
                  </p>
                )}
                <p className="sale-price-discount">
                  {lot.ty_le_giam > 0
                    ? `Giảm ${lot.ty_le_giam}%`
                    : "Không giảm giá"}
                </p>
                <p className="sale-price-payable">
                  Giá bán: {money(lot.don_gia)} / sản phẩm
                </p>
                <small>
                  {lot.so_luong_tru} × {money(lot.don_gia)}
                </small>
              </div>
              <strong>{money(lot.so_luong_tru * lot.don_gia)}</strong>
            </div>
          ))}
        </>
      ) : (
        <p className="muted">
          Lô đã trừ và đơn giá thực tế sẽ xuất hiện sau giao dịch.
        </p>
      )}
    </section>
  );
}
