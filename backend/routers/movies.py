from fastapi import APIRouter, HTTPException
from typing import Optional

from backend.ml.recommend_service import RecommendationService

router = APIRouter(prefix="/api", tags=["movies"])

_recommend_service: Optional[RecommendationService] = None


def init(recommend: RecommendationService) -> None:
    global _recommend_service
    _recommend_service = recommend


@router.get("/movie/{movie_id}")
def get_movie(movie_id: int):
   
    data = _recommend_service.get_movie_detail(movie_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Фильм не найден")
    return data