import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



class AppConfig:
    
    DB_DIR: str = os.path.join(BASE_DIR, "backend", "database")
    
    DB_PATH: str = os.path.join(DB_DIR, "app.db")
    