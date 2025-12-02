#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test cấu hình email SMTP
"""
import sys
import os
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv

# Load .env file
load_dotenv()

from utils.email_sender import send_email_from_config
from config import Config

def test_email_config():
    """Test cấu hình email"""
    print("=" * 60)
    print("KIEM TRA CAU HINH EMAIL")
    print("=" * 60)
    print()
    
    # Lấy config từ environment
    email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() in ('1', 'true', 'yes')
    mail_server = os.getenv('MAIL_SERVER', '')
    mail_port = int(os.getenv('MAIL_PORT', 587))
    mail_use_ssl = os.getenv('MAIL_USE_SSL', 'False').lower() in ('1', 'true', 'yes')
    mail_use_tls = os.getenv('MAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
    mail_username = os.getenv('MAIL_USERNAME', '')
    mail_password = os.getenv('MAIL_PASSWORD', '')
    mail_sender = os.getenv('MAIL_DEFAULT_SENDER', mail_username)
    
    print("Cấu hình hiện tại:")
    print(f"  EMAIL_ENABLED: {email_enabled}")
    print(f"  MAIL_SERVER: {mail_server}")
    print(f"  MAIL_PORT: {mail_port}")
    print(f"  MAIL_USE_SSL: {mail_use_ssl}")
    print(f"  MAIL_USE_TLS: {mail_use_tls}")
    print(f"  MAIL_USERNAME: {mail_username}")
    print(f"  MAIL_PASSWORD: {'*' * len(mail_password) if mail_password else '(trống)'}")
    print(f"  MAIL_DEFAULT_SENDER: {mail_sender}")
    print()
    
    if not email_enabled:
        print("❌ EMAIL_ENABLED = false. Vui lòng bật trong .env")
        return False
    
    if not mail_server or not mail_username or not mail_password:
        print("❌ Thiếu thông tin cấu hình (MAIL_SERVER, MAIL_USERNAME, hoặc MAIL_PASSWORD)")
        return False
    
    # Test gửi email
    print("Đang thử gửi email test...")
    print(f"  Từ: {mail_sender}")
    print(f"  Đến: {mail_username} (test)")
    print()
    
    # Tạo config dict để test
    test_config = {
        'EMAIL_ENABLED': email_enabled,
        'MAIL_SERVER': mail_server,
        'MAIL_PORT': mail_port,
        'MAIL_USE_TLS': mail_use_tls,
        'MAIL_USE_SSL': mail_use_ssl,
        'MAIL_USERNAME': mail_username,
        'MAIL_PASSWORD': mail_password,
        'MAIL_DEFAULT_SENDER': mail_sender
    }
    
    try:
        success, message = send_email_from_config(
            to_emails=[mail_username],  # Gửi cho chính mình để test
            subject="[TEST] Kiểm tra cấu hình email",
            body_text="Đây là email test để kiểm tra cấu hình SMTP.",
            body_html="<p>Đây là email test để kiểm tra cấu hình SMTP.</p>",
            config=test_config
        )
        
        if success:
            print("✅ GỬI EMAIL THÀNH CÔNG!")
            print(f"   {message}")
            print()
            print("Cấu hình email đã đúng. Bạn có thể sử dụng tính năng gửi email.")
        else:
            print("❌ GỬI EMAIL THẤT BẠI!")
            print(f"   Lỗi: {message}")
            print()
            print("Nguyên nhân có thể:")
            print("  1. App password không đúng hoặc đã hết hạn")
            print("  2. Cấu hình SMTP (port, SSL/TLS) không khớp với nhà cung cấp")
            print("  3. Tài khoản email bị khóa hoặc chưa bật SMTP")
            print()
            print("Vui lòng kiểm tra lại:")
            print("  - App password trong Yandex ID Security")
            print("  - Cấu hình trong file .env")
            return False
        
    except Exception as e:
        print("❌ LỖI KHI GỬI EMAIL!")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 60)
    return success

if __name__ == '__main__':
    test_email_config()

