"""
Module gửi email sử dụng smtplib và email.mime
Hỗ trợ gửi email với nội dung text, HTML và file đính kèm
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def send_email(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    from_email: str,
    to_emails: List[str],
    subject: str,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    use_tls: bool = True,
    use_ssl: bool = False
) -> Tuple[bool, str]:
    """
    Gửi email sử dụng SMTP
    
    Args:
        smtp_server: Địa chỉ máy chủ SMTP (ví dụ: smtp.gmail.com)
        smtp_port: Cổng SMTP (thường là 587 cho TLS, 465 cho SSL)
        username: Tên đăng nhập SMTP
        password: Mật khẩu hoặc App Password
        from_email: Địa chỉ email người gửi
        to_emails: Danh sách địa chỉ email người nhận
        subject: Tiêu đề email
        body_text: Nội dung email dạng text (tùy chọn)
        body_html: Nội dung email dạng HTML (tùy chọn)
        attachments: Danh sách đường dẫn file đính kèm (tùy chọn)
        use_tls: Sử dụng TLS (mặc định True)
        use_ssl: Sử dụng SSL (mặc định False)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Tạo message
        msg = MIMEMultipart('alternative')
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        # Thêm nội dung text
        if body_text:
            part_text = MIMEText(body_text, 'plain', 'utf-8')
            msg.attach(part_text)
        
        # Thêm nội dung HTML
        if body_html:
            part_html = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part_html)
        
        # Nếu không có nội dung nào, thêm nội dung mặc định
        if not body_text and not body_html:
            part_text = MIMEText('', 'plain', 'utf-8')
            msg.attach(part_text)
        
        # Thêm file đính kèm
        if attachments:
            for file_path in attachments:
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            
                            filename = os.path.basename(file_path)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {filename}'
                            )
                            msg.attach(part)
                    except Exception as e:
                        logger.warning(f"Không thể đính kèm file {file_path}: {e}")
        
        # Kết nối và gửi email
        if use_ssl:
            # Sử dụng SSL
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            # Sử dụng TLS
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
        
        # Xác thực
        server.login(username, password)
        
        # Gửi email
        server.sendmail(from_email, to_emails, msg.as_string())
        
        # Đóng kết nối
        server.quit()
        
        return True, "Email đã được gửi thành công"
    
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Lỗi xác thực SMTP: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    
    except smtplib.SMTPRecipientsRefused as e:
        error_msg = f"Địa chỉ email người nhận không hợp lệ: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    
    except smtplib.SMTPServerDisconnected as e:
        error_msg = f"Máy chủ SMTP đã ngắt kết nối: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    
    except Exception as e:
        error_msg = f"Lỗi khi gửi email: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def send_email_from_config(
    to_emails: List[str],
    subject: str,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    config: Optional[object] = None
) -> Tuple[bool, str]:
    """
    Gửi email sử dụng cấu hình từ Flask config
    
    Args:
        to_emails: Danh sách địa chỉ email người nhận
        subject: Tiêu đề email
        body_text: Nội dung email dạng text (tùy chọn)
        body_html: Nội dung email dạng HTML (tùy chọn)
        attachments: Danh sách đường dẫn file đính kèm (tùy chọn)
        config: Đối tượng config Flask (tùy chọn, sẽ lấy từ app nếu không có)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if config is None:
        from flask import current_app
        config = current_app.config
    
    # Kiểm tra email có được bật không
    if not config.get('EMAIL_ENABLED', False):
        return False, "Chức năng email chưa được bật trong cấu hình"
    
    # Lấy thông tin cấu hình
    smtp_server = config.get('MAIL_SERVER', '')
    smtp_port = config.get('MAIL_PORT', 587)
    username = config.get('MAIL_USERNAME', '')
    password = config.get('MAIL_PASSWORD', '')
    from_email = config.get('MAIL_DEFAULT_SENDER', username)
    use_tls = config.get('MAIL_USE_TLS', True)
    use_ssl = config.get('MAIL_USE_SSL', False)
    
    # Kiểm tra cấu hình đầy đủ
    if not smtp_server or not username or not password:
        return False, "Cấu hình email chưa đầy đủ. Vui lòng kiểm tra MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD"
    
    return send_email(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        username=username,
        password=password,
        from_email=from_email,
        to_emails=to_emails,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachments=attachments,
        use_tls=use_tls,
        use_ssl=use_ssl
    )

