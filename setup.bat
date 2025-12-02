@echo off
echo ========================================
echo SETUP DU AN QUAN LY TAI SAN
echo ========================================
echo.

echo [1/3] Cai dat thu vien...
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo LOI: Khong the cai dat thu vien
    pause
    exit /b 1
)
echo OK!

echo.
echo [2/3] Khoi tao database va du lieu mau...
py init_new_data.py
if errorlevel 1 (
    echo LOI: Khong the khoi tao database
    pause
    exit /b 1
)
echo OK!

echo.
echo [3/3] Hoan thanh!
echo.
echo ========================================
echo THONG TIN DANG NHAP MAC DINH:
echo   Username: admin
echo   Password: admin123
echo ========================================
echo.
echo Chay ung dung bang lenh: py run.py
echo.
pause





