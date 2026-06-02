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


@router.get("/movie/{movie_id}/similar")
def get_similar(movie_id: int, n: int = 15, offset: int = 0):
    movie_ids_map = _recommend_service._metadata.get_all_movie_ids()
    id_to_idx     = {mid: i for i, mid in enumerate(movie_ids_map)}

    if movie_id not in id_to_idx:
        raise HTTPException(status_code=404, detail="Фильм не найден")

    source = _recommend_service._metadata.get_by_id(movie_id)
    if not source:
        raise HTTPException(status_code=404, detail="Фильм не найден")

    import ast, re
    def safe_list(v):
        if not v: return []
        if isinstance(v, list): return v
        try: return ast.literal_eval(str(v))
        except: return [x.strip() for x in str(v).split(',') if x.strip()]

    source_title    = (source.get('title') or '').strip()
    source_director = (source.get('director') or '').lower().strip()
    source_genres   = {g.lower() for g in safe_list(source.get('genres'))}
    source_cast     = {
        (c['name'].lower() if isinstance(c, dict) else str(c).lower())
        for c in safe_list(source.get('cast'))[:5]
    }
    
    src_words = {w.lower() for w in re.findall(r'\w+', source_title) if len(w) > 2}
    
    matrix = _recommend_service._engine._loader.feature_matrix
    knn    = _recommend_service._engine._loader.knn
    idx    = id_to_idx[movie_id]
    n_search = min(500, matrix.shape[0])
    distances, indices = knn.kneighbors(matrix[idx], n_neighbors=n_search)

    sequels      = []  
    genre_only   = []  
    cast_genre   = []  
    genre_dir    = []  
    director     = []  

    for i, dist in zip(indices[0], distances[0]):
        mid = int(movie_ids_map[i])
        if mid == movie_id: continue
        data = _recommend_service._metadata.get_by_id(mid)
        if not data or not data.get('poster_url'): continue

        votes   = float(data.get('tmdb_votes')  or 0)
        revenue = float(data.get('revenue')     or 0)
        rating  = float(data.get('tmdb_rating') or 0)
        budget  = float(data.get('budget')      or 0)

        if votes < 50 or rating < 4.0: continue

        title    = (data.get('title') or '').strip()
        tgt_dir  = (data.get('director') or '').lower().strip()
        tgt_gen  = {g.lower() for g in safe_list(data.get('genres'))}
        tgt_cast = {
            (c['name'].lower() if isinstance(c, dict) else str(c).lower())
            for c in safe_list(data.get('cast'))[:5]
        }
        tgt_words = {w.lower() for w in re.findall(r'\w+', title) if len(w) > 2}

        common_words  = src_words & tgt_words
        common_genres = source_genres & tgt_gen
        same_director = source_director and tgt_dir == source_director
        common_cast   = source_cast & tgt_cast
        
        if not common_genres and not same_director:
            continue  

        item = {
            'movie_id': mid, 'data': data, 'dist': float(dist),
            'votes': votes, 'revenue': revenue,
            'rating': rating, 'budget': budget,
            'common_genres_count': len(common_genres),  
        }

        
        if common_words and title != source_title:
            sequels.append(item)
        
        elif common_genres and not same_director and not common_cast:
            genre_only.append(item)
        
        elif common_cast and common_genres:
            cast_genre.append(item)
        
        elif same_director and common_genres:
            
            if len(common_genres) >= 2:
                genre_dir.append(item)
        
        elif same_director and not common_genres:
            director.append(item)

    def quality(c):
        max_r = 2_000_000_000
        max_v = 50_000
        
        genre_bonus = c.get('common_genres_count', 0) * 0.05
        return (
            (c['revenue'] / max_r)  * 0.35 +
            (c['votes']   / max_v)  * 0.25 +
            (c['rating']  / 10.0)   * 0.20 +
            (c['budget']  / 200_000_000) * 0.10 +
            genre_bonus
        )

    
    for lst in [sequels, genre_only, cast_genre, genre_dir, director]:
        lst.sort(key=quality, reverse=True)

    
    
    must_have = sequels  
    
    pool = genre_only + cast_genre + genre_dir + director
    
    
    slots = n - len(must_have)
    if slots > 0:
        pool_start = offset % max(len(pool), 1)
        for i in range(slots):
            if not pool:
                break
            must_have.append(pool[(pool_start + i) % len(pool)])

    final = must_have

    
    seen = set()
    unique = []
    for c in final:
        if c['movie_id'] not in seen:
            seen.add(c['movie_id'])
            unique.append(c)

    from backend.entities.movie import Movie
    result = []
    for c in unique[:n]:
        d = c['data']
        result.append(Movie(
            movie_id    = c['movie_id'],
            title       = d.get('title',''),
            similarity  = max(0.0, 1.0 - c['dist']),
            poster_url  = d.get('poster_url'),
            overview    = d.get('overview'),
            genres      = safe_list(d.get('genres')),
            cast        = safe_list(d.get('cast')),
            director    = d.get('director'),
            release_year= _recommend_service._parse_year(d.get('release_date')),
            runtime     = d.get('runtime'),
            rating      = d.get('tmdb_rating'),
        ).to_dict())

    return result

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
    else:  
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