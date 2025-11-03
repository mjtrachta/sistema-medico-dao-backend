#!/bin/bash

# Script de configuración de entorno
# Ayuda a configurar el archivo .env fácilmente

set -e

echo "========================================="
echo "  Configuración de Entorno - Backend"
echo "========================================="
echo ""

# Verificar si ya existe .env
if [ -f .env ]; then
    echo "⚠️  Ya existe un archivo .env"
    read -p "¿Deseas sobrescribirlo? (s/N): " respuesta
    if [[ ! $respuesta =~ ^[Ss]$ ]]; then
        echo "❌ Operación cancelada"
        exit 0
    fi
fi

echo ""
echo "Selecciona el tipo de configuración:"
echo "1) Desarrollo Local (base de datos en localhost)"
echo "2) Conexión Remota vía Tailscale"
echo ""
read -p "Opción (1/2): " opcion

case $opcion in
    1)
        echo ""
        echo "📝 Configurando para desarrollo local..."
        cp .env.example .env
        echo "✅ Archivo .env creado desde .env.example"
        echo ""
        echo "⚠️  IMPORTANTE: Edita el archivo .env y configura:"
        echo "   - DB_PASSWORD: Tu contraseña de PostgreSQL"
        echo "   - MAIL_USERNAME y MAIL_PASSWORD si deseas probar emails"
        echo ""
        echo "💡 Para editar: nano .env"
        ;;
    2)
        echo ""
        echo "📝 Configurando para conexión remota..."
        
        # Verificar si Tailscale está instalado
        if ! command -v tailscale &> /dev/null; then
            echo "⚠️  Tailscale no está instalado"
            read -p "¿Deseas instalarlo ahora? (s/N): " instalar
            if [[ $instalar =~ ^[Ss]$ ]]; then
                echo "Instalando Tailscale..."
                curl -fsSL https://tailscale.com/install.sh | sh
                echo "✅ Tailscale instalado"
                echo ""
                echo "🔐 Ahora necesitas autenticarte:"
                sudo tailscale up
            else
                echo "❌ No se puede continuar sin Tailscale"
                exit 1
            fi
        fi
        
        cp .env.tailscale.example .env
        echo "✅ Archivo .env creado desde .env.tailscale.example"
        echo ""
        
        # Intentar obtener IPs disponibles
        echo "🔍 Buscando dispositivos en tu red Tailscale..."
        if command -v tailscale &> /dev/null; then
            echo ""
            tailscale status | head -10
            echo ""
        fi
        
        read -p "Ingresa la IP de Tailscale del host (ej: 100.105.169.57): " ip_host
        
        if [ ! -z "$ip_host" ]; then
            # Reemplazar la IP en el archivo .env
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/DB_HOST=100\.105\.169\.57/DB_HOST=$ip_host/" .env
            else
                sed -i "s/DB_HOST=100\.105\.169\.57/DB_HOST=$ip_host/" .env
            fi
            echo "✅ IP del host configurada: $ip_host"
        fi
        
        echo ""
        echo "⚠️  IMPORTANTE: Asegúrate de que:"
        echo "   1. Tailscale esté corriendo: tailscale status"
        echo "   2. El host tenga PostgreSQL configurado para aceptar conexiones remotas"
        echo "   3. Puedas hacer ping al host: ping $ip_host"
        echo ""
        echo "📚 Para más detalles, lee: TAILSCALE_SETUP.md"
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "✅ Configuración completada"
echo "========================================="
echo ""
echo "Próximos pasos:"
echo "1. Revisa/edita el archivo .env"
echo "2. Activa el entorno virtual: source .venv/bin/activate"
echo "3. Inicia la aplicación: python app.py"
echo ""
