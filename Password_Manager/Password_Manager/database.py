import sqlite3
from config import Config

class DatabaseManager:
    """Gestisce le operazioni del database"""
    
    @staticmethod
    def init_database() -> None:
        """Inizializza il database con le tabelle necessarie"""
        with sqlite3.connect(Config.DATABASE) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS utenti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    encryption_salt BLOB NOT NULL,
                    data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_salvate (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    utente_id INTEGER,
                    nome_sito TEXT NOT NULL,
                    username_sito TEXT NOT NULL,
                    password_sito_encrypted TEXT NOT NULL,
                    data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_modifica TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (utente_id) REFERENCES utenti (id)
                )
            ''')
            
            conn.commit()
    
    @staticmethod
    def get_connection() -> sqlite3.Connection:
        """Ottiene una connessione al database con row factory"""
        conn = sqlite3.connect(Config.DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
