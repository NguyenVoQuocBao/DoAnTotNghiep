@echo off
chcp 65001 >nul
title Hệ thống Phân tích và Gợi ý Học tập

echo ============================================================
echo   HỆ THỐNG PHÂN TÍCH VÀ GỢI Ý HỌC TẬP
echo ============================================================
echo.

REM Try multiple Python locations
set PYTHON=
if exist "C:\student_venv\Scripts\python.exe" (
    set PYTHON=C:\student_venv\Scripts\python.exe
    echo [OK] Tìm thấy Python tại C:\student_venv
) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    set PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe
    echo [OK] Tìm thấy Python 3.12
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON=python
        echo [OK] Tìm thấy Python trong PATH
    ) else (
        echo [ERROR] Không tìm thấy Python!
        echo.
        echo Vui lòng cài Python 3.11+ từ: https://www.python.org/downloads/
        echo Hoặc chạy: python -m venv C:\student_venv
        pause
        exit /b 1
    )
)

echo Python version:
"%PYTHON%" --version
echo.

REM Check/install dependencies
echo Đang kiểm tra dependencies...
"%PYTHON%" -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Dependencies chưa được cài đặt!
    echo Đang cài đặt...
    "%PYTHON%" -m pip install -q flask flask-wtf numpy pandas scikit-learn openpyxl redis
    if %errorlevel% neq 0 (
        echo [ERROR] Không thể cài đặt dependencies!
        pause
        exit /b 1
    )
    echo [OK] Đã cài đặt dependencies!
)

echo ============================================================
echo   ĐANG KHỞI ĐỘNG ỨNG DỤNG...
echo ============================================================
echo.
echo Sau khi khởi động, truy cập: http://localhost:5001
echo.
echo Tài khoản sinh viên: <MSSV thật> / 123456
echo Tài khoản giáo viên: teacher001 / teacher123
echo.
echo Nhấn Ctrl+C để dừng ứng dụng
echo ============================================================
echo.

REM launch_app.py handles Unicode path via Python
"%PYTHON%" ..\launch_app.py

pause