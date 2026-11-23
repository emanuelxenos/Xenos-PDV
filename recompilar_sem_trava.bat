@echo off
cd /d "%~dp0"
echo Recompilando o Xenos PDV sem nenhuma trava de licenca...
pyinstaller --noconfirm XenosPDV.spec
xcopy /E /I /Y "dados" "dist\XenosPDV\dados"
powershell -Command "Compress-Archive -Path 'dist\XenosPDV\*' -DestinationPath 'dist\XenosPDV_Sem_Trava.zip' -Force"
echo.
echo ========================================================
echo Concluido! O executavel esta em dist\XenosPDV\XenosPDV.exe
echo E o zip novo esta em dist\XenosPDV_Sem_Trava.zip
echo ========================================================
pause
