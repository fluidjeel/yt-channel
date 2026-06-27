@echo off
REM Setup script for Channel Intelligence Analyzer (Windows)

echo Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo Checking ffmpeg...
where ffmpeg >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ffmpeg not found. Attempting install via winget...
    winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
)

echo.
python main.py --check-deps
echo.
echo Setup complete. Activate with: .venv\Scripts\activate
echo Run analysis: python main.py "https://www.youtube.com/@channelname"
