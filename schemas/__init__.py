from flask_marshmallow import Marshmallow

ma = Marshmallow()

def init_ma(app):
    """Inicializa Marshmallow"""
    ma.init_app(app)
    return ma

__all__ = [
    'ma',
    'init_ma'
]
