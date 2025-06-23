
from flask import Flask
from config import Config
from .database import DatabaseManager

def create_app():
    """Crea e configura l'istanza dell'applicazione Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inizializza il database
    with app.app_context():
        DatabaseManager.init_database()

    # Registra le route (Blueprint)
    from . import routes
    app.register_blueprint(routes.main)

    return app