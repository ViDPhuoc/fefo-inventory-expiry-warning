-- Chạy từ thư mục scripts/. Database phải trống và đã có schema.
\set ON_ERROR_STOP on
BEGIN;
\copy nhom_hang (ma_nhom,ten_nhom,muc_canh_bao_vang,muc_canh_bao_do) FROM 'output/nhom_hang.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy nguoi_dung (ma_nv,ho_ten,ten_dang_nhap,mat_khau_hash,vai_tro,ngay_tao) FROM 'output/nguoi_dung.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy san_pham (ma_sp,barcode,ten_sp,gia_ban,ma_nhom,dang_kinh_doanh) FROM 'output/san_pham.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy lo_hang (ma_lo,ma_sp,ngay_san_xuat,han_su_dung,ngay_nhap,so_luong_nhap,so_luong_ton,trang_thai,ty_le_giam,ma_nv_nhap) FROM 'output/lo_hang.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy hoa_don_ban (ma_hd,ma_nv,thoi_gian_ban) FROM 'output/hoa_don_ban.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy chi_tiet_ban (ma_ct,ma_hd,ma_lo,so_luong,don_gia) FROM 'output/chi_tiet_ban.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
SELECT setval(pg_get_serial_sequence('chi_tiet_ban','ma_ct'), COALESCE(MAX(ma_ct),1), COUNT(*) > 0) FROM chi_tiet_ban;
COMMIT;
