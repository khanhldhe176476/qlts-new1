# Khắc Phục: Không Nhận Được Email

## Bước 1: Kiểm Tra Cấu Hình Email

Chạy script debug để kiểm tra:

```bash
python debug_email.py --check
```

Hoặc test gửi email:

```bash
python debug_email.py your-email@example.com
```

## Bước 2: Kiểm Tra File .env

Đảm bảo file `.env` trong thư mục `QLTaiSan` có đầy đủ:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
APP_URL=http://localhost:5000
```

### Nếu dùng Gmail:

1. **Bật 2-Step Verification**:
   - Vào Google Account → Security
   - Bật "2-Step Verification"

2. **Tạo App Password**:
   - Vào Google Account → Security → App passwords
   - Chọn "Mail" và "Other (Custom name)"
   - Nhập tên: "Quản lý tài sản"
   - Copy password 16 ký tự
   - Dán vào `MAIL_PASSWORD` trong file `.env`

**LƯU Ý**: Không dùng mật khẩu thông thường của Gmail, phải dùng App Password!

## Bước 3: Kiểm Tra Email Đã Gửi

### Kiểm tra trong Gmail:

1. **Hộp thư đến** - Kiểm tra email mới nhất
2. **Thư mục SPAM** - Email có thể bị vào đây
3. **Thư mục "Quảng cáo"** - Trong Gmail
4. **Thư mục "Cập nhật"** - Trong Gmail
5. **Tìm kiếm**: Tìm "Test Email" hoặc "Xác nhận bàn giao"

### Kiểm tra log trong console:

Khi chạy ứng dụng, xem log trong console:
- `[EMAIL] ✅ Đã gửi email đến...` → Email đã được gửi
- `[EMAIL] ❌ Lỗi khi gửi email...` → Có lỗi, xem chi tiết

## Bước 4: Test Gửi Email

### Cách 1: Dùng script debug
```bash
python debug_email.py your-email@example.com
```

### Cách 2: Dùng trang web
1. Vào "Bàn giao tài sản" → "Gửi Email"
2. Chọn nhân viên
3. Click "Gửi Email"
4. Kiểm tra thông báo thành công

### Cách 3: Tạo bàn giao
1. Tạo bàn giao tài sản mới
2. Chọn nhân viên có email
3. Email sẽ tự động gửi

## Bước 5: Xử Lý Lỗi Thường Gặp

### Lỗi: "Authentication failed"
- **Nguyên nhân**: App Password không đúng
- **Giải pháp**: Tạo lại App Password và cập nhật trong `.env`

### Lỗi: "Connection refused" hoặc "Connection timeout"
- **Nguyên nhân**: Firewall chặn port 587
- **Giải pháp**: 
  - Kiểm tra firewall
  - Thử dùng port 465 với `MAIL_USE_SSL=True`

### Lỗi: "Email chưa được cấu hình"
- **Nguyên nhân**: Thiếu thông tin trong `.env`
- **Giải pháp**: Kiểm tra lại file `.env` có đầy đủ thông tin

### Email không đến nhưng không có lỗi
- **Nguyên nhân**: Email bị spam filter chặn
- **Giải pháp**:
  - Kiểm tra thư mục SPAM
  - Thêm email gửi vào danh sách contacts
  - Kiểm tra sau vài phút (có thể bị delay)

## Bước 6: Kiểm Tra Log Chi Tiết

Xem log trong console khi chạy ứng dụng để biết:
- Email có được gửi không
- Lỗi cụ thể là gì
- Thông tin kết nối SMTP

## Bước 7: Test Với Email Khác

Thử gửi đến email khác để xác định:
- Vấn đề với email cụ thể
- Hay vấn đề với cấu hình chung

## Lưu Ý Quan Trọng

1. **App Password Gmail**: Phải dùng App Password, không dùng mật khẩu thông thường
2. **Đợi vài phút**: Email có thể bị delay 1-5 phút
3. **Kiểm tra SPAM**: Luôn kiểm tra thư mục SPAM trước
4. **Restart ứng dụng**: Sau khi thay đổi `.env`, cần restart ứng dụng
5. **Kiểm tra internet**: Đảm bảo server có kết nối internet

## Liên Hệ Hỗ Trợ

Nếu vẫn không nhận được email sau khi đã thử các bước trên:
1. Chạy `python debug_email.py your-email@example.com` và gửi kết quả
2. Kiểm tra log trong console và gửi lỗi cụ thể
3. Kiểm tra file `.env` (ẩn thông tin nhạy cảm trước khi gửi)

