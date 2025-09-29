FROM python:3.12-slim

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# работаем из корня
WORKDIR /

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# теперь каталог пакета — ровно /app
COPY app /app

# явно добавим корень в PYTHONPATH, чтобы импорт "app.main" точно находился
ENV PYTHONPATH=/

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","${PORT}"]
