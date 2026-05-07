from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from backend.entities.requests import PreferencesRequest
from backend.services.auth_service import AuthorizationService, AuthError
from backend.ml.recommend_service import RecommendationService
from backend.database.prefs_repo import PreferencesRepository
from backend.database.liked_movies_repo import LikedMoviesRepository
from backend.entities.user import UserPreferences

router = APIRouter(prefix="/api", tags=["recommendations"])

_auth_service: Optional[AuthorizationService]  = None
_recommend_service: Optional[RecommendationService] = None
_prefs_repo: Optional[PreferencesRepository] = None
_liked_repo: Optional[LikedMoviesRepository] = None


def init(
    auth:      AuthorizationService,
    recommend: RecommendationService,
    prefs:     PreferencesRepository,
    liked:     LikedMoviesRepository,
) -> None:
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



@router.post("/preferences")
def save_preferences(
    body: PreferencesRequest,
    authorization: str = Header(None),
):

    user_id = _get_user_id(authorization)
    prefs = UserPreferences(
        user_id     = user_id,
        genres      = body.genres,
        cast        = body.cast,
        director    = body.director,
        year_from   = body.year_from,
        year_to     = body.year_to,
        min_rating  = body.min_rating,
        max_runtime = body.max_runtime,
        keywords    = body.keywords,
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
    n: int = 15,
    authorization: str = Header(None),
):

    user_id = _get_user_id(authorization)

    if not _prefs_repo.exists(user_id):
        raise HTTPException(
            status_code=400,
            detail="Сначала пройдите тест предпочтений"
        )

    movies = _recommend_service.get_for_user(user_id, n=n)
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