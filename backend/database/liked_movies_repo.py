from __future__ import annotations

from backend.database.manager import DatabaseManager


class LikedMoviesRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def add_like(self, user_id: int, movie_id: int) -> bool:
        """
        Добавить лайк. Возвращает True, если строка вставлена,
        False если пара (user_id, movie_id) уже была (UNIQUE).
        """
        cur = self.db_manager.execute(
            "INSERT OR IGNORE INTO liked_movies (user_id, movie_id) VALUES (?, ?)",
            (user_id, movie_id),
        )
        self.db_manager.commit()
        return cur.rowcount > 0

    def remove_like(self, user_id: int, movie_id: int) -> bool:
        """Удалить лайк. True, если что-то удалили."""
        cur = self.db_manager.execute(
            "DELETE FROM liked_movies WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id),
        )
        self.db_manager.commit()
        return cur.rowcount > 0

    def is_liked(self, user_id: int, movie_id: int) -> bool:
        row = self.db_manager.execute(
            """
            SELECT 1 FROM liked_movies
            WHERE user_id = ? AND movie_id = ?
            LIMIT 1
            """,
            (user_id, movie_id),
        ).fetchone()
        return row is not None

    def list_movie_ids_by_user(self, user_id: int) -> list[int]:
        rows = self.db_manager.execute(
            "SELECT movie_id FROM liked_movies WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [int(r["movie_id"]) for r in rows]
