# test_recommend.py — запусти заново
from backend.core.config import AppConfig
from backend.ml.loader import ModelLoader
from backend.ml.recommender import RecommenderEngine
from backend.ml.metadata_store import MetadataStore

loader = ModelLoader(AppConfig)
loader.load()

metadata = MetadataStore(AppConfig.METADATA_PATH)
metadata.load()

engine = RecommenderEngine(loader)

r1 = engine.recommend({'genres': ['Action']})
r2 = engine.recommend({'genres': ['Romance']})
r3 = engine.recommend({'genres': ['Horror']})

ids1 = [x['matrix_index'] for x in r1[:5]]
ids2 = [x['matrix_index'] for x in r2[:5]]
ids3 = [x['matrix_index'] for x in r3[:5]]

print("Action:  ", ids1)
print("Romance: ", ids2)
print("Horror:  ", ids3)
print("Одинаковые?", ids1 == ids2)

# Смотрим реальные названия фильмов
movie_ids_map = metadata._df['movie_id'].tolist()
for label, ids in [("Action", ids1), ("Romance", ids2), ("Horror", ids3)]:
    print(f"\n{label}:")
    for idx in ids:
        mid = movie_ids_map[idx]
        data = metadata.get_by_id(mid)
        if data:
            print(f"  {data['title']} ({data.get('release_date','')[:4]})")