from backend.database.user_repo import UserRepository
from backend.database.session_repo import SessionRepository
from backend.core.security import PasswordHasher
from backend.entities.user import User
from backend.entities.session import Session

class AuthError (Exception):
    pass

class AuthorizationService:
    
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository, hasher: PasswordHasher) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._hasher = hasher
    
    def register(self, username, password) -> dict:
        username = username.strip()
        if self._user_repo.exists_user(username):
            raise AuthError(f"User {username}, уже есть [REGISTER]")
        
        if not self._hasher.is_strong(password):
            raise AuthError("не надежный пароль [REGISTER]")
        
        hash_password = self._hasher.hash(password)
        
        user = User(username, hash_password)
        
        user = self._user_repo.create_user(user)
        session = self._session_repo.create_session(user.id)
        
        return {"token": session.token, "user": user.to_dict()}
    
    def login(self, username, password) -> dict:
        username = username.strip()
        
        user = self._user_repo.get_user_by_username(username)
        if user is None:
            raise AuthError("Неверный логин или пароль [LOGIN]")
        
        if not self._hasher.verify(password, user.get_hash_password):
            raise AuthError("Неверный пароль [LOGIN]")
        session = self._session_repo.create_session(user.id)
        
        return {"token": session.token, "user":user.to_dict()}
    
    def get_current_user(self, token) -> User:
        session = self._session_repo.get_by_token(token)
        if session is None:
            raise AuthError("not found by token [GET CURRENT USER]")
        return self._user_repo.get_user_by_id(session.user_id)
    
    def logout(self, token) -> None:
        if self._session_repo.get_by_token(token) == None:
            raise AuthError(f"[LOGOUT] not found by token")
        self._session_repo.delete_by_token(token)
        
        