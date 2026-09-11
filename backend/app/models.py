"""Entity và ràng buộc CSDL. SQL trong database/schema.sql được xuất từ đây.

Giữ bốn lớp lõi NhomHang, SanPham, LoHang, NguoiDung; bảng giao dịch giúp
truy vết bán/kiểm kê/xử lý. Mức rủi ro được tính theo ngày, không lưu nhãn cũ.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Index,
    text,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.config import business_now, business_today
from app.errors import BusinessError


class NhomHang(Base):
    __tablename__ = "nhom_hang"
    ma_nhom = Column(String(20), primary_key=True)
    ten_nhom = Column(String(100), nullable=False)
    muc_canh_bao_vang = Column(Integer, nullable=False)
    muc_canh_bao_do = Column(Integer, nullable=False)
    __table_args__ = (
        CheckConstraint(
            "muc_canh_bao_do >= 0 AND muc_canh_bao_vang > muc_canh_bao_do",
            name="ck_nguong_hop_le",
        ),
    )

    def get_quy_tac_canh_bao(self):
        return {"vang": self.muc_canh_bao_vang, "do": self.muc_canh_bao_do}


class NguoiDung(Base):
    __tablename__ = "nguoi_dung"
    ma_nv = Column(String(20), primary_key=True)
    ho_ten = Column(String(100), nullable=False)
    ten_dang_nhap = Column(String(50), unique=True, nullable=False)
    mat_khau_hash = Column(String(255), nullable=False)
    vai_tro = Column(String(10), nullable=False)
    ngay_tao = Column(DateTime, nullable=False, default=business_now)
    __table_args__ = (
        CheckConstraint("vai_tro IN ('Manager','Staff')", name="ck_vai_tro"),
    )


class SanPham(Base):
    __tablename__ = "san_pham"
    ma_sp = Column(String(20), primary_key=True)
    barcode = Column(String(50), unique=True, nullable=False)
    ten_sp = Column(String(150), nullable=False)
    gia_ban = Column(Numeric(12, 0), nullable=False)
    ma_nhom = Column(
        String(20), ForeignKey("nhom_hang.ma_nhom"), nullable=False, index=True
    )
    dang_kinh_doanh = Column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    nhom_hang = relationship("NhomHang")
    __table_args__ = (CheckConstraint("gia_ban >= 0", name="ck_gia_ban"),)


class LoHang(Base):
    __tablename__ = "lo_hang"
    ma_lo = Column(String(40), primary_key=True)
    ma_sp = Column(String(20), ForeignKey("san_pham.ma_sp"), nullable=False, index=True)
    ngay_san_xuat = Column(Date, nullable=False)
    han_su_dung = Column(Date, nullable=False, index=True)
    ngay_nhap = Column(Date, nullable=False, default=business_today)
    so_luong_nhap = Column(Integer, nullable=False)
    so_luong_ton = Column(Integer, nullable=False)
    trang_thai = Column(String(20), nullable=False, default="DangGiaoDich")
    ty_le_giam = Column(Numeric(5, 2), nullable=False, default=0, server_default="0")
    ma_nv_nhap = Column(String(20), ForeignKey("nguoi_dung.ma_nv"), nullable=False)
    san_pham = relationship("SanPham")
    __table_args__ = (
        CheckConstraint(
            "so_luong_nhap > 0 AND so_luong_ton >= 0 AND so_luong_ton <= so_luong_nhap",
            name="ck_ton_hop_le",
        ),
        CheckConstraint(
            "ngay_san_xuat <= ngay_nhap AND ngay_nhap < han_su_dung", name="ck_ngay_lo"
        ),
        CheckConstraint("ty_le_giam >= 0 AND ty_le_giam < 100", name="ck_giam_gia_lo"),
        CheckConstraint(
            "trang_thai IN ('DangGiaoDich','DaBanHet','ChoXuatHuy','DaXuatHuy')",
            name="ck_trang_thai_lo",
        ),
        CheckConstraint(
            "(trang_thai IN ('DaBanHet','DaXuatHuy') AND so_luong_ton = 0) OR (trang_thai IN ('DangGiaoDich','ChoXuatHuy') AND so_luong_ton > 0)",
            name="ck_trang_thai_ton",
        ),
    )

    def tinh_so_ngay_con_lai(self, ngay_hien_tai=None):
        return (self.han_su_dung - (ngay_hien_tai or business_today())).days

    def cap_nhat_ton_kho(self, thay_doi):
        """Từ chối số tồn sai; không dùng max(0, ...) để che mất sai sót."""
        moi = self.so_luong_ton + thay_doi
        if not 0 <= moi <= self.so_luong_nhap:
            raise BusinessError("Số tồn phải từ 0 đến số lượng nhập của lô.")
        self.so_luong_ton = moi
        self.trang_thai = "DangGiaoDich" if moi else "DaBanHet"


class HoaDonBan(Base):
    __tablename__ = "hoa_don_ban"
    ma_hd = Column(String(40), primary_key=True)
    ma_nv = Column(String(20), ForeignKey("nguoi_dung.ma_nv"), nullable=False)
    thoi_gian_ban = Column(DateTime, nullable=False, default=business_now, index=True)
    chi_tiet_list = relationship("ChiTietBan", back_populates="hoa_don")


class ChiTietBan(Base):
    __tablename__ = "chi_tiet_ban"
    ma_ct = Column(Integer, primary_key=True, autoincrement=True)
    ma_hd = Column(
        String(40), ForeignKey("hoa_don_ban.ma_hd"), nullable=False, index=True
    )
    ma_lo = Column(String(40), ForeignKey("lo_hang.ma_lo"), nullable=False, index=True)
    so_luong = Column(Integer, nullable=False)
    don_gia = Column(Numeric(12, 0), nullable=False)
    hoa_don = relationship("HoaDonBan", back_populates="chi_tiet_list")
    __table_args__ = (
        CheckConstraint("so_luong > 0 AND don_gia >= 0", name="ck_chi_tiet_ban"),
    )


class DieuChinhTon(Base):
    __tablename__ = "dieu_chinh_ton"
    ma_dc = Column(Integer, primary_key=True, autoincrement=True)
    ma_lo = Column(String(40), ForeignKey("lo_hang.ma_lo"), nullable=False, index=True)
    so_luong_truoc = Column(Integer, nullable=False)
    so_luong_sau = Column(Integer, nullable=False)
    ly_do = Column(String(255), nullable=False)
    ma_nv = Column(String(20), ForeignKey("nguoi_dung.ma_nv"), nullable=False)
    thoi_gian = Column(DateTime, nullable=False, default=business_now)
    __table_args__ = (
        CheckConstraint(
            "so_luong_truoc >= 0 AND so_luong_sau >= 0", name="ck_dieu_chinh"
        ),
    )


class XuLyRuiRo(Base):
    __tablename__ = "xu_ly_rui_ro"
    ma_xl = Column(Integer, primary_key=True, autoincrement=True)
    ma_lo = Column(String(40), ForeignKey("lo_hang.ma_lo"), nullable=False, index=True)
    loai_xu_ly = Column(String(20), nullable=False)
    ty_le_giam = Column(Numeric(5, 2))
    so_luong = Column(Integer, nullable=False)
    gia_tham_chieu = Column(Numeric(12, 0), nullable=False)
    ma_nv_duyet = Column(String(20), ForeignKey("nguoi_dung.ma_nv"), nullable=False)
    ma_nv_thuc_hien = Column(String(20), ForeignKey("nguoi_dung.ma_nv"))
    trang_thai = Column(String(20), nullable=False, default="ChoXuLy")
    thoi_gian = Column(DateTime, nullable=False, default=business_now)
    hoan_tat_luc = Column(DateTime, index=True)
    ghi_chu = Column(String(255), nullable=False)
    huy_luc = Column(DateTime)
    ma_nv_huy = Column(String(20), ForeignKey("nguoi_dung.ma_nv"))
    ly_do_huy = Column(String(255))
    __table_args__ = (
        CheckConstraint(
            "loai_xu_ly IN ('GiamGia','XuatHuy') AND trang_thai IN ('ChoXuLy','DaHoanTat','DaHuyLenh')",
            name="ck_xu_ly",
        ),
        CheckConstraint(
            "(loai_xu_ly = 'GiamGia' AND ty_le_giam IS NOT NULL AND ty_le_giam > 0 AND ty_le_giam < 100) OR (loai_xu_ly = 'XuatHuy' AND ty_le_giam IS NULL)",
            name="ck_ty_le_xu_ly",
        ),
        CheckConstraint(
            "so_luong > 0 AND gia_tham_chieu >= 0", name="ck_so_luong_xu_ly"
        ),
        CheckConstraint(
            "(trang_thai IN ('ChoXuLy','DaHuyLenh') AND hoan_tat_luc IS NULL AND ma_nv_thuc_hien IS NULL) OR (trang_thai = 'DaHoanTat' AND hoan_tat_luc IS NOT NULL AND ma_nv_thuc_hien IS NOT NULL)",
            name="ck_hoan_tat_xu_ly",
        ),
        CheckConstraint(
            "(trang_thai = 'DaHuyLenh' AND huy_luc IS NOT NULL AND ma_nv_huy IS NOT NULL AND ly_do_huy IS NOT NULL) OR (trang_thai != 'DaHuyLenh' AND huy_luc IS NULL AND ma_nv_huy IS NULL AND ly_do_huy IS NULL)",
            name="ck_huy_lenh",
        ),
        Index(
            "uq_mot_lenh_dang_cho_moi_lo",
            "ma_lo",
            unique=True,
            postgresql_where=text("trang_thai = 'ChoXuLy'"),
            sqlite_where=text("trang_thai = 'ChoXuLy'"),
        ),
    )
