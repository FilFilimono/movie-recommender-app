import sqlite3
import os
from typing import Optional

from backend.core.config import AppConfig


class DatabaseManager:


    def __init__(self, db_path: str = AppConfig.DB_PATH):
        
        self._db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None


    def connect(self) -> None:
        """
        Открыть соединение с базой данных.

        SQLite хранит всю базу в одном файле — app.db
        Если файла нет — SQLite создаст его автоматически.
        """

        # Создаём папку "database/" если её нет
        # exist_ok=True — не падать с ошибкой если папка уже есть
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

        # Открываем (или создаём) файл базы данных
        # После этой строки файл app.db появится на диске
        self._connection = sqlite3.connect(self._db_path)

        # row_factory = sqlite3.Row — это очень важная настройка.
        # Без неё результаты запросов возвращаются как кортежи:
        #   row[0], row[1], row[2]  — неудобно и непонятно
        # С ней результаты как словари:
        #   row['id'], row['username']  — сразу понятно что есть что
        self._connection.row_factory = sqlite3.Row

        # Включаем поддержку FOREIGN KEY — по умолчанию в SQLite она ВЫКЛЮЧЕНА.
        # FOREIGN KEY — это связь между таблицами.
        # Например: preferences.user_id должен существовать в users.id
        # Без этой строки SQLite просто игнорирует эти связи.
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