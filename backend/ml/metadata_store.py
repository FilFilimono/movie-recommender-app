import pandas as pd
import ast
from typing import Optional

from backend.core.config import AppConfig


class MetadataStore:

    def __init__(self, csv_path: str = AppConfig.METADATA_PATH):
        self._csv_path = csv_path
        self._df: Optional[pd.DataFrame] = None
        self._index: Optional[pd.DataFrame] = None

    def load(self) -> None:
        self._df    = pd.read_csv(self._csv_path)
        self._index = self._df.set_index("movie_id")
        print(f"[Metadata] Загружено фильмов: {len(self._df)}")

    def is_loaded(self) -> bool:
        return self._df is not None

    def get_all_movie_ids(self) -> list[int]:
        
        self._check_loaded()
        return self._df["movie_id"].tolist()

    def get_by_id(self, movie_id: int) -> Optional[dict]:
        self._check_loaded()
        try:
            row = self._index.loc[movie_id]
        except KeyError:
            return None
        return self._row_to_dict(movie_id, row)

    def get_many(self, movie_ids: list[int]) -> list[dict]:
        return [
            d for mid in movie_ids
            if (d := self.get_by_id(mid)) is not None
        ]


    def _row_to_dict(self, movie_id: int, row) -> dict:
        return {
            "movie_id": int(movie_id),
            "title": self._safe_str(row.get("title")),
            "overview": self._safe_str(row.get("overview")),
            "tagline": self._safe_str(row.get("tagline")),
            "poster_url": self._safe_str(row.get("poster_url")),
            "director": self._safe_str(row.get("director")),
            "certification": self._safe_str(row.get("certification")),
            "release_date": self._safe_str(row.get("release_date")),
            "runtime": self._safe_int(row.get("runtime")),
            "tmdb_rating": self._safe_float(row.get("tmdb_rating")),
            "tmdb_votes": self._safe_int(row.get("tmdb_votes")),
            "budget": self._safe_int(row.get("budget")),
            "revenue": self._safe_int(row.get("revenue")),
            "genres": self._parse_list(row.get("genres")),
            "cast": self._parse_cast(row.get("cast")),
            "keywords": self._parse_list(row.get("keywords")),
        }

    def _parse_list(self, value) -> list[str]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        try:
            parsed = ast.literal_eval(str(value))
            return [str(x) for x in parsed] if isinstance(parsed, list) else []
        except Exception:
            return [x.strip() for x in str(value).split(",") if x.strip()]

    def _parse_cast(self, value) -> list[dict]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        try:
            parsed = ast.literal_eval(str(value))
            if isinstance(parsed, list):
                return parsed[:5]
        except Exception:
            pass
        return []

    @staticmethod
    def _safe_str(value) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, float) and pd.isna(value):
            return None
        return str(value)

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        try:
            return None if pd.isna(value) else int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        try:
            return None if pd.isna(value) else float(value)
        except (TypeError, ValueError):
            return None

    def _check_loaded(self) -> None:
        if self._df is None:
            raise RuntimeError("MetadataStore не загружен. Вызови load()")