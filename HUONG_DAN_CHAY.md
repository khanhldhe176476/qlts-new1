# HƯỚNG DẪN CHẠY ỨNG DỤNG

## Cách chạy ứng dụng

### 1. Kiểm tra trước khi chạy
```bash
py test_startup.py
```

### 2. Chạy ứng dụng
```bash
py run.py
```

### 3. Mở trình duyệt
Sau khi thấy thông báo "URL dang chay: http://127.0.0.1:5000", mở trình duyệt và truy cập:

**http://127.0.0.1:5000**

hoặc

**http://localhost:5000**

### 4. Đăng nhập
- **Username:** `admin`
- **Password:** `admin123` (hoặc giá trị trong file `.env` nếu đã cấu hình)

## Xử lý lỗi thường gặp

### Lỗi: Port đã được sử dụng
Nếu port 5000 đã được sử dụng, ứng dụng sẽ tự động chuyển sang port 5050.
Truy cập: **http://127.0.0.1:5050**

### Lỗi: Module không tìm thấy
Cài đặt lại dependencies:
```bash
pip install -r requirements.txt
```

### Lỗi: Database connection
Ứng dụng sẽ tự động fallback về SQLite nếu PostgreSQL không kết nối được.
Database sẽ được tạo tự động tại: `instance/app.db`

### Lỗi: Không mở được localhost
1. Kiểm tra xem ứng dụng có đang chạy không (xem terminal)
2. Thử dùng **127.0.0.1** thay vì **localhost**
3. Kiểm tra firewall có chặn port không
4. Thử port khác bằng cách thêm vào `.env`:
   ```
   PORT=8080
   ```

## Thay đổi cấu hình

Tạo file `.env` trong thư mục gốc (copy từ `env.example`):
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./instance/app.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-password
PORT=5000
HOST=127.0.0.1
```

## Kiểm tra nhanh

Chạy script test:
```bash
py test_startup.py
```

Nếu tất cả đều [OK], ứng dụng đã sẵn sàng chạy!

