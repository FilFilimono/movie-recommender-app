from backend.entities.user import User
from backend.database.manager import DatabaseManager

class UserRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_user(self, user: User) -> User:
        cursor = self.db_manager.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (user.username, user.get_hash_password),
        )
        self.db_manager.commit()
        new_id = cursor.lastrowid
        if not new_id:
            raise RuntimeError("INSERT не вернул id (lastrowid пустой)")
        row = self.db_manager.execute(
            "SELECT * FROM users WHERE id = ?", (new_id,)
        ).fetchone()
        if row is None:
            raise RuntimeError(
                f"Пользователь с id={new_id} не найден сразу после INSERT"
            )
        return self._row_to_user(row)
        
        
    
    def get_user_by_id(self, user_id) -> User | None:
        row = self.db_manager.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()    
        return self._row_to_user(row) 
    
    def get_user_by_username(self, username) -> User | None:
        row =  self.db_manager.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return self._row_to_user(row)
    
    def exists_user(self, username) -> bool:
        return self.db_manager.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,)).fetchone()[0] > 0
    
    def _row_to_user(self, row) -> User | None:
        if row is None:
            return None
        return User(
            id=row["id"],
            username=row["username"],
            hash_password=row["password_hash"],
            created_at=row["created_at"],
        )