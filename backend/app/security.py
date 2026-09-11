"""Xác thực tối giản cho demo local; quyền lấy từ CSDL, không tin vai trò gửi lên.

HTTP Basic giúp giữ phần đăng nhập gọn theo Thư 7. Mật khẩu lưu PBKDF2;
không dùng HTTP Basic trên mạng công khai không có HTTPS.
"""

import hashlib
import secrets
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NguoiDung

basic = HTTPBasic()


from app.passwords import hash_password, verify_password


def current_user(
    credentials: HTTPBasicCredentials = Depends(basic), db: Session = Depends(get_db)
):
    user = db.query(NguoiDung).filter_by(ten_dang_nhap=credentials.username).first()
    if not user or not verify_password(credentials.password, user.mat_khau_hash):
        raise HTTPException(
            401,
            "Tên đăng nhập hoặc mật khẩu không đúng.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


def require_role(role):
    def check(user: NguoiDung = Depends(current_user)):
        if user.vai_tro != role:
            raise HTTPException(
                403, "Tài khoản không có quyền thực hiện chức năng này."
            )
        return user

    return check


manager_only = require_role("Manager")
staff_only = require_role("Staff")
