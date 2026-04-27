import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.preprocessing import normalize


from backend.ml.loader import ModelLoader


class RecommenderEngine:
    """
    Обёртка над KNN моделью.

    Принимает criteria dict от пользователя →
    строит вектор запроса (tfidf + embedding + числа) →
    ищет ближайших соседей в feature_matrix →
    возвращает список фильмов с similarity.
    """

    
    NUM_FEATURES_COUNT = 7

    
    _NUM_DEFAULTS = { #FIXME Пересмотреть медианные значения 
        "runtime":    95.0,
        "popularity": 15.0,
        "budget":     20_000_000.0,
        "revenue":    50_000_000.0,
        "tmdb_rating": 7.0,
        "tmdb_votes": 1000.0,
        "year":       2005.0,
    }

    def __init__(self, loader: ModelLoader):
        self._loader = loader

    def recommend(self, criteria: dict, n: int = 15,) -> list[dict]:
        
        
        tfidf_vector = self._build_tfidf_vector(criteria)
        
        emb_vector = self._build_embedding_vector(criteria)
        
        num_vector = self._build_num_vector(criteria)

       
        query = hstack([num_vector, tfidf_vector, emb_vector])
        query = normalize(query, norm="l2")

       
        n_search = min(n * 2, self._loader.feature_matrix.shape[0])
        distances, indices = self._loader.knn.kneighbors(query, n_neighbors=n_search)


        results = self._build_results(indices[0], distances[0], n)
        return results

    

    def _build_tfidf_vector(self, criteria: dict):
        
        parts = []

        if criteria.get("genres"):
            genres_text = " ".join(
                g.lower().replace(" ", "_") for g in criteria["genres"]
            )
            parts.append(genres_text)

        if criteria.get("keywords"):
            kw_text = " ".join(
                k.lower().replace(" ", "_") for k in criteria["keywords"]
            )
            parts.append(kw_text)

        if criteria.get("director"):
            parts.append(
                criteria["director"].lower().replace(" ", "_")
            )

        if criteria.get("certification"):
            parts.append(criteria["certification"].lower())

        if criteria.get("cast"):
            cast_text = " ".join(
                c.lower().replace(" ", "_")
                for c in criteria["cast"][:5]
            )
            parts.append(cast_text)

        text = " ".join(parts) if parts else "movie"
        return self._loader.tfidf.transform([text])

    def _build_embedding_vector(self, criteria: dict):
        
        parts = []

        if criteria.get("genres"):
            parts.append(f"Genres: {', '.join(criteria['genres'])}")

        if criteria.get("keywords"):
            parts.append(f"Themes: {', '.join(criteria['keywords'])}")

        if criteria.get("cast"):
            parts.append(f"Cast: {', '.join(criteria['cast'])}")

        if criteria.get("director"):
            parts.append(f"Director: {criteria['director']}")

        text = " ".join(parts) if parts else "popular movie"

        vector = self._loader.embedder.encode(
            [text], normalize_embeddings=True
        )
        return csr_matrix(vector)

    def _build_num_vector(self, criteria: dict):
        
        d = self._NUM_DEFAULTS

        year_from = criteria.get("year_from", 1970)
        year_to   = criteria.get("year_to",   2024)
        year      = (year_from + year_to) / 2


        if criteria.get("max_runtime"):
            runtime = criteria["max_runtime"] * 0.75
        else:
            runtime = d["runtime"]

       
        min_rating = criteria.get("min_rating")
        rating = min_rating if min_rating is not None else d["tmdb_rating"]

        vec = pd.DataFrame([[runtime, d["popularity"], d["budget"], d["revenue"],
                     rating, d["tmdb_votes"], year]],
                   columns=['runtime','popularity','budget','revenue',
                            'tmdb_rating','tmdb_votes','year'])

       
        num_normalized = self._loader.scaler.transform(vec)
        return csr_matrix(num_normalized)

    

    def _build_results(self, indices: np.ndarray, distances: np.ndarray, n: int,) -> list[dict]:
        
        results = []
        for idx, dist in zip(indices, distances):
            similarity = float(max(0.0, 1 - dist))
            results.append({
                "matrix_index": int(idx),
                "similarity":   round(similarity, 4),
            })
            if len(results) >= n:
                break

        return results