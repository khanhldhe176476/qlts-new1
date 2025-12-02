# Hướng Dẫn Sử Dụng Tính Năng Bàn Giao Tài Sản

## Tổng Quan

Tính năng bàn giao tài sản cho phép chuyển giao tài sản giữa các nhân viên với xác nhận qua email. Khi nhân viên xác nhận đầy đủ số lượng thiết bị, hệ thống sẽ tự động cập nhật quyền sở hữu.

## Quy Trình Bàn Giao

### 1. Tạo Yêu Cầu Bàn Giao

1. Đăng nhập vào hệ thống
2. Vào menu **"Bàn giao tài sản"** → **"Tạo bàn giao mới"**
3. Điền thông tin:
   - **Tài sản bàn giao**: Chọn tài sản cần bàn giao
   - **Người nhận**: Chọn nhân viên sẽ nhận tài sản
   - **Số lượng**: Nhập số lượng thiết bị cần bàn giao
   - **Ghi chú**: (Tùy chọn) Thông tin bổ sung
4. Click **"Gửi yêu cầu bàn giao"**

### 2. Hệ Thống Gửi Email

- Hệ thống tự động gửi email đến người nhận
- Email chứa:
  - Mã bàn giao
  - Thông tin tài sản
  - Số lượng dự kiến
  - Link xác nhận (có hiệu lực 7 ngày)

### 3. Người Nhận Xác Nhận

1. Người nhận mở email và click vào link xác nhận
2. Kiểm tra thông tin bàn giao
3. Nhập số lượng thiết bị thực tế nhận được
4. Click **"Xác nhận bàn giao"**

### 4. Tự Động Cập Nhật

Khi người nhận xác nhận **đầy đủ** số lượng:
- ✅ Giảm số lượng tài sản của người gửi
- ✅ Tăng số lượng tài sản của người nhận (hoặc tạo mới nếu chưa có)
- ✅ Cập nhật trạng thái bàn giao thành "Đã xác nhận"
- ✅ Ghi nhận trong audit log

## Cấu Hình Email

Để sử dụng tính năng gửi email, cần cấu hình trong file `.env`:

```env
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
APP_URL=http://localhost:5000
```

### Cấu hình Gmail:

1. Bật 2-Step Verification
2. Tạo App Password:
   - Vào Google Account → Security
   - App passwords → Generate
   - Copy password và dán vào `MAIL_PASSWORD`

### Cấu hình Email khác:

- **Outlook**: `smtp-mail.outlook.com`, port 587
- **Yahoo**: `smtp.mail.yahoo.com`, port 587
- **Custom SMTP**: Cấu hình theo hướng dẫn của nhà cung cấp

## Trạng Thái Bàn Giao

- **pending**: Chờ xác nhận
- **confirmed**: Đã xác nhận đầy đủ
- **rejected**: Đã từ chối
- **cancelled**: Đã hủy

## Tính Năng

### ✅ Đã Hoàn Thành

- Tạo yêu cầu bàn giao
- Gửi email xác nhận với token bảo mật
- Xác nhận qua link trong email
- Tự động cập nhật tài sản khi xác nhận đầy đủ
- Hỗ trợ xác nhận từng phần (có thể xác nhận nhiều lần)
- Token có thời hạn 7 ngày
- Audit log cho mọi thao tác
- Phân quyền: User chỉ thấy bàn giao của mình

### 🔄 Có Thể Mở Rộng

- Gửi email thông báo cho người gửi khi xác nhận
- Cho phép từ chối bàn giao
- Hủy bàn giao
- Xem chi tiết bàn giao
- Export danh sách bàn giao

## Lưu Ý

1. **Email phải được cấu hình đúng** để gửi email xác nhận
2. **Link xác nhận có hiệu lực 7 ngày** - sau đó sẽ hết hạn
3. **Chỉ xác nhận đầy đủ mới cập nhật tài sản** - xác nhận từng phần chỉ lưu tiến độ
4. **Người nhận có thể xác nhận nhiều lần** để cập nhật số lượng
5. **Tài sản sẽ tự động merge** nếu người nhận đã có tài sản tương tự

## Troubleshooting

### Email không gửi được:
- Kiểm tra cấu hình SMTP trong `.env`
- Kiểm tra App Password (Gmail)
- Kiểm tra firewall/network
- Xem log trong console để biết lỗi chi tiết

### Link xác nhận không hoạt động:
- Kiểm tra token còn hiệu lực (7 ngày)
- Kiểm tra URL đúng format
- Kiểm tra database connection

### Tài sản không cập nhật:
- Đảm bảo đã xác nhận đầy đủ số lượng
- Kiểm tra số lượng tài sản gốc còn đủ
- Xem audit log để kiểm tra

