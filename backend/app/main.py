"""FastAPI application, API error mapping and optional React static files."""

import logging
import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from app import schemas
from app.database import engine
from app.config import business_today
from app.errors import BusinessError
from app.security import current_user
from app.routers import alerts, inventory, risk_action, rules, sales, reports

app = FastAPI(title="FEFO Inventory Expiry Warning", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(","),
    allow_methods=["GET", "POST", "PATCH", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(BusinessError)
async def domain_error(request, exc):
    return JSONResponse(
        status_code=exc.status, content={"detail": exc.message, "code": exc.code}
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Không trả nguyên request (có thể chứa thông tin người dùng) trong thông báo lỗi.
    errors = [
        {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": "Dữ liệu nhập chưa hợp lệ.", "errors": errors},
    )


@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    logging.getLogger(__name__).warning(
        "Ràng buộc dữ liệu bị từ chối: %s", type(exc.orig).__name__
    )
    return JSONResponse(
        status_code=409,
        content={
            "detail": "Dữ liệu bị trùng hoặc vi phạm ràng buộc. Hãy tải lại và kiểm tra thông tin."
        },
    )


@app.exception_handler(OperationalError)
async def connection_error(request, exc):
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Chưa kết nối được cơ sở dữ liệu. Kiểm tra PostgreSQL và cấu hình DATABASE_URL."
        },
    )


@app.get("/api/me", response_model=schemas.UserOut)
def me(user=Depends(current_user)):
    return user


@app.get("/api/health")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "ngay_nghiep_vu": business_today()}


for router in [
    rules.router,
    inventory.router,
    sales.router,
    alerts.router,
    risk_action.router,
    reports.router,
]:
    app.include_router(router)

# FastAPI serves the production frontend after running npm build.
dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if (dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")


@app.get("/")
def index():
    if (dist / "index.html").exists():
        return FileResponse(dist / "index.html")
    return {
        "status": "API đang chạy",
        "huong_dan": "Mở /docs để thử API hoặc build frontend theo README.",
    }
