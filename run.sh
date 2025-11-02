#!/bin/bash

echo "======================================"
echo "Iniciando Sistema de Turnos Médicos"
echo "======================================"
echo ""

# Verificar que existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "❌ Entorno virtual no encontrado"
    echo "Ejecuta primero: ./setup.sh"
    exit 1
fi

# Activar entorno virtual
source venv/bin/activate

# Verificar conexión a base de datos
echo "🔍 Verificando configuración..."
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado, usando valores por defecto"
fi

echo ""
echo "🚀 Iniciando servidor Flask..."
echo "   URL: http://localhost:5000"
echo "   Health: http://localhost:5000/api/health"
echo ""
echo "   Presiona Ctrl+C para detener"
echo ""

# Ejecutar aplicación
python app.py
