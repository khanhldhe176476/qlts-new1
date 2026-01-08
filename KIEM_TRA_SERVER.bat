@echo off
chcp 65001 >nul
echo ============================================================
echo KIEM TRA TRANG THAI SERVER
echo ============================================================
echo.

echo [1] Kiem tra port 5000...
netstat -ano | findstr :5000 >nul
if %errorlevel% == 0 (
    echo    [OK] Port 5000 dang duoc su dung
    echo    Server co the dang chay!
    echo.
    echo    Thu mo trinh duyet: http://127.0.0.1:5000
    echo    hoac: http://localhost:5000
    echo.
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo    Process ID: %%a
        tasklist /FI "PID eq %%a" /FO LIST | findstr "Image Name"
    )
) else (
    echo    [WARNING] Port 5000 khong co process nao dang su dung
    echo    Server chua chay hoac dang chay tren port khac
)

echo.
echo [2] Kiem tra Python...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    [ERROR] Python khong tim thay!
    goto end
)
py --version

echo.
echo [3] Kiem tra dependencies...
py -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo    [ERROR] Flask chua duoc cai dat!
    echo    Chay: py -m pip install -r requirements.txt
    goto end
)
echo    [OK] Flask da cai dat

echo.
echo [4] Kiem tra import app...
py -c "from app import app; print('    [OK] App import thanh cong')" 2>&1
if %errorlevel% neq 0 (
    echo    [ERROR] Co loi khi import app!
    goto end
)

echo.
echo ============================================================
echo KET QUA KIEM TRA
echo ============================================================
echo.
echo Neu server chua chay, ban co the:
echo   1. Chay file: CHAY_SERVER.bat
echo   2. Hoac chay: py run.py
echo.
echo ============================================================

:end
pause

