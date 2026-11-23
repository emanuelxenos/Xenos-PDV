@echo off
cd /d "%~dp0"
echo ==========================================================
echo        COMPILANDO VERSAO DEFINITIVA DO XENOS PDV
echo ==========================================================
echo.
pyinstaller --noconfirm XenosPDV.spec
if errorlevel 1 (
    echo [ERRO] Falha na compilacao com PyInstaller!
    pause
    exit /b 1
)

echo Copiando a pasta de dados oficial para a distribuicao...
xcopy /E /I /Y "dados" "dist\XenosPDV\dados"

echo.
echo Gerando o arquivo ZIP portatil para o cliente...
powershell -Command "Compress-Archive -Path 'dist\XenosPDV\*' -DestinationPath 'dist\XenosPDV_Pronto_Cliente.zip' -Force"

echo.
echo ==========================================================
echo [SUCESSO TOTAL!] 
echo O executavel corrigido esta em: dist\XenosPDV\XenosPDV.exe
echo O ZIP para levar ao cliente esta em: dist\XenosPDV_Pronto_Cliente.zip
echo ==========================================================
pause
