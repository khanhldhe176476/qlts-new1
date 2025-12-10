@echo off
chcp 65001 >nul
title Quan Ly Tai San - Server
echo.
echo ============================================================
echo DANG KHOI DONG UNG DUNG...
echo ============================================================
echo.
echo UNG DUNG SE CHAY TAI:
echo   http://127.0.0.1:5000
echo   http://localhost:5000
echo.
echo Tai khoan mac dinh:
echo   Username: admin
echo   Password: admin123
echo.
echo ============================================================
echo.
cd /d %~dp0
py run.py
pause

















