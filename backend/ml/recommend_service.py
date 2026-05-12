from backend.ml.recommender import RecommenderEngine
from backend.ml.metadata_store import MetadataStore
from backend.database.prefs_repo import PreferencesRepository
from backend.entities.movie import Movie


class RecommendationService:
    
    def __init__( self, engine: RecommenderEngine, metadata: MetadataStore, prefs_repo: PreferencesRepository):
        
        self._engine     = engine
        self._metadata   = metadata
        self._prefs_repo = prefs_repo
        self._movie_ids: list[int] = self._metadata.get_all_movie_ids()
        print(f"[RecommendService] Индекс: {len(self._movie_ids)} фильмов")

    def get_for_user(self, user_id: int, n: int = 15) -> list[Movie]:
        prefs = self._prefs_repo.get_by_user_id(user_id)
        if prefs is None:
            return []

        criteria = prefs.to_criteria_dict()

      
        raw = self._engine.recommend(criteria, n=n * 5)

        movies = []
        for item in raw:
            matrix_idx = item["matrix_index"]
            similarity  = item["similarity"]

            if matrix_idx >= len(self._movie_ids):
                continue
            movie_id = int(self._movie_ids[matrix_idx])
            data     = self._metadata.get_by_id(movie_id)
            if data is None:
                continue

            if not self._passes_filters(data, criteria):
                continue

            if not data.get("poster_url"):
                continue
            if not data.get("tmdb_rating"):
                continue

            if float(data.get("tmdb_rating", 0)) < 4.0:
                continue

            if float(data.get("tmdb_votes", 0)) < 50:
                continue

            movies.append(Movie(
                movie_id    = movie_id,
                title       = data.get("title", ""),
                similarity  = similarity,
                poster_url  = data.get("poster_url"),
                overview    = data.get("overview"),
                genres      = data.get("genres", []),
                cast        = data.get("cast", []),
                director    = data.get("director"),
                release_year= self._parse_year(data.get("release_date")),
                runtime     = data.get("runtime"),
                rating      = data.get("tmdb_rating"),
            ))
        movies.sort(
            key=lambda m: (m.similarity * 0.6) + (float(m.rating or 0) / 10 * 0.4),
            reverse=True
        )

        return movies[:n]

    def get_movie_detail(self, movie_id: int) -> dict | None:
        return self._metadata.get_by_id(movie_id)


    def _passes_filters(self, data: dict, criteria: dict) -> bool:
       
        year = self._parse_year(data.get("release_date"))
        if year is not None:
            if criteria.get("year_from") and year < criteria["year_from"]:
                return False
            if criteria.get("year_to") and year > criteria["year_to"]:
                return False

        rating = data.get("tmdb_rating")
        if rating is not None and criteria.get("min_rating"):
            if rating < criteria["min_rating"]:
                return False

        runtime = data.get("runtime")
        if runtime is not None and criteria.get("max_runtime"):
            if runtime > criteria["max_runtime"]:
                return False

        return True

    @staticmethod
    def _parse_year(release_date) -> int | None:
       
        if not release_date:
            return None
        try:
            return int(str(release_date)[:4])
        except (ValueError, TypeError):
            return None