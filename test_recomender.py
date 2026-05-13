# test_recommend.py
from backend.core.config import AppConfig
from backend.ml.loader import ModelLoader
from backend.ml.recommender import RecommenderEngine

loader = ModelLoader(AppConfig)
loader.load()
engine = RecommenderEngine(loader)

# Тест 1 — боевики
r1 = engine.recommend({'genres': ['Action'], 'min_rating': 7.0})
# Тест 2 — романтика
r2 = engine.recommend({'genres': ['Romance'], 'min_rating': 6.0})
# Тест 3 — ужасы
r3 = engine.recommend({'genres': ['Horror']})

print("Action:  ", [x['matrix_index'] for x in r1[:5]])
print("Romance: ", [x['matrix_index'] for x in r2[:5]])
print("Horror:  ", [x['matrix_index'] for x in r3[:5]])
print("Одинаковые?", r1[:5] == r2[:5])