from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str
    
class LoginRequest(BaseModel):
    username: str
    password: str

class PreferencesRequest(BaseModel):
    genres: list[str]  = []
    cast: list[str]  = []
    director: str= ""
    year_from: int= 1970
    year_to: int= 2024
    min_rating: float|None = None
    max_runtime: int= 240
    keywords: list[str]  = []
    certification: str = ""  
    