class Movie:
    def __init__(
        self,
        movie_id: int,
        title: str,
        similarity: float = 0.0,
        poster_url: str | None = None,
        overview: str | None = None,
        genres: list | None = None,
        cast: list | None = None,
        director: str | None = None,
        release_year: int | None = None,
        runtime: int | None = None,
        rating: float | None = None,
    ):
        self.movie_id = movie_id
        self.title = title
        self.similarity = similarity
        self.poster_url = poster_url
        self.overview = overview
        self.genres = genres if genres is not None else []
        self.cast = cast if cast is not None else []
        self.director = director
        self.release_year = release_year
        self.runtime = runtime
        self.rating = rating

    def to_dict(self):
        return {
            "movie_id": self.movie_id,
            "title": self.title,
            "similarity": self.similarity,
            "poster_url": self.poster_url,
            "overview": self.overview,
            "genres": self.genres,
            "cast": self.cast,
            "director": self.director,
            "release_year": self.release_year,
            "runtime": self.runtime,
            "rating": self.rating,
        }


class RecommendationResult:
    def __init__(self, user_id, movies=None, generated_at=None):
        self.user_id = user_id
        self.movies = movies if movies is not None else []
        self.generated_at = generated_at

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "movies": self.movies,
            "generated_at": self.generated_at,
        }

    def count(self):
        return len(self.movies)
    