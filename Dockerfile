FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HLA_BACKEND_HOST=0.0.0.0 \
    HLA_BACKEND_PORT=8000 \
    HLA_BACKEND_DATABASE_PATH=/app/data/transplant.db \
    HLA_BACKEND_EXPORT_DIR=/app/exports \
    HLA_BACKEND_LOG_LEVEL=INFO

WORKDIR /app

COPY pyproject.toml requirements.txt requirements-api.txt README.md ./
COPY *.py ./
COPY docs ./docs

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements-api.txt \
    && python -m pip install --no-cache-dir --no-deps . \
    && mkdir -p /app/data /app/exports /app/pyard-data

EXPOSE 8000
VOLUME ["/app/data", "/app/exports", "/app/pyard-data"]

CMD ["hla-api"]
