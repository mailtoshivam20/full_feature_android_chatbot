@echo off
echo === Building APK for Real Android Device ===
echo.

:: Find PC's local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4"') do (
    set LOCAL_IP=%%a
    goto :found
)
:found
set LOCAL_IP=%LOCAL_IP: =%
echo Detected PC IP: %LOCAL_IP%
echo (Make sure your phone is on the SAME Wi-Fi network)
echo.

cd /d "%~dp0frontend"

:: Write device env with detected IP
echo VITE_API_BASE_URL=http://%LOCAL_IP%:8000> .env.local

:: Build React app
echo [1/3] Building React app...
call npm run build
if errorlevel 1 ( echo BUILD FAILED & pause & exit /b 1 )

:: Sync with Android
echo [2/3] Syncing with Capacitor...
call npx cap sync android
if errorlevel 1 ( echo SYNC FAILED & pause & exit /b 1 )

:: Build APK
echo [3/3] Building APK...
cd android
call gradlew.bat assembleDebug
if errorlevel 1 ( echo GRADLE BUILD FAILED & pause & exit /b 1 )

echo.
echo === SUCCESS ===
echo APK is at:
echo   frontend\android\app\build\outputs\apk\debug\app-debug.apk
echo.
echo Install on phone:  adb install app\build\outputs\apk\debug\app-debug.apk
echo Or copy the APK file to your phone and install it.
echo.
pause
