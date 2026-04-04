import secrets

from backend.database.manager import DatabaseManager
from backend.entities.session import Session


class SessionRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def create_session(self, user_id: int) -> Session:
        """Создаёт новую сессию: токен генерируем мы, БД только хранит строку."""
        token = secrets.token_urlsafe(32)
        self.db_manager.execute(
            "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
            (token, user_id),
        )
        self.db_manager.commit()
        row = self.db_manager.execute(
            "SELECT * FROM sessions WHERE token = ?", (token,)
        ).fetchone()
        if row is None:
            raise RuntimeError("Сессия не найдена сразу после INSERT")
        return self._row_to_session(row)

    def get_by_token(self, token: str) -> Session | None:
        row = self.db_manager.execute(
            "SELECT * FROM sessions WHERE token = ?", (token,)
        ).fetchone()
        return self._row_to_session(row)

    def delete_by_token(self, token: str) -> None:
        self.db_manager.execute("DELETE FROM sessions WHERE token = ?", (token,))
        self.db_manager.commit()

    def delete_all_for_user(self, user_id: int) -> None:
        self.db_manager.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        self.db_manager.commit()

    def _row_to_session(self, row) -> Session | None:
        if row is None:
            return None
        return Session(
            token=row["token"],
            user_id=row["user_id"],
            created_at=row["created_at"],
        )
