import json

from backend.database.manager import DatabaseManager
from backend.entities.user import UserPreferences


class PreferencesRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_by_user_id(self, user_id: int) -> UserPreferences | None:
        row = self.db_manager.execute(
            "SELECT user_id, data FROM preferences WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        try:
            payload = json.loads(row["data"])
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Некорректный JSON в preferences для user_id={user_id}") from e
        return self._dict_to_preferences(int(row["user_id"]), payload)

    def save_by_user_id(self, prefs: UserPreferences, user_id: int) -> None:
        if prefs.user_id != user_id:
            raise ValueError(
                f"prefs.user_id ({prefs.user_id}) не совпадает с user_id ({user_id})"
            )
        data = json.dumps(self._preferences_payload(prefs), ensure_ascii=False)
        self.db_manager.execute(
            """
            INSERT INTO preferences (user_id, data) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                data = excluded.data,
                updated_at = datetime('now')
            """,
            (user_id, data),
        )
        self.db_manager.commit()

    def delete_by_user_id(self, user_id: int) -> None:
        self.db_manager.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,))
        self.db_manager.commit()

    def exists(self, user_id: int) -> bool:
        row = self.db_manager.execute(
            "SELECT 1 FROM preferences WHERE user_id = ? LIMIT 1",
            (user_id,),
        ).fetchone()
        return row is not None

    @staticmethod
    def _preferences_payload(prefs: UserPreferences) -> dict:
        return {
            "genres": prefs.genres,
            "cast": prefs.cast,
            "director": prefs.director,
            "year_from": prefs.year_from,
            "year_to": prefs.year_to,
            "min_rating": prefs.min_rating,
            "max_runtime": prefs.max_runtime,
            "certification": prefs.certification,
        }

    @staticmethod
    def _dict_to_preferences(user_id: int, d: dict) -> UserPreferences:
        return UserPreferences(
            user_id=user_id,
            genres=d.get("genres") or [],
            cast=d.get("cast") or [],
            director=d.get("director", ""),
            year_from=d.get("year_from", 1970),
            year_to=d.get("year_to", 2024),
            min_rating=d.get("min_rating"),
            max_runtime=d.get("max_runtime", 240),
            certification=d.get("certification", ""),
        )
