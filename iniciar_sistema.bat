@echo off
title Xenos PDV
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocorreu um erro ao executar o sistema. Pressione qualquer tecla para sair.
    pause >nul
)

