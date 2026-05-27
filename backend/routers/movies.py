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

@router.get("/search")
def search_movies(q: str = "",page: int = 1,limit: int = 30,sort: str = "votes",):
    
    if not q or len(q) < 2:
        return {"movies": [], "total": 0, "page": 1}

    df = _recommend_service._metadata._df
    q_lower = q.lower()

    
    mask   = df['title'].str.lower().str.contains(q_lower, na=False)
    result = df[mask].copy()

    
    if sort == 'rating':
        result = result.sort_values('tmdb_rating', ascending=False, na_position='last')
    elif sort == 'year':
        result = result.sort_values('release_date', ascending=False, na_position='last')
    elif sort == 'title':
        result = result.sort_values('title', ascending=True, na_position='last')
    else:  # votes — по умолчанию
        result = result.sort_values('tmdb_votes', ascending=False, na_position='last')

    total = len(result)
    start = (page - 1) * limit
    page_df = result.iloc[start:start + limit]

    movies = page_df.to_dict(orient='records')
    
    import math
    def clean(v):
        if isinstance(v, float) and math.isnan(v): return None
        return v
    movies = [{k: clean(v) for k,v in m.items()} for m in movies]

    return {"movies": movies, "total": total, "page": page}