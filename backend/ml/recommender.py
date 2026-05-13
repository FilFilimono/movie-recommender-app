import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.preprocessing import normalize


from backend.ml.loader import ModelLoader


class RecommenderEngine:
    
    NUM_FEATURES_COUNT = 7

    def __init__(self, loader: ModelLoader):
        self._loader = loader

    def recommend(self, criteria: dict, n: int = 50,) -> list[dict]: #FIXME n =15
        
        tfidf_vec = self._build_tfidf_vector(criteria)
        emb_vec   = self._build_embedding_vector(criteria)
        num_vec   = self._build_num_vector(criteria)

       
        query = hstack([
        num_vec   * 0.8,
        tfidf_vec * 3.0,
        emb_vec   * 2.0,
    ])
        query = normalize(query, norm="l2")

       
        n_search = min(n * 5, self._loader.feature_matrix.shape[0])
        distances, indices = self._loader.knn.kneighbors(query, n_neighbors=n_search)


        results = self._build_results(indices[0], distances[0], n)
        return results


    def _build_tfidf_vector(self, criteria: dict):
        parts = []

        if criteria.get("genres"):
            parts.append(" ".join(
                g.lower() for g in criteria["genres"]  # ← убрали replace
            ))
            
        if criteria.get("keywords"):
            parts.append(" ".join(
                k.lower().replace(" ", "_") for k in criteria["keywords"]
            ))

        if criteria.get("director"):
            parts.append(
                criteria["director"].lower().replace(" ", "_")
            )

        if criteria.get("cast"):
            parts.append(" ".join(
                c.lower().replace(" ", "_") for c in criteria["cast"][:5]
            ))

        if criteria.get("certification"):
            parts.append(criteria["certification"].lower())

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
        print(f"[DEBUG] Embedding text: '{text}'")
        print(f"[DEBUG] Embedding shape: {vector.shape}")
        print(f"[DEBUG] Embedding zeros: {(vector == 0).all()}")

        return csr_matrix(vector)



    def _build_num_vector(self, criteria: dict):

        year_from = criteria.get("year_from", 1970)
        year_to   = criteria.get("year_to",   2024)
        year      = (year_from + year_to) / 2

        runtime = criteria.get("max_runtime") or 93.0
        rating = criteria.get("min_rating")  or 6.0

        vec = pd.DataFrame([[
            np.log1p(runtime),     
            np.log1p(1.5),         
            np.log1p(4500000.0),         
            np.log1p(100000.0),         
            rating,                 
            np.log1p(500.0),         
            year,                 
        ]], columns=['runtime', 'popularity', 'budget',
                    'revenue', 'tmdb_rating', 'tmdb_votes', 'year'])

        num_normalized = self._loader.scaler.transform(vec)
        return csr_matrix(num_normalized)

    def _build_results(self, indices, distances, n):
        results = []
        for idx, dist in zip(indices, distances):
           
            similarity = float(max(0.0, 1.0 - dist))
            results.append({
                "matrix_index": int(idx),
                "similarity":   round(similarity, 4),
            })
            if len(results) >= n:
                break
        return results