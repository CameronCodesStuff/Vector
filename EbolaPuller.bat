@echo off
color A
title Ebola Puller
setlocal

rem save public ip as variable
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "(Invoke-RestMethod -Uri https://api.ipify.org)"`) do (
    set "publicip=%%i"
)

if not defined publicip (
    echo Failed to retrieve public IP.
    pause
    exit /b
)

set "tshark="

if exist "C:\Program Files\Wireshark\tshark.exe" (
    set "tshark=C:\Program Files\Wireshark\tshark.exe"
) else if exist "C:\Program Files (x86)\Wireshark\tshark.exe" (
    set "tshark=C:\Program Files (x86)\Wireshark\tshark.exe"
)

if not defined tshark (
    echo Wireshark not found.
    start https://www.wireshark.org/download.html
    pause
    exit /b
)

echo tshark.exe Found! (%tshark%)
echo.
"%tshark%" -D
echo.

set /p "interface=Interface #: "

cls
echo.
echo IP Dump
echo -------
echo.

"%tshark%" -i "%interface%" -f "udp" -Y "stun.type == 0x0101 && stun.att.type == 0x0020 && stun.att.ipv4 != %publicip%" -T fields -e stun.att.ipv4