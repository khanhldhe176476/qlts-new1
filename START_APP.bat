@echo off
chcp 65001 >nul
echo ============================================================
echo KHOI DONG UNG DUNG QUAN LY TAI SAN
echo ============================================================
echo.

echo Buoc 1: Kiem tra Docker Desktop...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [LOI] Docker Desktop chua chay!
    echo.
    echo Vui long:
    echo 1. Mo Docker Desktop tu Start Menu
    echo 2. Doi Docker Desktop khoi dong xong (icon Docker o system tray)
    echo 3. Chay lai script nay
    echo.
    pause
    exit /b 1
)
echo [OK] Docker Desktop dang chay
echo.

echo Buoc 2: Dung containers cu (neu co)...
docker compose down 2>nul
echo.

echo Buoc 3: Build images (neu can)...
docker compose build
if %errorlevel% neq 0 (
    echo.
    echo [LOI] Build that bai! Xem loi o tren.
    pause
    exit /b 1
)
echo [OK] Build thanh cong
echo.

echo Buoc 4: Khoi dong containers...
docker compose up -d
if %errorlevel% neq 0 (
    echo.
    echo [LOI] Khoi dong containers that bai! Xem loi o tren.
    pause
    exit /b 1
)
echo [OK] Containers da khoi dong
echo.

echo Buoc 5: Doi containers khoi dong hoan toan...
timeout /t 5 /nobreak >nul
echo.

echo Buoc 6: Kiem tra trang thai...
docker compose ps
echo.

echo ============================================================
echo HOAN TAT!
echo ============================================================
echo.
echo Ung dung dang chay tai:
echo   http://localhost
echo   http://localhost:5000
echo.
echo Tai khoan mac dinh:
echo   Username: admin
echo   Password: admin123
echo.
echo Nhan phim bat ky de mo trinh duyet...
pause >nul
start http://localhost
echo.



