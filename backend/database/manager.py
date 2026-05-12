import sqlite3
import os
from typing import Optional

from backend.core.config import AppConfig


class DatabaseManager:


    def __init__(self, db_path: str = AppConfig.DB_PATH):
        
        self._db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None


    def connect(self) -> None:
       
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

        self._connection = sqlite3.connect(
            self._db_path,
            check_same_thread=False
            )

        self._connection.row_factory = sqlite3.Row

        self._connection.execute("PRAGMA foreign_keys = ON")

        print(f"[DB] Подключено: {self._db_path}")


    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            print("[DB] Соединение закрыто")


    

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise RuntimeError(
                "Нет соединения с базой данных. Вызови сначала connect()"
            )
        return self._connection


    

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        
        return self.connection.execute(sql, params)


    def commit(self) -> None:
        self.connection.commit()


   
    def initialize(self) -> None:
        
        self._create_users_table()
        self._create_sessions_table()
        self._create_preferences_table()
        self._create_liked_movies_table()

        
        self._connection.commit()
        print("[DB] Таблицы готовы")


    def _create_users_table(self) -> None: 
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    DEFAULT (datetime('now'))
            )
        """)


    def _create_sessions_table(self) -> None:
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT    PRIMARY KEY,
                user_id    INTEGER NOT NULL,
                created_at TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


    def _create_preferences_table(self) -> None:
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL UNIQUE,
                data       TEXT    NOT NULL,
                updated_at TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


    def _create_liked_movies_table(self) -> None:
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS liked_movies (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                movie_id   INTEGER NOT NULL,
                created_at TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, movie_id)
            )
        """)