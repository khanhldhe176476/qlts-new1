# 🔧 Sửa lỗi ERR_CONNECTION_REFUSED

## ❌ Lỗi gặp phải

```
ERR_CONNECTION_REFUSED
localhost đã từ chối kết nối
```

## 🔍 Nguyên nhân

1. **Docker Desktop chưa chạy** (phổ biến nhất)
2. Containers chưa được start
3. Ứng dụng chưa build hoặc build lỗi

## ✅ Cách sửa

### Bước 1: Khởi động Docker Desktop

1. Mở **Docker Desktop** từ Start Menu
2. Đợi Docker Desktop khởi động hoàn toàn
3. Kiểm tra icon Docker ở system tray (góc dưới bên phải)
   - Icon đang quay = đang khởi động
   - Icon tĩnh = đã sẵn sàng

### Bước 2: Kiểm tra Docker đã chạy

Mở Terminal và chạy:
```bash
docker ps
```

Nếu thấy lỗi "Cannot connect to Docker daemon" = Docker Desktop chưa chạy.

### Bước 3: Build và chạy containers

```bash
cd D:\QLTS\QLTSC\qlts-new8

# Build images
docker compose build

# Chạy containers
docker compose up -d
```

### Bước 4: Kiểm tra containers đang chạy

```bash
docker compose ps
```

Phải thấy 3 containers:
- `qlts-nginx` - Status: Up
- `qlts-web` - Status: Up  
- `qlts-db` - Status: Up

### Bước 5: Kiểm tra logs

```bash
# Xem logs của web service
docker compose logs web

# Nếu có lỗi, xem chi tiết
docker compose logs -f web
```

## 🚀 Script tự động

Chạy file `rebuild-docker.bat`:
```bash
cd D:\QLTS\QLTSC\qlts-new8
rebuild-docker.bat
```

## ⚠️ Lưu ý

1. **Docker Desktop phải chạy trước** khi dùng docker commands
2. **Đợi Docker Desktop khởi động xong** (có thể mất 1-2 phút)
3. **Kiểm tra system tray** để biết Docker đã sẵn sàng chưa

## 🔍 Troubleshooting

### Lỗi: "Cannot connect to Docker daemon"
→ Docker Desktop chưa chạy. Mở Docker Desktop và đợi khởi động xong.

### Lỗi: "Port already in use"
→ Port 80 hoặc 5000 đã được dùng. Dừng service đang dùng port đó.

### Container không start
```bash
# Xem logs để biết lỗi
docker compose logs web

# Restart containers
docker compose restart
```

### Build lỗi
```bash
# Rebuild với --no-cache
docker compose build --no-cache
docker compose up -d
```

## ✅ Sau khi sửa xong

Truy cập:
- **http://localhost** (qua Nginx, port 80)
- **http://localhost:5000** (trực tiếp Flask)

Username: `admin`
Password: `admin123`



