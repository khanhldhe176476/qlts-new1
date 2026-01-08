@echo off
chcp 65001 >nul
echo ============================================================
echo REBUILD DOCKER - XOA CACHE VA BUILD LAI
echo ============================================================
echo.

echo Buoc 1: Dung containers...
docker compose down
echo.

echo Buoc 2: Xoa images cu...
docker rmi qlts-new8-web 2>nul
docker rmi qlts-new8_web 2>nul
echo.

echo Buoc 3: Xoa build cache...
docker builder prune -f
echo.

echo Buoc 4: Kiem tra package.json...
findstr /C:"zustand" frontend\package.json
if %errorlevel% neq 0 (
    echo LOI: zustand khong co trong package.json!
    pause
    exit /b 1
)
echo OK: zustand da co trong package.json
echo.

echo Buoc 5: Build lai voi --no-cache...
docker compose build --no-cache --build-arg CACHE_BUST=%RANDOM% web
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo BUILD THAT BAI! Xem loi o tren.
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo ============================================================
echo BUILD THANH CONG!
echo ============================================================
echo.

echo Buoc 6: Chay containers...
docker compose up -d

echo.
echo ============================================================
echo HOAN TAT! Truy cap: http://localhost
echo ============================================================
pause



