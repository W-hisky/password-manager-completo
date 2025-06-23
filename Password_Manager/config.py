import os

class Config:
    """Configurazione centralizzata dell'applicazione"""
    SECRET_KEY = os.urandom(24)
    DATABASE = 'password_manager.db'
    PBKDF2_ITERATIONS = 100
    SALT_LENGTH = 32
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128