@echo off
echo ========================================
echo SOLUCION SIMPLE PARA WINDOWS
echo ========================================
echo.

echo Desinstalando psycopg2 actual...
pip uninstall -y psycopg2 psycopg2-binary

echo.
echo Instalando psycopg2-binary limpio...
pip install psycopg2-binary

echo.
echo Probando conexion...
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', port='5432', database='turnos_medicos_dao', user='postgres', password='postgres123'); print('EXITO: Conexion funciona'); conn.close()"

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Plan B: Instalando psycopg v3
    echo ========================================
    pip uninstall -y psycopg2-binary
    pip install "psycopg[binary]"

    echo.
    echo Actualizando requirements.txt para usar psycopg v3...
    echo psycopg[binary]==3.1.19 > temp_req.txt
    type requirements.txt | findstr /v "psycopg2" >> temp_req.txt
    move /y temp_req.txt requirements.txt

    echo.
    echo Probando psycopg v3...
    python -c "import psycopg; conn = psycopg.connect('host=localhost port=5432 dbname=turnos_medicos_dao user=postgres password=postgres123'); print('EXITO: Conexion con psycopg v3 funciona'); conn.close()"
)

echo.
echo ========================================
echo LISTO - Intenta flask run ahora
echo ========================================
pause
