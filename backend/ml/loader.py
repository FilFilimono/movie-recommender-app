import joblib
from scipy import sparse
from sentence_transformers import SentenceTransformer

from backend.core.config import AppConfig


class ModelLoader:

    def __init__(self, config=AppConfig):
        self._config = config

        self._knn = None
        self._tfidf = None
        self._scaler = None
        self._embedding_model = None
        self._feature_matrix  = None
        self._loaded = False

    def load(self) -> None:
       
        print("[ML] Загрузка артефактов модели...")

        self._knn = joblib.load(self._config.KNN_PATH)
        print(f"[ML] KNN загружен")

        self._tfidf = joblib.load(self._config.TFIDF_PATH)
        print(f"[ML] TF-IDF загружен")

        self._scaler = joblib.load(self._config.SCALER_PATH)
        print(f"[ML] Scaler загружен")

        self._embedding_model = SentenceTransformer(
            self._config.EMBEDDING_MODEL_PATH
        )
        print(f"[ML] Embedding модель загружена")

        self._feature_matrix = sparse.load_npz(
            self._config.FEATURE_MATRIX_PATH
        )
        print(f"[ML] Матрица загружена: {self._feature_matrix.shape}")

        self._loaded = True
        print("[ML] Все артефакты загружены успешно")

    def is_loaded(self) -> bool:
        return self._loaded


    @property
    def knn(self):
        self._check_loaded()
        return self._knn

    @property
    def tfidf(self):
        self._check_loaded()
        return self._tfidf

    @property
    def scaler(self):
        self._check_loaded()
        return self._scaler

    @property
    def embedder(self):
        self._check_loaded()
        return self._embedding_model

    @property
    def feature_matrix(self):
        self._check_loaded()
        return self._feature_matrix

    

    def _check_loaded(self) -> None:
        if not self._loaded:
            raise RuntimeError(
                "Модель не загружена. Вызови loader.load() сначала"
            )