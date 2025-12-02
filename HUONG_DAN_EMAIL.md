# Hướng dẫn Gửi Email và Xác thực Email

## 1. Cấu hình Email (SMTP)

### Thiết lập trong file `.env`:

```env
EMAIL_ENABLED=true
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

### Cấu hình cho Gmail:

1. **Bật xác thực 2 bước** cho tài khoản Gmail
2. **Tạo Mật khẩu Ứng dụng**:
   - Vào: https://myaccount.google.com/apppasswords
   - Chọn "Ứng dụng" và "Thiết bị"
   - Copy mật khẩu ứng dụng (16 ký tự)
   - Sử dụng mật khẩu này trong `MAIL_PASSWORD`

### Cấu hình cho các nhà cung cấp khác:

**Outlook/Hotmail:**
```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
```

**Yahoo:**
```env
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=true
```

**SMTP tùy chỉnh:**
```env
MAIL_SERVER=smtp.yourdomain.com
MAIL_PORT=587
MAIL_USE_TLS=true
# hoặc
MAIL_PORT=465
MAIL_USE_SSL=true
```

## 2. Sử dụng Module Gửi Email

### Import module:

```python
from utils.email_sender import send_email, send_email_from_config
```

### Gửi email cơ bản:

```python
success, message = send_email(
    smtp_server='smtp.gmail.com',
    smtp_port=587,
    username='your_email@gmail.com',
    password='your_app_password',
    from_email='your_email@gmail.com',
    to_emails=['recipient@example.com'],
    subject='Tiêu đề email',
    body_text='Nội dung email dạng text',
    body_html='<h1>Nội dung email dạng HTML</h1>',
    use_tls=True
)
```

### Gửi email từ Flask config:

```python
success, message = send_email_from_config(
    to_emails=['recipient@example.com'],
    subject='Tiêu đề email',
    body_text='Nội dung email',
    body_html='<p>Nội dung HTML</p>',
    attachments=['/path/to/file.pdf']  # Tùy chọn
)
```

## 3. Xác thực Email

### Import module:

```python
from utils.email_validator import (
    validate_email_syntax,
    check_mx_record,
    validate_email_full,
    validate_email_with_api
)
```

### Kiểm tra cú pháp email:

```python
is_valid, message = validate_email_syntax('user@example.com')
if is_valid:
    print("Email hợp lệ")
else:
    print(f"Lỗi: {message}")
```

### Kiểm tra bản ghi MX:

```python
has_mx, message, mx_records = check_mx_record('example.com')
if has_mx:
    print(f"Tìm thấy MX records: {mx_records}")
```

### Xác thực đầy đủ:

```python
result = validate_email_full('user@example.com', check_mx=True)
print(f"Valid: {result['valid']}")
print(f"Syntax valid: {result['syntax_valid']}")
print(f"MX valid: {result['mx_valid']}")
print(f"Messages: {result['messages']}")
```

### Xác thực bằng API (ZeroBounce):

```python
result = validate_email_with_api(
    email='user@example.com',
    api_key='your_zerobounce_api_key',
    api_provider='zerobounce'
)
print(f"Valid: {result['valid']}")
print(f"Status: {result.get('status')}")
```

## 4. Test Gửi Email

### Truy cập trang test:

- **Gửi email:** http://localhost:5000/test/email/send
- **Xác thực email:** http://localhost:5000/test/email/validate

### Sử dụng trong code:

```python
# Trong route Flask
from utils.email_sender import send_email_from_config

@app.route('/send-notification')
def send_notification():
    success, message = send_email_from_config(
        to_emails=['user@example.com'],
        subject='Thông báo',
        body_html='<h1>Nội dung thông báo</h1>'
    )
    if success:
        flash('Email đã được gửi thành công', 'success')
    else:
        flash(f'Lỗi: {message}', 'error')
    return redirect(url_for('index'))
```

## 5. Cài đặt Dependencies

```bash
pip install dnspython requests
```

Hoặc cài đặt từ requirements.txt:

```bash
pip install -r requirements.txt
```

## 6. Xử lý Lỗi

Module tự động xử lý các lỗi phổ biến:
- Lỗi xác thực SMTP
- Địa chỉ email không hợp lệ
- Máy chủ SMTP ngắt kết nối
- Lỗi khi đính kèm file

Tất cả lỗi đều được log và trả về message rõ ràng.

## 7. Bảo mật

- **Không commit** file `.env` vào git
- Sử dụng **Mật khẩu Ứng dụng** thay vì mật khẩu chính
- Lưu trữ API keys an toàn
- Sử dụng TLS/SSL để mã hóa kết nối



