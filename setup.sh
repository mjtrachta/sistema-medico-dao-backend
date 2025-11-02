#!/bin/bash

echo "======================================"
echo "Sistema de Turnos Médicos - Setup"
echo "======================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi

echo "✅ Python 3 encontrado: $(python3 --version)"
echo ""

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "✅ Entorno virtual creado"
else
    echo "✅ Entorno virtual ya existe"
fi
echo ""

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip -q

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt -q

echo ""
echo "======================================"
echo "✅ Instalación completada!"
echo "======================================"
echo ""
echo "Para ejecutar el proyecto:"
echo "  1. source venv/bin/activate"
echo "  2. python app.py"
echo ""
echo "O directamente:"
echo "  ./run.sh"
echo ""
