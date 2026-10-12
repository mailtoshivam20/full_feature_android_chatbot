@echo off
echo === Building APK for Android Emulator ===
echo (Backend URL: http://10.0.2.2:8000)
echo.

cd /d "%~dp0frontend"

:: Copy emulator env
copy /Y .env.android.emulator .env.local

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
pause
