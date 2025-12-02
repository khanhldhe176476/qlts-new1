"""
Module xác thực email
Hỗ trợ kiểm tra cú pháp email và xác minh tên miền MX
"""
import re
import dns.resolver
import socket
from typing import Tuple, Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Regex pattern để kiểm tra cú pháp email cơ bản
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


def validate_email_syntax(email: str) -> Tuple[bool, str]:
    """
    Kiểm tra cú pháp địa chỉ email cơ bản
    
    Args:
        email: Địa chỉ email cần kiểm tra
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not email or not isinstance(email, str):
        return False, "Địa chỉ email không hợp lệ"
    
    email = email.strip()
    
    if not email:
        return False, "Địa chỉ email không được để trống"
    
    if len(email) > 254:  # RFC 5321 limit
        return False, "Địa chỉ email quá dài (tối đa 254 ký tự)"
    
    if not EMAIL_PATTERN.match(email):
        return False, "Địa chỉ email không đúng định dạng"
    
    # Kiểm tra phần local (trước @) không quá 64 ký tự
    local_part = email.split('@')[0]
    if len(local_part) > 64:  # RFC 5321 limit
        return False, "Phần tên email (trước @) quá dài (tối đa 64 ký tự)"
    
    return True, "Cú pháp email hợp lệ"


def check_mx_record(domain: str) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
    """
    Kiểm tra bản ghi MX (Mail Exchange) của tên miền
    
    Args:
        domain: Tên miền cần kiểm tra (ví dụ: gmail.com)
    
    Returns:
        tuple: (has_mx: bool, message: str, mx_records: list or None)
    """
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_list = []
        for mx in mx_records:
            mx_list.append({
                'priority': mx.preference,
                'exchange': str(mx.exchange)
            })
        
        if mx_list:
            return True, f"Tìm thấy {len(mx_list)} bản ghi MX", mx_list
        else:
            return False, "Không tìm thấy bản ghi MX", None
    
    except dns.resolver.NXDOMAIN:
        return False, f"Tên miền '{domain}' không tồn tại", None
    
    except dns.resolver.NoAnswer:
        return False, f"Tên miền '{domain}' không có bản ghi MX", None
    
    except dns.resolver.Timeout:
        return False, "Timeout khi kiểm tra bản ghi MX", None
    
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra MX record: {e}")
        return False, f"Lỗi khi kiểm tra bản ghi MX: {str(e)}", None


def validate_email_full(email: str, check_mx: bool = True) -> Dict[str, Any]:
    """
    Xác thực email đầy đủ: kiểm tra cú pháp và bản ghi MX
    
    Args:
        email: Địa chỉ email cần kiểm tra
        check_mx: Có kiểm tra bản ghi MX không (mặc định True)
    
    Returns:
        dict: {
            'valid': bool,
            'syntax_valid': bool,
            'mx_valid': bool,
            'domain': str,
            'messages': list,
            'mx_records': list or None
        }
    """
    result = {
        'valid': False,
        'syntax_valid': False,
        'mx_valid': False,
        'domain': '',
        'messages': [],
        'mx_records': None
    }
    
    # Kiểm tra cú pháp
    syntax_valid, syntax_msg = validate_email_syntax(email)
    result['syntax_valid'] = syntax_valid
    result['messages'].append(syntax_msg)
    
    if not syntax_valid:
        return result
    
    # Lấy tên miền
    try:
        domain = email.split('@')[1]
        result['domain'] = domain
    except IndexError:
        result['messages'].append("Không thể tách tên miền từ email")
        return result
    
    # Kiểm tra MX nếu được yêu cầu
    if check_mx:
        mx_valid, mx_msg, mx_records = check_mx_record(domain)
        result['mx_valid'] = mx_valid
        result['messages'].append(mx_msg)
        result['mx_records'] = mx_records
    
    # Email hợp lệ nếu cú pháp đúng và (không cần MX hoặc MX hợp lệ)
    result['valid'] = syntax_valid and (not check_mx or result['mx_valid'])
    
    return result


def validate_email_with_api(email: str, api_key: Optional[str] = None, api_provider: str = 'zerobounce') -> Dict[str, Any]:
    """
    Xác thực email sử dụng API của dịch vụ bên thứ ba (ZeroBounce, etc.)
    
    Args:
        email: Địa chỉ email cần kiểm tra
        api_key: API key của dịch vụ (tùy chọn)
        api_provider: Nhà cung cấp dịch vụ ('zerobounce', 'emailvalidator', etc.)
    
    Returns:
        dict: Kết quả xác thực từ API
    """
    if not api_key:
        return {
            'valid': False,
            'error': 'API key không được cung cấp',
            'provider': api_provider
        }
    
    try:
        import requests
        
        if api_provider.lower() == 'zerobounce':
            # ZeroBounce API
            url = 'https://api.zerobounce.net/v2/validate'
            params = {
                'api_key': api_key,
                'email': email
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'valid': data.get('status') in ['valid', 'catch-all'],
                'status': data.get('status'),
                'sub_status': data.get('sub_status'),
                'account': data.get('account'),
                'domain': data.get('domain'),
                'did_you_mean': data.get('did_you_mean'),
                'provider': 'zerobounce',
                'raw_response': data
            }
        
        else:
            return {
                'valid': False,
                'error': f'Nhà cung cấp "{api_provider}" chưa được hỗ trợ',
                'provider': api_provider
            }
    
    except ImportError:
        return {
            'valid': False,
            'error': 'Thư viện requests chưa được cài đặt. Chạy: pip install requests',
            'provider': api_provider
        }
    
    except Exception as e:
        logger.error(f"Lỗi khi gọi API xác thực email: {e}")
        return {
            'valid': False,
            'error': f'Lỗi khi gọi API: {str(e)}',
            'provider': api_provider
        }

