
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import secrets

from config import Config


class CryptographyManager:
    """
    Gestisce la crittografia delle password utilizzando PBKDF2 con SHA512 e Fernet
    """
    
    @staticmethod
    def generate_salt() -> bytes:
        """Genera un salt casuale per PBKDF2"""
        return secrets.token_bytes(Config.SALT_LENGTH)
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Deriva una chiave utilizzando PBKDF2 con SHA512
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            iterations=Config.PBKDF2_ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    @staticmethod
    def encrypt_password(password: str, master_key: bytes) -> str:
        """
        Crittografa una password usando Fernet
        """
        fernet = Fernet(master_key)
        encrypted_password = fernet.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted_password).decode()
    
    @staticmethod
    def decrypt_password(encrypted_password: str, master_key: bytes) -> str:
        """
        Decrittografa una password usando Fernet
        """
        try:
            fernet = Fernet(master_key)
            encrypted_data = base64.urlsafe_b64decode(encrypted_password.encode())
            decrypted_password = fernet.decrypt(encrypted_data)
            return decrypted_password.decode()
        except Exception as e:
            raise ValueError("Impossibile decrittografare la password") from e