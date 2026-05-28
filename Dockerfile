FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# (Критически важно!) Создаём пользователя с UID 1000, как просит Hugging Face [citation:7]
RUN useradd -m -u 1000 user
USER user


# Указываем команду для запуска сервера
# Порт должен быть 7860, хост 0.0.0.0
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]