@echo off
echo DNU Reminder - Hệ thống nhắc nhở học tập
echo ==========================================
echo.

echo Kiem tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Loi: Python khong duoc cai dat hoac khong co trong PATH
    echo Vui long cai dat Python 3.7+ va thu lai
    pause
    exit /b 1
)

echo.
echo Tao moi truong ao...
if not exist "venv" (
    python -m venv venv
    echo Moi truong ao da duoc tao
) else (
    echo Moi truong ao da ton tai
)

echo.
echo Kich hoat moi truong ao...
call venv\Scripts\activate.bat

echo.
echo Cai dat dependencies...
pip install -r requirements.txt

echo.
echo Khoi dong ung dung...
echo Ung dung se chay tai: http://localhost:5000
echo Nhan Ctrl+C de dung
echo.

python app.py

pause
