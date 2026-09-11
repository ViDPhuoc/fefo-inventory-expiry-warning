# Build React riêng, chỉ chuyển tài nguyên đã build sang ứng dụng Python.
FROM node:22-alpine AS ui
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /project
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY backend /project/backend
COPY scripts /project/scripts
COPY database /project/database
COPY --from=ui /frontend/dist /project/frontend/dist
WORKDIR /project/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
