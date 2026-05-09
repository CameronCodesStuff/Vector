@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo ===================================================
echo                Vector Install
echo ===================================================
echo.

:: ------------------------------
:: Detect Python
:: ------------------------------
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    py --version >nul 2>&1
    IF %ERRORLEVEL% EQU 0 (
        set "PY_CMD=py"
    ) ELSE (
        echo [ERROR] Python is not installed.
        echo Install Python from:
        echo https://www.python.org/downloads/
        pause
        exit /b 1
    )
) ELSE (
    set "PY_CMD=python"
)

echo [OK] Python detected via %PY_CMD%.

:: ------------------------------
:: Check Python version
:: ------------------------------
FOR /F "tokens=2 delims= " %%A IN ('%PY_CMD% --version 2^>^&1') DO SET PYVER=%%A
echo Detected Python version: %PYVER%

SET MAJOR_VER=%PYVER:~0,1%
IF %MAJOR_VER% LSS 3 (
    echo [ERROR] Python 3.x or higher is required.
    pause
    exit /b 1
)

:: ------------------------------
:: Ensure pip exists
:: ------------------------------
echo.
echo [INFO] Ensuring pip exists...
%PY_CMD% -m ensurepip --default-pip >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [WARNING] ensurepip failed. Trying to install pip manually...
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    %PY_CMD% get-pip.py
    del get-pip.py
)

echo [INFO] Upgrading pip...
%PY_CMD% -m pip install --upgrade pip

:: ------------------------------
:: Install Python packages
:: ------------------------------
echo.
echo ===================================================
echo Installing Python Packages
echo ===================================================
echo.

:: Space-separated list of packages. Use quotes for special characters like [ ] or >=
SET PACKAGES=^
requests beautifulsoup4 "web3[eth-account]" pywin32 cryptography faker scapy "colorama>=0.4.0" "netifaces>=0.11.0" opencv-python mss pyautogui pydirectinput numpy pillow flask piexif "pychromecast>=3.0.0" selenium PyQt5 PyQtWebEngine pycryptodome "psutil>=5.8.0" urwid pynput pyperclip plyer paramiko pycaw comtypes waitress matplotlib networkx fpdf skyfield plotly phonenumbers aiohttp discord.py "discord.py-self" openai rich watchdog "schedule>=1.0.0" "packaging>=21.0"

:: Install all packages
echo [INSTALLING] All packages...
%PY_CMD% -m pip install --upgrade %PACKAGES%
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] Some packages may have failed to install.
    echo Try installing the failed packages manually.
) ELSE (
    echo.
    echo [SUCCESS] All packages installed successfully.
)

echo.
echo ===================================================
echo Installation process finished
echo ===================================================
pause
exit /b 0