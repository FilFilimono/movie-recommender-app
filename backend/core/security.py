import bcrypt

class PasswordHasher:
    
    def __init__(self, rounds=12) -> None:
        self._rounds = rounds 
    
    def hash(self, password) -> str:
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds= self._rounds)
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode("utf-8")       
    
    def verify(self, password, hashed) -> bool:
        try:
            password_bytes = password.encode("utf-8")
            hashed_bytes = hashed.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except (ValueError, TypeError, UnicodeError):
            return False
        
    def is_strong(self, password: str) -> tuple[bool, str]:
        
        if len(password) < 6:
            return (False, "минимум 6 символов")
        
        if password.isdigit():
            return (False, "только цифры — слабо")
        
        return (True, "")