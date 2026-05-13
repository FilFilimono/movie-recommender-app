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
        print(f"[DEBUG] criteria: {criteria}")
        print(f"[DEBUG] n запрошено: {n}")

        raw = self._engine.recommend(criteria, n=n * 10)
        print(f"[DEBUG] KNN вернул: {len(raw)} кандидатов")

        movies = []
        skipped_filter = 0
        skipped_none = 0

        for item in raw:
            matrix_idx = item["matrix_index"]
            similarity  = item["similarity"]

            if matrix_idx >= len(self._movie_ids):
                continue
            movie_id = int(self._movie_ids[matrix_idx])
            data = self._metadata.get_by_id(movie_id)
            if data is None:
                skipped_none += 1
                continue

            if not self._passes_filters(data, criteria):
                skipped_filter += 1
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
        def sort_key(m):
           
            data = self._metadata.get_by_id(m.movie_id)
            revenue    = float(data.get("revenue")    or 0)
            votes      = float(data.get("tmdb_votes") or 0)
            rating     = float(m.rating               or 0)

            revenue_score = min(revenue / 2_923_706_026, 1.0)
            
            votes_score = min(votes / 39367, 1.0)

            score = (
                m.similarity          * 0.50 +
                revenue_score         * 0.25 +
                (rating / 10)         * 0.10 +
                votes_score           * 0.15
            )
            return score    

        movies.sort(key=sort_key, reverse=True)
        
        print(f"[DEBUG] Срезано фильтром: {skipped_filter}")
        print(f"[DEBUG] Не найдено в metadata: {skipped_none}")
        print(f"[DEBUG] Итого фильмов: {len(movies)}")

        return movies[:n]

    def get_movie_detail(self, movie_id: int) -> dict | None:
        return self._metadata.get_by_id(movie_id)


    def _passes_filters(self, data: dict, criteria: dict) -> bool:

        # Минимум голосов — убирает неизвестные фильмы
        votes = float(data.get("tmdb_votes") or 0)
        if votes < 200:        # ← минимум 200 голосов
            return False

        # Минимальный рейтинг по умолчанию
        rating = float(data.get("tmdb_rating") or 0)
        if rating < 5.0:       # ← совсем плохие не показываем
            return False

        # Постер обязателен
        if not data.get("poster_url"):
            return False

        # Год
        year = self._parse_year(data.get("release_date"))
        if year:
            if criteria.get("year_from", 1970) > 1970:
                if year < criteria["year_from"]:
                    return False
            if criteria.get("year_to", 2024) < 2024:
                if year > criteria["year_to"]:
                    return False

        # Рейтинг если задан юзером
        if criteria.get("min_rating"):
            if rating < float(criteria["min_rating"]):
                return False

        # Хронометраж если задан
        runtime = data.get("runtime")
        if runtime and criteria.get("max_runtime", 240) < 240:
            if int(runtime) > criteria["max_runtime"]:
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