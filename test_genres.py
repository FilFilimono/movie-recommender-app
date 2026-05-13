# test_filter.py
from backend.core.config import AppConfig
from backend.ml.loader import ModelLoader
from backend.ml.recommender import RecommenderEngine
from backend.ml.metadata_store import MetadataStore
from sentence_transformers import SentenceTransformer

loader = ModelLoader(AppConfig)
loader.load()
metadata = MetadataStore(AppConfig.METADATA_PATH)
metadata.load()
engine = RecommenderEngine(loader)

criteria = {'genres': ['Family'], 'year_from': 1986, 'year_to': 2024, 'min_rating': 6.0}

# Смотрим сколько KNN возвращает ДО фильтрации
raw = engine.recommend(criteria, n=200)
print(f"KNN вернул: {len(raw)} кандидатов")

movie_ids = metadata.get_all_movie_ids()
passed = 0
no_genre = 0
no_poster = 0
low_rating = 0

for item in raw:
    idx = item['matrix_index']
    if idx >= len(movie_ids): continue
    data = metadata.get_by_id(int(movie_ids[idx]))
    if not data: continue
    
    genres = [g.lower() for g in data.get('genres', [])]
    has_genre = 'family' in genres
    has_poster = bool(data.get('poster_url'))
    rating = float(data.get('tmdb_rating') or 0)
    
    if not has_genre: no_genre += 1
    if not has_poster: no_poster += 1
    if rating < 4.0: low_rating += 1
    if has_genre: passed += 1

print(f"Прошли фильтр жанра: {passed}")
print(f"Срезано по жанру: {no_genre}")
print(f"Срезано по постеру: {no_poster}")
print(f"Срезано по рейтингу <4: {low_rating}")