"""
PATRÓN: Strategy Pattern
========================

STRATEGY PATTERN:
----------------
Propósito: Definir una familia de algoritmos (estrategias),
           encapsular cada uno y hacerlos intercambiables.

Estructura:
- Strategy (interfaz): Define método común send()
- ConcreteStrategy: Implementaciones específicas (Email, SMS)
- Context: Usa la estrategia (NotificationService)

JUSTIFICACIÓN:
-------------
¿Por qué Strategy y no If/Else?

CON IF/ELSE (Anti-patrón):
```python
def enviar_notificacion(tipo, destinatario, mensaje):
    if tipo == 'email':
        # código de email
    elif tipo == 'sms':
        # código de sms
    elif tipo == 'push':
        # código de push
```

Problemas:
- Viola Open/Closed Principle (cerrado a extensión)
- Agregar nuevo tipo requiere modificar función
- Difícil de testear cada tipo
- Acoplamiento alto

CON STRATEGY PATTERN:
```python
class EmailStrategy:
    def send(self, destinatario, mensaje):
        # código de email

class SMSStrategy:
    def send(self, destinatario, mensaje):
        # código de sms
```

Beneficios:
- Cumple Open/Closed (agregar nueva estrategia sin modificar existentes)
- Cada estrategia es testeable independientemente
- Bajo acoplamiento
- Fácil agregar nuevas estrategias

EJEMPLO DE USO:
--------------
```python
# Crear estrategia
email_strategy = EmailStrategy()

# Usar estrategia
notification_service = NotificationService(email_strategy)
notification_service.send("user@example.com", "Turno confirmado")

# Cambiar estrategia en runtime
sms_strategy = SMSStrategy()
notification_service.set_strategy(sms_strategy)
notification_service.send("+549111234567", "Turno confirmado")
```
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


# ==========================================
# INTERFAZ STRATEGY (Clase Abstracta)
# ==========================================

class NotificationStrategy(ABC):
    """
    Interfaz base para estrategias de notificación.

    STRATEGY PATTERN: Define el contrato que todas las
    estrategias concretas deben cumplir.

    Cada estrategia implementa send() de forma diferente.
    """

    @abstractmethod
    def send(self, destinatario: str, asunto: str, mensaje: str,
             datos_adicionales: Dict[str, Any] = None) -> bool:
        """
        Envía una notificación.

        Args:
            destinatario: Dirección del destinatario (email, teléfono, etc.)
            asunto: Asunto/título de la notificación
            mensaje: Cuerpo del mensaje
            datos_adicionales: Datos extra específicos de cada estrategia

        Returns:
            True si se envió correctamente, False si falló
        """
        pass

    @abstractmethod
    def get_tipo(self) -> str:
        """
        Retorna el tipo de notificación (email, sms, etc.).

        Útil para logging y estadísticas.
        """
        pass


# ==========================================
# ESTRATEGIAS CONCRETAS
# ==========================================

class EmailStrategy(NotificationStrategy):
    """
    Estrategia concreta para envío de emails.

    STRATEGY PATTERN: Implementación específica del algoritmo de envío.

    Responsabilidad:
    - Conectar con servidor SMTP
    - Formatear email HTML
    - Enviar y manejar errores
    """

    def __init__(self, smtp_config: Dict[str, Any] = None):
        """
        Constructor que recibe configuración SMTP.

        DEPENDENCY INJECTION: Configuración inyectada
        Permite testear con servidor SMTP mock.

        Args:
            smtp_config: {
                'server': 'smtp.gmail.com',
                'port': 587,
                'username': 'email@gmail.com',
                'password': 'password',
                'use_tls': True
            }
        """
        self.smtp_config = smtp_config or {}

    def send(self, destinatario: str, asunto: str, mensaje: str,
             datos_adicionales: Dict[str, Any] = None) -> bool:
        """
        Envía email usando SMTP.

        TEMPLATE METHOD (dentro de Strategy):
        - Define pasos del envío: conectar → enviar → cerrar
        - Cada paso puede fallar, se maneja con try/except
        """
        try:
            # 1. Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = asunto
            msg['From'] = self.smtp_config.get('username', 'noreply@turnos-medicos.com')
            msg['To'] = destinatario

            # 2. Crear cuerpo HTML
            html = self._crear_html_mensaje(asunto, mensaje, datos_adicionales)
            msg.attach(MIMEText(html, 'html'))

            # 3. Conectar y enviar
            with smtplib.SMTP(
                self.smtp_config.get('server', 'smtp.gmail.com'),
                self.smtp_config.get('port', 587)
            ) as server:
                if self.smtp_config.get('use_tls', True):
                    server.starttls()

                server.login(
                    self.smtp_config.get('username', ''),
                    self.smtp_config.get('password', '')
                )

                server.send_message(msg)

            return True

        except Exception as e:
            # En producción, loggear el error
            print(f"Error enviando email: {e}")
            return False

    def _crear_html_mensaje(self, asunto: str, mensaje: str,
                           datos_adicionales: Dict[str, Any]) -> str:
        """
        Crea HTML del email.

        TEMPLATE METHOD: Paso personalizable del envío
        Puede sobrescribirse para diferentes templates
        """
        # Template HTML básico
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 5px; padding: 20px;">
                    <h2 style="color: #2c3e50;">{asunto}</h2>
                    <div style="margin: 20px 0; line-height: 1.6;">
                        {mensaje}
                    </div>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #7f8c8d; font-size: 12px;">
                        Sistema de Turnos Médicos<br>
                        Este es un mensaje automático, por favor no responder.
                    </p>
                </div>
            </body>
        </html>
        """
        return html

    def get_tipo(self) -> str:
        return 'email'


class SMSStrategy(NotificationStrategy):
    """
    Estrategia concreta para envío de SMS.

    STRATEGY PATTERN: Otra implementación del mismo contrato.

    En producción, esto se conectaría a un proveedor de SMS
    como Twilio, AWS SNS, etc.
    """

    def __init__(self, api_config: Dict[str, Any] = None):
        """
        Constructor con configuración de API de SMS.

        Args:
            api_config: {
                'provider': 'twilio',
                'account_sid': '...',
                'auth_token': '...',
                'from_number': '+1234567890'
            }
        """
        self.api_config = api_config or {}

    def send(self, destinatario: str, asunto: str, mensaje: str,
             datos_adicionales: Dict[str, Any] = None) -> bool:
        """
        Envía SMS.

        NOTA: Implementación simplificada para MVP.
        En producción usar Twilio, AWS SNS, etc.
        """
        try:
            # Validar formato de teléfono
            if not self._validar_telefono(destinatario):
                print(f"Teléfono inválido: {destinatario}")
                return False

            # SIMULACIÓN: En producción, llamar API de SMS
            print(f"[SMS SIMULADO] A: {destinatario} - {mensaje}")

            # Aquí iría integración real:
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # client.messages.create(
            #     to=destinatario,
            #     from_=from_number,
            #     body=mensaje
            # )

            return True

        except Exception as e:
            print(f"Error enviando SMS: {e}")
            return False

    def _validar_telefono(self, telefono: str) -> bool:
        """
        Valida formato de teléfono.

        Debe comenzar con + y tener solo dígitos.
        """
        import re
        patron = r'^\+[0-9]{10,15}$'
        return bool(re.match(patron, telefono))

    def get_tipo(self) -> str:
        return 'sms'


class PushNotificationStrategy(NotificationStrategy):
    """
    Estrategia para notificaciones push (futuro).

    STRATEGY PATTERN: Extensibilidad
    - Se puede agregar esta estrategia sin modificar código existente
    - Cumple Open/Closed Principle
    """

    def send(self, destinatario: str, asunto: str, mensaje: str,
             datos_adicionales: Dict[str, Any] = None) -> bool:
        """
        Envía notificación push.

        Implementación futura con Firebase Cloud Messaging, etc.
        """
        print(f"[PUSH SIMULADO] A: {destinatario} - {asunto}")
        return True

    def get_tipo(self) -> str:
        return 'push'


class WhatsAppStrategy(NotificationStrategy):
    """
    Estrategia para mensajes de WhatsApp (futuro).

    Ejemplo de EXTENSIBILIDAD del Strategy Pattern.
    """

    def send(self, destinatario: str, asunto: str, mensaje: str,
             datos_adicionales: Dict[str, Any] = None) -> bool:
        """
        Envía mensaje por WhatsApp Business API.
        """
        print(f"[WHATSAPP SIMULADO] A: {destinatario} - {mensaje}")
        return True

    def get_tipo(self) -> str:
        return 'whatsapp'


# ==========================================
# FACTORY PARA ESTRATEGIAS
# ==========================================
# PATRÓN: Factory Pattern + Strategy Pattern

class NotificationStrategyFactory:
    """
    Fábrica de estrategias de notificación.

    FACTORY PATTERN: Crea estrategias según tipo solicitado.

    COMBINACIÓN DE PATRONES:
    - Factory crea las estrategias
    - Strategy define el comportamiento

    Beneficio: Centraliza creación, facilita configuración.
    """

    @staticmethod
    def create(tipo: str, config: Dict[str, Any] = None) -> NotificationStrategy:
        """
        Crea una estrategia según el tipo.

        Args:
            tipo: 'email', 'sms', 'push', 'whatsapp'
            config: Configuración específica de la estrategia

        Returns:
            Instancia de la estrategia

        Raises:
            ValueError: Si el tipo no existe
        """
        strategies = {
            'email': EmailStrategy,
            'sms': SMSStrategy,
            'push': PushNotificationStrategy,
            'whatsapp': WhatsAppStrategy
        }

        strategy_class = strategies.get(tipo.lower())

        if not strategy_class:
            raise ValueError(
                f"Tipo de notificación '{tipo}' no soportado. "
                f"Tipos disponibles: {list(strategies.keys())}"
            )

        return strategy_class(config)
