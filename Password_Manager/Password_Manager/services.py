import sqlite3
from typing import Dict, List, Optional
from werkzeug.security import generate_password_hash, check_password_hash

from .database import DatabaseManager
from .core.cryptography import CryptographyManager


class UserManager:
    """Gestisce le operazioni sugli utenti"""
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
        """Recupera un utente dal database tramite username"""
        with DatabaseManager.get_connection() as conn:
            return conn.execute(
                'SELECT * FROM utenti WHERE username = ?', (username,)
            ).fetchone()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
        """Recupera un utente dal database tramite ID"""
        with DatabaseManager.get_connection() as conn:
            return conn.execute(
                'SELECT * FROM utenti WHERE id = ?', (user_id,)
            ).fetchone()
    
    @staticmethod
    def create_user(username: str, password: str) -> bool:
        """
        Crea un nuovo utente nel database
        """
        try:
            password_hash = generate_password_hash(password)
            encryption_salt = CryptographyManager.generate_salt()
            
            with DatabaseManager.get_connection() as conn:
                conn.execute(
                    'INSERT INTO utenti (username, password_hash, encryption_salt) VALUES (?, ?, ?)',
                    (username, password_hash, encryption_salt)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    @staticmethod
    def get_master_key(user_id: int, password: str) -> bytes:
        """
        Ottiene la chiave master dell'utente per la crittografia
        """
        user = UserManager.get_user_by_id(user_id)
        if not user:
            raise ValueError("Utente non trovato")
        
        return CryptographyManager.derive_key(password, user['encryption_salt'])


class PasswordService:
    """Servizio per la gestione delle password salvate"""
    
    @staticmethod
    def get_user_passwords(user_id: int, master_key: bytes) -> List[Dict]:
        """
        Recupera e decrittografa tutte le password di un utente
        """
        with DatabaseManager.get_connection() as conn:
            password_entries = conn.execute(
                'SELECT * FROM password_salvate WHERE utente_id = ? ORDER BY nome_sito',
                (user_id,)
            ).fetchall()
        
        decrypted_passwords = []
        for entry in password_entries:
            try:
                decrypted_password = CryptographyManager.decrypt_password(
                    entry['password_sito_encrypted'], master_key
                )
                decrypted_passwords.append({
                    'id': entry['id'],
                    'nome_sito': entry['nome_sito'],
                    'username_sito': entry['username_sito'],
                    'password_sito': decrypted_password,
                    'data_creazione': entry['data_creazione'],
                    'data_modifica': entry['data_modifica']
                })
            except ValueError:
                continue
        
        return decrypted_passwords
    
    @staticmethod
    def add_password(user_id: int, site_name: str, site_username: str, 
                    site_password: str, master_key: bytes) -> bool:
        """Aggiunge una nuova password crittografata"""
        try:
            encrypted_password = CryptographyManager.encrypt_password(site_password, master_key)
            
            with DatabaseManager.get_connection() as conn:
                conn.execute(
                    'INSERT INTO password_salvate (utente_id, nome_sito, username_sito, password_sito_encrypted) VALUES (?, ?, ?, ?)',
                    (user_id, site_name, site_username, encrypted_password)
                )
                conn.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_password_by_id(password_id: int, user_id: int) -> Optional[sqlite3.Row]:
        """Recupera una password specifica dell'utente"""
        with DatabaseManager.get_connection() as conn:
            return conn.execute(
                'SELECT * FROM password_salvate WHERE id = ? AND utente_id = ?',
                (password_id, user_id)
            ).fetchone()
    
    @staticmethod
    def update_password(password_id: int, user_id: int, site_name: str, 
                       site_username: str, site_password: str, master_key: bytes) -> bool:
        """Aggiorna una password esistente"""
        try:
            encrypted_password = CryptographyManager.encrypt_password(site_password, master_key)
            
            with DatabaseManager.get_connection() as conn:
                conn.execute(
                    'UPDATE password_salvate SET nome_sito = ?, username_sito = ?, password_sito_encrypted = ?, data_modifica = CURRENT_TIMESTAMP WHERE id = ? AND utente_id = ?',
                    (site_name, site_username, encrypted_password, password_id, user_id)
                )
                conn.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete_password(password_id: int, user_id: int) -> bool:
        """Elimina una password"""
        try:
            with DatabaseManager.get_connection() as conn:
                conn.execute(
                    'DELETE FROM password_salvate WHERE id = ? AND utente_id = ?',
                    (password_id, user_id)
                )
                conn.commit()
            return True
        except Exception:
            return False
