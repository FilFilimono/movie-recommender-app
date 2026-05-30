import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



class AppConfig:
    
    DB_DIR: str = os.path.join(BASE_DIR, "backend", "database")   
    DB_PATH: str = os.path.join(DB_DIR, "app.db")
    # DB_PATH: str = "/app/data/app.db"
    
    KNN_PATH: str = os.path.join(BASE_DIR, "data", "model", "transformers", "knn_model.joblib")
    TFIDF_PATH: str = os.path.join(BASE_DIR, "data", "model", "transformers", "tfidf.joblib")
    SCALER_PATH: str = os.path.join(BASE_DIR, "data", "model", "transformers", "scaler.joblib")
    EMBEDDING_MODEL_PATH: str = os.path.join(BASE_DIR, "data", "model", "transformers", "embedding_model")
    FEATURE_MATRIX_PATH: str = os.path.join(BASE_DIR, "data", "model", "matrix", "feature_matrix.npz")
 
    
    METADATA_PATH: str = os.path.join(BASE_DIR, "data", "model", "meta", "meta_movies_DB.csv")
 

    N_RECOMMENDATIONS: int = 15
    BCRYPT_ROUNDS:     int = 12
    TOKEN_LENGTH:      int = 32
 
    @classmethod
    def print_paths(cls) -> None:
        print("=== AppConfig ===")
        for attr in ["DB_PATH", "KNN_PATH", "TFIDF_PATH",
                     "SCALER_PATH", "FEATURE_MATRIX_PATH", "METADATA_PATH"]:
            path = getattr(cls, attr)
            exists = "✓" if os.path.exists(path) else "✗ НЕТ ФАЙЛА"
            print(f"  {attr}: {exists}")
        print("=================")
 
    