# 🐳 Hướng dẫn nhanh - Docker Desktop

## ⚡ Bắt đầu trong 3 bước

### 1️⃣ Mở Docker Desktop
- Khởi động Docker Desktop từ Start Menu
- Đợi icon Docker ở system tray không còn loading

### 2️⃣ Mở Terminal
- Mở **PowerShell** hoặc **Command Prompt**
- Hoặc click **Terminal** trong Docker Desktop

### 3️⃣ Chạy lệnh
```bash
cd D:\QLTS\QLTSC\qlts-new8
docker-compose up --build
```

## ✅ Kiểm tra thành công

Sau khi chạy lệnh, bạn sẽ thấy:
- 3 containers chạy: `qlts-nginx`, `qlts-web`, `qlts-db`
- Logs hiển thị: "Running on http://0.0.0.0:5000"
- Truy cập: **http://localhost**

## 🎯 Truy cập ứng dụng

- **URL**: http://localhost
- **Username**: `admin`
- **Password**: `admin123`

## 🛠️ Quản lý trong Docker Desktop

### Xem containers
1. Mở Docker Desktop
2. Tab **Containers**
3. Xem 3 containers: nginx, web, db

### Xem logs
- Click vào tên container → Tab **Logs**

### Dừng containers
- Click nút **Stop** (biểu tượng vuông) ở mỗi container

### Xóa containers
- Click nút **Delete** (thùng rác) ở mỗi container

## ⚠️ Lỗi thường gặp

### Port đã được sử dụng
```bash
# Dừng containers
docker-compose down

# Hoặc đổi port trong docker-compose.yml
```

### Docker Desktop chưa chạy
- Kiểm tra icon Docker ở system tray
- Mở Docker Desktop từ Start Menu

### Build lỗi
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📚 Xem hướng dẫn chi tiết

Xem file `HUONG_DAN_DOCKER.md` để biết thêm chi tiết.



