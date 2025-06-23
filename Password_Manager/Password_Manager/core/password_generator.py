import random
import string
from config import Config

class PasswordGenerator:
    """Generatore di password sicure con opzioni configurabili"""
    
    SPECIAL_CHARS = "!@#$%&*"
    
    @classmethod
    def generate_secure_password(
        cls,
        length: int = 16,
        use_special_chars: bool = True,
        use_uppercase: bool = True,
        use_numbers: bool = True
    ) -> str:
        """
        Genera una password casuale sicura
        """
        length = max(4, min(length, Config.MAX_PASSWORD_LENGTH))
        
        chars = string.ascii_lowercase
        required_chars = [random.choice(string.ascii_lowercase)]
        
        if use_uppercase:
            chars += string.ascii_uppercase
            required_chars.append(random.choice(string.ascii_uppercase))
        
        if use_numbers:
            chars += string.digits
            required_chars.append(random.choice(string.digits))
        
        if use_special_chars:
            chars += cls.SPECIAL_CHARS
            required_chars.append(random.choice(cls.SPECIAL_CHARS))
        
        remaining_length = length - len(required_chars)
        additional_chars = [random.choice(chars) for _ in range(remaining_length)]
        
        password_chars = required_chars + additional_chars
        random.shuffle(password_chars)
        
        return ''.join(password_chars)