"""Băm mật khẩu bằng thư viện chuẩn; generator có thể dùng mà không chạy API."""

import hashlib
import secrets


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), 260000
    ).hex()
    return f"pbkdf2_sha256$260000${salt}${digest}"


def verify_password(password, stored):
    try:
        name, iterations, salt, expected = stored.split("$")
        if name != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), int(iterations)
        ).hex()
        return secrets.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False
