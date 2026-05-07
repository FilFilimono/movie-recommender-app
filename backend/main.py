from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.core.config import AppConfig
from backend.core.security import PasswordHasher
from backend.database.manager import DatabaseManager
from backend.database.user_repo import UserRepository
from backend.database.session_repo import SessionRepository
from backend.database.prefs_repo import PreferencesRepository
from backend.database.liked_movies_repo import LikedMoviesRepository
from backend.ml.loader import ModelLoader
from backend.ml.metadata_store import MetadataStore
from backend.ml.recommender import RecommenderEngine
from backend.services.auth_service import AuthorizationService
from backend.ml.recommend_service import RecommendationService
from backend.routers import auth, recommendations, movies


app = FastAPI(
    title="CineMatch API",
    description="Рекомендательная система фильмов",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.on_event("startup")
def startup():
   
    AppConfig.print_paths()

    
    db = DatabaseManager(AppConfig.DB_PATH)
    db.connect()
    db.initialize()

    
    user_repo    = UserRepository(db)
    session_repo = SessionRepository(db)
    prefs_repo   = PreferencesRepository(db)
    liked_repo   = LikedMoviesRepository(db)

    
    loader = ModelLoader(AppConfig)
    loader.load()

    metadata = MetadataStore(AppConfig.METADATA_PATH)
    metadata.load()

    engine = RecommenderEngine(loader)

    
    auth_service = AuthorizationService(
        user_repo = user_repo,
        session_repo = session_repo,
        hasher = PasswordHasher(),
    )

    recommend_service = RecommendationService(
        engine = engine,
        metadata = metadata,
        prefs_repo = prefs_repo,
    )


    auth.init(auth_service)
    recommendations.init(auth_service, recommend_service, prefs_repo, liked_repo)
    movies.init(recommend_service)

    print("[App] Сервер готов к работе ✓")


app.include_router(auth.router)
app.include_router(recommendations.router)
app.include_router(movies.router)


frontend_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend"
)
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)