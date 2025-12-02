# HƯỚNG DẪN MỞ TRANG WEB

## ✅ Ứng dụng đang chạy!

Ứng dụng của bạn **ĐÃ CHẠY** tại port 5000.

## 🌐 Cách mở trang web

### Cách 1: Mở trực tiếp trong trình duyệt

**Copy và paste một trong các đường dẫn sau vào thanh địa chỉ trình duyệt:**

```
http://127.0.0.1:5000
```

hoặc

```
http://localhost:5000
```

### Cách 2: Click vào link (nếu có)

Nếu bạn thấy link trong terminal, click vào đó.

### Cách 3: Dùng file batch

1. **Double-click** vào file `CHAY_UNG_DUNG.bat`
2. Chờ ứng dụng khởi động
3. Mở trình duyệt và truy cập: `http://127.0.0.1:5000`

## 🔐 Thông tin đăng nhập

- **Username:** `admin`
- **Password:** `admin123`

## ❌ Nếu vẫn không mở được

### 1. Kiểm tra ứng dụng có đang chạy

Mở **Command Prompt** hoặc **PowerShell** và chạy:
```bash
netstat -ano | findstr :5000
```

Nếu thấy output, ứng dụng đang chạy.

### 2. Thử các URL khác

- `http://127.0.0.1:5000`
- `http://localhost:5000`
- `http://0.0.0.0:5000` (không khuyến khích trên Windows)

### 3. Kiểm tra Firewall

- Tạm thời tắt Windows Firewall để test
- Hoặc thêm exception cho port 5000

### 4. Thử trình duyệt khác

- Chrome
- Firefox
- Edge
- Opera

### 5. Xóa cache trình duyệt

- Nhấn `Ctrl + Shift + Delete`
- Xóa cache và cookies
- Thử lại

### 6. Kiểm tra proxy

- Tắt proxy nếu đang bật
- Kiểm tra settings trong trình duyệt

### 7. Chạy lại ứng dụng

1. Dừng ứng dụng hiện tại (Ctrl+C trong terminal)
2. Chạy lại: `py run.py`
3. Chờ thông báo "UNG DUNG DANG CHAY TAI"
4. Mở trình duyệt

## 🔧 Kiểm tra nhanh

Mở **Command Prompt** và chạy:
```bash
curl http://127.0.0.1:5000/healthz
```

Nếu thấy `{"status":"ok"}`, ứng dụng đang chạy tốt.

## 📝 Lưu ý

- **KHÔNG** đóng cửa sổ terminal khi ứng dụng đang chạy
- Nếu đóng terminal, ứng dụng sẽ dừng
- Để chạy nền, cần cấu hình service hoặc dùng screen/tmux

## 🆘 Vẫn không được?

1. Chạy file `KIEM_TRA_VA_CHAY.bat` để kiểm tra tự động
2. Kiểm tra log trong terminal xem có lỗi gì không
3. Thử port khác bằng cách tạo file `.env`:
   ```
   PORT=8080
   HOST=127.0.0.1
   ```
   Sau đó truy cập: `http://127.0.0.1:8080`

