@echo off
chcp 65001 >nul
echo ============================================================
echo KIEM TRA VA CHAY UNG DUNG QUAN LY TAI SAN
echo ============================================================
echo.

REM Kiem tra port 5000
echo [1] Kiem tra port 5000...
netstat -ano | findstr :5000 >nul
if %errorlevel% == 0 (
    echo    [WARNING] Port 5000 dang duoc su dung!
    echo    Ung dung co the da dang chay.
    echo    Thu mo trinh duyet: http://127.0.0.1:5000
    echo.
    choice /C YN /M "Ban co muon dung process cu va chay lai khong"
    if errorlevel 2 goto end
    if errorlevel 1 (
        echo    Dang tim process su dung port 5000...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
            echo    Dang dong process ID: %%a
            taskkill /F /PID %%a >nul 2>&1
        )
        timeout /t 2 >nul
    )
)

REM Kiem tra Python
echo [2] Kiem tra Python...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    [ERROR] Python khong tim thay!
    echo    Vui long cai dat Python hoac su dung 'python' thay vi 'py'
    goto end
)
py --version

REM Kiem tra dependencies
echo [3] Kiem tra dependencies...
py -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo    [ERROR] Flask chua duoc cai dat!
    echo    Dang cai dat dependencies...
    py -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo    [ERROR] Khong the cai dat dependencies!
        goto end
    )
)
echo    [OK] Dependencies da san sang

REM Chay ung dung
echo.
echo [4] Dang khoi dong ung dung...
echo.
echo ============================================================
echo UNG DUNG SE CHAY TAI:
echo   http://127.0.0.1:5000
echo   http://localhost:5000
echo ============================================================
echo.
echo Tai khoan mac dinh:
echo   Username: admin
echo   Password: admin123
echo.
echo Nhan Ctrl+C de dung ung dung
echo ============================================================
echo.

py run.py

:end
pause

