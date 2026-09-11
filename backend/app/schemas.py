"""Dữ liệu API: kiểm tra ngay tại đầu vào trước khi chạm đến tồn kho."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

PositiveInt = Annotated[int, Field(gt=0, strict=True)]
NonnegativeInt = Annotated[int, Field(ge=0, strict=True)]
Code = Annotated[str, Field(min_length=1, max_length=40)]
Reason = Annotated[str, Field(min_length=3, max_length=255)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class NhomHangUpdate(InputModel):
    muc_canh_bao_vang: PositiveInt
    muc_canh_bao_do: NonnegativeInt

    @model_validator(mode="after")
    def ordered(self):
        if self.muc_canh_bao_do >= self.muc_canh_bao_vang:
            raise ValueError("Ngưỡng Đỏ phải nhỏ hơn ngưỡng Vàng.")
        return self


class LoHangCreate(InputModel):
    ma_sp: Code
    ngay_san_xuat: date
    han_su_dung: date
    so_luong_nhap: PositiveInt


class DieuChinhTonRequest(InputModel):
    so_luong_thuc_te: NonnegativeInt
    ly_do: Reason


class BanHangRequest(InputModel):
    barcode: Annotated[str, Field(min_length=1, max_length=50)]
    so_luong: PositiveInt


class XuLyRuiRoRequest(InputModel):
    loai_xu_ly: Literal["GiamGia", "XuatHuy"]
    ty_le_giam: (
        Annotated[Decimal, Field(gt=0, lt=100, max_digits=5, decimal_places=2)] | None
    ) = None
    ghi_chu: Reason

    @model_validator(mode="after")
    def discount_matches(self):
        if (self.loai_xu_ly == "GiamGia") != (self.ty_le_giam is not None):
            raise ValueError("Giảm giá cần tỷ lệ; xuất hủy không được có tỷ lệ giảm.")
        return self


class OutModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserOut(OutModel):
    ma_nv: str
    ho_ten: str
    vai_tro: str


class NhomHangOut(OutModel):
    ma_nhom: str
    ten_nhom: str
    muc_canh_bao_vang: int
    muc_canh_bao_do: int


class SanPhamOut(OutModel):
    ma_sp: str
    barcode: str
    ten_sp: str
    gia_ban: Decimal
    ma_nhom: str


class LoHangOut(OutModel):
    ma_lo: str
    ma_sp: str
    ngay_san_xuat: date
    han_su_dung: date
    ngay_nhap: date
    so_luong_nhap: int
    so_luong_ton: int
    trang_thai: str
    ty_le_giam: Decimal


class XuLyRuiRoOut(OutModel):
    ma_xl: int
    ma_lo: str
    loai_xu_ly: str
    ty_le_giam: Decimal | None
    so_luong: int
    gia_tham_chieu: Decimal
    ma_nv_duyet: str
    ma_nv_thuc_hien: str | None
    trang_thai: str
    thoi_gian: datetime
    hoan_tat_luc: datetime | None
    ghi_chu: str
    huy_luc: datetime | None
    ma_nv_huy: str | None
    ly_do_huy: str | None


class HuyLenhRequest(InputModel):
    ly_do: Reason
