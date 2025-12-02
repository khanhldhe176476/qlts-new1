#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để dừng các process Flask cũ và khởi động lại với config mới
"""
import os
import sys
import subprocess
import signal
import time
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def kill_processes_on_port(port):
    """Dừng tất cả process đang dùng port"""
    try:
        if sys.platform == 'win32':
            # Windows: dùng netstat và taskkill
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True
            )
            pids = []
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids.append(pid)
            
            for pid in set(pids):
                try:
                    print(f"Đang dừng process PID {pid}...")
                    subprocess.run(['taskkill', '/F', '/PID', pid], 
                                 capture_output=True)
                except Exception as e:
                    print(f"Không thể dừng PID {pid}: {e}")
            
            time.sleep(2)  # Đợi process dừng
            return len(pids) > 0
        else:
            # Linux/Mac: dùng lsof và kill
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True
            )
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"Đã dừng process PID {pid}")
                    except Exception:
                        pass
            return len(pids) > 0
    except Exception as e:
        print(f"Lỗi khi dừng process: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("DUNG CAC PROCESS FLASK CU VA KHOI DONG LAI")
    print("=" * 60)
    print()
    
    port = 5000
    print(f"Đang kiểm tra port {port}...")
    
    if kill_processes_on_port(port):
        print(f"\n✅ Đã dừng các process trên port {port}")
        print("\nBây giờ bạn có thể chạy lại:")
        print("  python run.py")
    else:
        print(f"\n✅ Không có process nào đang dùng port {port}")
        print("\nBạn có thể chạy:")
        print("  python run.py")

