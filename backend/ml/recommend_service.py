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

    def get_for_user(self, user_id: int, n: int = 100, offset: int = 0) -> list[Movie]:
        prefs    = self._prefs_repo.get_by_user_id(user_id)
        if prefs is None: return []
        criteria = prefs.to_criteria_dict()

        raw = self._engine.recommend(criteria, n=1000)

        movies = []
        for item in raw:
            matrix_idx = item["matrix_index"]
            if matrix_idx >= len(self._movie_ids): continue
            movie_id = int(self._movie_ids[matrix_idx])
            data = self._metadata.get_by_id(movie_id)
            if data is None: continue
            if not self._passes_filters(data, criteria): continue

            revenue = float(data.get("revenue")     or 0)
            votes   = float(data.get("tmdb_votes")  or 0)
            rating  = float(data.get("tmdb_rating") or 0)
            budget  = float(data.get("budget")      or 0)

            movies.append({
                "movie": Movie(
                    movie_id    = movie_id,
                    title       = data.get("title", ""),
                    similarity  = item["similarity"],
                    poster_url  = data.get("poster_url"),
                    overview    = data.get("overview"),
                    genres      = data.get("genres", []),
                    cast        = data.get("cast", []),
                    director    = data.get("director"),
                    release_year= self._parse_year(data.get("release_date")),
                    runtime     = data.get("runtime"),
                    rating      = rating,
                ),
                "revenue": revenue,
                "votes":   votes,
                "rating":  rating,
                "budget":  budget,
            })

        if not movies: return []

        max_revenue = max(m["revenue"] for m in movies) or 1
        max_votes   = max(m["votes"]   for m in movies) or 1
        max_budget  = max(m["budget"]  for m in movies) or 1

        def sort_key(m):
            return (
                m["movie"].similarity      * 0.40 +
                (m["revenue"]/max_revenue) * 0.25 +
                (m["votes"]  /max_votes)   * 0.20 +
                (m["rating"] /10.0)        * 0.10 +
                (m["budget"] /max_budget)  * 0.05
            )

        movies.sort(key=sort_key, reverse=True)

        # offset позволяет получить следующую "страницу" рекомендаций
        # При offset=0 — топ 100, при offset=100 — следующие 100
        all_sorted = [m["movie"] for m in movies]
        start = offset % max(len(all_sorted), 1)
        # Берём n фильмов начиная с offset, по кругу
        result = []
        for i in range(n):
            idx = (start + i) % len(all_sorted)
            result.append(all_sorted[idx])
        return result

    def get_movie_detail(self, movie_id: int) -> dict | None:
        return self._metadata.get_by_id(movie_id)


    def _passes_filters(self, data: dict, criteria: dict) -> bool:
        votes  = float(data.get("tmdb_votes")  or 0)
        rating = float(data.get("tmdb_rating") or 0)
        year   = self._parse_year(data.get("release_date"))

        min_votes = 50 if (year and year < 2000) else 200
        if votes  < min_votes:           return False
        if rating < 5.0:                 return False
        if not data.get("poster_url"):   return False

        if year:
            if criteria.get("year_from", 1970) > 1970:
                if year < criteria["year_from"]: return False
            if criteria.get("year_to", 2024) < 2024:
                if year > criteria["year_to"]:   return False

        if criteria.get("min_rating"):
            if rating < float(criteria["min_rating"]): return False

        runtime = data.get("runtime")
        if runtime and criteria.get("max_runtime", 240) < 240:
            if int(runtime) > criteria["max_runtime"]: return False

        cert_filter = (criteria.get("certification") or "").strip()
        if cert_filter:
            allowed = [c.strip() for c in cert_filter.split(",") if c.strip()]
            if allowed:
                movie_cert = (data.get("certification") or "").strip()
                print(f"[CERT] movie={movie_cert!r} allowed={allowed} pass={movie_cert in allowed}")
                if not movie_cert or movie_cert not in allowed:
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