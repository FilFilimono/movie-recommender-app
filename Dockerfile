FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /app/data && chmod 777 /app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 user
RUN chown -R user:user /app
USER user


CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]