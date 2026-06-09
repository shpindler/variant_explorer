FROM python:3.13-slim

WORKDIR /app

# Устанавливаем системные зависимости (если нужны)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install poetry==2.4.1

# Настраиваем Poetry: не создавать виртуальное окружение внутри контейнера
RUN poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml README.md ./
RUN poetry install --no-interaction --no-ansi --no-root

COPY app.py .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]