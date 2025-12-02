@echo off
chcp 65001 >nul
echo ========================================
echo TẠO FILE .ENV CHO CẤU HÌNH EMAIL
echo ========================================
echo.

if exist .env (
    echo File .env đã tồn tại!
    echo Bạn có muốn ghi đè không? (Y/N)
    set /p overwrite=
    if /i not "%overwrite%"=="Y" (
        echo Đã hủy.
        pause
        exit /b
    )
)

echo Đang tạo file .env...
echo.

(
echo # Database Configuration
echo DATABASE_URL=sqlite:///./instance/app.db
echo SECRET_KEY=dev-key-change-in-production
echo.
echo # Flask Configuration
echo FLASK_ENV=development
echo FLASK_DEBUG=True
echo.
echo # Email Configuration ^(for asset transfer confirmation^)
echo # ====================================================
echo # VUI LÒNG ĐIỀN THÔNG TIN EMAIL CỦA BẠN VÀO ĐÂY:
echo # ====================================================
echo.
echo MAIL_SERVER=smtp.gmail.com
echo MAIL_PORT=587
echo MAIL_USE_TLS=True
echo MAIL_USERNAME=your-email@gmail.com
echo MAIL_PASSWORD=your-app-password
echo MAIL_DEFAULT_SENDER=your-email@gmail.com
echo APP_URL=http://localhost:5000
echo.
echo # HƯỚNG DẪN CẤU HÌNH GMAIL:
echo # 1. Bật 2-Step Verification trong Google Account -^> Security
echo # 2. Tạo App Password: Google Account -^> Security -^> App passwords
echo #    - Chọn "Mail" và "Other ^(Custom name^)"
echo #    - Nhập tên: "Quản lý tài sản"
echo #    - Copy password 16 ký tự
echo #    - Dán vào MAIL_PASSWORD ở trên
echo # 3. Thay "your-email@gmail.com" bằng email thật của bạn
echo # 4. Lưu file này
echo # 5. Restart ứng dụng để áp dụng cấu hình mới
) > .env

echo ✅ Đã tạo file .env thành công!
echo.
echo 📝 Vui lòng mở file .env và điền thông tin email của bạn:
echo    - MAIL_USERNAME
echo    - MAIL_PASSWORD (App Password từ Gmail)
echo    - MAIL_DEFAULT_SENDER
echo.
echo 📖 Xem hướng dẫn chi tiết trong file: HUONG_DAN_CAU_HINH_EMAIL.md
echo.
pause

