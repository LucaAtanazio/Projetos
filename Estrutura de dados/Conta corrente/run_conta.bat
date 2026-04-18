@echo off
TITLE Banco MONEY - Conta Corrente
echo [Banco MONEY] Iniciando ambiente de gestao no Lenovo...

:: Verifica se o Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH. 
    echo Verifique a instalacao no Windows 11.
    pause
    exit /b
)

:: Executa o script
echo [Banco MONEY] Rodando conta.py...
python conta.py

if %errorlevel% neq 0 (
    echo.
    echo [ALERTA] O programa encerrou com erro. 
    echo Verifique se as bibliotecas (redis, matplotlib) estao instaladas.
    pause
)