"""
Strategies - Strategy Pattern
"""

from .notification_strategy import (
    NotificationStrategy,
    EmailStrategy,
    SMSStrategy,
    PushNotificationStrategy,
    WhatsAppStrategy,
    NotificationStrategyFactory
)

__all__ = [
    'NotificationStrategy',
    'EmailStrategy',
    'SMSStrategy',
    'PushNotificationStrategy',
    'WhatsAppStrategy',
    'NotificationStrategyFactory'
]
