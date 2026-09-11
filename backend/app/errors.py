"""Lỗi nghiệp vụ có thông điệp rõ ràng cho người dùng, tách khỏi lỗi kỹ thuật."""


class BusinessError(Exception):
    def __init__(self, message, status=400, code="INVALID_OPERATION"):
        super().__init__(message)
        self.message, self.status, self.code = message, status, code
