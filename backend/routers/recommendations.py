from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel as PydanticBase
from sklearn.preprocessing import normalize as sk_normalize
from backend.entities.requests import PreferencesRequest
from backend.services.auth_service import AuthorizationService, AuthError
from backend.ml.recommend_service import RecommendationService
from backend.database.prefs_repo import PreferencesRepository
from backend.database.liked_movies_repo import LikedMoviesRepository
from backend.entities.user import UserPreferences
import numpy as np

router = APIRouter(prefix="/api", tags=["recommendations"])

_auth_service: Optional[AuthorizationService]  = None
_recommend_service: Optional[RecommendationService] = None
_prefs_repo: Optional[PreferencesRepository] = None
_liked_repo: Optional[LikedMoviesRepository] = None


def init(auth: AuthorizationService,recommend: RecommendationService,prefs: PreferencesRepository,liked: LikedMoviesRepository,) -> None:
    global _auth_service, _recommend_service, _prefs_repo, _liked_repo
    _auth_service = auth
    _recommend_service = recommend
    _prefs_repo = prefs
    _liked_repo = liked


def _get_token(authorization: Optional[str]) -> str:
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Токен не передан")
    return authorization.split(" ", 1)[1]


def _get_user_id(authorization: Optional[str]) -> int:
    token = _get_token(authorization)
    try:
        user = _auth_service.get_current_user(token)
        return user.id
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))

class ByLikesRequest(PydanticBase):
    movie_ids: list[int]
    n: int = 50
    
@router.post("/recommendations/by-likes")
def recommendations_by_likes(
    body: ByLikesRequest,
    authorization: str = Header(None),
):
    _get_user_id(authorization)

    if not body.movie_ids:
        raise HTTPException(status_code=400, detail="Список пустой")

    movie_ids_map = _recommend_service._metadata.get_all_movie_ids()
    id_to_idx     = {mid: i for i, mid in enumerate(movie_ids_map)}
    matrix        = _recommend_service._engine._loader.feature_matrix
    knn           = _recommend_service._engine._loader.knn

    indices = [id_to_idx[mid] for mid in body.movie_ids if mid in id_to_idx]
    if not indices:
        raise HTTPException(status_code=400, detail="Фильмы не найдены")

    vecs    = matrix[indices]
    avg_vec = np.asarray(vecs.mean(axis=0))
    avg_vec = sk_normalize(avg_vec, norm='l2')

    n_search = min(body.n * 5, matrix.shape[0])
    distances, nbrs = knn.kneighbors(avg_vec, n_neighbors=n_search)

    liked_set  = set(body.movie_ids)
    candidates = []

    for idx, dist in zip(nbrs[0], distances[0]):
        movie_id = int(movie_ids_map[idx])
        if movie_id in liked_set:
            continue

        data = _recommend_service._metadata.get_by_id(movie_id)
        if not data or not data.get('poster_url'):
            continue

        votes   = float(data.get('tmdb_votes')  or 0)
        revenue = float(data.get('revenue')     or 0)
        rating  = float(data.get('tmdb_rating') or 0)
        budget  = float(data.get('budget')      or 0)

        if votes  < 500: continue
        if rating < 5.0: continue

        candidates.append({
            'movie_id': movie_id,
            'data':     data,
            'dist':     float(dist),
            'votes':    votes,
            'revenue':  revenue,
            'rating':   rating,
            'budget':   budget,
        })

    if not candidates:
        return []

    max_votes   = max(c['votes']   for c in candidates) or 1
    max_revenue = max(c['revenue'] for c in candidates) or 1
    max_budget  = max(c['budget']  for c in candidates) or 1

    def quality_score(c):
        sim = float(max(0.0, 1.0 - c['dist']))
        return (
            sim                          * 0.30 +
            (c['revenue'] / max_revenue) * 0.30 +
            (c['votes']   / max_votes)   * 0.25 +
            (c['rating']  / 10.0)        * 0.10 +
            (c['budget']  / max_budget)  * 0.05
        )

    candidates.sort(key=quality_score, reverse=True)

    from backend.entities.movie import Movie
    result = []
    for c in candidates[:body.n]:
        d   = c['data']
        sim = float(max(0.0, 1.0 - c['dist']))
        result.append(Movie(
            movie_id    = c['movie_id'],
            title       = d.get('title', ''),
            similarity  = sim,
            poster_url  = d.get('poster_url'),
            overview    = d.get('overview'),
            genres      = d.get('genres', []),
            cast        = d.get('cast', []),
            director    = d.get('director'),
            release_year= _recommend_service._parse_year(d.get('release_date')),
            runtime     = d.get('runtime'),
            rating      = d.get('tmdb_rating'),
        ).to_dict())

    return result


@router.post("/preferences")
def save_preferences(
    body: PreferencesRequest,
    authorization: str = Header(None),
):

    user_id = _get_user_id(authorization)
    print(f"[PREFS] Получено: {body.dict()}")
    prefs = UserPreferences(
        user_id = user_id,
        genres = body.genres,
        cast = body.cast,
        director = body.director,
        year_from = body.year_from,
        year_to = body.year_to,
        min_rating = body.min_rating,
        max_runtime = body.max_runtime,
        keywords = body.keywords,
        certification = body.certification,
    )
    _prefs_repo.save_by_user_id(prefs, user_id)
    return {"ok": True}


@router.get("/preferences")
def get_preferences(authorization: str = Header(None)):
    user_id = _get_user_id(authorization)
    prefs = _prefs_repo.get_by_user_id(user_id)
    if prefs is None:
        return None
    return prefs.to_dict()




@router.get("/recommendations")
def get_recommendations(
    n: int = 100,
    offset: int = 0,
    authorization: str = Header(None),
):

    user_id = _get_user_id(authorization)
    if not _prefs_repo.exists(user_id):
        raise HTTPException(status_code=400, detail="Сначала пройдите тест")
    movies = _recommend_service.get_for_user(user_id, n=n, offset=offset)
    return [movie.to_dict() for movie in movies]




@router.post("/like/{movie_id}")
def like_movie(
    movie_id: int,
    authorization: str = Header(None),
):

    user_id = _get_user_id(authorization)
    added = _liked_repo.add_like(user_id, movie_id)
    return {"ok": True, "added": added}


@router.delete("/like/{movie_id}")
def unlike_movie(
    movie_id: int,
    authorization: str = Header(None),
):

    user_id = _get_user_id(authorization)
    removed = _liked_repo.remove_like(user_id, movie_id)
    return {"ok": True, "removed": removed}


@router.get("/likes")
def get_likes(authorization: str = Header(None)):

    user_id = _get_user_id(authorization)
    return {"movie_ids": _liked_repo.list_movie_ids_by_user(user_id)}