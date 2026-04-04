
class User:
    def __init__(self, username, hash_password,id=None,  created_at=None):
        self.id = id
        self.username = username
        self._hash_password = hash_password
        self.created_at = created_at
        
    @property
    def get_hash_password(self):
        return self._hash_password
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at
        }
    
    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, created_at={self.created_at})"
    

class UserPreferences:

    def __init__(
        self,
        user_id,
        genres=None,
        cast=None,
        director="",
        year_from=1970,
        year_to=2024,
        min_rating=None,
        max_runtime=240,
        certification="",
    ):
        self.user_id = user_id
        self.genres = genres if genres is not None else []
        self.cast = cast if cast is not None else []
        self.director = director
        self.year_from = year_from
        self.year_to = year_to
        self.min_rating = min_rating
        self.max_runtime = max_runtime
        self.certification = certification

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "genres": self.genres,
            "cast": self.cast,
            "director": self.director,
            "year_from": self.year_from,
            "year_to": self.year_to,
            "min_rating": self.min_rating,
            "max_runtime": self.max_runtime,
            "certification": self.certification,
        }
        
