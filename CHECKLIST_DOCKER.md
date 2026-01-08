# ✅ Checklist - Đảm bảo ứng dụng hoạt động với Docker

## ✅ Đã kiểm tra và sửa

### 1. Dockerfile ✅
- [x] Sử dụng Python 3.11-slim
- [x] Cài đặt dependencies hệ thống (gcc, postgresql-client)
- [x] Copy requirements.txt và cài đặt Python packages
- [x] Copy toàn bộ code
- [x] Tạo thư mục instance/exports
- [x] Set HOST=0.0.0.0 và PORT=5000 (quan trọng cho Docker)
- [x] Expose port 5000

### 2. docker-compose.yml ✅
- [x] Đã bỏ CACHE_BUST không cần thiết
- [x] Cấu hình 3 services: nginx, web, db
- [x] Environment variables đầy đủ
- [x] Volumes mount đúng
- [x] Health checks đã cấu hình
- [x] Networks đã setup

### 3. Dependencies ✅
- [x] requirements.txt đầy đủ
- [x] PostgreSQL driver (psycopg2-binary) đã có
- [x] Flask và các extensions đã có

### 4. Configuration ✅
- [x] config.py đọc environment variables đúng
- [x] Default values hợp lý
- [x] Database URL từ environment

### 5. Nginx ✅
- [x] nginx.conf proxy đúng đến web:5000
- [x] Health check endpoint
- [x] WebSocket support

## 🚀 Cách build và chạy

### Bước 1: Build
```bash
cd D:\QLTS\QLTSC\qlts-new8
docker compose build
```

### Bước 2: Chạy
```bash
docker compose up -d
```

### Bước 3: Kiểm tra
- Truy cập: http://localhost
- Hoặc: http://localhost:5000
- Username: `admin`
- Password: `admin123` (hoặc theo cấu hình)

## 🔍 Kiểm tra logs

```bash
# Xem logs của web service
docker compose logs -f web

# Xem logs của database
docker compose logs -f db

# Xem logs của nginx
docker compose logs -f nginx
```

## ⚠️ Lưu ý

1. **Frontend React**: 
   - Frontend React không được build trong Dockerfile hiện tại
   - Ứng dụng sử dụng Flask templates (Jinja2)
   - Nếu cần frontend React, cần build riêng hoặc thêm multi-stage build

2. **Database**:
   - Sử dụng PostgreSQL trong Docker
   - Dữ liệu được lưu trong volume `postgres_data`
   - Port 5433 exposed để local có thể kết nối

3. **Environment Variables**:
   - Có thể override trong docker-compose.yml
   - Hoặc tạo file .env (nhưng .env bị ignore trong .dockerignore)

## 🐛 Troubleshooting

### Lỗi: Cannot connect to database
```bash
# Kiểm tra database đã chạy chưa
docker compose ps db

# Xem logs database
docker compose logs db
```

### Lỗi: Port already in use
```bash
# Dừng service đang dùng port
# Hoặc đổi port trong docker-compose.yml
```

### Lỗi: Permission denied
```bash
# Trên Windows thường không có vấn đề này
# Trên Linux/Mac:
sudo chown -R $USER:$USER instance/
```

## ✅ Kết luận

Tất cả các file đã được kiểm tra và sửa. Ứng dụng sẵn sàng để build và chạy với Docker!



