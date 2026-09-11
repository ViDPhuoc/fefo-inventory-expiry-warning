-- PostgreSQL. Xuất từ backend/app/models.py. Dùng database demo mới.

-- Không DROP bảng hoặc dữ liệu cũ. Tạo bảng có sẵn sẽ báo lỗi.


CREATE TABLE nguoi_dung (
	ma_nv VARCHAR(20) NOT NULL, 
	ho_ten VARCHAR(100) NOT NULL, 
	ten_dang_nhap VARCHAR(50) NOT NULL, 
	mat_khau_hash VARCHAR(255) NOT NULL, 
	vai_tro VARCHAR(10) NOT NULL, 
	ngay_tao TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (ma_nv), 
	CONSTRAINT ck_vai_tro CHECK (vai_tro IN ('Manager','Staff')), 
	UNIQUE (ten_dang_nhap)
)

;


CREATE TABLE nhom_hang (
	ma_nhom VARCHAR(20) NOT NULL, 
	ten_nhom VARCHAR(100) NOT NULL, 
	muc_canh_bao_vang INTEGER NOT NULL, 
	muc_canh_bao_do INTEGER NOT NULL, 
	PRIMARY KEY (ma_nhom), 
	CONSTRAINT ck_nguong_hop_le CHECK (muc_canh_bao_do >= 0 AND muc_canh_bao_vang > muc_canh_bao_do)
)

;


CREATE TABLE hoa_don_ban (
	ma_hd VARCHAR(40) NOT NULL, 
	ma_nv VARCHAR(20) NOT NULL, 
	thoi_gian_ban TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (ma_hd), 
	FOREIGN KEY(ma_nv) REFERENCES nguoi_dung (ma_nv)
)

;

CREATE INDEX ix_hoa_don_ban_thoi_gian_ban ON hoa_don_ban (thoi_gian_ban);


CREATE TABLE san_pham (
	ma_sp VARCHAR(20) NOT NULL, 
	barcode VARCHAR(50) NOT NULL, 
	ten_sp VARCHAR(150) NOT NULL, 
	gia_ban NUMERIC(12, 0) NOT NULL, 
	ma_nhom VARCHAR(20) NOT NULL, 
	dang_kinh_doanh BOOLEAN DEFAULT true NOT NULL, 
	PRIMARY KEY (ma_sp), 
	CONSTRAINT ck_gia_ban CHECK (gia_ban >= 0), 
	UNIQUE (barcode), 
	FOREIGN KEY(ma_nhom) REFERENCES nhom_hang (ma_nhom)
)

;

CREATE INDEX ix_san_pham_ma_nhom ON san_pham (ma_nhom);


CREATE TABLE lo_hang (
	ma_lo VARCHAR(40) NOT NULL, 
	ma_sp VARCHAR(20) NOT NULL, 
	ngay_san_xuat DATE NOT NULL, 
	han_su_dung DATE NOT NULL, 
	ngay_nhap DATE NOT NULL, 
	so_luong_nhap INTEGER NOT NULL, 
	so_luong_ton INTEGER NOT NULL, 
	trang_thai VARCHAR(20) NOT NULL, 
	ty_le_giam NUMERIC(5, 2) DEFAULT '0' NOT NULL, 
	ma_nv_nhap VARCHAR(20) NOT NULL, 
	PRIMARY KEY (ma_lo), 
	CONSTRAINT ck_ton_hop_le CHECK (so_luong_nhap > 0 AND so_luong_ton >= 0 AND so_luong_ton <= so_luong_nhap), 
	CONSTRAINT ck_ngay_lo CHECK (ngay_san_xuat <= ngay_nhap AND ngay_nhap < han_su_dung), 
	CONSTRAINT ck_giam_gia_lo CHECK (ty_le_giam >= 0 AND ty_le_giam < 100), 
	CONSTRAINT ck_trang_thai_lo CHECK (trang_thai IN ('DangGiaoDich','DaBanHet','ChoXuatHuy','DaXuatHuy')), 
	CONSTRAINT ck_trang_thai_ton CHECK ((trang_thai IN ('DaBanHet','DaXuatHuy') AND so_luong_ton = 0) OR (trang_thai IN ('DangGiaoDich','ChoXuatHuy') AND so_luong_ton > 0)), 
	FOREIGN KEY(ma_sp) REFERENCES san_pham (ma_sp), 
	FOREIGN KEY(ma_nv_nhap) REFERENCES nguoi_dung (ma_nv)
)

;

CREATE INDEX ix_lo_hang_han_su_dung ON lo_hang (han_su_dung);

CREATE INDEX ix_lo_hang_ma_sp ON lo_hang (ma_sp);


CREATE TABLE chi_tiet_ban (
	ma_ct SERIAL NOT NULL, 
	ma_hd VARCHAR(40) NOT NULL, 
	ma_lo VARCHAR(40) NOT NULL, 
	so_luong INTEGER NOT NULL, 
	don_gia NUMERIC(12, 0) NOT NULL, 
	PRIMARY KEY (ma_ct), 
	CONSTRAINT ck_chi_tiet_ban CHECK (so_luong > 0 AND don_gia >= 0), 
	FOREIGN KEY(ma_hd) REFERENCES hoa_don_ban (ma_hd), 
	FOREIGN KEY(ma_lo) REFERENCES lo_hang (ma_lo)
)

;

CREATE INDEX ix_chi_tiet_ban_ma_hd ON chi_tiet_ban (ma_hd);

CREATE INDEX ix_chi_tiet_ban_ma_lo ON chi_tiet_ban (ma_lo);


CREATE TABLE dieu_chinh_ton (
	ma_dc SERIAL NOT NULL, 
	ma_lo VARCHAR(40) NOT NULL, 
	so_luong_truoc INTEGER NOT NULL, 
	so_luong_sau INTEGER NOT NULL, 
	ly_do VARCHAR(255) NOT NULL, 
	ma_nv VARCHAR(20) NOT NULL, 
	thoi_gian TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (ma_dc), 
	CONSTRAINT ck_dieu_chinh CHECK (so_luong_truoc >= 0 AND so_luong_sau >= 0), 
	FOREIGN KEY(ma_lo) REFERENCES lo_hang (ma_lo), 
	FOREIGN KEY(ma_nv) REFERENCES nguoi_dung (ma_nv)
)

;

CREATE INDEX ix_dieu_chinh_ton_ma_lo ON dieu_chinh_ton (ma_lo);


CREATE TABLE xu_ly_rui_ro (
	ma_xl SERIAL NOT NULL, 
	ma_lo VARCHAR(40) NOT NULL, 
	loai_xu_ly VARCHAR(20) NOT NULL, 
	ty_le_giam NUMERIC(5, 2), 
	so_luong INTEGER NOT NULL, 
	gia_tham_chieu NUMERIC(12, 0) NOT NULL, 
	ma_nv_duyet VARCHAR(20) NOT NULL, 
	ma_nv_thuc_hien VARCHAR(20), 
	trang_thai VARCHAR(20) NOT NULL, 
	thoi_gian TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	hoan_tat_luc TIMESTAMP WITHOUT TIME ZONE, 
	ghi_chu VARCHAR(255) NOT NULL, 
	huy_luc TIMESTAMP WITHOUT TIME ZONE, 
	ma_nv_huy VARCHAR(20), 
	ly_do_huy VARCHAR(255), 
	PRIMARY KEY (ma_xl), 
	CONSTRAINT ck_xu_ly CHECK (loai_xu_ly IN ('GiamGia','XuatHuy') AND trang_thai IN ('ChoXuLy','DaHoanTat','DaHuyLenh')), 
	CONSTRAINT ck_ty_le_xu_ly CHECK ((loai_xu_ly = 'GiamGia' AND ty_le_giam IS NOT NULL AND ty_le_giam > 0 AND ty_le_giam < 100) OR (loai_xu_ly = 'XuatHuy' AND ty_le_giam IS NULL)), 
	CONSTRAINT ck_so_luong_xu_ly CHECK (so_luong > 0 AND gia_tham_chieu >= 0), 
	CONSTRAINT ck_hoan_tat_xu_ly CHECK ((trang_thai IN ('ChoXuLy','DaHuyLenh') AND hoan_tat_luc IS NULL AND ma_nv_thuc_hien IS NULL) OR (trang_thai = 'DaHoanTat' AND hoan_tat_luc IS NOT NULL AND ma_nv_thuc_hien IS NOT NULL)), 
	CONSTRAINT ck_huy_lenh CHECK ((trang_thai = 'DaHuyLenh' AND huy_luc IS NOT NULL AND ma_nv_huy IS NOT NULL AND ly_do_huy IS NOT NULL) OR (trang_thai != 'DaHuyLenh' AND huy_luc IS NULL AND ma_nv_huy IS NULL AND ly_do_huy IS NULL)), 
	FOREIGN KEY(ma_lo) REFERENCES lo_hang (ma_lo), 
	FOREIGN KEY(ma_nv_duyet) REFERENCES nguoi_dung (ma_nv), 
	FOREIGN KEY(ma_nv_thuc_hien) REFERENCES nguoi_dung (ma_nv), 
	FOREIGN KEY(ma_nv_huy) REFERENCES nguoi_dung (ma_nv)
)

;

CREATE INDEX ix_xu_ly_rui_ro_hoan_tat_luc ON xu_ly_rui_ro (hoan_tat_luc);

CREATE INDEX ix_xu_ly_rui_ro_ma_lo ON xu_ly_rui_ro (ma_lo);

CREATE UNIQUE INDEX uq_mot_lenh_dang_cho_moi_lo ON xu_ly_rui_ro (ma_lo) WHERE trang_thai = 'ChoXuLy';