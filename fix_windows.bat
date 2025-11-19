@echo off
echo ========================================
echo SOLUCION SIMPLE PARA WINDOWS
echo Reemplazando psycopg2 con pg8000
echo ========================================
echo.

echo Desinstalando psycopg2...
pip uninstall -y psycopg2 psycopg2-binary

echo.
echo Instalando pg8000 (driver puro Python, sin binarios)...
pip install pg8000

echo.
echo LISTO - Ya puedes ejecutar flask run
echo ========================================
pause
