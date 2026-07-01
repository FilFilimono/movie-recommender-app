# CineMatch

Персональная рекомендательная система фильмов. Проект курсовой работы.

Пользователь проходит короткий тест, указывает жанры, период выхода и минимальный рейтинг. Система подбирает фильмы из базы в 95 000+ картин на основе ML-модели, обученной на данных TMDB и MovieLens.

---

## Скриншоты

**Главная страница**

<img width="978" height="556" alt="image" src="https://github.com/user-attachments/assets/f4acb749-c8fa-4a02-9847-cf9348d2753c" />




**Тест предпочтений**

<img width="978" height="556" alt="image" src="https://github.com/user-attachments/assets/99bb388b-2bef-4888-b74a-fc3a30991d3e" />



**Страница рекомендаций**

<img width="978" height="556" alt="image" src="https://github.com/user-attachments/assets/4bc1121c-31a0-481a-a814-2d6b5fe84504" />


<img width="1426" height="823" alt="image" src="https://github.com/user-attachments/assets/9e787c7e-a342-43d7-ba4b-2626438f019e" />




**Карточка фильма**

<img width="869" height="498" alt="image" src="https://github.com/user-attachments/assets/03968cd0-f5d1-4568-aa12-8845b61d8e0a" />

<img width="963" height="542" alt="image" src="https://github.com/user-attachments/assets/cbffcf10-855c-491c-b1b7-3f227ca1e7c0" />



**Поиск по базе**

<img width="963" height="550" alt="image" src="https://github.com/user-attachments/assets/1ce8ab04-9ae3-47cb-a651-c86e9be73e89" />


**Моё кино**

<img width="963" height="550" alt="image" src="https://github.com/user-attachments/assets/1a1a55e3-46cb-4c64-b662-e6d2c67017c2" />


<img width="1435" height="823" alt="image" src="https://github.com/user-attachments/assets/edcad92c-dfe9-4495-a1b9-891a268ef13f" />


---

## Стек

| Слой        | Технологии                                                           |
| ----------- | -------------------------------------------------------------------- |
| Backend     | Python 3.13, FastAPI, Uvicorn                                        |
| База данных | SQLite (через стандартный модуль `sqlite3`)                          |
| ML          | scikit-learn (KNN), sentence-transformers (all-MiniLM-L6-v2), TF-IDF |
| Данные      | TMDB API + MovieLens (95 501 фильм)                                  |
| Frontend    | Vanilla HTML / CSS / JavaScript (без фреймворков)                    |

---

## Архитектура

```
RecSys/
  backend/
    core/
      config.py          # Все пути и константы в одном месте
      security.py        # Хеширование паролей (bcrypt)
    entities/
      user.py            # User, UserPreferences — бизнес-объекты
      movie.py           # Movie — объект фильма
      session.py         # Session — сессия пользователя
      requests.py        # Pydantic-схемы для валидации запросов
    database/
      manager.py         # Подключение к SQLite
      user_repo.py       # CRUD для пользователей
      session_repo.py    # CRUD для сессий
      prefs_repo.py      # CRUD для предпочтений
      liked_movies_repo.py  # CRUD для избранного
    ml/
      loader.py          # Загрузка ML-артефактов при старте
      metadata_store.py  # Чтение movies_DB.csv, поиск по movie_id
      recommender.py     # Построение вектора запроса, KNN-поиск
    services/
      auth_service.py    # Регистрация, логин, токены
      recommend_service.py  # Связь БД + ML + метаданные
    routers/
      auth.py            # POST /api/register, /api/login, /api/logout
      recommendations.py # GET /api/recommendations, POST /api/preferences
      movies.py          # GET /api/movie/{id}, /api/search, /api/movie/{id}/similar
    main.py              # Точка входа, сборка всех зависимостей
  frontend/
    index.html           # Вход и регистрация
    onboarding.html      # Тест предпочтений (4 шага)
    recommendations.html # Страница рекомендаций
    movie.html           # Карточка фильма
    search.html          # Поиск по базе
    favorites.html       # Избранное и рекомендации по вкусу
  data/
    model/
      transformers/      # knn.joblib, tfidf.joblib, scaler.joblib, embedding_model/
      matrix/            # feature_matrix.npz
      meta/              # meta_movies_DB.csv
    upgrade_movies.csv   # Полный датасет (95 501 фильм)
  notebooks/
    rec_model.ipynb      # Обучение модели
```

---

## Как работает рекомендательная система

### Данные

Датасет собран из двух источников: TMDB (метаданные, постеры, актёры, бюджеты) и MovieLens (рейтинги). После очистки осталось 95 501 фильм с признаками: жанры, актёры, режиссёр, ключевые слова, возрастной рейтинг, год, хронометраж, бюджет, сборы, рейтинг, количество голосов.

### Матрица признаков

Для каждого фильма строится вектор из трёх частей:

```
feature_vector = [num_vector (7) | tfidf_vector (5000) | embedding_vector (384)]
```

**Числовые признаки (7)** — runtime, popularity, budget, revenue, tmdb_rating, tmdb_votes, year. Перед подачей в StandardScaler все числа логарифмируются через `log1p` — это сглаживает огромный разброс значений (бюджет от 0 до 3 млрд).

**TF-IDF (5000)** — текстовый вектор из жанров, ключевых слов, имён актёров и режиссёра. Слова нормализуются: жанры в нижнем регистре без изменений (`science fiction`), имена и ключевые слова с заменой пробелов на `_` (`christopher_nolan`). Это повторяется при построении вектора запроса.

**Embeddings (384)** — семантический вектор из модели `all-MiniLM-L6-v2`. На вход подаётся текст вида `"Genres: Action, Drama. Director: Christopher Nolan"`. Модель понимает смысл, а не только ключевые слова.

Итоговая матрица формы `(95501, 5391)` сохраняется в разреженном формате `.npz`.

### Поиск похожих

Обучается `NearestNeighbors` с метрикой cosine на всей матрице. При запросе пользователя:

1. Из его предпочтений строится такой же трёхчастный вектор
2. Веса частей: `num * 0.05 + tfidf * 5.0 + emb * 3.0` — числа почти не влияют, жанры доминируют
3. `knn.kneighbors(query)` возвращает индексы и расстояния
4. Similarity = `max(0, 1 - distance)` (косинусное расстояние)

### Постфильтрация и сортировка

KNN возвращает 1000 кандидатов. Они фильтруются:
- минимум 200 голосов (50 для фильмов до 2000 года)
- рейтинг >= 5.0
- наличие постера
- соответствие году, рейтингу и возрастному ограничению из настроек

Затем сортируются по формуле:

```
score = similarity * 0.40
      + revenue_norm * 0.25
      + votes_norm   * 0.20
      + rating_norm  * 0.10
      + budget_norm  * 0.05
```

Возвращаются топ-100.

---

## Авторизация

Без JWT и внешних библиотек. При логине генерируется случайный токен (32 байта hex), записывается в таблицу `sessions`. Каждый защищённый запрос проверяет `Authorization: Bearer <token>` по этой таблице.

Пароли хешируются через `bcrypt` (12 раундов).

---

## API

| Метод  | Путь                            | Описание                   |
| ------ | ------------------------------- | -------------------------- |
| POST   | `/api/register`                 | Регистрация                |
| POST   | `/api/login`                    | Вход                       |
| POST   | `/api/logout`                   | Выход                      |
| GET    | `/api/me`                       | Текущий пользователь       |
| POST   | `/api/preferences`              | Сохранить предпочтения     |
| GET    | `/api/preferences`              | Получить предпочтения      |
| GET    | `/api/recommendations`          | Персональные рекомендации  |
| POST   | `/api/recommendations/by-likes` | Рекомендации по избранному |
| POST   | `/api/like/{movie_id}`          | Добавить в избранное       |
| DELETE | `/api/like/{movie_id}`          | Убрать из избранного       |
| GET    | `/api/likes`                    | Список избранного          |
| GET    | `/api/movie/{id}`               | Данные фильма              |
| GET    | `/api/movie/{id}/similar`       | Похожие фильмы             |
| GET    | `/api/search`                   | Поиск по названию          |

Полная интерактивная документация: `http://localhost:8000/docs`



## Обучение модели

Ноутбук `notebooks/rec_model.ipynb` выполняет следующее:

1. Загрузка и очистка датасета из `data/upgrade_movies.csv`
2. Логарифмирование числовых признаков, обучение `StandardScaler`
3. Построение TF-IDF матрицы (5000 признаков, ngram 1-2)
4. Генерация sentence embeddings через `all-MiniLM-L6-v2`
5. Сборка итоговой матрицы: `hstack([num, tfidf, emb])`
6. Обучение `NearestNeighbors(metric='cosine')`
7. Сохранение артефактов:


---

## ООП-структура

Проект содержит 16 классов:

| Класс                   | Файл                            | Роль                 |
| ----------------------- | ------------------------------- | -------------------- |
| `AppConfig`             | `core/config.py`                | Константы и пути     |
| `PasswordHasher`        | `core/security.py`              | bcrypt               |
| `User`                  | `entities/user.py`              | Пользователь         |
| `UserPreferences`       | `entities/user.py`              | Предпочтения         |
| `Movie`                 | `entities/movie.py`             | Фильм                |
| `Session`               | `entities/session.py`           | Сессия               |
| `DatabaseManager`       | `database/manager.py`           | SQLite-соединение    |
| `UserRepository`        | `database/user_repo.py`         | CRUD пользователей   |
| `SessionRepository`     | `database/session_repo.py`      | CRUD сессий          |
| `PreferencesRepository` | `database/prefs_repo.py`        | CRUD предпочтений    |
| `LikedMoviesRepository` | `database/liked_movies_repo.py` | CRUD избранного      |
| `ModelLoader`           | `ml/loader.py`                  | Загрузка артефактов  |
| `MetadataStore`         | `ml/metadata_store.py`          | Чтение CSV           |
| `RecommenderEngine`     | `ml/recommender.py`             | Вектор запроса + KNN |
| `AuthorizationService`  | `services/auth_service.py`      | Регистрация, логин   |
| `RecommendationService` | `services/recommend_service.py` | Сборка рекомендаций  |

