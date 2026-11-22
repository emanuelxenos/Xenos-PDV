@echo off
title Sincronizar com GitHub - Xenos PDV
cd /d "%~dp0"
echo ======================================================
echo    ENVIANDO ATUALIZACOES PARA O GITHUB (XENOS PDV)
echo ======================================================
echo.

git add .
git commit -m "feat: central de backup em tela cheia com agendador background, restauracao zip e alerta de estoque"
git push origin main

echo.
echo ======================================================
echo    SINCRONIZACAO CONCLUIDA COM SUCESSO!
echo ======================================================
pause
