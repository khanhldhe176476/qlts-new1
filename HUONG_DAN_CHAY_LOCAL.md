# 🚀 Hướng dẫn chạy ứng dụng trên Localhost (không dùng Docker)

## ✅ Cách chạy nhanh nhất

### Phương pháp 1: Dùng file batch (Khuyến nghị)

1. Mở File Explorer
2. Điều hướng đến: `D:\QLTS\QLTSC\qlts-new8`
3. Double-click vào file: **`CHAY_UNG_DUNG.bat`**
4. Đợi server khởi động (5-10 giây)
5. Mở trình duyệt và truy cập: **http://localhost:5000**

### Phương pháp 2: Dùng Terminal

1. Mở **PowerShell** hoặc **Command Prompt**
2. Chạy lệnh:
   ```bash
   cd D:\QLTS\QLTSC\qlts-new8
   py run.py
   ```
3. Đợi thấy thông báo "Running on http://127.0.0.1:5000"
4. Mở trình duyệt: **http://localhost:5000**

## 🔐 Thông tin đăng nhập

- **URL**: http://localhost:5000
- **Username**: `admin`
- **Password**: `admin123`

## 📋 Yêu cầu

### Đã có sẵn:
- ✅ Python 3.13.2
- ✅ Flask và các dependencies đã được cài đặt

### Nếu thiếu dependencies:

Chạy lệnh sau để cài đặt:
```bash
cd D:\QLTS\QLTSC\qlts-new8
py -m pip install -r requirements.txt
```

## 🛑 Dừng ứng dụng

Trong cửa sổ Terminal đang chạy server:
- Nhấn **Ctrl + C**

## ⚠️ Lưu ý

1. **Port 5000 đã được dùng?**
   - Ứng dụng sẽ tự động chuyển sang port 5050
   - Hoặc dừng ứng dụng đang dùng port 5000

2. **Database**:
   - Sử dụng SQLite (file `instance/app.db`)
   - Tự động tạo khi chạy lần đầu

3. **Lần đầu chạy**:
   - Database sẽ được tạo tự động
   - Admin user sẽ được tạo tự động
   - Có thể mất 10-20 giây để khởi tạo

## 🔍 Kiểm tra server đã chạy chưa

Mở trình duyệt và truy cập:
- http://localhost:5000
- http://127.0.0.1:5000

Nếu thấy trang đăng nhập = ✅ Server đã chạy!

## 🐛 Troubleshooting

### Lỗi: "Module not found"
```bash
# Cài đặt lại dependencies
py -m pip install -r requirements.txt
```

### Lỗi: "Port already in use"
- Đóng ứng dụng đang dùng port 5000
- Hoặc đổi port trong file `.env`:
  ```
  PORT=5050
  ```

### Lỗi: "Cannot connect to database"
- Xóa file `instance/app.db` và chạy lại
- Hoặc kiểm tra quyền truy cập thư mục `instance/`

## 📝 File quan trọng

- **`CHAY_UNG_DUNG.bat`** - Script để chạy ứng dụng
- **`run.py`** - File chính để khởi động server
- **`config.py`** - Cấu hình ứng dụng
- **`requirements.txt`** - Danh sách dependencies

## ✅ Kết luận

Ứng dụng đã sẵn sàng chạy trên localhost!

Chỉ cần:
1. Double-click `CHAY_UNG_DUNG.bat`
2. Truy cập http://localhost:5000
3. Đăng nhập với `admin` / `admin123`



