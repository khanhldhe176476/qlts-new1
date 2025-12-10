"""Utility functions for voucher generation"""
from datetime import datetime

def generate_voucher_code(voucher_type: str, db_session, AssetVoucher):
    """
    Sinh mã chứng từ theo format: GT-YYYYMMDD-XXX (Ghi tăng)
    hoặc GG-YYYYMMDD-XXX (Ghi giảm)
    hoặc DG-YYYYMMDD-XXX (Đánh giá lại)
    """
    today = datetime.now()
    prefix_map = {
        'increase': 'GT',  # Ghi tăng
        'decrease': 'GG',  # Ghi giảm
        'reevaluate': 'DG'  # Đánh giá lại
    }
    prefix = prefix_map.get(voucher_type, 'CT')
    date_str = today.strftime('%Y%m%d')
    
    # Tìm số thứ tự tiếp theo
    last_voucher = db_session.query(AssetVoucher).filter(
        AssetVoucher.voucher_code.like(f'{prefix}-{date_str}-%')
    ).order_by(AssetVoucher.voucher_code.desc()).first()
    
    if last_voucher:
        try:
            last_num = int(last_voucher.voucher_code.split('-')[-1])
            next_num = last_num + 1
        except:
            next_num = 1
    else:
        next_num = 1
    
    return f'{prefix}-{date_str}-{next_num:03d}'

def generate_inventory_code(db_session, Inventory):
    """Sinh mã đợt kiểm kê: KK-YYYYMMDD-XXX"""
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    
    last_inventory = db_session.query(Inventory).filter(
        Inventory.inventory_code.like(f'KK-{date_str}-%')
    ).order_by(Inventory.inventory_code.desc()).first()
    
    if last_inventory:
        try:
            last_num = int(last_inventory.inventory_code.split('-')[-1])
            next_num = last_num + 1
        except:
            next_num = 1
    else:
        next_num = 1
    
    return f'KK-{date_str}-{next_num:03d}'

def generate_process_request_code(db_session, AssetProcessRequest):
    """Sinh mã đề nghị xử lý: DN-YYYYMMDD-XXX"""
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    
    last_request = db_session.query(AssetProcessRequest).filter(
        AssetProcessRequest.request_code.like(f'DN-{date_str}-%')
    ).order_by(AssetProcessRequest.request_code.desc()).first()
    
    if last_request:
        try:
            last_num = int(last_request.request_code.split('-')[-1])
            next_num = last_num + 1
        except:
            next_num = 1
    else:
        next_num = 1
    
    return f'DN-{date_str}-{next_num:03d}'
